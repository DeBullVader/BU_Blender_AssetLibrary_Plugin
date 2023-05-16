import bpy
from ..dependencies import import_dependencies
import subprocess
from .. import operators
from . import statusbar
from ..utils.addon_info import get_addon_name
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from .. import addon_updater_ops
from bpy.props import (
    StringProperty,
    EnumProperty,
)


# def get_statustext(self):
#     return self

# def set_statustext(self, value):
#     self = value

# def get_buttontext(self):
#     return self

# def set_buttontext(self, value):
#     self = value



@addon_updater_ops.make_annotations
class BUPrefLib(AddonPreferences):
    bl_idname = __package__

 
    # filepath = bpy.props.StringProperty(subtype='DIR_PATH')
    bsc_wallet_address: StringProperty(
        name="BSC Wallet address",
        description="Input wallet",
        default="",

        # 0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2
    )
    # 0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2

    lib_path : StringProperty(
        name = "AssetLibrary directory",
        description = "Choose a directory to setup the Asset Library",
        maxlen = 1024,
        subtype = 'DIR_PATH'
    )

    automatic_or_manual:EnumProperty(
        name = 'Download preference',
        description = "Choose if you like to download the library automaticly or manualy",
        items=[
            ('automatic_download', 'Automatic', '', '', 0),
            ('manual_download', 'Manual', '', '', 1)
        ],
        default='automatic_download'
    ) 

    auto_check_update = bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

    updater_interval_months = bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

    updater_interval_days = bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

    updater_interval_hours = bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

    updater_interval_minutes = bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)

    
    def draw(self,context):
        if not import_dependencies.dependencies_installed:
            dep_preferences(self, context)
        else:
            layout = self.layout
            wallet_input(self,context)
            layout.separator(factor=1)
            prefs_lib_reminder(self, context)
            layout.separator(factor=1)
            library_download_settings(self,  context)
            layout.separator(factor=1)



def dep_preferences(self, context):
    layout = self.layout
    layout.operator('wm.install_dependencies',text="Install Dependencies", icon="CONSOLE")

def disable_Input(self,context):
    
    if bpy.types.AddonPreferences.walletbutton == "Succes!":
        return False
    else:
        return True


def wallet_input(self, context):

    layout = self.layout
    row = layout.row(align = True)
    row.label(text='Verification settings')
    row.alignment = 'CENTER'
    box = layout.box()
    box.label (text = bpy.types.AddonPreferences.walletstatus)
    row = box.row()
    row.prop(self, 'bsc_wallet_address')
    row.enabled = disable_Input(self, context)
    row = box.row()
    row.operator('bu.verify', text = bpy.types.AddonPreferences.walletbutton)

def bu_asset_lib(self, context):
    layout = self.layout
    row = layout.row(align = True)
    row.label(text="Library file path setting")
    row.alignment = 'CENTER'
    box = layout.box()
    box.prop(self,"lib_path")
    row = box.row()
    row.operator('bu.addlibrary', text = 'Add asset library directory')
    # row.enabled = enable_state


def prefs_lib_reminder(self,context):
    
    def draw_warning(self,text):
        row = self.layout.row(align=True)
        if bpy.context.preferences.active_section == "ADDONS":
            row.alignment = "LEFT"
        else:
            row.alignment = "RIGHT"
        row.label(text=text, icon='ERROR')

    if bpy.context.preferences.active_section == "ADDONS":
        for lib in bpy.context.preferences.filepaths.asset_libraries:
            if lib.name == "BU_AssetLibrary_Core":
                    layout = self.layout
                    # bu_asset_lib(self, context)
                    row = layout.row()
                    row.label(text="Asset library location: " + lib.path, icon="CHECKMARK")
                    BUPrefLib.lib_path = lib.path
                    return
            # else:
            #     text = 'No asset library named "BU_AssetLibrary_Core", Please choose a directory above'
            #     bu_asset_lib(self, context, True)
            #     row = self.layout.row(align=True)
            #     row.label(text=text, icon='ERROR')

    if context.preferences.active_section == "ADDONS":
        bu_asset_lib(self, context)
        draw_warning(
            self,
            'No asset library named "BU_AssetLibrary_Core", Please choose a directory above',
        )
          

            
         

    # if bpy.context.preferences.active_section == "ADDONS":
    #     # add_library_layout(self, context, True)
        
    # else:
    #     draw_warning(self, 'BU_AssetLibrary_Core: No asset library named "BU_AssetLibrary_Core", please create it!')           

def library_download_settings(self, context):
    #lib_download_pref = get_addon_name().preferences.automatic_or_manual
    layout = self.layout
    row = self.layout.row(align = True)
    row.label(text='Library download settings')
    row.alignment = 'CENTER'
    box = layout.box()
    row = box.row()
    # row.prop(self, 'automatic_or_manual')
    # box.label(text='Confirm below to download the asset library')
    box.label(text='Download the current available Baked Universe asset library')
    box.alignment= 'CENTER'
    row = box.row()
    row.operator('wm.downloadall', text = 'Download Asset Library')
    statusbar.ui(self,context)
    addon_updater_ops.update_settings_ui(self,context)
    
    
    
    


    
    
    
