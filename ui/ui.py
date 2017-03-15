import maya.cmds as cmds
import os
from functools import partial
import system.utils as utils
reload(utils)

# The UI class
class RDojo_UI:

    def __init__(self, *args):
        print 'In RDojo_UI'
        mi = cmds.window('MayaWindow', ma=True, q=True)
        for m in mi:
            if m == 'RDojo_Menu':
                cmds.deleteUI('RDojo_Menu', m=True)

        mymenu = cmds.menu('RDojo_Menu', label='RDMenu', to=True, p='MayaWindow')
        cmds.menuItem(label='Rig Tool', parent=mymenu, command=self.ui)

        """ Create a dictionary to store UI elements.
        This will allow us to access these elements later. """
        self.UIElements = {}

        """ Create a modinfo dictionary to store details
        about the currently loaded module. """
        self.ModInfo = {}

        # This dictionary will store all of the available rigging modules.
        self.rigmodlst = []
        rigcontents = os.listdir(os.environ["RIGGING_TOOL"]+ '/rig/')
        for mod in rigcontents:
            if '.pyc' not in mod and 'init' not in mod:
                self.rigmodlst.append(mod)

        # An empty list to store information collected from the ui.
        self.uiinfo = {}

    def ui(self, *args):
        """ Check to see if the UI exists """
        windowName = "Window"
        if cmds.window(windowName, exists=True):
            cmds.deleteUI(windowName)
        """ Define width and height for buttons and windows"""    
        windowWidth = 400
        windowHeight = 120
        buttonWidth = 55
        buttonHeight = 22

        self.UIElements["window"] = cmds.window(windowName, width=windowWidth, height=windowHeight, title="RDojo_UI", sizeable=True)


        self.UIElements["guiFrameLayout1"] = cmds.frameLayout( label='rigging', borderStyle='in')
        self.UIElements["mainColLayout"] = cmds.rowLayout(numberOfColumns=2, columnWidth2=(windowWidth/3, windowWidth/2),
                                                          adjustableColumn=2, columnAlign=(1, 'right'),
                                                          columnAttach=[(1, 'both', 5), (2, 'both', 5)],
                                                          p=self.UIElements["guiFrameLayout1"])
        self.UIElements["guiFlowLayout1"] = cmds.flowLayout(v=True, width=buttonWidth + 10, height=windowHeight,
                                                            wr=False, cs=5,
                                                            p=self.UIElements["mainColLayout"])
        self.UIElements["guiRowLayout2"] = cmds.rowLayout(numberOfColumns=2, columnWidth2=(windowWidth/4, windowWidth/4),
                                                          adjustableColumn=2, columnAlign=(1, 'left'),
                                                          columnAttach=[(1, 'both', 5), (2, 'both', 5)],
                                                          p=self.UIElements["mainColLayout"])

        self.UIElements['optionFlowA'] = cmds.flowLayout(v=True,
                                                        p=self.UIElements["guiRowLayout2"])
        self.UIElements['optionFlowB'] = cmds.flowLayout(v=True,
                                                        p=self.UIElements["guiRowLayout2"])
        

        self.UIElements["rigMenu"] = cmds.optionMenu('Rig_Install', label='Rig', p= self.UIElements["guiFlowLayout1"], cc=self.updateUi)
        
        # Dynamically make a menu item for each rigging module.
        for mod in self.rigmodlst:
            itemname = mod.replace('.py', '')    
            cmds.menuItem(label=itemname, p=self.UIElements["rigMenu"])

        # Make a menu for left, right and center sides.
        # We will query the value later.
        sides = ['_L_', '_R_', '_C_']
        self.UIElements["sideMenu"] = cmds.optionMenu('Side', label='side', p=self.UIElements['optionFlowA'])
        for s in sides:
            cmds.menuItem(label=s, p=self.UIElements["sideMenu"])

        # Make a button to run the rig script
        cmds.separator(w=10, hr=True, st='none', p=self.UIElements["guiFlowLayout1"])
        self.UIElements["rigbutton"] = cmds.button(label="Rig", width=buttonWidth, height=buttonHeight,
                                    bgc=[0.2, 0.4, 0.2], p=self.UIElements["guiFlowLayout1"], c=partial(self.rigmod, itemname))

        cmds.separator(w=10, hr=True, st='none', p=self.UIElements["guiFlowLayout1"])
        self.UIElements["layoutbutton"] = cmds.button(label="Layout", width=buttonWidth, height=buttonHeight,
                                                   bgc=[0.2, 0.4, 0.2], p=self.UIElements["guiFlowLayout1"],
                                                   c=self.layout)

        """ Show the window"""
        cmds.showWindow(windowName)

        self.updateUi()

    def updateUi(self, *args):

        self.ModInfo['modfile'] = cmds.optionMenu(self.UIElements["rigMenu"], q=True, v=True)
        self.ModInfo['mod'] = __import__("rig." + self.ModInfo['modfile'], {}, {}, [self.ModInfo['modfile']])
        reload(self.ModInfo['mod'])


        self.ModInfo['side'] = cmds.optionMenu(self.UIElements["sideMenu"], q=True, v=True)

        self.ModInfo['moduleClass'] = getattr(self.ModInfo['mod'], self.ModInfo['mod'].CLASSNAME)
        self.ModInfo['datapath'] = self.ModInfo['mod'].DATAPATH
        self.ModInfo['title'] = self.ModInfo['mod'].TITLE

        self.ModInfo['moduleInstance'] = self.ModInfo['moduleClass'](self.ModInfo)

        # create a layout and parent to main ui
        if (cmds.flowLayout(self.UIElements['optionFlowB'], exists=True)):
            cmds.deleteUI(self.UIElements['optionFlowB'], layout=True)

            self.UIElements['optionFlowB'] = cmds.flowLayout(p=self.UIElements["guiRowLayout2"])

        modui = self.ModInfo['moduleInstance'].ui( self.UIElements['optionFlowB'])

        if modui:
            for item in modui:
                self.UIElements[item[1]] = item[0]



    def rigmod(self, *args):
        self.ModInfo['moduleInstance'].install()

    def layout(self, *args):
        self.ModInfo['moduleInstance'].layout()
