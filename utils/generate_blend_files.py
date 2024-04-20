import bpy,os,datetime,json,zipfile,shutil
from . import addon_info,catfile_handler
from .addon_logger import addon_logger
from ..ui import generate_previews
from mathutils import Vector


def write_original_file(asset):
    try:
        original_name = asset.name.removeprefix('temp_')
        asset_types =addon_info.type_mapping()
        data_collection = getattr(bpy.data, asset_types[asset.id_type])
        real_asset = data_collection[asset.name]
        real_asset.name = asset.name.removeprefix('temp_')
        asset_upload_dir = get_asset_upload_folder(original_name)
        asset_upload_file_path = os.path.join(asset_upload_dir,f'{asset.name}.blend')
        BU_Json_Text = create_asset_json_file(asset,is_placeholder=False)
        # save only the selected asset to a new clean blend file and its Asset info as JSON

        datablock ={asset.local_id, BU_Json_Text}
        bpy.data.libraries.write(asset_upload_file_path, datablock)
        
    except Exception as e:
        message =f'error generating original file: {e}'
        print(message)
        log_exception(message)
        raise Exception(message)

def add_asset_tags(asset):
    addon_prefs = addon_info.get_addon_prefs()
    if bpy.app.version >= (4,0,0):
        asset_metadata = asset.metadata
    else:
        asset_metadata = asset.asset_data
    blender_version_tag = f'Blender_{bpy.app.version_string}'
    if 'Original' not in asset_metadata.tags:
        asset_metadata.tags.new(name='Original')
    if addon_prefs.upload_target == 'premium_upload':
        if 'Premium' not in asset_metadata.tags:
            asset_metadata.tags.new(name='Premium')
    if blender_version_tag not in asset_metadata.tags:
        asset_metadata.tags.new(name=blender_version_tag)
    
        

def get_asset_thumb_paths(addon_prefs,original_name):
    addon_prefs = addon_info.get_addon_prefs()
    thumbs_directory = addon_prefs.thumb_upload_path
    asset_thumb_path = os.path.join(thumbs_directory, f'preview_{original_name}')
    if os.path.exists(f'{asset_thumb_path}.png'):
        return f'{asset_thumb_path}.png'
    if os.path.exists(f'{asset_thumb_path}.jpg'):
        return f'{asset_thumb_path}.jpg'
    
    # message ='No valid thumbnail path found, shutdown sync'
    # addon_logger.error(message)
    # print(message)
    # bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Please set a valid thumbnail path in the upload settings!'))
    return ''

def get_asset_upload_folder(original_name):
    try:
        uploadlib = addon_info.get_upload_asset_library()
        path =os.path.join(uploadlib,original_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        return path
    except Exception as e:
        message =f'error getting asset upload folder: {e}'
        log_exception(message)
        raise Exception(message)
def get_placeholder_upload_folder(original_name):
    try:
        uploadlib = addon_info.get_upload_asset_library()
        path =os.path.join(uploadlib,'Placeholders',original_name)
        if not os.path.isdir(path):
            os.makedirs(path)
        return path
    except Exception as e:
        message =f'error getting placeholder upload folder: {e}'
        log_exception(message)
        raise Exception(message)

def create_asset_json_file(asset,is_placeholder):
    try:
        asset_type = asset.id_type if is_placeholder ==False else asset.bl_rna.identifier
        file_name ='BU_OG_Asset_Info' if is_placeholder ==False else 'BU_PH_Asset_Info'

        asset_name =asset.name.removeprefix('temp_')
        asset_info = {
            "BU_Asset": asset_name,
            "Asset_type": asset_type,
            "Placeholder": is_placeholder,
            "Blender_version": bpy.app.version_string
            }
        creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        asset_info['creation_time'] = creation_time
        json_data = json.dumps(asset_info, indent=4)

        BU_Json_Text = bpy.data.texts.get(file_name)
        
        if BU_Json_Text is None:
            BU_Json_Text = bpy.data.texts.new(file_name)
        BU_Json_Text.clear()
        BU_Json_Text.write(json_data)
        return BU_Json_Text
    except Exception as e:
        message =f'error creating asset json file: {e}'
        log_exception(message)
        raise Exception(message)

def get_or_composite_placeholder_preview(asset_thumb_path):
    try:
        thumb_dir,preview_file = os.path.split(asset_thumb_path)
        placeholder_thumb_path = os.path.join(thumb_dir,'Placeholder_Previews','PH_'+preview_file)
        if not os.path.exists(placeholder_thumb_path):
            print('generating placeholder preview via compositor')
            placeholder_thumb_path = generate_previews.composite_placeholder_previews(asset_thumb_path)
            return placeholder_thumb_path
        return placeholder_thumb_path
    except Exception as e:
        message =f'error generating placeholder preview: {e}'
        log_exception(message)
        raise Exception(message)
    
def find_asset_by_name(asset_name):
    try:
        datablock_types = [
            bpy.data.objects,
            bpy.data.materials,
            bpy.data.collections,
            bpy.data.node_groups,
        ]
        
        for datablock in datablock_types:
            if asset_name in datablock:
                return (datablock[asset_name])
        
        return None
    except Exception as error_message:
        print(f"An error occurred finding asset by name: {error_message}")
    
def copy_metadata_to_placeholder(asset,ph_asset):
    addon_prefs = addon_info.get_addon_prefs()
    try:
        if bpy.app.version >= (4,0,0):
            ph_metadata = ph_asset.asset_data
            asset_metadata = asset.metadata
        else:
            ph_metadata = ph_asset.asset_data
            asset_metadata = asset.asset_data
        attributes_to_copy = ['copyright', 'catalog_id', 'description', 'tags','license', 'author',]
        # Copy metadata
        for attr in attributes_to_copy:
            if attr =='tags':
                if 'Placeholder' not in ph_metadata.tags:
                    ph_metadata.tags.new(name='Placeholder')
                
                if addon_prefs.upload_target == 'premium_upload':
                    if 'Premium' not in ph_metadata.tags:
                        ph_metadata.tags.new(name='Premium')
            if hasattr(asset_metadata, attr) and getattr(asset_metadata, attr):
                if attr == 'tags':
                    # Copy each tag individually
                    for tag in getattr(asset_metadata, attr):
                        if tag.name != 'Original' and tag.name != 'Premium':
                            ph_metadata.tags.new(name=tag.name)  
                else:
                    setattr(ph_metadata, attr, getattr(asset_metadata, attr))
    except Exception as e:
        message =f'error copying metadata: {e}'
        log_exception(message)
        raise Exception(message)
    
def copy_and_zip_catfile():
    #copy catfile from current
    upload_lib = addon_info.get_upload_asset_library()
    current_filepath,catfile = os.path.split(catfile_handler.get_current_file_catalog_filepath())
    shutil.copy(os.path.join(current_filepath,catfile), os.path.join(upload_lib,catfile))
    upload_catfile = os.path.join(upload_lib,catfile)
    #zip catfile
    zipped_cat_path = upload_catfile.replace('.txt','.zip')
    zipf = zipfile.ZipFile(zipped_cat_path, 'w', zipfile.ZIP_DEFLATED)
    root_dir,cfile = os.path.split(upload_catfile)
    os.chdir(root_dir) 
    zipf.write(cfile)
    return zipped_cat_path

def lib_id_load_custom_preview(context,asset,placeholder,filepath):
    try:
        asset_types =addon_info.type_mapping()
        data_collection = getattr(bpy.data, asset_types[asset.id_type])         
        ph_asset = data_collection[placeholder.name]
        with context.temp_override(id=ph_asset):

            bpy.ops.ed.lib_id_load_custom_preview(filepath=filepath)
        return 
    except Exception as e:
        log_exception(f'Error in lib_id_load_custom_preview: {e}')
        raise Exception(f'Error in lib_id_load_custom_preview: {e}')

def new_GeometryNodes_group():
    ''' Create a new empty node group that can be used
        in a GeometryNodes modifier.
    '''
    node_group = bpy.data.node_groups.new('GeometryNode_Placeholder', 'GeometryNodeTree')
    group_input : bpy.types.GeometryNodeGroup = node_group.nodes.new('NodeGroupInput')
    group_input.location = (0,0)
    group_output : bpy.types.GeometryNodeGroup = node_group.nodes.new('NodeGroupOutput')
    group_output.location = (300,0)
    if bpy.app.version < (4,0,0):
        node_group.outputs.new('NodeSocketGeometry', 'Geometry')
        node_group.inputs.new('NodeSocketGeometry', 'Geometry')
    else:
        node_group.interface.new_socket(name="Geometry",description="geometry_input",in_out ="INPUT", socket_type="NodeSocketGeometry")
        node_group.interface.new_socket(name="Geometry",description="geometry_output",in_out ="OUTPUT", socket_type="NodeSocketGeometry")
    node_group.links.new(group_input.outputs['Geometry'], group_output.inputs['Geometry'])  
    return node_group
    

def new_node_group_empty(original_name,nodetype):
    node_group =bpy.data.node_groups.new(original_name, nodetype)
    group_input = node_group.nodes.new('NodeGroupInput')
    group_input.location = (0,0)
    group_output = node_group.nodes.new('NodeGroupOutput')
    group_output.location = (300,0)
    node_group.links.new(group_input.outputs[0], group_output.inputs[0])
    return node_group

def create_placeholder(context,addon_prefs,asset):
    original_name = asset.name.removeprefix('temp_')
    add_asset_tags(asset)
    ph_asset = generate_placeholder_file(asset,original_name)
    if ph_asset:
        ph_asset.asset_mark()
        copy_metadata_to_placeholder(asset,ph_asset)
        asset_thumb_path = get_asset_thumb_paths(addon_prefs,original_name)
        if asset_thumb_path != '':
            placeholder_thumb_path = get_or_composite_placeholder_preview(asset_thumb_path)
            lib_id_load_custom_preview(context,asset,ph_asset,placeholder_thumb_path)
        return ph_asset
    else:
        raise Exception(f'Could generate placeholder asset PH_{original_name}')


def generate_placeholder_file(asset,original_name):
    try:
        print('generating placeholder asset')
        addon_logger.info('generating placeholder asset')
        ph_asset = None
        # real_asset.name = tempname
        if asset.id_type == 'OBJECT':
            ph_asset = bpy.data.objects.new(original_name,None)
            if ph_asset:
                return ph_asset
        elif asset.id_type == 'COLLECTION':
            ph_asset = bpy.data.collections.new(original_name)
            return ph_asset
        elif asset.id_type == 'MATERIAL':
            ph_asset = bpy.data.materials.new(original_name)
            if ph_asset:
                return ph_asset
        elif asset.id_type == 'NODETREE':
            nodetype = asset.local_id.bl_idname
            if nodetype in ('ShaderNodeTree','CompositorNodeTree') :
                ph_asset = new_node_group_empty(original_name,nodetype)
                if ph_asset:
                    return ph_asset
            elif nodetype == 'GeometryNodeTree':
                ph_asset = new_GeometryNodes_group()
                if ph_asset:
                    ph_asset.name = original_name
                    return ph_asset
      
            else:
                raise Exception('Node group asset_type not supported')
           
        else:
            return None
    except Exception as e:
        if ph_asset:
            remove_placeholder_asset(ph_asset)
        message = f"Error in Create placeholder and load preview {e}"
        log_exception(message)
        raise Exception(message)
    
def write_placeholder_file(ph_asset):
    try:
        print('writing placeholder asset')
        ph_asset_upload_dir=get_placeholder_upload_folder(ph_asset.name)
        placeholder_folder_file_path = os.path.join(ph_asset_upload_dir,f'PH_{ph_asset.name}.blend')
        BU_Json_Text = create_asset_json_file(ph_asset,is_placeholder=True)

        datablock = {ph_asset,BU_Json_Text}
        bpy.data.libraries.write(placeholder_folder_file_path, datablock)

        return ph_asset
    except Exception as e:
        if ph_asset:
            remove_placeholder_asset(ph_asset)
        message = f"An error occurred in writing placeholder files: {e}"
        log_exception(message)
        raise Exception(message)
     

def zip_directory(folder_path):
    try:
        root_dir,asset_folder = os.path.split(folder_path)
        if root_dir.endswith(f'{os.sep}Placeholders'):
            zip_path = os.path.join(root_dir,f'PH_{asset_folder}.zip')
        else:
            zip_path = os.path.join(root_dir,f'{asset_folder}.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    zipf.write(full_path, rel_path)
        return zip_path
    except Exception as e:
        message=f'error zipping directory: {e}'
        log_exception(message)
        raise Exception(message)

def remove_placeholder_asset(ph_asset):
    asset_types =addon_info.type_mapping()
    data_collection = getattr(bpy.data, asset_types[ph_asset.bl_rna.identifier])
    data_collection.remove(ph_asset)

def log_exception(message):
    print(message)
    addon_logger.error(message)

