__author__ = 'rgriffin'

"""
Helper module for creating PySide UI
"""

from Qt import QtWidgets, QtGui, QtCore
import os, sys

def createButton(text, bgc, fnt, mins, maxs, command, icon, *args):
    """
    Creates a PySide button and binds a command
    :param bgc: The button bg color. [1,1,1]
    :type bgc: tuple
    :param fnt: Setpoint size, bold, and color. [12, True, [1,1,1]]
    :type fnt: list
    :param mins: Minimum button size
    :param maxs: Maximum button size
    :param command:  Command to bind to the button
    :param icon: If True, provide the icon path, else False
    :return: button
    """

    # Create a font
    font = QtGui.QFont()
    font.setPointSize(fnt[0])
    font.setBold(fnt[1])

    # Create a button
    button = QtWidgets.QPushButton(text)
    #layout.addWidget(button)
    button.setFont(font)
    button.setMinimumSize(mins[0], mins[1])
    button.setMaximumSize(200, 40)

    if icon[0] == True:
        button.setStyleSheet("background-image: url(" + icon[1] + "); border: solid black 1px; color: rgb(bgc);")
    else:
        button.setStyleSheet("background-color: rgb(fnt[2]); color: rgb(bgc);")

    button.clicked.connect(command)

    return button