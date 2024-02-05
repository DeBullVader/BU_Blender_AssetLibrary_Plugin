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

class BU_PT_CoreToolsPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_CORE_TOOLS"
    bl_label = 'Tools panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe Kit'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        

class BU_PT_AddonSettings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ADDON_SETTINGS"
    bl_label = 'Addon Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}

    
    def draw(self,context):
        open_addon_prefs(self, context)
        addon_prefs = addon_info.get_addon_prefs()
        layout = self.layout
        draw_lib_path_info(self,context,addon_prefs)
        box = layout.box()
        text ="Automatic update" if addon_prefs.automaticly_update_original_assets else "Manual update"
        row = box.row(align = True)
        row.label(text="BU Asset Library sync behavior")
        addon_info.gitbook_link_getting_started(row,'add-on-settings-initial-setup/asset-browser-settings#bu-asset-library-sync-behavior','')
        row = box.row(align = True)
        row.label(text='Download asset updates on sync')
        row.prop(addon_prefs, "automaticly_update_original_assets", text=text,icon='FILE_REFRESH',toggle=False)
        row = box.row(align=True)
        text = "Remove deprecated assets" if addon_prefs.remove_deprecated_assets else "Move deprecated assets"
        row.label(text='Remove deprecated assets on sync')
        row.prop(addon_prefs, "remove_deprecated_assets", text=text,icon='TRASH',toggle=False)
        BU_PT_MarkTool_settings.draw(self,context)
        
        

 
def open_addon_prefs(self, context):
    layout = self.layout
    row = layout.row()
    row.label(text="Use the settings in the below panel or in the addon preferences")
    row = layout.row()
    row.operator("bu.open_addon_prefs", text="Addon preferences", icon='PREFERENCES')           
    

def draw_lib_path_info(self,context, addon_prefs):
    
    layout = self.layout
    box = layout.box()
    row = box.row()
    row.label(text="Library file path setting")
    addon_info.gitbook_link_getting_started(row,'add-on-settings-initial-setup/asset-browser-settings#library-filepath-settings','')
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
        split = box.split(factor=0.66, align=True)
        col = split.column()
        col.alignment = 'LEFT'
        box = col.box()
        col = box.column(align=False)
        col.alignment = 'LEFT'
        col.label(text='The Blender Universe Kit BETA')
        col.label(text='This add-on contains asset libraries and tools')
        col.label(text='Including:3D models, materials, geometry node setups, ')
        col.label(text='particle systems and asset tools')

        website =col.operator('wm.url_open',text='blender-universe.com',icon_value=i["BU_logo_v2"].icon_id)

        col = split.column(align=True)
        col.alignment = 'LEFT'
        youtube = col.operator('wm.url_open',text='Youtube',icon_value=i["youtube"].icon_id)
        discord = col.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        twitter_baked = col.operator('wm.url_open',text='Baked Universe',icon_value=i["X_logo_black"].icon_id)
        twitter_blender = col.operator('wm.url_open',text='Blender Universe',icon_value=i["X_logo_black"].icon_id)
        reddit = col.operator('wm.url_open',text='Reddit',icon_value=i["reddit"].icon_id)
        medium = col.operator('wm.url_open',text='Medium',icon_value=i["medium"].icon_id)     

        discord.url = 'https://discord.gg/bakeduniverse'
        twitter_baked.url = 'https://twitter.com/BakedUniverse'
        twitter_blender.url = 'https://twitter.com/BlenderUni'
        youtube.url = 'https://www.youtube.com/@blender-universe'
        reddit.url = 'https://www.reddit.com/user/BakedUniverse/'
        medium.url = 'https://medium.com/@bakeduniverse'
        website.url = 'https://blender-universe.com'

def draw_bu_logo():
    addon_path = addon_info.get_addon_path()
    path = os.path.join(addon_path, 'BU_plugin_assets','images','BU_logo_v2.png')
    img = bpy.data.images.load(path,check_existing=True)
    texture = bpy.data.textures.new(name="BU_Logo", type="IMAGE")
    texture.image = img
    
    return img

class BU_OT_OpenAddonPrefs(bpy.types.Operator):
    """ Open Blender Universe Addon Preferences """
    bl_idname = "bu.open_addon_prefs"
    bl_label = "Open Addon Preferences"
    bl_description = "Open Addon Preferences"

    def execute(self, context):
        addon_name = __name__.split('.')[0]
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[addon_name].preferences

        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        addon_prefs.active_section = 'ADDONS'
        bpy.ops.preferences.addon_expand(module = addon_name)
        bpy.ops.preferences.addon_show(module = addon_name)
            
        addon_prefs.addon_pref_tabs='toggle_all_addon_settings'
        return {'FINISHED'}

class BU_OT_Open_N_Panel(bpy.types.Operator):
    """ Open Blender Universe Addon Preferences """
    bl_idname = "bu.open_n_panel"
    bl_label = "Opens the N panel"
    bl_description = "Opens the N panel in the 3D View"

    def execute(self, context):
        
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                print(area.type)
                if area.type == 'VIEW_3D':
                    with context.temp_override(window=window, area=area):
                        bpy.ops.wm.context_toggle(data_path="space_data.show_region_ui")
        return {'FINISHED'}

class BBPS_Main_Addon_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_label = 'Blender Universe Core'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe Kit'


    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.3)
        row = layout.row(align=True)
        row.alignment = 'EXPAND' 
        box = row.box()
        row = box.row(align = True)
        i = icons.get_icons()
        box.template_icon(icon_value=i["BU_logo_v2"].icon_id, scale=4)


class BU_PT_Docs_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_DOCS"
    bl_label = 'Documentation & Getting Started'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        i = icons.get_icons()
        box = layout.box()        

        box.label(text='Help icon example: ',icon='HELP')
        col = box.column(align=True)
        col.label(text='Links to specific add-on functionality pages on gitbook,')
        col.label(text='can be found throughout the add-on with the help icon shown above.')
        col.label(text='More information about the Blender Universe add-on can be found on our Gitbook')
        addon_info.gitbook_link_getting_started(box, 'add-on-settings-initial-setup','Getting Started')
        addon_info.gitbook_link_getting_started(box, 'copyright-and-asset-license','BU Assets Copyright & License')

        box = layout.box()
        box.label(text='Troubleshooting',icon='ERROR')
        col = box.column(align=True)
        col.label(text='As we are developing the add-on some scenarios might give errors.')
        col.label(text='If this happens please open a ticket on our discord.')
        
        row = box.row()
        row.alignment = 'LEFT'
        discord = row.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        discord.url = 'https://discord.gg/bakeduniverse'

        col = box.column(align=True)
        col.label(text='You can either open the console and send us a screenshot of the error')
        col.label(text='or send us the error_log.txt file that can be found in the error_logs folder.')
        
        box.operator('wm.console_toggle',text='Toggle Console',icon='CONSOLE')
        box.operator('bu.open_error_logs_folder',text='Open Error Logs Folder',icon='TEXT')
        box.operator('bu.open_addon_location',text='Open Addon Install Location',icon='FILE_FOLDER')

class BU_OT_OpenAddonLocation(bpy.types.Operator):
    bl_idname = "bu.open_addon_location"
    bl_label = "Open Addon Location"

    def execute(self, context):
        addon_path = addon_info.get_addon_path()
        os.startfile(addon_path)
        return {'FINISHED'}
    
class BU_OT_OpenErrorLogFolder(bpy.types.Operator):
    bl_idname = "bu.open_error_logs_folder"
    bl_label = "Open error logs folder"

    def execute(self, context):
        addon_path = addon_info.get_addon_path()
        logs_folder = os.path.join(addon_path,'error_logs')
        if not os.path.isdir(logs_folder):
            os.mkdir(logs_folder)
        os.startfile(logs_folder)
        return {'FINISHED'}

def _label_multiline(context, text, parent):
    panel_width = int(context.region.width*2)   # 7 pix on 1 character
    uifontscale = 9 * context.preferences.view.ui_scale
    max_label_width = int(panel_width // uifontscale)
    wrapper = textwrap.TextWrapper(width=panel_width )
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line,)

def _label_multiline_width(context, text, parent,width):
    wrapper = textwrap.TextWrapper(width=width )
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line,)

classes = (
    BBPS_Main_Addon_Panel,
    BBPS_Info_Panel,
    Addon_Updater_Panel,
    BU_PT_CoreToolsPanel,
    BU_PT_AddonSettings,
    BU_PT_Docs_Panel,
    BU_OT_OpenAddonPrefs,
    BU_OT_Open_N_Panel,
    BU_OT_OpenAddonLocation,
    BU_OT_OpenErrorLogFolder,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
