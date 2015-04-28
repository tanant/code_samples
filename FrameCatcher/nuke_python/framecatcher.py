#FFS. I hate file i/o and the compacting.

''' 
You'll also need these in the write node under the python tab

before render:  
    import TT_utilities.framecatcher as fcs; 
    reload(fcs); 
    fc_context = fcs.FrameCatcher( debug = False, context = nuke.thisNode(), prefix = '.'.join(os.path.basename(nuke.thisNode()['file'].evaluate()).split('.')[0:-2]), enable = nuke.toNode('.'.join(nuke.thisNode().fullName().split('.')[0:-1]))['fc_enable'].value(), padding = 4)

before frame:
    fc_context.before_frame()

after frame:
    fc_context.after_frame()

after render:
    fc_context.after_render(cleanup=True)
'''


from __future__ import print_function

import os
import sys
import re
import shutil
import nuke
import uuid

# FIRSTFRAMESTRING = "FIRSTFRAME.txt"
# uuid in place to support mulitple instances being used and avoiding conflicts
FIRSTFRAMESTRING = uuid.uuid4().hex + '.txt'
FC_LOG_SUBDIR = "framecatcher_logs"

# I could inherit nuke.node.. but no. everything depends on nuke context node.
# must be called from the relevant before script
class FrameCatcher(object):
    """A class of support functions to be paired with the FrameCatcher C++ plugin to enable render-time frame inspection."""
    
    def __init__(self, **kwargs):
        try:
            self._padding = int(kwargs['padding'])
        except:
            self._padding = 7

        try:
            self._prefix = kwargs['prefix']
        except:
            self._prefix = "frame_report"

            
        try:
            self._enable = kwargs['enable']
        except:
            self._enable = False

        self._context = kwargs['context']
        self._catchers = []
        self._firstframe = True
        try:
            self._debug  = kwargs['debug']
        except:
            self._debug = False
        
        self._bootstrap(debug = self._debug)
        
        
    def _bootstrap(self, debug = False):
        """Completes framecatcher rig initialisation by creating directories and padding node variables.
        
        As we don't have access to shared memory at this point, we use text 
        file stubs as a synchronisation system with a post-frame compact phase.
        
        It's a bit messy, I know.
        """
        
        if self._enable == True:
            sweep_catchers()    # clear out all the frame catchers
        
            # based on the context, we will be peeking at the file knob
            logdir = os.path.join(os.path.dirname(self._context['file'].evaluate()), FC_LOG_SUBDIR)
            
            root_dir = logdir.replace('\\','/')
            
            # should we delegate this out? 
            # bootstrapping is not multisystem aware.. which is fine actually.
            try:
                os.makedirs(root_dir)
            except OSError as e:
                shutil.rmtree(root_dir)
                os.makedirs(root_dir)
                pass
            
            # now stick in a whole bunch of framecatchers with the right boot string
            self._catchers = []
            framestring = FIRSTFRAMESTRING
            iterateAllNodes(triggerFn = lambda x: x.Class() == 'Read', 
                            opFn = lambda x: self._catchers.append(inject_nodeclass('FrameCatcher', x)))
                            
            for fc in self._catchers:
                fc['frame_fragment'].setValue(framestring)
                fc['root_fragment'].setValue(root_dir)
                fc['out_file'].setValue('[value root_fragment]/[value name].[value frame_fragment]')
                fc['label'].setValue('[value out_file]')
                fc['column_header'].setValue('[python nuke.thisNode().input(0).fullName()]')
                fc['disable'].setValue(False)
                fc['monitor_enable'].setValue(True)
                fc['write_enable'].setValue(True)
                fc['cout_override'].setValue(debug)
                fc['clock'].setValue(not fc['clock'].value())              
        else:
            # print("FALSE")
            pass
            
    
    def before_frame(self):
        """Function call before frame render in the Write node.
        
        This function sets up the output file target matched to frame number, 
        enables monitoring, and twiddles the clock bit to force the upstream cook.
        """
        if self._enable == True:
            framestring = '{frm:0' + str(self._padding) + 'd}.txt'
            framestring = framestring.format(frm=nuke.frame()+1)
            for fc in self._catchers:
                fc['frame_fragment'].setValue(framestring)
                fc['monitor_enable'].setValue(True)
                fc['write_enable'].setValue(True)
                fc['disable'].setValue(False)
                fc['clock'].setValue(not fc['clock'].value())  
                # this single line slows down everything by invalidating the cache from the 
                # read node on each frame - this will report more accurately multiframe blends
                # it also seems to make things er. Work.

    def after_frame(self):
        """writes out a single file per framecatcher, and then compacts this into one large file."""
        if self._enable == True:
            if self._firstframe:
                self._firstframe = False
                for fc in self._catchers:
                    hackframestring = '{frm:0' + str(self._padding) + 'd}.txt'
                    hackframestring = hackframestring.format(frm=nuke.frame()) 
                    oldname =  re.sub(fc['frame_fragment'].evaluate(), FIRSTFRAMESTRING, fc['out_file'].evaluate())
                    newname = re.sub(fc['frame_fragment'].evaluate(), hackframestring, fc['out_file'].evaluate())
                    try:
                        os.remove(newname)  
                    except:
                        pass
                    
                    # oh FFS. this assumes an output was generated, which 
                    # isn't the case when you have read nodes that aren't connected
                    try:    
                        os.rename(oldname, newname)
                    except:
                        pass
            
            # we should deal with this. But later. It's such an annoying fix required..
            # this is a weird +1/-1 offset strangeness
            # just using the first one in the list. FuryFX pipeline doesn't support
            # the more complex general case yet..
    
            newfile_prefix = self._prefix
            rootdir = self._catchers[0]['root_fragment'].evaluate()
            framestring = '{frm:0' + str(self._padding) + 'd}.txt'
            framestring = framestring.format(frm=nuke.frame())
            candidates = os.listdir(rootdir)
            candidates = [x for x in candidates if os.path.isfile(os.path.join(rootdir,x)) and x.endswith(framestring)]
            compacted_output = os.path.join(rootdir, newfile_prefix + '.' + framestring)
            
            try:
                os.remove(compacted_output)
            except:
                pass
            with open(compacted_output, 'w') as fp_out:
                for x in candidates:
                    with open(os.path.join(rootdir, x)) as fp_in:
                        lines = fp_in.readlines()
                        fp_out.write(''.join(lines))
            for x in candidates:
                os.remove(os.path.join(rootdir, x)) # delayed cleanup. If this is called within the
                # with/for clause loop we get file locking issues. Basically, the file unlocking 
                # is not happing fast enough unless you jump out the second with clause. This bites.
        
    def after_render(self, cleanup=True):
        """delete all framecatcher nodes from an artist's comp script."""
        if self._enable == True:
            # this does cleanup of the framecatchers
            for fc in self._catchers:
                fc['monitor_enable'].setValue(False)
                fc['write_enable'].setValue(False)
                fc['disable'].setValue(True)
                if cleanup:
                    nuke.delete(fc)
            pass

    def Class(self):
        return self._context.Class()
    
    def fullName(self):
        return self._context.fullName()
    
    def isFirstFrame(self):
        return self._firstframe
    
    def setFirstFrame(self, value):
        self._firstframe = value
        
    def getCatchers(self):
        return self._catchers

# these are just some functions to pass through to the below 
# for all nodes
def _disable_FC(node):
    """internal only - sets the relevant flags for a 'disabled' state"""
    node['disable'].setValue(True)
    node['monitor_enable'].setValue(False)
    node['write_enable'].setValue(False)
    
    
def find_catchers():
    """Convenience function to print out fullname of all FrameCatcher instances."""
    iterateAllNodes(triggerFn = lambda x: x.Class() == 'FrameCatcher', 
                    opFn = lambda x: print(x.fullName()) )
    
def debug_catchers():
    """Convenience function to set debug mode on all FrameCatcher instances."""
    iterateAllNodes(triggerFn = lambda x: x.Class() == 'FrameCatcher', 
                    opFn = lambda x: x['cout_override'].setValue(True) )
                    
def disable_catchers():
    """Convenience function to disable all FrameCatcher instances."""
    iterateAllNodes(triggerFn = lambda x: x.Class() == 'FrameCatcher', 
                    opFn = _disable_FC)

def sweep_catchers():
    """Convenience function to delete all FrameCatcher instances."""  
    iterateAllNodes(triggerFn = lambda x: x.Class() == 'FrameCatcher', 
                    opFn = lambda x: nuke.delete(x))

                    

def iterateAllNodes(rootnode = None, triggerFn=None, opFn=None, deep = True):
    """from a given root level apply a certain function (opFn) to any node which makes a trigger return True (triggerFn).
    
    Defaults (assuming None supplied are:
    root -  nuke.root(), 
    trigger - True (i.e. always fires)
    operation - print node's fullName
    deep - True (i.e. will recurse into groups as far as it can)
    """
    if rootnode == None:
        rootnode = nuke.root()
    
    if triggerFn == None:
        triggerFn = lambda x: True
     
    if opFn == None:
        opFn = lambda x: print(x.fullName())
        
    with rootnode:
        for x in nuke.allNodes():
            if x.Class() == 'Group' and deep:
                iterateAllNodes(rootnode = x, triggerFn = triggerFn, opFn = opFn, deep = deep)    # recurse
            elif triggerFn(x):
                opFn(x)
      

def inject_nodeclass(node_class, after_here, move = True):
    """Inserts a copy of the node of class spec'd downstream."""
    for x in nuke.allNodes():
        try:
            x['selected'].setValue(False)
        except:
            pass    # this whole try/except is to catch dots which don't have a 'selected' attrib
    after_here['selected'].setValue(True)
    node = nuke.createNode(node_class, inpanel=False)
    return node


if __name__ == '__main__':
    '''
    tests = r'C:\Users\OM005188\Desktop\fc_logs'
    files_to_process = os.listdir(tests)
    for x in files_to_process:
        print(x)
    
    # standard is that we split on dots.
    # signature = before and after
    ts1 = r'path//ext/soemthing.a453-x023.989762.001.jpg'
    frame = ts1.split('.')[-2]
    print (frame)
    print (ts1.split(frame))
    
    x = SourceSignature(r'c:/akjhs/sghot/CY2_099/fishandchips.', None, '.jpg')
    tstring = r'c:/akjhs/sghot/CY2_099/fishandchips.123456.jpg'
    print (x)
    resp= x.re_search_pattern()
    print (resp.pattern) 
    print(re.match(resp,tstring).group('frame'))
    '''
    pass