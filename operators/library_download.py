import bpy
from bpy.types import Operator


class WM_OT_downloadLibrary(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadlibrary"
    bl_label = "Download the current library from url after pressing ok"
    def execute(self, context):
        
        # dir_path = bpy.context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.lib_path
        # lib_name = 'BU_AssetLibrary_Core'
        # if dir_path != "":
        #     bpy.ops.preferences.asset_library_add(directory =dir_path, check_existing = True)
        #     new_library = bpy.context.preferences.filepaths.asset_libraries[-1]
        #     new_library.name = lib_name
            
        return {'FINISHED'}
    
    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)
    
       