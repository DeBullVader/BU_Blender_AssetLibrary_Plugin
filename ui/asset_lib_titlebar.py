import bpy
from . import statusbar
from .. import icons
# from ..operators.asset_lib_operators import WM_OT_unmark_as_baked_asset,WM_OT_upload_files,WM_OT_mark_filter
# 
# 

class AssetLibraryOperations(bpy.types.Menu):
    bl_label = "BU Library Tools"
    bl_idname = "BU_MT_Library_Tools"

    
    def draw(self, context):
        layout = self.layout
        
        layout.operator('wm.markfilter', text=('Mark Selected Asset'))
        
        layout.operator('wm.unmarkasbuasset', text=('Unmark Selected Assets'))

def draw_menu(self, context):
    if context.space_data.params.asset_library_ref != "BU_AssetLibrary_Core":
        i = icons.get_icons()
        layout = self.layout
        layout.scale_x =1.1
        layout.menu(AssetLibraryOperations.bl_idname, icon_value=i["bakeduniverse"].icon_id)
    else:
        update_library(self,context)
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
    row.operator('wm.downloadall', text = ('Update Library'),  icon_value=i["bakeduniverse"].icon_id)

def upload_assets (self, context):
    if context.space_data.params.asset_library_ref != "BU_AssetLibrary_Core":
        return
    pass



def asset_browser_titlebar(self, context):
        if context.space_data.params.asset_library_ref != "BU_AssetLibrary_Core":
            return
        update_library(self, context)
       
        # b = row.box()  # Force some kind of emboss effect
        # b.menu("PHA_MT_pull_by_type", text="", icon="DOWNARROW_HLT")
        statusbar.ui_titlebar(self,context)
