import sys, getopt

import struct
import array
from enum import Enum
from dataclasses import dataclass

from enum import Enum
from collections import defaultdict

import numpy as np

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
    offset_to_value_dictonary = {}
    name_to_offset_dictonary = {}

    def convert_binary_to_CameraAnimationData(self, binary_data: bytes, offset_to_cameraAnimationData_Section: int):
        cam_animation_data = struct.unpack(">f f f f 3f 3f f", binary_data[offset_to_cameraAnimationData_Section:offset_to_cameraAnimationData_Section + 0x2C])
        print(cam_animation_data)

        self.offset_to_value_dictonary[0x00] = cam_animation_data[0]
        self.name_to_offset_dictonary["near clipping plane distance"] = 0x00

        self.offset_to_value_dictonary[0x04] = cam_animation_data[1]
        self.name_to_offset_dictonary["far clipping plane distance"] = 0x04

        self.offset_to_value_dictonary[0x08] = cam_animation_data[2]
        self.name_to_offset_dictonary["aspect ratio"] = 0x08

        self.offset_to_value_dictonary[0x0C] = cam_animation_data[3]
        self.name_to_offset_dictonary["height offset or fov"] = 0x0C

        self.offset_to_value_dictonary[0x10] = cam_animation_data[4]
        self.name_to_offset_dictonary["position (x)"] = 0x10
        self.offset_to_value_dictonary[0x14] = cam_animation_data[5]
        self.name_to_offset_dictonary["position (y)"] = 0x14
        self.offset_to_value_dictonary[0x18] = cam_animation_data[6]
        self.name_to_offset_dictonary["position (z)"] = 0x18

        self.offset_to_value_dictonary[0x1C] = cam_animation_data[7]
        self.name_to_offset_dictonary["rotation (x)"] = 0x1C
        self.offset_to_value_dictonary[0x20] = cam_animation_data[8]
        self.name_to_offset_dictonary["rotation (y)"] = 0x20
        self.offset_to_value_dictonary[0x24] = cam_animation_data[9]
        self.name_to_offset_dictonary["rotation (z)"] = 0x24

        self.offset_to_value_dictonary[0x28] = cam_animation_data[10]
        self.name_to_offset_dictonary["twist"] = 0x28

        print(self.offset_to_value_dictonary)
        print(self.name_to_offset_dictonary)

        pass

    pass

class Frame_Data_Type(Enum):
    SINGLE = 0
    FLOAT_16_BIT = 1
    BYTE = 2

class Key_Data_Type(Enum):
    SINGLE = 0
    INT16 = 1
    SBYTE = 2

class Curve_Data_Type(Enum):
    CUBIC_SINGLE = 0
    LINEAR_SINGLE = 1
    BAKED_SINGLE = 2
    # TODO: What is and where is 3?
    STEP_INTEGER = 4
    BAKED_INTEGER = 5
    STEP_BOOLEAN = 6
    BAKED_BOOLEAN = 7

@dataclass
class Curve():
    frame_data_type = Frame_Data_Type.SINGLE
    key_data_type = Key_Data_Type.SINGLE
    curve_data_type = Curve_Data_Type.CUBIC_SINGLE

    animation_data_offset = 0

    start_frame = 0.0
    end_frame = 0.0

    data_scale = 0.0
    data_offset = 0.0

    # if BFRES version >= 3.4.0.0
    data_delta = 0.0

    elements_per_key = 0

    def frame_data_type_to_struct_format_string(self, frame_data_type: Frame_Data_Type):
        if frame_data_type == Frame_Data_Type.SINGLE:
            return ('f', 4)
        elif frame_data_type == Frame_Data_Type.FLOAT_16_BIT:
            return ('2s', 2)
        elif frame_data_type == Frame_Data_Type.BYTE:
            return ('B', 1)

        raise ValueError('Unkown Frame_Data_Type value passed')

    def key_data_type_to_struct_format_string(self, key_data_type: Key_Data_Type):
        if key_data_type == Key_Data_Type.SINGLE:
            return ('f', 4)
        elif key_data_type == Key_Data_Type.INT16:
            return ('h', 2)
        elif key_data_type == Key_Data_Type.SBYTE:
            return ('b', 1)

        raise ValueError('Unkown Key_Data_Type value passed')

    def elements_per_key(self, curve_data_type: Curve_Data_Type):
        if curve_data_type == Curve_Data_Type.CUBIC_SINGLE:
            return 4
        elif curve_data_type == Curve_Data_Type.LINEAR_SINGLE:
            return 2
        elif curve_data_type >= Curve_Data_Type.BAKED_SINGLE and curve_data_type <= Curve_Data_Type.BAKED_BOOLEAN:
            return 1

        raise ValueError('Unkown Curve_Data_Type value passed')

    def convert_binary_to_Curve(self, binary_data: bytes, offset_to_curve: int):
        #######################
        # Curve Header

        # TODO: Implement bfres version curve header for less than 3.4.0.0
        # if parent_bfres_instance.version >= [3,4,0,0]
        #     print('is great')
        curve_header = struct.unpack(">H H I f f f f f i i", binary_data[offset_to_curve:offset_to_curve + 0x24])
        print(curve_header)

        i = curve_header[0]

        self.frame_data_type = Frame_Data_Type(i >> 0 & 0x3)
        self.key_data_type = Key_Data_Type(i >> 2 & 0x3)
        self.curve_data_type = Curve_Data_Type(i >> 4 & 0x7)
        print("Frames Data Type: ", self.frame_data_type)
        print("Keys Data Type: ", self.key_data_type)
        print("Interpolation Type: ", self.curve_data_type)

        self.start_frame = curve_header[3]
        self.end_frame = curve_header[4]

        self.data_scale = curve_header[5]
        self.data_offset = curve_header[6]
        print(self.data_scale, self.data_offset)

        # For whatever animation data struct this is linked to,
        # this value is the offset from the start of that struct that this curve controls
        self.animation_data_offset = curve_header[2]
        print(hex(self.animation_data_offset))

        key_count = curve_header[1]
        print("Key count: ", key_count)

        frame_array_offset = offset_to_curve + 0x1C + curve_header[8]
        key_array_offset = offset_to_curve + 0x20 + curve_header[9]

        frame_format, frame_format_size = self.frame_data_type_to_struct_format_string(self.frame_data_type)
        frame_count = key_count

        if self.frame_data_type == Frame_Data_Type.FLOAT_16_BIT:
            frame_format = 's'
            frame_count *= 2

        format_string = ">" + str(frame_count) + frame_format
        frames = struct.unpack(format_string, binary_data[frame_array_offset:frame_array_offset + (frame_format_size * key_count)])
        frame_values = frames[0]

        if self.frame_data_type == Frame_Data_Type.FLOAT_16_BIT:
            bytes_obj = frame_values
            # Split into pairs for easier parsing
            L = [bytes_obj[i * 2:(i * 2) + 2] for i in range(len(bytes_obj[::2]))]

            frame_values = []
            for pair in L:
                pair_flipped = bytes([c for t in zip(pair[1::2], pair[::2]) for c in t])
                float16 = np.frombuffer(pair_flipped, dtype = np.float16) / (1 << 5)
                frame_values.append(float16[0])

        frame_values = list(frame_values)
        print("Frames: ", frame_values)

        key_format, key_format_size = self.key_data_type_to_struct_format_string(self.key_data_type)
        self.elements_per_key = self.elements_per_key(self.curve_data_type)

        format_string = ">" + str(key_count * self.elements_per_key) + key_format
        keys = struct.unpack(format_string, binary_data[key_array_offset:key_array_offset + (key_format_size * self.elements_per_key * key_count)])
        keys = list(keys)

        # Granularity of keys will be garbage if INT16 or SBYTE.  Data_scale and data_offset fixes that
        keys = [(x * self.data_scale) for x in keys]
        for i in range(0, len(keys), self.elements_per_key):
            keys[i] += self.data_offset
            print(keys[i:i + self.elements_per_key])

        # print("Keys: ", keys)

        pass

    pass

@dataclass
class FCAM(Subfile):
    magic = "FCAM"

    cam_animation_data = None

    offset_to_curve_array_dictonary = defaultdict(list)

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

        print("CameraAnimationData:")
        cam_animation_data_offset = offset_to_FCAM_Section + 0x1C + fcam_header[8]
        print(cam_animation_data_offset)

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

        for i in range(curve_count):
            curve = Curve()

            current_curve_offset = curve_array_start_offset + (i * 0x24)
            curve.convert_binary_to_Curve(binary_data, current_curve_offset)

            self.offset_to_curve_array_dictonary[curve.animation_data_offset].append(curve)
            print(list(self.cam_animation_data.name_to_offset_dictonary.keys())[list(self.cam_animation_data.name_to_offset_dictonary.values()).index(curve.animation_data_offset)])

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
