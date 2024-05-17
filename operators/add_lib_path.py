import bpy
from bpy.types import Operator
from ..utils import addon_info
from ..utils.constants import *
class BU_OT_AddLibraryPath(Operator):
    """Sets up the asset library in your selected location"""
    bl_idname = "bu.addlibrarypath"
    bl_label = "Add library to preference filepaths"

    @classmethod
    def poll (cls,context):
        addon_prefs = addon_info.get_addon_prefs()
        if addon_prefs.lib_path != '':
            return True
        return False
    
    def execute(self, context):
        addon_info.add_library_paths(is_startup=False)
        return {'FINISHED'} 

class BU_OT_RemoveLibrary(Operator):
    """Remove asset library location and all assets downloaded"""
    bl_idname = "bu.removelibrary"
    bl_label = "Remove Uniblend Asset Library paths"
    bl_options = {"REGISTER"}

    def execute(self, context):
        addon_prefs = addon_info.get_addon_prefs()
        lib_names=(
            DEMO_LIB,
            PREMIUM_LIB,
            TEST_DEMO_LIB,
            TEST_PREMIUM_LIB,
            DEPRECATED_LIB,
        )
        for name in lib_names:
            if name in bpy.context.preferences.filepaths.asset_libraries: 
                idx = bpy.context.preferences.filepaths.asset_libraries.find(name)
                bpy.ops.preferences.asset_library_remove(index=idx)
        addon_prefs.lib_path = ''
        bpy.ops.wm.save_userpref()
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
    

    