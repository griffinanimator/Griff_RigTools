__author__ = 'rgriffin'

"""
Utility functions used in layout objects.
"""

from pymel.core import *
import os

def createPartContainer(name):
    """
    Creates a Asset used for rig parts
    :param name:  The name of the asset
    :type name: string
    :return: [partcon, localgrp, worldgrp, inputloc]
    """

    # dictionary to store asset information
    asset_info = {}

    # Create the main part asset
    asset_info['partasset'] = container(name=name + '_Part')
    setAttr('%s.containerType' % asset_info['partasset'], 'Part', type="string")


    # Create the layout asset
    asset_info['layoutasset'] = setupAsset(name, '_Layout')

    # Create the rig asset
    asset_info['rigasset'] = setupAsset(name, '_Rig')


    container(asset_info['partasset'], edit=True, an=asset_info['layoutasset'][0], inc=True, force=True)
    container(asset_info['partasset'], edit=True, an=asset_info['rigasset'][0], inc=True, force=True)

    setAttr(asset_info['partasset'] + '.iconName', os.environ['RIG_TOOL'] + '/icon/part_icon.png')
    setAttr(asset_info['layoutasset'][0] + '.iconName', os.environ['RIG_TOOL'] + '/icon/layout_icon.png')
    setAttr(asset_info['rigasset'][0] + '.iconName', os.environ['RIG_TOOL'] + '/icon/rig_icon.png')

    return (asset_info)

def setupAsset(name, prefix):
    if objExists(name + prefix):
        return ('This asset already exists')
    else:
        partcon = container(name=name + prefix)

    # Create a group that serves as the assets selection transform
    localgrp = group(em=True, n=name + prefix + '_local')

    # Create a group to hold nodes that are left in world space.
    worldgrp = group(em=True, n=name + prefix + '_world')

    # Add both groups to the asset
    container(partcon, edit=True, an=localgrp)
    container(partcon, edit=True, an=worldgrp)

    # Publish the selection transform
    container(partcon, edit=True, publishAsRoot = [localgrp, 1])

    # Create a locator to serve as the input connection for transforms.
    inputloc = spaceLocator(n=name + prefix + '_input')
    setAttr(inputloc + 'Shape.visibility', 0)
    container(partcon, edit=True, an=inputloc)
    parent(localgrp, inputloc)

    # Publish the locator transforms to the asset.
    container(partcon, edit=True, publishName='INPUT_T')
    container(partcon, edit=True, publishName='INPUT_R')
    container(partcon, edit=True, publishName='INPUT_S')

    container(partcon, edit=True, bindAttr=['%s.translate'% inputloc, 'INPUT_T'])
    container(partcon, edit=True, bindAttr=['%s.rotate' % inputloc, 'INPUT_R'])
    container(partcon, edit=True, bindAttr=['%s.scale' % inputloc, 'INPUT_S'])

    # Set the containers type attribute.
    assettype = prefix.rpartition('_')[2]

    setAttr('%s.containerType' % partcon, assettype, type="string")

    return ([partcon, localgrp, worldgrp, inputloc])


def publishToPartContainer(partcon, nodelist, pubnodes):
    """
    Publish a list of nodes to an asset
    :param nodelist: The node to be published and the name to publish as.
    :param partcon: The asset to bind to..
    :return:
    """

    if nodelist:
        for n in nodelist:
            # See if the node is already part of the asset.
            assetcontents = container(partcon, q=True, nl=True)
            if n in assetcontents:
                pass
            else:
                # If not, add the node
                try:
                    container(partcon, edit=True, an=n, force=True, ihb=True)
                except: pass

    if pubnodes:
        try:
            containerPublish(partcon, inConnections=True, mergeShared=True)
            for n in pubnodes:
                containerPublish(partcon, publishNode=[n[0], n[1]])
                containerPublish(partcon, bindNode=[n[0], n[0]])
        except: pass

def findTopLevelAsset():
    selcon = None
    if ls(sl=True):
        sel = ls(sl=True)[0]

        if nodeType(sel) == 'container' and '_Part' not in sel:
            # Try to find the top level container
            tmpcon = container(parcon, q=True, par=True)[0]
            if '_Part' in tmpcon:
                selcon = tmpcon

        elif nodeType(sel) != 'container':
            # Find the parent part container
            parcon = container(q=True, fc=sel)
            if parcon:
                if '_Part' in str(parcon):
                    selcon = parcon
                else:
                    # Try to find the top level container
                    tmpcon = container(parcon, q=True, par=True)
                    if tmpcon:
                        if '_Part' in tmpcon[0]:
                            selcon = tmpcon[0]

        else:
            if nodeType(sel) == 'container':
                selcon = sel

    if selcon:
        return selcon
    else:
        return "nothing selected"



