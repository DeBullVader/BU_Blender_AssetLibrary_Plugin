import bpy
import os
from ...utils import addon_info,asset_bbox_logic
from bpy.props import *
from bpy_extras import object_utils
from math import *
from mathutils import *
import bpy.utils.previews
from .asset_manager_utils import *
from .asset_manager_render_strategy import *


object_utils.world_to_camera_view

def update_exclude_items(self,context):
    AssetOperations.exclude_list = []
    AssetOperations.minimized_list = []

class SelectedAssets(bpy.types.PropertyGroup):
    asset:PointerProperty(name='Selected Assets', type=bpy.types.ID)

class AssetProperties(bpy.types.PropertyGroup):
    asset_types: EnumProperty(items=get_types() ,name ='Type', description='asset types',update=update_exclude_items)
    render_types: EnumProperty(items=get_render_types() ,name ='Render Type',default='Mat_Shaderball', description='get_render_types')
    exclude_extras: BoolProperty(name='Exclude Extras', default=True)
    enable_backdrop:BoolProperty(name="Enable Backdrop", default=False)
    backdrop_color:FloatVectorProperty(name="Backdrop Color", default=(1.0,1.0,1.0,1.0),subtype='COLOR', size=4,soft_min=0.0, soft_max=1.0)
    emissive_strength:FloatProperty(name="Emissive Strength", default=1.4,soft_min=0.0, soft_max=2.0)
    background_transparent:BoolProperty(name="Background Transparent", default=False)
    enable_ub_logo:BoolProperty(name="Enable UniBlend Logo", default=False)
    adjust_camera:BoolProperty(name="Adjust Camera", default=False)
    selected:CollectionProperty(type=SelectedAssets)
    rendered_assets:CollectionProperty(type=SelectedAssets)
    max_scale:FloatVectorProperty(name="Max Scale", default=(1.25,1.25,1.25),size=3,soft_min=0.0, soft_max=2.0,subtype='XYZ')
    use_asset_example_rotation:BoolProperty(name="Use Asset Example Rotation", default=False,description="Use the Preview asset rotation for rendering")
    asset_example:PointerProperty(name="Asset Example", type=bpy.types.Object)
    asset_example_rotation:FloatVectorProperty(name="Asset Example Rotation", default=(0.0, 0.0, 0.0),subtype='EULER', size=3)
    asset_example_location:FloatVectorProperty(name="Asset Example Location", default=(0.0, 0.0, 0.0),subtype='XYZ', size=3)
    render_camera:PointerProperty(name="Object Camera", type=bpy.types.Object)
    render_camera_rotation:FloatVectorProperty(name="Object Camera Rotation", default=(1.5312, 0.0, 0.0749),subtype='EULER', size=3)
    render_camera_location:FloatVectorProperty(name="Object Camera Location", default=(0.0, 0.0, 0.0),subtype='XYZ', size=3)
    original_camera:PointerProperty(name="Original Camera", type=bpy.types.Object)
    original_scene_res:IntVectorProperty(name="Original Scene Resolution", default=(1920,1080,0),size=3,subtype='XYZ')
    is_rendering:BoolProperty(default=False)
    debug:BoolProperty(default=False)


class UB_OT_Pivot_Bottom_Center(bpy.types.Operator):
    bl_idname = "ub.pivot_bottom_center"
    bl_label = "Pivot Bottom Center"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0
    
    def execute(self, context):
        for obj in context.selected_objects:
            cursor_original_loc = bpy.context.scene.cursor.location.xyz
            location_vector = asset_bbox_logic.get_bottom_center_extent(obj)
            bpy.context.scene.cursor.location = Vector(location_vector)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            bpy.context.scene.cursor.location.xyz = cursor_original_loc
        return {'FINISHED'}

    
class UB_OT_AdjustPreviewCamera(bpy.types.Operator):
    '''Adjust the preview render camera with an example object'''
    bl_idname = "ub.adjust_preview_camera"
    bl_label = "Adjust Preview Camera"
    bl_options = {'REGISTER', 'UNDO'}

    toggled:BoolProperty(name="Toggled", default=False)
    example_assets=[]

    def isolate_selected(self, context,camera,asset):
      
        selected_assets =context.scene.asset_props.selected
        if self.toggled:
            if selected_assets:
                for item in selected_assets:
                    item.asset.select_set(False)
            
            camera.select_set(True)
            asset.select_set(True)
            bpy.ops.view3d.localview()
            print(camera.name, camera.rotation_euler)
            align_camera_to_selected_asset(camera)
            camera.select_set(False)
            
            asset.select_set(False)
            area = next(area for area in context.screen.areas if area.type == 'VIEW_3D')
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            area.spaces[0].lock_camera = True
            
        else:
            bpy.ops.view3d.localview()
            camera.select_set(False)
            asset.select_set(False)
            if selected_assets:
                for item in selected_assets:
                    item.asset.select_set(True)          
            area = next(area for area in context.screen.areas if area.type == 'VIEW_3D')
            area.spaces[0].region_3d.view_perspective = 'PERSP'
            area.spaces[0].lock_camera = False
            
        
    def cleanup_current_scene(self, context):
        preview_col = bpy.data.collections.get('UB_Preview_Col')
        if preview_col:
            if preview_col.objects:
                for obj in preview_col.objects:
                    bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.collections.remove(preview_col, do_unlink=True)
        context.scene.asset_props.selected.clear()
        context.scene.camera = context.scene.asset_props.original_camera
        context.scene.asset_props.adjust_camera = False
        context.scene.render.resolution_x = context.scene.asset_props.original_scene_res[0]
        context.scene.render.resolution_y = context.scene.asset_props.original_scene_res[1]

        remove_preview_render_scene()

    def setup_adjustment_objects(self,context):
        preview_col = bpy.data.collections.new('UB_Preview_Col')
        context.scene.collection.children.link(preview_col)
        
        cam =bpy.data.cameras.new('UB_Preview_Camera')
        camera_obj = bpy.data.objects.new('UB_Preview_Camera', cam)
        bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0.5),scale=(1, 1, 1))
        bpy.context.active_object.name = 'UB_Preview_Asset'
        bpy.ops.object.shade_smooth()
        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.ops.object.subdivision_set(level=1)

        asset_example = bpy.data.objects.get('UB_Preview_Asset')
        asset_example.show_name = True
        asset_example.rotation_euler = context.scene.asset_props.asset_example_rotation
        preview_col.objects.link(camera_obj)
        asset_example.users_collection[0].objects.unlink(asset_example)
        preview_col.objects.link(asset_example)

        context.scene.asset_props.render_camera = camera_obj
        context.scene.asset_props.asset_example = asset_example
        context.scene.asset_props.original_camera = context.scene.camera
        context.scene.camera = camera_obj
        context.scene.camera.rotation_euler = context.scene.asset_props.render_camera_rotation
        context.scene.asset_props.original_scene_res = (context.scene.render.resolution_x,context.scene.render.resolution_y,0)
        
        
    def execute(self, context):
        if not self.toggled:
            selected_assets = get_selected_assets()
            if selected_assets:
                asset_names =(item.asset.name for item in context.scene.asset_props.selected)        
                for asset in selected_assets:
                    if asset.name not in asset_names:
                        add_selected =context.scene.asset_props.selected.add()
                        add_selected.asset = asset

            self.setup_adjustment_objects(context)            
            context.scene.render.resolution_x = 256
            context.scene.render.resolution_y = 256
            self.toggled = True
            context.scene.asset_props.adjust_camera = True
            
            self.isolate_selected(context,context.scene.asset_props.render_camera,context.scene.asset_props.asset_example)
        else:
            self.toggled = False
            context.scene.asset_props.asset_example_rotation = context.scene.asset_props.asset_example.rotation_euler
            preview_col = bpy.data.collections.get('UB_Preview_Col')
            if preview_col:
                self.isolate_selected(context,context.scene.asset_props.render_camera,context.scene.asset_props.asset_example)
                self.cleanup_current_scene(context)
            
        return {'FINISHED'}
    


    


class UB_OT_RenderPreviews(bpy.types.Operator):
    bl_idname = "ub.render_previews"
    bl_label = "Render Previews"
    
    _timer = None
    preview_filenames = None
    stop = None
    rendering = None
    asset_preview_path = None
    ph_asset_preview_path = None
    assets_to_render = []
    preview_col = None
    render_scene = None
    original_cam = None
    material_container = None
    shaderball_container = None
    object_container = None
    current_pivot_transform = None
    asset_props = None

    def __init__(self):
        self.state = 'INIT'

    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_prefs()
        asset_props = context.scene.asset_props
        if asset_props.adjust_camera:
            cls.poll_message_set('Adjust Camera is active')
            return False
        if not os.path.exists(addon_prefs.thumb_upload_path):
            cls.poll_message_set('Thumbnail upload path not found')
            return False
        return True
        
    def pre(self, scene='PreviewRenderScene', context=None):
        print("Render pre-handler called")
        self.rendering = True
        
    def post(self, scene='PreviewRenderScene', context=None):
        print("Render post-handler called")
        self.remove_ph_padding()
        asset = self.object_container.objects.get(self.assets_to_render[0].name+'_to_render')
        if asset:
            asset.hide_render = True
            self.object_container.objects.unlink(asset)
        self.preview_filenames.pop(0)
        rendered_asset =bpy.context.scene.asset_props.rendered_assets.add()
        rendered_asset.asset = self.assets_to_render[0]
        self.assets_to_render.pop(0)             
        self.rendering = False

    def cancelled(self, scene='PreviewRenderScene', context=None):
        self.stop = True


        

    def initialize_render_process(self, context):
        self.stop = False
        self.rendering = False
        self.preview_filenames = []
        self.assets_to_render = []
        self.asset_preview_path = addon_info.get_asset_preview_path()
        self.ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()

        #TODO: Move backup and restore backup settings to own scene stored propertygroup
        self.asset_props = context.scene.asset_props
        self.asset_props.original_scene_res = (context.scene.render.resolution_x, context.scene.render.resolution_y, 0)

        self.original_cam = context.scene.camera

    def setup_current_scene(self, context):
        #adjust current scene temporarily for the render process
        context.scene.render.resolution_x = 256
        context.scene.render.resolution_y = 256
        if context.scene.asset_props.asset_types in ('Objects','Collections','Geometry Nodes'):
            self.preview_col = setup_preview_col(context)
            if self.asset_props.render_camera is not None:
                if self.asset_props.render_camera.name not in self.preview_col.objects:
                    self.preview_col.objects.link(self.asset_props.render_camera)
        
            context.scene.camera = self.asset_props.render_camera
        
    def setup_render_scene(self, context):
        self.render_scene = import_render_scene(context)
        if self.render_scene is None:
            print('Preview Render Scene not found')
            raise Exception('Preview Render Scene not found')
        
        asset_types = context.scene.asset_props.asset_types
        object_cam_types = ('Objects','Collections','Geometry Nodes')
        render_cam_name = 'Camera_Objects' if asset_types in object_cam_types else 'Camera_Materials'

        context.scene.asset_props.render_camera = next((obj for obj in self.render_scene.objects if obj.name.startswith(render_cam_name)), None)
        context.scene.asset_props.asset_example = next((obj for obj in self.render_scene.objects if obj.name.startswith('BU_Example_Asset')), None)
        self.render_scene.camera = context.scene.asset_props.render_camera

        self.material_container = next((col for col in self.render_scene.collection.children if col.name.startswith('Material_Container')), None)
        self.object_container = next((col for col in self.render_scene.collection.children if col.name.startswith('Object_Container')), None)

        render_scene_items=(
            context.scene.asset_props.asset_example,
            context.scene.asset_props.render_camera,
            self.material_container,
            self.object_container
        )
        if any(item is None for item in render_scene_items):
            raise Exception("Required collections or objects not found in the imported scene")

        self.material_container.hide_render = True
        self.object_container.hide_render = True

        set_light_settings(self,context)
        set_render_settings(self,context)
        setup_compositer_links(self,context)
    
    def prepare_assets_for_render(self, context):
        print('prepare_assets_for_render')
        selected_assets = get_selected_assets()
        for asset in selected_assets:
            add_selected = self.asset_props.selected.add()
            add_selected.asset = asset
            asset.select_set(False)
        asset_type = context.scene.asset_props.asset_types
        filtered_hierarchy = filter_assets(selected_assets, asset_type)
        print('asset_type: ',asset_type)
        if asset_type == 'Geometry Nodes':
            self.get_geo_assets_to_render_from_hierarchy(context,filtered_hierarchy,asset_type)
        else:
            self.get_assets_to_render_from_hierarchy(context,filtered_hierarchy,asset_type)

    def get_assets_to_render_from_hierarchy(self, context,hierarchy, asset_type):
        for item in hierarchy:
            if item and hasattr(item, 'asset') and item.asset:
                if item.asset_type == asset_type and not item.children:
                    if not AssetOperations.is_excluded(item.asset):
                        self.preview_filenames.append(f'preview_{item.asset.name}.png')
                        self.assets_to_render.append(item.asset)
                if hasattr(item, 'children') and item.children:
                    self.get_assets_to_render_from_hierarchy(context, item.children, asset_type)

    def get_geo_assets_to_render_from_hierarchy(self, context,hierarchy, asset_type):
        for item in hierarchy:
            if item and hasattr(item, 'asset') and item.asset:
                if item.asset_type == 'Objects':
                    for modifier in item.asset.modifiers:
                        if modifier.type == 'NODES':
                            if not AssetOperations.is_excluded(modifier.node_group):
                                self.preview_filenames.append(f'preview_{modifier.node_group.name}.png')
                                self.assets_to_render.append(item.asset)
     

    def setup_render_handlers(self, context):
        bpy.app.handlers.render_pre.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.cancelled)
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        print('Setup Render Handlers')


    def create_copy_of_current_asset(self, asset):
        if asset.name+'_to_render' not in bpy.data.objects:
            copy = asset.copy()
            copy.name = asset.name+'_to_render'
        else:
            copy = bpy.data.objects.get(asset.name+'_to_render')
        return copy


    def link_to_object_container(self, asset):
        if asset.name not in self.object_container.objects:
            self.object_container.objects.link(asset)
        self.preview_col.objects.unlink(asset)



    def cleanup_render_process(self, context):
        print('Cleaning up render process')
        if self.pre in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(self.pre)
        if self.post in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(self.post)
        if self.cancelled in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(self.cancelled)

        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        # Clean up objects in the object container and preview collection
        if self.object_container:
            for obj in self.object_container.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            
        if self.preview_col:
            bpy.data.collections.remove(self.preview_col, do_unlink=True)
        
        # Restore original camera
        context.scene.camera = self.original_cam if self.original_cam else None
        for rendered_asset in context.scene.asset_props.rendered_assets:
            if rendered_asset.asset.asset_data:
                assign_previews(context,rendered_asset.asset)
        for selected_asset in context.scene.asset_props.selected:
            selected_asset.asset.select_set(True)
  

        # Clear selected assets, Restore original render resolution
        context.scene.asset_props.selected.clear()
        context.scene.asset_props.rendered_assets.clear()
        context.scene.render.resolution_x = self.asset_props.original_scene_res[0]
        context.scene.render.resolution_y = self.asset_props.original_scene_res[1]
        
        # Remove the imported PreviewRenderScene
        remove_preview_render_scene()
        print('Render process cleanup completed')

    def debug_render(self, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            center_point = bpy.data.objects.get('Center_Point')
            scale_range = bpy.data.objects.get('Preview_Scale_Range')
            if context.scene.asset_props.debug:
                center_point.hide_render = False
                scale_range.hide_render = False
            else:
                center_point.hide_render = True
                scale_range.hide_render = True
    
    def set_ph_asset_path(self):
        nodes = self.render_scene.node_tree.nodes
        self.render_scene.frame_current = 0
        ph_out = nodes.get('File_PH_Out')
        ph_filepath =  os.path.join(self.ph_asset_preview_path,'PH_preview_' + self.assets_to_render[0].name + '.png')
        if os.path.exists(ph_filepath):
            os.remove(ph_filepath)
        ph_out.file_slots[0].path = os.path.join(self.ph_asset_preview_path,'PH_preview_' + self.assets_to_render[0].name + '#.png')

    def remove_ph_padding(self):
        asset_name =self.assets_to_render[0].name
        padded_path = os.path.join(self.ph_asset_preview_path,'PH_preview_' + asset_name + '1.png')
        correct_name = 'PH_preview_' + asset_name + '.png'
        if os.path.exists(padded_path):
           os.rename(padded_path,os.path.join(os.path.join(self.ph_asset_preview_path,correct_name)))

    def render_next_asset(self, context):
        try:
            print('Rendering next previews')
            if not self.assets_to_render:
                print("No more assets to render")
                self.state = 'FINISHED'
                return
            print(f"{len(self.assets_to_render)} assets left to render")
            self.debug_render(context)
            asset = self.assets_to_render[0]
            
            current_pivot_transform = asset_bbox_logic.get_current_transform_pivotpoint()
            asset_bbox_logic.set_transform_pivot_point_to_bound_center()

            strategies = {
                'Objects': ObjectRenderStrategy(),
                'Materials': MaterialRenderStrategy(),
                'Collections': CollectionRenderStrategy(),
                'Material Nodes': MaterialNodeRenderStrategy(),
                'Geometry Nodes': GeometryNodeRenderStrategy(),
                # Add more strategies when implemented
            }

            asset_type = context.scene.asset_props.asset_types
            strategy = strategies.get(asset_type)
            if strategy:
                strategy.setup_render_type(context, asset, self)
            else:
                print(f"Unsupported asset type: {asset_type}")
                return
            
            asset_bbox_logic.restore_pivot_transform(current_pivot_transform)

            self.set_ph_asset_path()
            self.render_scene.render.filepath = self.asset_preview_path + self.preview_filenames[0]
            bpy.ops.render.render(scene='PreviewRenderScene', write_still=True, use_viewport=True)
        # TODO: Add exception handling for failed renders, use exceptions where needed not everywhere
        except Exception as e:
            print(f"Error rendering asset {asset.name}: {e}")
            self.cancelled('PreviewRenderScene', None)

    def execute(self, context):
        try:
            self.initialize_render_process(context)
            self.setup_render_scene(context)
            self.setup_current_scene(context)
            self.prepare_assets_for_render(context)
            self.setup_render_handlers(context)
            self.asset_props.is_rendering = True
            context.window_manager.modal_handler_add(self)
            print('Setup Render Handlers completed')
            return {"RUNNING_MODAL"}
        except Exception as e:
            print(f"Error in render preview execute: {e}")
            self.cleanup_render_process(context)
            return {'CANCELLED'}
    
    def modal(self, context, event):
        try:
            if event.type == 'TIMER':
                print(f"Modal state: {self.state}")
                if self.state == 'INIT':
                    self.state = 'RENDERING'
                    self.render_next_asset(context)
                if self.state == 'FINISHED':
                    self.cleanup_render_process(context)
                    self.asset_props.is_rendering = False
                    return {"FINISHED"}
                
                elif self.state == 'RENDERING':
                    print('Rendering Preview: ',self.preview_filenames)
                    if True in (not self.preview_filenames, self.stop is True):
                        self.cleanup_render_process(context)
                        self.state = 'FINISHED'
                        self.asset_props.is_rendering = False
                        return {"FINISHED"}
                    elif not self.rendering:
                        self.render_next_asset(context)
            return {"PASS_THROUGH"}
        except Exception as e:
           print(f"Error in modal function: {e}")
           self.cleanup_render_process(context)
           return {"CANCELLED"}
    
classes=(
    SelectedAssets,
    AssetProperties,
    UB_OT_RenderPreviews,
    UB_OT_AdjustPreviewCamera,
    UB_OT_Pivot_Bottom_Center,
    )

register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
    bpy.types.Scene.light_setup = bpy.props.EnumProperty(items=gen_light_setup_previews(),)
    bpy.types.Scene.asset_props = bpy.props.PointerProperty(type=AssetProperties)

    
def unregister():
    unregister_classes()
    del bpy.types.Scene.asset_props
    del bpy.types.Scene.light_setup