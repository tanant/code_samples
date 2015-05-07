#!/usr/bin/python

import re
import csv
import sys
import os

import matte_list_parser as mlp
reload(mlp)




def parse_stereo_shotstring(shotstring, line = None):
    bits = shotstring.split('/')  # split on slashes
    
    bit_dict ={}
    bit_dict['spool'] = bits[4]
    bit_dict['shotdir'] = bits[5]
    bit_dict['resolution']= bits[6]
    bit_dict['eye']= bits[7]
    bit_dict['file']= bits[8]
    
    bit_dict['file_eye'] = bit_dict['file'].split('_')[len(bit_dict['shotdir'].split('_'))-1]
    bit_dict['file_stereo_version'] = bit_dict['file'].split('_')[len(bit_dict['shotdir'].split('_'))].split('.')[0]
    bit_dict['extended_shotstring'] = '_'.join(bit_dict['shotdir'].split('_')[0:-1])
    bit_dict['stereo_version'] = bit_dict['shotdir'].split('_')[-1].split('.')[0]

    bit_dict['rawstring']=shotstring
    bit_dict['line'] = line
    return bit_dict




def parse_shotstring(shotstring, line = None):
    bits = shotstring.split('/')  # split on slashes
    
    bit_dict ={}
    if bits[3].endswith('S3D'):
        if bits[4] == 'mono_base':
            bit_dict['vendor'] = 'MONO'
        else:
            bit_dict['vendor'] = 'S3D'
    elif bits[3].endswith('VFX'):
        bit_dict['vendor'] = 'VFX'
    else:
        bit_dict['vendor'] = 'UNKNOWN'
        

    if bit_dict['vendor'] == 'S3D':
        bit_dict['spool'] = bits[4]
        bit_dict['shotdir'] = bits[5]
        bit_dict['resolution']= bits[6]
        bit_dict['eye']= bits[7]
        bit_dict['matte'] = bits[8]
        bit_dict['file']= bits[9]
        bit_dict['file_stereo_version'] = bit_dict['file'].split('_')[-1]
                
        bit_dict['file_eye'] = bit_dict['file'].split('_')[len(bit_dict['shotdir'].split('_'))-1]
        bit_dict['file_stereo_version'] = bit_dict['file'].split('_')[len(bit_dict['shotdir'].split('_'))]
        bit_dict['extended_shotstring'] = '_'.join(bit_dict['shotdir'].split('_')[0:-1])
        bit_dict['stereo_version'] = bit_dict['shotdir'].split('_')[-1]

        
        
    elif bit_dict['vendor'] == 'VFX':
        bit_dict['spool'] = None
        bit_dict['shotdir'] = bits[4]
        bit_dict['resolution']= bits[5]
        bit_dict['eye']= bits[6]
        bit_dict['file']= bits[7]
        bit_dict['extended_shotstring'] = None
        bit_dict['stereo_version'] = None
        
        
    elif bit_dict['vendor'] == 'UNKNOWN':
        bit_dict['spool'] = None
        bit_dict['shotdir'] = bits[4]
        bit_dict['resolution']= bits[5]
        bit_dict['eye']= bits[6]
        bit_dict['file']= bits[7]
        
    elif bit_dict['vendor'] == 'MONO':
        bit_dict['spool'] = bits[4]
        bit_dict['shotdir'] = bits[5]
        bit_dict['resolution']= bits[6]
        bit_dict['eye']= None
        bit_dict['file']= bits[7]
 
    bit_dict['rawstring']= shotstring
    bit_dict['line'] = line
    return bit_dict

    
def validate_parse(the_dict, ignore_nontga = False):
    ''' internal test suite '''
    
    errors = []
    
    # check - TGAs? Flag if not.
    if the_dict['file'].split('.')[-1].lower() != 'tga' and not ignore_nontga:
        errors+= ['non-TGA extension']

    # check - file contains same eye as eyedir
    if the_dict['file_eye'] != the_dict['eye'][0] :
        errors+= ['file eye/dir eye mismatch ({fe} vs {e})'.format(fe=the_dict['file_eye'], e=the_dict['eye'])]
    
    # check - file is same as shotdir, matches on seq/shot/v/sp/opt/s/etc
    if not the_dict['file'].startswith(the_dict['extended_shotstring']):
        errors+= ['file shotstring/dir mismatch ({a} vs {b})'.format(a=the_dict['file'], b=the_dict['extended_shotstring'], ) ]
    
    if the_dict['file_stereo_version'] != the_dict['stereo_version']:
        errors+= ['file stereo ver/dir stereo ver mismatch ({eye}:{a} vs {b})'.format(a=the_dict['file_stereo_version'], eye =the_dict['eye'], b=the_dict['stereo_version'])]
    

    return errors
    
    

def check_mattepack(list_of_mattes):
 

    
    errors = []

    # if there are no mattes in use
    if len(list_of_mattes) == 0:
        errors+= ['no mattes in use']

    # if all mattes are of type VFX
    ven_list = []
    for v in list_of_mattes:
        ven_list += [v['vendor']]

    if 'UNKNOWN' in ven_list:
        errors += ['1:UNKNOWN/weirdly named matte in use']
    
    if 'VFX' in ven_list and 'S3D' not in ven_list:
        errors += ['2:only VFX mattes in use (no S3D)']
        
    if 'VFX' in ven_list and 'S3D' in ven_list:
        errors += ['1:S3D and VFX mixed mattes']

    # now do detailed matte level checking
    for matte in list_of_mattes:
        if matte['vendor'] == 'S3D':
            if matte['file_eye'] != matte['eye'][0]:
                errors+= ['0:file eye/dir eye mismatch ({a} vs {b}, line {line})'.format(line=matte['line'], a=matte['file_eye'], b=matte['eye'])]
            
            if matte['file'].split('.')[-1].lower() != 'tga':
                errors+= ['2:non-TGA extension (line {line})'.format(line=matte['line'])]
                
            # check - file is same as shotdir, matches on seq/shot/v/sp/opt/s/etc
            if not matte['file'].startswith(matte['extended_shotstring']):
                errors+= ['0:file shotstring/dir mismatch ({a} vs {b}, line {line})'.format(a=matte['file'], b= matte['extended_shotstring'], line=matte['line'])]
                
            if matte['file_stereo_version'] != matte['stereo_version']:
                errors+= ['0:file stereo ver/dir stereo ver mismatch ({a} vs {b},line {line})'.format(line=matte['line'], a=matte['file_stereo_version'],b= matte['stereo_version']    )]
    tmpset = []
    for matte in list_of_mattes:
        try:
            tmpset += [matte['extended_shotstring']]
        except KeyError:
            errors += ['1:UNKNOWN matte spotted']
            pass
    
    tmpset = list(set(tmpset))
    if len(tmpset) > 1:
        errors += ["0:multiple matte versions in use ({a})".format(a=str(tmpset))]
        
    # need to check for left and rightness.
    eyes = []
    for matte in list_of_mattes:
        eyes += [matte['eye']]
    if len(list_of_mattes) !=0:
        if 'left' not in eyes and 'right' not in eyes  :
             errors += ['1:no eyes, but something found']        
        elif 'left' not in eyes or 'right' not in eyes:
             errors += ['0:only one eye']
    return errors