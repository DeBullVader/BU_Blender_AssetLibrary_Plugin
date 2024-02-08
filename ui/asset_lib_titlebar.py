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
        self.layout.label(text='|')
        addon_info.gitbook_link_getting_started(self.layout,'upload-assets-to-server','')
        i = icons.get_icons()
        if addon_prefs.debug_mode == True:
            scene = context.scene
            self.layout.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
            self.layout.label(text='|')
        #Check if we are in current file in the asset browser
        
        if addon_prefs.thumb_upload_path == '':
            
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
    addon_info.gitbook_link_getting_started(self.layout,'how-to-use-the-asset-browser/sync-and-downloading-assets','')
    amount = len(context.scene.assets_to_update)
    amount_premium = len(context.scene.premium_assets_to_update)
    if addon_info.is_lib_premium():
        if context.scene.premium_assets_to_update:
            self.layout.operator('bu.assets_to_update', text=f'({amount_premium}) Premium Asset Updates', icon='MONKEY')
    else:
        if context.scene.assets_to_update:
            self.layout.operator('bu.assets_to_update', text=f'({amount}) Asset Updates', icon='MONKEY')

        
    if addon_info.is_lib_premium():
        if sync_manager.SyncManager.is_sync_operator('bu.sync_premium_assets'):
            self.layout.operator('bu.sync_premium_assets', text='Cancel Sync', icon='CANCEL')
        else:
            self.layout.operator('bu.sync_premium_assets', text='Sync Premium Assets', icon='URL')
    else:
        if sync_manager.SyncManager.is_sync_operator('bu.sync_assets'):
            self.layout.operator('bu.sync_assets', text='Cancel Sync', icon='CANCEL')
        else:
            self.layout.operator('bu.sync_assets', text='Sync Assets', icon='URL')
    
    if sync_manager.SyncManager.is_sync_operator('bu.download_original_asset'):
        self.layout.operator('bu.download_original_asset', text='Cancel Sync', icon='CANCEL')
    else:
        self.layout.operator('bu.download_original_asset', text='Download Asset(s)', icon='URL')
    
    
    statusbar.draw_progress(self,context)


        

