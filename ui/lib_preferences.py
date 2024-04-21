import bpy

from . import statusbar
from .. import addon_updater_ops
from ..utils import addon_info
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from .bu_main_panels import BBPS_Info_Panel,BBPS_Main_Addon_Panel,BU_PT_Docs_Panel
from .bu_main_panels import BU_PT_AddonSettings
from ..premium.premium_ui import Premium_Main_Panel,Premium_validation_Panel
from ..import icons
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

    web3_gumroad_switch:EnumProperty(
        name = 'validation_preference',
        description = "verify web3 or gumroad license for premium",
        items=[
            ('premium_gumroad_license', 'Gumroad', '', '', 0),
            ('premium_web3_license', 'Web3', '', '', 1)
        ],
        default='premium_gumroad_license'
    )  

    license_type: StringProperty(
        name = "License Type",
        description = "Type of premium license",
        maxlen = 1024, 
        options={'HIDDEN'}, 
    )

    user_id: StringProperty(
        name="User ID",
        description="user ID",
        maxlen = 1024,
        options={'HIDDEN'},
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
    toggle_premium_panel: BoolProperty(
        name="Toggle Premium Panel",
        description="Toggle Premium Panel",
        default=False,
    )

    toggle_documentation_panel: BoolProperty(
        name="Toggle Documentation Panel",
        description="Toggle Documentation Panel",
        default=False,
    )

    toggle_addon_updater: BoolProperty(
        name="Toggle Addon Updater",
        description="Toggle Addon Updater",
        default=False,
    )

    toggle_all_addon_settings: BoolProperty(
        name="Toggle BU Asset Browser settings",
        description="Toggle BU Asset Browser settings",
        default=False,
    )

    toggle_experimental_BU_Render_Previews: BoolProperty(
        name="Toggle Experimental Render",
        description="Toggle Experimental Render",
        default=True,
    )

    addon_pref_tabs: EnumProperty(
        name = 'addon tabs',
        description = "Switch between addon tabs",
        default='toggle_premium_panel',
        items = [
            ('toggle_premium_panel', 'Premium', '', 'ASSET_MANAGER', 0),
            ('toggle_documentation_panel', 'Documentation & Quick Start', '', 'HELP', 1),
            ('toggle_addon_updater', 'Addon Updater', '', 'FILE_BACKUP', 2),
            ('toggle_all_addon_settings', 'Addon Settings', '', 'TOOL_SETTINGS', 3)
        ]
    )

    def draw(self,context):
        layout = self.layout
        
        layout.label(text='Addon Settings')
        BBPS_Main_Addon_Panel.draw(self,context)

        BBPS_Info_Panel.draw(self,context)
        layout.separator(factor = 1)
        row = layout.row()
        row.prop(self,'addon_pref_tabs',text='Addon Tabs',expand=True)
        if self.addon_pref_tabs == 'toggle_premium_panel':
            Premium_Main_Panel.draw(self,context)
            # layout.separator(factor = 1)
            Premium_validation_Panel.draw(self,context)

        if self.addon_pref_tabs == 'toggle_documentation_panel':
            BU_PT_Docs_Panel.draw(self,context)
        
        if self.addon_pref_tabs == 'toggle_addon_updater':
            addon_updater_ops.update_settings_ui(self,context)

        if self.addon_pref_tabs == 'toggle_all_addon_settings':
            box = layout.box()
            row = box.row(align=True)
            row.alignment = 'CENTER'
            col = row.column()
            col.alignment = 'CENTER'
            col.label(text="Our addon has a panel in the 3D viewport side panel")
            col.label(text="Click the button below to open the 3D viewport panel")
            col.label(text="Then navigate to the 'Blender Universe Kit' panel")
            
            col.operator('bu.open_n_panel', text = 'Open Viewport panels', icon = 'VIEWZOOM')
            row = box.row()
            row.alignment = 'CENTER'
            row.label(text ="Or in the settings panel below")
            BU_PT_AddonSettings.addon_settings(self,context)
        layout.separator(factor = 2)
            
            




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
            row_upload.label(text=f'Author: {str(addon_info.get_addon_prefs.author)}')
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
    
    
    
    
    


    
    
    
