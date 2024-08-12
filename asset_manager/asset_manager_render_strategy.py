import bpy
from mathutils import Vector,Matrix
from ..utils import asset_bbox_logic

def create_collection_instance(source_coll):
    col_bottom_center_location =asset_bbox_logic.get_col_bottom_center(source_coll)
    instance_obj = bpy.data.objects.new(f'{source_coll.name}_instance', None)
    instance_obj.instance_collection = source_coll
    instance_obj.instance_type = 'COLLECTION'
    instance_obj.instance_collection.instance_offset = col_bottom_center_location
    return instance_obj

def scale_asset_to_render(context,scene,object_to_render):
    print('scale asset to render')
    asset_props = context.scene.asset_props
    current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
    set_transform_pivot_point_to_bound_center()
    asset_bbox_logic.scale_asset_for_render(scene,object_to_render,asset_props.max_scale) 
    asset_bbox_logic.restore_pivot_transform(current_pivot_transform)

def align_camera_to_selected_asset(camera):
    bpy.ops.view3d.camera_to_view_selected()
    loc = Matrix.Translation((0.0, 0.0, 0.5))
    camera.matrix_world @= loc

class AssetRenderStrategy:
  def setup_render_type(self, context, asset, render_preview):
      raise NotImplementedError

class ObjectRenderStrategy(AssetRenderStrategy):
  def setup_render_type(self, context, asset, render_preview):
      asset_copy = render_preview.create_copy_of_current_asset(asset)
      if asset_copy.name not in render_preview.preview_col.objects:
          render_preview.preview_col.objects.link(asset_copy)

      asset_copy = render_preview.preview_col.objects.get(asset_copy.name)
      asset_copy.select_set(True)
      asset_copy.location = (0, 0, 0)

      asset_copy.rotation_euler = context.scene.asset_props.asset_example_rotation
      context.scene.camera.rotation_euler = context.scene.asset_props.render_camera_rotation
      scale_asset_to_render(context, context.scene, asset_copy)
      pivot_point = asset_bbox_logic.get_obj_center_pivot_point(asset)
      asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
      align_camera_to_selected_asset(context.scene.camera)
      asset.select_set(False)
      render_preview.link_to_object_container(asset_copy)
      render_preview.object_container.hide_render = False
      asset_to_render = render_preview.object_container.objects.get(asset_copy.name)
      asset_to_render.hide_render = False

class MaterialRenderStrategy(AssetRenderStrategy):
    def setup_render_type(self, context, asset, render_preview):
        render_obj = get_render_object(self, context, render_preview)
        render_obj.data.materials.clear()
        render_obj.data.materials.append(asset)
        render_preview.material_container.hide_render = False

class CollectionRenderStrategy(AssetRenderStrategy):
    def setup_render_type(self, context, asset, render_preview):
        context.scene.camera.rotation_euler = context.scene.asset_props.render_camera_rotation
        source_col = bpy.data.collections.get(asset.name)
        for obj in source_col.objects:
            obj.select_set(True)
            obj.hide_render = False
        
        col_scale_factor = asset_bbox_logic.calc_col_scale_factor(source_col)
        instance_obj = create_collection_instance(source_col)
        
        if instance_obj.name not in render_preview.preview_col.objects:
            render_preview.preview_col.objects.link(instance_obj)

        instance_obj = render_preview.preview_col.objects.get(instance_obj.name)
        instance_obj.rotation_euler = context.scene.asset_props.asset_example_rotation
        instance_obj.scale *= col_scale_factor
        bpy.context.view_layer.update()
        
        asset_bbox_logic.set_col_bottom_center(instance_obj, source_col, col_scale_factor)
        bpy.context.view_layer.update()
        instance_obj.location = Vector((0, 0, 0))

        pivot_point = asset_bbox_logic.get_col_center_pivot_point(source_col, col_scale_factor)

        for obj in source_col.objects:
            obj.select_set(False)
        instance_obj.select_set(True)
        
        asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
        align_camera_to_selected_asset(context.scene.camera)
        
        render_preview.link_to_object_container(instance_obj)
        instance_obj.select_set(False)
        bpy.context.view_layer.update()
        render_preview.object_container.hide_render = False
        asset_to_render = render_preview.object_container.objects.get(instance_obj.name)
        asset_to_render.hide_render = False
  
class MaterialNodeRenderStrategy(AssetRenderStrategy):
    def setup_render_type(self, context, asset, render_preview):
        render_obj = get_render_object(self, context, render_preview)
        # render_obj.data.materials.clear()
        # render_obj.data.materials.append(asset)
        # render_preview.material_container.hide_render = False

        # print(asset.__dir__())
        
        print(asset.interface.items_tree.__dir__())
        for item in asset.interface.items_tree:
            if item.item_type == 'SOCKET':
                if item.in_out == 'INPUT':
                    print('input: ',item)
                elif item.in_out == 'OUTPUT':
                    print('output: ',item)



class GeometryNodeRenderStrategy(AssetRenderStrategy):
    def setup_render_type(self, context, asset, render_preview):
        pass

        # def setup_render_type(self, context, asset, render_preview):
def get_render_object(self, context, render_preview):
    selected_render_type = context.scene.asset_props.render_types
    render_obj = None
    for obj in render_preview.material_container.objects:
        if selected_render_type =='Mat_Shaderball':
            if obj.name == selected_render_type:
                obj.hide_render = False
                render_obj = obj
            else:
                if obj.parent:
                    if obj.parent.name ==selected_render_type:
                        obj.hide_render = False
                else:
                    obj.hide_render = True
        else:
            if obj.name == selected_render_type:
                obj.hide_render = False
                render_obj = obj
            else:
                obj.hide_render = True
    return render_obj

# Add more strategies for Material Nodes and Geometry Nodes when implemented