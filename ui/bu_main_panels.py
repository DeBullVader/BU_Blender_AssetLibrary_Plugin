import bpy
import os
from bpy.types import Context
import textwrap
from ..utils import addon_info
from .. import addon_updater_ops
from .. import icons
import urllib, json
import requests



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
 
        # box = layout.box()
        split = layout.split(factor=0.4,align=True)
        box = split.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label( text = "Main social accounts!",)
        discord = box.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        twitter_baked = box.operator('wm.url_open',text='Twitter Baked Universe',icon_value=i["twitter"].icon_id)
        twitter_blender = box.operator('wm.url_open',text='Twitter Blender Universe',icon_value=i["twitter"].icon_id)
        reddit = box.operator('wm.url_open',text='Reddit',icon_value=i["reddit"].icon_id)
        box = split.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="More information about Blender Universe Kit",icon_value=i["BU_logo_v2"].icon_id)
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="is available at our Gitbook")
        gitbook = box.operator('wm.url_open',text='Gitbook',icon='INFO')
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label( text = "Our youtube has some handy beginner tutorials!",)
        youtube = box.operator('wm.url_open',text='Youtube',icon_value=i["youtube"].icon_id)
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
    bl_category = 'BU Core'

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
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
