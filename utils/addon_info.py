import os
import bpy
from pathlib import Path

def get_path():
    return os.path.dirname(os.path.realpath(__file__))

def No_lib_path_warning():
       return print('Could not find Library path. Please add a library path in the addon preferences!')

def get_addon_name():
    package = __package__
    try:
        name = package.removesuffix('.utils')
        # print(f'name : {name}')
        addon_name = bpy.context.preferences.addons[name]
        return addon_name
    except:
        raise ValueError("couldnt get Name of addon")


def get_core_asset_library():
    core_name ='BU_AssetLibrary_Core'
    addon_name = get_addon_name()
    dir_path = addon_name.preferences.lib_path
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
    # if "BU_AssetLibrary_Core" in bpy.context.preferences.filepaths.asset_libraries:
    #     lib = bpy.context.preferences.filepaths.asset_libraries["BU_AssetLibrary_Core"]
    #     if not Path(lib.path).exists():
    #         return print('Could not find Library path. Please add a library path in the addon preferences!')
    #     else:
    #         return lib
    # else:
    #     print('Could not find Library path. Please add a library path in the addon preferences!')
        

    # for lib in context.preferences.filepaths.asset_libraries:
    #     if lib.name == "BU_AssetLibrary_Core":
    #         if not Path(lib.path).exists():
               
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
    # else:
    #     No_lib_path_warning()




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
    # user_dir_path =bu_lib + lib_username
    if os.path.exists(dir_path):
        if dir_path != "":
            if not os.path.isdir(str(user_dir_path)): # checks whether the directory exists
                os.mkdir(str(user_dir_path)) # if it does not yet exist, makes it

            # No need to create a library. its not used as a library only a folder holding the zipped assets to upload
            # bpy.ops.preferences.asset_library_add(directory =user_dir_path,  check_existing = True)
            bpy.ops.wm.save_userpref()
            return user_dir_path
    # else:
    #     No_lib_path_warning()
    

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

