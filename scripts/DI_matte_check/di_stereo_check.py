#!/usr/bin/python

import os
import re
import csv
import sys
import lib.matte_list_parser as mlp
import lib.spool_list_parser as slp

reload(mlp)
reload(slp)

print "\n"
print "----------------------"
print "V2 - potato!"
print "----------------------\n"


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "ERROR: no files supplied!"
        print "You need to supply spool dump script to read and analyse, for example:\n"
        print "\t{thisscript} SP4_v080_S3D_v07_1504170035.txt".format(thisscript = sys.argv[0])
        print "\n"
        exit(1)

    infile = sys.argv[1]
else:
    infile = r'./SP4_v080_S3D_v07_1504170035-errorgen1.txt'


print "SCANNING..."



cut_block = {}
slient = False

with open(infile) as fpin:
    for idx, row in enumerate(fpin):

        if (not row.strip().startswith('#') ) and (len(row.strip())>0):
            identifier = row.strip().split('\t')[0]+'-'+ row.split('\t')[1]

            try:
                cut_block[identifier] += []
            except KeyError:
                cut_block[identifier] = []
            
            # need to drop this issue down to a filteration.
            # check if there's a spool.
            # if spool in string and matte NOT in string
            
            shotstring = row.strip().split('\t')[2]
            if 'matte' not in shotstring and 'spool' in shotstring:
                try:
                    cut_block[identifier] += [slp.parse_stereo_shotstring(shotstring, line=idx)]
                except IndexError:
                    print "line {line} : odd looking source line" .format(line =idx)
                    pass
                
   
# now we have digested all the cut blocks. Time to work on consistency between them.
all_blocks = cut_block.keys()
all_blocks.sort(key=lambda x: int(x.split('-')[0]))


block_keys = ['2202-2247']
block_keys = all_blocks

with open('.'.join(infile.split('.')[0:-1])+'-stereo_report.txt',"wt") as fout:
    for block in block_keys:
        output_dump = []
        output_dump += block.split('-') # first two ranges
        errors = []
        
        candidate = cut_block[block]

        if len(candidate) == 0:
            errors += ['no eyes']
        elif len(candidate) != 2:
            # do some line folding
            tmpset = []
            for c in candidate:
                tmpset += [c['rawstring']]
            tmpset = set(tmpset)
            if len(tmpset) !=2:
                errors += ['more than two sources, expecting only 2']
        else:   # we have two eyes potentially only, good!
            pass
     
        # need to check for left and rightness.
        eyes = []
        for item in candidate:
            eyes += [item['eye']]
        if len(candidate) !=0:
            if 'left' not in eyes and 'right' not in eyes  :
                 errors += ['no eyes, but something found']        
            elif 'left' not in eyes or 'right' not in eyes:
                 errors += ['only one eye']
        

         
        if len(errors) == 0 :   # we can only do checks if zero errors so far.
            # the fact we run this for each item, even though we know there's duplicates to get here, 
            # is because it's cheaper to do this than to design for the scenario in a one-shot tool
            for c in candidate:
                errors += slp.validate_parse(c, ignore_nontga=True)
            
            # finally, assuming you have no errors at this point, the last
            # test is if they're the same dang matte.
            tmpset = []
            for c in candidate:
                tmpset += [c['extended_shotstring']+'_'+c['file_stereo_version']]
            tmpset = set(tmpset)
            if len(tmpset) > 1:
                errors += ["mixed sources detected ( {info} )".format(info=str(list(tmpset)))]
            
        if len(errors ) == 0:
            fout.write('\t'.join(output_dump[0:2]+['OK']))

            
        else:
            output_dump += ['ERROR']
            output_dump += errors
        
            for x in output_dump:
                fout.write(x)
                fout.write('\t')

        fout.write('\n')
        
        
        
    print "DONE - output to", '.'.join(infile.split('.')[0:-1])+'-report.txt'
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
