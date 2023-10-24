import bpy
from . import addon_info


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
    addonprefs=addon_info.get_addon_name().preferences
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
    if addon_prefs.debug_mode == True:
        addon_prefs.author = 'DebugMode'


class BU_OT_DebugMode(bpy.types.Operator):
    '''Testing operator Debug mode'''
    bl_idname = "bu.debug_mode"
    bl_label = "Debug mode"
    bl_description = "Debug mode"
    bl_options = {'REGISTER', 'UNDO'}



    def execute(self, context):
        addonprefs=addon_info.get_addon_name().preferences
        addon_info.set_drive_ids(context)
        addonprefs.debug_mode = not addonprefs.debug_mode
        addonprefs.author = 'DebugMode'
        set_upload_target(self,context)
        return {'FINISHED'}
    
class AdminPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Admin"
    bl_label = 'Admin panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Admin'
    

    def draw(self,context):
        addonprefs =addon_info.get_addon_name().preferences
        addonprefs.is_admin = True
        layout = self.layout
        layout.label(text='Switch to test folders debug')
        layout.label(text='Enable to switch to test server folders')
        layout.operator("bu.debug_mode", text="Debug mode", depress=True if addonprefs.debug_mode else False)
        # layout.prop(self.addonprefs, "debug_mode", text="Server Debug mode", toggle= True,)
        box = layout.box()
        
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
                        
                        if current_library_name in ('BU_AssetLibrary_Core', 'BU_AssetLibrary_Premium'):
                            print(current_library_name)
                            if current_library_name == 'BU_AssetLibrary_Core':
                                box.label(text='Core Library', icon='FILE_FOLDER')
                            elif current_library_name == 'BU_AssetLibrary_Premium':
                                box.label(text='Premium Library', icon='FILE_FOLDER')
                            box.label(text= 'Download drive folder IDs: Test Folders' if addonprefs.debug_mode else 'Download drive folder IDs: Real Folders')
                            box.label(text=f' download folder id: {addonprefs.download_folder_id}'if current_library_name == 'BU_AssetLibrary_Core' else 'download folder id: This is handled in aws')
                            box.label(text=f' download folder id placeholder: {addonprefs.download_folder_id_placeholders}')
                        elif current_library_name == 'LOCAL': 
                            box.label(text='Upload to Library', icon='FILE_NEW')
                            scene = context.scene
                            box.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
                            box.label(text= 'Upload drive folder IDs: Test Folders' if addonprefs.debug_mode else 'Upload drive folder IDs: Real Folders')
                            # box.label(text= 'Core'if scene.upload_target_enum.switch_upload_target == 'core_upload' else 'Premium')
                            box.label(text=f' ID: {addonprefs.upload_parent_folder_id}')

                        else:
                            box.label(text = 'select CORE,Premium or current file to display folder ids')


        


        
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