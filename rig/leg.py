__author__ = 'rgriffin'

"""
Base class inherited by all rig parts.
"""

from PySide import QtGui
from pymel.core import *
from scripts.tools.rigging.utilities import part_util
reload(part_util)
from scripts.tools.rigging.utilities import rig_util
reload(rig_util)
from scripts.tools.rigging.utilities import control_util
reload(control_util)
from scripts.tools.rigging.utilities import ik_util
reload(ik_util)
from scripts.tools.rigging.utilities import asset_util
reload(asset_util)

CLASS_NAME = "Create_Leg"
TITLE = "leg"
DESCRIPTION = "Create a leg part"

class Create_Leg():
    def __init__(self):
        print "Part Loaded"



    def layout(self, options, *args):
        # Define default option values and overwrite if able.
        udname = 'Leg'
        secop = 5
        sideop = 'C'

        # Standard options
        if 'SIDE' in options.keys():
            sideop = options['SIDE'].currentText()

        # create part with above defined options.
        # returns assets, 'udname': , 'instance': , layout controls
        part_info = part_util.createPart(['NAME', udname], ['Sections', int(secop)], ['SIDE', sideop], [], CLASS_NAME, TITLE, *args)

        # create additional placement nodes for the heel, and bank
        adcontrols = ['heel', 'lbank', 'rbank']
        for s in adcontrols:
            nameprefix = s +  '__' + sideop + '_' + part_info['instance']

            # Create the part control node.
            ntype = 'customLoc'
            node = 'dfSphere'
            name = nameprefix + '_Layout_CTRL'
            options = [['.colorR', 1], ['.colorG', 1], ['.colorB', 0], ['.transparency', .5], ['.drawOver', 1],
                       ['.drawType', 1], ['.radius', .5]]
            groups = None
            lockattrs = ['.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
            part_info[s] = control_util.createControl(ntype, node, name, options, groups, lockattrs)

            # Create a joint
            select(d=True)
            pjnt = joint(n=nameprefix + '_LYT_JNT', p=[0.0, 0.0, 0.0])
            parent(pjnt, part_info['mctrlgrp'])
            container(part_info['asset_info']['layoutasset'][0], edit=True, an=pjnt)
            pointConstraint(part_info[s][2], pjnt)

            xform(part_info[s][0], ws=True, t=[0.0 , 0.0, 0.0])

            # parent and add node to asset
            parent(part_info[s][0], part_info['asset_info']['layoutasset'][1])
            asset_util.publishToPartContainer(part_info['asset_info']['layoutasset'][0], part_info[s], [[part_info[s][2], 'transform']] )

        lockNode(part_info['asset_info']['layoutasset'][0])

    def rig(self, part):
        """

        :param part:
        :return:
        """

        # dictionary to store rig nodes.
        self.rig_info = {}

        # Unlock the part
        lockNode(part, lock=False)

        # Collect the layout info
        layout_info = rig_util.collectLayoutInfo(part)

        # placeholders for custom attributes
        ik = None
        fk = None


        # validate custom options
        sections = 4
        for item in layout_info['customattrs']:
            if 'NAME' in item:
                index = layout_info['customattrs'].index(item)
                udname = layout_info['customattrs'][index][1]
            if 'CLASSNAME' in item:
                index = layout_info['customattrs'].index(item)
                classname = layout_info['customattrs'][index][1]
            if 'SIDE' in item:
                index = layout_info['customattrs'].index(item)
                side = layout_info['customattrs'][index][1]
            if 'INSTANCE' in item:
                index = layout_info['customattrs'].index(item)
                instance = layout_info['customattrs'][index][1]


        # create the joint chains and establish a list for joint connection
        blendsets = []
        # create rig joints
        self.rig_info['rigjnts'] = rig_util.createJoints('_LYT_JNT', '_RIGJNT', layout_info['joints'][0:5],
                                                    layout_info['pos'][0:5],
                                                    layout_info['rot'][0:5], layout_info['orient'][0:5],
                                                    layout_info['rigasset'] + '_local')
        container(layout_info['rigasset'], edit=True, an=self.rig_info['rigjnts'][0], ihb=True)
        blendsets.append(self.rig_info['rigjnts'])

        # create ik joints
        self.rig_info['ikjnts'] = rig_util.createJoints('_LYT_JNT', '_IKJNT', layout_info['joints'][0:5],
                                                    layout_info['pos'][0:5],
                                                    layout_info['rot'][0:5], layout_info['orient'][0:5],
                                                    layout_info['rigasset'] + '_local')
        container(layout_info['rigasset'], edit=True, an=self.rig_info['ikjnts'][0], ihb=True)
        blendsets.append(self.rig_info['ikjnts'])

        # create fk joints
        self.rig_info['fkjnts'] = rig_util.createJoints('_LYT_JNT', '_FKJNT', layout_info['joints'][0:5],
                                                   layout_info['pos'][0:5],
                                                   layout_info['rot'][0:5], layout_info['orient'][0:5],
                                                   layout_info['rigasset'] + '_local')
        container(layout_info['rigasset'], edit=True, an=self.rig_info['fkjnts'][0], ihb=True)
        blendsets.append(self.rig_info['fkjnts'])


        # connect joints through a blendColorNode
        self.rig_info['blendset'] = blendsets
        self.rig_info['blendconstraints'] = rig_util.connectThroughBC(self.rig_info['blendset'][1], self.rig_info['blendset'][2], self.rig_info['blendset'][0], udname)
        # add blend nodes to the asset
        for b in self.rig_info['blendconstraints']:
            container(layout_info['rigasset'], edit=True, an=b, ihb=True)

        # create the fk controls
        self.rig_info['fkcontrols'] = []
        for i in range(sections):
            nameprefix = udname + str(i) + '__' + side + '_' + instance
            # create a control object
            # Create the root node.
            ntype = 'customLoc'
            node = 'clCilinder'
            name = nameprefix + '_FK_CTRL'
            shpoptions = [['.colorR', 1], ['.colorG', 1], ['.colorB', 1], ['.lineWidth', 4], ['.drawOver', 1],
                          ['.drawType', 1],
                          ['.segment', 8],
                          ['.transparency', .5]]
            groups = None
            lockattrs = ['.sx', '.sy', '.sz']
            self.rig_info['fkcontrols'].append(control_util.createControl(ntype, node, name, shpoptions, groups, lockattrs))

            self.rig_info['fkcontrols'][i][0].setTranslation(layout_info['pos'][i])
            self.rig_info['fkcontrols'][i][0].setRotation(layout_info['rot'][i])

            # constrain fk joint to control
            parentConstraint(self.rig_info['fkcontrols'][i][2], self.rig_info['fkjnts'][i], mo=True, n=nameprefix + '_FK_CTRL_ParentCon')

            # create control hierarchy
            if i > 0:
                parent(self.rig_info['fkcontrols'][i][0], self.rig_info['fkcontrols'][i-1][2])

            # add fk controls to the asset
            asset_util.publishToPartContainer(layout_info['rigasset'], [self.rig_info['fkcontrols'][i][0]],
                                              [[self.rig_info['fkcontrols'][i][2], 'transform']])

        parent(self.rig_info['fkcontrols'][0][0], layout_info['rigasset'] + '_local')

        # create ik setup
        # create the ik control
        nameprefix = udname + '_' + side + '_' + instance
        ntype = 'customLoc'
        node = 'clCircle'
        name = nameprefix + '_IK_CTRL'
        shpoptions = [['.colorR', 1], ['.colorG', 1], ['.colorB', 1], ['.lineWidth', 4], ['.drawOver', 1],
                      ['.drawType', 0],
                      ['.segment', 8],
                      ['.transparency', .5]]
        groups = None
        lockattrs = ['.sx', '.sy', '.sz']
        self.rig_info['ikcontrol'] = control_util.createControl(ntype, node, name, shpoptions, groups, lockattrs)

        # set position and rotation
        self.rig_info['ikcontrol'][0].setTranslation(layout_info['pos'][2])
        self.rig_info['ikcontrol'][0].setRotation(layout_info['rot'][2])

        # parent control
        parent(self.rig_info['ikcontrol'][0], layout_info['rigasset'] + '_local', a=True)

        # add ik foot control to asset after the foot so all nodes get added
        asset_util.publishToPartContainer(layout_info['rigasset'], [self.rig_info['ikcontrol'][0]],
                                          [[self.rig_info['ikcontrol'][2], 'transform']])

        # Create stretchy ik
        axis = '.tx'  # joint aim axis
        self.rig_info.update(ik_util.createStretchyIK(self.rig_info['ikjnts'][0:3], self.rig_info['rigjnts'][0:3],
                            layout_info['pos'][0:3], nameprefix , self.rig_info['ikcontrol'][2], axis))

        # add the pv control
        asset_util.publishToPartContainer(layout_info['rigasset'], [self.rig_info['pvcontrol'][0]],
                                          [[self.rig_info['pvcontrol'][2], 'transform']])

        from scripts.common.filesystem import data
        reload(data)
        #localnodes, worldnodes, publishnodes
        for item in data.traverse(self.rig_info['publishnodes']):
            try:
                if objExists(item) == True:
                    container(layout_info['rigasset'], edit=True, an=item, ihb=True)
            except:
                pass
        for item in data.traverse(self.rig_info['localnodes']):
            try:
                if len(listRelatives(item, p=True)) < 1:
                    parent(item, layout_info['rigasset'] + '_local')
            except:
                pass
        for item in data.traverse(self.rig_info['worldnodes']):
            try:
                if len(listRelatives(item, p=True)) < 1:
                    parent(item, layout_info['rigasset'] + '_world')
            except:
                pass

        # Rig the foot
        # update adds the key values from the returned dictionary to self.rig_info
        nameprefix = udname + '_' + side + '_' + instance
        self.rig_info.update(rig_util.setupFoot(self.rig_info['ikcontrol'][2], layout_info['pos'][2:8], ['.rx', '.ry', '.rz', 'pos'],
                           self.rig_info['ikjnts'][2:6], layout_info['orient'][2:7], nameprefix, self.rig_info['publishnodes'][0]))

        for each in self.rig_info['footgrps']:
            try:
                container(layout_info['rigasset'], edit=True, an=each, ihb=True)
            except:
                pass

        for each in self.rig_info['foot_util_nodes']:
            try:
                container(layout_info['rigasset'], edit=True, an=each, ihb=True)
            except: pass

        # publish foot controls to the asset
        asset_util.publishToPartContainer(layout_info['rigasset'], [self.rig_info['heelcontrol'][0]],
                                          [[self.rig_info['heelcontrol'][2], 'transform']])
        asset_util.publishToPartContainer(layout_info['rigasset'], [self.rig_info['ballcontrol'][0]],
                                          [[self.rig_info['ballcontrol'][2], 'transform']])
        asset_util.publishToPartContainer(layout_info['rigasset'], [self.rig_info['toecontrol'][0]],
                                          [[self.rig_info['toecontrol'][2], 'transform']])

        # lock the part
        lockNode(part)



    def ui(self, *args):
        """
        Adds to the rig_ui to provide options for the part.
        Titles such as Sections are defined and should be followed
        or new options added to the master list of definitions.
        :return: part_options
        """
        self.part_options = []

        return (self.part_options)


