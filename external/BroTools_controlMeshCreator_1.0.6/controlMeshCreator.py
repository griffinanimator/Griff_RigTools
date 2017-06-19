#!/usr/bin/env python
#region MayaMixin copy paste
"""
Maya mixin classes to add common functionality for custom PyQt/PySide widgets in Maya.

* MayaQWidgetBaseMixin      Mixin that should be applied to all custom QWidgets created for Maya
                            to automatically handle setting the objectName and parenting

* MayaQWidgetDockableMixin  Mixin that adds dockable capabilities within Maya controlled with
                            the show() function
"""


import uuid

from maya import cmds
from maya import mel
from maya import OpenMayaUI as omui

# Import available PySide or PyQt package, as it will work with both
try:
    try:
        from PySide2.QtGui import *
        from PySide2.QtCore import *
        from PySide2.QtWidgets import *
        from shiboken2 import wrapInstance
        print "Using PySide2"

    except:
        from PySide.QtGui import *
        from PySide.QtCore import *
        from shiboken import wrapInstance
        print "Using PySide"
    _qtImported = 'PySide'
except ImportError, e1:
    try:
        from PyQt4.QtCore import Qt, QPoint, QSize
        from PyQt4.QtCore import pyqtSignal as Signal
        from PyQt4.QtGui import *
        from sip import wrapinstance as wrapInstance
        _qtImported = 'PyQt4'
    except ImportError, e2:
        raise ImportError, '%s, %s'%(e1,e2)


class MayaQWidgetBaseMixin(object):
    '''
    Handle common actions for Maya Qt widgets during initialization:
        * auto-naming a Widget so it can be looked up as a string through
          maya.OpenMayaUI.MQtUtil.findControl()
        * parenting the widget under the main maya window if no parent is explicitly
          specified so not to have the Window disappear when the instance variable
          goes out of scope

    Integration Notes:
        Inheritance ordering: This class must be placed *BEFORE* the Qt class for proper execution
        This is needed to workaround a bug where PyQt/PySide does not call super() in its own __init__ functions

    Example:
        class MyQWidget(MayaQWidgetBaseMixin, QPushButton):
            def __init__(self, parent=None):
                super(MyQWidget, self).__init__(parent=parent)
                self.setText('Push Me')
        myWidget = MyQWidget()
        myWidget.show()
        print myWidget.objectName()
    '''
    def __init__(self, parent=None, *args, **kwargs):
        super(MayaQWidgetBaseMixin, self).__init__(parent=parent, *args, **kwargs) # Init all baseclasses (including QWidget) of the main class
        self._initForMaya(parent=parent)


    def _initForMaya(self, parent=None, *args, **kwargs):
        '''
        Handle the auto-parenting and auto-naming.

        :Parameters:
            parent (string)
                Explicitly specify the QWidget parent.  If 'None', then automatically
                parent under the main Maya window
        '''
        # Set parent to Maya main window if parent=None
        if parent == None:
            self._makeMayaStandaloneWindow()

        # Set a unique object name string so Maya can easily look it up
        if self.objectName() == '':
            self.setObjectName('%s_%s'%(self.__class__.__name__, uuid.uuid4()))


    def _makeMayaStandaloneWindow(self):
        '''Make a standalone window, though parented under Maya's mainWindow.
        The parenting under Maya's mainWindow is done so that the QWidget will not
        auto-destroy itself when the instance variable goes out of scope.
        '''
        origParent = self.parent()

        # Parent under the main Maya window
        mainWindowPtr = omui.MQtUtil.mainWindow()
        mainWindow = wrapInstance(long(mainWindowPtr), QMainWindow)
        self.setParent(mainWindow)

        # Make this widget appear as a standalone window even though it is parented
        if isinstance(self, QDockWidget):
            self.setWindowFlags(Qt.Dialog|Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.Window)

        # Delete the parent QDockWidget if applicable
        if isinstance(origParent, QDockWidget):
            origParent.close()


class MayaQDockWidget(MayaQWidgetBaseMixin,QDockWidget):
    '''QDockWidget tailored for use with Maya.
    Mimics the behavior performed by Maya's internal QMayaDockWidget class and the dockControl command

    :Signals:
        closeEventTriggered: emitted when a closeEvent occurs

    :Known Issues:
        * Manually dragging the DockWidget to dock in the Main MayaWindow will have it resize to the 'sizeHint' size
          of the child widget() instead of preserving its existing size.
    '''
    # Custom Signals
    closeEventTriggered = Signal()   # Qt Signal triggered when closeEvent occurs


    def __init__(self, parent=None, *args, **kwargs):
        super(MayaQDockWidget, self).__init__(parent=parent, *args, **kwargs) # Init all baseclasses (including QWidget) of the main class

        # == Mimic operations performed by Maya internal QmayaDockWidget ==
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)

        # WORKAROUND: The mainWindow.handleDockWidgetVisChange may not be present on some PyQt and PySide systems.
        #             Handle case if it fails to connect to the attr.
        mainWindowPtr = omui.MQtUtil.mainWindow()
        mainWindow = wrapInstance(long(mainWindowPtr), QMainWindow)
        try:
            self.visibilityChanged.connect(mainWindow.handleDockWidgetVisChange)
        except AttributeError, e:
            # Error connecting visibilityChanged trigger to mainWindow.handleDockWidgetVisChange.
            # Falling back to using MEL command directly.
            mel.eval('evalDeferred("updateEditorToggleCheckboxes()")')  # Currently mainWindow.handleDockWidgetVisChange only makes this updateEditorToggleCheckboxes call


    def setArea(self, area):
        '''Set the docking area
        '''
        # Skip setting the area if no area value passed in
        if area == Qt.NoDockWidgetArea:
            return
        # Mimic operations performed by Maya dockControl command
        mainWindowPtr = omui.MQtUtil.mainWindow()
        mainWindow = wrapInstance(long(mainWindowPtr), QMainWindow)
        childrenList = mainWindow.children()
        foundDockWidgetToTab = False
        for child in childrenList:
            # Create Tabbed dock if a QDockWidget already at that area
            if (child != self) and (isinstance(child, QDockWidget)):
                if  not child.isHidden() and  not child.isFloating():
                    if mainWindow.dockWidgetArea(child) == area:
                        mainWindow.tabifyDockWidget(child, self)
                        self.raise_()
                        foundDockWidgetToTab = True
                        break
        # If no other QDockWidget at that area, then just add it
        if not foundDockWidgetToTab:
            mainWindow.addDockWidget(area, self)


    def resizeEvent(self, evt):
        '''Store off the 'savedSize' property used by Maya's QMainWindow to set the
        size of the widget when it is being docked.
        '''
        self.setProperty('savedSize', self.size())
        return super(MayaQDockWidget, self).resizeEvent(evt)


    def closeEvent(self, evt):
        '''Hide the QDockWidget and trigger the closeEventTriggered signal
        '''
        # Handle the standard closeEvent()
        super(MayaQDockWidget, self).closeEvent(evt)

        if evt.isAccepted():
            # Force visibility to False
            self.setVisible(False) # since this does not seem to have happened already

            # Emit that a close event is occurring
            self.closeEventTriggered.emit()


class MayaQWidgetDockableMixin(MayaQWidgetBaseMixin):
    '''
    Handle Maya dockable actions controlled with the show() function.

    Integration Notes:
        Inheritance ordering: This class must be placed *BEFORE* the Qt class for proper execution
        This is needed to workaround a bug where PyQt/PySide does not call super() in its own __init__ functions

    Example:
        class MyQWidget(MayaQWidgetDockableMixin, QPushButton):
            def __init__(self, parent=None):
                super(MyQWidget, self).__init__(parent=parent)
                self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred )
                self.setText('Push Me')
        myWidget = MyQWidget()
        myWidget.show(dockable=True)
        myWidget.show(dockable=False)
        print myWidget.showRepr()
    '''
    def setDockableParameters(self, dockable=None, floating=None, area=None, allowedArea=None, width=None, height=None, x=None, y=None, *args, **kwargs):
        '''
        Set the dockable parameters.

        :Parameters:
            dockable (bool)
                Specify if the window is dockable (default=False)
            floating (bool)
                Should the window be floating or docked (default=True)
            area (string)
                Default area to dock into (default='left')
                Options: 'top', 'left', 'right', 'bottom'
            allowedArea (string)
                Allowed dock areas (default='all')
                Options: 'top', 'left', 'right', 'bottom', 'all'
            width (int)
                Width of the window
            height (int)
                Height of the window
            x (int)
                left edge of the window
            y (int)
                top edge of the window

        :See: show(), hide(), and setVisible()
        '''
        if (dockable == True) or (dockable == None and self.isDockable()): # == Handle docked window ==
            # Conversion parameters (used below)
            dockAreaStrMap = {
                'left'   : Qt.LeftDockWidgetArea,
                'right'  : Qt.RightDockWidgetArea,
                'top'    : Qt.TopDockWidgetArea,
                'bottom' : Qt.BottomDockWidgetArea,
                'all'    : Qt.AllDockWidgetAreas,
                'none'   : Qt.NoDockWidgetArea,   # Note: Not currently supported in maya dockControl command
            }

            # Create dockControl (QDockWidget) if needed
            if dockable == True and not self.isDockable():
                # Retrieve original position and size
                # Position
                if x == None:
                    x = self.x()
                if y == None:
                    y = self.y()
                # Size
                unininitializedSize = QSize(640,480)  # Hardcode: (640,480) is the default size for a QWidget
                if self.size() == unininitializedSize:
                    # Get size from widget sizeHint if size not yet initialized (before the first show())
                    widgetSizeHint = self.sizeHint()
                else:
                    widgetSizeHint = self.size() # use the current size of the widget
                if width == None:
                    width = widgetSizeHint.width()
                if height == None:
                    height = widgetSizeHint.height()

                # Create the QDockWidget
                dockWidget = MayaQDockWidget()
                dockWidget.setWindowTitle(self.windowTitle())
                dockWidget.setWidget(self)

                # By default, when making dockable, make it floating
                #   This addresses an issue on Windows with the window decorators
                #   not showing up.  Setting this here will cause setFloating() to be called below.
                if floating == None:
                    floating = True

                # Hook up signals
                dockWidget.topLevelChanged.connect(self.floatingChanged)
                dockWidget.closeEventTriggered.connect(self.dockCloseEventTriggered)
            else:
                if floating == True:
                    # Retrieve original position (if floating)
                    pos = self.parent().mapToGlobal( QPoint(0,0) )
                    if x == None:
                        x = pos.x()
                    if y == None:
                        y = pos.y()

                # Retrieve original size
                if width == None:
                    width = self.width()
                if height == None:
                    height = self.height()

            # Get dock widget identifier
            dockWidget = self.parent()

            # Update dock values
            if area        != None:
                areaValue = dockAreaStrMap.get(area, Qt.LeftDockWidgetArea)
                dockWidget.setArea(areaValue)
            if allowedArea != None:
                areaValue = dockAreaStrMap.get(allowedArea, Qt.AllDockWidgetAreas)
                dockWidget.setAllowedArea(areaValue)
            if floating    != None:
                dockWidget.setFloating(floating)

            # Position window
            if dockWidget.isFloating() and ((x != None) or (y != None)):
                dockPos = dockWidget.mapToGlobal( QPoint(0,0) )
                if x == None:
                    x = dockPos.x()
                if y == None:
                    y = dockPos.y()
                dockWidget.move(x,y)
            if (width != None) or (height != None):
                if width == None:
                    width = self.width()
                if height == None:
                    height = self.height()
                # Perform first resize on dock, determine delta with widget, and resize with that adjustment
                # Result: Keeps the content widget at the same size whether under the QDockWidget or a standalone window
                dockWidget.resize(width, height) # Size once to know the difference in the dockWidget to the targetSize
                dockWidgetSize = dockWidget.size() + QSize(width,height)-self.size() # find the delta and add it to the current dock size
                # Perform the final resize (call MayaQDockWidget.resize() which also sets the 'savedSize' property used for sizing when docking to the Maya MainWindow)
                dockWidget.resize(dockWidgetSize)

        else:  # == Handle Standalone Window ==
            # Make standalone as needed
            if dockable == False and self.isDockable():
                # Retrieve original position and size
                dockPos = self.parent().mapToGlobal( QPoint(0,0) )
                if x == None:
                    x = dockPos.x()
                if y == None:
                    y = dockPos.y()
                if width == None:
                    width = self.width()
                if height == None:
                    height = self.height()
                # Turn into a standalone window and reposition
                currentVisibility = self.isVisible()
                self._makeMayaStandaloneWindow() # Set the parent back to Maya and remove the parent dock widget
                self.setVisible(currentVisibility)

            # Handle position and sizing
            if (width != None) or (height != None):
                if width == None:
                    width = self.width()
                if height == None:
                    height = self.height()
                self.resize(width, height)
            if (x != None) or (y != None):
                if x == None:
                    x = self.x()
                if y == None:
                    y = self.y()
                self.move(x,y)


    def show(self, *args, **kwargs):
        '''
        Show the QWidget window.  Overrides standard QWidget.show()

        :See: setDockableParameters() for a list of parameters
        '''
        # Update the dockable parameters first (if supplied)
        if len(args) or len(kwargs):
            self.setDockableParameters(*args, **kwargs)

        # Handle the standard setVisible() operation of show()
        QWidget.setVisible(self, True) # NOTE: Explicitly calling QWidget.setVisible() as using super() breaks in PySide: super(self.__class__, self).show()

        # Handle special case if the parent is a QDockWidget (dockControl)
        parent = self.parent()
        if isinstance(parent, QDockWidget):
            parent.show()


    def hide(self, *args, **kwargs):
        '''Hides the widget.  Will hide the parent widget if it is a QDockWidget.
        Overrides standard QWidget.hide()
        '''
        # Update the dockable parameters first (if supplied)
        if len(args) or len(kwargs):
            self.setDockableParameters(*args, **kwargs)

        # Handle special case if the parent is a QDockWidget (dockControl)
        parent = self.parent()
        if isinstance(parent, QDockWidget):
            parent.hide()

        QWidget.setVisible(self, False) # NOTE: Explicitly calling QWidget.setVisible() as using super() breaks in PySide: super(self.__class__, self).show()


    def setVisible(self, makeVisible, *args, **kwargs):
        '''
        Show/hide the QWidget window.  Overrides standard QWidget.setVisible() to pass along additional arguments

        :See: show() and hide()
        '''
        if (makeVisible == True):
            return self.show(*args, **kwargs)
        else:
            return self.hide(*args, **kwargs)


    def raise_(self):
        '''Raises the widget to the top.  Will raise the parent widget if it is a QDockWidget.
        Overrides standard QWidget.raise_()
        '''
        # Handle special case if the parent is a QDockWidget (dockControl)
        parent = self.parent()
        if isinstance(parent, QDockWidget):
            parent.raise_()
        else:
            QWidget.raise_(self)  # NOTE: Explicitly using QWidget as using super() breaks in PySide: super(self.__class__, self).show()


    def isDockable(self):
        '''Return if the widget is currently dockable (under a QDockWidget)

        :Return: bool
        '''
        parent = self.parent()
        return isinstance(parent, QDockWidget)


    def isFloating(self):
        '''Return if the widget is currently floating (under a QDockWidget)
        Will return True if is a standalone window OR is a floating dockable window.

        :Return: bool
        '''
        parent = self.parent()
        if not isinstance(parent, QDockWidget):
            return True
        else:
            return parent.isFloating()


    def floatingChanged(self, isFloating):
        '''Triggered when QDockWidget.topLevelChanged() signal is triggered.
        Stub function.  Override to perform actions when this happens.
        '''
        pass


    def dockCloseEventTriggered(self):
        '''Triggered when QDockWidget.closeEventTriggered() signal is triggered.
        Stub function.  Override to perform actions when this happens.
        '''
        pass


    def dockArea(self):
        '''Return area if the widget is currently docked to the Maya MainWindow
        Will return None if not dockable

        :Return: str
        '''
        dockControlQt = self.parent()

        if not isinstance(dockControlQt, QDockWidget):
            return None
        else:
            mainWindowPtr = omui.MQtUtil.mainWindow()
            mainWindow = wrapInstance(long(mainWindowPtr), QMainWindow)
            dockAreaMap = {
                Qt.LeftDockWidgetArea   : 'left',
                Qt.RightDockWidgetArea  : 'right',
                Qt.TopDockWidgetArea    : 'top',
                Qt.BottomDockWidgetArea : 'bottom',
                Qt.AllDockWidgetAreas   : 'all',
                Qt.NoDockWidgetArea     : 'none',   # Note: 'none' not supported in maya dockControl command
            }
            dockWidgetAreaBitmap = mainWindow.dockWidgetArea(dockControlQt)
            return dockAreaMap[dockWidgetAreaBitmap]


    def setWindowTitle(self, val):
        '''Sets the QWidget's title and also it's parent QDockWidget's title if dockable.

        :Return: None
        '''
        # Handle the standard setVisible() operation of show()
        QWidget.setWindowTitle(self, val) # NOTE: Explicitly calling QWidget.setWindowTitle() as using super() breaks in PySide: super(self.__class__, self).show()

        # Handle special case if the parent is a QDockWidget (dockControl)
        parent = self.parent()
        if isinstance(parent, QDockWidget):
            parent.setWindowTitle(val)


    def showRepr(self):
        '''Present a string of the parameters used to reproduce the current state of the
        widget used in the show() command.

        :Return: str
        '''
        reprDict = {}
        reprDict['dockable'] = self.isDockable()
        reprDict['floating'] = self.isFloating()
        reprDict['area']     = self.dockArea()
        #reprDict['allowedArea'] = ??
        if reprDict['dockable'] == True:
            dockCtrl = self.parent()
            pos = dockCtrl.mapToGlobal( QPoint(0,0) )
        else:
            pos = self.pos()
        sz  = self.geometry().size()
        reprDict['x'] = pos.x()
        reprDict['y'] = pos.y()
        reprDict['width'] = sz.width()
        reprDict['height'] = sz.height()

        # Construct the repr show() string
        reprShowList = ['%s=%r'%(k,v) for k,v in reprDict.items() if v != None]
        reprShowStr = 'show(%s)'%(', '.join(reprShowList))
        return reprShowStr
# Copyright (C) 1997-2014 Autodesk, Inc., and/or its licensors.
# All rights reserved.
#
# The coded instructions, statements, computer programs, and/or related
# material (collectively the "Data") in these files contain unpublished
# information proprietary to Autodesk, Inc. ("Autodesk") and/or its licensors,
# which is protected by U.S. and Canadian federal copyright law and by
# international treaties.
#
# The Data is provided for use exclusively by You. You have the right to use,
# modify, and incorporate this Data into other products for purposes authorized
# by the Autodesk software license agreement, without fee.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. AUTODESK
# DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTIES
# INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF NON-INFRINGEMENT,
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR ARISING FROM A COURSE
# OF DEALING, USAGE, OR TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS
# LICENSORS BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL,
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK AND/OR ITS
# LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY OR PROBABILITY OF SUCH DAMAGES.
#endregion

# ************************************
#
# Replacing ctrl curve by mesh.
# Idea by Jason Schleifer: https://vimeo.com/155562003
#
# ************************************

import maya.cmds as cmds
import maya.mel as mel
import os

import maya.OpenMayaUI as mui

import datetime
import traceback
import sys
import threading
import urllib2
try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    print "Using PySide2"

except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance
    print "Using PySide"
from maya import OpenMayaUI as omui
#from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import webbrowser
import platform
currentVersion = '1.0.6'

def getOS():
    try:
        osString = "{} {} ({})".format(platform.system(), platform.release(), platform.version())
    except:
        osString = ''
    return osString

def getMayaVersion():
    return cmds.about(iv=True)

errorText = "\n=========== Oh, uh, seems there is an error? ============"
realPath = os.path.dirname(os.path.realpath(__file__))
controlMeshCreatorCss = os.path.join(realPath, 'controlMeshCreator.css')

def convertToQt(mayaName, objectType):
    """
    Given the name of a Maya UI element of any type, return the corresponding QT Type object.
    """
    ptr = mui.MQtUtil.findControl(mayaName)
    if ptr is None:
        ptr = mui.MQtUtil.findLayout(mayaName)
        if ptr is None:
            ptr = mui.MQtUtil.findMenuItem(mayaName)
    if ptr is not None:
        return wrapInstance(long(ptr), objectType)

class BroRig_Error(Exception):
    pass


def try_except(fn):
    """
    BroRig exception wrapper. Use @try_except above the function to wrap it.
    Args:
        fn: function to wrap

    Returns:
        wrapped: wrapped function
    """

    def wrapped(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True)
            result = fn(*args, **kwargs)
            cmds.undoInfo(closeChunk=True)
            return result
        except Exception, e:
            cmds.undoInfo(closeChunk=True)
            gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

            et, ei, tb = sys.exc_info()
            print errorText, '\n'
            print "ERROR IN:", fn.__name__, "Function."
            print e, "\n"
            print traceback.print_exc(), '\n'
            print "====================HELP======================"
            print fn.__doc__, '\n'
            print "====================ERROR====================="
            cmds.inViewMessage( amg='<span style=\"color:#F05A5A;\">Error: </span>' + str(e)+' <span style=\"color:#FAA300;\">More info in script editor.</span>', pos='topCenter', fade=True, fst=2000, dk=True)
            raise BroRig_Error, BroRig_Error(e), tb

    return wrapped

def log(type='', *args):
    time = str(datetime.datetime.now())
    prefix = type*3
    text = ''
    for item in args:
        text += ' '
        text += str(item)
    print prefix,time+":",text


def inViewLog(color='', *args):
    text = ''
    for item in args:
        text += ' '
        text += str(item)

    log ('', text)
    if color != '':
        text = "<span style=\"color:{0};\">{1}</span>".format(color, text)

    cmds.inViewMessage(amg=text, pos='topCenter', fade=True, fst=1000, dk=True)


def getVersionActual():
    try:
        text = ''
        data = urllib2.urlopen("https://dl.dropboxusercontent.com/s/coix2knwx19lojx/latestVersion.txt").read(5)
        data2 = urllib2.urlopen("https://dl.dropboxusercontent.com/s/7lj5gogw41svizr/changeLog.txt").read()
        match = 'Your version is up-to-date.'
        stat = ""
        if data != currentVersion:
            match = 'New version available!'
        inViewLog("#00FF00", match)
        text = "\n\n////////// Control Mesh Creator Info //////////\n{0}\nYour version: {1}; Latest version: {2} \n {3}".format(match, currentVersion, data, data2)
        print text


    except:
        inViewLog("#FFFF00", "Unable to obtain data online.")

def getVersion():
    inViewLog('#00FF00', 'Information will be printed in script editor in a moment.\n')
    log ("<", 'Downloading version information...')
    download_thread = threading.Thread(target=getVersionActual)
    download_thread.start()

def getDistance(obj1, obj2, areObjects = True, log=True):
    """
    Get distance between two objects. No nodes used.
    Args:
        obj1(str): Obj 1
        obj2(str): Obj 2

    Returns(float): Distance

    """
    if log:
        print ">>>", obj1, obj2
    if areObjects:
        Ax, Ay, Az = cmds.xform(obj1, q=True, ws=True, t=True)
        Bx, By, Bz = cmds.xform(obj2, q=True, ws=True, t=True)
    else:
        Ax, Ay, Az = obj1[0], obj1[1], obj1[2]
        Bx, By, Bz = obj2[0], obj2[1], obj2[2]
    dist = ((Ax - Bx) ** 2 + (Ay - By) ** 2 + (Az - Bz) ** 2) ** 0.5
    if log:
        print "DISTANCE:", dist
    return dist

@try_except
def replaceCtrlWithMesh(sel, mesh, deleteOld = False, hideOld = True, autoSelect = True, autoDelete = True, distanceThreshold = 5, shiftAxis = 0, shift = 5, push = True, pushDistance = 0.1, refresh=False):
    if sel < 1:
        cmds.error ("Nothing is selected. You need to select at least 1 control object.")

    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')

    cmds.progressBar(gMainProgressBar,
                     edit=True,
                     beginProgress=True,
                     isInterruptable=True,
                     status='...',
                     maxValue=5000)

    selectedVerts = cmds.ls(sl=True, fl=True)
    object = selectedVerts[0].split(".vtx")[0]
    vertsTotal = cmds.polyEvaluate(object, v=True)

    steps = 4
    if autoSelect:
        steps = 5

    cmds.progressBar(gMainProgressBar, e=True, maxValue=len(sel*steps))
    cmds.progressBar(gMainProgressBar, edit=True, pr=0)
    cmds.progressBar(gMainProgressBar, edit=True, status='Curve replacer working...')

    startTime = datetime.datetime.now()
    remainingTime = 0

    for idx, ctrl in enumerate(sel):
        if cmds.progressBar(gMainProgressBar, query=True, isCancelled=True):
            break

        cmds.progressBar(gMainProgressBar, edit=True, status="Time remaining: "+str(remainingTime))

        if hideOld:
            oldShapes = cmds.listRelatives(ctrl, shapes=True)
            for s in oldShapes:
                cmds.setAttr(s+'.visibility', 0)


        if deleteOld:
            cmds.delete(cmds.listRelatives(ctrl, shapes=True))
        cmds.progressBar(gMainProgressBar, edit=True, step=1, status="Time remaining: "+str(remainingTime))


        meshNode = cmds.createNode ('mesh', parent=ctrl, n=ctrl+'MeshShape')
        transformNode = cmds.createNode('transformGeometry')

        cmds.connectAttr (cmds.listRelatives(mesh, shapes=1)[0]+'.outMesh', transformNode+'.inputGeometry')
        cmds.connectAttr (transformNode+'.outputGeometry', meshNode+'.inMesh')
        cmds.connectAttr (ctrl+'.worldInverseMatrix', transformNode+'.transform')
        cmds.progressBar(gMainProgressBar, edit=True, step=1, status="Time remaining: "+str(remainingTime))

        if pushDistance > 0:
            cmds.select(ctrl, r=1)
            pushNode = cmds.polyMoveVertex(ltz=pushDistance)

        if autoSelect:
            vertsTotal = cmds.polyEvaluate(meshNode, v=True)
            allVerts = []
            unselectedVerts = []
            vPs = {}

            for i in range(0, vertsTotal):
                vert = meshNode + '.vtx[' + str(i) + ']'
                allVerts.append(vert)
                vPs[vert] = cmds.xform(vert, q=True, translation=True, ws=True)


            ctrlPos = cmds.xform(ctrl, q=1, ws=1, t=1)
            ctrlPos[shiftAxis] += shift
            minDistVx = ''
            prevDist = 9999999999
            vertsToDelete = []
            cmds.progressBar(gMainProgressBar, edit=True, step=1, status="Time remaining: "+str(remainingTime))
            for idd, v in enumerate(allVerts):
                vPos = vPs[v]
                dist = getDistance(vPos, ctrlPos, areObjects=0, log=0)
                if dist > distanceThreshold:
                    vertsToDelete.append(v)

            cmds.progressBar(gMainProgressBar, edit=True, step=1, status="Time remaining: "+str(remainingTime))
            facesToDelete = cmds.polyListComponentConversion(vertsToDelete, fv=True, tf=True, internal=True )
            cmds.select (facesToDelete, r=True)
            if autoDelete:
                cmds.delete()
        averageTime = (datetime.datetime.now()-startTime)/(idx+1)
        remainingTime = (averageTime*len(sel))-(averageTime*(idx+1))



        cmds.select(meshNode, r=True)
        if refresh:
            cmds.refresh()
        cmds.progressBar(gMainProgressBar, edit=True, step=1, status="Time remaining: "+str(remainingTime))
    cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

'''
class BatchWindow(MayaQWidgetBaseMixin, QDialog):
    def __init__(self, rootWidget=None, *args, **kwargs):
        super(BatchWindow, self).__init__(*args, **kwargs)

        # Determine root widget to scan
        if rootWidget != None:
            self.rootWidget = rootWidget
        else:
            mayaMainWindowPtr = omui.MQtUtil.mainWindow()
            self.rootWidget = wrapInstance(long(mayaMainWindowPtr), QWidget)
'''

class controlMeshCreatorWindow(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self, rootWidget=None, *args, **kwargs):
        super(controlMeshCreatorWindow, self).__init__(*args, **kwargs)

        # Determine root widget to scan
        if rootWidget != None:
            self.rootWidget = rootWidget
        else:
            mayaMainWindowPtr = omui.MQtUtil.mainWindow()
            self.rootWidget = wrapInstance(long(mayaMainWindowPtr), QWidget)

        self.cWidget = QWidget()
        self.setCentralWidget(self.cWidget)

        # Destroy this widget when closed.  Otherwise it will stay around
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        with open(controlMeshCreatorCss) as styleSheetFile:
            self.setStyleSheet(styleSheetFile.read())

        self.setWindowTitle("MeshControlCreator")
        #self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.label = QLabel("http://www.nixes.ru")
        self.versionLabel = QLabel("v"+currentVersion)
        self.versionLabel.setAlignment(Qt.AlignRight)

        self.meshNameLayout = QHBoxLayout()
        self.meshNameLayout.setAlignment(Qt.AlignTop)
        self.meshName = QLineEdit()
        self.meshName.setPlaceholderText("Geometry to use.")
        self.meshNameBtn = QPushButton("Set")
        self.meshNameBtn.setFixedWidth(30)
        self.meshNameBtn.clicked.connect(self.setMeshName)
        self.meshNameLayout.addWidget(self.meshName)
        self.meshNameLayout.addWidget(self.meshNameBtn)

        self.formLayout = QFormLayout()
        self.formLayout.setLabelAlignment(Qt.AlignRight)
        self.formLayout.setAlignment(Qt.AlignRight)
        self.formLayout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.hideOld = QCheckBox()
        self.hideOld.setChecked(True)
        self.hideOld.setStatusTip("Will hide all shapes from control except the newly created mesh-shape. You will be able to unhide them if needed.")

        self.deleteOld = QCheckBox()
        self.deleteOld.setChecked(False)
        self.deleteOld.setStatusTip("Will remove all shapes from control before creating new mesh-shape.")

        self.autoSelect = QCheckBox()
        self.autoSelect.setChecked(True)
        self.autoSelect.setStatusTip("Will select faces, which are outside the distance threshold.")

        self.autoDelete = QCheckBox()
        self.autoDelete.setChecked(True)
        self.autoDelete.setStatusTip("Will delete faces, which are outside the distance threshold. autoSelect must be active.")

        self.distanceThreshold = QDoubleSpinBox()
        self.distanceThreshold.setDecimals(3)
        self.distanceThreshold.setSingleStep(0.1)
        self.distanceThreshold.setValue(5.0)
        self.distanceThreshold.setRange(-999999999,999999999)
        self.distanceThreshold.setStatusTip("Distance to select and\or delete faces by. Used for autoSelect and autoDelete.")

        self.shiftAxis = QSpinBox()
        self.shiftAxis.setRange(0,2)
        self.shiftAxis.setStatusTip("X,Y,Z = 0,1,2. Allows you to shift automatic selection center point away from control.")

        self.shift = QDoubleSpinBox()
        self.shift.setDecimals(3)
        self.shift.setSingleStep(0.1)
        self.shift.setValue(5.0)
        self.shift.setRange(-999999,999999)

        self.pushDistance = QDoubleSpinBox()
        self.pushDistance.setDecimals(3)
        self.pushDistance.setSingleStep(0.1)
        self.pushDistance.setValue(0.1)
        self.pushDistance.setRange(-999999999,999999999)
        self.pushDistance.setStatusTip("Mesh of control will be pushed outwards, to make it visible and selectable above the original mesh. Negative value will push it inward.")

        self.refresh = QCheckBox()
        self.refresh.setChecked(False)

        self.formLayout.addRow(("&Hide old shape"), self.hideOld)
        self.formLayout.addRow(("&Delete old shape"), self.deleteOld)
        self.formLayout.addRow(("&Auto Select"), self.autoSelect)
        self.formLayout.addRow(("&Auto Delete"), self.autoDelete)
        self.formLayout.addRow(("&Distance Threshold"), self.distanceThreshold)
        self.formLayout.addRow(("&Shift Axis"), self.shiftAxis)
        self.formLayout.addRow(("&Shift Distance"), self.shift)
        self.formLayout.addRow(("&Push Distance"), self.pushDistance)
        self.formLayout.addRow(("&Refresh viewport"), self.refresh)

        self.doButton = QPushButton("Generate")
        self.doButton.clicked.connect(self.replaceCurve)
        self.doButton.setStatusTip("Run creation procedure.")



        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.hLine = QFrame()
        self.hLine.setFrameShape(QFrame.HLine)
        self.hLine.setFrameShadow(QFrame.Sunken)



        self.mainLayout.addLayout(self.meshNameLayout)
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(self.doButton)
        self.mainLayout.addWidget(self.hLine)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.versionLabel)

        self.cWidget.setLayout(self.mainLayout)

        #regeion Menu bar
        menuBar = QMenuBar()
        helpMenu = menuBar.addMenu(("&Help"))

        DocumentationAction = QAction(("&Documentation"), self)
        DocumentationAction.triggered.connect(lambda: self.openWebUrl('http://nixes.ru/?page_id=505'))
        helpMenu.addAction(DocumentationAction)

        BugReportAction = QAction(("&Bug report"), self)
        BugReportAction.triggered.connect(lambda: self.openWebUrl('https://docs.google.com/forms/d/e/1FAIpQLSeuVYcOwnxh__FTszuA3OhPnj7kGGX8xiBTGB6pvvUnzQm9fQ/viewform?entry.1842004859&entry.1101948584={0}&entry.1455089707={1}&entry.688648412&entry.757481838'.format(getMayaVersion(), getOS())))
        helpMenu.addAction(BugReportAction)

        UsageSurveyAction = QAction(("&Usage survey"), self)
        UsageSurveyAction.triggered.connect(lambda: self.openWebUrl('http://goo.gl/forms/cTmbOxhLOBBFKwd83'))
        helpMenu.addAction(UsageSurveyAction)

        aboutAction = QAction(("&Check for updates"), self)
        aboutAction.triggered.connect(getVersion)
        helpMenu.addAction(aboutAction)
        aboutAction.setStatusTip("Try to check for updates online. Will also print changelog. Info will be printed in script editor.")

        self.setMenuBar(menuBar)

        #endregion



        self.setFocus()

    def openWebUrl(self, url=None):
        if url != None:
            try:
                webbrowser.open(url)
            except Exception as e:
                log.log('warning', 'Tried to open web-link, but experienced an error:',e)
        else:
            log.log("Tried to open web-link, but no link provided.")

    @try_except
    def replaceCurve(self):
        if self.meshName.text() == '':
            cmds.error ("No mesh provided. Please, add mesh to mesh input field.")

        if cmds.objExists(self.meshName.text()) != True:
            cmds.error ("Object "+str(self.meshName.text())+" was not found. Please, make sure there are no mistakes in object's name.")

        replaceCtrlWithMesh(cmds.ls(sl=True), mesh=self.meshName.text(), deleteOld = self.deleteOld.isChecked(), hideOld = self.hideOld.isChecked(),
                            autoSelect = self.autoSelect.isChecked(), autoDelete = self.autoDelete.isChecked(), distanceThreshold = self.distanceThreshold.value(),
                            shiftAxis = self.shiftAxis.value(), shift = self.shift.value(), pushDistance=self.pushDistance.value(), refresh=self.refresh.isChecked())

    def setMeshName(self):
        self.meshName.setText(cmds.ls(sl=True, l=True)[0])


def getMayaWindow():
        pointer = mui.MQtUtil.mainWindow()
        return wrapInstance(long(pointer),QWidget)

def initUI():
    broControlCurveReplacer_WindowName = "broControlCurveReplacer_Window"

    global broControlcontrolMeshCreatorWindow

    if cmds.window(broControlCurveReplacer_WindowName, ex=True):
        cmds.deleteUI (broControlCurveReplacer_WindowName, wnd=True)


    #create a window
    parent = getMayaWindow()

    broControlcontrolMeshCreatorWindow = controlMeshCreatorWindow(parent)
    broControlcontrolMeshCreatorWindow.setObjectName(broControlCurveReplacer_WindowName)
    broControlcontrolMeshCreatorWindow.show()
    currentSize = broControlcontrolMeshCreatorWindow.size()
    broControlcontrolMeshCreatorWindow.setFixedSize(currentSize)
    log (":", "UI initialized.")

