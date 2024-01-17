import os
import bpy
from pathlib import Path

import addon_utils
from bpy.app.handlers import persistent
from datetime import datetime, timezone
import textwrap
from . import version_handler
from .addon_logger import addon_logger
from .constants import(
    core_lib_folder_id,
    ph_core_lib_folder_id,
    premium_lib_folder_id,
    ph_premium_lib_folder_id,
    test_core_lib_folder_id,
    ph_test_core_lib_folder_id,
    test_premium_lib_folder_id,
    ph_test_premium_lib_folder_id,
    user_upload_folder_id,   
    )

# flags_enum = iter(range(1, 100, 1))
asset_types = [
    # ("actions", "Actions", "Action", "ACTION", 2 ** 1),
    ("Object", "Object", "Object", "OBJECT_DATA", 2 ** 1),
    ("Material", "Materials", "Materials", "MATERIAL", 2 ** 2),
    # ("worlds", "Worlds", "Worlds", "WORLD", 2 ** 4),
    ("Geometry_Node", "Geometry Nodes", "Node Groups", "NODETREE", 2 ** 5),
    # ("Collection", "Collection", "Collections", "OUTLINER_COLLECTION", 2 ** 6),
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
# asset_types.sort(key=lambda t: t[0])
def get_types(*args, **kwargs):
    return asset_types

def get_data_types():
    return [
        'objects',
        'collections',
        'node_groups',
        'materials'
    ]

def type_mapping ():
    return {
    "OBJECT": "objects",
    "MATERIAL": "materials",
    "WORLD": "worlds",
    "NODETREE": "node_groups",
    "COLLECTION": "collections",
    "Material":"materials",
    "ShaderNodeTree": "node_groups",
    "Object": "objects",
    "Collection": "collections",
    "GeometryNodeTree": "node_groups",
    }


def get_object_type():
    return[
        ("ARMATURE", "Armature", "Armature", "ARMATURE_DATA", 2 ** 1),
        ("CAMERA", "Camera", "Camera", "CAMERA_DATA", 2 ** 2),
        ("CURVE", "Curve", "Curve", "CURVE_DATA", 2 ** 3),
        ("EMPTY", "Empty", "Empty", "EMPTY_DATA", 2 ** 4),
        ("GPENCIL", "Grease Pencil", "Grease Pencil", "OUTLINER_DATA_GREASEPENCIL", 2 ** 5),
        ("LIGHT", "Light", "Light", "LIGHT", 2 ** 6),
        ("LIGHT_PROBE", "Light Probe", "Light Probe", "OUTLINER_DATA_LIGHTPROBE", 2 ** 7),
        ("LATTICE", "Lattice", "Lattice", "LATTICE_DATA", 2 ** 8),
        ("MESH", "Mesh", "Mesh", "MESH_DATA", 2 ** 9),
        ("META", "Metaball", "Metaball", "META_DATA", 2 ** 10),
        ("POINTCLOUD", "Point Cloud", "Point Cloud", "POINTCLOUD_DATA", 2 ** 11),
        ("SPEAKER", "Speaker", "Speaker", "OUTLINER_DATA_SPEAKER", 2 ** 12),
        ("SURFACE", "Surface", "Surface", "SURFACE_DATA", 2 ** 13),
        ("VOLUME", "Volume", "Volume", "VOLUME_DATA", 2 ** 14),
        ("FONT", "Text", "Text", "FONT_DATA", 2 ** 15),
    ]

class WM_OT_RedrawArea(bpy.types.Operator):
    bl_idname = "wm.redraw"
    bl_label = "Redraw"
    bl_description = "Refresh current area"
    bl_options = {"REGISTER"}

    def execute(self, context):
        context.area.tag_redraw()
        # redraw(self,context, context.area.type)
        return {'FINISHED'}

def redraw(self, context,area_type):
    if context.screen is not None:
        for a in context.screen.areas:
            if a.type == area_type:
                a.tag_redraw()

def get_addon_path():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == 'Blender Universe':
            filepath = mod.__file__
            return os.path.dirname(os.path.realpath(filepath))
        
def get_addon_blend_files_path():
    addon_path = get_addon_path()
    return os.path.join(addon_path,'BU_plugin_assets','blend_files')

def get_path():
    return os.path.dirname(os.path.realpath(__file__))

def No_lib_path_warning():
       return print('Could not find Library path. Please add a library path in the addon preferences!')

def get_addon_name():
    package = __package__
    try:
        name = package.removesuffix('.utils')
        addon_name = bpy.context.preferences.addons[name]
        return addon_name
    except:
        raise ValueError("couldnt get Name of addon")

def get_addon_prefs():
    return get_addon_name().preferences

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
                return (datablock[asset_name],datablock)
        
        return None,None
    except Exception as error_message:
        print(f"An error occurred finding asset by name: {error_message}")
        

def calculate_dynamic_chunk_size(file_size):
    try:
        addon_prefs = get_addon_name().preferences
        file_size_mb = file_size / (1024 * 1024)
        # If file size is less than 1 MB, download in one chunk
        if file_size_mb <= 1:  # 1 MB
            return min(file_size, addon_prefs.max_chunk_size * 1024)
        # For files larger than 10 MB, use a larger chunk size (e.g., 5 MB)
        if file_size_mb > 10:
            larger_chunk_size = 5 * 1024 * 1024  # 5 MB

            return larger_chunk_size
        # Calculate chunk size based on percentage
        percentage = addon_prefs.chunk_size_percentage / 100
        calculated_size = file_size * percentage

        # Adjust chunk size to be a multiple of 256 KB
        chunk_size_256kb = 256 * 1024  # 256 KB in bytes
        adjusted_chunk_size = (calculated_size + chunk_size_256kb - 1) // chunk_size_256kb * chunk_size_256kb
        return adjusted_chunk_size
    except Exception as error_message:
        print('Error calculating chunk size:',error_message)
    


def get_core_asset_library():
    addon_prefs = get_addon_name().preferences
    core_name =get_lib_name(True,addon_prefs.debug_mode)
    dir_path = addon_prefs.lib_path
    core_path = os.path.join(dir_path,core_name)

    if dir_path !='':
        if not Path(core_path).exists():
            add_library_paths()
            if core_name in bpy.context.preferences.filepaths.asset_libraries:
                core_lib = bpy.context.preferences.filepaths.asset_libraries[core_name]
                return core_lib
            
        if core_name in bpy.context.preferences.filepaths.asset_libraries:
            core_lib = bpy.context.preferences.filepaths.asset_libraries[core_name]
            if core_lib.path != core_path:
                core_lib.path = core_path
                return core_lib
            return core_lib
        else:
            #TODO RAISE ERROR
            print('Error getting BU_AssetLibrary_Core')

    else:
        No_lib_path_warning()

# This is temporary. needs to be changed and hooked to validation unlock 
def get_premium_asset_library():
    addon_prefs = get_addon_name().preferences
    premium_name =get_lib_name(True,addon_prefs.debug_mode)
    dir_path = addon_prefs.lib_path
    premium_path = os.path.join(dir_path,premium_name)

    if dir_path !='':
        if premium_name in bpy.context.preferences.filepaths.asset_libraries:
            premium_lib = bpy.context.preferences.filepaths.asset_libraries[premium_name]
            if premium_lib.path != premium_path:
                premium_lib.path = premium_path
                return premium_lib
            return premium_lib
    else:
        No_lib_path_warning()

def get_lib_name(is_premium,debug_mode):
    if debug_mode:
        return "TEST_BU_AssetLibrary_Premium" if is_premium else "TEST_BU_AssetLibrary_Core"
    else:
        return "BU_AssetLibrary_Premium" if is_premium else "BU_AssetLibrary_Core"

def get_target_lib(context):
    
    addon_prefs = get_addon_name().preferences
    debug_mode = addon_prefs.debug_mode
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        current_library_name = version_handler.get_asset_library_reference(context)
        isPremium = current_library_name in ['BU_AssetLibrary_Premium', 'TEST_BU_AssetLibrary_Premium']
        library_name = get_lib_name(isPremium, debug_mode)
        target_lib = context.preferences.filepaths.asset_libraries[library_name]
        return target_lib
                
def get_local_selected_assets(context):
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        asset_lib_ref = version_handler.get_asset_library_reference(context)
        if asset_lib_ref == 'LOCAL':
            selected_assets = version_handler.get_selected_assets(context)
            return selected_assets
        return None
                
def is_lib_premium():
    
    current_library_name = version_handler.get_asset_library_reference(bpy.context)
    isPremium = current_library_name in ['BU_AssetLibrary_Premium', 'TEST_BU_AssetLibrary_Premium']
    return isPremium

def get_asset_browser_window_area(context):
    for window in context.window_manager.windows:
        screen = window.screen
        if 'FILE_BROWSER' in [area.type for area in screen.areas]:
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    return window,area
        else:
            return None,None

           
                


def set_drive_ids(context):
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    current_library_name = version_handler.get_asset_library_reference(context)
                    if current_library_name == 'BU_AssetLibrary_Core':
                        set_core_download_server_ids()
                    elif current_library_name == 'TEST_BU_AssetLibrary_Core':
                        set_core_download_server_ids()
                    elif current_library_name == 'BU_AssetLibrary_Premium':
                        set_premium_download_server_ids()
                    elif current_library_name == 'TEST_BU_AssetLibrary_Premium':
                        set_premium_download_server_ids()
                    elif current_library_name == 'LOCAL':
                        set_local_server_ids(context)
                        
def set_core_download_server_ids():
    addon_prefs = get_addon_name().preferences
    if addon_prefs.debug_mode:
        addon_prefs.download_folder_id =test_core_lib_folder_id
        addon_prefs.download_folder_id_placeholders=ph_test_core_lib_folder_id
        addon_prefs.download_catalog_folder_id= ph_test_core_lib_folder_id
    else:
        addon_prefs.download_folder_id = core_lib_folder_id
        addon_prefs.download_folder_id_placeholders = ph_core_lib_folder_id
        addon_prefs.download_catalog_folder_id = ph_core_lib_folder_id

        

def set_premium_download_server_ids():
    addon_prefs = get_addon_name().preferences
    if addon_prefs.debug_mode:
        addon_prefs.download_folder_id = test_premium_lib_folder_id
        addon_prefs.download_folder_id_placeholders = ph_test_premium_lib_folder_id
        addon_prefs.download_catalog_folder_id = ph_test_premium_lib_folder_id
    else:
        addon_prefs.download_folder_id = premium_lib_folder_id
        addon_prefs.download_folder_id_placeholders = ph_premium_lib_folder_id
        addon_prefs.download_catalog_folder_id = ph_premium_lib_folder_id

def set_local_server_ids(context):
    addon_prefs = get_addon_name().preferences
    library_target =context.scene.upload_target_enum.switch_upload_target
    if library_target == 'core_upload':
        addon_prefs.test_upload_folder_id = test_core_lib_folder_id
        addon_prefs.test_upload_placeholder_folder_id = ph_test_core_lib_folder_id    
    elif library_target == 'premium_upload':
        addon_prefs.test_upload_folder_id = test_premium_lib_folder_id
        addon_prefs.test_upload_placeholder_folder_id = ph_test_premium_lib_folder_id    
        


def convert_to_UTC_datetime(l_time,g_time):
    l_datetime = datetime.fromtimestamp(l_time, tz=timezone.utc)
    g_datetime = datetime.fromisoformat(g_time.replace('Z', '+00:00'))
    return (l_datetime,g_datetime)

def get_current_file_location():
    return bpy.data.filepath

def get_core_cat_file():
    context = bpy.context
    corelib = get_core_asset_library()
    catfile = os.path.join(corelib.path,'blender_assets.cats.txt')
    if catfile is not None:
        return catfile

def get_upload_cat_file():
    uploadlib = get_upload_asset_library()
    catfile = os.path.join(uploadlib.path,'blender_assets.cats.txt')
    if catfile is not None:
        return catfile
    
def get_catalog_trick_uuid(path):   
    
    target_catalog = "Catalog"
    if os.path.exists(path):
        with open(file=path) as f:
            for line in f.readlines():
                if line.startswith(("#", "VERSION", "\n")):
                    continue
                # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
                name = line.split(":")[2].split("\n")[0]
                if name == target_catalog:
                    uuid = line.split(":")[0]
                    return uuid
                
    


def get_upload_asset_library():
    context = bpy.context
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    if dir_path !='':
        lib_username = "BU_User_Upload"
        user_dir_path =os.path.join(dir_path,lib_username) 
        if not Path(user_dir_path).exists():
            add_user_upload_folder(dir_path) 
        return user_dir_path
    

def get_author():
    author = get_addon_name().preferences.author
    if author == '':
        author = 'Anonymous'
    return author

    
def add_user_upload_folder():
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    lib_username = "BU_User_Upload"
    user_dir_path =os.path.join(dir_path,lib_username)    
    if os.path.exists(dir_path):
        if dir_path != "":
            if not os.path.isdir(str(user_dir_path)): # checks whether the directory exists
                os.mkdir(str(user_dir_path)) # if it does not yet exist, makes it
            # No need to create a library. its not used as a library only a folder holding the zipped assets to upload
            bpy.ops.wm.save_userpref()
            return user_dir_path
        

def update_core_library_path():
    #TODO: This needs changing. We need to check for existing assets and copy them.
    #We need to make sure all paths exist in the new location else call add_library_paths
    #Then remove the old libraries
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    if dir_path != "":
        bpy.ops.preferences.asset_library_add(directory = dir_path, check_existing = True)
        return dir_path
    bpy.ops.wm.save_userpref()
    return dir_path
 
def get_original_lib_names():
    return (
        'BU_AssetLibrary_Core',
        'BU_AssetLibrary_Premium',
        'BU_User_Upload',
        'TEST_BU_AssetLibrary_Core',
        'TEST_BU_AssetLibrary_Premium',
        'BU_AssetLibrary_Deprecated',
    )

def get_test_lib_names():
    return (
        'TEST_BU_AssetLibrary_Core',
        'TEST_BU_AssetLibrary_Premium',
    )

def get_bu_lib_names():
    return (
        'BU_AssetLibrary_Core',
        'BU_AssetLibrary_Premium',
    )

def get_or_create_lib_path_dir(dir_path,lib_name):
    if os.path.exists(dir_path):
        lib_path = os.path.join(dir_path,lib_name)
        if not os.path.isdir(str(lib_path)):
            os.mkdir(str(lib_path))
            addon_logger.info(f'Created Library path because it did not exist: {lib_name}')
    return lib_path

def add_library_to_blender(dir_path,lib_name):
    if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
        lib_path = get_or_create_lib_path_dir(dir_path,lib_name)
        bpy.ops.preferences.asset_library_add(directory = lib_path, check_existing = True)
        addon_logger.info(f'Added Library to blender because it did not exist: {lib_name}')
    lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    return lib


def get_asset_library(dir_path,lib_name):
    lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    # check if the existing directory is the same as the directory set in addon_prefs.lib_path
    if lib:
        lib_dirpath,_ = os.path.split(lib.path)
        if lib_dirpath != dir_path:
            lib.path = os.path.join(dir_path,lib_name)
            lib.name = lib_name
            addon_logger.info(f'Library found but directory was different. Adjusted to the correct one for library: {lib_name}')
        addon_logger.info(f'Library found: {lib_name}')   
    return lib

def try_switch_to_library(dir_path,lib_name,target_lib_name):
    
    lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
    if lib:
        #check if target lib path exists, if so we can switch to target lib
        lib_path = os.path.join(dir_path,target_lib_name)
        if os.path.exists(lib_path):
            lib.path = os.path.join(dir_path,target_lib_name)
            lib.name = target_lib_name
            addon_logger.info(f'Library found and switched to {target_lib_name}')
            return True
        return False
            

def remove_library_from_blender(lib_name):
    if lib_name in bpy.context.preferences.filepaths.asset_libraries:
        lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
        lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
        if lib:
            if lib_index != -1:
                bpy.ops.preferences.asset_library_remove(index=lib_index)
                addon_logger.info(f'Removed library from blender: {lib_name}')


# if any of our libs does not exist, create it. Called on event Load post
def add_library_paths():
    BU_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium')
    addon_prefs = get_addon_prefs()
    dir_path = addon_prefs.lib_path
    
    lib_names = get_original_lib_names()
      
    # if lib_path is empty see if we can get it frome existing BU libraries
    if addon_prefs.lib_path == '':
        dir_path = find_lib_path(addon_prefs,lib_names)

    #check if upload folder exists if not make it
    get_or_create_lib_path_dir(dir_path,'BU_User_Upload')
    for lib_name in BU_lib_names:
        test_lib_name ='TEST_'+lib_name
       
        if addon_prefs.debug_mode:
            lib_name = test_lib_name
            if lib_name in bpy.context.preferences.filepaths.asset_libraries:
                try_switch_to_library(dir_path,lib_name,test_lib_name)
        else:
            if test_lib_name in bpy.context.preferences.filepaths.asset_libraries:
                switched = try_switch_to_library(dir_path,test_lib_name,lib_name)
                if not switched:
                    remove_library_from_blender(test_lib_name)

        get_or_create_lib_path_dir(dir_path,lib_name)
        lib = get_asset_library(dir_path,lib_name)
        if not lib:
            lib = add_library_to_blender(dir_path,lib_name)


    # check if BU libraries exist else create them
    # for lib_name in BU_lib_names:
    #     if os.path.exists(dir_path):
    #         lib_path = os.path.join(dir_path,lib_name)
    #         test_lib_path = os.path.join(dir_path,'TEST_'+lib_name)
    #         if not addon_prefs.debug_mode:
    #             #if TEST libs exist but debug mode is false try to rename them to original if the originals exist
    #             test_lib_name = 'TEST_'+lib_name
    #             lib =bpy.context.preferences.filepaths.asset_libraries.get(test_lib_name)
    #             lib_index = bpy.context.preferences.filepaths.asset_libraries.find(test_lib_name)
    #             if lib:
    #                 path = os.path.join(dir_path,lib_name)
    #                 if os.path.exists(path):
    #                     print(os.path.join(dir_path,lib_name))
    #                     lib.path = os.path.join(dir_path,lib_name)
    #                     lib.name = lib_name
    #                 else:
    #                     bpy.ops.preferences.asset_library_remove(index=lib_index)
    #                     print('Removed library', lib_index)
                    

    #             if not os.path.isdir(str(lib_path)):
    #                 os.mkdir(str(lib_path))
                    
    #                 print('Created directory and library path', os.path.isdir(str(lib_path)))
    #         else:
    #             if not os.path.isdir(str(test_lib_path)):
                    
    #                 os.mkdir(str(test_lib_path)) 
    #                 print('Created directory and library path', os.path.isdir(str(test_lib_path)))

    #         if lib_name !='BU_User_Upload':
    #             lib_name = 'TEST_'+lib_name if addon_prefs.debug_mode else lib_name
    #             if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
    #                 lib_path = os.path.join(dir_path,lib_name)
    #                 bpy.ops.preferences.asset_library_add(directory = lib_path, check_existing = True)
    #             else:
    #                 lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    #                 if lib:
    #                     lib_dirpath,_ = os.path.split(lib.path)
    #                     if lib_dirpath != dir_path:
    #                         lib.path = os.path.join(dir_path,lib_name)
    #                         lib.name = lib_name
            
        bpy.ops.wm.save_userpref()   
            

            


#Look if any of our libraries excists and extract the path from it
def find_lib_path(addon_prefs,lib_names):
    for lib_name in lib_names:
        
        if lib_name in bpy.context.preferences.filepaths.asset_libraries:
            lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
            if lib_name.startswith('TEST_'):
                if addon_prefs.debug_mode == False:
                    dir_path,lib_name = os.path.split(lib.path)
                    lib_name.removeprefix('TEST_')
                    lib.path = os.path.join(dir_path,lib_name)
                    lib.name = lib_name

            if lib:
                dir_path,lib_name = os.path.split(lib.path)
                addon_prefs.lib_path = dir_path
                return dir_path
        
    dir_path = ''
    return dir_path

# Does not work!!
def refresh(self, context,library_name):
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                version_handler.set_asset_library_reference(context,library_name)
                asset_lib_ref = version_handler.get_asset_library_reference(context)
                if asset_lib_ref == library_name:
                    bpy.ops.asset.catalog_new()
                    bpy.ops.asset.catalogs_save()
                    lib = bpy.context.preferences.filepaths.asset_libraries[library_name]
                    path = os.path.join(lib.path, 'blender_assets.cats.txt')
                    uuid = get_catalog_trick_uuid(path)
                    if uuid:
                        bpy.ops.asset.catalog_delete(catalog_id=uuid)
    bpy.ops.asset.library_refresh()

# Does not work!!
def refresh_override(self, context,library_name):
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        version_handler.set_asset_library_reference(context,library_name)
        asset_lib_ref = version_handler.get_asset_library_reference(context)
        if asset_lib_ref == library_name:
            bpy.ops.asset.catalog_new()
            bpy.ops.asset.catalogs_save()
            lib = bpy.context.preferences.filepaths.asset_libraries[library_name]
            path = os.path.join(lib.path, 'blender_assets.cats.txt')
            uuid = get_catalog_trick_uuid(path)
            if uuid:
                bpy.ops.asset.catalog_delete(catalog_id=uuid)
        
def set_upload_target(self,context):
    upload_target = context.scene.upload_target_enum.switch_upload_target
    addon_prefs = get_addon_name().preferences
    if upload_target == 'core_upload':
        addon_prefs.upload_folder_id = user_upload_folder_id if addon_prefs.debug_mode == False else test_core_lib_folder_id
        addon_prefs.upload_placeholder_folder_id = ph_test_core_lib_folder_id
        addon_prefs.download_catalog_folder_id = ph_test_core_lib_folder_id
    elif upload_target == 'premium_upload':
        addon_prefs.upload_folder_id = user_upload_folder_id if addon_prefs.debug_mode == False else test_premium_lib_folder_id
        addon_prefs.upload_placeholder_folder_id = ph_test_premium_lib_folder_id
        addon_prefs.download_catalog_folder_id = ph_test_premium_lib_folder_id

def get_asset_preview_path():
    addon_prefs = get_addon_name().preferences
    addon_prefs.thumb_upload_path
    if os.path.exists(addon_prefs.thumb_upload_path):
        
        ph_preview_dir = os.path.join(addon_prefs.thumb_upload_path, 'Placeholder_Previews')
        if not os.path.exists(ph_preview_dir):
            os.mkdir(ph_preview_dir)
    return addon_prefs.thumb_upload_path

def get_placeholder_asset_preview_path():
    asset_preview_path = get_asset_preview_path()
    return os.path.join(asset_preview_path, 'Placeholder_Previews')

def get_addon_blend_files_path():
    addon_path = get_addon_path()
    return os.path.join(addon_path,'BU_plugin_assets','blend_files')

GITBOOKURL ='https://blenderuniverse.gitbook.io/blender-universe/getting-started/'

def gitbook_link(layout,anchor):
    gitbook = layout.operator('wm.url_open',text='',icon='HELP')
    gitbook.url = GITBOOKURL+anchor

class UploadTargetProperty(bpy.types.PropertyGroup):
    switch_upload_target: bpy.props.EnumProperty(
        name = 'Upload target',
        description = "Upload to Core or Premium",
        items=[
            ('core_upload', 'Core', '', '', 0),
            ('premium_upload', 'Premium', '', '', 1)
        ],
        default='core_upload',
        update=set_upload_target
    )

class INFO_OT_custom_dialog(bpy.types.Operator):
    bl_idname = "info.custom_dialog"
    bl_label = "Info Message Dialog"

    title: bpy.props.StringProperty()
    info_message: bpy.props.StringProperty()
    dont_show_again: bpy.props.BoolProperty()
    # new_asset_names: bpy.props.CollectionProperty(type=bpy.types.StringProperty)

    # @classmethod
    # def poll(cls, context):
    #     dont_show_again = cls.dont_show_again
    #     if dont_show_again:
    #         return False
    #     return True

        
    def _label_multiline(self,context, text, parent):
        panel_width = int(context.region.width)   # 7 pix on 1 character
        uifontscale = 9 * context.preferences.view.ui_scale
        max_label_width = int(panel_width // uifontscale)
        wrapper = textwrap.TextWrapper(width=50 )
        text_lines = wrapper.wrap(text=text)
        for text_line in text_lines:
            parent.label(text=text_line,)

    def draw(self, context):
        self.layout.label(text=self.title)
        
        intro_text = self.info_message
        self._label_multiline(
        context=context,
        text=intro_text,
        parent=self.layout
        )
        # self.layout.prop(self, 'dont_show_again', text="Don't show again")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.dont_show_again:
            pass
        else:
            return context.window_manager.invoke_props_dialog(self, width= 300)
        
class BU_OT_OpenAddonLocation(bpy.types.Operator):
    bl_idname = "bu.open_addon_location"
    bl_label = "Open Addon Location"

    def execute(self, context):
        addon_path = get_addon_path()
        os.startfile(addon_path)
        return {'FINISHED'}

classes =(
    UploadTargetProperty, 
    INFO_OT_custom_dialog,
    WM_OT_RedrawArea,
    BU_OT_OpenAddonLocation,
)

@persistent
def on_blender_startup(dummy):
    add_library_paths()
    addon_prefs = get_addon_name().preferences
    if addon_prefs.gumroad_premium_licensekey!='' and addon_prefs.premium_licensekey != '':
        if addon_prefs.toggle_experimental_BU_Premium_panels:
            bpy.ops.bu.validate_gumroad_license()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.upload_target_enum = bpy.props.PointerProperty(type=UploadTargetProperty)
    bpy.app.handlers.load_post.append(on_blender_startup)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.upload_target_enum
    bpy.app.handlers.load_post.remove(on_blender_startup)
    
