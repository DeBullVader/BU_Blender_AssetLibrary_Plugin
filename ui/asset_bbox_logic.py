import bpy
from mathutils import Vector,Euler
import math
def get_obj_world_bbox_corners(obj):
    world_bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return world_bbox_corners

def get_obj_world_bbox_size(world_bbox_corners):
    world_bbox_size = [max(corner[i] for corner in world_bbox_corners) - min(corner[i] for corner in world_bbox_corners) for i in range(3)]
    return world_bbox_size

def get_scale_factor(obj, target_x_size,target_y_size, target_z_size):
    world_bbox_corners =get_obj_world_bbox_corners(obj)
    world_bbox_size = get_obj_world_bbox_size(world_bbox_corners)
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
    return lower_z_extent,center_x,center_y

def set_object_location_to_zero(object_type,obj,location):
    obj.location = location
   

def set_col_front_lower_to_floor(collection):
    lower_z_extent,front_y_extent = get_col_front_lower_extent(collection)


def set_bottom_center(obj):
    
    bottom_center = get_bottom_center_extent(obj)
    obj.location -= Vector(bottom_center)
            

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

def get_col_front_lower_extent(collection):
    max_coords,min_coords = get_collection_bounding_box(collection)
    lower_z_extent = min_coords.z
    front_y_extent = min_coords.y
    return lower_z_extent,front_y_extent

def set_rotation(obj, target_rotation):

    if isinstance(obj, bpy.types.Object):
        print('target_rotation',target_rotation)
        # rot_radians = [math.radians(angle) for angle in target_rotation]
        # euler_rot = Euler(rot_radians, 'XYZ')
        # print('euler_rot',euler_rot)
        obj.rotation_euler = target_rotation
    elif isinstance(obj, bpy.types.Collection):
        for object_in_collection in obj.objects:
            # rot_radians = [math.radians(angle) for angle in target_rotation]
            # euler_rot = Euler(rot_radians, 'XYZ')
            object_in_collection.rotation_euler = target_rotation
    
