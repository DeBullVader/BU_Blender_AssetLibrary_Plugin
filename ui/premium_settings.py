import bpy
import json
from bpy.types import Context
from ..utils.addon_info import get_addon_name
from ..operators.handle_license_api import validate_license_api
from .. import icons

class Validate_Options(bpy.types.Operator):
    bl_idname = "bu.validate_options" 
    bl_label = "Validate Options" 
    bl_options = {"REGISTER"}

 

    def execute(self, context):
        return {'FINISHED'}
    

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

class Validate_Gumroad_License(bpy.types.Operator):
    bl_idname = "bu.validate_gumroad_license" 
    bl_label = "Register Gumroad License" 
    bl_options = {"REGISTER"}
    
    
    @classmethod
    def poll (cls,context):
        userid = get_addon_name().preferences.gumroad_premium_licensekey
        
        if userid == '':
            cls.poll_message_set('Please input a valid license gumroad license')
            return False
        return True

    def execute(self, context):
        addon_prefs = get_addon_name().preferences
        uuid = addon_prefs.premium_licensekey
        print(addon_prefs.premium_licensekey)
        userid = addon_prefs.gumroad_premium_licensekey
        licensetype = 'gumroad'
        succes, data, error = validate_license_api(userid, uuid, licensetype)
        # succes, data, error = verify_gumroad_license(gumroad_premium_licensekey)
        print('this is succes = ' + str(succes))
        print('this is data = ' + str(data))
        print('this is error = ' + str(error))
        print(type(data)) 
        if succes:
            jsonData = json.loads(data)
            print(jsonData)
            addon_prefs.payed = jsonData['payed']
            addon_prefs.premium_licensekey = jsonData['uuid']
            
            if jsonData['payed'] == False:
                bpy.types.Scene.validation_error_message ='You have a Free Core license'
            else:
                bpy.types.Scene.validation_message = 'Your premium license is valid!'
                bpy.types.Scene.validation_error_message = ''
                addon_prefs.premium_licensekey = jsonData['uuid']
            

        else:
            bpy.types.Scene.validation_message = 'Your premium license is not valid!'
            bpy.types.Scene.validation_error_message = error
        return{'FINISHED'}
        
        

def gumroad_register(self,context, status, error,box):
    addon_prefs = get_addon_name().preferences
    row = box.row()
    row.label(text='Validate your gumroad license')
    row = box.row()
    row.label(text='Gumroad License Key')
    if error !='' and not 'You have a Free Core license':
        row.alert = True   
    row.prop(addon_prefs, 'gumroad_premium_licensekey', text='' )
    row = box.row()
    row.label(text='BUK Premium License Key')
    if addon_prefs.premium_licensekey =='':
        row.label(text=addon_prefs.premium_licensekey)
    else:
        row.prop(addon_prefs, 'premium_licensekey', text='' )
    row = box.row()
    row.operator('bu.validate_gumroad_license', text='Validate Premium License')
       
def web3_premium_validation(self,context, status, error,box):
    i = icons.get_icons()
    addon_prefs = get_addon_name().preferences

    row = box.row()
    row.label(text='Make sure to validate your nfts and generate a license')
    row = box.row()
    get_web3_license = row.operator('wm.url_open',text='Get Web3 License',icon_value=i["bakeduniverse"].icon_id)
    get_web3_license.url = 'https://license.blender-universe.com/'
    row = box.row()
    row.label(text='Validate your web3 License')
    row = box.row()
    row.label(text='Wallet address')
    row.prop(addon_prefs, 'userID', text='')
    row = box.row()
    row.label(text='License Key')
    if error !='':
        row.alert = True
    row.prop(addon_prefs, 'premium_licensekey', text='' )
    row = box.row()
    row.operator('bu.validate_license', text='Validate Premium License')    

class Upload_settings_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_UPLOAD_SETTINGS_PANEL"
    bl_label = 'Blender Pro Suite Upload Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_PREMIUM_SETTINGS_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self,context):
        layout = self.layout
        box = layout.box()
        addon_prefs = get_addon_name().preferences
        box.prop(addon_prefs, 'thumb_upload_path', text='Thumbs Upload Path')
        box.prop(addon_prefs, 'author', text='Author')


class Premium_validation_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_PREMIUM_VALIDATION_PANEL"
    bl_label = 'Blender Pro Suite Premium Validation'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_PREMIUM_SETTINGS_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    addon_name = get_addon_name()

    bpy.types.Scene.validation_error_message = bpy.props.StringProperty()
    bpy.types.Scene.validation_message = bpy.props.StringProperty()
    bpy.types.Scene.validation_message = "Please validate your license"
    bpy.types.Scene.validation_error_message = ''

    def draw(self,context):
        layout = self.layout
        box = layout.box()
        addon_prefs = get_addon_name().preferences
        status = bpy.types.Scene.validation_message
        error = bpy.types.Scene.validation_error_message
        row = box.row()
        row.label(text='Premium Verification settings')
        row = box.row()
        row = box.row()

        if error == 'You have a Free Core license': 
            row.label(text=error)
            row = box.row()
            row.label(text='If you want to use premium features, please upgrade your license.')
            row = box.row()
            upgrade_license = row.operator('wm.url_open',text='Upgrade License',icon='UNLOCKED')
            upgrade_license.url = 'https://bakeduniverse.gumroad.com/l/bbps'
        else:
            row.label(text=status)
            row.label(text=error)
        row = box.row()
        row = box.row()
        row.prop(addon_prefs, 'web3_gumroad_switch', expand=True)
        row = box.row()
        box = row.box()
        if addon_prefs.web3_gumroad_switch == 'premium_gumroad_license':
            gumroad_register(self,context, status, error,box)
        elif addon_prefs.web3_gumroad_switch == 'premium_web3_license':
            web3_premium_validation(self,context, status, error,box)

class Premium_Settings_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_PREMIUM_SETTINGS_PANEL"
    bl_label = 'Blender Pro Suite Premium Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_Premium"



    def draw (self, context):
        layout = self.layout

        


classes = (
    Premium_Settings_Panel,
    Validate_Options,
    Validate_Premium_License,
    Validate_Gumroad_License,
    Premium_validation_Panel,
    Upload_settings_Panel,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)