import os
import bpy
from pathlib import Path
import addon_utils

def get_addon_path():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == 'Blender Universe':
            filepath = mod.__file__
            return os.path.dirname(filepath)

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


def get_core_asset_library():
    core_name ='BU_AssetLibrary_Core'
    addon_name = get_addon_name()
    addon_prefs = addon_name.preferences
    dir_path = addon_prefs.lib_path
    core_path = os.path.join(dir_path,core_name)

    if dir_path !='':
        if not Path(core_path).exists():
            core_lib = add_core_library_path()
            return core_lib
            
        if "BU_AssetLibrary_Core" in bpy.context.preferences.filepaths.asset_libraries:
            core_lib = bpy.context.preferences.filepaths.asset_libraries["BU_AssetLibrary_Core"]
            if core_lib.path != core_path:
                core_lib.path = core_path
                return core_lib
            return core_lib
        else:
            print()

    else:
        No_lib_path_warning()

# This is temporary. needs to be changed and hooked to validation unlock 
def get_premium_asset_library():
    premium_name ='BU_AssetLibrary_Premium'
    addon_prefs = get_addon_name().preferences
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

def get_target_lib():
    
    current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
    if current_library_name == 'BU_AssetLibrary_Core' or 'BU_AssetLibrary_Premium':
        target_lib = bpy.context.preferences.filepaths.asset_libraries[current_library_name]
    return target_lib
    
def set_drive_ids():
    
    current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
    if current_library_name == 'BU_AssetLibrary_Core':
        set_core_server_ids()
    elif current_library_name == 'BU_AssetLibrary_Premium':
        set_premium_server_ids()

def set_core_server_ids():
    addon_prefs = get_addon_name().preferences
    def default(pref_name):
        return addon_prefs.bl_rna.properties[pref_name].default
    addon_prefs.download_folder_id = default('download_folder_id') if addon_prefs.debug_mode == False else "1COJ6oknO-LDyNx_FP6QPvo80iKrvDXlb"
    addon_prefs.download_folder_id_placeholders = default('download_folder_id_placeholders') if addon_prefs.debug_mode == False else "1Jnc45SV7-zK4ULQzmFSA0pK6JKc8z3DN"
    addon_prefs.upload_parent_folder_id = default('upload_parent_folder_id') if addon_prefs.debug_mode == False else "1dcVAyMUiJ5IcV7QBtQ7a99Jl_DdvL8Qo"

def set_premium_server_ids():
    addon_prefs = get_addon_name().preferences
    addon_prefs.download_folder_id_placeholders = "1FU-do5DYHVMpDO925v4tOaBPiWWCNP_9" if addon_prefs.debug_mode == False else "146BSw9Gw6YpC9jUA3Ehe7NKa2C8jf3e7"
    addon_prefs.upload_parent_folder_id = "1rh2ZrFM9TUJfWDMatbaniCKaXpKDvnkx" if addon_prefs.debug_mode == False else "1IWX6B2XJ3CdqO9Tfbk2m5HdvnjVmE_3-"
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

def BULibPath():
    assetlibs = bpy.context.preferences.filepaths.asset_libraries
    for lib in assetlibs:
        if lib.name == "BU_AssetLibrary_Core":
            lib_path = str(lib.path)
        if lib.name == "BU_User_Upload":
            upload_path = str(lib.path)
        return lib_path,upload_path
    
def add_user_upload_folder(bu_lib):
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
 

def add_core_library_path():
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    lib_name = 'BU_AssetLibrary_Core'
    core_path = os.path.join(dir_path,lib_name)
    if os.path.exists(dir_path):
        print(dir_path)
        if not os.path.isdir(str(core_path)): # checks whether the directory exists
            os.mkdir(str(core_path)) # if it does not yet exist, makes it
            print(os.path.isdir(str(core_path)))
        if dir_path != "":
            bpy.ops.preferences.asset_library_add(directory = core_path, check_existing = True)
            if "BU_AssetLibrary_Core" in bpy.context.preferences.filepaths.asset_libraries:
                core_lib = bpy.context.preferences.filepaths.asset_libraries["BU_AssetLibrary_Core"]
                return core_lib
        else:
            print(dir_path)
    # else:
    #     No_lib_path_warning()
    bpy.ops.wm.save_userpref()

def update_core_library_path():
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    lib_name = 'BU_AssetLibrary_Core'
    lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
    if dir_path != "":
        bpy.ops.preferences.asset_library_add(directory = dir_path, check_existing = True)
        return dir_path
    bpy.ops.wm.save_userpref()
    return dir_path



