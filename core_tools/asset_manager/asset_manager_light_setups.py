import bpy,os
from bpy.utils import register_classes_factory,register_class, unregister_class
from ...utils import addon_info
from .asset_manager_ui import AssetManager_settings

preview_collections = {}

def gen_preview_collection(collection_name):
    pcoll = preview_collections[collection_name]
    image_location = pcoll.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg','exr')
    enum_items = []
    # Generate the thumbnails
    for i, image in enumerate(os.listdir(image_location)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(image_location, image)
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
            enum_items.append((image, image, "", thumb.icon_id, i))      
    return enum_items

def scene_world_settings(self,context,render_scene):
    hdri_file_name = context.scene.hdri
    plugin_assets_dir = addon_info.get_plugin_assets_dir()
    hrdi_filepath = os.path.join(plugin_assets_dir,'hdri',hdri_file_name)
    world = render_scene.world
    if hdri_file_name not in bpy.data.images:
        hdri_image = bpy.data.images.load(hrdi_filepath)
    else:
        hdri_image = bpy.data.images[hdri_file_name]
    world.node_tree.nodes['Environment Texture'].image = hdri_image
    world.node_tree.nodes['Exposure'].outputs['Value'].default_value = context.scene.render_settings.world_exposure
    world.node_tree.nodes['Temperature'].outputs['Value'].default_value = context.scene.render_settings.world_temperature
def set_light_settings(self,context,render_scene):
    # render_scene = self.render_scene
    render_settings = context.scene.render_settings
    backdrop = render_scene['Floor_And_Backdrop']
    render_scene.view_layers[0].layer_collection.children['Floor_And_Backdrop'].hide_viewport = not render_settings.enable_backdrop
    backdrop.hide_render = not render_settings.enable_backdrop
    backdrop_plane = render_scene['Background_Plane']
    backdrop_plane['Background_Color'] = render_settings.background_color
    backdrop_plane['Emissive_Strength'] = render_settings.emissive_strength
    for obj in backdrop.objects:
        obj.visible_camera = not render_settings.background_transparent 

    light_setup = context.scene.light_setup.removesuffix('.png')
    for col in render_scene.collection.children['Light_Setups'].children:
        is_hidden = False if col.name == light_setup else True
        col.hide_render = is_hidden
        render_scene.view_layers[0].layer_collection.children['Light_Setups'].children[col.name].hide_viewport = is_hidden

def add_preview_collections(path,preview_col_name):
    pcoll = bpy.utils.previews.new()
    pcoll.images_location = path
    preview_collections[preview_col_name] = pcoll

def remove_preview_collections():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

# classes=(
#     SelectedAssets,
#     AssetProperties,
#     )

# register_classes, unregister_classes = register_classes_factory(classes)

def register():
    plugin_assets_path =addon_info.get_plugin_assets_dir()
    light_setups_path = os.path.join(plugin_assets_path,'light_setups')
    hdri_path = os.path.join(plugin_assets_path,'HDRI')
    blender_dir,_ = os.path.split(bpy.app.binary_path)
    # print(bpy.utils.user
    b_hdri_path = os.path.join(blender_dir,'4.1','datafiles','studiolights','world')
    
    #Do later add user resources path for hdris so that user installed hdris are included in hdri previews.
    # path_studiolights = os.path.join("studiolights", 'world')
    # path_studiolights = bpy.utils.user_resource('DATAFILES', path=path_studiolights, create=True)
    # print(os.listdir(path_studiolights))
    add_preview_collections(light_setups_path,"thumbnail_previews")
    add_preview_collections(b_hdri_path,"hdri_previews")
    bpy.types.Scene.light_setup = bpy.props.EnumProperty(items=gen_preview_collection("thumbnail_previews"), options={'HIDDEN'})
    bpy.types.Scene.hdri = bpy.props.EnumProperty(items=gen_preview_collection("hdri_previews"), options={'HIDDEN'})
    
def unregister():
    del bpy.types.Scene.light_setup
    del bpy.types.Scene.hdri
    remove_preview_collections()