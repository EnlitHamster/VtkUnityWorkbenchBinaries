from ErrorObserver import *
from vtk import *
from Pipeline import *
import ctypes
import collections

import time


class Introspector:

	def setupGlobalWarningHandling(self):
		# Redirect output to a file.
		ow = vtkFileOutputWindow()
		ow.SetFileName("log/vtk_errors.txt")
		vtkOutputWindow.SetInstance(ow)

		# And catch errors in the errorObserver.
		self.eo = ErrorObserver()
		ow.AddObserver('ErrorEvent', self.eo)
		ow.AddObserver('WarningEvent', self.eo)


	def __init__(self):
		self.setupGlobalWarningHandling()
		self.classTree = ClassTree(self.eo, "categories.txt", "categoriesMapping.txt")


	def getVtkObjectOutputPort(self, node):
		return node.vtkInstanceCall('GetOutputPort')


	def updateVtkObject(self, node):
		node.vtkInstanceCall('Update')


	'''
	Generates a wrapped Python VTK objects in a PipelineObject, which then exposes the 
	methods for introspective calls. It returns the PyObject itself. For the C++ object
	underlying, use the utility function `getAddress`.
	'''
	def createVtkObject(self, objectName):
		return self.classTree.getTreeObjectByName(objectName).createNode()


	# TODO LOW: move to the TreeObject class
	def getVtkObjectDescriptor(self, node):
		cls = node.vtkInstance.__class__
		methods = getSubclassMethods(cls)
		attributes = [m[3:] for m in methods if m.startswith('Set')]
		get_methods = [m for m in [m for m in methods if m.startswith('Get')] if m[3:] in attributes]

		desc = []

		for m in get_methods:
			method = getattr(node.vtkInstance, m)
			try:
				ret = method()
				if not ret == None and isinstance(ret, collections.Sequence) and not isinstance(ret, str):
					mlen = len(ret)
					if mlen > 0:
						mtype = type2name(ret[0]) + str(mlen);
						desc.append((m[3:], mtype))
				else:
					desc.append((m[3:], type2name(ret)))
			except (TypeError):
				pass

		print(desc)
		return desc


	def getVtkObjectAttribute(self, node, attribute):
		return str(node.vtkInstanceCall("Get" + attribute))


	def setVtkObjectAttribute(self, node, attribute, newValue):
		methodName = "Set" + attribute
		valueType, value = newValue.split("::", 1)
		if valueType == "int":
			node.callSetValueIntMethod(methodName, int(value))
			print(node.vtkInstanceCall("Get" + attribute))
		elif valueType == "dbl":
			node.callSetValueFloatMethod(methodName, float(value))
		elif valueType == "str":
			node.callSetValueStringMethod(methodName, value)
		elif valueType == "bool":
			node.vtkInstanceCall(methodName, bool(value))
		elif valueType == "dbl3":
			v1, v2, v3 = value.split(",", 2)
			node.vtkInstanceCall(methodName, (float(v1), float(v2), float(v3)))
		else:
			print("not recognised type", valueType, "with value", value)


	def vtkInstanceCall(self, node, methodName, *args, **kwargs):
		return node.vtkInstanceCall(methodName, *args, **kwargs)


	def deleteVtkObject(self, node):
		del node


def type2name(t):
	if isinstance(t, int):
		return "int"
	elif isinstance(t, float):
		return "dbl"
	elif isinstance(t, str):
		return "str"
	elif isinstance(t, bool):
		return "bool"
	else:
		return None


def is_abstract(cls):
	try:
		_ = cls()
		return False
	except (TypeError, NotImplementedError):
		return True


def getSubclassMethods(cls):
	methods = set(dir(cls()))
	superclasses = [b for b in cls.__bases__ if not is_abstract(b)]
	if superclasses:
		return list(methods.difference(*(dir(base()) for base in superclasses)))
	else:
		return list(methods)
