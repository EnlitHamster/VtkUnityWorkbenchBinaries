#
# Created by: Henk Dreuning
# Student number: 10550461
# Date: 08-06-2016
#

from vtk import *
from PipelineObject import *
from ClassTree import *
from TreeObject import *
import utils

# Class that represents the pipeline created by the user.
class Pipeline():
    def __init__(self, classTree):
        self.elements = []
        self.classTree = classTree
        self.lastChosenClassTreeElem = None
        self.actors = []
        self.shownActors = []
        self.activatedPipelineObject = None

    def resetLastChosenClassTreeElem(self):
        self.lastChosenClassTreeElem = None

    def appendToPipeline(self, newNode):
        # Appends the given node to the pipeline.

        if len(self.elements) != 0:
            # Not the first element in the pipeline, so set input and output
            # connections.
            lastNode = self.elements[-1]
            outputPort = lastNode.vtkInstanceCall("GetOutputPort")
            newNode.vtkInstanceCall("SetInputConnection", outputPort)

        self.elements.append(newNode)

        # Call Update() if possible.
        if newNode.vtkInstanceCall("IsA", "vtkAlgorithm"):
            newNode.vtkInstanceCall("Update")

        # If the added node is a vtkMapper, add an actor for it.
        if newNode.vtkInstanceCall("IsA", "vtkMapper"):
            actor = vtkActor()
            actor.SetMapper(newNode.vtkInstance)
            self.actors.append(actor)

    def getLastNode(self):
        if len(self.elements) != 0:
            return self.elements[-1]
        else:
            return None

    def refresh(self, renderer, renderWindowInteractor, keepSelected=False):
        # Refresh the resulting visualization.

        # Remove all old actors
        for actor in self.shownActors:
            renderer.RemoveActor(actor)

        self.shownActors = []

        # Add all new actors
        for actor in self._getActors():
            self.shownActors.append(actor)
            renderer.AddActor(actor)

    def _getActors(self):
        return self.actors

    def editPipelineObject(self, pipelineObject):
        self.setActivatedPipelineObject(pipelineObject)
        return pipelineObject.edit()

    def setActivatedPipelineObject(self, pipelineObject):
        self.activatedPipelineObject = pipelineObject

    def getActivatedPipelineObject(self):
        return self.activatedPipelineObject

    def getElements(self):
        return self.elements

    def __iter__(self):
        for pipelineObject in self.elements:
            yield pipelineObject

    def __len__(self):
        return len(self.elements)