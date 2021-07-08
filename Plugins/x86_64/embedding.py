import vtk

import inspect
from buildPipeline import build

import time


start = time.perf_counter();
build(False)
end = time.perf_counter();

print ("ClassTree generation time: %ss" % (end - start))

print ("Object was %s." % precreated_object)

precreated_object.set_name("edited by Python")