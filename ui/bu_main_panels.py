import bpy
import os
from bpy.types import Context
import textwrap
from ..utils import addon_info
from .. import addon_updater_ops
from .. import icons
from .asset_mark_setup import BU_PT_MarkTool_settings
import urllib, json
import requests

class BU_PT_AssetBrowser_Tools_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_label = 'Blender Universe asset browser tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe Kit'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        

class BU_PT_AssetBrowser_settings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_SETTINGS"
    bl_label = 'Asset Browser Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}

    addon_prefs = addon_info.get_addon_name().preferences
    
    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences     
        layout = self.layout
        row = layout.row()
        
        draw_lib_path_info(self,context,addon_prefs)
       
        box = layout.box()
        text ="Automatic update" if addon_prefs.automaticly_update_original_assets else "Manual update"
        row = box.row(align = True)
        row.label(text="BU Asset Library sync behavior")
        addon_info.gitbook_link(row,'add-on-settings-initial-setup/asset-browser-settings#bu-asset-library-sync-behavior')
        row = box.row(align = True)
        row.label(text='Download asset updates on sync')
        row.prop(addon_prefs, "automaticly_update_original_assets", text=text,icon='FILE_REFRESH',toggle=False)
        row = box.row(align=True)
        text = "Remove deprecated assets" if addon_prefs.remove_deprecated_assets else "Move deprecated assets"
        row.label(text='Remove deprecated assets on sync')
        row.prop(addon_prefs, "remove_deprecated_assets", text=text,icon='TRASH',toggle=False)
        BU_PT_MarkTool_settings.draw(self,context)

def draw_lib_path_info(self,context, addon_prefs):
    
    layout = self.layout
    box = layout.box()
    row = box.row()
    row.label(text="Library file path setting")
    addon_info.gitbook_link(row,'add-on-settings-initial-setup/asset-browser-settings#library-filepath-settings')
    if context.scene.adjust ==False and addon_prefs.lib_path != '':  
        box.label(text=f' Library Location: {addon_prefs.lib_path}',icon='CHECKMARK')
        box.prop(context.scene,'adjust', text = 'Unlock',toggle=True,icon='UNLOCKED')
    else:
        
        row = box.row(align = True)
        row.alignment = 'LEFT'
        row.label(text=f'Library Location:',icon='ERROR' if addon_prefs.lib_path == '' else 'CHECKMARK')
        row.prop(addon_prefs,'lib_path', text='')
        row.prop(context.scene,'adjust', text = 'Lock',toggle=True,icon='LOCKED',invert_checkbox=True)
    
    test_lib_names = addon_info.get_test_lib_names()
    bu_lib_names = addon_info.get_bu_lib_names()
    
    lib_names = test_lib_names if addon_prefs.debug_mode else bu_lib_names
    lib_dir_valid = validate_library_dir(addon_prefs,lib_names)
    lib_names_valid = validate_bu_library_names(addon_prefs,lib_names)
    
    if (lib_dir_valid == False or lib_names_valid == False):
        box.label(text="We need to generate library paths",icon='ERROR')
        box.operator('bu.addlibrarypath', text = 'Generate Library paths', icon='NEWFOLDER')
    else:    
        for lib_name in lib_names:
            if lib_name in bpy.context.preferences.filepaths.asset_libraries:
                box.label(text=lib_name, icon='CHECKMARK')
        if any(lib_name in bpy.context.preferences.filepaths.asset_libraries for lib_name in lib_names):
            box.operator('bu.removelibrary', text = 'Clear library paths', icon='TRASH',)  

def validate_library_dir(addon_prefs,lib_names):
    for lib_name in lib_names:
        if lib_name in bpy.context.preferences.filepaths.asset_libraries:
            lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
            if lib is not None:
                dir_path,lib_name = os.path.split(lib.path)
                if addon_prefs.lib_path.endswith(os.sep):
                    dir_path = dir_path+os.sep
                if not os.path.exists(lib.path):
                    return False
                if addon_prefs.lib_path != dir_path:
                    return False
                return True

def validate_bu_library_names(addon_prefs,lib_names):

    if not all(lib_name in bpy.context.preferences.filepaths.asset_libraries for lib_name in lib_names):
        return False
    return True

class Addon_Updater_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_UPDATER"
    bl_label = 'Blender Universe Kit Updater'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw (self, context):
        addon_updater_ops.update_settings_ui(self, context)

    
class BBPS_Info_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BBPS_INFO_PANEL"
    bl_label = 'Blender Universe Kit Info'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        i = icons.get_icons()
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label( text = "Our blender classes can be found on our youtube channel!",)
        row = box.row()
        youtube = row.operator('wm.url_open',text='Youtube',icon_value=i["youtube"].icon_id)
        row = box.row()
        discord = row.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        twitter_baked = row.operator('wm.url_open',text='Baked Universe',icon_value=i["X_logo_black"].icon_id)
        twitter_blender = row.operator('wm.url_open',text='Blender Universe',icon_value=i["X_logo_black"].icon_id)
        reddit = row.operator('wm.url_open',text='Reddit',icon_value=i["reddit"].icon_id)
        box = layout.box()

        row= box.row()
        row.alignment = 'CENTER'
        row.label(text="Links to specific add-on functionality pages on gitbook ")
        row= box.row()
        row.alignment = 'CENTER'
        row.label(text="can be found throughout the add-on",icon='HELP')
        box = layout.box()
        row= box.row()
        row.alignment = 'CENTER'
        row.label(text="More information about the Blender Universe add-on")
        row= box.row()
        row.alignment = 'CENTER'
        row.label(text="can be found on Gitbook")
        col = box.column(align=True)
        gitbook = col.operator('wm.url_open',text='Gitbook',icon='HELP')
        addon_info.gitbook_link_with_text(col, 'copyright-and-asset-license','BU Assets Copyright & License')
        

        discord.url = 'https://discord.gg/bakeduniverse'
        twitter_baked.url = 'https://twitter.com/BakedUniverse'
        twitter_blender.url = 'https://twitter.com/BlenderUni'
        youtube.url = 'https://www.youtube.com/@blender-universe'
        reddit.url = 'https://www.reddit.com/user/BakedUniverse/'
        # latest_yt_tut.url =  addon_prefs.youtube_latest_vid_url
        gitbook.url= 'https://bakeduniverse.gitbook.io/baked-blender-pro-suite/introduction/welcome-to-baked-blender-pro-suite'

def draw_bu_logo():
    addon_path = addon_info.get_addon_path()
    path = os.path.join(addon_path, 'BU_plugin_assets','images','BU_logo_v2.png')
    img = bpy.data.images.load(path,check_existing=True)
    texture = bpy.data.textures.new(name="BU_Logo", type="IMAGE")
    texture.image = img
    
    return img

class BBPS_Main_Addon_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_label = 'Blender Universe Kit'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe Kit'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.alignment = 'EXPAND' 
        box = row.box()
        row = box.row(align = True)
        i = icons.get_icons()
        box.template_icon(icon_value=i["BU_logo_v2"].icon_id, scale=5)
        intro_text = 'The Blender Universe Kit (BUK) is an asset library that contains 3D models, materials, geometry node setups, particle systems, and eventually much more.'
        _label_multiline(
        context=context,
        text=intro_text,
        parent=box
        )


def _label_multiline(context, text, parent):
    panel_width = int(context.region.width*1.5)   # 7 pix on 1 character
    uifontscale = 9 * context.preferences.view.ui_scale
    max_label_width = int(panel_width // uifontscale)
    wrapper = textwrap.TextWrapper(width=max_label_width )
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line,)



classes = (
    BBPS_Main_Addon_Panel,
    BBPS_Info_Panel,
    Addon_Updater_Panel,
    BU_PT_AssetBrowser_Tools_Panel,
    BU_PT_AssetBrowser_settings, 
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
