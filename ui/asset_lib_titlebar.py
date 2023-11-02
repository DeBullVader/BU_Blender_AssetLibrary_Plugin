from . import statusbar
from .. import icons
from ..utils import addon_info 



def draw_menu(self, context):
    lib_names=(
        "BU_AssetLibrary_Core",
        "TEST_BU_AssetLibrary_Core",
        "BU_AssetLibrary_Premium",
        "TEST_BU_AssetLibrary_Premium"
    )
    addon_prefs = addon_info.get_addon_name().preferences
    #Check if we are in current file in the asset browser
    current_library_name = context.area.spaces.active.params.asset_library_ref
    for lib_name in lib_names:
        if current_library_name == lib_name:
            draw_download_asset(self,context)
    if current_library_name == 'LOCAL':
        i = icons.get_icons()
        #Check if we are in current file in the asset browser
        self.layout.operator('bu.upload_settings', text='^', icon ='SETTINGS')
        self.layout.operator('wm.save_files', icon_value=i["bakeduniverse"].icon_id)
        self.layout.operator('bu.cancel_sync', text='cancel_sync', icon='URL')
        statusbar.draw_progress(self,context)

def draw_download_asset(self, context):
    if not context.selected_asset_files:
        self.layout.operator('wm.sync_assets', text='Sync placeholders', icon='URL')
        
    else:
        self.layout.operator('bu.download_original_asset', text='Download Original', icon='URL')
    self.layout.operator('bu.cancel_sync', text='cancel_sync', icon='URL')
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
        

