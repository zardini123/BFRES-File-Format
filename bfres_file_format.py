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

@dataclass
class BFRES:
    version = []
    little_endian = False

    file_type_index_groups = [None] * len(SubfileTypes)

    def __init__(self, binary_data: bytes):
        self.convert_binary_to_BFRES(binary_data = binary_data)
        pass

    def convert_binary_to_BFRES(self, binary_data: bytes):
        #######################
        # FRES Header
        # WiiU is big-endian (format char '>')
        # TODO: Find FRES magic first and use endian
        fresHeader = struct.unpack(">4s bbbb 2s H I I i i i 12i 12H I", binary_data[0:0x6C])
        print(fresHeader)

        # TODO: Assign all unpacked variables to class

        self.version = [fresHeader[1], fresHeader[2], fresHeader[3], fresHeader[4]]
        self.little_endian = fresHeader[5] == 0xFFFE

        fileOffsets = fresHeader[12:24]
        fileCounts = fresHeader[24:36]

        for i in range(len(fileOffsets)):
            if fileOffsets[i] != 0 and fileCounts[i] != 0:
                self.file_type_index_groups[i] = IndexGroup()
                print(SubfileTypes[i])

                # The offset for this index group's start
                # FRES start offset + File Offsets start offset + index group offset + actual index group offset
                indexGroupStartOffset = 0x00 + 0x20 + (i * 4) + fileOffsets[i]
                self.file_type_index_groups[i].convert_binary_to_IndexGroup(binary_data, indexGroupStartOffset, self)
            else:
                continue
        pass

    pass

@dataclass
class Subfile:
    magic = ""
    parent_bfres_instance: BFRES
    pass

@dataclass
class IndexGroupDataEntry:
    search_value: int
    left_index: int
    right_index: int
    name_of_entry: str
    data = None
    pass

@dataclass
class IndexGroup:
    entries = []

    def convert_binary_to_IndexGroup(self, binary_data: bytes, indexGroupStartOffset: int, bfres_instance: BFRES):
        #######################
        # Index Group header
        indexGroupHeader = struct.unpack(">I i", binary_data[indexGroupStartOffset:indexGroupStartOffset + 0x08])
        print(indexGroupHeader)

        # Number of entries (tree nodes) in the group, excluding the root entry (same as possibly available file counts in headers).
        numOfTreeNodes = indexGroupHeader[1]
        firstTreeNodeEntryOffset = indexGroupStartOffset + 0x08

        # Add one to numOfTreeNodes to include root entry
        for t in range(numOfTreeNodes + 1):
            #######################
            # Index Group Data Entry (Tree Node) header
            treeNodeEntryOffset = firstTreeNodeEntryOffset + (t * 0x10)
            print(treeNodeEntryOffset)

            treeNodeEntry = struct.unpack(">I H H i i", binary_data[treeNodeEntryOffset:treeNodeEntryOffset + 0x10])
            print(treeNodeEntry)

            treeNodeEntryNameOffset = treeNodeEntryOffset + 0x08 + treeNodeEntry[3]
            treeNodeEntryDataOffset = treeNodeEntryOffset + 0x0C + treeNodeEntry[4]

            # TODO: Get entry names properly
            entryName = "".join(map(chr, struct.unpack(">10s", binary_data[treeNodeEntryNameOffset:treeNodeEntryNameOffset + 10])[0]))

            indexGroupEntry = IndexGroupDataEntry(search_value = treeNodeEntry[0], left_index = treeNodeEntry[1], right_index = treeNodeEntry[2], name_of_entry = entryName)
            self.add_entry(indexGroupEntry)

            print(treeNodeEntryDataOffset)

            # If not root entry
            if t > 0:
                #######################
                # Data Type header
                dataEntryIdentifier = struct.unpack(">4s", binary_data[treeNodeEntryDataOffset:treeNodeEntryDataOffset + 4])
                print(dataEntryIdentifier)

                # Subfiles
                if dataEntryIdentifier[0] == b'FSCN':
                    self.data = FSCN(bfres_instance)
                    self.data.convert_binary_to_FSCN(binary_data, treeNodeEntryDataOffset)
                    pass

                # Sections
                if dataEntryIdentifier[0] == b'FCAM':
                    self.data = FCAM(bfres_instance)
                    self.data.convert_binary_to_FCAM(binary_data, treeNodeEntryDataOffset)
                    pass

            pass

    def add_entry(self, new_entry: IndexGroupDataEntry):
        self.entries.append(new_entry)

    def get_number_of_entries_without_root(self):
        return len(self.entries) - 1

    def get_root_entry(self):
        return self.entries[0]

@dataclass
class FSCN(Subfile):
    magic = "FSCN"
    file_name = ""
    file_path = ""

    fcam_index_group = None
    flit_index_group = None
    ffog_index_group = None
    # TODO: User Data section

    def convert_binary_to_FSCN(self, binary_data: bytes, offset_to_FSCN_Section: int):
        #######################
        # FSCN Header
        fscn_header = struct.unpack(">4s i i H H H H i i i i", binary_data[offset_to_FSCN_Section:offset_to_FSCN_Section + 0x24])
        print(fscn_header)

        fcam_count = fscn_header[4]
        flit_count = fscn_header[5]
        ffog_count = fscn_header[6]

        fcam_index_group_offset = offset_to_FSCN_Section + 0x14 + fscn_header[7]

        if fcam_count > 0:
            fcam_index_group = IndexGroup()
            fcam_index_group.convert_binary_to_IndexGroup(binary_data = binary_data, indexGroupStartOffset = fcam_index_group_offset, bfres_instance = self.parent_bfres_instance)

        # fcam_header = struct.unpack(">4s H xx i B x H I I I I I")
        pass

    pass

@dataclass
class CameraAnimationData:
    near_clipping_plane = 0
    far_clipping_plane = 0
    aspect_ratio = 0
    height_offset_or_fov = 0
    position = []
    rotation_aim_direction = []
    twist = 0

    def convert_binary_to_CameraAnimationData(self, binary_data: bytes, offset_to_cameraAnimationData_Section: int):
        cam_animation_data = struct.unpack(">f f f f 3f 3f f", binary_data[offset_to_cameraAnimationData_Section:offset_to_cameraAnimationData_Section + 0x2C])
        print(cam_animation_data)

        near_clipping_plane = cam_animation_data[0]
        far_clipping_plane = cam_animation_data[1]
        aspect_ratio = cam_animation_data[2]
        height_offset_or_fov = cam_animation_data[3]
        position = cam_animation_data[4:7]
        rotation = cam_animation_data[7:10]
        twist = cam_animation_data[10]

        print(position)
        print(rotation)

        pass

    pass

@dataclass
class FCAM(Subfile):
    magic = "FCAM"

    cam_animation_data = None

    def convert_binary_to_FCAM(self, binary_data: bytes, offset_to_FCAM_Section: int):
        #######################
        # FCAM Header
        fcam_header = struct.unpack(">4s H xx i B x H I I I I I", binary_data[offset_to_FCAM_Section:offset_to_FCAM_Section + 0x24])
        print(fcam_header)
        print(format(fcam_header[1], 'b')[::-1])

        i = fcam_header[1]
        print("Baked: ", i >> 0 & 1)
        print("Looping: ", i >> 2 & 1)
        print("(Yes) Euler ZYX / (No) Aim Direction: ", i >> 8 & 1)
        print("(Yes) Perspective / (No) Orthographic: ", i >> 10 & 1)

        # TODO: Flags

        cam_animation_data_offset = offset_to_FCAM_Section + 0x1C + fcam_header[8]

        self.cam_animation_data = CameraAnimationData()
        self.cam_animation_data.convert_binary_to_CameraAnimationData(binary_data, cam_animation_data_offset)

        frame_count = fcam_header[2]
        curve_count = fcam_header[3]
        baked_length = fcam_header[5]
        curve_array_start_offset = offset_to_FCAM_Section + 0x18 + fcam_header[7]

        name_offset = offset_to_FCAM_Section + 0x14 + fcam_header[6]
        name = "".join(map(chr, struct.unpack(">10s", binary_data[name_offset:name_offset + 10])[0]))
        print("Animation name: ", name)

        print("Frame count: ", frame_count)
        print("Curve count: ", curve_count)
        print("Baked length: ", baked_length)

        # TODO: Implement bfres version curve header for less than 3.4.0.0
        # if parent_bfres_instance.version >= [3,4,0,0]
        #     print('is great')

        for i in range(curve_count):
            current_curve_offset = curve_array_start_offset + (i * 0x24)

            curve_header = struct.unpack(">H H I f f f f f i i", binary_data[current_curve_offset:current_curve_offset + 0x24])
            print(format(curve_header[0], 'b')[::-1])
            print(curve_header)

            i = curve_header[0]
            print("Frames Data Type: ", i >> 0 & 0x3)
            print("Keys Data Type: ", i >> 2 & 0x3)
            print("Interpolation Type: ", i >> 4 & 0x7)

            pass

        pass

    pass

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

        bfres_file = BFRES(binary_data = fileContent)

if __name__ == "__main__":
   main(sys.argv[1:])
