from . import statusbar
from .. import icons
from ..utils import addon_info,sync_manager,version_handler



def draw_menu(self, context):
    # if context.workspace.name == 'Layout':
    lib_names=(
        "BU_AssetLibrary_Core",
        "TEST_BU_AssetLibrary_Core",
        "BU_AssetLibrary_Premium",
        "TEST_BU_AssetLibrary_Premium"
    )
    
    addon_prefs = addon_info.get_addon_name().preferences
    current_library_name = version_handler.get_asset_library_reference(context)
    # for lib_name in lib_names:
    if current_library_name in lib_names:
        draw_download_asset(self,context)
    if current_library_name == 'LOCAL':
        i = icons.get_icons()
        if addon_prefs.debug_mode == True:
            scene = context.scene
            self.layout.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
            self.layout.label(text='|')
        #Check if we are in current file in the asset browser
        
        if addon_prefs.thumb_upload_path == '':
            self.layout.label(text='  |  ')
            self.layout.alert = True
            self.layout.operator('bu.upload_settings', text='Settings', icon ='SETTINGS')
        self.layout.alert = False
        text = 'Sync assets to BU server' if addon_prefs.debug_mode == False else 'Sync assets to BU Test server'
        self.layout.operator('wm.save_files', text=text,icon_value=i["BU_logo_v2"].icon_id) 
        statusbar.draw_progress(self,context)
    if current_library_name =='BU_AssetLibrary_Deprecated':
        self.layout.operator("bu.remove_library_asset", text='Remove selected library asset', icon='TRASH')

def draw_download_asset(self, context):
    # if context.workspace.name == 'Layout':
    amount = len(context.scene.assets_to_update)
    amount_premium = int(len(context.scene.premium_assets_to_update)/2)
    if addon_info.is_lib_premium():
        if amount_premium>0:
            self.layout.operator('bu.assets_to_update', text=f'({amount_premium}) Premium Asset Updates', icon='MONKEY')
    else:
        if amount>0:
            self.layout.operator('bu.assets_to_update', text=f'({amount}) Asset Updates', icon='MONKEY')

        
    if addon_info.is_lib_premium():
        if sync_manager.SyncManager.is_sync_operator('bu.sync_premium_assets'):
            self.layout.operator('bu.sync_premium_assets', text='Cancel Sync', icon='CANCEL')
        else:
            self.layout.operator('bu.sync_premium_assets', text='Sync Premium Previews', icon='URL')
    else:
        if sync_manager.SyncManager.is_sync_operator('wm.sync_assets'):
            self.layout.operator('wm.sync_assets', text='Cancel Sync', icon='CANCEL')
        else:
            self.layout.operator('wm.sync_assets', text='Sync Core Previews', icon='URL')
    
    if sync_manager.SyncManager.is_sync_operator('bu.download_original_asset'):
        self.layout.operator('bu.download_original_asset', text='Cancel Sync', icon='CANCEL')
    else:
        self.layout.operator('bu.download_original_asset', text='Download Original', icon='URL')
    
    # self.layout.operator('bu.cancel_sync', text='cancel_sync', icon='URL')
    statusbar.draw_progress(self,context)


def update_library(self, context):
    i = icons.get_icons()
    layout = self.layout
    layout.scale_y = 1.2
    box = layout.box()
    row = box.row(align=True)
    row.use_property_split = True
    props = context.window_manager.bu_props
    if props.new_assets > 0:
        row.operator('wm.downloadall', text = ('Update Library'),  icon_value=i["bakeduniverse"].icon_id)
    elif props.updated_assets >0: 
        row.operator('wm.downloadall', text = ('Update Library'),  icon_value=i["bakeduniverse"].icon_id)
    else:
        row.operator('wm.checklibupdate', text = ('Check for new assets'),  icon_value=i["bakeduniverse"].icon_id) 
    

def asset_browser_titlebar(self, context):
    update_library(self, context)
        

