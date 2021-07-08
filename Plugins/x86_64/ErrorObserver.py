from vtk import *

class ErrorObserver:
    # Catches VTK errors and saves them until a new error occures.
    #
    # Source:
    # http://public.kitware.com/pipermail/vtkusers/2012-June/074703.html
    
    def __init__(self):
        self.__ErrorOccurred = False
        self.__ErrorMessage = None
        self.CallDataType = 'string0'

    def __call__(self, obj, event, message):
        self.__ErrorOccurred = True
        self.__ErrorMessage = message

    # These two functions are for manual checking if an error has occured.
    def ErrorOccurred(self):
        occ = self.__ErrorOccurred
        self.__ErrorOccurred = False
        return occ

    def ErrorMessage(self):
        return self.__ErrorMessage