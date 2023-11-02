import bpy
import os
from . import addon_info
from bpy.app.handlers import persistent

def set_upload_target(self,context):
    upload_target = context.scene.upload_target_enum.switch_upload_target
    addon_prefs = addon_info.get_addon_name().preferences
    if upload_target == 'core_upload':
        addon_prefs.upload_parent_folder_id = addon_prefs.bl_rna.properties['upload_parent_folder_id'].default if addon_prefs.debug_mode == False else "1dcVAyMUiJ5IcV7QBtQ7a99Jl_DdvL8Qo"
    elif upload_target == 'premium_upload':
        addon_prefs.upload_parent_folder_id = "1rh2ZrFM9TUJfWDMatbaniCKaXpKDvnkx" if addon_prefs.debug_mode == False else "1IWX6B2XJ3CdqO9Tfbk2m5HdvnjVmE_3-"
    

class UploadTargetProperty(bpy.types.PropertyGroup):
    switch_upload_target: bpy.props.EnumProperty(
        name = 'Upload target',
        description = "Upload to Core or Premium",
        items=[
            ('core_upload', 'Core', '', '', 0),
            ('premium_upload', 'Premium', '', '', 1)
        ],
        default='core_upload',
        update=set_upload_target
    )
def drawUploadTarget(self,context):
    addon_prefs=addon_info.get_addon_name().preferences
    current_library_name = context.area.spaces.active.params.asset_library_ref
    if current_library_name == "LOCAL":
        layout = self.layout
        row= layout.row()
         
        row.label(text=' ') # adding some space to menu
        scene = context.scene
        row.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
        set_upload_target(self,context)
        row.label(text='|') # adding some space to menu

def defaults():
    addon_prefs = addon_info.get_addon_name().preferences
    lib_names = addon_info.get_original_lib_names()
    addon_info.find_lib_path(addon_prefs,lib_names)
    
    # if addon_prefs.debug_mode == True:
    #     addon_prefs.author = 'DebugMode'
    # else:
    #     addon_prefs.author = ''



def get_test_lib_paths():
    libs =[]
    lib_names = ['TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium']
    addon_prefs = addon_info.get_addon_name().preferences
    dir_path = addon_prefs.lib_path
    for lib_name in lib_names:
        lib_path = os.path.join(dir_path,lib_name)
        if dir_path !='':
            if lib_name in bpy.context.preferences.filepaths.asset_libraries:
                lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
                if lib.path != lib_path:
                    lib.path = lib_path
                    libs.append(lib)
                else:
                    libs.append(lib)
    return libs

# def switch_between_test_and_real_libs():
#     test_lib_names = ('TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium')
#     real_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium')
#     addon_prefs = addon_info.get_addon_name().preferences

#     def create_libraries(lib_names):
#         dir_path = addon_prefs.lib_path
#         for lib_name in lib_names:
#             lib_path = os.path.join(dir_path,lib_name)
#             if os.path.exists(dir_path):
#                 if not os.path.isdir(str(lib_path)): # checks whether the directory exists
#                     os.mkdir(str(lib_path)) # if it does not yet exist, makes it
#                     print('Created directory and library path', os.path.isdir(str(lib_path)))
#                 if dir_path != "":
#                     if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
#                         bpy.ops.preferences.asset_library_add(directory = lib_path, check_existing = True)
#                 else:
#                     print('Did not add library path', lib_name)
    

#     def remove_lib_paths(lib_names):
#         for lib_name in lib_names:
#             if lib_name in bpy.context.preferences.filepaths.asset_libraries:
#                 lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
#                 bpy.ops.preferences.asset_library_remove(lib_index)

#     if addon_prefs.debug_mode == True:
#         remove_lib_paths(real_lib_names)
#         create_libraries(test_lib_names)
#     else:
#         remove_lib_paths(test_lib_names)
#         create_libraries(real_lib_names)
#     bpy.ops.wm.save_userpref()
    
class BU_OT_DebugMode(bpy.types.Operator):
    '''Testing operator Debug mode'''
    bl_idname = "bu.debug_mode"
    bl_label = "Debug mode"
    bl_description = "Debug mode"
    bl_options = {'REGISTER', 'UNDO'}



    def execute(self, context):
        addonprefs=addon_info.get_addon_name().preferences
        addonprefs.debug_mode = not addonprefs.debug_mode
        addon_info.set_drive_ids(context)
        addonprefs.author = 'DebugMode'
        set_upload_target(self,context)
        addon_info.add_library_paths()
        return {'FINISHED'}
    
class AdminPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Admin"
    bl_label = 'Admin panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Admin'
    

    def draw(self,context):
        test_lib_names = ('TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium')
        real_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium')
        addon_prefs =addon_info.get_addon_name().preferences
        addon_prefs.is_admin = True
        layout = self.layout
        layout.label(text='Switch to test folders debug')
        layout.label(text='Enable to switch to test server folders')
        layout.operator("bu.debug_mode", text="Debug mode", depress=True if addon_prefs.debug_mode else False)
        # layout.prop(self.addonprefs, "debug_mode", text="Server Debug mode", toggle= True,)
        box = layout.box()
        
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
                        # print(current_library_name)
                        
                        if current_library_name in test_lib_names:
                            box.label(text='Core Test Library' if current_library_name == test_lib_names[0] else 'Premium Test Library', icon='FILE_FOLDER' )
                            box.label(text=f' download folder id: {addon_prefs.download_folder_id}' if current_library_name == test_lib_names[0] else 'download folder id: Handled in AWS')
                            box.label(text=f' download folder id placeholder: {addon_prefs.download_folder_id_placeholders}')
                        
                        elif current_library_name in real_lib_names:
                            box.label(text='Core Library' if current_library_name == real_lib_names[0] else 'Premium Library', icon='FILE_FOLDER' )
                            box.label(text=f' download folder id: {addon_prefs.download_folder_id}' if current_library_name == real_lib_names[0] else 'download folder id: Handled in AWS')
                            box.label(text=f' download folder id placeholder: {addon_prefs.download_folder_id_placeholders}')
                        elif current_library_name == 'LOCAL': 
                            box.label(text='Upload to Library', icon='FILE_NEW')
                            scene = context.scene
                            box.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
                            box.label(text= 'Upload drive folder IDs: Test Folders' if addon_prefs.debug_mode else 'Upload drive folder IDs: Real Folders')
                            # box.label(text= 'Core'if scene.upload_target_enum.switch_upload_target == 'core_upload' else 'Premium')
                            box.label(text=f' ID: {addon_prefs.upload_parent_folder_id}')
                        

                        else:
                            box.label(text = 'select CORE,Premium or current file to display folder ids')
        layout = self.layout
        layout.operator('bu.upload_settings', text='Upload Settings',icon='SETTINGS')

        


        
classes =(
    UploadTargetProperty,
    AdminPanel,
    BU_OT_DebugMode
   
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.upload_target_enum = bpy.props.PointerProperty(type=UploadTargetProperty)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(drawUploadTarget)
    defaults()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.upload_target_enum
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(drawUploadTarget)
