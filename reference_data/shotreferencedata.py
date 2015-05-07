import os
import sys
import re
import shutil
import subprocess
import tempfile


class ReferenceDataConstants(object):
    # mainly allowing us to manage padding at this level..
    VSTRING = 'v{index:03d}'
    VSTRINGMATCH = r'^(?i)v(?P<index>[0-9]{3})$'
    IGNOREFILES = ['.ds_store', 'thumbs.db']


class ReferenceData(object):
    ''' handles a particular category of data, and all the relevant version mangling.
        Subclass this class for each and every type of data you want to accept into
        a particular class/subclass. Note that this does not have a generic handler for 
        USING the data.. '''

    def __init__(self, root, cls, subcls, testmode=False):
        self.testmode = testmode
        self.CONSTANTS = ReferenceDataConstants()
        self.root = os.path.join(root, cls, subcls)
        self.cls = cls
        self.subcls = subcls

        self.exists = False
        # this is a convienience function designed to halt a lot of spurious
        # os.listdir calls. We can do it once, and not bother after all..

        try:
            if os.path.isdir(self.root):
                self.exists = True
        except OSError:
            pass

    # in a world of multiple commits/sync then we have a state issue.. we either do a single
    # state hit and store/cache state, or we force constant updates and filesystem lags..
    # perhaps we do caching and then have a reload cache?
    # hell, it's not exactly a problem for reads - but it is going to cause collisions when multiple
    # people are working

    def get_files(self, version_number):
        ''' returns a list of files with full pathing for the given version. 
            [] if the version doesn't exist '''

        if os.path.isdir(os.path.join(self.root, self.CONSTANTS.VSTRING.format(index=version_number))):
            return [os.path.join(self.root, self.CONSTANTS.VSTRING.format(index=version_number), x) for x in self._listdir(os.path.join(self.root, self.CONSTANTS.VSTRING.format(index=version_number)))]
        else:
            return []

    def get_latest_files(self):
        try:
            return self.get_files(int(self.get_latest_version()[1:]))
        except (TypeError, IndexError):
            return []

    #  oh gawd. Shouldn't be using this..
    def get_latest_version(self):
        ''' returns a v### text string describing the latest directory for the item
            this MIGHT return an empty directory, next_slot is the function that checks 
            for that (since that's the only point at which it becomes important to know..)

            returns None if does not exist
            '''
        try:
            latest = self.get_versions()[-1]
        except (TypeError, IndexError, OSError):
            latest = None

        return latest

    def _listdir(self, path):
        ''' a VERY thin wrapper around os.listdir that filters out .DS_Store files '''
        return [x for x in os.listdir(path) if not x.lower() in self.CONSTANTS.IGNOREFILES]

    def next_slot(self, makedir=False):
        ''' returns a v### string in the form of CONSTANTS.VSTRING that gives us the next slot 
        that should be populated 
        '''
        if self.exists:
            candidate = self.get_latest_version()
            if candidate is not None:
                if self._listdir(os.path.join(self.root, candidate)) == []:
                    return candidate
                else:
                    index = int(
                        re.search(self.CONSTANTS.VSTRINGMATCH, candidate).group('index')) + 1
            else:
                index = 1
        else:
            index = 1

        if makedir:
            os.makedirs(
                os.path.join(self.root, self.CONSTANTS.VSTRING.format(index=index)))

        return self.CONSTANTS.VSTRING.format(index=index)

    def get_versions(self):
        ''' returns a list contaning v### strings which correspond to available versions.
            will report back empty dirs (as in, won't check) '''

        if self.exists:
            candidates = sorted(os.listdir(self.root))
            # do some filtering - this is a performance penalty for unclean directory
            # structures

            # reduce to directories only
            candidates = [
                x for x in candidates if os.path.isdir(os.path.join(self.root, x))]

            # reduce to CORRECTLY named dirs only (which means starting with v
            # and ending with three digits)
            candidates = [
                x for x in candidates if re.match(self.CONSTANTS.VSTRINGMATCH, x)]

            return sorted(candidates)
        else:
            return []

    @classmethod
    def accept_file(cls, f):
        # pass in a single file and if it is acceptable, we can try take it. Note that
        # this is a classmethod, and that by default, we accept nothing
        return False

    # yes you can ingest to a non latest version. Right now we are
    # externally, versions are all handled as numbers

    # _ingest provides protection nonsensical versions, and also prevents ingest
    # of files that don't exist. Does NOT prevent you from ingesting
    # directories btw..
    def _ingest(self, files, version=None, subdir=None):
        # if you're going to do any locking, this is the place do to it
        if version == None:
            target_slot = self.next_slot()
        else:
            if isinstance(version, str):
                version = int(version[1:])
            elif isinstance(version, int):
                version = version
            else:
                raise ValueError(
                    "nonsensical version specified - not an int or a string beginning with 'v'")

            if os.path.isdir(os.path.join(self.root, self.CONSTANTS.VSTRING.format(index=version))):
                target_slot = self.CONSTANTS.VSTRING.format(index=version)
            else:
                raise ValueError(
                    "version specified does not exist, not patching directory")

        # avoid rollback issue, and check for all incoming existence
        for x in files:
            if not os.path.exists(x):
                raise ValueError("supplied file {x} doesn't exist".format(x=x))

        if self.testmode:
            old_os_ren = os.rename
            old_makedirs = os.makedirs
            old_shutil_copy2 = shutil.copy2

            # regardless of exists, we should do creates
            os.rename = lambda * \
                args: sys.stdout.write('monkey.os.rename:: ' + ', '.join([str(x) for x in args] + ['\n']))
            os.makedirs = lambda * \
                args: sys.stdout.write('monkey.os.makedirs:: ' + ', '.join([str(x) for x in args] + ['\n']))
            shutil.copy2 = lambda * \
                args: sys.stdout.write('monkey.shutil.copy2:: ' + ', '.join([str(x) for x in args] + ['\n']))

        if subdir is not None:

            target = os.path.join(self.root, target_slot, subdir)
        else:
            target = os.path.join(self.root, target_slot)

        try:
            os.makedirs(target)
        except:
            pass

        for x in files:
            shutil.copy2(x, target)

        if self.testmode:
            os.rename = old_os_ren
            os.makedirs = old_makedirs
            shutil.copy2 = old_shutil_copy2

        self.exists = True
        # lock_release

    def report(self):
        ''' just a single level os.dirwalk. Returns a dict with keys 
        that should be simply v001, v002, v003, v004 etc. Not guaranteed 
        unless the filesystem is clean (which it won't be..) '''
        reportdict = {}
        if self.exists:
            keys = os.listdir(self.root)
            for x in keys:
                if os.path.isdir(os.path.join(self.root, x)):
                    reportdict[x] = os.listdir(os.path.join(self.root, x))
                else:
                    reportdict[x] = None
        return reportdict

    def __str__(self):

        printstring = "{root} {cls}.{subcls} ({num} versions, latest: {latest})"

        if not self.exists:
            num = 0
            latest = None
        else:
            num = len(self.get_versions())
            latest = self.get_latest_version()

        return printstring.format(root=os.path.dirname(os.path.dirname(self.root)),
                                  cls=self.cls,
                                  subcls=self.subcls,
                                  num=num,
                                  latest=latest)

    def ingest(self, *args):
        raise ValueError(
            'generic data handler ingest not valid. Please implement something!')


class GenericDataHandler(ReferenceData):

    def __init__(self, root, cls, subcls, testmode=True):
        super(GenericDataHandler, self).__init__(
            root, cls, subcls, testmode=testmode)

    def ingest(self, files):
        if not isinstance(files, list):
            files = [files]

        # this should call the self.accept_file method
        for x in files:
            if not os.path.isfile(x):
                raise ValueError('ingest is not a file.')

        self._ingest(files)

    @classmethod
    def accept_file(cls, f):
        return True


class AAFHandler(ReferenceData):

    def __init__(self, root, testmode=False):
        super(AAFHandler, self).__init__(
            root, 'respeed', 'aaf', testmode=testmode)

    def ingest(self, files, tick_over=True, subdir=None):
        if not isinstance(files, list):
            files = [files]

        # patch the file list to only ones we can locate
        goodlist = []
        for x in files:
            if not self.accept_file(x):
                print 'SKIPPING {x} - not an accepted extension.'.format(x=x)
                #raise ValueError('ingesting a file without an .aaf extension')

            elif not os.path.isfile(x):
                print 'SKIPPING {x} - not a file.'.format(x=x)
                #raise ValueError('ingest {x} is not a file.'.format(x=x))
            else:
                goodlist.append(x)
        files = goodlist

        if tick_over:
            target_slot = self.next_slot(makedir=True)
        else:
            target_slot = self.get_latest_version()

        # need to convert to JPGs as well
        self._ingest(files, version=target_slot, subdir=subdir)

        if not self.testmode:
            # post conversions
            binary = r'H:\tools\software\FFmbc\ffmbc.exe'
            for x in files:
                if x.lower().endswith('mxf'):
                    src = os.path.join(
                        self.root, target_slot, subdir, os.path.basename(x))
                    tgt = os.path.join(
                        src[0:-4], 'jpg', os.path.basename(src)[0:-4] + '.%07d.jpg')

                    try:
                        os.makedirs(os.path.dirname(tgt))
                    except:
                        pass

                    command_string = [binary,
                                      "-i",
                                      '' + src + '',
                                      '' + tgt + '', ]

                    subprocess.check_call(command_string)

    @classmethod
    def accept_file(cls, f):
        if f.lower().endswith('.aaf') or f.lower().endswith('.mxf'):
            return True
        else:
            return False


class MovHandler(ReferenceData):

    def __init__(self, root, testmode=False):
        super(MovHandler, self).__init__(
            root, 'reference', 'QT', testmode=testmode)

    def ingest(self, files, tick_over=True, subdir=None):
        if not isinstance(files, list):
            files = [files]

        # patch the file list to only ones we can locate
        goodlist = []
        for x in files:
            if not self.accept_file(x):
                print 'SKIPPING {x} - file not acceptable'.format(x=x)
                #raise ValueError('ingesting a file without an .aaf extension')

            elif not os.path.isfile(x):
                print 'SKIPPING {x} - not a file.'.format(x=x)
                #raise ValueError('ingest {x} is not a file.'.format(x=x))

            else:
                goodlist.append(x)
        files = goodlist

        if tick_over:
            target_slot = self.next_slot(makedir=True)
        else:
            target_slot = self.get_latest_version()

        # need to convert to JPGs as well
        self._ingest(files, version=target_slot, subdir=subdir)

        if not self.testmode:
            # post conversions
            binary = r'H:\tools\software\FFmbc\ffmbc.exe'
            for x in files:
                if x.lower().endswith('mov'):
                    src = os.path.join(
                        self.root, target_slot, os.path.basename(x))
                    tgt = os.path.join(
                        src[0:-4], 'jpg', os.path.basename(src)[0:-4] + '.%07d.jpg')

                    try:
                        os.makedirs(os.path.dirname(tgt))
                    except:
                        pass

                    command_string = [binary,
                                      "-i",
                                      '' + src + '',
                                      '' + tgt + '', ]

                    subprocess.check_call(command_string)

    @ classmethod
    def accept_file(cls, f):
        if f.lower().endswith('.mov'):
            return True
        else:
            return False


class JPGHandler(ReferenceData):

    def __init__(self, root, testmode=True):
        super(JPGHandler, self).__init__(
            root, 'reference', 'JPG', testmode=testmode)

    def ingest(self, files):
        if not isinstance(files, list):
            files = [files]

        for x in files:
            if not self.accept_file(x):
                raise ValueError('ingesting a file without an .jpg extension')
            if not os.path.isfile(x):
                raise ValueError('ingest is not a file.')
        self._ingest(files)

    @classmethod
    def accept_file(cls, f):
        return f.lower().endswith('.jpg')


class LookLUTHandler(ReferenceData):

    def __init__(self, root, testmode=False):
        super(LookLUTHandler, self).__init__(
            root, 'lut', 'lookLUT', testmode=testmode)

    def ingest(self, files):
        if not isinstance(files, list):
            files = [files]

        # this should call the self.accept_file method
        for x in files:
            if not os.path.isfile(x):
                raise ValueError('ingest is not a file.')

        self._ingest(files)


class BalanceLUTHandler(GenericDataHandler):

    def __init__(self, root, testmode=False):
        super(BalanceLUTHandler, self).__init__(
            root, 'lut', 'balanceLUT', testmode=testmode)

    def ingest(self, lutstring, filename):

        fp_temp, tempname = tempfile.mkstemp(suffix='.cc')

        os.write(fp_temp, lutstring)
        os.close(fp_temp)
        os.rename(tempname, os.path.join(
            os.path.dirname(tempname), filename + '.cc'))
        self._ingest(
            [os.path.join(os.path.dirname(tempname), filename + '.cc')])
        os.remove(os.path.join(os.path.dirname(tempname), filename + '.cc'))

        '''
        # this should call the self.accept_file method
        for x in files:
            if not os.path.isfile(x):
                raise ValueError('ingest is not a file.')
        
        self._ingest(files)
        '''

# we don't reaaaaaly need the below... these classes are considered unused


class ShotReferenceDataConstants(object):
    SEQSTRINGMATCH = r'^(?i)(?P<seq>[a-z0-9]){3}$'
    SEQSHOTSTRINGMATCH = r'^(?i)(?P<seq>[a-z0-9]){3}_(?P<shot>[a-z0-9]){3}$'


class ShotReferenceData(object):

    def __init__(self, root):
        ''' needs a root path which is the base '''
        self.root = root
        self.CONSTANTS = ShotReferenceDataConstants()

        # we start empty and do a lazy load.
        self.shotseqs = {}

        # stub build the first index of what's avai. This is lazy.
        self._get_index()

    # lazy build
    def _get_index(self):
        sequences = [x for x in os.listdir(self.root) if re.search(
            self.CONSTANTS.SEQSTRINGMATCH, x)]
        for key in sequences:
            candidates = [x for x in os.listdir(os.path.join(self.root, key)) if re.search(
                self.CONSTANTS.SEQSHOTSTRINGMATCH, x)]
            for x in candidates:
                self.shotseqs[x] = None

    def _fetch(self):
        pass

    # might want a consistency check here for say, {root}/BUZ/GMR_123. This
    # situation will blow stuff out :P
    def __str__(self):
        '''
        q:\shotReferenceData holding sequences "WAS, BLH, OAS, SPP, ZPE, OGW"

        printstring = "{root}"

        '''
        return "TBA"


''' usage will be along the lines of

srd = ShotReferenceData(r'q:/shotreferencedata')
.
.
.


srd.fetch_classes(seq='buz', shot='010')
--> kw list of what classes are avail

srd.fetch_subclasses(seq='buz', shot='010', class = 'documents')
--> kw list of what subclasses are avail 

srd.fetch_refdata(seq='buz', shot='010')
--> a whole lot of ref data objects
to do this, we have to go into each class dir, and we have to have a handler or the generic handler

which means we need a lookup to know what the signature is to make the handler.. and
we have to hope that the handler signatures we're doing are consistent with the interal handling each SRD handler


srd.ingest(seq='buz', shot = '010', files = [files])
-> and then inside srd we have to decide how to deal with the files, create a handler, and then shove them in
-> this is brutal, and we have to have logic to decide how to manage all these files.. 

srd.ingest(seq='buz', shot = '010', what='aaf', files = [files])
-> this hints what those files are, which is probably a better approach. This almost implies we
-> we could define in the refdata types an 'accept' function to tell us what it accepts? Never 
-> let the geneirc one there.

srd.fetch(seq='buz', shot='010', what='aaf')
srd.fetch(seq='buz', shot='010', what='jpg')
srd.fetch(seq='buz', shot='010', what='shotsheet')
--> this implies that there's fetching an object. this will be the most likely usage


Currently we're dealing with just a dir browser.. ugh. We either do it properly or rough.
'''


def test_ReferenceDataGeneric():

    dh = GenericDataHandler(r'Q:\shotReferenceData\AAF\AAF_010',
                            'LUT',
                            'balanceLUT',
                            testmode=True)
    print "__str__:", dh
    print "next_slot:", dh.next_slot()
    print "report:", dh.report()
    # dh.ingest('c:\eula.1028.txt',1)

    # GenericDataHandler(r'Q:\shotReferenceData\AAF\AAF_010','LUT', 'balanceLUT', testmode=False).ingest(r'Q:\shotReferenceData\AAF\AAF_010\documents\aaf\v001\052 - Mediocre Morsov v5.aaf')
    print GenericDataHandler(r'Q:\shotReferenceData\AAF\AAF_010', 'LUT', 'balanceLUT', testmode=False).get_latest_files()

    #afdh = AAFHandler(r'Q:\shotReferenceData\AAF\AAF_010', testmode=False)
    #afdh.ingest(r'Q:\shotReferenceData\AAF\AAF_010\documents\aaf\v001\052 - Mediocre Morsov v5.aaf')
    # print afdh

    #jpdh = JPGHandler(r'Q:\shotReferenceData\AAF\AAF_010', testmode=False)
    # print jpdh
    # jpdh.ingest(r'H:\user\anthony.tan\garbage\New folder')
    # print jpdh

    # JPGHandler(r'Q:\shotReferenceData\AAF\AAF_010',
    # testmode=False).ingest(r'H:\user\anthony.tan\garbage\yetmore_garbarge.0006.jpg')


def test_ShotReferenceData():
    srd = ShotReferenceData(r'Q:\shotReferenceData')
    print srd.shotseqs


def test():
    print ('you should be doing your testrunner here..')
    '''
    ReferenceData should be called on a particular pkg root -> Q:\shotReferenceData\AAF\AAF_010
        and knows cls, subcls
    
    ShotReferenceData works on the level up -> Q:\shotReferenceData\AAF\
        and knows shot/seq
    '''
    test_ReferenceDataGeneric()
    # test_ShotReferenceData()


if __name__ == '__main__':
    test()
