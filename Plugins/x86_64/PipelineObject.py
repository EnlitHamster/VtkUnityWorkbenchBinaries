#
# Created by: Henk Dreuning
# Student number: 10550461
# Date: 08-06-2016
#

from vtk import *
import utils
import re

# Class that wraps a vtk object for use in the Pipeline object.
# Function calls to the wrapped vtkInstance(s) should be done via:
#      vtkInstanceCall(<method>, <arguments to method>)
class PipelineObject():
    def __init__(self, vtkInstance, methods):
        if vtkInstance == None:
            raise TypeError("Cannot wrap 'None' vtk instance")

        if not vtkInstance.IsA("vtkAlgorithm"):
            message = "PipelineObject: vtk instance must be "
            message += "(subclass of) vtkAlgorithm."
            raise TypeError(message)

        self.vtkInstance = vtkInstance
        self.setToMethods, self.onOffMethods, self.setValueMethods = methods

    def _assertInstanceSet(self):
        if self.vtkInstance == None:
            raise Error("PipelineObject has no vtkInstance set")
            return

    def vtkInstanceCall(self, methodName, *args, **kwargs):
        # Call a method of the wrapped vtkInstance.        

        self._assertInstanceSet()

        # Call vtkInstance's function with the given name
        return getattr(self.vtkInstance, methodName)(*args, **kwargs)

    def edit(self):
        """ Callback for editing a pipeline object. Returns an event for the
        UIManager to handle. """

        return "POEditStartedEvent"

    def getVtkAttributes(self):
        # This can be used to show more elements in the pipeline visualization
        # than just the pipelineObjects themselves. As it is unused for now,
        # don't return any objects.        
        return []

    def getSetToMethods(self):
        return self.setToMethods

    def getOnOffMethods(self):
        return self.onOffMethods

    def getSetValueMethods(self):
        return self.setValueMethods

    def getCurrentValue(self, setValueMethod):
        # Retrieve the current value associated with a given setValueMethod.

        returnType = self.setValueMethods[setValueMethod]["getReturnType"]
        getMethod = self.setValueMethods[setValueMethod]["getMethod"]

        # For experiments: add extra argument if the 'GetValue' method of the
        # vtkContourFilter is called.
        if (type(self.vtkInstance).__name__ == 'vtkContourFilter'
            and getMethod == 'GetValue'):
            return returnType, self.vtkInstanceCall(getMethod, 0)

        return returnType, self.vtkInstanceCall(getMethod)

    def callSetToMethod(self, attributeInfo):
        # A value for a setTo method was chosen, set the new value.

        attributeName, setMethodName = attributeInfo

        # Unselect previous selection.
        setToMethods = self.setToMethods[attributeName]["setToMethods"]

        for i, (_, isSelected) in enumerate(setToMethods):
            if isSelected:
                setToMethods[i][1] = False
                break

        # Call setToMethod.
        self.vtkInstanceCall(setMethodName)

        # Set new value as selected.
        for i, (setToMethod, _) in enumerate(setToMethods):
            if setToMethod == setMethodName:
                setToMethods[i][1] = True
                break

        return "POAttributeChangedEvent"

    def toggleOnOffMethod(self, attributeName):
        # An onOff method was activated, toggle its value.

        getMethodName = "Get" + attributeName
        if self.vtkInstanceCall(getMethodName) == 1:
            self.vtkInstanceCall(attributeName + "Off")
        else:
            self.vtkInstanceCall(attributeName + "On")

        # Save new value
        self.onOffMethods[attributeName][1] = self.vtkInstanceCall(getMethodName)

        return "POAttributeChangedEvent"

    def callSetValueIntMethod(self, methodName,  *args, **kwargs):
        self.vtkInstanceCall(methodName, *args, **kwargs)
        return "POEditIntStoppedEvent"

    def callSetValueFloatMethod(self, methodName,  *args, **kwargs):
        # For experiments: add extra argument if the 'SetValue' method of the
        # vtkContourFilter is called.
        if (type(self.vtkInstance).__name__ == 'vtkContourFilter'
            and methodName == 'SetValue'):
            args = [0] + list(args)

        self.vtkInstanceCall(methodName, *args, **kwargs)
        return "POEditFloatStoppedEvent"
    
    def callSetValueStringMethod(self, methodName,  *args, **kwargs):
        self.vtkInstanceCall(methodName, *args, **kwargs)
        return "POEditStringStoppedEvent"