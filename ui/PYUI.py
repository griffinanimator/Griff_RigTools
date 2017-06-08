__author__ = 'rgriffin'
__description__ = "Main UI for the rigging tools"

import os
import sys
import pkgutil
import importlib

from pymel.core import *

from shiboken import wrapInstance
from PySide import QtGui
from PySide import QtCore

from maya import OpenMayaUI as OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget

import ui_ops as uop

class Rig_Ui(MayaQWidgetDockableMixin, QtGui.QMainWindow):
    toolName = 'Griff_Rigging_Tool'

    def __init__(self, parent=None):
        """ Create a dictionary to store UI elements.
                This will allow us to access these elements later. """
        self.UIElements = {}

        """ Create a modinfo dictionary to store details
        about the currently loaded module. """
        self.ModInfo = {}

        # This list will store all of the available rigging modules.
        self.rigmodlst = []
        rigcontents = os.listdir(os.environ["RIGGING_TOOL"] + '/rig/')
        for mod in rigcontents:
            if '.pyc' not in mod and 'init' not in mod:
                self.rigmodlst.append(mod.replace('.py', ''))


        super(self.__class__, self).__init__(parent=parent)
        mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
        self.mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QMainWindow)
        self.setObjectName(self.__class__.toolName)  # Make this unique enough if using it to clear previous instance!

        #Setup window's properties
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle('Griff_Rigging_Tool')
        self.w = 100
        self.h = 84
        self.resize(self.w, self.h)

        # Size policy for buttons
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        self.centralwidget = QtGui.QWidget()

        self.setCentralWidget(self.centralwidget)

        # Status bar
        self.statusBar().showMessage('Rigging Tool Ready')

        # Menu
        self.menubar = self.menuBar()
        filemenu = self.menubar.addMenu('&File')

        """
        create layouts
        """
        self.mainLayout = QtGui.QVBoxLayout()
        self.subLayout = QtGui.QHBoxLayout()
        self.centralwidget.setLayout(self.mainLayout)

        # Create a grid layout that sets spacing for entire UI
        self.centralgrid = QtGui.QGridLayout()
        self.centralgrid.setSpacing(10)

        self.lytbuttonwidget = QtGui.QWidget()

        # Create a box layout to hold create and delete part buttons
        self.lytbuttonlayout = QtGui.QVBoxLayout(self.lytbuttonwidget)
        self.lytbuttonlayout.addStretch(1)

        self.lytbuttonframe = QtGui.QHBoxLayout()

        # Create some buttons
        self.createpartbutton = uop.createButton("LYT", [0, 0, 0], [12, True, [100, 100, 100]], [32, 32], [32, 32],
                                                  self.layout, [False, None])
        self.createpartbutton.setSizePolicy(sizePolicy)
        self.createpartbutton.setStatusTip('Adds a part to the scene')
        self.createpartbutton.installEventFilter(self)

        # ComboBox of available parts
        # coboBox to hold all available rig parts
        self.partcombobox = QtGui.QComboBox()
        self.partcombobox.setStatusTip('All parts available for use')
        self.partcombobox.installEventFilter(self)

        partslot = lambda: self.loadPartOptions()
        self.partcombobox.activated.connect(partslot)



        """
        parent the layouts
        """
        self.mainLayout.addLayout(self.centralgrid)

        self.lytbuttonlayout.addLayout(self.lytbuttonframe)
        self.centralgrid.addWidget(self.lytbuttonwidget, 0, 0)

        self.lytbuttonframe.addWidget(self.createpartbutton, 0, 0)

        self.lytbuttonframe.addWidget(self.partcombobox, 0, 0)

        # Fill out the UI
        self.loadParts()

    def layout(self, *args):
        return
        #self.ModInfo['moduleInstance'].layout()

    def loadPartOptions(self):
        return


    def dockCloseEventTriggered(self):
        # If it's floating or docked, this will run and delete it self when it closes.
        # You can choose not to delete it here so that you can still re-open it through the right-click menu, but do disable any callbacks/timers that will eat memory
        self.deleteInstances()

    # Delete any instances of this class
    def deleteInstances(self):
        mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
        mayaMainWindow = wrapInstance(long(mayaMainWindowPtr),
                                      QtGui.QMainWindow)  # Important that it's QMainWindow, and not QWidget/QDialog

        # Go through main window's children to find any previous instances
        for obj in mayaMainWindow.children():
            if type(obj) == MayaQDockWidget:

                # if obj.widget().__class__ == self.__class__: # Alternatively we can check with this, but it will fail if we re-evaluate the class
                if obj.widget().objectName() == self.__class__.toolName:  # Compare object names
                    # If they share the same name then remove it
                    print 'Deleting instance {0}'.format(obj)
                    mayaMainWindow.removeDockWidget(
                        obj)  # This will remove from right-click menu, but won't actually delete it! ( still under mainWindow.children() )
                    # Delete it for good
                    obj.setParent(None)
                    obj.deleteLater()

        if self.id:
            scriptJob(kill=self.id)

    # Show window with docking ability
    def run(self):
        self.show(dockable=True)

    def loadParts(self, *args):
        """
        Import and load all available parts and add them to the UI
        :param args:
        :return:
        """
        for mod in self.rigmodlst:
            print mod

            m = __import__("rig." + mod, {}, {}, [mod])
            reload(m)


            if m:
                try:
                    modkey = getattr(m, 'TITLE')

                    self.partcombobox.addItem(modkey)
                except:
                    pass