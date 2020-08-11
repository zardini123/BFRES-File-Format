import sys, getopt

import struct
import array
from enum import Enum
from dataclasses import dataclass

SubfileTypes = {
    0: "FMDL",
    1: "FTEX",
    2: "FSKA",
    3: "FSHU",
    4: "FSHU",
    5: "FSHU",
    6: "FTXP",
    7: "FVIS",
    8: "FVIS",
    9: "FSHA",
    10: "FSCN",
    11: "Embedded"
}

# @dataclass
# class BFRESFile:
#     file_magic: str
#     version_numbers: array
#     byte_order_mark: bytes
#     header_length: integer
#     file_length: integer
#     file_alignment: integer
#     file_name_offset: integer
#

def main(argv):
    inputfileDir = ''

    try:
        opts, args = getopt.getopt(argv,"hi:",["ifile="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfileDir = arg

    print('Input file is ', inputfileDir)

    with open(inputfileDir, mode = 'rb') as file:
        fileContent = file.read()

        # FRES Header
        # WiiU is big-endian (format char '>')
        fresHeader = struct.unpack(">4s bbbb 2s H I I i i i 12i 12H I", fileContent[0:0x6C])
        print(fresHeader)

        fileOffsets = fresHeader[12:24]
        fileCounts = fresHeader[24:36]

        print(fileOffsets)
        print(fileCounts)

        for i in range(len(fileOffsets)):
            if fileOffsets[i] != 0 and fileCounts[i] != 0:
                print(SubfileTypes[i])

                # Index Group header
                # FRES start offset + File Offsets start offset + index group offset + actual index group offset
                indexGroupStartOffset = 0x00 + 0x20 + (i * 4) + fileOffsets[i]
                indexGroupHeader = struct.unpack(">I i", fileContent[indexGroupStartOffset:indexGroupStartOffset + 0x08])
                print(indexGroupHeader)

                # Number of entries (tree nodes) in the group, excluding the root entry (same as possibly available file counts in headers).
                numOfTreeNodes = indexGroupHeader[1]

                firstTreeNodeEntryOffset = indexGroupStartOffset + 0x08

                # Add one to numOfTreeNodes to include root entry
                for t in range(numOfTreeNodes + 1):
                    treeNodeEntryOffset = firstTreeNodeEntryOffset + (t * 0x10)
                    print(treeNodeEntryOffset)

                    treeNodeEntry = struct.unpack(">I H H i i", fileContent[treeNodeEntryOffset:treeNodeEntryOffset + 0x10])
                    print(treeNodeEntry)

                    treeNodeEntryNameOffset = treeNodeEntryOffset + 0x08 + treeNodeEntry[3]
                    treeNodeEntryDataOffset = treeNodeEntryOffset + 0x0C + treeNodeEntry[4]

                    print( "".join(map(chr, struct.unpack(">10s", fileContent[treeNodeEntryNameOffset:treeNodeEntryNameOffset + 10])[0])))

                    print(treeNodeEntryDataOffset)
                    pass
            else:
                continue

            # print("ERROR: File offset or file count for ", SubfileTypes[i], " is zero but the other isn't")

if __name__ == "__main__":
   main(sys.argv[1:])
