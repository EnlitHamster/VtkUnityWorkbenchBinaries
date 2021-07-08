#
# Created by: Henk Dreuning
# Student number: 10550461
# Date: 08-06-2016
#

from vtk import *
from PipelineObject import *
from TreeObject import *
from copy import deepcopy
import json

# A class that creates a classtree of VTK.
class ClassTree():
    def __init__(self, eo, categoriesFilename=None, categoriesMappingFilename=None):
        if eo == None:
            raise TypeError("error observer cannot be None")
            return

        self.pipeline = None
        self.categoriesFilename = categoriesFilename
        self.categoriesMappingFilename = categoriesMappingFilename
        self.eo = eo

        self.root = TreeObject(vtkAlgorithm, eo)

        self.categories = self._loadCategories()
        self.categoriesMapping = self._loadCategoriesMapping()
        
        self.categories = self.root.setCategories(self.categories,
            self.categoriesMapping)

        self.selection = self._loadSelection(deepcopy(self.categories))
        
        self.nameToTreeObject = self.root.createHashTable({})

    def setPipeline(self, pipeline):
        if pipeline == None:
            raise TypeError("Pipeline cannot be None")
            print("Pipeline cannot be None")
            return

        self.pipeline = pipeline

    def getRoot(self):
        return self.root

    def getTreeObjectByName(self, className):
        # Use the dictionary built before to quickly retrieve
        # the TreeObject belonging to the given class name.

        try:
            return self.nameToTreeObject[className]
        except KeyError:
            return None

    def _loadCategories(self):
        # Load the categories to use.

        categories = self._readJsonFromFile(self.categoriesFilename)

        if categories == None:
            print("Could not read categories from file, using default values.")
            
            categories = {"Image": [], "Mapper": [], "Actor": [], "Source": [],
                            "Reader": [], "Writer": [], "Streamer": [],
                            "Filter": [], "OpenGL": [], "Polydata": [],
                            "Grid": []}

        return categories

    def _loadCategoriesMapping(self):
        # Load the manual mapping for categories to use.

        mapping = self._readJsonFromFile(self.categoriesMappingFilename)

        if mapping == None:
            print ("Could not read categories mapping from file, " +
                "using default (no mapping).")

            mapping = {}

        return mapping

    def _readJsonFromFile(self, filename): 
        try:
            with open(filename, "r") as fp:
                return json.load(fp)
        except IOError:
            print("Can not open JSON file", filename)
            return None
        except ValueError:
            print("JSON in ", filename, "not valid.")
            return None
        except TypeError:
            print("No JSON file given.")
            return None

    def _loadSelection(self, selection):
        # Load the inital values (all False) into the dictionary
        # representing the current selection.

        if type(selection) == list:
            return False
        else:
            for key in selection:
                selection[key] = self._loadSelection(selection[key])
            return selection

    def getCategories(self):
        return self.categories

    def getSelection(self):
        return self.selection

    def getClassNamesByCategory(self, subCategoryLists, andOrOr):
        # subCategoryLists should be a list of:
        # ["category", "subCategory", "subSubCategory", etc.]
        # 
        # So:
        # [["category", "subCategory", "subSubCategory", etc.], ...]

        if len(subCategoryLists) < 1:
            return []

        resultingClassNames = self._getClassNamesFromSubCategoryList(
            self.categories, subCategoryLists[0])

        for subCategoryList in subCategoryLists[1:]:
            classNames = self._getClassNamesFromSubCategoryList(
                self.categories, subCategoryList)

            resultingClassNames = self._combineLists(classNames,
                resultingClassNames, andOrOr)

        return resultingClassNames

    def isCategorySelected(self, categoryName):
        # Check if a given category is selected ('on'),
        # only works for first level categories.
        try:
            return self.selection[categoryName]
        except KeyError:
            return False

    def isSelected(self, subCategoryList):
        # subCategoryList should be a list of:
        # ["category", "subCategory", "subSubCategory", etc.]

        if len(subCategoryList) < 1:
            raise KeyError("no category given")

        return self._isSelected(subCategoryList, self.selection)

    def _isSelected(self, subCategoryList, selection):
        if len(subCategoryList) == 0:
            return self.allSubcategoriesSelected(selection)

        if type(selection[subCategoryList[0]]) == bool:
            if len(subCategoryList) == 1:
                return selection[subCategoryList[0]]
            else:
                raise KeyError("category not present")
        else:
            return self._isSelected(subCategoryList[1:], selection[subCategoryList[0]])


    def allSubcategoriesSelected(self, selection):
        allSelected = True

        for key in selection:
            if type(selection[key]) == bool:
                if selection[key] == False:
                    allSelected = False
            else:
                if not self.allSubcategoriesSelected(selection[key]):
                    allSelected = False

        return allSelected


    def _getClassNamesFromSubCategoryList(self, categories, subCategoryList):
        for subCategory in subCategoryList:
            try:
                categories = categories[subCategory]
            except KeyError:
                categories = []
                break
            except TypeError:
                categories = []
                break

        # If this is not yet a list/lowest level subcategory, create a list of
        # all elements of all subcategories.

        categories = self._getAllClassNames(categories)

        # categories now contains all classNames in the category indicated by
        # subCategoryList.
        return categories

    def _getAllClassNames(self, categories):
        if type(categories) == list:
            return categories
        else:
            result = []
            first = True
            for key in categories:
                if first:
                    result = self._getAllClassNames(categories[key])
                    first = False
                else:
                    classNames = self._getAllClassNames(categories[key])
                    result = self._combineLists(classNames, result, "or")

            return result

    def _combineLists(self, classNames1, classNames2, andOrOr):
        # 'ANDs' or 'ORs' two lists.

        classNames1 = set(classNames1)
        classNames2 = set(classNames2)

        if andOrOr == "and":
            # The resulting classes must be in all enabled (sub)categories,
            # so take AND of lists.
            return list(set.intersection(classNames1, classNames2))
        else:
            # The resulting classes can be in any of the enabled
            # (sub)categories, so take OR of existing values.
            return list(set.union(classNames1, classNames2))

    def getSelectedClassNames(self, prevNode=None):
        # Get the names of all classes that belong to the
        # categories that are currently selected.

        selected = []

        for key in self.selection:
            value = self.selection[key]
            if type(value) == bool and value == True:
                selected.append([key])


        andOrOr = "and"
        classNames = deepcopy(self.getClassNamesByCategory(selected, andOrOr))
        
        # Filter abstract classes:
        for className in classNames[:]:
            treeObject = self.getTreeObjectByName(className)
            if treeObject.isAbstract:
                classNames.remove(className)


        # Filter accepting classes
        if prevNode != None:
            # Reset error handler/observer
            self.eo.ErrorOccurred()

            # Use 'real' previous node (not a dummy) to ensure first part of
            # pipeline is 'valid'. Otherwise missing input connections could
            # cause unwanted vtk errors.
            outputPort = prevNode.vtkInstanceCall("GetOutputPort")
            prevNodeTypeName = type(prevNode.vtkInstance).__name__

            # If there is a previous node, but is has no output port, nothing
            # else can be added.
            if self.eo.ErrorOccurred():
                return []

        else:
            outputPort = None
            prevNodeTypeName = None


        for className in classNames[:]:
            treeObject = self.getTreeObjectByName(className)

            if not treeObject.acceptsAsInput(outputPort, prevNodeTypeName, prevNode):
                classNames.remove(className)

        return classNames

    def classChosen(self, className):
        # Create pipelineObject from the last chosen classTreeElem
        treeObject = self.getTreeObjectByName(className)
        newNode = treeObject.createNode()
        self.pipeline.appendToPipeline(newNode)
        return "CATchosenEvent"

    def switchPressed(self, categoryName):
        # Toggle the selection of a given category,
        # only works for first level categories.
        try:
            self.selection[categoryName] = not self.selection[categoryName]
        except KeyError:
            pass

        return "CATFilterSwitchedEvent"