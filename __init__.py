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
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

def apply_animation_curves_to_blender_object(fcam_instance: bfres_file_format.FCAM, action: bpy.types.Action, curve_name: str, data_path: str, data_path_index: int, frame_offset: int, key_modifier = 1):
    fc = action.fcurves.new(data_path=data_path, index=data_path_index)

    curve_offset = fcam_instance.cam_animation_data.name_to_offset_dictonary[curve_name]
    curves = fcam_instance.offset_to_curve_array_dictonary[curve_offset]

    for curve_idx, curve in enumerate(curves):
        existing_points_on_curve = len(fc.keyframe_points)

        frames = len(curve.frames)
        elements_per_key = curve.elements_per_key

        fc.keyframe_points.add(frames)

        for k in range(existing_points_on_curve, frames):
            frame_index = k - existing_points_on_curve
            key_index_base = frame_index * elements_per_key

            diff = curve.end_frame - curve.start_frame
            frame = (curve.frames[frame_index] * diff) + curve.start_frame + frame_offset

            kp = fc.keyframe_points[k]
            # TODO: Implement each interpolation method in Curve
            kp.interpolation = 'BEZIER'
            kp.co = (frame, curve.keys[key_index_base] * key_modifier)

            # kp.handle_left = kp.co

            kp.handle_left = (kp.co[0] - (curve.keys[key_index_base + 2] * curve.keys[key_index_base + 1] / 3), kp.co[1] - (curve.keys[key_index_base + 3] * curve.keys[key_index_base + 1] / 3))
            kp.handle_right = (kp.co[0] + (curve.keys[key_index_base + 2] * curve.keys[key_index_base + 1] / 3), kp.co[1] + (curve.keys[key_index_base + 3] * curve.keys[key_index_base + 1] / 3))

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

    offset: IntProperty(
        name="Start Frame Offset"
    )

    def execute(self, context):
        with open(self.filepath, mode = 'rb') as f:
            fileContent = f.read()

            bfres_file = bfres_file_format.BFRES(binary_data = fileContent)
            fcam_instance = bfres_file.file_type_index_groups[10].entries[1].data.fcam_index_group.entries[1].data

            obj = bpy.data.objects.new( "empty", None )

            # due to the new mechanism of "collection"
            bpy.context.scene.collection.objects.link(obj)

            # empty_draw was replaced by empty_display
            obj.empty_display_size = 2
            obj.empty_display_type = 'PLAIN_AXES'

            # Setup animation data for object
            obj.animation_data_clear()
            obj.animation_data_create()
            action = obj.animation_data.action = bpy.data.actions.new("groovy")

            # BotW coordinate system:
            #   +X east
            #   +Z south
            #   +Y up
            # Blender coordinate system:
            #   +X east
            #   +Y north
            #   +Z up

            # X axis flipped
            apply_animation_curves_to_blender_object(fcam_instance, action, "position (x)", "location", 0, self.offset, key_modifier = -1)
            # Curve Y applied to Z axis
            apply_animation_curves_to_blender_object(fcam_instance, action, "position (y)", "location", 2, self.offset)
            # Curve Z applied to Y axis
            apply_animation_curves_to_blender_object(fcam_instance, action, "position (z)", "location", 1, self.offset)

            obj2 = bpy.data.objects.new( "empty", None )

            # due to the new mechanism of "collection"
            bpy.context.scene.collection.objects.link(obj2)

            # empty_draw was replaced by empty_display
            obj2.empty_display_size = 2
            obj2.empty_display_type = 'PLAIN_AXES'

            # Setup animation data for object
            obj2.animation_data_clear()
            obj2.animation_data_create()
            action2 = obj2.animation_data.action = bpy.data.actions.new("groovy")

            # X axis flipped
            apply_animation_curves_to_blender_object(fcam_instance, action2, "rotation (x)", "location", 0, self.offset, key_modifier = -1)
            # Curve Y applied to Z axis
            apply_animation_curves_to_blender_object(fcam_instance, action2, "rotation (y)", "location", 2, self.offset)
            # Curve Z applied to Y axis
            apply_animation_curves_to_blender_object(fcam_instance, action2, "rotation (z)", "location", 1, self.offset)

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
