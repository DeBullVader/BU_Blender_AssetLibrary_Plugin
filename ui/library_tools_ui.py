import bpy,os,textwrap
from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from ..utils import addon_info,sync_manager
from . import marktool_tabs
from bpy.props import *

class BU_PT_AssetLibraryTools(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETLIBRARYTOOLS"
    bl_label = 'Asset Library'
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

class BU_PT_AddToAssetLibrary(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_ADDTOASSETLIBRARY"
    bl_label = 'Add to Asset Library'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETLIBRARYTOOLS"
    bl_category = 'Blender Universe'
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        
        # dir_path = addon_prefs.lib_path
        # if  dir_path !='':
        return True

    def draw(self,context): 
        addon_prefs = addon_info.get_addon_prefs()
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.label(text = 'Select assets in the outliner to add')
        
        row = box.row(align=True)
        split = row.split(factor=0.5)
        row = split.row(align=True)
        row.alignment = 'LEFT'
        row.operator('wm.add_to_mark_tool', text=('Add Selected'), icon ='ADD')
        row.operator('wm.clear_mark_tool', text=('Clear List'), icon = 'CANCEL')
        row= split.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(addon_prefs, 'toggle_add_to_library_settings', text = 'Settings', icon = 'TOOL_SETTINGS')
        if addon_prefs.toggle_add_to_library_settings:
            box = layout.box()
            mark_tool_settings(self,context,box,addon_prefs)
            draw_get_bu_catalog_file(self,context,box,addon_prefs)
        row.prop(addon_prefs, 'toggle_library_tool_info', text = 'More Information',toggle=True,icon ='HELP')
        if addon_prefs.toggle_library_tool_info:
            library_tool_info(self,context,addon_prefs)

        if len(context.scene.mark_collection)>0:
            # col.prop(addon_prefs, 'toggle_experimental_BU_Render_Previews', text = 'Toggle Render Previews',toggle=True,icon ='OUTPUT')
            switch_marktool = context.scene.switch_marktool
            layout = self.layout
            row = layout.row(align=True)
            
            for enum_item in switch_marktool.bl_rna.properties['switch_tabs'].enum_items:
                row.prop_enum(switch_marktool, "switch_tabs", enum_item.identifier, text=enum_item.name)
            
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.operator('bu.select_all_items', text='Select all assets', icon='RESTRICT_SELECT_OFF')
            is_local_view = context.space_data.local_view is not None
            row.operator('bu.isolate_selected', text='Isolate selected' if not is_local_view else 'Deisolate selected', icon='STICKY_UVS_LOC',depress= is_local_view)
            marktool_tabs.draw_marktool_default(self, context)
            
            
            row = layout.row()
            row.operator('wm.confirm_mark', text=('Mark all Assets'), icon='BLENDER')
            row.operator('wm.clear_marked_assets', text =('Bath unmark assets'), icon = 'CANCEL')

def library_tool_info(self,context,addon_prefs):
    layout = self.layout
    row = layout.row()
    split = row.split(factor=0.5)
    row = split.row()
    row.alignment = 'LEFT'
    row.label(text = 'Library Tool Info: ')
    row = split.row()
    row.alignment = 'RIGHT'
    addon_info.gitbook_link_getting_started(row,'mark-asset-tools/mark-tool','Full guide')
    
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
    # col.label(text='Naming conventions are not mendatory but help identify asset types by name:')
    # naming_conventions ='SM_ = Object(Static Mesh) \nAM_ = Object(Animated Mesh)\nM_ = Material \nNG_ = Node Group \nC_ = Collection \nPS_ = Particle System \nT_ = Texture'
    # for line in naming_conventions.split('\n'):
    #     col.label(text=line)
    # box.label(text=str(naming_example.split('\n')))
    # naming_example_text = wrapp.wrap(text=naming_example.split('\n'))
    # box = self.layout.box()
    # for text in naming_example_text:
    #     box.label(text=text)

def mark_tool_settings(self, context,parent,addon_prefs):
    row = parent.row()
    row.label(text = 'Upload settings: ')
    
    addon_info.gitbook_link_getting_started(row,'mark-asset-tools/mark-tool#mark-tool-settings','')
    col = parent.column(align=True)
    # col.alignment = 'LEFT'
    sub=col.column()
    sub.use_property_split = True
    sub.use_property_decorate = False
    sub.prop(addon_prefs, 'author', text = 'Global Author name ')
    sub.prop(addon_prefs, 'thumb_upload_path', text = 'BU Upload Asset Previews')

    
def draw_get_bu_catalog_file(self,context,parent,addon_prefs):
    row = parent.row()
    if addon_prefs.is_admin:
        # row.label(text = 'Select a library catalog to download:')
        row = parent.row(align=False)
        row.alignment = 'RIGHT'
        scene = context.scene
        row.prop(scene.upload_target_enum, "switch_upload_target", text="")
    if sync_manager.SyncManager.is_sync_operator('bu.sync_catalog_file'):
        row.operator('bu.sync_catalog_file', text='Cancel Sync', icon='CANCEL')
    else:
        row.operator('bu.sync_catalog_file', text='Get BU catalog file' if not addon_prefs.debug_mode else 'Get BU Test catalog file', icon='OUTLINER')


class AddtoLibraryCatagories(bpy.types.PropertyGroup):
    switch_tabs: bpy.props.EnumProperty(
        name = 'mark tool catagories',
        description = "Switch between mark tool catagories",
        items=[
            ('asset_properties', 'Asset Properties', '', 'BLENDER', 0),
            ('render_previews', 'Render Previews', '', 'OUTPUT', 1),
            ('metadata', 'Asset Metadata', '', 'WORDWRAP_ON', 2)
        ],
        default='asset_properties',
    )

class BU_PT_PreviewRenderScene(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_PREVIEWRENDEROPTIONS"
    bl_label = 'Preview Render Scene'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETLIBRARYTOOLS"
    bl_category = 'Blender Universe'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        mainrow = box.row()
        mainrow.alignment = 'LEFT'
        col = mainrow.column()
        
        col.label(text='Preview Render scene:')
        row = col.row(align=True)
        
        row.operator("bu.append_preview_render_scene", text="Append", icon='APPEND_BLEND')
        row.operator("bu.remove_preview_render_scene", text="Remove", icon='REMOVE')
        col = mainrow.column()
        col.alignment = 'LEFT'
        col.label(text='Switch scenes:')
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        # row.operator("bu.switch_to_preview_render_scene", text="Switch Scene", icon='SCENE_DATA')
        window = context.window
        screen = context.screen
        scene = window.scene
        row.template_ID(window, "scene", new="scene.new",unlink="scene.delete")
        mainrow.alignment = 'RIGHT'
        addon_info.gitbook_link_getting_started(mainrow,'mark-asset-tools/preview-render-scene','')
        
class BU_PT_MarkTool_settings(bpy.types.Panel):
    bl_label = 'Mark Tool Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe'
    bl_parent_id = "VIEW3D_PT_BU_ASSETLIBRARYTOOLS"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        # box = layout.box()
        row = layout.row()
        row.label(text = 'Mark asset tool settings: ')
        
        addon_info.gitbook_link_getting_started(row,'mark-asset-tools/mark-tool#mark-tool-settings','')
        col = layout.column(align=True)
        # col.alignment = 'LEFT'
        sub=col.column()
        sub.prop(addon_prefs, 'author', text = 'Global Author name ')
        sub.prop(addon_prefs, 'thumb_upload_path', text = 'Asset preview folder')
    
        row = layout.row()
        if addon_prefs.is_admin:
            # row.label(text = 'Select a library catalog to download:')
            row = layout.row(align=False)
            row.alignment = 'RIGHT'
            scene = context.scene
            row.prop(scene.upload_target_enum, "switch_upload_target", text="")
        if sync_manager.SyncManager.is_sync_operator('bu.sync_catalog_file'):
            row.operator('bu.sync_catalog_file', text='Cancel Sync', icon='CANCEL')
        else:
            row.operator('bu.sync_catalog_file', text='Get BU catalog file' if not addon_prefs.debug_mode else 'Get BU Test catalog file', icon='OUTLINER')

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
    BU_PT_AssetLibraryTools,
    BU_PT_AddToAssetLibrary,
    BU_PT_PreviewRenderScene,
    AddtoLibraryCatagories,
    CatalogTargetProperty,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.catalog_target_enum = bpy.props.PointerProperty(type=CatalogTargetProperty)
    bpy.types.Scene.switch_marktool = bpy.props.PointerProperty(type=AddtoLibraryCatagories)

def unregister():
    del bpy.types.Scene.catalog_target_enum
    del bpy.types.Scene.switch_marktool
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)