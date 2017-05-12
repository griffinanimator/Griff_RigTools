__author__ = 'rgriffin'

"""
Helper module for creating PySide UI
"""

from Qt import QtWidgets, QtGui, QtCore
import maya.OpenMayaUI as omui

import os
import maya.cmds as cmds

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

def maya_api_version():
    return int(cmds.about(api=True))

class SimpleWindow(QtWidgets.QWidget):
    MAYA2014 = 201400
    MAYA2015 = 201500
    MAYA2016 = 201600
    MAYA2016_5 = 201650
    MAYA2017 = 201700

    def __init__(self):
        super(SimpleWindow, self).__init__()

        self.title = 'default'

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle(self.title)
        #icon = os.environ['FXS_MAYA_FRAMEWORK'] + '/icon/FiraxisMayaIcon.png'
        #self.setWindowIcon(QtGui.QIcon(icon))
        self.toolName = 'default'

        self.show()

        def run(self):
            '''
    		2017 docking is a little different...
    		'''

            def run2017():
                self.setObjectName(self.toolName)

                # The deleteInstances() dose not remove the workspace control, and we need to remove it manually
                workspaceControlName = self.objectName() + 'WorkspaceControl'
                self.deleteControl(workspaceControlName)
                self.show()
                cmds.workspaceControl(workspaceControlName, e=True, wp="preferred")
                self.raise_()


            def run2016():
                self.setObjectName(self.toolName)
                self.show()
                self.raise_()
                self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)

            if maya_api_version() < SimpleWindow.MAYA2017:
                run2016()
            else:
                run2017()

    def deleteControl(self, control):
        if cmds.workspaceControl(control, q=True, exists=True):
            cmds.workspaceControl(control, e=True, close=True)
            cmds.deleteUI(control, control=True)

def show():
    '''
	this is the function that start things up
	'''
    global SimpleWindow
    MySimpleWindow = SimpleWindow(parent=maya_main_window())
    MySimpleWindow.run()
    return MySimpleWindow

