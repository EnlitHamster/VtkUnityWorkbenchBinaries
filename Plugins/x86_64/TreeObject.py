#
# Created by: Henk Dreuning
# Student number: 10550461
# Date: 08-06-2016
#

from vtk import *
from PipelineObject import *
from copy import deepcopy

# Class that wraps a VTK class in the classTree and determines its
# characteristics.
class TreeObject():
    def __init__(self, classType, eo):
        self.classType = classType
        self.eo = eo

        self.isAbstract = None
        self.implemented = None
        
        self.subclasses = None
        self.implementedSubclasses = None
        self.acceptsCache = {}
        self.onOffMethods = []
        self.setToMethods = []
        self.setValueMethods = []

        self.categories = []

        self.buildSubtree()
        self.parseMethods()

    def parseMethods(self):
        # Only parse methods if this is not an abstract class.
        if self.isAbstract:
            return
        
        dummyNode = self.classType()

        # Get methods of the different types.
        setValueMethods, setToMethods = utils.getSetMethods(dir(dummyNode))
        onOffMethods = utils.getOnOffMethods(dir(dummyNode))
        getMethods = utils.getGetMethods(dir(dummyNode))

        # Group their accompanying 'get' methods.
        setValueMethods, ogm1 = self.groupGetMethods("setValueMethod", setValueMethods, getMethods)
        setToMethods, ogm2 = self.groupGetMethods("setToMethod", setToMethods, getMethods)
        onOffMethods, ogm3 = self.groupGetMethods("onOffMethod", onOffMethods, getMethods)

        # Note: setValueMethods, setToMethods and onOffMethods now contain
        # tuples with (setValueMethod, GetMethod), (setToMethod, GetMethod)
        # and (onOffMethod, GetMethod) respectively.

        # Remove unused (obsolete) 'get' methods.
        obsoleteGetMethods = ogm1 + ogm2 + ogm3
        getMethods = self.removeObsoleteGetMethods(obsoleteGetMethods, getMethods)
        setValueMethods = self.removeObsoleteSetValueMethods(onOffMethods,
            setToMethods, setValueMethods)

        # Group all setTo methods that operate on the same property.
        # Idem for OnOff methods.
        # Determine return and argument types for setValue methods.
        self.parseSetToMethods(setToMethods, dummyNode)
        self.parseOnOffMethods(onOffMethods, dummyNode)
        self.parseSetValueMethods(setValueMethods, dummyNode)

    def parseSetToMethods(self, setToMethods, dummyNode):
        # Group all setTo methods that operate on the same property.

        attributes = {}
        for setMethod, getMethod in setToMethods:
            # Take "Get" off the front
            attributeName = getMethod[3:]

            # Add to the list of Set*To* methods for this attribute.
            if attributeName in attributes:
                attributes[attributeName]["setToMethods"].append([setMethod, False])
            else:
                # Also save the current (default) value. The accompanying
                # Set*To* method is set al selected later.
                attributes[attributeName] = {"getMethod": getMethod,
                                            "setToMethods": [[setMethod, False]]}

        toRemove = []

        # Set the currently 'active' (default) Set*To* methods as selected.
        for attribute, methods in attributes.items():

            getMethod = methods["getMethod"]
            defaultValue = getattr(dummyNode, getMethod)()

            for i, [setToMethod, isSelected] in enumerate(methods["setToMethods"]):
                # Set this value and check if it equals default
                try:
                    getattr(dummyNode, setToMethod)()
                except:
                    # Skip this option
                    # print "Skipping", setToMethod, getMethod, self.classType.__name__
                    toRemove.append((attribute, i))
                    continue

                value = getattr(dummyNode, getMethod)()

                if value == defaultValue:
                    # Set as selected 
                    methods["setToMethods"][i][1] = True
                    break

        # Remove the skipped options
        for attribute, i in toRemove:
            key = list(attributes[attribute].keys())[i]
            del attributes[attribute][key]

        self.setToMethods = attributes

    def parseOnOffMethods(self, onOffMethods, dummyNode):
        # Group all onOff methods that operate on the same property.
        # Only saves property's name and the getMethod.

        onOffMethodsDict = {}

        for i, (attributeName, getMethod) in enumerate(onOffMethods):
            # Select default value
            value = getattr(dummyNode, getMethod)()
            onOffMethodsDict[attributeName] = [getMethod, value]

        self.onOffMethods = onOffMethodsDict

    def parseSetValueMethods(self, setValueMethods, dummyNode):
        # Determine return and argument types for setValue methods.

        setValueMethodsDict = {}
        
        # For experiments: check if this is a vtkContourFilter,
        # used to add the 'SetValue' method manually.
        isContourFilter = False
        if self.classType == vtkContourFilter:
            isContourFilter = True


        for setMethod, getMethod in setValueMethods:
            methodSignatures = utils.getMethodSignature(dummyNode, setMethod)
            setTypes = utils.evalTypes(methodSignatures, setMethod)

            methodSignatures = utils.getMethodSignature(dummyNode, getMethod)
            getTypes = utils.evalTypes(methodSignatures, getMethod)

            # getTypes and setType are of the form:
            # [returntype, (argument type, argument type, ...)]

            # Currently only the first method signature is used.

            basicTypes = [int, float, str]
            
            if (getTypes[0][0] in basicTypes and getTypes[0][1] == "void"
                and setTypes[0][1] in basicTypes):
                value = getattr(dummyNode, getMethod)()
                setValueMethodsDict[setMethod] = {"getMethod": getMethod,
                                                "value": value,
                                                "getReturnType": getTypes[0][0],
                                                "getParameterTypes": getTypes[0][1],
                                                "setReturnType": setTypes[0][0],
                                                "setParameterTypes": setTypes[0][1]}
            
            # For experiments: 'manually' add SetValue method if this is a
            # vtkContourFilter.
            if isContourFilter and setMethod == "SetValue":
                setValueMethodsDict = self.addSetValueContourFilter(
                    setValueMethodsDict, dummyNode, setMethod, getMethod)
                
        self.setValueMethods = setValueMethodsDict

    # For experiments: if this is a vtkContourFilter, add the 'SetValue'
    # method manually.
    def addSetValueContourFilter(self, setValueMethodsDict, dummyNode, setMethod, getMethod):
        value = getattr(dummyNode, getMethod)(0)
        setValueMethodsDict[setMethod] = {"getMethod": getMethod,
                                            "value": value,
                                            "getReturnType": float,
                                            "getParameterTypes": "void",
                                            "setReturnType": "void",
                                            "setParameterTypes": float}

        return setValueMethodsDict

    def groupGetMethods(self, methodType, methodNames, getMethods):
        # Group the accompanying 'get' method for setTo/setValue/onOff methods.

        obsoleteGetMethods = []
        newMethodNames = []

        # Iterate over a copy of methodNames, as we might modify it in the else
        # clause.
        for methodName in methodNames[:]:
            getMethod = self.renameToGetMethod(methodType, methodName)

            if getMethod in getMethods:
                # change methodName into a tuple containing:
                # (setValueMethod/setToMethod/onOffMethod, getMethod)
                newMethodNames.append((methodName, getMethod))

                # Remove getMethod from getMethods, since value is of no
                # interest to show anywhere else.
                obsoleteGetMethods.append(getMethod)

            else:
                # setValueMethod has no get method, don't show it
                methodNames.remove(methodName)

        return newMethodNames, obsoleteGetMethods

    def removeObsoleteGetMethods(self, obsoleteGetMethods, getMethods):
        # Remove obsolete get methods
        for getMethod in obsoleteGetMethods:
            # Doubles can exist (i.e. both MethodOn/MethodOff and SetMethod
            # exist), so catch ValueError (not in list).
            try:
                getMethods.remove(getMethod)
            except ValueError:
                pass

        return getMethods

    def removeObsoleteSetValueMethods(self, onOffMethods, setToMethods, setValueMethods):
        # Remove Set<property> methods if there already are <property>On/Off
        # methods.
        for attributeName, getMethod in onOffMethods:
            if ("Set" + attributeName, getMethod) in setValueMethods:
                setValueMethods.remove(("Set" + attributeName, getMethod))
                # print "removed obsolete Set Method", "Set" + attributeName

        # Remove Set<property> methods if there already are
        # Set<property>To<value> methods.
        for _, getMethod in setToMethods:
            setMethod = "Set" + getMethod[3:]
            if (setMethod, getMethod) in setValueMethods:
                setValueMethods.remove((setMethod, getMethod))
                # print "removed obsolete Set Method", setMethod

        return setValueMethods


    def renameToGetMethod(self, methodType, methodName):
        # Given a setTo, setValue or onOff method, get the name of the
        # accompanying 'get' method.

        if (methodType == "setValueMethod"):
            return "G" + methodName[1:]

        elif (methodType == "setToMethod"):
            baseMethodName = re.sub("To\w+$", "", methodName)
            return "G" + baseMethodName[1:]
        
        elif (methodType == "onOffMethod"):
            return "Get" + methodName


    def buildSubtree(self):
        # This will create TreeObjects for all subclasses (recursively)
        # and determine if this vtk class (type) is abstract and implemented.
        # The tree can be used for selecting a new node to add to the pipeline. 
        subclasses = self.classType.__subclasses__()
        self.subclasses = []

        for subClassType in subclasses:
            subClassTreeObject = TreeObject(subClassType, self.eo)
            self.subclasses.append(subClassTreeObject)
            
        self._determineIsAbstract()
        # This will set both self.implemented and
        # fill self.implementedSubclasses
        self._isImplemented()

    def _determineIsAbstract(self):
        # Instantiate to test if class is abstract
        try:
            _ = self.classType()
            self.isAbstract = False            
        except (TypeError, NotImplementedError):
            self.isAbstract = True

    def _isImplemented(self):
        if self.implemented == None:
            self._determineIsImplemented()

        return self.implemented

    def _determineIsImplemented(self):
        implemented = None
        
        # Test subclasses, first check if they have been built
        if self.subclasses == None:
            message = "Subclasses not built, cannot check if implemented"
            raise Exception(message)
        else:
            self.implementedSubclasses = []

            # For each class, check if it is implemented
            implemented = False
            for subClass in self.subclasses:
                if subClass._isImplemented():
                    implemented = True
                    self.implementedSubclasses.append(subClass)

            # Concrete classes are always implemented (by themselves), but the
            # previous loop is executed anyways to fill 'implementedSubclasses'.
            if not self.isAbstract:
                implemented = True

        self.implemented = implemented

    def _getImplementedSubclasses(self):
        if self.implementedSubclasses == None:
            self._determineIsImplemented()

        return self.implementedSubclasses

    def listImplementedSubclasses(self):
        for i, subClass in enumerate(self.implementedSubclasses):
            print("[{}]: {}".format(i, subClass.classType.__name__))

    def acceptsAsInput(self, outputPort, prevNodeTypeName=None, prevNode=None):
        # Only test self if self is not abstract. 
        if self.isAbstract:
            return False

        # First try if a result was cached
        if prevNodeTypeName != None:
            try:
                return self.acceptsCache[prevNodeTypeName]
            except KeyError:
                pass

        # Test if self has the right amount of input/output ports.
        
        dummyNode = self.classType()

        # Only list single output objects (for linear pipeline)
        if dummyNode.GetNumberOfOutputPorts() > 1:
            return False

        # Only list no input objects for source objects
        if outputPort == None:
            if dummyNode.GetNumberOfInputPorts() != 0:
                return False
            else:
                # No input needed, so list this one
                return True

        # Only use objects with one or more input ports (for non-source
        # objects).
        else:
            if dummyNode.GetNumberOfInputPorts() < 1:
                return False

        # The object has the correct amount of input and output ports, check
        # if the output is accepted now:

        # Reset error handler/observer
        self.eo.ErrorOccurred()

        # Test if self accepts outputPort as input
        dummyNode.SetInputConnection(prevNode.vtkInstanceCall("GetOutputPort"))
        dummyNode.UpdateInformation()


        if not self.eo.ErrorOccurred():
            # Cache the result
            if prevNodeTypeName != None:
                self.acceptsCache[prevNodeTypeName] = True
            
            return True

        # Cache the result
        if prevNodeTypeName != None:
            self.acceptsCache[prevNodeTypeName] = False
        
        return False

    def createHashTable(self, hashTable):
        # Adds this TreeObject and its subclasses to a hash table/dictionary
        # with class names/TreeObjects as key/value pairs.

        className = self.classType.__name__
        hashTable[className] = self
        for subClass in self.subclasses:
            hashTable = subClass.createHashTable(hashTable)

        return hashTable

    def createNode(self):
        # Create a pipelineObject with which wraps a vtkInstance of the class
        # that this TreeObject represents, and return it.

        # This method should not be called for abstract classes.
        if self.isAbstract:
            raise Exception("Cannot instantiate abstract class.")

        # Instantiate vtkInstance
        vtkInstance = self.classType()

        # Copy attribute methods and current (default) values
        methods = [deepcopy(self.setToMethods), deepcopy(self.onOffMethods),
                    deepcopy(self.setValueMethods)]

        # Wrap in pipelineObject
        pipelineObject = PipelineObject(vtkInstance, methods)

        # print "Created node:", pipelineObject, pipelineObject.vtkInstance
        return pipelineObject

    def setCategories(self, categories, mapping):
        # Determine the categories that this class belongs to and store it.

        className = self.classType.__name__
        categories = self.checkCategory(className, categories, mapping)

        for subClass in self.subclasses:
            categories = subClass.setCategories(categories, mapping)
        
        return categories
        
    def checkCategory(self, className, categories, mapping):
        # Determine the categories that this class belongs to.

        categorized = False
        
        for category in categories.keys():
            if category in className:
                categorized = True
                if type(categories[category]) == list:
                    self.categories.append(category)
                    categories[category].append(className)
                else:
                    categories[category] = self.checkCategory(className,
                        categories[category], mapping)

        if not categorized:
            if "Miscellaneous" not in categories:
                categories["Miscellaneous"] = []

            categories["Miscellaneous"].append(className)
            # If self.categories is going to be used, it should be set here
            # as well.

        return categories