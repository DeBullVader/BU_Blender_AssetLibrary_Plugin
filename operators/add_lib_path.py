import bpy
import os
import platform
from bpy.types import Context, Operator
from ..utils.addon_info import add_core_library,add_user_upload_folder



    
class BU_OT_AddLibraryPath(Operator):
    bl_idname = "bu.addlibrary"
    bl_label = "add library to preference filepaths"
   
    def execute(self, context):
        dir_path = add_core_library()
        user_dir = add_user_upload_folder(dir_path)
        return {'FINISHED'} 
    

    #TO DO Remove libs button
class BU_OT_RemoveLibraryPath(Operator):
    bl_idname = "bu.removeLibrary"
    bl_label = "Remove BU asset Libraries from preferences filepaths"

    def execute(self, context):
        lib_name = 'BU_AssetLibrary_Core'
        lib_username = "BU_User_Upload"
        
        return {'FINISHED'} 