import logging

try:
    import pysideuic
    from shiboken import wrapInstance

    logging.Logger.manager.loggerDict["pysideuic.uiparser"].setLevel(logging.CRITICAL)
    logging.Logger.manager.loggerDict["pysideuic.properties"].setLevel(logging.CRITICAL)
except ImportError:
    import pyside2uic as pysideuic
    from shiboken2 import wrapInstance

    logging.Logger.manager.loggerDict["pyside2uic.uiparser"].setLevel(logging.CRITICAL)
    logging.Logger.manager.loggerDict["pyside2uic.properties"].setLevel(logging.CRITICAL)

from Qt import QtWidgets, QtCore, QtGui

from gt_ui import pyside_ui as pyui
from maya import OpenMayaUI as OpenMayaUI
from gt_ui.MayaDockingClass import MyDockingWindow

from pymel.core import *

class Utils_UI(MyDockingWindow):
    toolName='Utils_UI'

    def __init__(self, parent=None):
        # Delete any previous instances of the ui that is detected. Do this before parenting self to main window!
        self.deleteInstances()

        super(self.__class__, self).__init__(parent=parent)
        mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
        self.mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtWidgets.QMainWindow)
        self.setObjectName(self.__class__.toolName)  # Make this unique enough if using it to clear previous instance!

        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)

        # Setup window's properties
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle('Utils_UI')

        self.w = 60
        self.h = 600
        self.resize(self.w, self.h)

        # Size policy for buttons
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.setStretch(0, 5)
        self.mainLayout.setContentsMargins(10, 2, 10, 2)
        self.mainLayout.setSpacing(10)
        self.mainLayout.setAlignment(QtCore.Qt.LeftToRight)


