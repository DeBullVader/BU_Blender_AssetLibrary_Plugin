import bpy
from . import statusbar
from .. import icons
from ..utils import addon_info 

# 
# 


def draw_menu(self, context):
    #Check if we are in current file in the asset browser
    current_library_name = context.area.spaces.active.params.asset_library_ref
    if current_library_name == "BU_AssetLibrary_Core":
        update_library(self,context)
        statusbar.ui_titlebar(self,context)
    if current_library_name == 'LOCAL':
        i = icons.get_icons()
        #Check if we are in current file in the asset browser
        current_library_name = context.area.spaces.active.params.asset_library_ref
        if current_library_name == "LOCAL":
            self.layout.operator('wm.save_files', icon_value=i["bakeduniverse"].icon_id)
            statusbar.ui_titlebar_upload(self,context)
            return



def update_library(self, context):
    # new_asset = context.window_manager.bu_props.new_assets
    i = icons.get_icons()
    layout = self.layout
    layout.scale_y = 1.2
    box = layout.box()
    row = box.row(align=True)
    # row.alignment = 'RIGHT'
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
        

