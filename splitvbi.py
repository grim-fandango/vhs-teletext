# T42 new format to old format converter
# 
# Splits the monolithic new file into files of 64k chunks  each

#
# Jason Robertson 2016

import argparse
import sys

# Get args

parser = argparse.ArgumentParser()

parser.add_argument('inputfile', type=str, help='Monolithic vbi file to read from')
parser.add_argument('outputfile', type=str, help='Folder into which the vbi chunks will go')

args = parser.parse_args()

# Load monolithic file

infilereader = open(args.inputfile, 'rb')



# Cycle file in 32*42 byte chunks until EoF

chunk = infilereader.read(65536)
filenumber = 0

while chunk:

    # Write file to new file
    
    outfilereader = open(args.outputfile + '\\%08d.vbi' % filenumber , 'wb')
    outfilereader.write(chunk)
    outfilereader.close()
    
    sys.stdout.write(args.outputfile + '\\%08d.vbi\n' % filenumber)
    
    filenumber += 1
    
    chunk = infilereader.read(65536)

# Close monolith
infilereader.close()