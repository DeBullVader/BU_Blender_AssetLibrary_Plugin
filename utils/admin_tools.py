import bpy
from . import addon_info


def set_upload_target(self,context):
    
    upload_target = context.scene.upload_target_enum.switch_upload_target
    
    if upload_target == 'core_upload':
        addon_info.set_core_server_ids()
    elif upload_target == 'premium_upload':
        addon_info.set_premium_server_ids()
    addon_prefs = addon_info.get_addon_name().preferences
    print(addon_prefs.upload_parent_folder_id)


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
    current_library_name = context.area.spaces.active.params.asset_library_ref
    if current_library_name == "LOCAL":
        layout = self.layout
        row= layout.row()
         
        row.label(text=' ') # adding some space to menu
        scene = context.scene
        row.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
        row.label(text='|') # adding some space to menu

class BU_OT_DebugMode(bpy.types.Operator):
    bl_idname = "bu.debug_mode"
    bl_label = "Debug mode"
    bl_description = "Debug mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addon_info.get_addon_name().preferences.debug_mode = not addon_info.get_addon_name().preferences.debug_mode
        return {'FINISHED'}
    
class AdminPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Admin"
    bl_label = 'Admin panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Admin'
    
    
    def __init__(self):
        self.addonprefs = addon_info.get_addon_name().preferences
        self.addonprefs.is_admin = True

    def draw(self,content):
        layout = self.layout
        layout.label(text='Switch to test folders debug')
        layout.label(text='Enable to switch to test server folders')
        layout.prop(self.addonprefs, "debug_mode", text="Server Debug mode", toggle= True)
        
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
   
        

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.upload_target_enum
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(drawUploadTarget)