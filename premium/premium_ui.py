import bpy
import textwrap
from ..utils.addon_info import get_addon_prefs,gitbook_link_getting_started
from . import premium_logic
from ..import icons


class Premium_Assets_Preview(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Premium_Assets_Preview"
    bl_label = 'Premium assets previews'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UniBlend'
    bl_parent_id = "VIEW3D_PT_BU_Premium"
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='Previews will be shown here')


class Premium_validation_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_PREMIUM_VALIDATION_PANEL"
    bl_label = 'Premium License Validation'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_Premium"
    bl_options = {'DEFAULT_CLOSED'}
    

    bpy.types.Scene.validation_error_message = bpy.props.StringProperty()
    bpy.types.Scene.validation_message = bpy.props.StringProperty()
    bpy.types.Scene.validation_message = "Please validate your license"
    bpy.types.Scene.validation_error_message = ''

    def draw(self,context):
        layout = self.layout
        box = layout.box()
        addon_prefs = get_addon_prefs()
        status = bpy.types.Scene.validation_message
        error = bpy.types.Scene.validation_error_message
        row = box.row()
        row.prop(addon_prefs, 'web3_gumroad_switch', expand=True)
        row = box.row()
        if addon_prefs.web3_gumroad_switch == 'premium_gumroad_license':
            premium_logic.gumroad_register(self,context, status, error,box)
        if addon_prefs.web3_gumroad_switch == 'premium_web3_license':
            premium_logic.web3_premium_validation(self,context, status, error,box)

class Premium_Settings_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_PREMIUM_SETTINGS_PANEL"
    bl_label = 'Premium Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_Premium"

    def draw (self, context):
        layout = self.layout

    
class Premium_Main_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Premium"
    bl_label = 'UniBlend Premium'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UniBlend'
    bl_options = {'DEFAULT_CLOSED'}

    
    def draw(self,context):
        i = icons.get_icons()
        factor=0.6
        self.layout.alignment = 'EXPAND'
        col = self.layout.column(align=True)
        split = col.split(factor=factor, align=True)
        split.alignment = 'EXPAND'
        box = split.box()
        box.label(text='Purchase a Premium License at:')
        box = split.box()
        upgrade_license = box.operator('wm.url_open',text='Gumroad License',icon='UNLOCKED')
        upgrade_license.url = 'https://bakeduniverse.gumroad.com/l/bbps'

        split = col.split(factor=factor, align=True)
        box = split.box()
        box.label(text='Get Premium via Baked Universe NFTS at:')
        box = split.box()
        bu_site = box.operator('wm.url_open',text='Web3 License',icon_value=i["bakeduniverse"].icon_id)
        bu_site.url = 'https://comic.bakeduniverse.com'

        split = col.split(factor=factor, align=True)
        box = split.box()
        box.label(text='Find more information about premium at:')
        box = split.box()
        gitbook_link_getting_started(box,'Premium','Premium')


classes =(
    Premium_Main_Panel,
    # Premium_Settings_Panel,
    Premium_validation_Panel,
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
       
