import bpy
from mathutils import Vector,Matrix
from ...utils import asset_bbox_logic
from .asset_manager_utils import AssetOperations

def create_collection_instance(source_coll):
    col_bottom_center_location =asset_bbox_logic.get_col_bottom_center(source_coll)
    instance_obj = bpy.data.objects.new(f'{source_coll.name}_instance', None)
    instance_obj.instance_collection = source_coll
    instance_obj.instance_type = 'COLLECTION'
    instance_obj.instance_collection.instance_offset = col_bottom_center_location
    return instance_obj

def scale_asset_to_render(asset_props,scene,object_to_render):
    current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
    asset_bbox_logic.set_transform_pivot_point_to_bound_center()
    asset_bbox_logic.scale_asset_for_render(scene,object_to_render,asset_props.max_scale) 
    asset_bbox_logic.restore_pivot_transform(current_pivot_transform)

def align_camera_to_selected_asset(camera):
    bpy.ops.view3d.camera_to_view_selected()
    loc = Matrix.Translation((0.0, 0.0, 0.5))
    camera.matrix_world @= loc


  
class ObjectRenderStrategy():
    def setup_render_type(cls, context, asset,self):
        asset_copy = self.create_copy_of_current_asset(asset)
        asset_props = context.scene.asset_props
        if asset_copy.name not in self.preview_col.objects:
            self.preview_col.objects.link(asset_copy)

        asset_copy = self.preview_col.objects.get(asset_copy.name)
        asset_copy.select_set(True)
        asset_copy.location = (0, 0, 0)
        
        set_asset_and_cam_rotation(context,asset_props, asset_copy)
        scale_asset_to_render(asset_props, context.scene, asset_copy)
        pivot_point = asset_bbox_logic.get_obj_center_pivot_point(asset_copy)
        asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
        align_camera_to_selected_asset(context.scene.camera)
        asset.select_set(False)
        self.link_to_object_container(asset_copy)

        self.render_scene['Object_Container'].hide_render = False
        self.render_scene['Object_Container'].objects[asset_copy.name].hide_render = False

class MaterialRenderStrategy():
    def setup_render_type(cls, context, asset,self):
        render_obj = get_render_object(self, context)
        render_obj.data.materials.clear()
        render_obj.data.materials.append(asset)
        self.render_scene['Material_Container'].hide_render = False

class CollectionRenderStrategy():
    def setup_render_type(cls, context, asset,self):
        asset_props = context.scene.asset_props
        
        source_col = bpy.data.collections.get(asset.name)
        for obj in source_col.objects:
            obj.select_set(True)
            obj.hide_render = False
        
        col_scale_factor = asset_bbox_logic.calc_col_scale_factor(source_col)
        instance_obj = create_collection_instance(source_col)
        
        if instance_obj.name not in self.preview_col.objects:
            self.preview_col.objects.link(instance_obj)

        instance_obj = self.preview_col.objects.get(instance_obj.name)
        instance_obj.scale *= col_scale_factor
        bpy.context.view_layer.update()
        
        asset_bbox_logic.set_col_bottom_center(instance_obj, source_col, col_scale_factor)
        bpy.context.view_layer.update()
        instance_obj.location = Vector((0, 0, 0))

        pivot_point = asset_bbox_logic.get_col_center_pivot_point(source_col, col_scale_factor)

        bpy.context.view_layer.update()
        asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
        set_asset_and_cam_rotation(context,asset_props, instance_obj)
        align_camera_to_selected_asset(context.scene.camera)
        for obj in source_col.objects:
            obj.select_set(False)
        instance_obj.select_set(True)
    
        self.link_to_object_container(instance_obj)
        instance_obj.select_set(False)
        self.render_scene['Object_Container'].hide_render = False
        self.render_scene['Object_Container'].objects[instance_obj.name].hide_render = False
  
class MaterialNodeRenderStrategy():
    def setup_render_type(cls, context, node,self):
        # Store original input values
        original_values = {}
        for input in node.inputs:
            if hasattr(input, 'default_value'):
                original_values[input.name] = input.default_value
        asset = node.node_tree
        render_obj = get_render_object(self, context)
        mat_name = f"render_mat_{asset.name}"
        render_mat = bpy.data.materials.new(mat_name)
        render_mat.use_nodes = True
        node_tree = render_mat.node_tree
        nodes = node_tree.nodes

        target_node = nodes.new(type='ShaderNodeGroup')
        target_node.node_tree = asset

        # Apply stored values to new node group
        for input_name, value in original_values.items():
            if input_name in target_node.inputs:
                target_node.inputs[input_name].default_value = value

        mat_output = nodes.get('Material Output')
        bsdf = nodes.get('Principled BSDF')
        if not bsdf:
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        output_types = {
            'bsdf': ['Base Color', 'Normal', 'Roughness', 'Metallic', 'Specular', 'Emission', 'Alpha', 'IOR'],
            'color': ['Color', 'Diffuse'],
            'uv': ['Vector', 'UV']
        }

        # Connect BSDF to Material Output if needed
        if any(item.name in output_types['bsdf'] + output_types['color'] 
                for item in target_node.node_tree.interface.items_tree 
                if item.item_type == 'SOCKET' and item.in_out == 'OUTPUT'):
            node_tree.links.new(bsdf.outputs['BSDF'], mat_output.inputs['Surface'])

        def connect_output(item):
            if item.name in output_types['uv']:
                node_tree.links.new(target_node.outputs[item.name], mat_output.inputs['Surface'])
            elif item.name in output_types['bsdf']:
                node_tree.links.new(target_node.outputs[item.name], bsdf.inputs[item.name])
            elif item.name in output_types['color']:
                node_tree.links.new(target_node.outputs[item.name], bsdf.inputs['Base Color'])
            else:
                # Connect directly to Surface if not in output_types
                node_tree.links.new(target_node.outputs[item.name], mat_output.inputs['Surface'])

        for item in target_node.node_tree.interface.items_tree:
            if item.item_type == 'SOCKET':
                if item.in_out == 'INPUT':
                    if item.name in output_types['uv']:
                        tex_coord = nodes.new('ShaderNodeTexCoord')
                        mapping = nodes.new('ShaderNodeMapping')
                        node_tree.links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], target_node.inputs[item.name])
                elif item.in_out == 'OUTPUT':
                    connect_output(item)

        render_obj = get_render_object(self, context)
        render_obj.data.materials.clear()
        render_obj.data.materials.append(render_mat)
        self.render_scene['Material_Container'].hide_render = False

class GeometryNodeRenderStrategy():
    def setup_render_type(cls, context, asset,self):
        asset_copy = self.create_copy_of_current_asset(asset)
        asset_props = context.scene.asset_props
        if asset_copy.name not in self.preview_col.objects:
            self.preview_col.objects.link(asset_copy)

        asset_copy = self.preview_col.objects.get(asset_copy.name)
        asset_copy.select_set(True)
        asset_copy.location = (0, 0, 0)
        set_asset_and_cam_rotation(context,asset_props, asset_copy)
        
        scale_asset_to_render(asset_props, context.scene, asset_copy)
        pivot_point = asset_bbox_logic.get_obj_center_pivot_point(asset)
        asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
        align_camera_to_selected_asset(context.scene.camera)
        asset.select_set(False)
        self.link_to_object_container(asset_copy)
        self.render_scene['Object_Container'].hide_render = False
        asset_to_render = self.render_scene['Object_Container'].objects.get(asset_copy.name)
        asset_to_render.hide_render = False

def set_asset_and_cam_rotation(context,asset_props, asset):
    if asset_props.use_asset_example_rotation:
        asset.rotation_euler = asset_props.asset_example_rotation
    context.scene.camera.rotation_euler = asset_props.render_camera_rotation

def get_render_object(self, context):
    selected_render_type = context.scene.asset_props.render_types
    render_obj = None
    for obj in self.render_scene['Material_Container'].objects:
        if selected_render_type =='Mat_Shaderball':
            if selected_render_type in obj.name:
                obj.hide_render = False
                render_obj = obj
            else:
                if obj.parent:
                    if selected_render_type in obj.parent.name:
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