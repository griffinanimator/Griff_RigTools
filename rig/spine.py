__author__ = 'rgriffin'


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
from scripts.tools.rigging.utilities import surface_util
reload(surface_util)

CLASS_NAME = "Create_Spine"
TITLE = "spine"
DESCRIPTION = "Create a spine part"

class Create_Spine():
    def __init__(self):
        print "Part Loaded"


    def layout(self, options, *args):
        print options
        # Define default option values and overwrite if able.
        secop = 5
        sideop = 'C'
        ismirror = False
        udname = 'Spine'

        # Standard options

        # Custom options

        # create part with above defined options.
        part_util.createPart(['NAME', udname], ['Sections', int(secop)], ['SIDE', sideop], ['ISMIRROR', ismirror], [], CLASS_NAME, TITLE, *args)


    def rig(self, part):
        """

        :param part:
        :return:
        """
        # Unlock the part
        lockNode(part, lock=False)

        # dictionary to store rig nodes.
        rig_info = {}

        # Collect the layout info
        layout_info = rig_util.collectLayoutInfo(part)

        # validate custom options
        for item in layout_info['customattrs']:
            if 'SECTIONS' in item:
                index = layout_info['customattrs'].index(item)
                sections = layout_info['customattrs'][index][1]
            if 'NAME' in item:
                index = layout_info['customattrs'].index(item)
                udname = layout_info['customattrs'][index][1]
            if 'CLASSNAME' in item:
                index = layout_info['customattrs'].index(item)
                classname = layout_info['customattrs'][index][1]
            if 'SIDE' in item:
                index = layout_info['customattrs'].index(item)
                side = layout_info['customattrs'][index][1]
            if 'ISMIRROR' in item:
                index = layout_info['customattrs'].index(item)
                ismirror = layout_info['customattrs'][index][1]
            if 'INSTANCE' in item:
                index = layout_info['customattrs'].index(item)
                instance = layout_info['customattrs'][index][1]



        # create the joint chains and establish a list for joint connection
        blendsets = []
        # create rig joints
        rig_info['rigjnts'] = rig_util.createJoints('_LYT_JNT', '_RIGJNT', layout_info['joints'],
                                                    layout_info['pos'],
                                                    layout_info['rot'], layout_info['orient'],
                                                    layout_info['rigasset'] + '_local')
        container(layout_info['rigasset'], edit=True, an=rig_info['rigjnts'][0], ihb=True)
        blendsets.append(rig_info['rigjnts'])

        # create ik joints
        rig_info['ikjnts'] = rig_util.createJoints('_LYT_JNT', '_IKJNT', layout_info['joints'],
                                                    layout_info['pos'],
                                                    layout_info['rot'], layout_info['orient'],
                                                    layout_info['rigasset'] + '_local')
        container(layout_info['rigasset'], edit=True, an=rig_info['ikjnts'][0], ihb=True)

        blendsets.append(rig_info['ikjnts'])


        # connect joints through a blendColorNode
        rig_info['blendset'] = blendsets
        rig_info['blendconstraints'] = rig_util.connectThroughBC(rig_info['blendset'][1], [], rig_info['blendset'][0], udname)
        # add blend nodes to the asset
        for b in rig_info['blendconstraints']:
            container(layout_info['rigasset'], edit=True, an=b, ihb=True)

        # create the controls
        controlops = [['Pelvis', 'dfBox'], ['Spine1', 'clCilinder'], ['Belly', 'dfBox'], ['Spine2', 'clCilinder'], ['Chest', 'dfBox']]
        rig_info['controls'] = []
        for i in range(sections):
            nameprefix = controlops[i][0] + '__' + side + '_' + instance
            # create a control object
            # Create the root node.
            ntype = 'customLoc'
            node = controlops[i][1]
            name = nameprefix + '_CTRL'
            shpoptions = [['.colorR', 1], ['.colorG', 1], ['.colorB', 1], ['.lineWidth', 4], ['.drawOver', 1],
                          ['.drawType', 1],
                          ['.segment', 8],
                          ['.transparency', .5]]
            groups = None
            lockattrs = ['.sx', '.sy', '.sz']
            rig_info['controls'].append(control_util.createControl(ntype, node, name, shpoptions, groups, lockattrs))

            rig_info['controls'][i][0].setTranslation(layout_info['pos'][i])
            rig_info['controls'][i][0].setRotation(layout_info['rot'][i])

            # create control hierarchy
            parent(rig_info['controls'][0][0], layout_info['rigasset'] + '_local')

        # add controls to the asset
        for c in rig_info['controls']:
            container(layout_info['rigasset'], edit=True, an=c[0], ihb=True)

        # custom attrs to control twist
        addAttr(rig_info['controls'][4][2], shortName='Mid_Twist', longName='Mid_Twist', min=0, max=1, defaultValue=.5, k=False)
        addAttr(rig_info['controls'][4][2], shortName='Mid_Bias', longName='Mid_Bias', min=0, max=0.5, defaultValue=0, k=False)

        # Create a ribbon surface
        convecs = [[0.0, 0.0, 1.0], [0.0, -1.0, 0.0]] # Determines aim vector
        axis = 'y'
        offset = [1, 1]
        surfacenodes = (surface_util.make_ribbon([rig_info['ikjnts'][3], rig_info['ikjnts'][1]], udname, rig_info['controls'][2][2], instance, convecs, axis, offset))
        rig_info.update(surfacenodes)

        delete(rig_info['mpointcon'])
        delete(rig_info['mlocpntcon'])

        #bengrppos = xform(rig_info['ikjnts'][2], q=True, ws=True, t=True)
        #xform(rig_info['bendzerogrpm'], ws=True, t=bengrppos)
        #xform(rig_info['controls'][6][0], ws=True, t=bengrppos)
    
        parent(rig_info['folgrp'], layout_info['rigasset'] + '_world')
        parent(rig_info['surface'], layout_info['rigasset'] + '_world')

        parent(rig_info['bendgrpb'], rig_info['controls'][0][2])
        parent(rig_info['bendzerogrpm'], rig_info['controls'][3][2])
        parent(rig_info['bendgrpt'], rig_info['controls'][4][2])

        for item in surfacenodes:
            try:
                container(layout_info['rigasset'], edit=True, an=surfacenodes[item], ihb=True)
            except: print surfacenodes[item]

        # Setup math nodes to control amount of twist
        mdivmidfoltop = shadingNode("multiplyDivide", asUtility=True,
                                         n='mdivNode_' + instance + 'midSpineFollowTop')
        mdivmidfolbtm = shadingNode("multiplyDivide", asUtility=True,
                                         n='mdivNode_' + instance + 'midSpineFollowBottom')
        pmamidfollow = shadingNode("plusMinusAverage", asUtility=True,
                                        n='pmaNode_' + instance + 'midSpineFollow')
        pmamidbiastop = shadingNode("plusMinusAverage", asUtility=True,
                                         n='pmaNode_' + instance + 'midSpineBiasTop')
        pmamidbiasbtm = shadingNode("plusMinusAverage", asUtility=True,
                                         n='pmaNode_' + instance + 'midSpineBiasBtm')

        ##########################
        connectAttr('%s.translate' % rig_info['controls'][4][2], '%s.input1' % mdivmidfoltop)
        connectAttr('%s.translate' % rig_info['controls'][0][2], '%s.input1' % mdivmidfolbtm)
        setAttr('%s.operation' % pmamidfollow, 1)
        setAttr('%s.operation' % pmamidbiastop, 1)
        setAttr('%s.operation' % pmamidbiasbtm, 2)

        connectAttr('%s.Mid_Bias' % rig_info['controls'][4][2], '%s.input1D[0]' % pmamidbiastop)
        connectAttr('%s.Mid_Bias' % rig_info['controls'][4][2], '%s.input1D[0]' % pmamidbiasbtm)
        setAttr('%s.input1D[1]' % pmamidbiasbtm, 0.5)
        setAttr('%s.input1D[1]' % pmamidbiastop, 0.5)
        connectAttr('%s.output1D' % pmamidbiasbtm, '%s.input2X' % mdivmidfolbtm)
        connectAttr('%s.output1D' % pmamidbiasbtm, '%s.input2Y' % mdivmidfolbtm)
        connectAttr('%s.output1D' % pmamidbiasbtm, '%s.input2Z' % mdivmidfolbtm)
        connectAttr('%s.output1D' % pmamidbiastop, '%s.input2X' % mdivmidfoltop)
        connectAttr('%s.output1D' % pmamidbiastop, '%s.input2Y' % mdivmidfoltop)
        connectAttr('%s.output1D' % pmamidbiastop, '%s.input2Z' % mdivmidfoltop)

        connectAttr('%s.output' % mdivmidfoltop, '%s.input3D[0]' % pmamidfollow)
        connectAttr('%s.output' % mdivmidfolbtm, '%s.input3D[1]' % pmamidfollow)

        connectAttr('%s.output3D' % pmamidfollow, '%s.translate' % rig_info['controls'][2][1])



        pmamidtwist = shadingNode("plusMinusAverage", asUtility=True,
                                       n='pmaNode_' + instance + 'midSpineTwist')
        mdivmidtwist = shadingNode("multiplyDivide", asUtility=True,
                                        n='mdivNode_' + instance + 'midSpineTwist')

        connectAttr('%s.rx' % rig_info['controls'][0][2], '%s.input3D[0].input3Dx' % pmamidtwist)
        connectAttr('%s.ry' % rig_info['controls'][0][2], '%s.input3D[0].input3Dy' % pmamidtwist)
        connectAttr('%s.rz' % rig_info['controls'][0][2], '%s.input3D[0].input3Dz' % pmamidtwist)
        connectAttr('%s.rx' % rig_info['controls'][4][2], '%s.input3D[1].input3Dx' % pmamidtwist)
        connectAttr('%s.ry' % rig_info['controls'][4][2], '%s.input3D[1].input3Dy' % pmamidtwist)
        connectAttr('%s.rz' % rig_info['controls'][4][2], '%s.input3D[1].input3Dz' % pmamidtwist)

        connectAttr('%s.output3D.output3Dx' % pmamidtwist, '%s.input1X' % mdivmidtwist)
        connectAttr('%s.output3D.output3Dy' % pmamidtwist, '%s.input1Y' % mdivmidtwist)
        connectAttr('%s.output3D.output3Dz' % pmamidtwist, '%s.input1Z' % mdivmidtwist)

        connectAttr('%s.Mid_Twist' % rig_info['controls'][4][2], '%s.input2X' % mdivmidtwist)
        connectAttr('%s.Mid_Twist' % rig_info['controls'][4][2], '%s.input2Y' % mdivmidtwist)
        connectAttr('%s.Mid_Twist' % rig_info['controls'][4][2], '%s.input2Z' % mdivmidtwist)

        connectAttr('%s.outputX' % mdivmidtwist, '%s.rx' % rig_info['controls'][2][1])


    def ui(self, *args):
        """
        Adds to the rig_ui to provide options for the part.
        Titles such as Sections are defined and should be followed
        or new options added to the master list of definitions.
        :return: part_options
        """
        self.part_options = []

        return (self.part_options)


