import maya.cmds as cmds
from pymel.core import *
import json
import os
import system.utils as utils
import system.math_utils as mu
import system.data_utils as du
reload(du)
reload(utils)

class Rig():
    def __init__(self, uiinfo, numjnts):
        self.uiinfo = uiinfo
        self.numjnts = numjnts
        self.datapath = uiinfo['data_path']
        self.modFile = uiinfo['modfile']
        self.moduleInstance = uiinfo['modclass']

        # Dictionary to store rig specific data
        # rig_info stores all data needed to build the rig.
        self.rig_info = {}

        # declare some default values to override later
        self.rig_info['partnum'] = 1

        # Use our readJson function
        data = utils.readJson(self.datapath)
        # Load the json into a dictionary
        # module_info stores all the data needed to build the layout object
        self.module_info = json.loads(data)

    def install(self):
        print 'In Rig Install'
        self.collectRigData()

        if self.rig_info:
            print "Ready for Install"
        else:
            return

    def part(self):
        partlist = self.findPartsInScene()
        # Find the instance of the object
        self.module_info['partnum'] = str(
            utils.findHighestTrailingNumber(partlist, self.module_info['rootname'] + self.uiinfo['side']))

        self.module_info['instance'] = self.uiinfo['side'] + self.module_info['partnum'] + '_'

        self.module_info['udname'] = self.module_info['rootname'] + self.module_info['instance']

        # Create a master asset
        if cmds.objExists(self.module_info['rootname'] + self.module_info['instance'] + 'ASSET') == True:
            # NOTE:  This would be a good place to further check for asset contents
            self.module_info['mainasset'] = self.module_info['rootname'] + self.module_info['instance'] + 'ASSET'
        else:
            self.module_info['mainasset'] = cmds.container(
                n=self.module_info['rootname'] + self.module_info['instance'] + 'ASSET')


        # Create a layout asset
        self.module_info['layoutasset'] = cmds.container(
            n=self.module_info['rootname'] + self.module_info['instance'] + 'LAYOUT')
        # Add the layout to the main
        cmds.container(self.module_info['mainasset'] , edit=True, an=self.module_info['layoutasset'] )

        # Add attributes to the asset
        self.addAssetAttrs()

    def layout(self):
        self.layout_nodes={}
        # Initialize the part
        self.part()

        cmds.namespace(set=':')
        for n in range(self.numjnts - 1):
            self.createPartChain(n)

        for key, value in self.layout_nodes.iteritems():
            flat =  du.traverse(value)
            for f in flat:
                container(self.module_info['layoutasset'], edit=True, an=f)

        return

    def createPartChain(self, inst):
        # Dictionary to store created nodes for asset add

        # Create the part control node.
        layoutcontrol = self.createControl([self.module_info['positions'][inst], self.module_info['rootname']+'_'+str(inst)+'_LytRoot', 'sphereControl.ma'])

        self.layout_nodes.setdefault('layoutcontrol', []).append(layoutcontrol)

        if 'layoutcontrol' in self.layout_nodes:
            self.layout_nodes['layoutcontrol'].append(layoutcontrol)
        else:
            self.layout_nodes['layoutcontrol'] = layoutcontrol

        select(d=True)
        agrp = group(n='tmp' + '_CTRL_AIM')
        parent(agrp, layoutcontrol[1])
        xform(agrp, ws=True, t=self.module_info['positions'][inst])

        # Create the orient control node.
        orientcontrol = self.createControl([self.module_info['positions'][inst], self.module_info['rootname']+'_'+str(inst)+'_LytOrient', 'coordinateControl.ma'])
        self.layout_nodes.setdefault('orientcontrol', []).append(orientcontrol)
        #self.layout_nodes['orientcontrol' + str(inst)] = [orientcontrol, 'transform']

        if 'orientcontrol' in self.layout_nodes:
            self.layout_nodes['orientcontrol'].append(orientcontrol)
        else:
            self.layout_nodes['orientcontrol'] = orientcontrol

        #xform(orientcontrol[0], ws=True, t=[inst + 0.5, 0.0, 0.0])

        # Create the part end control node.
        endcontrol = self.createControl([self.module_info['positions'][inst + 1], self.module_info['rootname']+'_'+str(inst)+'_LytEnd', 'sphereControl.ma'])
        self.layout_nodes.setdefault('endcontrol', []).append(endcontrol)
        #self.layout_nodes['endcontrol'+ str(inst)] = [endcontrol, 'transform']

        #xform(endcontrol[0], ws=True, t=[inst + 1, 0.0, 0.0])

        # Hide the end control if more than one part
        if inst >= 1:
            setAttr(self.layout_nodes['endcontrol'][inst - 1][1] + '.visibility', 0)
            parent(self.layout_nodes['endcontrol'][inst - 1][0], layoutcontrol[1])

        # Create a joint
        select(d=True)
        pjnt = joint(n='tmp' + '_LYT_JNT')
        self.layout_nodes.setdefault('partjoint', []).append(pjnt)
        parent(pjnt, layoutcontrol[1])

        # Point constraint orient control
        pointConstraint(endcontrol[1], layoutcontrol[1], orientcontrol[0], mo=True)

        # aim constraint ctrl aim
        aimConstraint(endcontrol[1], agrp, mo=False, u=[0.0, 1.0, 0.0], aim=[0.1, 0.0, 0.0], wut="scene")

        # Hide the joint
        setAttr(pjnt + '.drawStyle', 2)

        makeIdentity(pjnt, apply=True)
        # point constrain the joint
        pointConstraint(layoutcontrol[1], pjnt, mo=False)
        # Connect joint attrs
        connectAttr(agrp + '.rotate', pjnt + '.jointOrient')
        connectAttr(pjnt + '.jointOrient', orientcontrol[0] + '.rotate')


    def addAssetAttrs(self):
        attrlist = (['modclass', self.module_info['modclass']],
                    ['partnum', self.module_info['partnum']],
                    ['rootname',self.module_info['rootname']],
                    ['instance', self.module_info['instance']],
                    ['mainasset', self.module_info['mainasset']],
                    ['layoutasset', self.module_info['layoutasset']])

        for a in attrlist:
            if cmds.attributeQuery(a[0], node=self.module_info['mainasset'], ex=True):
                pass
            else:
                cmds.addAttr(self.module_info['mainasset'], sn=a[0], dt='string', k=False)
                cmds.setAttr(self.module_info['mainasset'] + '.' + a[0], a[1], type='string')

    def queryAssetAttrs(self):
        attrlist = ('modclass',
                    'rootname',
                    'instance',
                    'mainasset',
                    'layoutasset')
        for a in attrlist:
            if cmds.attributeQuery(a, node=self.rig_info['mainasset'], ex=True):
                val = cmds.getAttr(self.rig_info['mainasset'] + '.' + a)
                self.rig_info[a] = val

    @staticmethod
    def findPartsInScene():
        # find all part of type in the scene.
        assetlist = cmds.ls(type='container')

        partlist = []
        for a in assetlist:
            if a.endswith('ASSET'):
                partlist.append(a)
        return partlist

    def ui(self):
        return

    def collectRigData(self):
        """
        Function used to collect the data we need to build the rig
        :return:
        """

        self.queryPartAsset()
        self.queryAssetAttrs()

        if self.rig_info['layoutasset']:
            # We identified the part.
            # get the positions of the joints
            for item in cmds.container(self.rig_info['layoutasset'], q=True, nl=True):
                if cmds.nodeType(item) == 'joint' and item.endswith('LYT_JNT') == True:
                    pos = cmds.xform(item, q=True, ws=True, t=True)
                    self.rig_info.setdefault('positions', []).append(pos)
                    rot = cmds.xform(item, q=True, ws=True, ro=True)
                    self.rig_info.setdefault('rotations', []).append(rot)

            self.rig_info['instance'] = cmds.getAttr(self.rig_info['mainasset'] + '.instance')

        else:
            raise RuntimeError('No Valid Layout Selected.')

    def queryPartAsset(self):
        """
        function used to find the main asset
        :return:
        """

        sel = cmds.ls(sl=True)

        if sel:
            # Navigate up to see if the selection is an asset or a child of one.
            parentcon = cmds.container(q=True, fc=sel[0])
            print parentcon
            if parentcon:
                # Look for the main asset
                maincon = cmds.container(q=True, fc=parentcon)
                if maincon:
                    # Look for identifier
                    if cmds.attributeQuery('modclass', node=maincon, ex=True):
                        # We found an asset
                        self.rig_info['mainasset'] = maincon

            elif cmds.nodeType(sel[0]) == 'container':
                maincon = cmds.container(q=True, fc=sel[0])
                if maincon:
                    # Look for identifier
                    if cmds.attributeQuery('modclass', node=maincon, ex=True):
                        # We found an asset
                        self.rig_info['mainasset'] = maincon

                else:
                    #We must have selected the main asset
                    if cmds.attributeQuery('modclass', node=sel[0], ex=True):
                        # We found an asset
                        self.rig_info['mainasset'] = maincon

            else:
                raise RuntimeError('No Valid Layout Found.')

            print self.rig_info


    def createJoint( self, name, position, rotation, instance, *args):
        # Use a list comprehension to build joints.
        jnt_list = []
        cmds.select(d=True)
        for i in range(len(name)-1):
            j = cmds.joint(n=name[i].replace('_s_', instance))
            xform(j, ws=True, ro=rotation[i])
            xform(j, ws=True, t=position[i])
            makeIdentity(j, apply=True)
            jnt_list.append(j)

        return (jnt_list)

    def createControl(self, ctrlinfo):

        # Create ik control
        # Get ws position of the joint
        pos = ctrlinfo[0]
        # Create circle control object
        ctrl_file = os.environ["DATA_PATH"] + '/controls/' + ctrlinfo[2]
        # Import a control object
        cmds.file(ctrl_file, i=True)
        ctrl = ctrlinfo[1]
        ctrlgrp = ctrlinfo[1]+'_grp'
        if cmds.objExists('grp_control') == True:
            cmds.rename('grp_control', ctrlgrp)
            cmds.rename('control', ctrl)
        # Move the group to the joint
        if len(pos)>3:
            cmds.xform(ctrlgrp, m=pos, ws=True)
        else:
            cmds.xform(ctrlgrp, t=pos, ws=True)
        control_info = [ctrlgrp, ctrl]
        return (control_info)

    def connectThroughBC(self, parentsA, parentsB, children, switchattr, instance, *args):
        constraints = []
        for j in range(len(children)):
            switchPrefix = children[j].partition('_')[0]
            bcNodeT = cmds.shadingNode("blendColors", asUtility=True, n='bcNodeT_switch_' + self.rig_info['instance'] + switchPrefix)
            if switchattr:
                cmds.connectAttr(switchattr, bcNodeT + '.blender')
            bcNodeR = cmds.shadingNode("blendColors", asUtility=True, n='bcNodeR_switch_' + self.rig_info['instance'] + switchPrefix)
            if switchattr:
                cmds.connectAttr(switchattr, bcNodeR + '.blender')
            bcNodeS = cmds.shadingNode("blendColors", asUtility=True, n='bcNodeS_switch_' + self.rig_info['instance'] + switchPrefix)
            if switchattr:
                cmds.connectAttr(switchattr, bcNodeS + '.blender')
            constraints.append([bcNodeT, bcNodeR, bcNodeS])
            # Input Parents
            cmds.connectAttr(parentsA[j] + '.translate', bcNodeT + '.color1')
            cmds.connectAttr(parentsA[j] + '.rotate', bcNodeR + '.color1')
            cmds.connectAttr(parentsA[j] + '.scale', bcNodeS + '.color1')
            if parentsB != 'None':
                cmds.connectAttr(parentsB[j] + '.translate', bcNodeT + '.color2')
                cmds.connectAttr(parentsB[j] + '.rotate', bcNodeR + '.color2')
                cmds.connectAttr(parentsB[j] + '.scale', bcNodeS + '.color2')
            # Output to Children
            cmds.connectAttr(bcNodeT + '.output', children[j] + '.translate')
            cmds.connectAttr(bcNodeR + '.output', children[j] + '.rotate')
            cmds.connectAttr(bcNodeS + '.output', children[j] + '.scale')
        return constraints

    def queryCurrentXform(self, objlist):
        self.rig_info['xform'] = [xform(x, q=True, ws=True, m=True) for x in objlist]
        return self.rig_info['xform']


    def mirrorPart(self):
        # Make a mirror part if mirror checked.
        if self.side[1] == 'C':
            print "You can't mirror a center part"
        else:
            dupnodesets = self.duplicatePart(self.part_info['partasset'])

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
        except:
            pass

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
            except:
                pass

            returnnodes.append([org, name[2]])
        if namespace(exists=':tmp') == True:
            namespace(force=True, mv=[':tmp', ':'])
            namespace(rm=':tmp', f=True)

        return (returnnodes)




