#!/usr/bin/python

import re
import csv
import sys
import os



def parse_shotstring(shotstring):
    bits = shotstring.split('/')  # split on slashes
    canary_string = r'[a-z0-9]{3}_[0-9]{3}_v[0-9]{3}'
    
    bit_dict = {}
    # walk through until you find the canary and then go from there to build up the bits
    for idx, blob in enumerate(bits):
        if re.match(canary_string, blob):
            bit_dict['spool'] = bits[idx-1]
            break

    
    bit_dict['shotdir'] = bits[idx]
    bit_dict['resolution'] = bits[idx+1]
    bit_dict['eye'] = bits[idx+2]
    bit_dict['matte'] = bits[idx+3]
    bit_dict['file'] = bits[idx+4]
    
    # file eye is always in the same relative position.
    # -- number of fragments in the dirstring, -1 
    bit_dict['file_eye'] = bit_dict['file'].split('_')[len(bit_dict['shotdir'].split('_'))-1]
    bit_dict['file_stereo_version'] = bit_dict['file'].split('_')[len(bit_dict['shotdir'].split('_'))]
    
    bit_dict['extended_shotstring'] = '_'.join(bit_dict['shotdir'].split('_')[0:-1])
    bit_dict['stereo_version'] = bit_dict['shotdir'].split('_')[-1]
    
    return bit_dict


def validate_parse(the_dict, ignore_nontga = False):
    ''' internal test suite '''
    
    errors = []
    
    # check - TGAs? Flag if not.
    if the_dict['file'].split('.')[-1].lower() != 'tga' and not ignore_nontga:
        errors+= ['non-TGA extension']

    # check - file contains same eye as eyedir
    if the_dict['file_eye'] != the_dict['eye'][0] :
        errors+= ['file eye/dir eye mismatch']
    
    # check - file is same as shotdir, matches on seq/shot/v/sp/opt/s/etc
    if not the_dict['file'].startswith(the_dict['extended_shotstring']):
        errors+= ['file shotstring/dir mismatch']
    
    if the_dict['file_stereo_version'] != the_dict['stereo_version']:
        errors+= ['file stereo ver/dir stereo ver mismatch']
    

    return errors

def _pp_dict(theDict):
    for key, value in theDict.iteritems():
        print key,
        print ':',
        print value
        
        
def selftest():
    testvalues = [r'/vol/bl0446-images/fury_road/source/000S3D/spool03/bfc_196_v019_sp3_opt_01_v01a_s022/2150x1210/right/matte/bfc_196_v019_sp3_opt_01_v01a_r_s022_m01.%.7F.tga',
                  r'/vol/bl0446-images/fury_road/source/000S3D/spool04/nt1_108_v020_ungraded_s042/2150x1210/right/matte/nt1_108_v020_ungraded_r_s042_m01.%.7F.tga',
                  r'/vol/bl0446-images/fury_road/source/000S3D/spool01/buz_030_v014_s051/2150x1210/right/matte/buz_030_v014_r_s051_m01.%.7F.tga',
                  r'/vol/bl0446-images/fury_road/source/000S3D/spool04/nt1_126_v012_sp4_opt_01_v01a_ungraded_s046/2150x1210/right/matte/nt1_126_v012_sp4_opt_01_v01a_ungraded_r_s046_m01.%.7F.tga',
                  r'/vol/bl0446-images/fury_road/source/000S3D/spool01/was_130_v046_s049/2150x1210/right/matte/was_130_v046_r_s049_m01.%.7F.dpx',
                  
                  ]
    for x in testvalues:
        print x
        _pp_dict(parse_shotstring(x))
        print 'errors:'+ str(validate_parse(parse_shotstring(x)))
        print 
        

