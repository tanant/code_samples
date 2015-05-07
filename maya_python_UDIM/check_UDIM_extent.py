'''
from https://groups.google.com/forum/#!topic/python_inside_maya/CceOUNDo-7k

Thought I'd just target the uv query to see if that can be sped up any, or
where a bottleneck would be (can't imagine it's converting UV to UDIM
coordinates, that's almost a one-liner).

So yes, taking three approaches, PyMEL/getUVs feels manageable out to say,
2-300k UVs, but does feel sluggish at 4-500k. Maya.cmds is just diabolical -
that's also because I'm not very good with it and I'm 100% sure i'm doing it a
horrible way, but the API is fine through to a million at which point I figured
it was Fast Enough.

One thing I'd point out with my API approach - I've just done the bare minimum
to get a result - I'd trust PyMEL over my implementation of UV grabbing until I
did some more testing, wouldn't be surprised if there are issues I'm glossing
over in this test scenario that PyMEL handles correctly, and I don't handle at
all.

Just using a polysphere with 1000x200 subdivs to give me ~200k UVs, my numbers
were roughly 4s for maya.cmds, 0.4s for pymel, and 0.001 for the API. The API
approach scales decently as well, while I could've sworn pymel didn't have a
linear growth pattern. (my local machine, Maya 2013x64/SP2)

checking pSphereShape1 for 1 iterations
maya.cmds    : 3.95910561149
PyMel        : 0.344888150405
OpenMaya/API : 0.00120376245754
---------------
(for 201199 uvs):
---------------
DONE

The figures above are just for grabbing the UVs and not processing them, but
depending on what cases you want to trap, the UV/UDIM thing didn't feel
expensive at the ranges you were quoting (out to 500k) using my naive approach
of testing every coordinate and building up a set, so I didn't investigate that
too much further. If you wanted to do things by-shell i have a feeling API is
going to be where you want to head.

-Anthony

(Here's my code dump, scuse the mess but you should be able to execute the
thing as it stands to replicate my results once you create a polySphere or
similar to play with)
'''


import timeit
mesh_string = 'pSphereShape1'
timer_iterations = 1

# pymel version
import pymel.core as pm


def pymel_getuvs(mesh_string):
    """return a list of two lists, idx 0 is U, idx 1 is V"""
    mesh = pm.PyNode(mesh_string)
    uvs = mesh.getUVs()
    return uvs



# mc version
import maya.cmds as mc


def mc_getuvs(mesh_string):
    """return a list of (u,v) tuples"""
    x = mc.getAttr(
        mesh_string + '.uvpt', multiIndices=True)  # determine UV idxs
    uvs = []
    for i in x:
        # probably quite a naive way to iterate through an object's UVs-I don't
        # use maya.cmds much
        uvs += mc.getAttr('{mesh_string}.uvpt[{idx}]'.format(idx=i,
                                                             mesh_string=mesh_string))
    return uvs



# OpenMaya version
import maya.OpenMaya as om


def om_getuvs(mesh_string):
    """return a list of two lists, idx 0 is U, idx 1 is V"""
    # Y'know it's really weird to think of malloc-ing in python..
    selection_list = om.MSelectionList()
    mObject_holder = om.MObject()
    u = om.MFloatArray()
    v = om.MFloatArray()
    function_set = om.MFnMesh()

    # see https://groups.google.com/forum/#!topic/python_inside_maya/usFLgzJBrpM/discussion
    # for a note on why this, instead of a flat selection_list.add.
    om.MGlobal.getSelectionListByName(mesh_string, selection_list)
    iterator = om.MItSelectionList(selection_list)
    iterator.getDependNode(mObject_holder)
    function_set.setObject(mObject_holder)
    function_set.getUVs(u, v)
    return [u, v]


def uv_to_udim(u, v):
    '''return UDIM tile corresponding to UV coord

    NOTE:very poorly defined response on edges..
    '''
    import math
    return int(1000 + (math.floor(u) + 1) + (math.floor(v) * 10))


# the zip function itself is a bit slow
def equivalence(pymel_result, mc_result, om_result):
    pm_uv = zip(pymel_result[0], pymel_result[1])
    om_uv = zip(om_result[0], om_result[1])
    for i, x in enumerate(pm_uv):
        if pm_uv[i] != om_uv[i]:
            raise ValueError('pm != om')
        elif pm_uv[i] != mc_result[i]:
            raise ValueError('pm != mc')
    print "OK"

print "checking {mesh} for {it} iterations".format(mesh=mesh_string,
                                                   it=timer_iterations)

print "maya.cmds    :",
t = timeit.Timer(stmt=lambda: mc_getuvs(mesh_string))
print t.timeit(timer_iterations)

print "PyMel        :",
t = timeit.Timer(stmt=lambda: pymel_getuvs(mesh_string))
print t.timeit(timer_iterations)

print "OpenMaya/API :",
t = timeit.Timer(stmt=lambda: om_getuvs(mesh_string))
print t.timeit(timer_iterations)

print "---------------"
print "(for {n} uvs)".format(n=len(om_getuvs(mesh_string)[0]))
print "---------------"
print "DONE"

uvs = om_getuvs(mesh_string)
udim_list = set()
for x in xrange(0, len(uvs[0])):
    udim_list.add(uv_to_udim(uvs[0][x], uvs[1][x]))
print udim_list
