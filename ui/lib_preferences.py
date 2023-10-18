import bpy
from ..dependencies import import_dependencies
import subprocess
from .. import operators
from . import statusbar
from .. import addon_updater_ops
from ..utils.addon_info import get_addon_name
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup

from bpy.props import (
    BoolProperty,
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

    
    is_admin: BoolProperty(
        name="Admin mode",
        description="Enable admin mode",
        default=False,
    )
    # filepath = bpy.props.StringProperty(subtype='DIR_PATH')
    bsc_wallet_address: StringProperty(
        name="BSC Wallet address",
        description="Input wallet",
        default="",

        # 0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2
    )

    lib_path: StringProperty(
        name = "AssetLibrary directory",
        description = "Choose a directory to setup the Asset Library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
        # default='C:\\Users\Lenovo\\Documents\\BBPS_core_lib',
    )

    
    new_lib_path: StringProperty(
        name = "New AssetLibrary directory",
        description = "Choose a new directory for the asset library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
    )

    author: StringProperty(
        name = "Author",
        description = "Author of the asset",
        maxlen = 1024,
        default='DEV',
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

    premium_licensekey: StringProperty(
        name = "Premium License Key",
        description = "Input for the premium license key",
        maxlen = 1024,
        # default='09ae0726-64df-40f2-87b2-e1f68144e95f'
    )
    userID: StringProperty(
        name="User ID",
        description="Input either Web3 wallet address or gumroad license key",
        maxlen = 1024,
        # default="0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2",
        

        # 0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2
    )

    web3_gumroad_switch:EnumProperty(
        name = 'validation_preference',
        description = "verify web3 or gumroad license for premium",
        items=[
            ('premium_gumroad_license', 'Gumroad', '', '', 0),
            ('premium_web3_license', 'Web3', '', '', 1)
        ],
        default='premium_gumroad_license'
    )  

    gumroad_premium_licensekey: StringProperty(
        name = "Gumroad Premium License Key",
        description = "Input for the Gumroad premium license key",
        maxlen = 1024,
        # default='2BF55F25-4A114A22-A73C745A-7BF010A1'
    )


    def draw(self,context):
        layout = self.layout
        addon_updater_ops.update_settings_ui(self,context)
        layout.separator(factor=0.2)
        wallet_input(self,context)
        layout.separator(factor=0.2)
        prefs_lib_reminder(self, context)
        layout.separator(factor=0.2)



def dep_preferences(self, context):
    layout = self.layout
    layout.operator('wm.install_dependencies',text="Install Dependencies", icon="CONSOLE")



def wallet_input(self, context):
    layout = self.layout
    boxmain = layout.box()
    row = boxmain.row()
    row.label(text='Premium Verification settings')
    row = boxmain.row()
    row.label(text='Please insert your license key below')
    row= boxmain.row()
    row.label(text='User ID')
    row.prop(self, 'bsc_wallet_address', text='')
    row = boxmain.row()
    row.label(text='Premium License Key')
    row.prop(self, 'premium_licensekey', text='')
    row = boxmain.row()
    row.operator('bu.validate_license', text='Validate Premium License')

def add_bu_asset_lib(self, context):
    layout = self.layout

    # row.enabled = enable_state

def change_or_remove_asset_lib(self):
    layout = self.layout



def prefs_lib_reminder(self,context):
    
    def draw_warning(self,text):
        row = self.layout.row(align=True)
        if bpy.context.preferences.active_section == "ADDONS":
            row.alignment = "LEFT"
        else:
            row.alignment = "RIGHT"
        row.label(text=text, icon='ERROR')

    if bpy.context.preferences.active_section == "ADDONS":
        if 'BU_AssetLibrary_Core' in bpy.context.preferences.filepaths.asset_libraries:
            lib_index = bpy.context.preferences.filepaths.asset_libraries.find("BU_AssetLibrary_Core")   
            lib = bpy.context.preferences.filepaths.asset_libraries[lib_index]
            layout = self.layout
            box_main = layout.box()
            row_upload = box_main.row()
            row_upload.label(text="Asset Upload Settings")
            row_upload = box_main.row()
            row_upload.label(text=f'Author: {str(get_addon_name().preferences.author)}')
            row_upload = box_main.row()
            box = row_upload.box()
            split = box.split()
            row = split.row(align=True)
            row.label(text="Set Author")
            row = split.row()
            row.prop(self,'author', text='')
            row = split.row()
            row.operator('bu.confirmsetting', text = 'save')

            row = box_main.row()
            row.label(text="Library file path setting") 
            row_loc_and_rem = box_main.row()
            box = row_loc_and_rem.box()
            row=box.row()
            row.label(text="Current Asset library location: ")  
            row=box.row()
            split = row.split(factor =0.6)
            col = split.column()
            col.label(text=lib.path)
            col = split.column()
            col.operator('bu.removelibrary', text = 'Remove Library')
            BUPrefLib.lib_path = lib.path
            row_tooltip = box_main.row()
            box = row_tooltip.box()
            row = box.row()
            row.label(text="How to download the library!!")
            row = box.row()
            row.label(text="To download the library open the asset browser and click Check for new assets")
            row = box.row()
            row.label(text="Then press update library to initiate the download process")
            row_change=box_main.row()
            box = row_change.box()
            row=box.row()
            row.label(text="Change to a new Library directory")
            row=box.row()
            split = row.split(factor= 0.6)
            col = split.column()
            col.prop(self,"new_lib_path", text ='')
            col = split.column()
            col.operator('bu.changelibrarypath', text = 'Change library directory')

            return


        if context.preferences.active_section == "ADDONS":
            layout = self.layout
            row = layout.row(align = True)
            row.label(text="BU Asset Library Settings")
            row.alignment = 'CENTER'
            box = layout.box()
            box.prop(self,"lib_path")
            row = box.row()
            row.label(text="Library Location")
            row = box.row()
            row.operator('bu.addlibrarypath', text = 'Add asset library directory')
            draw_warning(
                self,
                'No asset library named "BU_AssetLibrary_Core", Please choose a directory above',
            )
   
          
def download_lib_tooltip(self):
    layout = self.layout
    box_main = layout.box()
    row = box_main.row(align = True)
    row.label(text='Download Library')
    row.alignment = 'CENTER'


            

def library_download_settings(self, context):
    layout = self.layout
    row = self.layout.row(align = True)
    row.label(text='Library download settings')
    row.alignment = 'CENTER'
    box = layout.box()
    row = box.row()
    box.label(text='Download the current available Baked Universe asset library')
    box.alignment= 'CENTER'
    row = box.row()
    row.operator('wm.downloadall', text = 'Download Asset Library')
    statusbar.ui(self,context)
    
    
    
    
    


    
    
    
