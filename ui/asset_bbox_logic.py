import bpy
from mathutils import Vector,Euler
import math
def get_obj_world_bbox_corners(obj):
    world_bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return world_bbox_corners

def get_obj_world_bbox_size(world_bbox_corners):
    world_bbox_size = [max(corner[i] for corner in world_bbox_corners) - min(corner[i] for corner in world_bbox_corners) for i in range(3)]
    return world_bbox_size





def set_camera_look_at_vector(pivot_point):
    if 'Preview Camera' in bpy.data.objects:
        camera = bpy.data.objects['Preview Camera']

        look_at(camera, pivot_point)

def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()
    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')
    # assume we're using euler rotation
    obj_camera.rotation_euler.x = rot_quat.to_euler().x

def get_current_transform_pivotpoint():
    return bpy.context.scene.tool_settings.transform_pivot_point

def set_transform_pivot_point_to_bound_center():
    bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
    
def set_pivot_point_and_cursor(pivot_point):
    bpy.context.scene.cursor.location = pivot_point

    bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'

def restore_pivot_transform(transform_pivotpoint):
    bpy.context.scene.tool_settings.transform_pivot_point = transform_pivotpoint

def get_scale_factor(obj, target_x_size,target_y_size, target_z_size):
    world_bbox_corners =get_obj_world_bbox_corners(obj)
    world_bbox_size = get_obj_world_bbox_size(world_bbox_corners)
    
    print()
    
    increase = 1.4
    if obj.dimensions.x<obj.dimensions.y/1.3:
        target_x_size *= increase
        target_y_size *= increase
    elif obj.dimensions.y<=obj.dimensions.x/1.3:
        target_x_size *= increase
        target_y_size *= increase

    scale_factor_x = target_x_size / world_bbox_size[0] if world_bbox_size[0] != 0 else 1
    scale_factor_y = target_y_size / world_bbox_size[1] if world_bbox_size[1] != 0 else 1
    scale_factor_z = target_z_size / world_bbox_size[2] if world_bbox_size[2] != 0 else 1
    scale_factor = min(scale_factor_x,scale_factor_y, scale_factor_z)
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

def get_bottom_center_extent(obj):
    world_bbox_corners =get_obj_world_bbox_corners(obj)
    lower_z_extent = min(corner.z for corner in world_bbox_corners)

    min_x = min(corner.x for corner in world_bbox_corners)
    max_x = max(corner.x for corner in world_bbox_corners)
    center_x = (min_x + max_x) / 2

    # Get the center in the Y direction
    min_y = min(corner.y for corner in world_bbox_corners)
    max_y = max(corner.y for corner in world_bbox_corners)
    center_y = (min_y + max_y) / 2
    location_vector = Vector((center_x, center_y, lower_z_extent))
    return location_vector

def get_obj_center_pivot_point(obj):
    world_bbox_corners =get_obj_world_bbox_corners(obj)
    min_x = min(corner.x for corner in world_bbox_corners)
    max_x = max(corner.x for corner in world_bbox_corners)
    center_x = (min_x + max_x) / 2

    min_y = min(corner.y for corner in world_bbox_corners)
    max_y = max(corner.y for corner in world_bbox_corners)
    center_y = (min_y + max_y) / 2

    min_z = min(corner.z for corner in world_bbox_corners)
    max_z = max(corner.z for corner in world_bbox_corners)
    center_z = (min_z + max_z) / 2
    pivot_point = Vector((center_x, center_y, center_z))
    return pivot_point


def set_bottom_center(obj):
    location_vector = get_bottom_center_extent(obj)
    obj.location -=location_vector
    obj.location.x -=0.04        

def get_collection_bounding_box(collection):
    min_coords = Vector((float('inf'), float('inf'), float('inf')))
    max_coords = Vector((-float('inf'), -float('inf'), -float('inf')))
    object_sizes =[]
    for obj in collection.objects:
        if obj.type == 'MESH':
            for corner in [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]:
                min_coords.x = min(min_coords.x, corner.x)
                min_coords.y = min(min_coords.y, corner.y)
                min_coords.z = min(min_coords.z, corner.z)
                max_coords.x = max(max_coords.x, corner.x)
                max_coords.y = max(max_coords.y, corner.y)
                max_coords.z = max(max_coords.z, corner.z)
    return (max_coords,min_coords)


def get_col_scale_factor(collection, target_x_size,target_y_size, target_z_size):
    max_coords,min_coords = get_collection_bounding_box(collection)
    world_bbox_size =max_coords-min_coords
    increase = 1.4
    if world_bbox_size.x<world_bbox_size.y/1.3:
        target_x_size *= increase
        target_y_size *= increase
    elif world_bbox_size.y<=world_bbox_size.x/1.3:
        target_x_size *= increase
        target_y_size *= increase



    scale_factor_x = target_x_size / world_bbox_size[0] if world_bbox_size[0] != 0 else 1
    scale_factor_y = target_y_size / world_bbox_size[1] if world_bbox_size[1] != 0 else 1
    scale_factor_z = target_z_size / world_bbox_size[2] if world_bbox_size[2] != 0 else 1
    scale_factor = min(scale_factor_x,scale_factor_y, scale_factor_z)
    
    return scale_factor

def scale_collection_for_render(collection, scale_factor):
    # Apply the scale factor
    for obj in collection.objects:
        obj.scale *= scale_factor
    bpy.context.view_layer.update()

def set_col_bottom_center(col_instance,collection,col_scale_factor):
    location_vector = get_col_bottom_center(collection)
    location_vector *= col_scale_factor
    col_instance.location -= location_vector
    col_instance.location.x -=0.04

def get_col_bottom_center(collection):
    max_coords,min_coords = get_collection_bounding_box(collection)
    center_x = (min_coords.x + max_coords.x) / 2
    center_y = (min_coords.y + max_coords.y) / 2
    lower_z_extent = min_coords.z
    location_vector = Vector((center_x, center_y, lower_z_extent))
    return location_vector

def get_col_center_pivot_point(collection,col_scale_factor):
    max_coords,min_coords = get_collection_bounding_box(collection)
    pivot_point =(min_coords+max_coords)/2
    pivot_point *= col_scale_factor
    
    location_offset =get_col_bottom_center(collection)
    location_offset*= col_scale_factor
    pivot_point -= location_offset
    

    # currected_pivot_point = pivot_point - location_offset
    return pivot_point

    
