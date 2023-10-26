import bpy
import os
import shutil
from bpy.types import Operator
from ..utils.addon_info import add_library_paths,get_addon_name



    
class BU_OT_AddLibraryPath(Operator):
    """Adds a location to where assets of the library get downloaded to"""
    bl_idname = "bu.addlibrarypath"
    bl_label = "Add library to preference filepaths"
   
    def execute(self, context):
        # if 'BU_AssetLibrary_Core' or 'BU_AssetLibrary_Premium' not in bpy.context.preferences.filepaths.asset_libraries:
        add_library_paths()
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
        
        addon_name = get_addon_name()
        old_dir_path = addon_name.preferences.lib_path
        new_lib_path = addon_name.preferences.new_lib_path
        lib_names=(
            'BU_AssetLibrary_Core', 
            'BU_AssetLibrary_Premium',
        )
        for lib_name in lib_names:
            old_core_lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
            bpy.ops.preferences.asset_library_remove(old_core_lib_index)
            current_core_path = f'{old_dir_path}{os.sep}{lib_name}'
        if os.path.exists(current_core_path):
            shutil.copytree(old_dir_path,new_lib_path,dirs_exist_ok=True)
            shutil.rmtree(current_core_path)   
            addon_name.preferences.lib_path = new_lib_path
            add_library_paths()
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
       
            
        
        return {'FINISHED'} 
    #TO DO Remove libs button

class BU_OT_RemoveLibrary(Operator):
    """Remove asset library location and all assets downloaded"""
    bl_idname = "bu.removelibrary"
    bl_label = "Remove BU asset Libraries paths"
    bl_options = {"REGISTER","UNDO"}
    def execute(self, context):
        lib_names=(
            'BU_AssetLibrary_Core', 
            'BU_AssetLibrary_Premium',
        )
        for lib_name in lib_names:
            if lib_name in bpy.context.preferences.filepaths.asset_libraries:
                lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
                bpy.ops.preferences.asset_library_remove(lib_index)
                # shutil.rmtree(c_lib.path)
        get_addon_name().preferences.lib_path = ''
        return {'FINISHED'} 
    
    
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self,context):
        layout = self.layout
        layout.label(text='Warning: This will remove the asset paths and Library path location',icon='TRASH')
    
class BU_OT_ConfirmSetting(Operator):
    """Set Author for uploaded assets"""
    bl_idname = "bu.confirmsetting"
    bl_label = "Remove BU asset Libraries"
    bl_options = {"REGISTER"}
    def execute(self, context):
        bpy.ops.wm.save_userpref()
        return {'FINISHED'} 
    

    