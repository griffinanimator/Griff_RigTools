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

CLASS_NAME = "Create_Part"
TITLE = "part"
DESCRIPTION = "Create an rig part"

class Create_Part():
    def __init__(self):
        print "Part Loaded"

    def layout(self, options, *args):
        print options
        # Define default option values and overwrite if able.
        udname = 'Default'
        fkop = True
        ikop = False
        secop = 1
        sideop = 'C'
        ismirror = False

        # Standard options
        if 'NAME' in options.keys():
            if options['NAME'].text() != "":
                udname = options['NAME'].text()
            else: udname = 'Default'

        if 'Sections' in options.keys():
            secop = options['Sections'].text()

        if 'SIDE' in options.keys():
            sideop = options['SIDE'].currentText()

        if 'MIRROR'in options.keys():
            ismirror = options['MIRROR'].isChecked()


        # Custom options
        if 'FK' in options.keys():
            fkop = options['FK'].isChecked()

        if 'IK' in options.keys():
            ikop = options['IK'].isChecked()

        # create part with above defined options.
        part_util.createPart(['NAME', udname], ['Sections', int(secop)], ['SIDE', sideop], ['ISMIRROR', ismirror], [['IK', ikop], ['FK', fkop]], CLASS_NAME, TITLE, *args)


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
        layout_info = rig_util.collectLayoutInfo(part) #[{'rigasset': u'Default_Rig', 'joints': [nt.Joint(u'Default0_LYT_JNT')],
        # 'customattrs': [[u'CLASSNAME', u'Create_Part'], [u'TITLE', u'part'], [u'NAME', u'NAME'], [u'SECTIONS', 1],
        # [u'IK', False], [u'FK', False]], 'pos': [dt.Vector([0.0, 0.0, 0.0])], 'layoutasset': u'Default_Layout',
        # 'partcontents': [nt.Transform(u'Default_Layout_local'), nt.Transform(u'Default_Layout_world'),
        # nt.Transform(u'Default_Layout_input'), nt.Transform(u'Default_LYT_CTRL_GRP'),
        # nt.Transform(u'Default0_Layout_CTRL_OFFSET'), nt.Transform(u'Default0_Layout_CTRL_ZERO'),
        # nt.Transform(u'Default0_Layout_CTRL_GRP'), nt.Transform(u'Default0_Layout_CTRL'),
        # nt.DfSphere(u'Default0_Layout_CTRLShape'), nt.Transform(u'Default0_CTRL_AIM'),
        # nt.AimConstraint(u'Default0_CTRL_AIM_aimConstraint1'), nt.Transform(u'Default0_LYT_ORIENT_CTRL_OFFSET'),
        # nt.Transform(u'Default0_LYT_ORIENT_CTRL_AIM'), nt.Transform(u'Default0_LYT_ORIENT_CTRL_ZERO'),
        # nt.Transform(u'Default0_LYT_ORIENT_CTRL_GRP'), nt.Transform(u'Default0_LYT_ORIENT_CTRL'),
        # nt.OrientLoc(u'Default0_LYT_ORIENT_CTRLShape'), nt.PointConstraint(u'Default0_LYT_ORIENT_CTRL_AIM_pointConstraint1'),
        #  nt.Transform(u'Default0_LYT_END_CTRL_OFFSET'), nt.Transform(u'Default0_LYT_END_CTRL_ZERO'), nt.Transform(u'Default0_LYT_END_CTRL_GRP'),
        # nt.Transform(u'Default0_LYT_END_CTRL'), nt.DfSphere(u'Default0_LYT_END_CTRLShape'), nt.Joint(u'Default0_LYT_JNT'),
        # nt.PointConstraint(u'Default0_LYT_JNT_pointConstraint1')], 'rot': [dt.EulerRotation([0.0, -0.0, 0.0])], 'orient': [Quaternion([0.0, 0.0, 0.0, 1.0])]}

        # placeholders for custom attributes
        ik = None
        fk = None


        # validate custom options
        for item in layout_info['customattrs']:
            if 'IK' in item:
                index = layout_info['customattrs'].index(item)
                if layout_info['customattrs'][index][1] == True:
                    ik = True
            if 'FK' in item:
                index = layout_info['customattrs'].index(item)
                if layout_info['customattrs'][index][1] == True:
                    fk = True
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
        if ik == True:
            rig_info['ikjnts'] = rig_util.createJoints('_LYT_JNT', '_IKJNT', layout_info['joints'],
                                                        layout_info['pos'],
                                                        layout_info['rot'], layout_info['orient'],
                                                        layout_info['rigasset'] + '_local')
            container(layout_info['rigasset'], edit=True, an=rig_info['ikjnts'][0], ihb=True)
        else:
            rig_info['ikjnts'] = []

        blendsets.append(rig_info['ikjnts'])

        # create fk joints
        if fk == True:
            rig_info['fkjnts'] = rig_util.createJoints('_LYT_JNT', '_FKJNT', layout_info['joints'],
                                                       layout_info['pos'],
                                                       layout_info['rot'], layout_info['orient'],
                                                       layout_info['rigasset'] + '_local')
            container(layout_info['rigasset'], edit=True, an=rig_info['fkjnts'][0], ihb=True)
        else:
            rig_info['fkjnts'] = []

        blendsets.append(rig_info['fkjnts'])


        # connect joints through a blendColorNode
        if fk == True or ik ==True:
            rig_info['blendset'] = blendsets
            rig_info['blendconstraints'] = rig_util.connectThroughBC(rig_info['blendset'][1], rig_info['blendset'][2], rig_info['blendset'][0], udname)
            # add blend nodes to the asset
            for b in rig_info['blendconstraints']:
                container(layout_info['rigasset'], edit=True, an=b, ihb=True)

        # create the fk controls
        if fk == True:
            rig_info['fkcontrols'] = []
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
                rig_info['fkcontrols'].append(control_util.createControl(ntype, node, name, shpoptions, groups, lockattrs))

                rig_info['fkcontrols'][i][0].setTranslation(layout_info['pos'][i])
                rig_info['fkcontrols'][i][0].setRotation(layout_info['rot'][i])

                # constrain fk joint to control
                parentConstraint(rig_info['fkcontrols'][i][2], rig_info['fkjnts'][i], mo=True, n=udname + '_' + str(i) + '_FK_CTRL_ParentCon')

                # create control hierarchy
                if i > 0:
                    parent(rig_info['fkcontrols'][i][0], rig_info['fkcontrols'][i-1][2])


            # add fk controls to the asset
            for c in rig_info['fkcontrols']:
                container(layout_info['rigasset'], edit=True, an=c[0], ihb=True)

            parent(rig_info['fkcontrols'][0][0], layout_info['rigasset'] + '_local')


        # create ik setup
        nameprefix = udname + '__' + side + '_' + instance

        iktype = None
        if ik == True:
            if sections == 2:
                iktype = 'sc'
            if sections > 2:
                iktype == 'spline'

        if iktype == 'sc':
            # create the ik control
            ntype = 'customLoc'
            node = 'clCircle'
            name = nameprefix + '_IK_CTRL'
            shpoptions = [['.colorR', 1], ['.colorG', 1], ['.colorB', 1], ['.lineWidth', 4], ['.drawOver', 1],
                          ['.drawType', 0],
                          ['.segment', 8],
                          ['.transparency', .5]]
            groups = None
            lockattrs = ['.sx', '.sy', '.sz']
            rig_info['ikcontrol'] = control_util.createControl(ntype, node, name, shpoptions, groups, lockattrs)

            # set position and rotation
            rig_info['ikcontrol'][0].setTranslation(layout_info['pos'][sections -1])
            rig_info['ikcontrol'][0].setRotation(layout_info['rot'][sections -1])

            # Add control to asset and parent
            container(layout_info['rigasset'], edit=True, an=rig_info['ikcontrol'][0], ihb=True)
            parent(rig_info['ikcontrol'][0], layout_info['rigasset'] + '_local', a=True)

            # Create stretchy ik
            axis = '.tx'  # joint aim axis
            rig_info['ikinfo'] = ik_util.scStretchyIk(rig_info['ikjnts'], nameprefix, rig_info['ikcontrol'][2], axis)

            for item in rig_info['ikinfo']:
                container(layout_info['rigasset'], edit=True, an=item, ihb=True)

            for i in range(len(rig_info['ikinfo'])):
                if len(listRelatives(rig_info['ikinfo'][i], p=True)) < 1:
                    try:
                        parent(rig_info['ikinfo'][i], layout_info['rigasset'] + '_local')
                    except: pass

        control_util.makeWingControl()


    def ui(self, *args):
        """
        Adds to the rig_ui to provide options for the part.
        Titles such as Sections are defined and should be followed
        or new options added to the master list of definitions.
        :return: part_options
        """
        self.part_options = []

        self.partnum = QtGui.QSpinBox()
        self.partnum.setMinimum(1)
        self.partnum.setMaximum(12)
        self.part_options.append(["Sections", self.partnum])

        self.mirobox = QtGui.QCheckBox(None)
        self.part_options.append(["MIRROR", self.mirobox])

        self.namefield = QtGui.QLineEdit()
        self.part_options.append(["NAME", self.namefield])

        self.fkobox = QtGui.QCheckBox(None)
        self.part_options.append(["FK", self.fkobox])

        self.ikobox = QtGui.QCheckBox(None)
        self.part_options.append(["IK", self.ikobox])

        return (self.part_options)


