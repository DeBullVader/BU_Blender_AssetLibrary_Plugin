import bpy
from .. import bu_dependencies
import subprocess
from .. import operators
from . import statusbar
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
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
    
    def draw(self,context):
        if not bu_dependencies.dependencies_installed:
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
    layout.operator(operators.BU_OT_install_dependencies.bl_idname, icon="CONSOLE")

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

def bu_asset_lib(self, context, enable_state):
    layout = self.layout
    row = layout.row(align = True)
    row.label(text="Library file path setting")
    row.alignment = 'CENTER'
    box = layout.box()
    box.prop(self,"lib_path")
    row = box.row()
    row.operator('bu.addlibrary', text = 'add library')
    row.enabled = enable_state


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
                    bu_asset_lib(self, context, False)
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
        bu_asset_lib(self, context, True)
        draw_warning(
            self,
            'No asset library named "BU_AssetLibrary_Core", Please choose a directory above',
        )
          

            
         

    # if bpy.context.preferences.active_section == "ADDONS":
    #     # add_library_layout(self, context, True)
        
    # else:
    #     draw_warning(self, 'BU_AssetLibrary_Core: No asset library named "BU_AssetLibrary_Core", please create it!')           

def library_download_settings(self, context):
    props = context.window_manager.bu_props
    lib_download_pref = bpy.context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.automatic_or_manual
    layout = self.layout
    row = self.layout.row(align = True)
    row.label(text='Library download settings')
    row.alignment = 'CENTER'
    box = layout.box()
    row = box.row()
    row.prop(self, 'automatic_or_manual')
    box.label(text='Confirm below to download the asset library')
    box.alignment= 'CENTER'
    row = box.row()
    row.operator('wm.downloadall', text = 'Confirm Download Setting')
    statusbar.ui(self,context)
    
    
    


    
    
    
