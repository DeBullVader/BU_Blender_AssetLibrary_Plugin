import bpy
from bpy.types import Operator


class BU_OT_AddLibraryPath(Operator):
    bl_idname = "bu.addlibrary"
    bl_label = "add library to preference filepaths"
    def execute(self, context):
        
        dir_path = bpy.context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.lib_path
        lib_name = 'BU_AssetLibrary_Core'
        if dir_path != "":
            bpy.ops.preferences.asset_library_add(directory =dir_path, check_existing = True)
            new_library = bpy.context.preferences.filepaths.asset_libraries[-1]
            new_library.name = lib_name
            # asset_libraries.append(bpy.types.UserAssetLibrary())
        return {'FINISHED'}
    