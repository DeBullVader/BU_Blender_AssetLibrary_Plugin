import bpy
from bpy.props import *
from ...utils import addon_info
from .asset_manager_utils import *
from bpy.utils import register_classes_factory
from ...ui import library_tools_ui
class UB_PT_AssetManager(bpy.types.Panel):
    bl_idname = "UB_PT_AssetManager"
    bl_label = "Asset Manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UniBlend"
    bl_parent_id = "VIEW3D_PT_BU_CORE_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass

class E_AssetManagerSettings(bpy.types.PropertyGroup):
    switch_tabs: bpy.props.EnumProperty(
        name = 'Asset manager settings',
        description = "Switch between setting tabs",
        items=[
            ('operators', 'Operators', '', 'ASSET_MANAGER', 0),
            ('render_settings', 'Render Settings', '', 'OUTPUT', 1),
            ('tool_settings', 'Tool Settings', '', 'TOOL_SETTINGS', 2),
        ],
        default='operators',
    )


class AssetManager_settings():
    # def __init__(self):

    def draw_asset_manager_options(self,context,layout):
        am_settings_tabs = context.scene.asset_manager_settings_tabs.switch_tabs
        box = layout.box()
        box.separator(factor=1)
        if am_settings_tabs == 'operators':
            self.draw_tool_operators(context,box)
        if am_settings_tabs == 'tool_settings':

            self.draw_tool_settings(context,box)

        if am_settings_tabs == 'render_settings':
            self.draw_render_settings(context,box)

    def draw_tool_settings(self,context,layout):
        addon_prefs = addon_info.get_addon_prefs()
        asset_props =context.scene.asset_props
        box= layout.box()
        library_tools_ui.upload_settings(self,context,box,addon_prefs)
        col = layout.column(align=False)
        
        col.prop(asset_props,'exclude_extras',text='Exclude Extras')
        col.prop(asset_props, "use_asset_example_rotation", text="Use preview asset rotation")
        col.separator(factor=1)
        col.prop(asset_props,'debug',text='Debug Preview Render',toggle=True)

    def draw_render_settings(self,context,layout):
        render_settings = context.scene.render_settings
        box= layout.box()
        row= box.row(align=True)
        col= row.column(align=False)
        col.template_icon_view(context.scene, "light_setup",scale=8,scale_popup=5)
  
        subrow = col.row(align=True)
        subrow.alignment = 'CENTER'
        subrow.label(text=context.scene.light_setup.removesuffix('.png'))
        col = row.column(align=True) 
        col.template_icon_view(context.scene, "hdri",scale=8, scale_popup=5)
        col.prop(render_settings, "world_exposure", text="Exposure")
        col.prop(render_settings, "world_temperature", text="Temperature")
        # row.template_ID_preview(bpy.data.screens["Layout"].shading, "studio_light", rows=4,cols =6)
        row = layout.row(align=True)
        # self.mat_list(context,layout)
        col = layout.column(align=False)
        col.alignment = 'CENTER'

        col.prop(render_settings, "enable_backdrop", text="Enable Background",icon='IMAGE_BACKGROUND')
        if render_settings.enable_backdrop:
            row = col.row(align=True)
            row.prop(render_settings, "background_color", text="Background Color")
            row = col.row(align=True)
            row.prop(render_settings, "emissive_strength", text="Emissive Strength")
            col.separator(factor=1)
        col.prop(render_settings, "background_transparent", text='Transparent ',toggle=False)
        col.prop(render_settings, "enable_ub_logo", text="Render with UniBlend Logo",toggle=False)
        col.prop(render_settings,"floor_height", text="Adjust Floor height")
        col.label(text="Floor Material Settings")
        col.prop(render_settings,"floor_metallic", text="Floor Metallic")
        col.prop(render_settings,"floor_roughness", text="Floor Roughness")

    def draw_tool_operators(self, context, layout):
        asset_props =context.scene.asset_props
        camera_ui_text = "Adjust Camera" if not asset_props.adjust_camera else "Confirm Adjustments"
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.scale_y = 1.25
        row.operator("ub.adjust_preview_camera",text=camera_ui_text,icon="VIEW_CAMERA",depress=asset_props.adjust_camera)
        
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.scale_y = 1.25
        row.operator('ub.mark_assets', text="Mark all", icon='ASSET_MANAGER')
        row.operator('ub.unmark_assets', text="Unmark all", icon='CANCEL')

    def mat_list(self,context,layout):
        world = context.scene.world
        layout = self.layout
        # layout.template_preview(world)
        # props = context.scene.extra_material_list
        # layout.template_ID_preview("MATERIAL_UL_extra_material_list.material_list", "", bpy.data,'worlds', props, 'world_id', rows=len(bpy.data.worlds))

        wNode = world.node_tree.nodes.active
        if wNode.type == 'TEX_ENVIRONMENT':
            layout.label(text=wNode.name, icon='TEXTURE')
            layout.template_ID_preview(
            wNode, "image",
            new = "image.new",
            open = "image.open",
            rows = 4, cols = 6)
            img = wNode.image





class UB_PT_AssetManager_UIList(bpy.types.Panel,AssetManager_settings):
    bl_idname = "UB_PT_AssetManager_UIList"
    bl_label = "Asset List"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "UB_PT_AssetManager"
    bl_category = "UniBlend"
    bl_options = {'DEFAULT_CLOSED','HIDE_HEADER'}
    
    bl_order = 1
    render_scene = None
           
    def draw(self, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            self.render_scene = bpy.data.scenes.get('PreviewRenderScene')
        asset_props =context.scene.asset_props
        am_settings_tabs = context.scene.asset_manager_settings_tabs
        layout = self.layout
        selected_assets =get_selected_assets()
        col = layout.column(align=True)
        row = col.row(align=True)
        for enum_item in am_settings_tabs.bl_rna.properties['switch_tabs'].enum_items:
            row.prop_enum(am_settings_tabs, "switch_tabs", enum_item.identifier, text=enum_item.name)
        self.draw_asset_manager_options(context,col)

        list_options_box = layout.box()
        row = list_options_box.row(align=True)
        row.alignment = 'CENTER'
    
        if selected_assets:
            status_text = f'{len(selected_assets)} Selected asset(s):'
        elif asset_props.is_rendering:
            status_text = 'Rendering Previews'
        elif asset_props.adjust_camera:
            status_text = 'Adjusting Camera'
        else:
            status_text = 'Select assets in the viewport to begin!'

        assets_col = list_options_box.column(align=False)
        assets_col.scale_y = 1.25
        split = assets_col.split(align=True)

        if asset_props.asset_types in ('Material Nodes','Materials'):
            row = assets_col.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(asset_props,'render_types',expand=True,icon_only=True)

        row = split.row(align=False)
        row.prop(asset_props,'asset_types',expand=False,text='')
        row = split.row()
        row.alignment = 'RIGHT'
        # rtype,rname,icon =asset_props.render_types
        row.operator('ub.render_previews', text="Render Previews", icon='OUTPUT')


        assets_box = layout.box()
        assets_box.enabled = len(selected_assets) > 0 
        row = assets_box.row(align=True)
        row.alignment = 'LEFT'
        row.label(text=status_text,icon="SELECT_SET")
        row = assets_box.row(align=True)
        assets_to_filter = selected_assets if not asset_props.is_rendering else [selected.asset for selected in asset_props.selected]
        filtered_hierarchy = filter_assets(assets_to_filter, asset_props.asset_types)
        self.render_asset_hierarchy(assets_box, filtered_hierarchy,asset_props.asset_types)
        # print_hierarchy(filtered_hierarchy)

        
    def render_asset_hierarchy(self,layout, hierarchy, selected_asset_type, level=0):
        main_col = layout.column(align=True)
        if level != 0:
            level +=1
        if not hierarchy:
            box = main_col.box()
            row =box.row(align=True)
            row.alignment = 'EXPAND'
            row.label(text="No Assets Found with Type: " + selected_asset_type)
        for item in hierarchy:
                if item and hasattr(item, 'asset') and item.asset:
                    row=main_col.row(align=True)
                    row.separator(factor=level)  # Indent based on hierarchy level
                    if hasattr(item, 'children') and item.children:
                        box=row.box()
                        box_row = box.row(align=True)
                        # box_row.alignment = 'EXPAND'
                        minimized =item.asset.name in AssetOperations.minimized_list
                        icon = 'RIGHTARROW' if minimized else 'DOWNARROW_HLT'
                        depress = True if minimized else False
                        op = box_row.operator("ub.minimize_asset_details", text="", icon=icon, depress=depress, emboss=False)
                        op.asset_name = item.asset.name
                        box_row.separator(factor=0.5)
                        if selected_asset_type =='Objects' and item.asset.children:
                            AssetOperations.clear_parent(box_row, item.asset, selected_asset_type)
                        box_row.separator(factor=1)
                        box_row.label(text=item.asset.name, icon=get_icon_for_asset_type(item.asset_type))

                        if selected_asset_type == 'Material Nodes' and item.asset.id_type == 'OBJECT':
                            pass
                        if len(item.children) > 1:
                            AssetOperations.op_exclude_all(box_row, item.children)
                            AssetOperations.op_mark_clear_children(box_row, item.asset, selected_asset_type)
                    else:
                        if level != 0 and item.asset_type != selected_asset_type:
                            row.label(text="", icon='BLANK1')  # Placeholder for leaf nodes   
                        
                    if item.asset_type == selected_asset_type  and not item.children:
                        target_asset = item.asset if item.asset_type != 'Material Nodes' else item.asset.node_tree
                        ui_asset_data(row, item.asset_type, target_asset,selected_asset_type)

                    # Render children immediately after the parent
                    if hasattr(item, 'children') and item.children and not minimized:
                        child_col = main_col.column(align=True)
                        self.render_asset_hierarchy(child_col, item.children, selected_asset_type, level + 1)
                        child_col.separator(factor=0.5)
                else:
                    row = main_col.row(align=True)
                    row.label(text="Invalid item in hierarchy")

def print_hierarchy(hierarchy, level=0):
  for item in hierarchy:
      if item.children:
          print_hierarchy(item.children, level + 1)

class UB_OT_RemoveFromList(bpy.types.Operator):
    bl_idname = "ub.remove_from_list"
    bl_label = "Remove from List"
    bl_description = "Remove from list"
    bl_options = {'REGISTER', 'UNDO'}

    asset_name: bpy.props.StringProperty()
    
    def execute(self, context):
        if self.asset_name not in AssetOperations.exclude_list:
            AssetOperations.exclude_list.append(self.asset_name)
        else:
            AssetOperations.exclude_list.remove(self.asset_name)
        return {'FINISHED'}
    
class UB_OT_MinimizeAssetDetails(bpy.types.Operator):
    bl_idname="ub.minimize_asset_details"
    bl_label = "Minimize/Maximize"
    
    asset_name: bpy.props.StringProperty()

    def execute(self, context):
        toggle_minimize(context,self.asset_name)
        return {'FINISHED'}
   
def is_minimized(context, asset_name):
    return asset_name in AssetOperations.minimized_list

def toggle_minimize(context, asset_name):
    if is_minimized(context, asset_name):
        AssetOperations.minimized_list.remove(asset_name)
    else:
        AssetOperations.minimized_list.append(asset_name)



classes=(
    UB_PT_AssetManager,
    UB_PT_AssetManager_UIList,
    UB_OT_MinimizeAssetDetails,
    UB_OT_RemoveFromList,
    E_AssetManagerSettings,
    
    )

register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
    bpy.types.Scene.asset_manager_settings_tabs = bpy.props.PointerProperty(type=E_AssetManagerSettings, options={'HIDDEN'})
   
def unregister():
    unregister_classes()
    del bpy.types.Scene.asset_manager_settings_tabs