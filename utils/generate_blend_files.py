import bpy,os,datetime,json,zipfile,shutil
from . import addon_info,catfile_handler
from .addon_logger import addon_logger
from ..ui import generate_previews


def generate_original_file(asset):
    try:
        asset_upload_dir = get_asset_upload_folder(asset)
        asset_upload_file_path = os.path.join(asset_upload_dir,f'{asset.name}.blend')
        BU_Json_Text = create_asset_json_file(asset,is_placeholder=False)
        # save only the selected asset to a new clean blend file and its Asset info as JSON
        datablock ={asset.local_id, BU_Json_Text}
        bpy.data.libraries.write(asset_upload_file_path, datablock)
        bpy.data.texts.remove(BU_Json_Text)
    except Exception as e:
        message =f'error generating original file: {e}'
        log_exception(message)
        raise Exception(message)

def add_asset_tags(asset):
    if bpy.app.version >= (4,0,0):
        asset_metadata = asset.metadata
    else:
        asset_metadata = asset.asset_data
    blender_version_tag = f'Blender_{bpy.app.version_string}'
    if 'Original' not in asset_metadata.tags:
        asset_metadata.tags.new(name='Original')
    if blender_version_tag not in asset_metadata.tags:
        asset_metadata.tags.new(name=blender_version_tag)
    
        

def get_asset_thumb_paths(asset):
    addon_prefs = addon_info.get_addon_prefs()
    thumbs_directory = addon_prefs.thumb_upload_path
    asset_thumb_path = os.path.join(thumbs_directory, f'preview_{asset.name}')
    if os.path.exists(f'{asset_thumb_path}.png'):
        return f'{asset_thumb_path}.png'
    if os.path.exists(f'{asset_thumb_path}.jpg'):
        return f'{asset_thumb_path}.jpg'
    
    message ='No valid thumbnail path found, shutdown sync'
    addon_logger.error(message)
    print(message)
    bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Please set a valid thumbnail path in the upload settings!'))
    return ''

def get_asset_upload_folder(asset):
    uploadlib = addon_info.get_upload_asset_library()
    path =os.path.join(uploadlib,asset.name)
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

def get_placeholder_upload_folder(asset):
    uploadlib = addon_info.get_upload_asset_library()
    path =os.path.join(uploadlib,'Placeholders',asset.name)
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

def create_asset_json_file(asset,is_placeholder):
    try:
        asset_type = asset.id_type if is_placeholder ==False else asset.bl_rna.identifier
        file_name ='BU_OG_Asset_Info' if is_placeholder ==False else 'BU_PH_Asset_Info'
        asset_info = {
            "BU_Asset": asset.name,
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
            if hasattr(asset_metadata, attr) and getattr(asset_metadata, attr):
                if attr == 'tags':
                    # Copy each tag individually
                    for tag in getattr(asset_metadata, attr):
                        if tag.name != 'Original':
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

def lib_id_load_custom_preview(context,placeholder,filepath):
    try:
        with bpy.context.temp_override(id=placeholder):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=filepath)
    except Exception as e:
        log_exception(f'Error in lib_id_load_custom_preview: {e}')
        raise Exception(f'Error in lib_id_load_custom_preview: {e}')


def generate_placeholder_file(asset):
    try:
        print('generating placeholder asset')
        addon_logger.info('generating placeholder asset')
        if asset.id_type == 'OBJECT':
            ph_asset = bpy.data.objects.new(f'PH_{asset.name}',None)
            return ph_asset
        elif asset.id_type == 'COLLECTION':
            ph_asset = bpy.data.collections.new(f'PH_{asset.name}')
            return ph_asset
        elif asset.id_type == 'MATERIAL':
            ph_asset = bpy.data.materials.new(f'PH_{asset.name}')
            return ph_asset
        elif asset.id_type == 'NODETREE':
            nodetype = asset.local_id.bl_idname
            ph_asset = bpy.data.node_groups.new(f'PH_{asset.name}', nodetype)
            return ph_asset
        else:
            raise Exception('asset_type not supported')
    except Exception as e:
        if ph_asset:
            remove_placeholder_asset(ph_asset)
        message = f"Error in Create placeholder and load preview {e}"
        log_exception(message)
        raise Exception(message)
    
def write_placeholder_file(asset,ph_asset):
    try:
        ph_asset_upload_dir=get_placeholder_upload_folder(asset)
        placeholder_folder_file_path = os.path.join(ph_asset_upload_dir,f'PH_{asset.name}.blend')
        BU_Json_Text = create_asset_json_file(ph_asset,is_placeholder=True)
        #temporary rename asset
        tempname = f'temp_{asset.name}'
        original_name = asset.name
        ph_original_name = ph_asset.name

        asset_types =addon_info.type_mapping()
        data_collection = getattr(bpy.data, asset_types[asset.id_type])
        real_asset = data_collection[asset.name]

        real_asset.name = tempname
        ph_asset.name = original_name
        #write placeholder file
        datablock = {ph_asset, BU_Json_Text}
        bpy.data.libraries.write(placeholder_folder_file_path, datablock)

        #rename back to original names
        ph_asset.name = ph_original_name
        real_asset.name = original_name

        #Remove placeholder asset
        bpy.data.texts.remove(BU_Json_Text)
        return ph_asset
    except Exception as e:
        if ph_asset:
            remove_placeholder_asset(ph_asset)
        message = f"An error occurred in generating files: {e}"
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
                    
        # Remove the original folder
        shutil.rmtree(folder_path)
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
