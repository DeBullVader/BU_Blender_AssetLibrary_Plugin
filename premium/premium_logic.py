import bpy,json,textwrap

from bpy.types import Context
from ..utils.addon_info import get_addon_prefs
from .. import icons
from .handle_license_api import validate_license_api

class Validate_Options(bpy.types.Operator):
    bl_idname = "bu.validate_options" 
    bl_label = "Validate Options" 
    bl_options = {"REGISTER"}

 

    def execute(self, context):
        return {'FINISHED'}
    
class Validate_Web3_License(bpy.types.Operator):
    bl_idname = "bu.validate_web3_license" 
    bl_label = "Register web3 License" 
    bl_options = {"REGISTER"}
    
    license_type: bpy.props.StringProperty()
    userId: bpy.props.StringProperty()
    
    
    def execute(self, context):
        addon_prefs = get_addon_prefs()
        user_id = self.userId if addon_prefs.user_id=='' else addon_prefs.user_id
        if self.userId != '':
            succes, data, error = validate_license_api(user_id, '', self.license_type)
            if succes:
                jsonData = json.loads(data)
                bpy.types.Scene.validation_message = 'Your premium license is valid!'
                bpy.types.Scene.validation_error_message = ''
                addon_prefs.payed = jsonData['payed']
                license_type = jsonData['licenseType']
                if license_type == 'web3':
                    addon_prefs.user_id = jsonData['userId']
                    addon_prefs.license_type = license_type
            else:
                bpy.types.Scene.validation_message = 'Your premium license is not valid!'
                bpy.types.Scene.validation_error_message = error
        else:
            bpy.types.Scene.validation_message = 'Please validate your license'
            bpy.types.Scene.validation_error_message = ''
        return{'FINISHED'}
   
    def draw(self,context):
        addon_prefs = get_addon_prefs()
        layout = self.layout           
        if self.license_type == 'web3':
            if addon_prefs.user_id=='':
                layout.prop(self, 'userId', text='License')
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class Validate_Gumroad_License(bpy.types.Operator):
    bl_idname = "bu.validate_gumroad_license" 
    bl_label = "Register Gumroad License" 
    bl_options = {"REGISTER"}
    
    license_type: bpy.props.StringProperty()
    key: bpy.props.StringProperty()
    
    def execute(self, context):
        addon_prefs = get_addon_prefs()

        if self.key != '':
            succes, data, error = validate_license_api('', self.key, self.license_type)
            if succes:
                jsonData = json.loads(data)
                bpy.types.Scene.validation_message = 'Your premium license is valid!'
                bpy.types.Scene.validation_error_message = ''
                addon_prefs.payed = jsonData['payed']
                license_type = jsonData['licenseType']
                if license_type == 'gumroad':
                    addon_prefs.user_id = jsonData['userId']
                    addon_prefs.license_type = license_type
            else:
                jsonError = json.loads(error)
                bpy.types.Scene.validation_message = 'Your premium license is not valid!'
                bpy.types.Scene.validation_error_message = jsonError['error']
        else:
            if addon_prefs.user_id!='':
                succes, data, error = validate_license_api(addon_prefs.user_id, '', self.license_type)
                if succes:
                    jsonData = json.loads(data)
                    bpy.types.Scene.validation_message = 'Your premium license is valid!'
                    bpy.types.Scene.validation_error_message = ''
                    addon_prefs.payed = jsonData['payed']
                    license_type = jsonData['licenseType']
                    if license_type == 'gumroad':
                        addon_prefs.user_id = jsonData['userId']
            else:
                bpy.types.Scene.validation_message = 'Please validate your license'
                bpy.types.Scene.validation_error_message = ''
        return{'FINISHED'}
   
    def draw(self,context):
        addon_prefs = get_addon_prefs()
        layout = self.layout
        if self.license_type == 'gumroad':
            if addon_prefs.user_id=='':
                layout.prop(self, 'key',text='License' )
        
    def invoke(self, context, event):
        addon_prefs = get_addon_prefs()
        if addon_prefs.user_id!='':
            self.key =''
        else:
            return context.window_manager.invoke_props_dialog(self)
    
def gumroad_register(self,context, status, error,box):
    addon_prefs = get_addon_prefs()
    row=box.row()
    row.alignment='CENTER'
    col = row.column()
    if error == 'You have a Free Core license': 
        col.label(text=error,icon ='ERROR')
        col.label(text='If you want to use premium features, please upgrade your license.')
        upgrade_license = col.operator('wm.url_open',text='Upgrade License',icon='UNLOCKED')
        upgrade_license.url = 'https://bakeduniverse.gumroad.com/l/bbps'
    else:
        if status !='':
            col.label(text=status, icon='CHECKMARK' if addon_prefs.payed else 'GREASEPENCIL')
        if error != '':
            col.label(text=error,icon='ERROR')
    col.separator(factor=1)
    row = box.row()
    if not addon_prefs.user_id:
        gumroad_op =row.operator('bu.validate_gumroad_license', text='Validate Gumroad License')
        gumroad_op.license_type = 'gumroad'
    else:
        row.operator('bu.reset_validate', text='Reset License Validation')

    
def web3_premium_validation(self,context, status, error,box):
    i = icons.get_icons()
    addon_prefs = get_addon_prefs()
    row=box.row()
    row.alignment='CENTER'
    col = row.column()
    if status !='':
        col.label(text=status, icon='CHECKMARK' if addon_prefs.payed else 'GREASEPENCIL')
    if error != '':
        col.label(text=error,icon='ERROR')
    col.separator(factor=1)
    row = box.row()
    if not addon_prefs.user_id:
        web3_op =row.operator('bu.validate_web3_license', text='Validate Web3 License')
        web3_op.license_type = 'web3'
    else:
        row.operator('bu.reset_validate', text='Reset License Validation')

class Validate_Reset(bpy.types.Operator):
    bl_idname = "bu.reset_validate"
    bl_label = "Reset License Validation"

    def execute(self, context):
        addon_prefs = get_addon_prefs()
        addon_prefs.user_id = ''
        return {'FINISHED'} 

classes = (
    Validate_Options,
    Validate_Gumroad_License,
    Validate_Web3_License,
    Validate_Reset,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)