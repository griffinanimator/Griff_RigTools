import maya.cmds as cmds
import json
import os
#import system.rig as rig
import system.rig as rig
import system.utils as utils
import system.math_utils as math_utils
from pymel.core import *
reload(utils)
reload(rig)


# We can use variables above the class level that can be read on class import
# This is also known as an attribute of a class

CLASSNAME = 'Rig_Hinge'
TITLE = 'Hinge'
DATAPATH = os.environ["DATA_PATH"] + '/rig/hinge.json'

class Rig_Hinge(rig.Rig):
    def __init__(self, uiinfo, *args):
        self.numjnts = 4
        self.datapath = os.environ["DATA_PATH"] + '/rig/hinge.json'
        rig.Rig.__init__(self, uiinfo, self.numjnts)
        self.ik_info = {}

    def install(self):
        rig.Rig.install(self)
        print 'hinge install'
        if self.rig_info == None:
            raise RuntimeWarning('Unable to rig the part.')
            return

        cmds.select(d=True)
        # Create Ik joints
        self.rig_info['ikjnts'] = rig.Rig.createJoint(self, self.module_info['ikjnts'], self.rig_info['positions'],
                                                      self.rig_info['rotations'], self.rig_info['instance'])

        # Create Fk joints
        self.rig_info['fkjnts'] = rig.Rig.createJoint(self, self.module_info['fkjnts'], self.rig_info['positions'],
                                                      self.rig_info['rotations'], self.rig_info['instance'])

        # Create Rig joints
        self.rig_info['rigjnts'] = rig.Rig.createJoint(self, self.module_info['rigjnts'],
                                                       self.rig_info['positions'],
                                                       self.rig_info['rotations'],
                                                       self.rig_info['instance'])

        # connect joint chains
        self.rig_info['bccons'] = rig.Rig.connectThroughBC(self, self.rig_info['ikjnts'], self.rig_info['fkjnts'],
                                                           self.rig_info['rigjnts'], None,
                                                           self.rig_info['instance'])

        for key, val in self.rig_info.iteritems():
            if type(self.rig_info[key]) != int:
                for item in self.rig_info[key]:
                    try:
                        cmds.container(self.rig_info['mainasset'], edit=True, an=item)
                    except:
                        pass

        # create fk controls
        mat = rig.Rig.queryCurrentXform(self, self.rig_info['fkjnts'])
        fkcontrols = []
        for x in self.module_info['fkcontrols']:
            fkcontrols.append(x.replace('_s_', self.module_info['instance']))

        self.rig_info['fkcontrols'] = []
        for x in range(len(fkcontrols)):
            self.rig_info['fkcontrols'].append(rig.Rig.createControl(self, [self.rig_info['xform'][x],
                                                                           fkcontrols[x], 'BoxControl.ma']))

        print self.rig_info['fkcontrols']
        for i in range(len(self.rig_info['fkcontrols'])):
            if i > 0:
                parent(self.rig_info['fkcontrols'][i][0], self.rig_info['fkcontrols'][i-1][1])
            parentConstraint(self.rig_info['fkcontrols'][i][1], self.rig_info['fkjnts'][i])

        # create stretchy ik
        ikcontrol = self.module_info['ikcontrols'][0].replace('_s_', self.module_info['instance'])
        self.rig_info['ikcontrol']=rig.Rig.createControl(self, [self.rig_info['xform'][2], ikcontrol, 'BoxControl.ma'])
        self.createStretchyIK()

    def layout(self):
        rig.Rig.layout(self)

    def ui(self, parentlyt):
        print "hinge ui"
        cb = cmds.checkBox(label='mirror', p=parentlyt)
        return ([[cb, 'mirror_cb']])

    def createStretchyIK(self, saxis='.tx'):
        # dictionary to store nodes

        rootpos = xform(self.rig_info['ikjnts'][0], q=True, t=True, ws=True)
        midpos = xform(self.rig_info['ikjnts'][1], q=True, t=True, ws=True)
        endpos = xform(self.rig_info['ikjnts'][2], q=True, t=True, ws=True)

        # Create the ikSolver and ikHandle
        iksol = ikSolver(st='ikRPsolver', ep=0.0, n=self.module_info['udname'] + '_ikSolver')
        ikh = ikHandle(n=self.module_info['udname'] + '_ikHandle', sj=self.rig_info['ikjnts'][0], ee=self.rig_info['ikjnts'][2], s='sticky',
                       sol=iksol)
        iksol = ikHandle(ikh[0], q=True, sol=True)

        # Stretch ----------------------------------------------------------
        # Start by creating all of the nodes we will need for the stretch.
        conRStretch = shadingNode("condition", asUtility=True, n=self.module_info['udname'] + '_conNode_RStretch')
        conEStretch = shadingNode("condition", asUtility=True, n=self.module_info['udname'] + '_conNode_EStretch')

        mdGMStretch = shadingNode("multiplyDivide", asUtility=True, n=self.module_info['udname'] + '_mdNode_GoffsetStretchM')
        mdGRStretch = shadingNode("multiplyDivide", asUtility=True, n=self.module_info['udname'] + '_mdNode_GoffsetStretchR')
        mdGEStretch = shadingNode("multiplyDivide", asUtility=True, n=self.module_info['udname'] + '_mdNode_GoffsetStretchE')
        mdMStretch = shadingNode("multiplyDivide", asUtility=True, n=self.module_info['udname'] + '_mdNode_MStretch')
        mdRStretch = shadingNode("multiplyDivide", asUtility=True, n=self.module_info['udname'] + '_mdNode_RStretch')
        mdEStretch = shadingNode("multiplyDivide", asUtility=True, n=self.module_info['udname'] + '_mdNode_EStretch')

        btaTglStretch = shadingNode("blendTwoAttr", asUtility=True, n=self.module_info['udname'] + '_btaNode_TglStretch')
        btaRStretch = shadingNode("blendTwoAttr", asUtility=True, n=self.module_info['udname'] + '_btaNode_RStretch')
        btaEStretch = shadingNode("blendTwoAttr", asUtility=True, n=self.module_info['udname'] + '_btaNode_EStretch')

        pmaRStretch = shadingNode("plusMinusAverage", asUtility=True, n=self.module_info['udname'] + '_pmaNode_RStretch')
        pmaEStretch = shadingNode("plusMinusAverage", asUtility=True, n='_pmaNode_EStretch')

        ucMStretch = shadingNode("unitConversion", asUtility=True, n=self.module_info['udname'] + '_ucNode_MStretch')
        ucRStretch = shadingNode("unitConversion", asUtility=True, n=self.module_info['udname'] + '_ucNode_RStretch')
        ucEStretch = shadingNode("unitConversion", asUtility=True, n=self.module_info['udname'] + '_ucNode_EStretch')

        # Set operations for nodes
        setAttr(mdGMStretch + '.operation', 2)
        setAttr(mdGRStretch + '.operation', 2)
        setAttr(mdGEStretch + '.operation', 2)
        setAttr(mdMStretch + '.operation', 2)
        setAttr(mdEStretch + '.operation', 1)
        setAttr(mdRStretch + '.operation', 1)

        setAttr(conRStretch + '.operation', 2)
        setAttr(conEStretch + '.operation', 2)

        setAttr(pmaRStretch + '.operation', 1)
        setAttr(pmaEStretch + '.operation', 1)

        select(d=True)

        lctrstart = spaceLocator(n=self.module_info['udname'] + '_startDistance_LCTR')
        xform(lctrstart, ws=True, t=rootpos)
        lctrend = spaceLocator(n=self.module_info['udname'] + '_endDistance_LCTR')
        xform(lctrend, ws=True, t=endpos)
        lctrmid = spaceLocator(n=self.module_info['udname'] + '_midDistance_LCTR')
        xform(lctrmid, ws=True, t=midpos)

        self.ik_info['dist_lctrs'] = [lctrstart, lctrend, lctrmid]
        for l in self.ik_info['dist_lctrs']:
            setAttr(l + '.visibility', 0)

        # Disdim for total chain length
        select(lctrstart, lctrend)
        distanceDimension(sp=(rootpos), ep=(endpos))
        disdimshape = self.module_info['udname'] + 'Shape_stretchMain_DISDIM'
        disdim = self.module_info['udname'] + '_stretchMain_DISDIM'
        rename('distanceDimensionShape1', disdimshape)
        rename('distanceDimension1', disdim)

        con = listConnections(disdimshape + '.endPoint', p=True)[0]
        if con != None:
            disconnectAttr(con, disdimshape + '.endPoint')
        con = listConnections(disdimshape + '.startPoint', p=True)[0]
        if con != None:
            disconnectAttr(con, disdimshape + '.startPoint')

        connectAttr(lctrstart + 'Shape.worldPosition[0]', disdimshape + '.startPoint', f=True)
        connectAttr(lctrend + 'Shape.worldPosition[0]', disdimshape + '.endPoint', f=True)

        # Disdim for first 2 joints
        select(d=True)
        distanceDimension(sp=(rootpos), ep=(midpos))
        disdimushape = self.module_info['udname'] + 'Shape_stretchUp_DISDIM'
        disdimu = self.module_info['udname'] + '_stretchUp_DISDIM'
        rename('distanceDimensionShape1', disdimushape)
        rename('distanceDimension1', disdimu)

        con = listConnections(disdimushape + '.endPoint', p=True)[0]
        if con != None:
            disconnectAttr(con, disdimushape + '.endPoint')
        con = listConnections(disdimushape + '.startPoint', p=True)[0]
        if con != None:
            disconnectAttr(con, disdimushape + '.startPoint')

        connectAttr(lctrstart + 'Shape.worldPosition[0]', disdimushape + '.startPoint', f=True)
        connectAttr(lctrend + 'Shape.worldPosition[0]', disdimushape + '.endPoint', f=True)

        # Disdim for second set joints
        select(d=True)
        distanceDimension(sp=(midpos), ep=(endpos))
        disdimlshape = self.module_info['udname'] + 'Shape_stretchLow_DISDIM'
        disdiml = self.module_info['udname'] + '_stretchLow_DISDIM'
        rename('distanceDimensionShape1', disdimlshape)
        rename('distanceDimension1', disdiml)

        self.ik_info['util_nodes'] = [conRStretch, conEStretch, mdMStretch, mdRStretch, mdEStretch, btaTglStretch,
                                 btaRStretch,
                                 btaEStretch, pmaRStretch, pmaEStretch, ucMStretch, ucRStretch, ucEStretch, mdGMStretch,
                                 mdGRStretch, mdGEStretch, iksol, ikh, disdim, disdimu, disdiml]

        con = listConnections(disdimlshape + '.endPoint', p=True)[0]
        if con != None:
            disconnectAttr(con, disdimlshape + '.endPoint')
        con = listConnections(disdimlshape + '.startPoint', p=True)[0]
        if con != None:
            disconnectAttr(con, disdimlshape + '.startPoint')

        connectAttr(lctrstart + 'Shape.worldPosition[0]', disdimlshape + '.startPoint', f=True)
        connectAttr(lctrend + 'Shape.worldPosition[0]', disdimlshape + '.endPoint', f=True)

        # Connect the stretch attribute
        if attributeQuery('stretch', node=self.rig_info['ikcontrol'][1], exists=True):
            connectAttr(self.rig_info['ikcontrol'][1] + '.stretch', btaTglStretch + '.attributesBlender')
        else:
            addAttr(self.rig_info['ikcontrol'][1], ln='stretch', min=0, max=10, k=True)
            connectAttr(self.rig_info['ikcontrol'][1] + '.stretch', btaTglStretch + '.attributesBlender')

        # parent the end locator to the control
        parent(lctrend, self.rig_info['ikcontrol'][1])
        parent(ikh[0], self.rig_info['ikcontrol'][1])

        # length of joint chain sections
        rootlen = getAttr(self.rig_info['ikjnts'][1] + saxis)
        endlen = getAttr(self.rig_info['ikjnts'][2] + saxis)
        chainlen = (rootlen + endlen)

        # negative value if x axis is negative
        negval = False

        setAttr(ucMStretch + '.conversionFactor', 1)
        setAttr(ucRStretch + '.conversionFactor', 1)
        setAttr(ucEStretch + '.conversionFactor', 1)

        if chainlen < 0:
            negval = True
            setAttr(ucRStretch + '.conversionFactor', -1)
            setAttr(ucEStretch + '.conversionFactor', -1)

        # connect attrs for sticky elbow.
        connectAttr(disdimshape + '.distance', mdGMStretch + '.input1X')
        connectAttr(mdGMStretch + '.outputX', btaTglStretch + '.input[0]')

        connectAttr(btaTglStretch + '.output', ucMStretch + '.input')
        connectAttr(ucMStretch + '.output', mdMStretch + '.input1X')
        connectAttr(ucMStretch + '.output', conRStretch + '.firstTerm')
        connectAttr(ucMStretch + '.output', conEStretch + '.firstTerm')

        connectAttr(mdMStretch + '.outputX', mdRStretch + '.input1X')
        connectAttr(mdMStretch + '.outputX', mdEStretch + '.input1X')
        connectAttr(mdRStretch + '.outputX', conRStretch + '.colorIfTrueR')
        connectAttr(mdEStretch + '.outputX', conEStretch + '.colorIfTrueR')

        connectAttr(disdimushape + '.distance', mdGRStretch + '.input1X')
        connectAttr(mdGRStretch + '.outputX', ucRStretch + '.input')
        connectAttr(ucRStretch + '.output', btaRStretch + '.input[1]')

        connectAttr(disdimlshape + '.distance', mdGEStretch + '.input1X')
        connectAttr(mdGEStretch + '.outputX', ucEStretch + '.input')
        connectAttr(ucEStretch + '.output', btaEStretch + '.input[1]')
        connectAttr(conRStretch + '.outColorR', btaRStretch + '.input[0]')
        connectAttr(conEStretch + '.outColorR', btaEStretch + '.input[0]')
        connectAttr(btaRStretch + '.output', pmaRStretch + '.input1D[0]')
        connectAttr(btaEStretch + '.output', pmaEStretch + '.input1D[0]')

        # Set node attributes for chain length
        setAttr(btaTglStretch + '.input[1]', 0)

        setAttr(mdRStretch + '.input2X', rootlen)
        setAttr(mdEStretch + '.input2X', endlen)

        if negval == True:
            setAttr(conRStretch + '.secondTerm', chainlen * -1)
            setAttr(conEStretch + '.secondTerm', chainlen * -1)
            setAttr(mdMStretch + '.input2X', chainlen * -1)
        else:
            setAttr(conRStretch + '.secondTerm', chainlen)
            setAttr(conEStretch + '.secondTerm', chainlen)
            setAttr(mdMStretch + '.input2X', chainlen)

        setAttr(conRStretch + '.colorIfFalseR', rootlen)
        setAttr(conEStretch + '.colorIfFalseR', endlen)

        # Connect to ik jnt tx
        connectAttr(pmaRStretch + '.output1D', self.rig_info['ikjnts'][1] + saxis)
        connectAttr(pmaEStretch + '.output1D', self.rig_info['ikjnts'][2] + saxis)

        # Connect control attributes
        if attributeQuery('pv_lock', node=self.rig_info['ikcontrol'][1], exists=True):
            connectAttr(self.rig_info['ikcontrol'][1] + '.pv_lock', btaRStretch + '.attributesBlender')
            connectAttr(self.rig_info['ikcontrol'][1] + '.pv_lock', btaEStretch + '.attributesBlender')
        else:
            addAttr(self.rig_info['ikcontrol'][1], ln='pv_lock', min=0, max=1, k=True)
            connectAttr(self.rig_info['ikcontrol'][1] + '.pv_lock', btaRStretch + '.attributesBlender')
            connectAttr(self.rig_info['ikcontrol'][1] +'.pv_lock', btaEStretch + '.attributesBlender')

        # Standard PV
        pvt = 'st'
        if pvt == "st":

            pvpos = math_utils.findPoleVectorPosition([self.rig_info['rigjnts'][0], self.rig_info['rigjnts'][1],
                                                       self.rig_info['rigjnts'][2]])

            # Setup switch to standard pole vector
            self.ik_info['pvcontrol'] = rig.Rig.createControl(self, [self.rig_info['xform'][1],
                                        self.module_info['ikcontrols'][2].replace('_s', self.rig_info['instance']),
                                        'BoxControl.ma'])

            xform(self.ik_info['pvcontrol'][0], ws=True, t=pvpos)

            poleVectorConstraint(self.ik_info['pvcontrol'][1], ikh[0], weight=1)
            parent(lctrmid, self.ik_info['pvcontrol'][1])

            # Calculate twist offset
            offset = math_utils.matchTwistAngle(ikh[0] + ".twist", self.rig_info['ikjnts'], self.rig_info['rigjnts'])

            for item in self.ik_info['util_nodes']:
                try:
                    setAttr(item + '.visibility', 0)
                except:
                    pass
