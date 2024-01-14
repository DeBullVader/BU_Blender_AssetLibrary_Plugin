import bpy
from ..dependencies import import_dependencies
import subprocess
from .. import operators
from . import statusbar
from .. import addon_updater_ops
from ..utils.addon_info import get_addon_name
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from .bu_main_panels import BBPS_Info_Panel,BBPS_Main_Addon_Panel
from .asset_mark_setup import BU_PT_MarkTool_settings
from .bu_main_panels import BU_PT_AssetBrowser_settings
from bpy.props import (
    BoolProperty,
    StringProperty,
    EnumProperty,
    FloatProperty,
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

    experimental: BoolProperty(
        name="Experimental Functions toggle",
        description="Enable Experimental Functions",
        default=False,
    )

    # filepath = bpy.props.StringProperty(subtype='DIR_PATH')
    bsc_wallet_address: StringProperty(
        name="BSC Wallet address",
        description="Input wallet",
        default="",
    )

    lib_path: StringProperty(
        name = "AssetLibrary directory",
        description = "Choose a directory to setup the Asset Library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
        
    )

    
    new_lib_path: StringProperty(
        name = "New AssetLibrary directory",
        description = "Choose a new directory for the asset library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
    )

    thumb_upload_path: StringProperty(
        name = "Path to thumbs upload folder",
        description = "Choose a new directory for the asset library",
        maxlen = 1024,
        subtype = 'DIR_PATH',   
    )

    remove_deprecated_assets: BoolProperty(
        name="Remove deprecated assets",
        description="Remove deprecated assets from the library on sync, false will store them in BU_AssetLibrary_deprecated",
        default=False,
    )

    automaticly_update_original_assets: BoolProperty(
        name="Automaticly update original assets on sync",
        description="Automaticly update (re-download) original assets when syncing assets",
        default=False,
    )

    author: StringProperty(
        name = "Author",
        description = "Author of the asset",
        maxlen = 1024,
        default='',
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

    accessToken: StringProperty(
        name = "accesToken",
        description = "Acces token for the service",
        maxlen = 1024,
    )

    accessToken_timestamp: FloatProperty(
        name = "accessToken_timestamp",
        description = "Timestamp for the accesToken",
        default=0.0
    )

    premium_licensekey: StringProperty(
        name = "Premium License Key",
        description = "Input for the premium license key",
        maxlen = 1024,
        
    )
    userID: StringProperty(
        name="User ID",
        description="Input either Web3 wallet address or gumroad license key",
        maxlen = 1024,

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
        
        
        
    )
    stored_gumroad_premium_licensekey: StringProperty(
        name = "Gumroad Premium License Key",
        description = "Input for the Gumroad premium license key",
        maxlen = 1024,
        
    )
    payed: BoolProperty(
        name="Payed License",
        description="If the license is a payed license",
        default=False,
    )
    youtube_latest_vid_url: StringProperty(
        name = "Latest Video Title",
        description = "Our latest tutorial title",
        maxlen = 1024,
          
    )
    youtube_latest_vid_title: StringProperty(
        name = "Latest Video Title",
        description = "Our latest tutorial title",
        maxlen = 1024,   
    )

    toggle_info_panel: BoolProperty(
        name="Toggle Info Panel",
        description="Toggle Info Panel",
        default=False,
    )

    toggle_addon_updater: BoolProperty(
        name="Toggle Addon Updater",
        description="Toggle Addon Updater",
        default=False,
    )

    toggle_asset_browser_settings: BoolProperty(
        name="Toggle BU Asset Browser settings",
        description="Toggle BU Asset Browser settings",
        default=False,
    )
    # EXPERIMENTAL FEATURES -----------------------------------------------
    # toggle_experimental_BU_Premium_panels: BoolProperty(
    #     name="Toggle Experimental Premium",
    #     description="Toggle Experimental Premium",
    #     default=False,

    # )
    toggle_experimental_BU_Render_Previews: BoolProperty(
        name="Toggle Experimental Render",
        description="Toggle Experimental Render",
        default=True,
    )
    # EXPERIMENTAL FEATURES END -----------------------------------------------
    def draw(self,context):
        layout = self.layout
        
        layout.label(text='Addon Settings')
        
        BBPS_Main_Addon_Panel.draw(self,context)
        layout.prop(self, 'toggle_info_panel', text='Blender Universe Links',toggle=True,icon='URL')
        if self.toggle_info_panel:
            BBPS_Info_Panel.draw(self,context)
        gitbook = layout.operator('wm.url_open',text='Documentation',icon='HELP')
        gitbook.url= 'https://bakeduniverse.gitbook.io/baked-blender-pro-suite/introduction/welcome-to-baked-blender-pro-suite'
        layout.prop(self, 'toggle_addon_updater', text='Addon Updater',toggle=True,icon='FILE_BACKUP') 
        if self.toggle_addon_updater:
            addon_updater_ops.update_settings_ui(self,context)
        layout.prop(self, 'toggle_asset_browser_settings', text='Asset Browser Settings',toggle=True,icon='TOOL_SETTINGS')
        if self.toggle_asset_browser_settings:
            BU_PT_AssetBrowser_settings.draw(self,context)
        layout.prop(self, 'experimental', text='Experimental Features',toggle=True,icon='EXPERIMENTAL')
        if self.experimental:
            row = layout.row()
            row.alert = True
            row.label(text='Use at own risk!')

            box = layout.box()
            row = box.row(align=True)
            row.label(text='Open folder where addon is installed: ')
            row.operator('bu.open_addon_location',text='Open Addon Location',icon='FILE_FOLDER')
            row = box.row(align=True)
            # row.alignment = 'LEFT'
            row.label(text='Premium Main Panel: ')
            row.prop(self, 'toggle_experimental_BU_Premium_panels', text='Premium Panels',toggle=True)
            




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
    
    
    
    
    


    
    
    
