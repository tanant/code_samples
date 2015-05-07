'''
maya_tools.py

assistive tools for setting maya projects and general ancillary functions

2013-04-30-AT: Created
'''
import maya.cmds as mc
import pymel.core as pm
import maya.mel as mel


def setProject(projectdir, forceReset=False):
    '''Sets a project directory and simulates three button presses to open
    the Maya Project window, reset the fields to factory default,
    and then pressing Accept to create the directories.
    '''

    pm.workspace.mkdir(projectdir)
    pm.workspace.open(projectdir)
    if pm.workspace.fileRules.keys() == [] or forceReset:
        cmds_string = r"ProjectWindow; np_resetAllFileRulesTextFields; np_editCurrentProjectCallback;"
        mel.eval(cmds_string)
    else:
        print ("project partially set up, not resetting dirstructures")


def loadFile(shotfile=None):
    '''A simple wrapper to load a file and set up project and pathing

    Mimicks the standard maya dialog with a propmt to save unsaved changes
    leaving the call as 'none' is a new file target situation.

    Returns False if cancel clicked and further actions should stop.
    '''
    scenename = pm.sceneName()
    if len(scenename) == 0:
        scenename = 'Untitled Scene'

    try:
        if shotfile is None:
            pm.newFile()
        else:
            pm.openFile(shotfile)
    except RuntimeError:
        result = pm.confirmDialog(title='Unsaved Changes',
                                  message='Save changes to {0}?'.format(
                                      scenename),
                                  button=['Save', "Don't Save", 'Cancel'],
                                  defaultButton='Yes',
                                  cancelButton='Yes', dismissString='No')
        if result == 'Cancel':
            return False
        else:
            if result == 'Save':
                if scenename == 'Untitled Scene':
                    pm.fileDialog2()
                else:
                    pm.saveFile()
            if shotfile is None:
                pm.newFile(force=True)
            else:
                pm.openFile(shotfile, force=True)

    return True


def newFile():
    '''stub function, a straight pass through to our core helper function'''
    return loadFile(None)


def toggle_renderthumbs():
    if pm.renderThumbnailUpdate(query=True):
        pm.renderThumbnailUpdate(False)
    else:
        pm.renderThumbnailUpdate(True)


def set_renderthumbs(state):
    pm.renderThumbnailUpdate(state)
