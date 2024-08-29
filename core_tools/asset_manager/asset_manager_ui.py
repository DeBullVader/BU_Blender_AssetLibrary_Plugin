import bpy
from ...utils import addon_info
from .asset_manager_utils import *
from bpy.utils import register_classes_factory

class UB_PT_AssetManager(bpy.types.Panel):
    bl_idname = "UB_PT_AssetManager"
    bl_label = "Asset Manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UniBlend"
    bl_parent_id = "VIEW3D_PT_BU_CORE_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # layout.label(text="Asset Manager")

class E_AssetManagerSettings(bpy.types.PropertyGroup):
    switch_tabs: bpy.props.EnumProperty(
        name = 'Asset manager settings',
        description = "Switch between setting tabs",
        items=[
            ('hide_settings', 'Hide Settings', '', 'HIDE_OFF', 0),
            ('tool_settings', 'Tool Settings', '', 'TOOL_SETTINGS', 1),
            ('render_settings', 'Render Settings', '', 'OUTPUT', 2),
        ],
        default='hide_settings',
    )


class AssetManager_settings():
    # bl_idname = "UB_PT_AssetManager_settings"
    # bl_label = "Asset Manager Settings"
    # bl_space_type = 'VIEW_3D'
    # bl_region_type = 'UI'
    # bl_category = "UniBlend"
    # bl_parent_id ='UB_PT_AssetManager'
    # bl_options = {'DEFAULT_CLOSED'}
    # bl_order = 0

    def draw_settings(self, context,layout):
        am_settings_tabs = context.scene.asset_manager_settings_tabs.switch_tabs
        if am_settings_tabs == 'tool_settings':
            self.draw_base_settings(context,layout)

        if am_settings_tabs == 'render_settings':
            self.draw_render_settings(context,layout)


    def draw_base_settings(self,context,layout):
        addon_prefs = addon_info.get_addon_prefs()
        asset_props =context.scene.asset_props
        row = layout.row(align=True)
        row.prop(addon_prefs,'thumb_upload_path',text = 'Asset preview folder')

        row = layout.row(align=True)
        row.prop(asset_props,'exclude_extras',text='Exclude Extras')
        row.prop(asset_props,'debug',text='Debug')



    def draw_render_settings(self,context,layout):
        asset_props =context.scene.asset_props
        row = layout.row(align=True)
        row.template_icon_view(context.scene, "light_setup",scale=8,scale_popup=8)
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Light Setup: " + context.scene.light_setup.removesuffix('.png'))

        col = layout.column(align=False)
        col.alignment = 'CENTER'

        col.prop(asset_props, "enable_backdrop", text="Enable Background",icon='IMAGE_BACKGROUND')
        if context.scene.asset_props.enable_backdrop:
            row = col.row(align=True)
            row.prop(asset_props, "backdrop_color", text="Background Color")
            row = col.row(align=True)
            row.prop(asset_props, "emissive_strength", text="Emissive Strength")
            col.separator(factor=1)
        col.prop(asset_props, "background_transparent", text='Transparent ',toggle=False)
        col.prop(asset_props, "enable_ub_logo", text="Render with UniBlend Logo",toggle=False)



class UB_PT_AssetManager_UIList(bpy.types.Panel,AssetManager_settings):
    bl_idname = "UB_PT_AssetManager_UIList"
    bl_label = "Asset List"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "UB_PT_AssetManager"
    bl_category = "UniBlend"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1
    render_scene = None
    
    @classmethod
    def poll(cls, context):
        return True
       
    def draw(self, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            self.render_scene = bpy.data.scenes.get('PreviewRenderScene')
        
        asset_props =context.scene.asset_props
        am_settings_tabs = context.scene.asset_manager_settings_tabs
        layout = self.layout
        # selected_assets = bpy.context.selected_objects
        # set_selected_assets(selected_assets)
        selected_assets =get_selected_assets()
      
        layout.separator(factor=1)
        settings_box = layout.box()
        col = settings_box.column(align=True)
        row = col.row(align=True) 
        for enum_item in am_settings_tabs.bl_rna.properties['switch_tabs'].enum_items:
            row.prop_enum(am_settings_tabs, "switch_tabs", enum_item.identifier, text=enum_item.name)
        self.draw_settings(context,col)
        camera_ui_text = "Adjust Camera" if not asset_props.adjust_camera else "Confirm Adjustments"
        col.operator("ub.adjust_preview_camera",text=camera_ui_text,icon="VIEW_CAMERA",depress=asset_props.adjust_camera)
        if asset_props.adjust_camera:
            settings_box.prop(asset_props, "use_asset_example_rotation", text="Use Asset Example Rotation for render",toggle=False)

        assets_box = layout.box()
        assets_box.enabled = len(selected_assets) > 0 
        row = assets_box.row(align=True)
        row.alignment = 'CENTER'
        
        if selected_assets:
            status_text = 'Selected Assets'
        elif asset_props.is_rendering:
            status_text = 'Rendering Previews'
        elif asset_props.adjust_camera:
            status_text = 'Adjusting Camera'
        else:
            status_text = 'Select assets in the viewport to begin!'
        
        assets_col = assets_box.column(align=False)


        split = assets_col.split(align=True)
        row = split.row(align=False)
        row.prop(asset_props,'asset_types',expand=False,text='')

        row = split.row()
        row.alignment = 'RIGHT'
        # rtype,rname,icon =asset_props.render_types
        row.operator('ub.render_previews', text="Render Previews", icon='OUTPUT')

        if asset_props.asset_types in ('Material Nodes','Materials'):
            row = col.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(asset_props,'render_types',expand=True,icon_only=True)

        row = assets_col.row(align=True)
        row.alignment = 'CENTER'
        row.label(text=status_text)
        row = assets_col.row(align=True)
        row.alignment='RIGHT'
        row.operator('ub.mark_assets', text="Mark all", icon='ASSET_MANAGER')
        row.operator('ub.unmark_assets', text="Unmark all", icon='CANCEL')
        row = assets_col.row(align=True)
        assets_to_filter = selected_assets if not asset_props.is_rendering else [selected.asset for selected in asset_props.selected]
        filtered_hierarchy = filter_assets(assets_to_filter, asset_props.asset_types)
        render_asset_hierarchy(assets_box, filtered_hierarchy,asset_props.asset_types)
        # print_hierarchy(filtered_hierarchy)

def print_hierarchy(hierarchy, level=0):
  for item in hierarchy:
      print("  " * level + f"{item.asset_type}: {item.asset.name}")
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

class UB_OT_ClearParent(bpy.types.Operator):
    '''Create a copy of the asset, unlink it from the parent object'''
    bl_idname = "ub.object_clear_parent"
    bl_label = "Clear Parent"
    bl_options = {'REGISTER', 'UNDO'}

    asset_name: bpy.props.StringProperty()
    asset_type: bpy.props.StringProperty()

    def execute(self, context):
        selected_assets = get_selected_assets()
        asset = get_asset_from_datatype(self.asset_name,self.asset_type)
        if asset:
            print(self.asset_type)
            if self.asset_type == 'Object':
                if asset.parent_type == 'OBJECT':
                    for idx,sel_asset in enumerate(selected_assets):
                        if sel_asset.name == asset.name:
                            
                            selected_assets.pop(idx)
                            obj_copy = self.duplicate(asset,data=True,actions=False,collection =bpy.context.collection)
                            selected_assets.insert(idx,obj_copy)
                            obj_copy.location =(0,0,0)
                            asset.select_set(False)
                            obj_copy.select_set(True)
        return {'FINISHED'}
    
    def duplicate(self,obj, data=True, actions=True, collection=None):
        obj_copy = obj.copy()
        if data:
            obj_copy.data = obj_copy.data.copy()
        if actions and obj_copy.animation_data:
            obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
        collection.objects.link(obj_copy)
        obj_copy.parent = None
        return obj_copy

classes=(
    UB_PT_AssetManager,
    UB_PT_AssetManager_UIList,
    UB_OT_MinimizeAssetDetails,
    UB_OT_RemoveFromList,
    UB_OT_ClearParent,
    E_AssetManagerSettings,
    
    )

register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
    bpy.types.Scene.asset_manager_settings_tabs = bpy.props.PointerProperty(type=E_AssetManagerSettings)
   
def unregister():
    unregister_classes()