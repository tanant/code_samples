#!/usr/bin/python

import sys
import lib.matte_list_parser as mlp
import lib.spool_list_parser as slp

reload(mlp)
reload(slp)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "ERROR: no files supplied!"
        print "You need to supply spool dump script to read and analyse and the S3D master, for example:\n"
        print "\t{thisscript} SP4_v080_S3D_v07_1504170035.txt 000S3D_mattes.txt".format(thisscript=sys.argv[0])
        print "\n"
        exit(1)

    infile = sys.argv[1]
    matte_master = sys.argv[2]
else:
    infile = r'./SP4_v080_S3D_v07_1504170035-mattes-errorgen.txt'
    matte_master = r'./000S3D_mattes.txt'


# load in the S3D blob
flag_fail = False
print "loading S3D matte master blob...",
with open(matte_master) as fpin:
    for idx, row in enumerate(fpin):
        if (not row.strip().startswith('#')) and (len(row.strip()) > 0):
            parse = mlp.parse_shotstring(row.split('\t')[0])
            if len(mlp.validate_parse(parse, ignore_nontga=True)) > 0:
                print "row", idx + 1, ':', (row.split('\t')[0])
                print 'errors:' + str(mlp.validate_parse(parse, ignore_nontga=True))
                flag_fail = True
if flag_fail:
    print "non-warning error detected. Fix or comment out the broken lines in the S3D pack first."
    raise ValueError()
else:
    print "OK"

matte_dict = {}
with open(matte_master) as fpin:
    for idx, row in enumerate(fpin):
        if (not row.strip().startswith('#')) and (len(row.strip()) > 0):
            data = '/'.join(['%C'] + row.split('\t')[0].split('/')[3:8] +
                            ['%R'] + row.split('\t')[0].split('/')[9:])
            key = '_'.join(row.split('\t')[0].split('/')[7].split('_')[0:-1])
            st_ver = row.split('\t')[0].split('/')[7].split('_')[-1]
            matte_dict[key] = {'stereo_version': st_ver, 'filestring': data}
cut_block = {}
slient = False

print "Analysing..",
with open(infile) as fpin:
    for idx, row in enumerate(fpin):
        if (not row.strip().startswith('#')) and (len(row.strip()) > 0):
            identifier = row.strip().split('\t')[0] + '-' + row.split('\t')[1]
            # always create an entry

            try:
                cut_block[identifier] += []
            except KeyError:
                cut_block[identifier] = []

            if 'matte' in row:
                try:
                    info = slp.parse_shotstring(
                        row.strip().split('\t')[2], line=idx)
                except IndexError:

                    print "ROW ", idx, ':',
                    print row.strip().split('\t')[2]
                    raise
                except ValueError as e:
                    if not slient:
                        print "ROW ", idx, ':',
                        print row.strip().split('\t')[2]
                        print e, ":SKIPPING"
                    pass

                try:
                    cut_block[identifier] += [info]
                except KeyError:
                    cut_block[identifier] = [info]

            else:
                pass

# now we have digested all the cut blocks. Time to work on consistency
# between them.
all_blocks = cut_block.keys()
all_blocks.sort(key=lambda x: int(x.split('-')[0]))

block_keys = ['2202-2247']
block_keys = all_blocks


with open('.'.join(infile.split('.')[0:-1]) + '-mattecheck_report.txt', "wt") as fout:
    for block in block_keys:
        output_dump = []
        output_dump += block.split('-')  # first two ranges
        errors = []

        candidate = cut_block[block]
        errors = slp.check_mattepack(cut_block[block])

        # use the extended shotstring as the key binding the s3d spool and this
        # together

        stver_patch = False
        if len(errors) == 0:
            # now, and ONLY now can we look at upgrades
            for c in candidate:
                key = c['extended_shotstring']
                if matte_dict[key]['stereo_version'] != c['stereo_version']:
                    errors += ['0:Stereo Version mismatch ({a} avail, {b} used - see next row for patch suggestion)'.format(
                        a=matte_dict[key]['stereo_version'], b=c['stereo_version'])]
                    stver_patch = True
                    break

        if len(errors) != 0:
            output_dump += ['ERROR']
            errors.sort()
            output_dump += errors

        fout.write('\t'.join(output_dump))
        if stver_patch:
            fout.write('\n')
            fout.write('\t'.join(
                output_dump[0:2] + [c['rawstring'].strip()] + [matte_dict[key]['filestring']]))
        if len(errors) == 0:
            fout.write('\tOK')

        fout.write('\n')
print '..Done.\nreport written to : {rpt}'.format(rpt='.'.join(infile.split('.')[0:-1]) + '-mattecheck_report.txt')
