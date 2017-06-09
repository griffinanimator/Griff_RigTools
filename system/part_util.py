__author__ = 'rgriffin'

"""
Utilities for creating and editing layout parts
"""

from pymel.core import *
from rigging.utilities import control_util
reload(control_util)

from rigging.utilities import asset_util
reload(asset_util)
import os
class Create_Part():
    def __init__(self, prefix, sections, side, ismirror, options, classname, title, overrides):

        return
    
    def createPartChain(self, s, i):
        childlist = []
        # Dictionary to store created nodes for asset add
        if self.overrides:
            nameprefix = self.overrides[i][s][0] + '__' + self.side[1] + '_' + self.part_info['instance']
        else:
            nameprefix = self.part_info['udname'] + str(s) + '__' + self.side[1] + '_' + self.part_info['instance']

        # Create the part control node.
        ntype = 'customLoc'
        node = 'dfSphere'
        name = nameprefix + '_Layout_CTRL'
        options = [['.colorR', 1], ['.colorG', 1], ['.colorB', 0], ['.transparency', .5], ['.drawOver', 1],
                   ['.drawType', 1], ['.radius', .5]]
        groups = None
        lockattrs = ['.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
        layoutcontrol = control_util.createControl(ntype, node, name, options, groups, lockattrs)
        self.asset_nodes['layoutcontrol' + str(s)] = [layoutcontrol, 'transform']
        childlist.append(layoutcontrol[0])
        if 'layoutcontrol' in self.part_info:
            self.part_info['layoutcontrol'].append(layoutcontrol)
        else:
            self.part_info['layoutcontrol'] = layoutcontrol

        select(d=True)
        agrp = group(n=nameprefix + '_CTRL_AIM')
        parent(agrp, layoutcontrol[2])

        if self.overrides:
            xform(layoutcontrol[0], ws=True, t=self.overrides[i][s][1])
        else:
            xform(layoutcontrol[0], ws=True, t=[s, 0.0, 0.0])

        # Create the orient control node.
        ntype = 'customLoc'
        node = 'orientLoc'
        name = nameprefix + '_LYT_ORIENT_CTRL'
        self.options = [['.size', 1]]
        groups = ['AIM']
        lockattrs = ['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
        orientcontrol = control_util.createControl(ntype, node, name, self.options, groups, lockattrs)
        self.asset_nodes['orientcontrol' + str(s)] = [orientcontrol, 'transform']
        childlist.append(orientcontrol[0])
        if 'orientcontrol' in self.part_info:
            self.part_info['orientcontrol'].append(orientcontrol)
        else:
            self.part_info['orientcontrol'] = orientcontrol

        if self.overrides:
            from scripts.common.math import vector_util
            if s != self.sections[1] - 1:
                midpos = vector_util.averageFloatLists([self.overrides[i][s][1], self.overrides[i][s + 1][1]])
                xform(orientcontrol[0], ws=True, t=midpos)
            else:
                xform(orientcontrol[0], ws=True,
                      t=[self.overrides[i][s][1][0] + .5, self.overrides[i][s][1][1] + .5, self.overrides[i][s][1][2] + .5])
        else:
            xform(orientcontrol[0], ws=True, t=[s + 0.5, 0.0, 0.0])

        # Create the part end control node.
        ntype = 'customLoc'
        node = 'dfSphere'
        name = nameprefix + '_LYT_END_CTRL'
        self.options = [['.colorR', 1], ['.colorG', 1], ['.colorB', 0], ['.transparency', .5], ['.drawOver', 1],
                   ['.drawType', 1], ['.radius', .25]]
        groups = None
        lockattrs = ['.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
        endcontrol = control_util.createControl(ntype, node, name, self.options, groups, lockattrs)
        self.asset_nodes['endcontrol' + str(s)] = [endcontrol, 'transform']
        childlist.append(endcontrol[0])

        if self.overrides:
            if s != self.sections[1] - 1:
                xform(endcontrol[0], ws=True, t=self.overrides[i][s + 1][1])
            else:
                xform(endcontrol[0], ws=True,
                      t=[self.overrides[i][s][1][0] + 1, self.overrides[i][s][1][1] + 1, self.overrides[i][s][1][2] + 1])
        else:
            xform(endcontrol[0], ws=True, t=[s + 1, 0.0, 0.0])

        # Hide the end control if more than one part
        if s >= 1:
            setAttr(self.asset_nodes['endcontrol' + str(s - 1)][0][2] + '.visibility', 0)
            parent(self.asset_nodes['endcontrol' + str(s - 1)][0][2], layoutcontrol[2])

        # Create a joint
        select(d=True)
        pjnt = joint(n=nameprefix + '_LYT_JNT')
        parent(pjnt, agrp)
        childlist.append(pjnt)

        # Point constraint orient control
        pointConstraint(endcontrol[2], layoutcontrol[2], orientcontrol[3][0], mo=True)

        # point constrain the joint
        pointConstraint(layoutcontrol[2], pjnt, mo=False)

        # aim constraint ctrl aim
        aimConstraint(endcontrol[2], agrp, mo=False, u=[0.0, 1.0, 0.0], aim=[0.1, 0.0, 0.0], wut="scene")

        # Hide the joint
        setAttr(pjnt + '.drawStyle', 2)

        # Connect joint attrs
        connectAttr(agrp + '.rotate', pjnt + '.jointOrient')
        connectAttr(pjnt + '.jointOrient', orientcontrol[3][0] + '.rotate')

        # Publish nodes to the asset
        controlnodes = []
        for a in self.asset_nodes:
            controlnodes.append([self.asset_nodes[a][0][2], self.asset_nodes[a][1]])

        self.part_info['childlist'] = childlist

        nameprefix = self.part_info['udname'] + '__' + self.side[1] + '_' + self.part_info['instance']
        if objExists(nameprefix + '_LYT_CTRL_GRP') == True:
            self.part_info['mctrlgrp'] = nameprefix + '_LYT_CTRL_GRP'
        else:
            self.part_info['mctrlgrp'] = group(n=nameprefix + '_LYT_CTRL_GRP', em=True)

        for c in self.part_info['childlist']:
            parent(c, self.part_info['mctrlgrp'])

        return self.part_info

    def mirrorPart(self):
        # Make a mirror part if mirror checked.
        if self.side[1] == 'C':
            print "You can't mirror a center part"
        else:
            dupnodesets = duplicatePart(self.part_info['partasset'])

            outnodes = []
            ctrltypes = ('clCircle', 'dfSphere')
            for p in dupnodesets:
                if nodeType(p[0]) == 'transform':
                    pshp = PyNode(p[0]).getShape()
                    if nodeType(pshp) in ctrltypes:
                        if '_Layout' in PyNode(p[0]).name() or 'LYT_ROOT_CTRL' in PyNode(
                                p[0]).name() or 'LYT_END_CTRL' in PyNode(p[0]).name():
                            outnodes.append(p)

            import scripts.tools.rigging.utilities.rig_util as ru
            reload(ru)
            for nodes in outnodes:
                symcon = ru.connectThroughSymmetry(nodes[0], nodes[1], nodes[1])
                if symcon:
                    container(self.part_info['partasset'], edit=True, an=symcon)
            self.part_info['mirrorpart'] = dupnodesets



def duplicatePart(part):
    returnnodes = []

    namespace(set=':')
    if namespace(exists=':tmp') == True:
        namespace(rm='tmp', f=True)
    namespace(add='tmp')
    namespace(set='tmp')
    dupnodes = duplicate(part, un=True)
    try:
        setAttr(dupnodes[0] + '.side', 'R')
    except: pass

    for n in dupnodes:
        org = n.replace('tmp:', '')
        name = 'NONE'
        if '__L_' in str(n):
            name = n.replace('__L', '__R')
            try:
                setAttr(dupnodes[0] + '.side', 'R')
            except:
                pass
        if '__R_' in str(n):
            name = str(n).replace('__R', '__L')
            try:
                setAttr(dupnodes[0] + '.side', 'L')
            except:
                pass
        name = str(name).partition(':')
        namespace(set=':')
        try:
            n.rename(name[2])
        except: pass

        returnnodes.append([org, name[2]])
    if namespace(exists=':tmp') == True:
        namespace(force=True, mv=[':tmp', ':'])
        namespace(rm=':tmp', f=True)

    return(returnnodes)







