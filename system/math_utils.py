from pymel.core import *
import maya.cmds as cmds
import maya.api.OpenMaya as om
import math

def matchTwistAngle(twistAttribute, ikJoints, targetJoints):
    currentVector = []
    targetVector = []

    currentVector = calculateTwistVector(ikJoints[0], ikJoints[1], ikJoints[len(ikJoints)-1])
    targetVector = calculateTwistVector(targetJoints[0], targetJoints[1], targetJoints[len(targetJoints)-1])

    targetVector = normaliseVector(targetVector)
    currentVector = normaliseVector(currentVector)

    offsetAngle = calculateAngleBetweenNormalisedVectors(targetVector, currentVector)

    finalOffset = offsetAngle*-1
    finalOffset = offsetAngle

    return finalOffset

def calculateTwistVector(startJoint, secondJoint, endJoint, *args):
    a = xform(startJoint, q=True, ws=True, t=True)
    endPos = xform(endJoint, q=True, ws=True, t=True)

    b = [endPos[0] - a[0], endPos[1] - a[1], endPos[2] -a[2]]
    b = normaliseVector(b)

    p = xform(secondJoint, q=True, ws=True, t=True)

    p_minus_a = [p[0]-a[0], p[1]-a[1], p[2]-a[2]]
    p_minus_a__dot__b = p_minus_a[0]*b[0] + p_minus_a[1]*b[1] + p_minus_a[2]*b[2]

    p_minus_a__dot__b__multiply_b = [p_minus_a__dot__b * b[0], p_minus_a__dot__b * b[1], p_minus_a__dot__b * b[2]]

    q = [a[0] + p_minus_a__dot__b__multiply_b[0], a[1] + p_minus_a__dot__b__multiply_b[1], a[2] + p_minus_a__dot__b__multiply_b[2]]

    twistVector = [p[0] - q[0], p[1] - q[1], p[2] - q[2]]

    return twistVector

def normaliseVector(vector, *args):
    from math import sqrt
    returnVector = list(vector)

    vectorLength = sqrt( returnVector[0]*returnVector[0] + returnVector[1]*returnVector[1] + returnVector[2]*returnVector[2])

    if vectorLength != 0:
        returnVector[0] /= vectorLength
        returnVector[1] /= vectorLength
        returnVector[2] /= vectorLength
    else:
        returnVector[0] = 1.0
        returnVector[1] = 0.0
        returnVector[2] = 0.0

    return returnVector

def calculateAngleBetweenNormalisedVectors(VectA, VectB, *args):
    from math import acos, degrees

    dotProduct = VectA[0]*VectB[0] + VectA[1]*VectB[1] + VectA[2]*VectB[2]\

    if dotProduct <= -1.0:
        dotProduct = -1.0
    elif dotProduct >= 1.0:
        dotProduct = 1.0

    radians = acos(dotProduct)

    return degrees(radians)


def calculateDistance(a, b, attr, value):

    cmds.setAttr(attr, value)

    ikLocPos = cmds.xform(a, q=True, ws=True, t=True)
    ikLocVec = OpenMaya.MVector(ikLocPos[0], ikLocPos[1], ikLocPos[2])

    fkLocPos = cmds.xform(b, q=True, ws=True, t=True)
    fkLocVec = OpenMaya.MVector(fkLocPos[0], fkLocPos[1], fkLocPos[2])

    return (ikLocVec - fkLocVec).length()

def getLocalVecToWorldSpace(node, vec=om.MVector.kXaxisVector):
    matrix = om.MGlobal.getSelectionListByName(node).getDagPath(0).inclusiveMatrix()
    vec = (vec * matrix).normal()
    return vec


def axisVectorColinearity(node, vec):
    vec = om.MVector(vec)

    x = getLocalVecToWorldSpace(node, vec=om.MVector.kXaxisVector)
    y = getLocalVecToWorldSpace(node, vec=om.MVector.kYaxisVector)
    z = getLocalVecToWorldSpace(node, vec=om.MVector.kZaxisVector)

    #return the dot products
    return {'x': vec*x, 'y':vec*y, 'z':vec*z}


def averageFloatLists(poslist):
    print poslist
    poslen = len(poslist)
    tmpflt = [0.0, 0.0, 0.0]
    for each in poslist:
        tmpflt = [x + y for x, y in zip(each, tmpflt)]
    averagex = tmpflt[0] / poslen
    averagey = tmpflt[1] / poslen
    averagez = tmpflt[2] / poslen
    return(averagex, averagey, averagez)

def printInverseMatrix():
    import pymel.core as pm
    invmtx =  pm.ls(sl=True)[0].transformationMatrix().inverse()
    print invmtx


def normaliseVector(vector):
    from math import sqrt
    returnVector = list(vector)

    vectorLength = sqrt( returnVector[0]*returnVector[0] + returnVector[1]*returnVector[1] + returnVector[2]*returnVector[2])

    if vectorLength != 0:
        returnVector[0] /= vectorLength
        returnVector[1] /= vectorLength
        returnVector[2] /= vectorLength
    else:
        returnVector[0] = 1.0
        returnVector[1] = 0.0
        returnVector[2] = 0.0

    return returnVector

def calculateAngleBetweenNormalisedVectors(VectA, VectB):
    from math import acos, degrees

    dotProduct = VectA[0]*VectB[0] + VectA[1]*VectB[1] + VectA[2]*VectB[2]\

    if dotProduct <= -1.0:
        dotProduct = -1.0
    elif dotProduct >= 1.0:
        dotProduct = 1.0

    radians = acos(dotProduct)
    return degrees(radians)


def matchTwistAngle(twistAttribute, ikJoints, targetJoints):
    #forceSceneUpdate()

    currentVector = []
    targetVector = []

    # Get the current and target vector
    # Is this a single or multiple joint segment?
    if len(ikJoints) <= 2:
        currentVector = calculateTwistVectorForSingleJointChain(ikJoints[0])
        targetVector = calculateTwistVectorForSingleJointChain(targetJoints[0])
    else:
        currentVector = calculateTwistVector(ikJoints[0], ikJoints[1], ikJoints[len(ikJoints)-1])
        targetVector = calculateTwistVector(targetJoints[0], targetJoints[1], targetJoints[len(targetJoints)-1])

    targetVector = normaliseVector(targetVector)
    currentVector = normaliseVector(currentVector)

    offsetAngle = calculateAngleBetweenNormalisedVectors(targetVector, currentVector)

    cmds.setAttr(twistAttribute, cmds.getAttr(twistAttribute)+offsetAngle)

    if len(ikJoints) <= 2:
        currentVector = calculateTwistVectorForSingleJointChain(ikJoints[0])
    else:
        currentVector = calculateTwistVector(ikJoints[0], ikJoints[1], ikJoints[len(ikJoints)-1])

    currentVector = normaliseVector(currentVector)

    newAngle = calculateAngleBetweenNormalisedVectors(targetVector, currentVector)
    if newAngle > 0.1:
        offsetAngle *= -2
        cmds.setAttr(twistAttribute, cmds.getAttr(twistAttribute)+offsetAngle)



def calculateTwistVectorForSingleJointChain(startJoint):
    tempLocator = cmds.spaceLocator()[0]

    cmds.setAttr(tempLocator+".visibility", 0)

    cmds.parent(tempLocator, startJoint, relative=True)
    cmds.setAttr(tempLocator+".translateZ", 5.0)

    jointPos = cmds.xform(startJoint, q=True, ws=True, translation=True)
    locatorPos = cmds.xform(tempLocator, q=True, ws=True, translation=True)

    twistVector = [ locatorPos[0]-jointPos[0], locatorPos[1]-jointPos[1], locatorPos[2]-jointPos[2]]

    cmds.delete(tempLocator)

    return twistVector

def calculateTwistVector(startJoint, secondJoint, endJoint):
    a = cmds.xform(startJoint, q=True, ws=True, t=True)
    endPos = cmds.xform(endJoint, q=True, ws=True, t=True)

    b = [endPos[0] - a[0], endPos[1] - a[1], endPos[2] -a[2]]
    b = normaliseVector(b)

    p = cmds.xform(secondJoint, q=True, ws=True, t=True)

    p_minus_a = [p[0]-a[0], p[1]-a[1], p[2]-a[2]]
    p_minus_a__dot__b = p_minus_a[0]*b[0] + p_minus_a[1]*b[1] + p_minus_a[2]*b[2]

    p_minus_a__dot__b__multiply_b = [p_minus_a__dot__b * b[0], p_minus_a__dot__b * b[1], p_minus_a__dot__b * b[2]]

    q = [a[0] + p_minus_a__dot__b__multiply_b[0], a[1] + p_minus_a__dot__b__multiply_b[1], a[2] + p_minus_a__dot__b__multiply_b[2]]

    twistVector = [p[0] - q[0], p[1] - q[1], p[2] - q[2]]

    return twistVector

def findPoleVectorPosition(joints):
    from maya import OpenMaya
    if len(joints) != 3:
        return
    else:
        start = xform(joints[0], q=1, ws=1, t=1)
        mid = xform(joints[1], q=1, ws=1, t=1)
        end = xform(joints[2], q=1, ws=1, t=1)
        startV = OpenMaya.MVector(start[0], start[1], start[2])
        midV = OpenMaya.MVector(mid[0], mid[1], mid[2])
        endV = OpenMaya.MVector(end[0], end[1], end[2])
        startEnd = endV - startV
        startMid = midV - startV
        dotP = startMid * startEnd
        proj = float(dotP) / float(startEnd.length())
        startEndN = startEnd.normal()
        projV = startEndN * proj
        arrowV = startMid - projV
        arrowV *= 5
        finalV = arrowV + midV
        return [finalV.x, finalV.y, finalV.z]