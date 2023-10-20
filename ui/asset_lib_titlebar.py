from . import statusbar
from .. import icons
from ..utils import addon_info 



def draw_menu(self, context):
    addon_prefs = addon_info.get_addon_name().preferences
    #Check if we are in current file in the asset browser
    current_library_name = context.area.spaces.active.params.asset_library_ref
    if current_library_name == "BU_AssetLibrary_Core":
        draw_download_asset(self,context)
        # statusbar.draw_progress(self,context)
        # statusbar.ui_titlebar(self,context)
        # addon_prefs.download_folder_id = addon_prefs.bl_rna.properties['download_folder_id'].default
        # addon_prefs.download_folder_id_placeholders = addon_prefs.bl_rna.properties['download_folder_id_placeholders'].default
    #TODO:move to unlock later
    if current_library_name == "BU_AssetLibrary_Premium":
        draw_download_asset(self,context)
        # statusbar.draw_progress(self,context)
        # addon_prefs.download_folder_id = '1ggG-7BifR4yPS5lAfDJ0aukfX6J02eLk'
        # addon_prefs.download_folder_id_placeholders = '1FU-do5DYHVMpDO925v4tOaBPiWWCNP_9'

    if current_library_name == 'LOCAL':
        i = icons.get_icons()
        #Check if we are in current file in the asset browser
        self.layout.operator('wm.save_files', icon_value=i["bakeduniverse"].icon_id)
        statusbar.ui_titlebar_upload(self,context)

def draw_download_asset(self, context):
    self.layout.operator('wm.sync_assets', text='Sync Assets', icon='URL')
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
    
def upload_assets (self, context):
    if context.space_data.params.asset_library_ref != "BU_AssetLibrary_Core":
        return
    pass

def asset_browser_titlebar(self, context):
        update_library(self, context)
        

