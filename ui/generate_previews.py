import bpy
import os
import subprocess
import json
import shlex
from bpy.types import Context
from mathutils import Vector,Euler
import math
from bpy.utils import register_classes_factory
from ..utils import addon_info,addon_logger
from . import asset_bbox_logic


def get_scale_factor(obj, target_z_size=1.25, target_x_size=1.5):
    world_bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    world_bbox_size = [max(corner[i] for corner in world_bbox_corners) - min(corner[i] for corner in world_bbox_corners) for i in range(3)]
    scale_factor_z = target_z_size / world_bbox_size[2] if world_bbox_size[2] != 0 else 1
    scale_factor_x = target_x_size / world_bbox_size[0] if world_bbox_size[0] != 0 else 1
    scale_factor = min(scale_factor_z, scale_factor_x)
    return scale_factor

def scale_object_for_render(obj, scale_factor):
    # Apply the scale factor
    obj.scale *= scale_factor
    bpy.context.view_layer.update()

def reset_object_scale_location(obj, original_scale,original_location):
    # Reset the scale
    obj.scale = original_scale
    bpy.context.view_layer.update()
    obj.location = original_location
    bpy.context.view_layer.update()

def get_front_lower_extent(obj):
    # Calculate the bounding box corners in world space
    # Find the lowest Z-coordinate
    world_bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower_z_extent = min(corner.z for corner in world_bbox_corners)
    front_y_extent = min(corner.y for corner in world_bbox_corners)
    return lower_z_extent,front_y_extent

def adjust_object_z_location(obj):
    # If the object is below the floor, move it up
    lower_z_extent,front_y_extent = get_front_lower_extent(obj)
    obj.location.z -= lower_z_extent
    obj.location.y -= front_y_extent


def get_collection_bounding_box(collection):
    min_coords = Vector((float('inf'), float('inf'), float('inf')))
    max_coords = Vector((-float('inf'), -float('inf'), -float('inf')))

    for obj in collection.objects:
        if obj.type == 'MESH':
            for corner in [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]:
                min_coords.x = min(min_coords.x, corner.x)
                min_coords.y = min(min_coords.y, corner.y)
                min_coords.z = min(min_coords.z, corner.z)
                max_coords.x = max(max_coords.x, corner.x)
                max_coords.y = max(max_coords.y, corner.y)
                max_coords.z = max(max_coords.z, corner.z)

    return (min_coords, max_coords)

class BU_OT_Append_Preview_Render_Scene(bpy.types.Operator):
    '''Append preview render scene to current file'''
    bl_idname = "bu.append_preview_render_scene"
    bl_label = "Append preview render scene to current file"
    bl_description = "Append the preview render scene to the current blend file. For rendering custom previews"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            return False
        return True
    
    def execute(self, context):
        addon_path = addon_info.get_addon_path()
        preview_render_file_path = os.path.join(addon_path,'BU_plugin_assets','blend_files','Preview_Rendering.blend')
        with bpy.data.libraries.load(preview_render_file_path) as (data_from, data_to):
            data_to.scenes = data_from.scenes

        if 'PreviewRenderScene' in bpy.data.scenes:
            print('Preview Render Scene has been added to the current blend file')
        return {'FINISHED'}

    
class BU_OT_Remove_Preview_Render_Scene(bpy.types.Operator):
    '''Remove preview render scene from current file'''
    bl_idname = "bu.remove_preview_render_scene"
    bl_label = "Remove preview render scene from current file"
    bl_description = "Remove the preview render scene from the current blend file. For rendering custom previews"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if 'PreviewRenderScene' not in bpy.data.scenes:
            return False
        return True
    
    def execute(self, context):
        bpy.data.scenes.remove(bpy.data.scenes['PreviewRenderScene'])
        bpy.data.orphans_purge(do_recursive=True)
        return {'FINISHED'}

class BU_OT_Switch_To_Preview_Render_Scene(bpy.types.Operator):
    '''Switch to preview render scene'''
    bl_idname = "bu.switch_to_preview_render_scene"
    bl_label = "Switch to preview render scene"
    bl_description = "Switch to the preview render scene"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if 'PreviewRenderScene' not in bpy.data.scenes:
            return False
        return True
    
    def execute(self, context):
        
            
        if context.scene.name != 'PreviewRenderScene':
            context.window.scene = bpy.data.scenes['PreviewRenderScene']
        else:
            for scene in bpy.data.scenes:
                if scene.name != 'PreviewRenderScene':
                    context.window.scene = scene
                    break
        return {'FINISHED'}

class BU_OT_SpawnPreviewCamera(bpy.types.Operator):
    bl_idname = "bu.spawn_preview_camera"
    bl_label = "Spawn preview camera"
    bl_description = "Spawn preview camera"
    bl_options = {'REGISTER'}

    idx: bpy.props.IntProperty()

    def execute(self, context):
        
        if 'Preview Camera' in bpy.data.cameras:
            preview_cam = bpy.data.cameras.get('Preview Camera')
        else:
            preview_cam = bpy.data.cameras.new('Preview Camera')
        preview_cam.lens =50
        preview_cam.sensor_width = 40
        if preview_cam:
            if 'Preview Camera' in context.scene.collection.objects:
                preview_cam_obj = context.scene.objects.get('Preview Camera')
                
            else:
                if 'Preview Camera' in bpy.data.objects:
                    preview_cam_obj = bpy.data.objects.get('Preview Camera')
                    context.scene.collection.objects.link(preview_cam_obj)
                else:
                    preview_cam_obj = bpy.data.objects.new('Preview Camera', preview_cam)
                    context.scene.collection.objects.link(preview_cam_obj)
        

        item = context.scene.mark_collection[self.idx]
        item.cam_loc = Vector((0.0,-2.0,0.95))
        item.cam_rot = Euler((1.39626,0,0))
        preview_cam_obj.location = item.cam_loc
        # Convert rotation from degrees to radians and set it
        preview_cam_obj.rotation_euler =item.cam_rot

        preview_cam_obj.lock_location[0] = True
        preview_cam_obj.lock_location[1] = True
        preview_cam_obj.lock_rotation[1] = True
        preview_cam_obj.lock_rotation[2] = True
        

        item.override_camera = True
        item.draw_override_camera = True
        context.scene.camera = preview_cam_obj
        context.scene.render.resolution_x = 256
        context.scene.render.resolution_y = 256
        return {'FINISHED'}
    
class BU_OT_ApplyCameraTransform(bpy.types.Operator):
    bl_idname = "bu.apply_camera_transform"
    bl_label = "Apply Camera Transform"

    idx: bpy.props.IntProperty()

    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
        item.lock_camera = True
        if 'Preview Camera' in bpy.data.objects:
            camera = bpy.data.objects.get('Preview Camera')
            item.cam_loc = camera.location
            item.cam_rot =  camera.rotation_euler
        return {'FINISHED'}
    
class BU_OT_Apply_AssetTransform(bpy.types.Operator):
    bl_idname = "bu.apply_asset_transform"
    bl_label = "Apply Asset Transform"

    idx: bpy.props.IntProperty()

    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
        if 'Preview Camera' in bpy.data.objects:
            camera = bpy.data.objects.get('Preview Camera')
            item.cam_loc = camera.location
            item.cam_rot = camera.rotation_euler
        return {'FINISHED'}
    
class BU_OT_ResetCameraTransform(bpy.types.Operator):
    bl_idname = "bu.reset_camera_transform"
    bl_label = "Reset Camera Transform"

    idx: bpy.props.IntProperty()

    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
        item.lock_camera = False
        item.cam_loc = Vector((0.0,-2.0,0.95))
        item.cam_rot = Euler((1.39626,0,0))
        if 'Preview Camera' in bpy.data.objects:
            camera = bpy.data.objects.get('Preview Camera')
            camera.location =item.cam_loc
            camera.rotation_euler = item.cam_rot

        return {'FINISHED'}

class BU_OT_RemovePreviewCamera(bpy.types.Operator):
    bl_idname = "bu.remove_preview_camera"
    bl_label = "Remove preview camera"
    bl_description = "Remove preview camera"
    bl_options = {'REGISTER'}
    
    idx: bpy.props.IntProperty()

    def execute(self, context):
        item = context.scene.mark_collection[self.idx]

        item.override_camera = False
        item.lock_camera = False
        if 'Preview Camera' in bpy.data.objects:
            camera = bpy.data.objects.get('Preview Camera')
            cam = bpy.data.cameras.get('Preview Camera')
            bpy.data.objects.remove(camera, do_unlink=True)
            bpy.data.cameras.remove(cam)
        return {'FINISHED'}
    
def create_collection_instance(context,item,collection_name):
    source_col = bpy.data.collections.get(collection_name)
    object_to_render = bpy.data.objects.new(f'{collection_name}_instance', None)
    item.col_instance = object_to_render
    object_to_render.instance_collection = source_col
    object_to_render.instance_type = 'COLLECTION'
    context.scene.collection.objects.link(object_to_render)
    return object_to_render

class BU_OT_Object_to_Preview_Dimensions(bpy.types.Operator):
    bl_idname = "bu.object_to_preview_demensions"
    bl_label = "Preview demensions"
    bl_description = "Preview demensions"
    bl_options = {'REGISTER'}
    
    idx: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
        item.enable_offsets = True
        item.draw_enable_offsets = True
        if item.object_type == 'Object':
            object_to_render = bpy.data.objects.get(item.asset.name)
            # print(object_to_render.__dir__())
            current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
            asset_bbox_logic.set_transform_pivot_point_to_bound_center()
            obj_scale_factor =asset_bbox_logic.get_scale_factor(item.asset,item.max_scale.x,item.max_scale.y,item.max_scale.z)
            # print(obj_scale_factor)
            asset_bbox_logic.scale_object_for_render(item.asset,obj_scale_factor)
            object_to_render.location =Vector((0,0,0))
            asset_bbox_logic.set_bottom_center(object_to_render)
            bpy.context.view_layer.update()
            pivot_point =asset_bbox_logic.get_obj_center_pivot_point(object_to_render)
            asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
            asset_bbox_logic.set_camera_look_at_vector(pivot_point)
            object_to_render.rotation_euler = (0,0,0.436332)
            object_to_render.location.x +=0.04
            asset_bbox_logic.restore_pivot_transform(current_pivot_transform)
            
            
            
        elif item.object_type == 'Collection':
            collection =bpy.data.collections.get(item.asset.name)
            current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
            asset_bbox_logic.set_transform_pivot_point_to_bound_center()
            object_to_render = asset_bbox_logic.create_collection_instance(context,item.asset.name)
            item.col_instance = object_to_render
            col_scale_factor =asset_bbox_logic.get_col_scale_factor(item.asset,item.max_scale.x,item.max_scale.y,item.max_scale.z)
            object_to_render.scale *= col_scale_factor
            object_to_render.location =Vector((0,0,0))
            asset_bbox_logic.set_col_bottom_center(object_to_render,collection,col_scale_factor)
            
            bpy.context.view_layer.update()
            
            pivot_point = asset_bbox_logic.get_col_center_pivot_point(collection,col_scale_factor)
            
            asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
            asset_bbox_logic.set_camera_look_at_vector(pivot_point)
            object_to_render.rotation_euler = (0,0,0.436332)
            asset_bbox_logic.restore_pivot_transform(current_pivot_transform)
            

            original_col =get_layer_collection(collection)
            original_col.hide_viewport = True

        
        return {'FINISHED'}

def get_layer_collection(collection):
    '''Returns the view layer LayerCollection for a specificied Collection'''
    def scan_children(lc, result=None):
        for c in lc.children:
            if c.collection == collection:
                return c
            result = scan_children(c, result)
        return result

    return scan_children(bpy.context.view_layer.layer_collection)

class BU_OT_Reset_Object_Original_Dimensions(bpy.types.Operator):
    bl_idname = "bu.reset_object_original_dimensions"
    bl_label = "Reset Object Original Dimensions"
    bl_description = "Reset Object Original Dimensions"
    bl_options = {'REGISTER'}
    
    idx: bpy.props.IntProperty()
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
        item.enable_offsets = False
        
        if item.object_type == 'Object':
            asset = bpy.data.objects.get(item.asset.name)
            asset.rotation_euler = Euler((0, 0, 0))
            asset.scale = Vector((1, 1, 1))
            asset.location = Vector((0, 0, 0))
            # asset_bbox_logic.set_bottom_center(item.asset)

        elif item.object_type == 'Collection':
            if item.col_instance:
                if item.col_instance.name in bpy.data.objects:
                    object_to_render = bpy.data.objects.get(item.col_instance.name)
                    if object_to_render:
                        bpy.data.objects.remove(object_to_render, do_unlink=True)
                item.scale =1
                collection =bpy.data.collections.get(item.asset.name)
                original_col =get_layer_collection(collection)
                original_col.hide_viewport = False

   
        return {'FINISHED'}

is_subprocess_running = False

def assign_previews(self,context,asset):
    asset_preview_path = addon_info.get_asset_preview_path()
    path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
    if os.path.exists(path):
        with bpy.context.temp_override(id=asset):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=path)

def set_preview_if_marked(self,context,idx,asset_type,asset_name):
    item = context.scene.mark_collection[idx]
    if asset_type =='collections':
        obj = bpy.data.collections.get(asset_name)
    elif asset_type =='objects' and item.types == 'Object':
        obj = bpy.data.objects.get(asset_name)
    elif asset_type =='materials':
        obj = bpy.data.materials.get(asset_name)
    elif item.types == 'Geometry_Node':
        obj = bpy.data.node_groups.get(asset_name)
    if obj:
        assign_previews(self,context,obj)


class BU_OT_RunPreviewRender(bpy.types.Operator):
    bl_idname = "bu.render_previews_modal"
    bl_label = "Run Preview Render"
    bl_description = "Render previews"
    bl_options = {'REGISTER'}

    idx: bpy.props.IntProperty()
    asset_type: bpy.props.StringProperty()
    asset_name: bpy.props.StringProperty()
    _timer = None
    _process = None

    @classmethod
    def poll(cls, context):
        global is_subprocess_running
        addon_prefs = addon_info.get_addon_name().preferences
        # if bpy.data.is_dirty:
        #     cls.poll_message_set('Please save the scene first')
        #     return False
        if not addon_prefs.thumb_upload_path:
            cls.poll_message_set('Please set the asset preview folder first')
            return False
        if is_subprocess_running:
            cls.poll_message_set('Rendering previews in progress')
            return False
        return cls._process is None
    
    def modal(self, context, event):
        
        if event.type == 'TIMER':
            try:
                if self._process is not None:
                    ret = self._process.poll()
                    
                    if ret is not None:  # Subprocess has finished
                        print("Subprocess finished ",ret)
                                                    
                        if ret == 0:
                            print("Subprocess finished successfully.")
                            print("Subprocess output:", self._process.stdout.read())
                            self.finish(context)
                        else:
                            print("Subprocess finished with error.")
                            print("Subprocess error:", self._process.stderr.read())
                            print("Subprocess output:", self._process.stdout.read())
                            error_message = self._process.stderr.read()
                            addon_logger.addon_logger.error(f"Error Rendering previews: {error_message}")
                            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(error_message))
                            self.finish(context)
                        return self.finish(context)
                    output = self._process.stdout.read()
                    error = self._process.stderr.read()
                    if output:
                        print("Subprocess output:", output)
                        set_preview_if_marked(self,context,self.idx,self.asset_type,self.asset_name)
                        self.finish(context)
                    if error:
                        print("Subprocess error:", error)
                    
    
                else:
                    print("No subprocess to poll.")
                    return self.finish(context)
            except Exception as e:
                print(f"An error occurred: {e}")
                addon_logger.addon_logger.error(e)
                self.finish(context)
        return {'PASS_THROUGH'}

    def finish(self, context):
        global is_subprocess_running
        is_subprocess_running = False
        context.window_manager.event_timer_remove(self._timer)
        self._process = None
        return {'FINISHED'}

    def execute(self, context):
        global is_subprocess_running
        is_subprocess_running = True

        idx = self.idx
        asset_data = context.scene.mark_collection[idx]
        asset_type = self.asset_type
        asset_name = self.asset_name
        object_type = asset_data.object_type
        render_bg = asset_data.render_bg
        render_logo = asset_data.render_logo
        override_camera = asset_data.override_camera
        cam_loc = list(asset_data.cam_loc)
        cam_rot = list(asset_data.cam_rot)
        enable_offsets = asset_data.enable_offsets
        max_scale = list(asset_data.max_scale)
        location = list(asset_data.location)
        rotation = list(asset_data.rotation)
        scale = asset_data.scale

        # print(self.asset_type)
        if asset_type == 'materials':
            if self.asset_name in bpy.data.materials:
                asset_data = bpy.data.materials[self.asset_name]
        # elif asset_type == 'node_groups':
        #     geo_modifier = next((modifier for modifier in asset_data.asset.modifiers.values() if modifier.type == 'NODES'), None)
        #     if geo_modifier:
        #         g_nodes = geo_modifier.node_group
        #         asset_data = g_nodes

        # Define paths
        asset_preview_path = addon_info.get_asset_preview_path()
        ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
        blender_executable_path = bpy.app.binary_path
        asset_blend_file_path = bpy.data.filepath
        addon_blend_file_path = addon_info.get_addon_blend_files_path()
        
        preview_blend_file_path = os.path.join(addon_blend_file_path,'Preview_Rendering.blend')
        dir_path = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.join(dir_path, 'handle_preview_setup.py')

        # Start the subprocess
        self._process = subprocess.Popen(
            [
                blender_executable_path,'--background','--python', script_path,'--',
                asset_blend_file_path,
                preview_blend_file_path,
                asset_preview_path,
                ph_asset_preview_path,
                json.dumps({'asset_name':asset_name, 'asset_type':asset_type,'object_type':object_type,'enable_offsets':enable_offsets,'location':location,'scale':scale,'rotation':rotation,'max_scale':max_scale}),
                json.dumps({'render_bg':render_bg, 'render_logo':render_logo,}),
                json.dumps({'override_camera':override_camera,'cam_loc':cam_loc,'cam_rot':cam_rot}),
            ],
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE,  # Capture standard errors
                text=True
        )

        print("Subprocess started, PID:", self._process.pid)
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class BU_OT_Render_Previews(bpy.types.Operator):
    '''Render previews'''
    bl_idname = "bu.render_previews"
    bl_label = "Render previews"
    bl_description = "Render previews"
    bl_options = {'REGISTER'}

    idx: bpy.props.IntProperty()
    asset_type: bpy.props.StringProperty()
    asset_name: bpy.props.StringProperty()
    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_name().preferences
        if not bpy.data.filepath:
            cls.poll_message_set('Please save the blend file first')
            return False
        if not addon_prefs.thumb_upload_path:
            cls.poll_message_set('Please set the asset preview folder first')
            return False
        return True
    

    def execute(self, context):

        idx = self.idx
        asset_data = context.scene.mark_collection[idx]
        asset_type = self.asset_type
        asset_name = self.asset_name
        object_type = asset_data.object_type
        render_bg = asset_data.render_bg
        render_logo = asset_data.render_logo
        override_camera = asset_data.override_camera
        cam_loc = list(asset_data.cam_loc)
        cam_rot = list(asset_data.cam_rot)
        enable_offsets = asset_data.enable_offsets
        max_scale = list(asset_data.max_scale)
        location = list(asset_data.location)
        rotation = list(asset_data.rotation)
        scale = asset_data.scale
        # print(self.asset_name)
        # print(self.asset_type)
        if asset_type == 'materials':
            # print(self.asset_name)
            if self.asset_name in bpy.data.materials:
                asset_data = bpy.data.materials[self.asset_name]
                
        elif asset_type == 'node_groups':
            geo_modifier = next((modifier for modifier in asset_data.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                g_nodes = geo_modifier.node_group
                asset_data = g_nodes

        # Define paths
        asset_preview_path = addon_info.get_asset_preview_path()
        ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
        blender_executable_path = bpy.app.binary_path
        asset_blend_file_path = bpy.data.filepath
        addon_blend_file_path = addon_info.get_addon_blend_files_path()
        
        preview_blend_file_path = os.path.join(addon_blend_file_path,'Preview_Rendering.blend')
        dir_path = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.join(dir_path, 'handle_preview_setup.py')

        
        try:
            # Run Blender in headless mode to execute the script
            result = subprocess.run(
                [
                    blender_executable_path,'--background','--python', script_path,'--',
                    asset_blend_file_path,
                    preview_blend_file_path,
                    asset_preview_path,
                    ph_asset_preview_path,
                    json.dumps({'asset_name':asset_name, 'asset_type':asset_type,'object_type':object_type,'enable_offsets':enable_offsets,'location':location,'scale':scale,'rotation':rotation,'max_scale':max_scale}),
                    json.dumps({'render_bg':render_bg, 'render_logo':render_logo,}),
                    json.dumps({'override_camera':override_camera,'cam_loc':cam_loc,'cam_rot':cam_rot}),
                # asset name, asset type, and other needed arguments
                ],
                    stdout=subprocess.PIPE,  # Capture standard output
                    stderr=subprocess.PIPE,  # Capture standard errors
                    text=True 
            )
                # Check if subprocess was successful

            if result.stdout:
                print("Output from subprocess:", result.stdout)

            if result.returncode != 0:
                message ="Error in subprocess:", result.stderr
                print(message)
                # bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message))
                addon_logger.addon_logger.error(message)
            else:
                print("Subprocess completed successfully:", result.stdout)
                # Process successful completion as needed

        except subprocess.CalledProcessError as e:
            message = f"Error Rendering previews: {e}"
            # bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
            addon_logger.addon_logger.error(message)
            print(message)

        return {'FINISHED'}

def composite_placeholder_previews(asset_thumb_path):
    #paths
    asset_thumb_dir = os.path.dirname(asset_thumb_path)
    asset_thumb_file = os.path.basename(asset_thumb_path)
    original_thumb_path = f'{asset_thumb_dir}{os.sep}{asset_thumb_file}'
    placeholder_thumb_path = f'{asset_thumb_dir}{os.sep}PH_{asset_thumb_file}'
    addon_path = addon_info.get_addon_path()
    asset_download_icon_path = f'{addon_path}{os.sep}BU_plugin_assets{os.sep}images{os.sep}Download_Icon_white.png'

# Initialize compositor
    scene = bpy.context.scene
    scene.use_nodes = True
    nodes = scene.node_tree.nodes

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create input image node (thumbnail)
    thumb_image = bpy.data.images.load(asset_thumb_path, check_existing=True)
    download_icon = bpy.data.images.load(asset_download_icon_path, check_existing=True)
    thumbnail_node = nodes.new(type='CompositorNodeImage')
    thumbnail_node.image = thumb_image
    
    thumbnail_node.location = (0, 0)

    #scale incomming image to fit output render size of 256px
    scale_node = nodes.new(type= 'CompositorNodeScale')
    scale_node.space = 'RENDER_SIZE'
    scale_node.frame_method = 'FIT'
    scale_node.location =(200,-100)

    # Create input image node (icon)
    icon_node = nodes.new(type='CompositorNodeImage')
    icon_node.image = download_icon
    icon_node.location = (0, -400)

    transform_node = nodes.new(type='CompositorNodeTransform')
    transform_node.location = (200, -400)
    transform_node.inputs['X'].default_value  = 95
    transform_node.inputs['Y'].default_value  = -95
    transform_node.inputs['Scale'].default_value  = 1

    multiply_node = nodes.new(type='CompositorNodeMath')
    multiply_node.operation = 'MULTIPLY'
    multiply_node.location = (300, -400)
    multiply_node.inputs[0].default_value = 1
    multiply_node.inputs[2].default_value = (0.0,0.9,1.0,1.0)

    # Create Alpha Over node
    alpha_over = nodes.new(type='CompositorNodeAlphaOver')
    alpha_over.use_premultiply = True
    alpha_over.location = (400, -100)

    # Create Composite node
    comp_node = nodes.new(type='CompositorNodeComposite')   
    comp_node.location = (600,-100)

    viewer_node = nodes.new(type='CompositorNodeViewer')
    viewer_node.location = (600, -300)

    # Link nodes
    links = scene.node_tree.links
    link = links.new
    link(thumbnail_node.outputs["Image"], scale_node.inputs["Image"])
    link(scale_node.outputs["Image"],alpha_over.inputs[1])
    link(icon_node.outputs["Image"], transform_node.inputs["Image"])
    link(transform_node.outputs["Image"], multiply_node.inputs[1])
    link(multiply_node.outputs["Image"], alpha_over.inputs[2])
    link(alpha_over.outputs["Image"], comp_node.inputs["Image"])
    link(alpha_over.outputs["Image"], viewer_node.inputs["Image"])

    # Update & render composite 
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x =256
    scene.render.resolution_y =256
    scene.render.filepath = placeholder_thumb_path
    bpy.ops.render.render(write_still=True)
    
    # Cleanup: Remove the nodes you created
    # nodes.remove(thumbnail_node)
    # nodes.remove(scale_node)
    # nodes.remove(icon_node)
    # nodes.remove(transform_node)
    # nodes.remove(alpha_over)
    # nodes.remove(comp_node)
    # nodes.remove(viewer_node)

    # # Reset the node tree (optional, depending on your workflow)
    # scene.node_tree.links.clear()

    return placeholder_thumb_path

classes = [BU_OT_RunPreviewRender,
           BU_OT_Render_Previews,
           BU_OT_Append_Preview_Render_Scene,
           BU_OT_Remove_Preview_Render_Scene,
           BU_OT_Switch_To_Preview_Render_Scene,
           BU_OT_SpawnPreviewCamera,
           BU_OT_RemovePreviewCamera,
           BU_OT_ApplyCameraTransform,
           BU_OT_ResetCameraTransform,
           BU_OT_Object_to_Preview_Dimensions,
           BU_OT_Reset_Object_Original_Dimensions
           ]
   

register_classes, unregister_classes = register_classes_factory(classes)  
  
def register():  
    register_classes()
    bpy.types.Scene.original_scale = bpy.props.FloatVectorProperty(name="original scale", default=(1.0, 1.0, 1.0))  
    bpy.types.Scene.original_location = bpy.props.FloatVectorProperty(name="original Location", default=(0.0, 0.0, 0.0))  
def unregister():  
    unregister_classes()
    del bpy.types.Scene.original_scale
    del bpy.types.Scene.original_location