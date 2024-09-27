import bpy,os
from bpy.utils import register_classes_factory,register_class, unregister_class
from ...utils import addon_info


preview_collections = {}

def gen_light_setup_previews():
    pcoll = preview_collections["thumbnail_previews"]
    image_location = pcoll.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')
    enum_items = []
    # Generate the thumbnails
    for i, image in enumerate(os.listdir(image_location)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(image_location, image)
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
            enum_items.append((image, image, "", thumb.icon_id, i))      
    return enum_items

def add_preview_collections():
    addon_path = addon_info.get_addon_path()
    light_setups_path = os.path.join(addon_path,'BU_plugin_assets','light_setups')
    pcoll = bpy.utils.previews.new()
    pcoll.images_location = light_setups_path
    preview_collections["thumbnail_previews"] = pcoll

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
    add_preview_collections()
    bpy.types.Scene.light_setup = bpy.props.EnumProperty(items=gen_light_setup_previews(), options={'HIDDEN'})
    
def unregister():
    del bpy.types.Scene.light_setup
    remove_preview_collections()