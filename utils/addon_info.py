import os
import bpy
from pathlib import Path
def get_path():
    return os.path.dirname(os.path.realpath(__file__))

def get_addon_name():
    package = __package__
    try:
        name = package.removesuffix('.utils')
        # print(f'name : {name}')
        addon_name = bpy.context.preferences.addons[name]
        return addon_name
    except:
        raise ValueError("couldnt get Name of addon")


def get_core_asset_library(context):
    if "BU_AssetLibrary_Core" in bpy.context.preferences.filepaths.asset_libraries:
        lib = bpy.context.preferences.filepaths.asset_libraries["BU_AssetLibrary_Core"]
        if not Path(lib.path).exists():
            return print('Could not find Library path. Please add a library path in the addon preferences!')
        else:
            return lib
    else:
        print('Could not find Library path. Please add a library path in the addon preferences!')
        return

    # for lib in context.preferences.filepaths.asset_libraries:
    #     if lib.name == "BU_AssetLibrary_Core":
    #         if not Path(lib.path).exists():
               

def get_cat_file(context):
    uploadlib = get_upload_asset_library(context)
    catfile = os.path.join(uploadlib.path,'blender_assets.cats.txt')
    if catfile is not None:
        return catfile

def get_upload_asset_library(context):
    core_lib = get_core_asset_library(context)
    if "BU_User_Upload" in context.preferences.filepaths.asset_libraries:
        lib = context.preferences.filepaths.asset_libraries["BU_User_Upload"]   
        if not Path(lib.path).exists():
            add_user_upload_folder(core_lib.path) 

    else:
        add_user_upload_folder(core_lib.path) 
        # lib = bpy.context.preferences.filepaths.asset_libraries[-1]
    lib = context.preferences.filepaths.asset_libraries["BU_User_Upload"]   
    return lib
    # core_lib = get_core_asset_library(context)
    # for lib in context.preferences.filepaths.asset_libraries:
    #     if lib.name == "BU_User_Upload":
    #         if not Path(lib.path).exists():
    #             add_user_upload_folder(core_lib.path) 
    #             lib = bpy.context.preferences.filepaths.asset_libraries[-1]  
    #         return lib


def BULibPath():
    assetlibs = bpy.context.preferences.filepaths.asset_libraries
    for lib in assetlibs:
        if lib.name == "BU_AssetLibrary_Core":
            lib_path = str(lib.path)
        if lib.name == "BU_User_Upload":
            upload_path = str(lib.path)
        return lib_path,upload_path
    
def add_user_upload_folder(bu_lib):
    if bu_lib =="":
        return
    lib_username = "BU_User_Upload"
    user_dir_path =os.path.join(bu_lib,lib_username)    
    # user_dir_path =bu_lib + lib_username
    abs_filepath = bpy.path.abspath(user_dir_path)
    if not os.path.isdir(str(abs_filepath)): # checks whether the directory exists
        os.mkdir(str(user_dir_path)) # if it does not yet exist, makes it
    bpy.ops.preferences.asset_library_add(directory =user_dir_path,  check_existing = True)
    bpy.ops.wm.save_userpref()
    return user_dir_path
    

def add_core_library_path():
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    lib_name = 'BU_AssetLibrary_Core'
    if dir_path != "":
        bpy.ops.preferences.asset_library_add(directory = dir_path, check_existing = True)
        new_library = bpy.context.preferences.filepaths.asset_libraries[-1]
        new_library.name = lib_name
        return dir_path
    bpy.ops.wm.save_userpref()
    return dir_path

def update_core_library_path():
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
    lib_name = 'BU_AssetLibrary_Core'
    lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
    if dir_path != "":
        bpy.ops.preferences.asset_library_add(directory = dir_path, check_existing = True)
        new_library = bpy.context.preferences.filepaths.asset_libraries[-1]
        new_library.name = lib_name
        return dir_path
    bpy.ops.wm.save_userpref()
    return dir_path
