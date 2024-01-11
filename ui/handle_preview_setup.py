import bpy
import sys
import os
import json
import traceback
import shlex
import logging
from bpy.app.handlers import persistent
from logging.handlers import RotatingFileHandler
from mathutils import Vector,Euler
import math
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)
import asset_bbox_logic
print("Subprocess script started.")

def setup_logger(name, log_file, level=logging.ERROR, max_size=1048576, backups=5):
    """Sets up a rotating file logger.

    Args:
        name (str): Name of the logger.
        log_file (str): Path to the log file.
        level (int, optional): Logging level. Defaults to logging.ERROR.
        max_size (int, optional): Max size of log file in bytes. Defaults to 1048576 (1MB).
        backups (int, optional): Number of backup files to keep. Defaults to 5.
    
    Returns:
        logging.Logger: Configured logger.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a rotating file handler
    handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backups)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger

addon_directory = os.path.dirname(os.path.dirname(__file__))
error_dir =f'{addon_directory}{os.sep}error_logs'
# Set up the logger (adjust the file path as needed)
log_file_path = os.path.join(error_dir, 'error_log.txt')
if not os.path.exists(error_dir):
    os.mkdir(error_dir)
addon_logger = setup_logger('addon_logger', log_file_path)

def clear_logger():
    try:
        print("Clearing logger...")
        addon_logger.handlers.clear()
        for handler in addon_logger.handlers:
            handler.close()
            addon_logger.handlers.remove(handler)
    except Exception as e:
        print(f"An error occurred in clear_logger: {str(e)}")
        sys.exit(1)


def load_source_blend_file(source_blend_file,asset_info):
    try:
        asset_name = asset_info['asset_name']
        asset_type = asset_info['asset_type']
        print(asset_name,asset_type)
        # print('inside load_source_blend_file')
        # print('asset_name: ',asset_name)
        # print('asset_type: ',asset_type)
        # print('source_blend_fil: ',source_blend_file)
        with bpy.data.libraries.load(source_blend_file, link=False) as (data_from, data_to):
            # print('inside libraries.load')
            if asset_type not in dir(data_from):
                print((f"Invalid asset type: {asset_type}"))
                sys.exit(1)
            if asset_type == 'node_groups':
                asset_type = 'objects'
            asset_names = getattr(data_from, asset_type)
            if asset_name in asset_names:
                # print('asset_names: ',asset_names)
                # print('asset_name', asset_name)
                getattr(data_to, asset_type).append(asset_name)
                print(f"Asset '{asset_name}' of type '{asset_type}' loaded from {source_blend_file}")
            else:
                print((f"Asset '{asset_name}' of type '{asset_type}' not found in {source_blend_file}"))
                sys.exit(1)
                   
    except Exception as e:
        print(f"An error occurred in load_source_blend_file: {str(e)}")
        sys.exit(1)

def handle_material_setup(scene,view_layer,asset_name):
    try:
        print('inside handle_material_setup')
        print(scene.objects)
        for obj in scene.objects:
            print('obj', obj)
        shaderball = scene.objects.get('BU_Shaderball')
        print('inside handle_material_setup')
        print('shaderball')
        if shaderball:
            material = bpy.data.materials.get(asset_name)
            print('material', material)
            if material:
                shaderball.data.materials.append(material)
                
            else:
                print(f"Material '{asset_name}' not found")
            for mats in shaderball.data.materials:
                print('mats',mats)
            
        else:
            print('No shaderball found')
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred in handle_material_setup: {str(e)}")
        sys.exit(1)

def handle_object_setup(scene,view_layer,asset_type,asset_info):
    try:
        asset_name = asset_info['asset_name']
        asset_type = asset_info['asset_type']
        object_type = asset_info['object_type']
        enable_offsets = asset_info['enable_offsets']
        location = asset_info['location']
        float_scale = asset_info['scale']
        scale = (float_scale, float_scale, float_scale)
        rotation = asset_info['rotation']
        max_scale = Vector(asset_info['max_scale'])

        object_container = scene.collection.children.get('Object_Container')
        if object_container:
            
            object_to_render = bpy.data.objects.get(asset_name)
            object_container.objects.link(object_to_render)
            object_to_render.hide_render = False
            scale_factor = asset_bbox_logic.get_scale_factor(obj=object_to_render,target_x_size=max_scale.x,target_y_size=max_scale.y,target_z_size=max_scale.z)
            asset_bbox_logic.scale_object_for_render(object_to_render,scale_factor)
            if enable_offsets:
                object_to_render.rotation_euler = rotation
                object_to_render.location = location
                object_to_render.scale = scale
            else:
                object_to_render.location = (0,0,0)
                asset_bbox_logic.set_bottom_center(object_to_render)
                object_to_render.rotation_euler = (0,0,0.436332)
                object_to_render.location.x +=0.04
                       
        else:
            print('object_container does not exist')
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred in handle_object_setup: {str(e)}")
        sys.exit(1)

def handle_collection_setup(scene,asset_info):
    try:
        asset_name = asset_info['asset_name']
        asset_type = asset_info['asset_type']
        object_type = asset_info['object_type']
        location = Vector(asset_info['location'])
        rotation = asset_info['rotation']
        scale = asset_info['scale']
        max_scale = Vector(asset_info['max_scale'])
        
        source_col = bpy.data.collections.get(asset_name)
        # for obj in source_col.objects:
        #     obj.hide_render = False
        object_to_render = asset_bbox_logic.create_collection_instance(bpy.context,asset_name)
        # object_to_render.hide_render = False
        object_to_render.location = location
        object_to_render.rotation_euler = rotation
        current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
        if scale !=1:
            object_to_render.scale = Vector((scale,scale,scale))
        else:
            col_scale_factor =asset_bbox_logic.get_col_scale_factor(source_col,max_scale.x,max_scale.y,max_scale.z)
            object_to_render.scale *= col_scale_factor
            object_to_render.location =Vector((0,0,0))
            asset_bbox_logic.set_col_bottom_center(object_to_render,source_col,col_scale_factor)
            bpy.context.view_layer.update()
            pivot_point = asset_bbox_logic.get_col_center_pivot_point(source_col,col_scale_factor)
            asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
            asset_bbox_logic.set_camera_look_at_vector(pivot_point)
            object_to_render.rotation_euler = (0,0,0.436332)
            asset_bbox_logic.restore_pivot_transform(current_pivot_transform)
    except Exception as e:
        print(f"An error occurred in handle_collection_setup: {str(e)}")
        sys.exit(1)


def get_layer_collection(collection):
    '''Returns the view layer LayerCollection for a specificied Collection'''
    def scan_children(lc, result=None):
        for c in lc.children:
            if c.collection == collection:
                return c
            result = scan_children(c, result)
        return result

    return scan_children(bpy.context.view_layer.layer_collection)

def set_camera_transform(cam_info):
    try:
        cam = bpy.data.objects.get('Camera_Objects')
        override_camera = cam_info['override_camera']

        print('override_camera: ',override_camera)
        if override_camera:
            cam_loc = cam_info['cam_loc']
            cam_rot = cam_info['cam_rot']
        else:
            cam_loc = Vector((0.0,-2.0,0.95))
            cam_rot = Euler((1.39626,0,0))
        if cam:
            cam.location = cam_loc
            cam.rotation_euler = cam_rot
    except Exception as e:
        print(f"An error occurred in set_camera_transform: {str(e)}")
        sys.exit(1)       

def setup_render(asset_preview,ph_asset_preview,asset_name,render_logo):
    try:
        path_org,file_name = os.path.split(asset_preview)
        path_ph,ph_file_name = os.path.split(ph_asset_preview)
        if not os.path.exists(path_org):
            print(f"Asset preview path does not exist: {path_org}")
            sys.exit(1)
        else:
            if not os.path.exists(path_ph):
                os.mkdir(path_ph)
        
        scene = bpy.context.scene
        scene.use_nodes = True
        nodes = scene.node_tree.nodes

        
        scene.render.engine = 'CYCLES'
        
        scene.cycles.feature_set = 'SUPPORTED'
        scene.cycles.device = 'GPU'
        scene.cycles.samples = 64
        scene.use_nodes = True
        scene.render.use_sequencer = False
        scene.render.use_overwrite = False
        scene.render.use_file_extension = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.use_placeholder = True
        scene.render.resolution_x =256
        scene.render.resolution_y =256
        scene.render.image_settings.view_settings.view_transform = 'Standard'
        scene.render.image_settings.view_settings.look = 'None'
        scene.render.film_transparent = True
        scene.render.image_settings.color_mode = 'RGBA'
        scene.cycles.film_transparent_glass = True
        scene.render.filepath = asset_preview

        render_layers_node = nodes.get('Render_Layers')
        composite_node = nodes.get('Composite')
        alphaover_ph_node = nodes.get('Alpha_Over_Placeholder')
        alphaover_org_node =nodes.get('Alpha_Over_Original')
        ph_out = nodes.get('File_PH_Out')
        ph_out.file_slots[0].path = ph_asset_preview
        scene.frame_current = 0

        links = scene.node_tree.links
        link = links.new
        
        if (asset_type == 'materials' or not render_logo):
            link(render_layers_node.outputs["Image"], composite_node.inputs["Image"])
            link(render_layers_node.outputs["Image"], alphaover_ph_node.inputs[1])
        else:
            link(alphaover_org_node.outputs["Image"], composite_node.inputs["Image"])
            link(alphaover_org_node.outputs["Image"], alphaover_ph_node.inputs[1])
        print('setup_render complete')
        
        
        
        
        
    except Exception as e:
        addon_logger.error(e)
        traceback.print_exc()
        print(f"An error occurred in perform_render: {str(e)}")
        sys.exit(1)


def exit(dummy):
    sys.exit(1)

def cleanup(scene,object_type,asset_name):
    try:
        print("cleaning up")
        nodes = scene.node_tree.nodes
        image = nodes.get('Image_To_Composite')
        if asset_name in bpy.data.images:
            bpy.data.images.remove(image.image)
            # image.image = None
        object_container = scene.collection.children.get('Object_Container')
        
        shaderball = scene.objects.get('BU_ShaderBall')
        for object in object_container.objects:
            object_container.objects.unlink(object)
        if shaderball:
            bpy.data.objects.remove(shaderball, do_unlink=True)
        clear_logger()
        
    except Exception as e:
        print(f"An error occurred in cleanup: {str(e)}")
        sys.exit(1)

@persistent
def finish(dummy):
    try:
        print("finishing..")
        cleanup(bpy.context.scene,object_type,asset_name)
        check_finished(asset_preview)
    except Exception as e:
        print(f"An error occurred in finish: {str(e)}")
        sys.exit(1)


def check_finished(asset_preview):
    print(f"check_finished: {asset_preview}")
    if os.path.exists(asset_preview):
        dir,name = os.path.split(asset_preview)
        print(f"Render complete for {name}")
        sys.exit(0)
    else:
        print(f"Final check failed for {asset_preview} and {ph_asset_preview}")
        sys.exit(1)

try:
    args = sys.argv[sys.argv.index("--") + 1:]
    source_blend_file = args[0]
    preview_blend_file_path = args[1]
    asset_preview_path = args[2]
    ph_asset_preview_path = args[3]
    asset_info = json.loads(args[4])
    scene_info = json.loads(args[5])
    cam_info = json.loads(args[6])

    asset_name = asset_info['asset_name']
    asset_type = asset_info['asset_type']
    object_type = asset_info['object_type']
    render_bg = scene_info['render_bg']
    render_logo = scene_info['render_logo']
    override_camera = cam_info['override_camera']
    cam_loc = cam_info['cam_loc']
    cam_rot = cam_info['cam_rot']


    source_blend_file = os.path.abspath(source_blend_file)

    preview_blend_file_path = os.path.abspath(preview_blend_file_path)
    bpy.ops.wm.open_mainfile(filepath=preview_blend_file_path)
    
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    camera_objects = bpy.data.objects.get("Camera_Objects")
    camera_materials = bpy.data.objects.get("Camera_Materials")
    shaderball_container = scene.collection.children.get('Shaderball_Container')
    object_container = scene.collection.children.get('Object_Container')
    background = scene.objects.get('Background')
    shadow_catcher = scene.objects.get('Shadow_Catcher')
    logo = scene.collection.children.get('Logo')
    if logo:
        logo.hide_render = True

    load_source_blend_file(source_blend_file,asset_info)

    if asset_type =='node_groups':
        obj = bpy.data.objects.get(asset_name)
        geo_modifier = next((modifier for modifier in obj.modifiers.values() if modifier.type == 'NODES'), None)
        if geo_modifier:
            g_nodes = geo_modifier.node_group
            asset_name = g_nodes.name
    
    asset_preview = os.path.join(asset_preview_path, 'preview_' + asset_name + '.png')
    ph_asset_preview =os.path.join(ph_asset_preview_path, 'PH_preview_' + asset_name + '#.png')
    ph_asset_preview_temp =os.path.join(ph_asset_preview_path, 'PH_preview_' + asset_name + '0.png')
    ph_asset_preview_noframe =os.path.join(ph_asset_preview_path, 'PH_preview_' + asset_name + '.png')
    if os.path.exists(asset_preview):
        os.remove(asset_preview)
    if os.path.exists(ph_asset_preview_temp):
        os.remove(ph_asset_preview_temp)
    if os.path.exists(ph_asset_preview_noframe):
        os.remove(ph_asset_preview_noframe)
    
    
    set_camera_transform(cam_info)
    if object_type == 'Collection':
        background.hide_render = not render_bg
        shadow_catcher.hide_render = render_bg
        
        object_container.hide_render = False
        shaderball_container.hide_render = True
        handle_collection_setup(scene,asset_info)
        scene.camera = camera_objects

    if object_type == 'Object' and asset_type == 'objects':
        background.hide_render = not render_bg
        shadow_catcher.hide_render = render_bg
        object_container.hide_render = False
        shaderball_container.hide_render = True
        handle_object_setup(scene,view_layer, asset_type, asset_info)
        scene.camera = camera_objects

    elif object_type == 'Object' and asset_type == 'node_groups':
        background.hide_render = not render_bg
        shadow_catcher.hide_render = render_bg
        object_container.hide_render = False
        shaderball_container.hide_render = True
        handle_object_setup(scene,view_layer, asset_type, asset_info)
        scene.camera = camera_objects

    elif asset_type == 'materials':
        object_container.hide_render = True
        shaderball_container.hide_render = False
        handle_material_setup(scene,view_layer,asset_name)
        scene.camera = camera_materials
    

    setup_render(asset_preview,ph_asset_preview,asset_name,render_logo)
    
    bpy.ops.render.render(layer='ViewLayer',write_still=True)

    if os.path.exists(asset_preview):
        if os.path.exists(ph_asset_preview_temp):
            os.rename(ph_asset_preview_temp, ph_asset_preview_noframe)
    cleanup(scene,object_type,asset_name)


    
except Exception as e:
    addon_logger.error(e)
    print("Error: Could not find the file", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)  # Exit with a non-zero status to indicate error
    


    