# T42 new format to old format converter
# 
# Splits the monolithic new file into files of 64k chunks  each

#
# Jason Robertson 2016

import argparse
import sys

# Get args

parser = argparse.ArgumentParser()

parser.add_argument('inputfile', type=str, help='File in T42 format')
parser.add_argument('outputfile', type=str, help='T43 file to be created')

args = parser.parse_args()

# Load monolithic file

infilereader = open(args.inputfile, 'rb')



# Cycle file in 32*42 byte chunks until EoF

chunk = infilereader.read(42)
packetnumber = 0
outfilewriter = open(args.outputfile, 'wb')
    
while chunk:

    # Write to new file
    
    outfilewriter.write(chunk)
    outfilewriter.write(b'\x64')
    
    print ('\rWriting packet: %08d' % packetnumber),
    
    packetnumber += 1
    
    chunk = infilereader.read(42)

# Close monolith
infilereader.close()    
outfilewriter.close()