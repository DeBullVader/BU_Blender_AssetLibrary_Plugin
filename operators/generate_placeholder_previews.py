import bpy
import os
from ..utils import addon_info


def composite_placeholder_previews(asset_thumb_path):
    #paths
    asset_thumb_dir = os.path.dirname(asset_thumb_path)
    asset_thumb_file = os.path.basename(asset_thumb_path)
    original_thumb_path = f'{asset_thumb_dir}{os.sep}{asset_thumb_file}'
    placeholder_thumb_path = f'{asset_thumb_dir}{os.sep}PH_{asset_thumb_file}'
    addon_path = addon_info.get_addon_path()
    asset_download_icon_path = f'{addon_path}{os.sep}BU_plugin_assets{os.sep}images{os.sep}Download_Icon.png'

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
    link(transform_node.outputs["Image"], alpha_over.inputs[2])
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