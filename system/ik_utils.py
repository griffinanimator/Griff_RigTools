from pymel.core import *

from math import vector_util
reload(vector_util)


def scStretchyIk(joints, udname, control, axis, *args):
    # Empty list to store nodes generated in scStretchyIk
    ikNodes = []

    select(d=True)

    sjnt = joints[0]
    ejnt = joints[1]
    sjPos = xform(sjnt, q=True, t=True, ws=True)
    ejPos = xform(ejnt, q=True, t=True, ws=True)

    # Create the ik solver
    iksol = ikSolver(st='ikRPsolver', ep=1.0, n=udname + '_ikSolver' )
    ikH = ikHandle(n=udname + '_ikH', sj=sjnt, ee=ejnt, sol=iksol, w=1)
    setAttr(ikH[0] +'.visibility', 0)

    # Stretch ----------------------------------------------------------
    mdEStretch = shadingNode("multiplyDivide", asUtility=True, n=udname + '_endStretch_MDIV')
    select(d=True)

    # NOTE: I need to change disDim transform name
    lctrR = spaceLocator(n=udname + '_startDistance_LCTR')
    xform(lctrR, ws=True, t=sjPos)
    lctrE = spaceLocator(n=udname + '_endDistance_LCTR')
    xform(lctrE, ws=True, t=ejPos)
    distanceDimension(sp=(sjPos), ep=(sjPos))

    rename('distanceDimension1', udname + '_distance_DISDIM')
    setAttr(udname + '_distance_DISDIM.visibility', 0)

    con = listConnections(udname + '_distance_DISDIMShape.endPoint', p=True)[0]
    if con != None:
        disconnectAttr(con, udname + '_distance_DISDIMShape.endPoint')
    con = listConnections(udname + '_distance_DISDIMShape.startPoint', p=True)[0]
    if con != None:
        disconnectAttr(con, udname + '_distance_DISDIMShape.startPoint')

    connectAttr(lctrR + 'Shape.worldPosition[0]', udname + '_distance_DISDIMShape.startPoint', f=True)
    connectAttr(lctrE + 'Shape.worldPosition[0]', udname + '_distance_DISDIMShape.endPoint', f=True)


    # Determine the length of the joint chain in default position
    endLen = getAttr(joints[1] + '.tx')

    #connectAttr("%s.stretch" % control, mdEStretch + '.input2X')
    setAttr(mdEStretch + '.input2X', 1)
    setAttr(mdEStretch + '.operation', 2)

    #Finally, we output our new values
    connectAttr(udname + '_distance_DISDIMShape.distance', mdEStretch + '.input1X')
    connectAttr(mdEStretch + '.outputX', ejnt + axis)

    # Set locator visibility to off
    setAttr(lctrE + '.visibility', 0)
    setAttr(lctrR + '.visibility', 0)

    pointConstraint(control, ikH[0], mo=True)
    parent(lctrE, control)

    ikNodes = [ikH[0], lctrR, lctrE, iksol, mdEStretch, udname + '_distance_DISDIM']

    return ikNodes





