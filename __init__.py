bl_info = {
    "name": "BFRES File Format",
    'author': 'Taras Palczynski III',
    'version': (0,0,1),
    "blender": (2, 80, 0),
    'location': 'File > Import',
    "category": "Import/Export",
}

import bpy
from . import bfres_file_format

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class Import_BFRES(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""

    bl_idname = "import.bfres"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import BFRES"

    # ImportHelper mixin class uses this
    # filename_ext = ".txt"

    # filter_glob: StringProperty(
    #     default="*.txt",
    #     options={'HIDDEN'},
    #     maxlen=255,  # Max internal buffer length, longer would be clamped.
    # )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    # use_setting: BoolProperty(
    #     name="Example Boolean",
    #     description="Example Tooltip",
    #     default=True,
    # )
    #
    # type: EnumProperty(
    #     name="Example Enum",
    #     description="Choose between two items",
    #     items=(
    #         ('OPT_A', "First Option", "Description one"),
    #         ('OPT_B', "Second Option", "Description two"),
    #     ),
    #     default='OPT_A',
    # )

    def execute(self, context):
        with open(self.filepath, mode = 'rb') as f:
            fileContent = f.read()

            bfres_file = bfres_file_format.BFRES(binary_data = fileContent)

            fcam_instance = bfres_file.file_type_index_groups[10].entries[1].data.fcam_index_group.entries[1].data

            pos_x_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary["position (x)"]
            pos_x_curves = fcam_instance.offset_to_curve_array_dictonary[pos_x_offset]

            pos_y_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary["position (y)"]
            pos_y_curves = fcam_instance.offset_to_curve_array_dictonary[pos_y_offset]

            pos_z_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary["position (z)"]
            pos_z_curves = fcam_instance.offset_to_curve_array_dictonary[pos_z_offset]

            obj = bpy.data.objects.new( "empty", None )

            # due to the new mechanism of "collection"
            bpy.context.scene.collection.objects.link(obj)

            # empty_draw was replaced by empty_display
            obj.empty_display_size = 2
            obj.empty_display_type = 'PLAIN_AXES'

            length = len(pos_x_curves[0].frames)
            print(length, pos_x_curves[0].elements_per_key, len(pos_x_curves[0].keys))
            start_frame = pos_x_curves[0].start_frame
            end_frame = pos_x_curves[0].end_frame
            diff = end_frame - start_frame

            for frame_index in range(length):
                key_index = pos_x_curves[0].elements_per_key * frame_index

                obj.location.x = pos_x_curves[0].keys[key_index]

                frame = (pos_x_curves[0].frames[frame_index] * diff) + start_frame
                frame = int(round(frame))
                obj.keyframe_insert(data_path="location", index=0, frame=frame)

            length = len(pos_y_curves[0].frames)
            print(length)
            start_frame = pos_y_curves[0].start_frame
            end_frame = pos_y_curves[0].end_frame
            diff = end_frame - start_frame

            for frame_index in range(length):
                key_index = pos_y_curves[0].elements_per_key * frame_index

                obj.location.y = pos_y_curves[0].keys[key_index]

                frame = (pos_y_curves[0].frames[frame_index] * diff) + start_frame
                frame = int(round(frame))
                obj.keyframe_insert(data_path="location", index=1, frame=frame)

            length = len(pos_z_curves[0].frames)
            print(length)
            start_frame = pos_z_curves[0].start_frame
            end_frame = pos_z_curves[0].end_frame
            diff = end_frame - start_frame

            for frame_index in range(length):
                key_index = pos_z_curves[0].elements_per_key * frame_index

                obj.location.z = pos_z_curves[0].keys[key_index]

                frame = (pos_z_curves[0].frames[frame_index] * diff) + start_frame
                frame = int(round(frame))
                obj.keyframe_insert(data_path="location", index=2, frame=frame)

            # TODO: Figure out aim direction
            rot_x_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary["rotation (x)"]
            rot_x_curves = fcam_instance.offset_to_curve_array_dictonary[rot_x_offset]

            rot_y_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary["rotation (y)"]
            rot_y_curves = fcam_instance.offset_to_curve_array_dictonary[rot_y_offset]

            rot_z_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary["rotation (z)"]
            rot_z_curves = fcam_instance.offset_to_curve_array_dictonary[rot_z_offset]

            length = len(rot_x_curves[0].frames)
            print(length, rot_x_curves[0].elements_per_key, len(rot_x_curves[0].keys))
            start_frame = rot_x_curves[0].start_frame
            end_frame = rot_x_curves[0].end_frame
            diff = end_frame - start_frame

            for frame_index in range(length):
                key_index = rot_x_curves[0].elements_per_key * frame_index

                obj.rotation_euler.x = rot_x_curves[0].keys[key_index] / (180 / 3.14)

                frame = (rot_x_curves[0].frames[frame_index] * diff) + start_frame
                frame = int(round(frame))
                obj.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)

            length = len(rot_y_curves[0].frames)
            print(length)
            start_frame = rot_y_curves[0].start_frame
            end_frame = rot_y_curves[0].end_frame
            diff = end_frame - start_frame

            for frame_index in range(length):
                key_index = rot_y_curves[0].elements_per_key * frame_index

                obj.rotation_euler.y = rot_y_curves[0].keys[key_index] / (180 / 3.14)

                frame = (rot_y_curves[0].frames[frame_index] * diff) + start_frame
                frame = int(round(frame))
                obj.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)

            length = len(rot_z_curves[0].frames)
            print(length)
            start_frame = rot_z_curves[0].start_frame
            end_frame = rot_z_curves[0].end_frame
            diff = end_frame - start_frame

            for frame_index in range(length):
                key_index = rot_z_curves[0].elements_per_key * frame_index

                obj.rotation_euler.z = rot_z_curves[0].keys[key_index] / (180 / 3.14)

                frame = (rot_z_curves[0].frames[frame_index] * diff) + start_frame
                frame = int(round(frame))
                obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)

        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(Import_BFRES.bl_idname, text="Binary caFe RESources (BFRES)")


def register():
    bpy.utils.register_class(Import_BFRES)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(Import_BFRES)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
