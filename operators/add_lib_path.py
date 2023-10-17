import bpy
import os
import shutil
from bpy.types import Operator
from ..utils.addon_info import add_core_library_path,add_user_upload_folder,get_addon_name



    
class BU_OT_AddLibraryPath(Operator):
    """Adds a location to where assets of the library get downloaded to"""
    bl_idname = "bu.addlibrarypath"
    bl_label = "Add library to preference filepaths"
   
    def execute(self, context):
        if 'BU_AssetLibrary_Core' not in bpy.context.preferences.filepaths.asset_libraries:
            dir_path = add_core_library_path()
        if 'BU_User_Upload' not in bpy.context.preferences.filepaths.asset_libraries:
            add_user_upload_folder(dir_path)
        return {'FINISHED'} 
    
class BU_OT_ChangeLibraryPath(Operator):
    """Change to a new directory location for the library, this will copy existing assets and remove the old library"""
    bl_idname = "bu.changelibrarypath"
    bl_label = "Change core library path"

    @classmethod
    def poll (cls,context):
        addon_name = get_addon_name()
        new_lib_path = addon_name.preferences.new_lib_path
        dir_path = addon_name.preferences.lib_path
        if dir_path != '':
            if new_lib_path == dir_path:
                cls.poll_message_set('This is the same directory. Please select a different directory')
                return False
        if new_lib_path != '':
            cls.poll_message_set('Please choose a directory')
            return True
       

    def execute(self, context):
        
        c_lib = bpy.context.preferences.filepaths.asset_libraries['BU_AssetLibrary_Core']
        addon_name = get_addon_name()
        dir_path = addon_name.preferences.lib_path
        new_lib_path = addon_name.preferences.new_lib_path

        old_core_lib_index = bpy.context.preferences.filepaths.asset_libraries.find('BU_AssetLibrary_Core')
        bpy.ops.preferences.asset_library_remove(old_core_lib_index)
        current_core_path = f'{dir_path}{os.sep}BU_AssetLibrary_Core'
        if os.path.exists(current_core_path):
            shutil.copytree(dir_path,new_lib_path,dirs_exist_ok=True)
            shutil.rmtree(current_core_path)   
            addon_name.preferences.lib_path = new_lib_path
            add_core_library_path()
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
       
            
        
        return {'FINISHED'} 
    #TO DO Remove libs button

class BU_OT_RemoveLibrary(Operator):
    """Remove asset library location and all assets downloaded"""
    bl_idname = "bu.removelibrary"
    bl_label = "Remove BU asset Libraries"
    bl_options = {"REGISTER","UNDO"}
    def execute(self, context):
        if 'BU_AssetLibrary_Core' in bpy.context.preferences.filepaths.asset_libraries:
            c_lib = bpy.context.preferences.filepaths.asset_libraries['BU_AssetLibrary_Core']
            lib_index = bpy.context.preferences.filepaths.asset_libraries.find('BU_AssetLibrary_Core')
            bpy.ops.preferences.asset_library_remove(lib_index)
            shutil.rmtree(c_lib.path)
            return {'FINISHED'} 
    
    
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self,context):
        layout = self.layout
        layout.label(text='Are you sure you want to remove the library and ALL downloaded assets?')
    
class BU_OT_ConfirmSetting(Operator):
    """Set Author for uploaded assets"""
    bl_idname = "bu.confirmsetting"
    bl_label = "Remove BU asset Libraries"
    bl_options = {"REGISTER"}
    def execute(self, context):
        bpy.ops.wm.save_userpref()
        return {'FINISHED'} 
    

    