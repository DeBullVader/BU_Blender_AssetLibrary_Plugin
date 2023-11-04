import os
import bpy
from pathlib import Path
import addon_utils
from bpy.app.handlers import persistent
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
            print('Error gettiing BU_AssetLibrary_Core')

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

def get_target_lib():
    context = bpy.context
    addon_prefs = get_addon_name().preferences
    debug_mode = addon_prefs.debug_mode
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
                    isPremium = current_library_name in ['BU_AssetLibrary_Premium', 'TEST_BU_AssetLibrary_Premium']
                    library_name = get_lib_name(isPremium, debug_mode)
                    target_lib = bpy.context.preferences.filepaths.asset_libraries[library_name]
                    return target_lib

def is_lib_premium(context):
    addon_prefs = get_addon_name().preferences
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
                    isPremium = current_library_name in ['BU_AssetLibrary_Premium', 'TEST_BU_AssetLibrary_Premium']
                    return isPremium
    
def set_drive_ids(context):
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
                    if current_library_name == 'BU_AssetLibrary_Core':
                        set_core_download_server_ids()
                    elif current_library_name == 'TEST_BU_AssetLibrary_Core':
                        set_core_download_server_ids()
                    elif current_library_name == 'BU_AssetLibrary_Premium':
                        set_premium_download_server_ids()
                    elif current_library_name == 'TEST_BU_AssetLibrary_Premium':
                        set_premium_download_server_ids()

def set_core_download_server_ids():
    addon_prefs = get_addon_name().preferences
    if addon_prefs.debug_mode:
         addon_prefs.download_folder_id ="1COJ6oknO-LDyNx_FP6QPvo80iKrvDXlb"
         addon_prefs.download_folder_id_placeholders="1Jnc45SV7-zK4ULQzmFSA0pK6JKc8z3DN"
    else:
        addon_prefs.download_folder_id = addon_prefs.bl_rna.properties['download_folder_id'].default
        addon_prefs.download_folder_id_placeholders = addon_prefs.bl_rna.properties['download_folder_id_placeholders'].default
    

def set_premium_download_server_ids():
    addon_prefs = get_addon_name().preferences
    if addon_prefs.debug_mode:
        addon_prefs.download_folder_id_placeholders = "146BSw9Gw6YpC9jUA3Ehe7NKa2C8jf3e7"
    else:
        addon_prefs.download_folder_id_placeholders = "1FU-do5DYHVMpDO925v4tOaBPiWWCNP_9"
    

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
        'BU_Placeholder_Premium_Cache',
        'TEST_BU_AssetLibrary_Core',
        'TEST_BU_AssetLibrary_Premium',
    )
# if any of our libs does not exist, create it. Called on event Load post
def add_library_paths():
    test_lib_names = ('TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium','BU_User_Upload')
    real_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium','BU_User_Upload')
    addon_prefs = get_addon_name().preferences
    dir_path = addon_prefs.lib_path
    
    lib_names = get_original_lib_names()
    if addon_prefs.lib_path == '':
        dir_path = find_lib_path(addon_prefs,lib_names)
       

    def create_libraries(dir_path,lib_names):
        for lib_name in lib_names:
            lib_path = os.path.join(dir_path,lib_name)
            if os.path.exists(dir_path):
                if not os.path.isdir(str(lib_path)): # checks whether the directory exists
                    os.mkdir(str(lib_path)) # if it does not yet exist, makes it
                    print('Created directory and library path', os.path.isdir(str(lib_path)))
                if dir_path != "" and lib_name !='BU_User_Upload':
                    if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
                        bpy.ops.preferences.asset_library_add(directory = lib_path, check_existing = True)
                else:
                    print('Did not add library path', lib_name)
    
    def remove_lib_paths(dir_path,lib_names):
        for lib_name in lib_names:
            if lib_name in bpy.context.preferences.filepaths.asset_libraries:
                lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
                bpy.ops.preferences.asset_library_remove(lib_index)

    if addon_prefs.debug_mode == True:
        remove_lib_paths(dir_path,real_lib_names)
        create_libraries(dir_path,test_lib_names)
    else:
        print('dir_path', dir_path)
        remove_lib_paths(dir_path,test_lib_names)
        create_libraries(dir_path,real_lib_names)
    print('dir_path', dir_path)
    # if dir_path:
    #     for lib_name in lib_names:
    #         lib_path = f'{dir_path}{os.sep}{lib_name}'
    #         if not os.path.isdir(str(lib_path)): # checks whether the directory exists
    #             os.mkdir(str(lib_path)) # if it does not yet exist, makes it
    #             print('Created directory and library path', os.path.isdir(str(lib_path)))
    #         if lib_name !='BU_User_Upload':
                
    #             if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
    #                 print('Adding library path', lib_name)
    #                 bpy.ops.preferences.asset_library_add(directory = lib_path, check_existing = True)
    #             else:
    #                 print('Library path already exists ', lib_name)
    #         else:
    #             print('Did not add library path', lib_name)
    #     # else:
    #     #     No_lib_path_warning()
    bpy.ops.wm.save_userpref()



#Look if any of our libraries excists and extract the path from it
def find_lib_path(addon_prefs,lib_names):
    for lib_name in lib_names:
        if lib_name.startswith('TEST_'):
            addon_prefs.debug_mode = True
        else:
            addon_prefs.debug_mode = False
        if lib_name in bpy.context.preferences.filepaths.asset_libraries:
            lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
            if lib is not None:
                dir_path,lib_name = os.path.split(lib.path)
                addon_prefs.lib_path = dir_path
                return dir_path
        else:
            dir_path = ''
            return dir_path
        
def set_upload_target(self,context):
    print('called set upload target')
    upload_target = context.scene.upload_target_enum.switch_upload_target
    addon_prefs = get_addon_name().preferences
    if upload_target == 'core_upload':
        addon_prefs.upload_parent_folder_id = addon_prefs.bl_rna.properties['upload_parent_folder_id'].default if addon_prefs.debug_mode == False else "1dcVAyMUiJ5IcV7QBtQ7a99Jl_DdvL8Qo"
        addon_prefs.download_catalog_folder_id = addon_prefs.bl_rna.properties['download_catalog_folder_id'].default if addon_prefs.debug_mode == False else "1Jnc45SV7-zK4ULQzmFSA0pK6JKc8z3DN"
    elif upload_target == 'premium_upload':
        addon_prefs.upload_parent_folder_id = "1rh2ZrFM9TUJfWDMatbaniCKaXpKDvnkx" if addon_prefs.debug_mode == False else "1IWX6B2XJ3CdqO9Tfbk2m5HdvnjVmE_3-"
        addon_prefs.download_catalog_folder_id = "1FU-do5DYHVMpDO925v4tOaBPiWWCNP_9" if addon_prefs.debug_mode == False else "146BSw9Gw6YpC9jUA3Ehe7NKa2C8jf3e7"
    print(context.scene.upload_target_enum.switch_upload_target)        

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
classes =(
    UploadTargetProperty, 
)

@persistent
def on_blender_startup(dummy):
    add_library_paths()
    addon_prefs = get_addon_name().preferences
    if addon_prefs.gumroad_premium_licensekey!='' and addon_prefs.premium_licensekey != '':
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
    
