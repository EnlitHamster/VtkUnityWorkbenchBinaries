#
# Created by: Henk Dreuning
# Student number: 10550461
# Date: 08-06-2016
#
# This file contains some utility functions used by several objects
# in the application.
#

import re, math
from vtk import *

def getSetMethods(methodList):
    # Get all setTo and setValue methods out of the
    # given list of methods.
    setPattern = re.compile("^Set\w+$")
    setToPattern = re.compile("^Set\w+To\w+$")

    setValueMethods = []
    setToMethods = []

    for method in methodList:
        # Check if it is a 'Set' method.
        if setPattern.match(method) != None:
            # Check if it is a 'Set*To*' method.
            if setToPattern.match(method) != None:
                setToMethods.append(method)
            else:
                setValueMethods.append(method)

    return setValueMethods, setToMethods

def getGetMethods(methodList):
    # Get all 'get' methods out of the
    # given list of methods.
    getPattern = re.compile("^Get\w+$")

    getMethods = []

    for method in methodList:
        # Check if it is a 'Get' method.
        if getPattern.match(method) != None:
            getMethods.append(method)

    return getMethods

def getOnOffMethods(methodList):
    # Get all onOff methods out of the
    # given list of methods.
    onPattern = re.compile("^\w+On$")
    offPattern = re.compile("^\w+Off$")

    onMethods = []
    offMethods = []
    onOffMethods = []
    
    for method in methodList:
        # Check if it is a 'On' or 'Off' method.
        if onPattern.match(method) != None:
            onMethods.append(method)
        if offPattern.match(method) != None:
            offMethods.append(method)

    # Only methods that have both an on and Off variant are
    # real 'OnOff' methods. So filter out methods that have both variants.
    for onMethod in onMethods:
        baseMethodName = onMethod[0:-2]
        offMethod = baseMethodName + "Off"
        if offMethod in offMethods:
            onOffMethods.append(baseMethodName)

    return onOffMethods


# -----------------------------
# Method signature parsing
# -----------------------------

def getMethodSignature(vtkObject, methodName):
    # vtkObject should be an instantiated vtk object.

    # Pattern for a method signature.
    # Parentheses do 2 things: just grouping characters together and 'capturing
    # groups'. The last thing causes re.findall to do funny things. To use
    # parentheses only for 'just' grouping characters, use: (?:...) (with ...
    # being the characters to group). That is used here as well.
    signaturePattern= "[Vx]\." + methodName + "\(" + "[\w\s\[\]\(\)\.,]*" + "\)" + "(?:\s->\s)*" + "[-\w]*"

    # Pattern for an enum value (sometimes enums and their values have a None docstring)
    # sometimes they match this. Both are ignored.
    enumPattern = "int" + "\(" + "[\w\s\[\]\(\)\.,\=]*" + "\)" + "( -> )*" + "[-\w]*"

    if len(re.findall("__\w+__", methodName)) != 0:
        return None

    docstring = getattr(vtkObject, methodName).__doc__

    if docstring == None:
        return None

    signatureList = re.findall(signaturePattern, docstring)
    
    if len(signatureList) != 0:
        return signatureList
    else:
        return None

        # As long as the 'else' below is not handled, the code below
        # is unnecessary. Left here for later use.

        # Check if it is an enum value
        if len(re.findall(enumPattern, docstring)) != 0:
            return None
        else:
            # Tested that this is only true for one method in
            # all subclasses of vtkObject, namely the method 'SetKernel7x7x7'
            # of 'vtkImageConvolve'. That one has an empty docstring.
            # Could be handled manually.
            return None

def parseSig(signature):
    # Parses a method's signature. The )string) description is
    # divided into a part describing the return type and a part
    # describing the types of the arguments.
    
    signature = re.sub('[\s+]', '', signature)
    signature = signature.split('->')
    
    if len(signature) > 1:
        if signature[1] == "":
            call = signature[0]
            rettype = None
        else:
            call, rettype = signature
    else:
        call = signature[0]
        rettype = None

    return call, rettype

def parseReturn(rettype):
    # Determines the types of a method's return value.

    if rettype != None:

        # Apply manual mappings
        rettype = rettype.replace("string", "str")
        
        try:
            retType = eval(rettype)
            return retType
        except Exception:
            return "error"
    else:
        return "void"

def parseArgs(call, methodName):
    # Determines the types of a method's paramters/arguments.

    call = call.replace('V.' + methodName, '')
    call = call.replace('\n', '')
    call = call[1:-1]

    # Apply manual mappings
    call = call.replace("string", "str")

    if call == "":
        return "void"
    else:
        try:
            types = eval(call)
            return types
        except Exception:
            return "error"

def evalTypes(signatureList, methodName):
    # Determines the types of a method's paramters/arguments
    # and return value.

    results = []

    if signatureList == None:
        return results

    for signature in signatureList:
        call, rettype = parseSig(signature)
        returnType = parseReturn(rettype)
        argTypes = parseArgs(call, methodName)
        results.append((returnType, argTypes))

    return results