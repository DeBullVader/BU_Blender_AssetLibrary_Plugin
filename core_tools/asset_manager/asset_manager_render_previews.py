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


# object_utils.world_to_camera_view

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


class UB_Preview_Defaults():
    def __init__(self):
        self.asset_props = bpy.context.scene.asset_props
        self.preview_col = self.get_or_create('collections','UB_Preview_Col')
        self.cam =self.get_or_create('cameras', 'UB_Preview_Camera')
        self.render_camera = self.get_or_create('objects', 'UB_Preview_Camera', self.cam)
        if bpy.context.scene.camera:
            if bpy.context.scene.camera.name != 'UB_Preview_Camera':
                self.original_camera_name = bpy.context.scene.camera.name
        else:
            self.original_camera_name = ''
        self.asset_example = None
        self.original_scene_res = (bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y,0)
    
    def get_or_create(self,data_type, name, *args, **kwargs):
        data_collection = getattr(bpy.data, data_type)
        item = data_collection.get(name)
        if item is None:
            if data_type =='objects':
                item = data_collection.new(name, *args)
                return item
            item = data_collection.new(name)
        return item 
    
class UB_OT_AdjustPreviewCamera(bpy.types.Operator,UB_Preview_Defaults):
    '''Adjust the preview render camera with an example object'''
    bl_idname = "ub.adjust_preview_camera"
    bl_label = "Adjust Preview Camera"
    bl_options = {'REGISTER', 'UNDO'}

    __slots__ = (
        "asset_props",
        "asset_example",
        "preview_col",
        "cam",
        "render_camera",
        "original_scene_res"
    )
    toggled:BoolProperty(name="Toggled", default=False)
    original_camera_name:StringProperty()
    active_asset_name:StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' 
    
        
    def invoke(self,context,event):
        super().__init__()
        return self.execute(context)

    def create_asset_example(self):
        if 'UB_Preview_Asset' in bpy.data.objects:
            self.asset_example = bpy.data.objects.get('UB_Preview_Asset')
            return
        bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0.5),scale=(1, 1, 1))
        bpy.context.active_object.name = 'UB_Preview_Asset'
        bpy.ops.object.shade_smooth()
        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.ops.object.subdivision_set(level=1)
        self.asset_example = bpy.data.objects.get('UB_Preview_Asset')
        self.asset_example.show_name = True
        self.asset_example.rotation_euler = self.asset_props.asset_example_rotation
        return 

    def isolate_selected(self, context):
      
        selected_assets =self.asset_props.selected
        if self.toggled:
            if selected_assets:
                for item in selected_assets:
                    item.asset.select_set(False)
            
            self.render_camera.select_set(True)
            self.asset_example.select_set(True)
            bpy.ops.view3d.localview()
            align_camera_to_selected_asset(self.render_camera)
            self.render_camera.select_set(False)
            
            self.asset_example.select_set(False)
            area = next(area for area in context.screen.areas if area.type == 'VIEW_3D')
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            area.spaces[0].lock_camera = True
            
        else:
            bpy.ops.view3d.localview()
            self.render_camera.select_set(False)
            self.asset_example.select_set(False)
            if selected_assets:
                for item in selected_assets:
                    item.asset.select_set(True)
                    if self.active_asset_name != '' and item.asset.name == self.active_asset_name:
                        context.view_layer.objects.active = item.asset          
            area = next(area for area in context.screen.areas if area.type == 'VIEW_3D')
            area.spaces[0].region_3d.view_perspective = 'PERSP'
            area.spaces[0].lock_camera = False
            
        
    def cleanup_current_scene(self, context):
        if self.preview_col:
            if self.preview_col.objects:
                for obj in self.preview_col.objects:
                    bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.collections.remove(self.preview_col, do_unlink=True)
        self.asset_props.selected.clear()
        original_camera = bpy.data.objects.get(self.original_camera_name)
        if original_camera:
            context.scene.camera = original_camera
        self.asset_props.adjust_camera = False
        context.scene.render.resolution_x = self.original_scene_res[0]
        context.scene.render.resolution_y = self.original_scene_res[1]
        remove_preview_render_scene()

    def setup_adjustment_objects(self,context):
        context.scene.collection.children.link(self.preview_col)
        self.preview_col.objects.link(self.render_camera)
        self.asset_example.users_collection[0].objects.unlink(self.asset_example)
        self.preview_col.objects.link(self.asset_example)
        context.scene.camera = self.render_camera
        self.render_camera.rotation_euler = self.asset_props.render_camera_rotation
        
        
        
    def execute(self, context):
        
        if not self.toggled:
            selected_assets = get_selected_assets()
            if selected_assets:
                asset_names =(item.asset.name for item in self.asset_props.selected)        
                for asset in selected_assets:
                    if asset.name == context.view_layer.objects.active.name:
                        self.active_asset_name = asset.name
                    if asset.name not in asset_names:
                        add_selected =self.asset_props.selected.add()
                        add_selected.asset = asset
            self.create_asset_example()
            self.setup_adjustment_objects(context)            
            context.scene.render.resolution_x = 256
            context.scene.render.resolution_y = 256
            self.toggled = True
            self.asset_props.adjust_camera = True
            self.isolate_selected(context)
        else:
            self.toggled = False
            self.create_asset_example()
            self.asset_props.render_camera_rotation = self.render_camera.rotation_euler
            if self.asset_example:
                self.asset_props.asset_example_rotation = self.asset_example.rotation_euler
            if self.preview_col:
                self.isolate_selected(context)
                self.cleanup_current_scene(context)
        return {'FINISHED'}
    


    


class UB_OT_RenderPreviews(bpy.types.Operator,UB_Preview_Defaults):
    bl_idname = "ub.render_previews"
    bl_label = "Render Previews"
    
    ph_asset_preview_path = None
    assets_to_render = []
    render_scene = None
    material_container = None
    shaderball_container = None
    object_container = None
    current_pivot_transform = None
    original_camera_name:StringProperty()

    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_prefs()
        if context.scene.asset_props.adjust_camera:
            cls.poll_message_set('Adjust Camera is active')
            return False
        if not os.path.exists(addon_prefs.thumb_upload_path):
            cls.poll_message_set('Thumbnail upload path not found')
            return False
        return True
    
    def invoke(self, context, event):
        # print("Invoke Render Previews")
        super().__init__()
        self.state = 'INIT'
        self._timer = None
        
        self.stop = False
        self.rendering = False
        self.preview_filenames = []
        self.assets_to_render = []
        self.asset_preview_path = addon_info.get_asset_preview_path()
        self.ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
        self.setup_scenes(context)
        self.prepare_assets_for_render(context)
        self.setup_render_handlers(context)
        return self.execute(context)
        
    def pre(self, scene='PreviewRenderScene', context=None):
        # print("Render pre-handler called")
        self.rendering = True
        
    def post(self, scene='PreviewRenderScene', context=None):
        # print("Render post-handler called")
        self.remove_ph_padding()
        asset = self.render_scene['Object_Container'].objects.get(self.assets_to_render[0].name+'_to_render')
        if asset:
            # asset.hide_render = True
            self.render_scene['Object_Container'].objects.unlink(asset)
        self.preview_filenames.pop(0)
        rendered_asset =bpy.context.scene.asset_props.rendered_assets.add()
        if hasattr(self.assets_to_render[0], 'type') and self.assets_to_render[0].type == 'GROUP':
            rendered_asset.asset = self.assets_to_render[0].node_tree
        else:
            rendered_asset.asset = self.assets_to_render[0]
        self.assets_to_render.pop(0)             
        self.rendering = False

    def cancelled(self, scene='PreviewRenderScene', context=None):
        self.stop = True

    # def setup_current_scene(self, context):


    def setup_scenes(self, context):
        self.render_scene = import_render_scene(context)
        if self.render_scene is None:
            print('Preview Render Scene not found')
            raise Exception('Preview Render Scene not found')
        
        #adjust current scene temporarily for the render process
        context.scene.render.resolution_x = 256
        context.scene.render.resolution_y = 256
        object_cam_types = ('Objects','Collections','Geometry Nodes')
        asset_type = context.scene.asset_props.asset_types
        self.preview_col = setup_preview_col(context)
        if asset_type in object_cam_types:
           
            self.render_camera =self.render_scene['Camera_Objects']
            self.preview_col.objects.link(self.render_camera)
            context.scene.camera = self.render_camera
        else:
            self.render_camera =self.render_scene['Camera_Materials']
        if self.render_camera is not None:
            context.scene.camera = self.render_camera
            self.render_scene.camera = self.render_camera
        
        self.render_scene['Material_Container'].hide_render = True
        self.render_scene['Object_Container'].hide_render = True
        set_light_settings(self,context)
        set_render_settings(self,context)
        setup_compositer_links(self,context)
    
    def prepare_assets_for_render(self, context):
        # print('prepare_assets_for_render')
        selected_assets = get_selected_assets()
        for asset in selected_assets:
            add_selected = self.asset_props.selected.add()
            add_selected.asset = asset
            asset.select_set(False)
        asset_type = context.scene.asset_props.asset_types
        filtered_hierarchy = filter_assets(selected_assets, asset_type)
        if asset_type == 'Geometry Nodes':
            self.get_geo_assets_to_render_from_hierarchy(context,filtered_hierarchy,asset_type)
        else:
            self.get_assets_to_render_from_hierarchy(context,filtered_hierarchy,asset_type)

    def get_assets_to_render_from_hierarchy(self, context,hierarchy, asset_type):
        for item in hierarchy:
            if item and hasattr(item, 'asset') and item.asset:
                if item.asset_type == asset_type and not item.children:
                    if not AssetOperations.is_excluded(item.asset):
                        if item.asset_type == 'Material Nodes':
                            self.preview_filenames.append(f'preview_{item.asset.node_tree.name}.png')
                        else:
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
        # print('Setup Render Handlers')


    def create_copy_of_current_asset(self, asset):
        if asset.name+'_to_render' not in bpy.data.objects:
            copy = asset.copy()
            copy.name = asset.name+'_to_render'
        else:
            copy = bpy.data.objects.get(asset.name+'_to_render')
        return copy


    def link_to_object_container(self, asset):
        if asset.name not in self.render_scene['Object_Container'].objects:
            self.render_scene['Object_Container'].objects.link(asset)
        self.preview_col.objects.unlink(asset)

    def cleanup_render_process(self, context):
        # print('Cleaning up render process')
        if self.pre in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(self.pre)
        if self.post in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(self.post)
        if self.cancelled in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(self.cancelled)

        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        # Clean up objects in the object container and preview collection
        if self.render_scene['Object_Container']:
            for obj in self.render_scene['Object_Container'].objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        if self.preview_col:
            bpy.data.collections.remove(self.preview_col, do_unlink=True)
        
        # Restore original camera
        original_camera = bpy.data.objects.get(self.original_camera_name)
        context.scene.camera = original_camera if original_camera else None
        for rendered_asset in context.scene.asset_props.rendered_assets:
            if rendered_asset.asset.asset_data:
                assign_previews(context,rendered_asset.asset)
        for selected_asset in context.scene.asset_props.selected:
            selected_asset.asset.select_set(True)
  

        # Clear selected assets, Restore original render resolution
        context.scene.asset_props.selected.clear()
        context.scene.asset_props.rendered_assets.clear()
        context.scene.render.resolution_x = self.original_scene_res[0]
        context.scene.render.resolution_y = self.original_scene_res[1]
        
        # Remove the imported PreviewRenderScene
        remove_preview_render_scene()
        # print('Render process cleanup completed')

    def debug_render(self, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            self.render_scene['Center_Point'].hide_render = False if context.scene.asset_props.debug else True
            self.render_scene['Preview_Scale_Range'].hide_render = False if context.scene.asset_props.debug else True
    
    def set_ph_asset_path(self):
        nodes = self.render_scene.node_tree.nodes
        self.render_scene.frame_current = 0
        ph_out = nodes.get('File_PH_Out')
        asset_name =self.preview_filenames[0].removesuffix('.png')
        ph_filepath =  os.path.join(self.ph_asset_preview_path,'PH_' + asset_name + '.png')
        if os.path.exists(ph_filepath):
            os.remove(ph_filepath)
        ph_out.file_slots[0].path = os.path.join(self.ph_asset_preview_path,'PH_' + asset_name + '#.png')

    def remove_ph_padding(self):
        asset_name =self.preview_filenames[0].removesuffix('.png')
        padded_path = os.path.join(self.ph_asset_preview_path,'PH_' + asset_name + '1.png')
        correct_name = 'PH_' + asset_name + '.png'
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
                strategy.setup_render_type(context, asset,self)
            else:
                print(f"Unsupported asset type: {asset_type}")
                return
            
            asset_bbox_logic.restore_pivot_transform(current_pivot_transform)

            self.set_ph_asset_path()
            self.render_scene.render.filepath = os.path.join(self.asset_preview_path,self.preview_filenames[0])
            bpy.ops.render.render(scene='PreviewRenderScene', write_still=True, use_viewport=True)
        # TODO: Add exception handling for failed renders, use exceptions where needed not everywhere
        except Exception as e:
            print(f"Error in Render next asset( {asset.name}) : {e}")
            self.cancelled('PreviewRenderScene', None)

    def execute(self, context):
        try:
            # print('Executing Render Preview')
            self.is_rendering = True
            context.window_manager.modal_handler_add(self)
            # print('Setup Render Handlers completed')
            return {"RUNNING_MODAL"}
        except Exception as e:
            print(f"Error in render preview execute: {e}")
            self.cleanup_render_process(context)
            return {'CANCELLED'}
    
    def modal(self, context, event):
        try:
            if event.type == 'TIMER':
               
                # print(f"Modal state: {self.state}")
                if self.state == 'INIT':
                    self.state = 'RENDERING'
                    # print('Running Modal Render Preview')
                    self.render_next_asset(context)
                if self.state == 'FINISHED':
                    print('Finished Render Previews')
                    self.cleanup_render_process(context)
                    self.asset_props.is_rendering = False
                    return {"FINISHED"}
                
                elif self.state == 'RENDERING':
                   
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
    UB_OT_RenderPreviews,
    UB_OT_AdjustPreviewCamera,
    UB_OT_Pivot_Bottom_Center,
    )

register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()


    
def unregister():
    unregister_classes()
