import bpy
from ..dependencies import import_dependencies
import subprocess
from .. import operators
from . import statusbar
from .. import addon_updater_ops
from ..utils.addon_info import get_addon_name
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

    lib_path: StringProperty(
        name = "AssetLibrary directory",
        description = "Choose a directory to setup the Asset Library",
        maxlen = 1024,
        subtype = 'DIR_PATH'
    )
    new_lib_path: StringProperty(
        name = "New AssetLibrary directory",
        description = "Choose a new directory for the asset library",
        maxlen = 1024,
        subtype = 'DIR_PATH'
    )

    author: StringProperty(
        name = "Author",
        description = "Author of the asset",
        maxlen = 1024,
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
        layout = self.layout
        addon_updater_ops.update_settings_ui(self,context)
        layout.separator(factor=0.2)
        prefs_lib_reminder(self, context)
        layout.separator(factor=0.2)
        wallet_input(self,context)
        layout.separator(factor=0.2)
       


        # if not import_dependencies.dependencies_installed:
        #     dep_preferences(self, context)
        # else:
        #     layout = self.layout
        #     wallet_input(self,context)
        #     layout.separator(factor=1)
        #     prefs_lib_reminder(self, context)
        #     layout.separator(factor=1)
        #     library_download_settings(self,  context)
        #     layout.separator(factor=1)



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
    boxmain = layout.box()
    row = boxmain.row()
    row.label(text='Verification settings')
    row = boxmain.row()
    row.label(text='This section is a testcase for web3 integration.')
    row = boxmain.row()
    row.label (text = bpy.types.AddonPreferences.walletstatus)
    row = boxmain.row()
    row.prop(self, 'bsc_wallet_address')
    # row.enabled = disable_Input(self, context)
    row = boxmain.row()
    row.operator('bu.verify', text = bpy.types.AddonPreferences.walletbutton)

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
           
            row_upload.label(text=get_addon_name().preferences.author)
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
            # row.alignment = 'LEFT'
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
    #lib_download_pref = get_addon_name().preferences.automatic_or_manual
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
    
    
    
    
    


    
    
    
