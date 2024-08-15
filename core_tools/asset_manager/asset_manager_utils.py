import bpy,os
from bpy.utils import register_classes_factory
from .asset_manager_hierarchy import build_hierarchy
from... utils import addon_info,version_handler,asset_bbox_logic
class AssetOperations:
    exclude_list = []
    minimized_list=[]
    toggled=False
    asset_types =addon_info.type_mapping()
    

    @staticmethod
    def op_exclude_asset(layout,asset):
        op_icon = 'ADD' if asset.name in AssetOperations.exclude_list else 'REMOVE'
        op_depress=False if asset.name in AssetOperations.exclude_list else True
        op = layout.operator('ub.remove_from_list', text="", icon=op_icon, depress=op_depress)
        op.asset_name = asset.name

    @staticmethod
    def op_exclude_all(layout,children):
        op_icon = 'ADD' if all(child.asset.name in AssetOperations.exclude_list for child in children) else 'REMOVE'
        op_depress=False if all(child.asset.name in AssetOperations.exclude_list for child in children) else True
        op = layout.operator('ub.exclude_all_children', text="", icon=op_icon, depress=op_depress)
        op.children_names = ','.join([child.asset.name for child in children])

    @staticmethod
    def op_mark_clear_children(layout,asset,asset_type):
        children = get_child_assets(asset,asset_type)
        op_icon = 'CANCEL' if all(child.asset_data for child in children) else 'ASSET_MANAGER'
        op_depress=True if all(child.asset_data for child in children) else False
        op = layout.operator('ub.mark_all_children', text="", icon=op_icon, depress=op_depress)
        op.asset_name = asset.name
        op.asset_type = asset_type
        op.children_names = ','.join([child.name for child in children])

    @staticmethod
    def op_minimize_asset(layout,asset):
        minimized = asset.name in AssetOperations.minimized_list
        op_minimize = layout.operator('ub.minimize_asset_details', text="", icon='TRIA_RIGHT' if minimized else 'TRIA_DOWN', emboss=False)
        op_minimize.asset_name = asset.name
        return minimized
    
    @staticmethod
    def is_excluded(asset):
        return asset.name in AssetOperations.exclude_list
    
       

class AssetType:
  def __init__(self, name, icon, filter_func):
      self.name = name
      self.icon = icon
      self.filter_func = filter_func

EXCLUDE_TYPES = ['CAMERA','LIGHT','LIGHT_PROBE','POINTCLOUD','SPEAKER','VOLUME']
selected_assets = []

def get_exclude_types():
    return EXCLUDE_TYPES


def get_filter_asset_type(asset_type):
    asset_types = {
        'Objects': AssetType('Objects', 'OBJECT_DATA', filter_objects),
        'Collections': AssetType('Collections', 'COLLECTION', filter_collections),
        'Materials': AssetType('Materials', 'MATERIAL', filter_materials),
        'Material Nodes': AssetType('Material Nodes', 'NODETREE', filter_material_nodes),
        'Geometry Nodes': AssetType('Geometry Nodes', 'NODETREE', filter_geometry_nodes),
    }
    # return asset_types.get(asset_type, None)
    return asset_types[asset_type]

asset_types = [
    # ("actions", "Actions", "Action", "ACTION", 2 ** 1),
    ("Objects", "Objects", "Object", "OBJECT_DATA", 2 ** 1),
    ("Materials", "Materials", "Materials", "MATERIAL", 2 ** 2),
    # ("worlds", "Worlds", "Worlds", "WORLD", 2 ** 4),
    ("Material Nodes", "Material Nodes", "Material Node Groups", "NODE", 2 ** 3),
    ("Geometry Nodes", "Geometry Nodes", "Node Groups", "NODETREE", 2 ** 4),
    ("Collections", "Collections", "Collections", "OUTLINER_COLLECTION", 2 ** 5),
    # ("hair_curves", "Hairs", "Hairs", "CURVES_DATA", 2 ** 7),
    # ("brushes", "Brushes", "Brushes", "BRUSH_DATA", 2 ** 8),
    # ("cache_files", "Cache Files", "Cache Files", "FILE_CACHE", 2 ** 9),
    # ("linestyles", "Freestyle Linestyles", "", "LINE_DATA", 2 ** 10),
    # ("images", "Images", "Images", "IMAGE_DATA", 2 ** 11),
    # ("masks", "Masks", "Masks", "MOD_MASK", 2 ** 13),
    # ("movieclips", "Movie Clips", "Movie Clips", "FILE_MOVIE", 2 **14),
    # ("paint_curves", "Paint Curves", "Paint Curves", "CURVE_BEZCURVE", 2 ** 15),
    # ("palettes", "Palettes", "Palettes", "COLOR", 2 ** 16),
    # ("particles", "Particle Systems", "Particle Systems", "PARTICLES", 2 ** 17),
    # ("scenes", "Scenes", "Scenes", "SCENE_DATA", 2 ** 18),
    # ("sounds", "Sounds", "Sounds", "SOUND", 2 ** 19),
    # ("Text", "Texts", "Texts", "TEXT", 2 ** 20),
    # ("Texture", "Textures", "Textures", "TEXTURE_DATA", 2 ** 21),
    # ("workspaces", "Workspaces", "Workspaces", "WORKSPACE", 2 ** 22),

    ]
def get_types(*args, **kwargs):
    return asset_types

render_types =[    
    ("Mat_Shaderball","Shaderball","Use Shaderball Preview","MATSHADERBALL",2 ** 1),
    ("Mat_Cube", "Cube","Use Cube as Preview","MESH_CUBE",2 ** 2),
    ("Mat_Plane", "Plane","Mat_Plane","MESH_PLANE",2 ** 3),
    ("Mat_Sphere", "Sphere","Mat_Sphere","SPHERE",2 ** 4),
    ("Mat_Monkey", "Monkey","Mat_Monkey","MONKEY",2 ** 5),
    ]
def get_render_types(*args, **kwargs):
    return render_types

def set_selected_assets(assets):
    global selected_assets
    selected_assets = assets

def get_asset_props():
    return bpy.context.scene.asset_props



def get_selected_assets():
    selected_assets = bpy.context.selected_objects
    asset_props = bpy.context.scene.asset_props
    if asset_props.exclude_extras:
        selected_assets = [asset for asset in selected_assets if asset.type not in EXCLUDE_TYPES]
    return selected_assets

def get_selected_ids(self,context):
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'OUTLINER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        return context.selected_ids


def get_icon_for_asset_type(asset_type):
    icons = {
        'Objects': 'OBJECT_DATA',
        'Collections':'OUTLINER_COLLECTION',
        'Materials':'MATERIAL',
        'Material Nodes':'NODETREE',
        'Geometry Nodes':'NODETREE',
    }
    return icons.get(asset_type, 'QUESTION')


def filter_assets(selected_assets, asset_type):
        hierarchy = build_hierarchy(selected_assets, asset_type)
        return [h for h in hierarchy if get_filter_asset_type(asset_type).filter_func(h)]

def set_render_settings(context,render_scene):
    asset_props = get_asset_props()
    print('set render settings')
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "OPTIX"
    render_scene.cycles.device = 'GPU'
    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    render_scene.cycles.samples = 128
    render_scene.render.engine = 'CYCLES'
    render_scene.cycles.feature_set = 'SUPPORTED'
    render_scene.cycles.device = 'GPU'
    render_scene.render.film_transparent = context.scene.asset_props.background_transparent
    render_scene.render.image_settings.color_mode = 'RGBA'
    render_scene.render.image_settings.file_format = 'PNG'
    render_scene.render.resolution_x = 256
    render_scene.render.resolution_y = 256
    render_scene.use_nodes = True
    nodes = render_scene.node_tree.nodes


    links = render_scene.node_tree.links
    link = links.new
    logo_setup_node = nodes.get('Logo_Setup')
    composite_node = nodes.get('Composite')
    ph_out = nodes.get('File_PH_Out')

    
    render_logo =asset_props.enable_ub_logo
    logo_output = "Original" if render_logo else "No Logo Original"
   
    link(logo_setup_node.outputs[logo_output], composite_node.inputs["Image"])
    if context.scene.asset_props.asset_types in ['Materials','Material Nodes']:
        render_type = context.scene.asset_props.render_types in ['Mat_Shaderball']
        logo_output = "Original" if not render_type else "No Logo Original"
        link(logo_setup_node.outputs[logo_output], composite_node.inputs["Image"])
            
        


def set_light_settings(context,render_scene):
    print('set light settings')
    light_setup = context.scene.light_setup.removesuffix('.png')
    backdrop = render_scene.collection.children['Backdrop']
    render_scene.view_layers[0].layer_collection.children['Backdrop'].hide_viewport = not context.scene.asset_props.enable_backdrop
    backdrop.hide_render = not context.scene.asset_props.enable_backdrop
    backdrop_plane = backdrop.objects.get('Backdrop_Plane')
    backdrop_plane['Backdrop_Color'] = context.scene.asset_props.backdrop_color
    backdrop_plane['Emissive_Strength'] = context.scene.asset_props.emissive_strength
    for obj in backdrop.objects:
        obj.visible_camera = not context.scene.asset_props.background_transparent 
    for col in render_scene.collection.children['Light_Setups'].children:
        is_hidden = False if col.name == light_setup else True
        col.hide_render = is_hidden
        render_scene.view_layers[0].layer_collection.children['Light_Setups'].children[col.name].hide_viewport = is_hidden

def import_render_scene(context):
    print('import render scene')
    addon_path = addon_info.get_addon_path()
    preview_render_file_path = os.path.join(addon_path,'BU_plugin_assets','blend_files','Preview_Rendering.blend')
    remove_preview_render_scene()
        
    with bpy.data.libraries.load(preview_render_file_path) as (data_from, data_to):
        data_to.scenes = [s for s in data_from.scenes if s == 'PreviewRenderScene']
    if 'PreviewRenderScene' not in bpy.data.scenes:
        raise Exception("Failed to import PreviewRenderScene")
    
    return bpy.data.scenes['PreviewRenderScene']

def remove_preview_render_scene():
    if 'PreviewRenderScene' in bpy.data.scenes:
        bpy.data.scenes.remove(bpy.data.scenes['PreviewRenderScene'], do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_recursive=True,do_linked_ids=True)


def setup_preview_col(context):
    if 'UB_Preview_Col' not in bpy.data.collections:
        preview_col = bpy.data.collections.new('UB_Preview_Col')
    else:
        preview_col = bpy.data.collections.get('UB_Preview_Col')
    if 'UB_Preview_Col' not in context.scene.collection.children:
        context.scene.collection.children.link(preview_col)
    return preview_col

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



def render_asset_hierarchy(layout, hierarchy, selected_asset_type, level=0):
    main_col = layout.column(align=True)
    if level != 0:
        level +=1
    if not hierarchy:
        box = main_col.box()
        row =box.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text="No Assets Found with Type: " + selected_asset_type)
    for item in hierarchy:
            if item and hasattr(item, 'asset') and item.asset:
                row=main_col.row(align=True)
                row.separator(factor=level)  # Indent based on hierarchy level
                if hasattr(item, 'children') and item.children:
                    box=row.box()
                    box_row = box.row(align=True)
                    # box_row.alignment = 'EXPAND'
                    minimized =item.asset.name in AssetOperations.minimized_list
                    icon = 'RIGHTARROW' if minimized else 'DOWNARROW_HLT'
                    depress = True if minimized else False
                    op = box_row.operator("ub.minimize_asset_details", text="", icon=icon, depress=depress, emboss=False)
                    op.asset_name = item.asset.name
                    box_row.separator(factor=1)
                    box_row.label(text=item.asset.name, icon=get_icon_for_asset_type(item.asset_type))
                    if selected_asset_type == 'Material Nodes' and item.asset.id_type == 'OBJECT':
                        pass
                    else:
                        if len(item.children) > 1:
                            AssetOperations.op_exclude_all(box_row, item.children)
                            AssetOperations.op_mark_clear_children(box_row, item.asset, selected_asset_type)
                else:
                    if level != 0 and item.asset_type != selected_asset_type:
                        row.label(text="", icon='BLANK1')  # Placeholder for leaf nodes   
                    
                if item.asset_type == selected_asset_type  and not item.children:
                    ui_asset_data(row, item.asset_type, item.asset,selected_asset_type)

                # Render children immediately after the parent
                if hasattr(item, 'children') and item.children and not minimized:
                    child_col = main_col.column(align=True)
                    render_asset_hierarchy(child_col, item.children, selected_asset_type, level + 1)
                    child_col.separator(factor=0.5)
            else:
                row = main_col.row(align=True)
                row.label(text="Invalid item in hierarchy")

def get_child_assets(asset, asset_type):
    if asset.id_type == 'OBJECT':
        if asset_type == 'Materials':
            return [slot.material for slot in asset.material_slots if slot.material]
        elif asset_type == 'Geometry Nodes':
            return [mod.node_group for mod in asset.modifiers if mod.type == 'NODES']
    if asset.id_type == 'MATERIAL' and asset_type == 'Material Nodes':
            child_assets = []
            for node in asset.node_tree.nodes:
                if node.type == 'GROUP':
                    child_assets.append(node.node_tree)
            return child_assets
    return []

def get_asset_from_datatype(asset_name, asset_type):
    data_collection=getattr(bpy.data, AssetOperations.asset_types[asset_type])
    return data_collection.get(asset_name)

def filter_objects(item):
    return item.asset

def filter_collections(item):
    return item.asset

def filter_materials(item):
    return any(
        slot.material
        for slot in item.asset.material_slots
    )

def filter_material_nodes(item):
    return any(
        slot.material and 
        slot.material.node_tree and 
        any(node.type == 'GROUP' for node in slot.material.node_tree.nodes)
        for slot in item.asset.material_slots
    )

def filter_geometry_nodes(item):
    return any(mod.type=='NODES' for mod in item.asset.modifiers)
    

def ui_asset_data(layout,asset_type,asset,selected_asset_type):
    def has_previews(asset):
        asset_preview_dir = addon_info.get_asset_preview_path()
        ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
        path = f'{asset_preview_dir}{os.sep}preview_{asset.name}.png'
        ph_path = f'{ph_asset_preview_path}{os.sep}PH_preview_{asset.name}.png'
        if os.path.exists(path):
            return 'IMAGE_RGB_ALPHA'
        else:
            return 'SHADING_BBOX'
    icon = get_icon_for_asset_type(asset_type)

    AssetOperations.op_exclude_asset(layout,asset)
    row = layout.row(align=True)
    row.alignment = 'EXPAND'
    row.enabled =False if asset.name in AssetOperations.exclude_list else True
    row.prop(asset,'name',text='',icon=icon)
    if selected_asset_type == 'Objects':
        if asset.parent:
            if asset.parent_type == 'OBJECT':
                parent_op =row.operator('ub.object_clear_parent',text='',icon='UNLINKED')
                parent_op.asset_name = asset.name
                parent_op.asset_type = selected_asset_type

    mark_text='Mark'  if not asset.asset_data else 'Clear'
    mark_icon ='ASSET_MANAGER' if not asset.asset_data else 'CANCEL'
    mark_depress=False if not asset.asset_data else True
    mark_op = row.operator('ub.mark_or_clear_asset',text=mark_text,icon=mark_icon,depress=mark_depress)
    mark_op.asset_name = asset.name
    mark_op.asset_type = selected_asset_type

    row.label(text='',icon=has_previews(asset))
    row = layout.row(align=True)
    row.enabled = True if asset.asset_data and asset.name not in AssetOperations.exclude_list else False
    metadata_op = row.operator('ub.asset_metadata', text="Metadata", icon='TEXT')
    metadata_op.asset_name = asset.name
    metadata_op.asset_type = selected_asset_type


def pack_object_mat_images_recursive(asset):
    material = has_materials(asset)
    if material:
        pack_images(material)
    if asset.children_recursive:
        for obj in asset.children_recursive:
            material = has_materials(obj)
            if material:
                pack_images(material)

def has_materials(obj):
    if obj.material_slots:
        for slot in obj.material_slots:
            material =slot.material
            if slot.material:
                return material
    return None
    
def pack_images(material):
    if hasattr(material, "node_tree"):
        if hasattr(material.node_tree, "nodes"):
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    if node.image:
                        if node.image.packed_file == None:
                            node.image.pack()

def has_previews(asset):
    # Iterate through asset's material slots and add them to mats
    asset_preview_dir = addon_info.get_asset_preview_path()
    ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
    path = f'{asset_preview_dir}{os.sep}preview_{asset.name}.png'
    ph_path = f'{ph_asset_preview_path}{os.sep}PH_preview_{asset.name}.png'
    # if os.path.exists(path) and os.path.exists(ph_path):
    if os.path.exists(path):
        return 'IMAGE_RGB_ALPHA'
    else:
        return 'SHADING_BBOX'
    

def assign_previews(context,asset):
    asset_preview_path = addon_info.get_asset_preview_path()
    path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
    
    if os.path.exists(path):
        if version_handler.latest_version(context):
            with bpy.context.temp_override(id=asset):
                bpy.ops.ed.lib_id_load_custom_preview(
                filepath = path
                )
        else:
            bpy.ops.ed.lib_id_load_custom_preview(
                {"id": asset}, 
                filepath = path
                )
    else:
        with bpy.context.temp_override(id=asset):
            asset.asset_generate_preview()

def register():
    addon_path = addon_info.get_addon_path()
    light_setups_path = os.path.join(addon_path,'BU_plugin_assets','light_setups')
    pcoll = bpy.utils.previews.new()
    pcoll.images_location = light_setups_path
    preview_collections["thumbnail_previews"] = pcoll

def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()