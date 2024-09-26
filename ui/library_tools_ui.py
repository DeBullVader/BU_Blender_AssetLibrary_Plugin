import bpy,os,textwrap
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from bpy_extras import asset_utils
from ..utils import addon_info,sync_manager,version_handler
from .. import icons
from . import marktool_tabs,statusbar
from bpy.props import *
from ..utils.constants import *

class BU_PT_AssetLibraryTools(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETLIBRARYTOOLS"
    bl_label = 'Asset Manager'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_CORE_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self,context):
        layout = self.layout

class ASSETBROWSER_UL_metadata_tags(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        tag = item

        row = layout.row(align=True)
        # Non-editable entries would show grayed-out, which is bad in this specific case, so switch to mere label.
        if tag.is_property_readonly("name"):
            row.label(text=tag.name, icon_value=icon, translate=False)
        else:
            row.prop(tag, "name", text="", emboss=False, icon_value=icon)

class BU_PT_AB_LibrarySection(asset_utils.AssetBrowserPanel,bpy.types.Panel):
    bl_label = 'BU Library handler'
    bl_idname = "BU_PT_BU_LIBRARY_SECTION"
    # bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}
    bl_order = 0

    def draw(self,context):
        addon_prefs =addon_info.get_addon_prefs()
        bu_lib = addon_info.get_uniblend_lib_names()
        current_library_name = version_handler.get_asset_library_reference(context)
        if current_library_name.removeprefix('TEST_') in bu_lib:
            self.draw_bu_download_ops(context)
        if current_library_name == 'LOCAL':
            self.draw_bu_upload_ops(context,addon_prefs)
        if current_library_name == DEPRECATED_LIB:
            self.layout.operator("bu.remove_library_asset", text='Remove selected library asset', icon='TRASH')


                
            
    def draw_bu_download_ops(self,context):
        amount = len(context.scene.assets_to_update)
        amount_premium = len(context.scene.premium_assets_to_update)
        split = self.layout.split(factor=0.1)
        row = split.row(align=True)
        row.alignment = 'LEFT'
        addon_info.gitbook_link_getting_started(row,'how-to-use-the-asset-browser/sync-and-downloading-assets','')
        col = split.column(align=True)
        row = col.row(align=True)
        row.alignment = 'CENTER'
        
        if addon_info.is_lib_premium():
            
            if sync_manager.SyncManager.is_sync_operator('bu.sync_premium_assets'):
                row.operator('bu.sync_premium_assets', text='Cancel Sync', icon='CANCEL')
            else:
                row.operator('bu.sync_premium_assets', text='Sync Premium Assets', icon='DESKTOP')
        else:
            if sync_manager.SyncManager.is_sync_operator('bu.sync_assets'):
                row.operator('bu.sync_assets', text='Cancel Sync', icon='CANCEL')
            else:
                row.operator('bu.sync_assets', text='Sync Assets', icon='DESKTOP')
        
        if sync_manager.SyncManager.is_sync_operator('bu.download_original_asset'):
            row.operator('bu.download_original_asset', text='Cancel Sync', icon='CANCEL')
        else:
            original_download_op = row.operator('bu.download_original_asset', text='Download Asset(s)', icon='URL')
            original_download_op.is_premium = True if addon_info.is_lib_premium() else False
        row = col.row(align=True)
        if addon_info.is_lib_premium():
            if context.scene.premium_assets_to_update:
                row.operator('bu.assets_to_update', text=f'({amount_premium}) Premium Asset Updates', icon='MONKEY')
        else:
            if context.scene.assets_to_update:
                row.operator('bu.assets_to_update', text=f'({amount}) Asset Updates', icon='MONKEY')
    
    def draw_bu_upload_ops(self,context,addon_prefs):
        i = icons.get_icons()
        split = self.layout.split(factor=0.2)
        row=split.row(align=True)
        row.alignment = 'LEFT'
        addon_info.gitbook_link_getting_started(row,'upload-assets-to-server','')
        if addon_prefs.thumb_upload_path == '':    
            row.alert = True
        row.operator('bu.upload_settings', text='', icon ='SETTINGS')
        row=split.row(align=True)
        row.alignment = 'CENTER'
        if addon_prefs.debug_mode == True:
            scene = context.scene
            row.prop(addon_prefs, "upload_target", text="")
        #Check if we are in current file in the asset browser
        

        row.alert = False
        text = 'Upload to BU server' if addon_prefs.debug_mode == False else 'Upload to Test server'
        row.operator('wm.save_files', text=text,icon_value=i["BU_logo_v2"].icon_id) 
        # statusbar.draw_progress(self,context)
            

def library_tool_info(self,context,addon_prefs):
    layout = self.layout
    row = layout.row()
    split = row.split(factor=0.5)
    row = split.row()
    row.alignment = 'LEFT'
    row.label(text = 'Library Tool Info: ')
    row = split.row()
    row.alignment = 'RIGHT'
    addon_info.gitbook_link_getting_started(row,'tools-panel/library-manager','Library Manager guide')
    
    disclaimer = 'By uploading your own assets, you confirm that you have the necessary rights and permissions to use and share the content. You understand that you are solely responsible for any copyright infringement or violation of intellectual property rights. We assume no liability for the content you upload. Please ensure you have the appropriate authorizations before proceeding.'
    wrapp = textwrap.TextWrapper(width=int(context.region.width/6) ) #50 = maximum length       
    disclaimer_text = wrapp.wrap(text=disclaimer)
    box = self.layout.box()
    col = box.column(align=True)
    col.label(text = 'Please read the following disclaimer before using this tool')
    col.label(text='Disclaimer:')
    for text in disclaimer_text:
        col.label(text=text)
    box = self.layout.box()
    col = box.column(align=True)
    col.label(text = 'Naming Guidelines:')
    naming_example = f'Make sure to use descriptive names for assets you want to add!\nExample for a mesh: SM_Door_Damaged \nExample for Material: M_Wood_Peeled_Paint'
    for line in naming_example.split('\n'):
        col.label(text=line)

def upload_settings(self, context,parent,addon_prefs):
    row = parent.row()
    row.label(text = 'Upload settings: ')
    addon_info.gitbook_link_getting_started(row,'tools-panel/library-manager#upload-settings','')
    row = parent.row()
    row.use_property_split = True
    row.use_property_decorate = False
    row.alignment = 'RIGHT'
    row.prop(addon_prefs, 'author', text = 'Global Author name ',icon = 'USER')
   
    row = parent.row()
    row.alignment = 'RIGHT'

    
    if not addon_prefs.lib_path:
        row = parent.row()
        row.label(text='No Library path has been set')
        row.label(text='Please set a library path first')
        row.prop(addon_prefs, 'lib_path', text = 'Library path')
    else:
        col = parent.column()
        td,tt =os.path.splitdrive(addon_prefs.thumb_upload_path)
        ld,lt =os.path.splitdrive(addon_prefs.lib_path)
        
        thumbs_path =os.path.relpath(addon_prefs.thumb_upload_path,addon_prefs.lib_path) if td==ld else addon_prefs.thumb_upload_path
        custom_path_text = 'Enable Custom Thumnail Path' if not addon_prefs.enable_custom_thumnail_path else ''
        custom_path_icon = 'OUTLINER_DATA_GP_LAYER' if not addon_prefs.enable_custom_thumnail_path else 'CANCEL'
        row = col.row(align=True)
        row.prop(addon_prefs, 'enable_custom_thumnail_path', text = custom_path_text,icon =custom_path_icon,toggle=True)
        
        if addon_prefs.enable_custom_thumnail_path:
            row.prop(addon_prefs, 'thumb_upload_path', text = 'Asset preview folder path')
        else:
            upload_path = os.path.join(addon_prefs.lib_path,UPLOAD_LIB)
            addon_info.ensure_thumbnail_folder_exists(addon_prefs,upload_path)
            col.label(text=f'Thumbnail Path: {thumbs_path}' )



def draw_get_bu_catalog_file(self,context,parent,addon_prefs):
    row = parent.row()
    if addon_prefs.is_admin:
        # row.label(text = 'Select a library catalog to download:')
        row = parent.row(align=False)
        row.alignment = 'RIGHT'
        # scene = context.scene
        row.prop(addon_prefs, "upload_target", text="")
    if sync_manager.SyncManager.is_sync_operator('bu.sync_catalog_file'):
        row.operator('bu.sync_catalog_file', text='Cancel Sync', icon='CANCEL')
    else:
        row.operator('bu.sync_catalog_file', text='Get BU catalog file' if not addon_prefs.debug_mode else 'Get BU Test catalog file', icon='OUTLINER')


# class AddtoLibraryCatagories(bpy.types.PropertyGroup):
#     switch_tabs: bpy.props.EnumProperty(
#         name = 'mark tool catagories',
#         description = "Switch between mark tool catagories",
#         items=[
#             ('asset_properties', 'Asset Properties', '', 'BLENDER', 0),
#             ('render_previews', 'Render Previews', '', 'OUTPUT', 1),
#             ('metadata', 'Asset Metadata', '', 'WORDWRAP_ON', 2)
#         ],
#         default='asset_properties',
#     )

        
def set_catalog_file_target(self,context):
    catalog_target = context.scene.catalog_target_enum.switch_catalog_target
    addon_prefs = addon_info.get_addon_prefs()
    if catalog_target == 'core_catalog_file':
        addon_prefs.download_catalog_folder_id = addon_prefs.bl_rna.properties['upload_folder_id'].default if addon_prefs.debug_mode == False else "1Jnc45SV7-zK4ULQzmFSA0pK6JKc8z3DN"
    elif catalog_target == 'premium_catalog_file':
        addon_prefs.download_catalog_folder_id = "1FU-do5DYHVMpDO925v4tOaBPiWWCNP_9" if addon_prefs.debug_mode == False else "146BSw9Gw6YpC9jUA3Ehe7NKa2C8jf3e7"
    

class CatalogTargetProperty(bpy.types.PropertyGroup):
    switch_catalog_target: bpy.props.EnumProperty(
        name = 'catalog target',
        description = "get Core or Premium catalog file from server",
        items=[
            ('core_catalog_file', 'Core', '', '', 0),
            ('premium_catalog_file', 'Premium', '', '', 1)
        ],
        default='core_catalog_file',
        update=set_catalog_file_target
    )
    
def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

class LibToolsPrefs(AddonPreferences):
    bl_idname = __package__

    toggle_add_to_library_settings: BoolProperty(
        name="Toggle Add to Library Settings",
        description="Show the settings for the Add to Library tool",
        default=False,
    )
    toggle_library_tool_info: BoolProperty(
        name="Toggle library tool info",
        description="Show the library tool info section",
        default=False,
    )

classes=(
    # BU_PT_AssetLibraryTools,
    # AddtoLibraryCatagories,
    CatalogTargetProperty,
    BU_PT_AB_LibrarySection,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.catalog_target_enum = bpy.props.PointerProperty(type=CatalogTargetProperty)
    # bpy.types.Scene.switch_marktool = bpy.props.PointerProperty(type=AddtoLibraryCatagories)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(statusbar.draw_progress)

def unregister():
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(statusbar.draw_progress)
    del bpy.types.Scene.catalog_target_enum
    # del bpy.types.Scene.switch_marktool
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)