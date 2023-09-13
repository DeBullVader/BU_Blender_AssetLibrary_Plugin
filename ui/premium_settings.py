import bpy
from ..utils.addon_info import get_addon_name
from ..operators.handle_license_api import validate_license_api

class Validate_Premium_License(bpy.types.Operator):
    bl_idname = "bu.validate_license" 
    bl_label = "Validate License" 
    bl_options = {"REGISTER"}

    @classmethod
    def poll (cls,context):
        addon_name = get_addon_name()
        premium_licensekey = addon_name.preferences.premium_licensekey
        if premium_licensekey == '':
            cls.poll_message_set('Please input a valid license key')
            return False
        return True
    
    def execute(self, context):
        
        userid = get_addon_name().preferences.userID
        uuid = get_addon_name().preferences.premium_licensekey

        succes, data, error = validate_license_api(userid, uuid)
        print('this is succes = ' + str(succes))
        print('this is data = ' + str(data))
        print('this is error = ' + str(error))
        if succes:
            bpy.types.Scene.validation_message = 'Your premium license is valid!'
            bpy.types.Scene.validation_error_message = ''
        else:
            bpy.types.Scene.validation_message = 'Your premium license is not valid!'
            bpy.types.Scene.validation_error_message = error
        return{'FINISHED'}



       
    

    

class Premium_Settings_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_PREMIUM_SETTINGS_PANEL"
    bl_label = 'Blender Pro Suite Premium Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bpy.types.Scene.validation_error_message = bpy.props.StringProperty()
    bpy.types.Scene.validation_message = bpy.props.StringProperty()
    bpy.types.Scene.validation_message = "Please validate your license"
    bpy.types.Scene.validation_error_message = ''
    def draw (self, context):
        addon_prefs = get_addon_name().preferences
        status = bpy.types.Scene.validation_message
        error = bpy.types.Scene.validation_error_message
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text='Premium Verification settings')
        row = box.row()
        row = box.row()
        row.label(text=status)
        row.label(text=error)
        row = box.row()
        box = row.box()
        row = box.row()
        row.label(text='User ID')
        row.prop(addon_prefs, 'userID', text='')
        row = box.row()
        row.label(text='License Key')
        if error !='':
            row.alert = True
        row.prop(addon_prefs, 'premium_licensekey', text='' )
        row = box.row()
        row.operator('bu.validate_license', text='Validate Premium License')


classes = (
    Premium_Settings_Panel,
    Validate_Premium_License,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)