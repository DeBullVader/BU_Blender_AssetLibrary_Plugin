import bpy,os
from ..utils import addon_info,version_handler
from .asset_manager_utils import *
from bpy.utils import register_classes_factory

class UB_PT_AssetManager_UIList(bpy.types.Panel):
    bl_idname = "UB_PT_AssetManager_UIList"
    bl_label = "Asset List"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETLIBRARYTOOLS"
    bl_category = "UniBlend"
    bl_options = {'DEFAULT_CLOSED'}

    render_scene = None
    
    @classmethod
    def poll(cls, context):
        return True
    
    def asset_manager_settings_ui(self, context,layout):
        asset_props =get_asset_props()
        addon_prefs = addon_info.get_addon_prefs()
        box = layout.box()
        box.label(text='Settings')
        row = box.row()
        row.prop(addon_prefs,'thumb_upload_path',text = 'Asset preview folder')
        row = box.row(align=True)
        
        row.prop(asset_props,'exclude_extras',text='Exclude Extras')
        row.prop(asset_props,'debug',text='Debug')
        row = box.row(align=True)
        row.alignment = 'RIGHT'
        row.alert = True
        row.operator('temp.clear_render_scene', text="Reset", icon='CANCEL')

        row = box.row(align=True)
        row.template_icon_view(context.scene, "light_setup",scale=8,scale_popup=8)
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Light Setup: " + bpy.context.scene.light_setup.removesuffix('.png'))

        col = box.column(align=False)
        col.alignment = 'CENTER'

        col.prop(asset_props, "enable_backdrop", text="Enable Background",icon='IMAGE_BACKGROUND')
        if context.scene.asset_props.enable_backdrop:
            row = col.row(align=True)
            # row.label(text="Background Color:")
            row.prop(asset_props, "backdrop_color", text="Background Color")
            row = col.row(align=True)
            row.prop(asset_props, "emissive_strength", text="Emissive Strength")
            col.separator(factor=1)
        col.prop(asset_props, "background_transparent", text='Transparent ',toggle=False)
        col.prop(asset_props, "enable_ub_logo", text="Render with UniBlend Logo",toggle=False)
        col.separator(factor=1)

        
        camera_ui_text = "Adjust Camera" if not asset_props.adjust_camera else "Confirm Adjustments"
        col.operator("ub.adjust_preview_camera",text=camera_ui_text,icon="VIEW_CAMERA",depress=asset_props.adjust_camera)
        if asset_props.adjust_camera:
            if 'PreviewRenderScene' in bpy.data.scenes:
                object_cam = bpy.data.objects['Camera_Objects']
                row =col.row()
                row.prop(object_cam, "location", text="Location", icon="CAMERA_DATA")
                row =col.row()
                row.prop(object_cam, "rotation_euler", text="Rotation", icon="CAMERA_DATA")
        row = layout.row(align=True)

    def draw(self, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            self.render_scene = bpy.data.scenes.get('PreviewRenderScene')
        
        asset_props =context.scene.asset_props
        layout = self.layout
        # selected_assets = bpy.context.selected_objects
        # set_selected_assets(selected_assets)
        selected_assets =get_selected_assets()
        self.asset_manager_settings_ui(context,layout)
      
        layout.separator(factor=1)
        box = layout.box()
        row = box.row(align=True)
        split = row.split(align=True)
        row = split.row(align=True)
        row.alignment = 'LEFT'
        row.scale_y = 1.420
        row.enabled = len(selected_assets) > 0
        row.operator('ub.mark_assets', text="Mark Assets", icon='ASSET_MANAGER')
        row.operator('ub.unmark_assets', text="Unmark Assets", icon='CANCEL')
        # row.separator(factor=5)
        row = split.row(align=True)
        row.scale_y = 1.420
        row.alignment = 'RIGHT'
        row.operator('ub.render_previews', text="Render Previews", icon='OUTPUT')

        box.separator(factor=1)
        row = box.row(align=True)
        row.alignment = 'CENTER'

        if selected_assets:
            status_text = 'Selected Assets'
        elif asset_props.is_rendering:
            status_text = 'Rendering Previews'
        elif asset_props.adjust_camera:
            status_text = 'Adjusting Camera'
        else:
            status_text = 'Select assets in the viewport to begin!'
        row.label(text=status_text)

        row = box.row(align=True)
        row.scale_y = 1.420
        row.prop(asset_props,'asset_types',expand=False)
        
        if asset_props.asset_types in ('Material Nodes','Materials'):
            row = box.row(align=True)
            row.alignment = 'RIGHT'
            # rtype,rname,icon =asset_props.render_types
            row.prop(asset_props,'render_types',expand=True,icon_only=True)
        
        assets_to_filter = selected_assets if not asset_props.is_rendering else [selected.asset for selected in asset_props.selected]
        filtered_hierarchy = filter_assets(assets_to_filter, asset_props.asset_types)
        render_asset_hierarchy(box, filtered_hierarchy,asset_props.asset_types)
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
    UB_PT_AssetManager_UIList,
    UB_OT_MinimizeAssetDetails,
    UB_OT_RemoveFromList,
    UB_OT_ClearParent,
    )

register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
   
def unregister():
    unregister_classes()