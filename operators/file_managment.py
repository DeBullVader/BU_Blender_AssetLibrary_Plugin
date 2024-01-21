import os
import io
import shutil
import bpy
import json
from functools import partial
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError


from ..utils import addon_info
from . import network
from . import task_manager
from ..utils import progress,version_handler
from ..utils.addon_logger import addon_logger


class TaskSpecificException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)

class CriticalException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)


class AssetSync:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.task_manager = task_manager.task_manager_instance
        self.selected_assets = []
        self.is_done_flag = False
        self.requested_cancel = False
        self.current_state = None
        self.future = None
        self.assets =None
        self.ph_assets = []
        self.og_assets = []
        self.downloaded_assets = []
        self.download_progress_dict = {}
        self.assets_to_download = None
        self.assets_to_update = []
        self.prog = 0
        self.prog_text = None
        self.catalog_file_info={}
        self.target_lib = None
        self.premium_libs = ("BU_AssetLibrary_Premium", "TEST_BU_AssetLibrary_Premium")
        self.core_libs = ("BU_AssetLibrary_Core", "TEST_BU_AssetLibrary_Core")
        self.isPremium = False

    def reset(self):
        self.task_manager = task_manager.task_manager_instance
        self.selected_assets = []
        self.is_done_flag = False
        self.requested_cancel = False
        self.current_state = None
        self.future = None
        self.assets =None
        self.ph_assets = []
        self.og_assets = []
        self.downloaded_assets = []
        self.assets_to_download = None
        self.download_progress_dict = {}
        self.assets_to_update = []
        self.prog = 0
        self.prog_text = None
        self.catalog_file_info={}
        self.target_lib = None
        self.premium_libs = ("BU_AssetLibrary_Premium", "TEST_BU_AssetLibrary_Premium")
        self.core_libs = ("BU_AssetLibrary_Core", "TEST_BU_AssetLibrary_Core")
        self.isPremium = False

    def sync_original_assets(self,context):

        if self.current_state == 'fetch_original_asset_ids'and not self.requested_cancel: 
            
            # target_lib_path = self.target_lib.path
            # path,lib = os.path.split(target_lib_path)
            
            try:    
                if self.future is None:
                    if self.isPremium:
                        self.future = self.task_manager.executor.submit(fetch_original_premium_asset_ids, self.selected_assets)
                    else:
                        self.future = self.task_manager.executor.submit(fetch_original_asset_ids, self.selected_assets)
                    self.task_manager.futures.append(self.future)

                elif self.future.done():
                    
                    self.assets = self.future.result()
                    if self.assets == None:
                        self.current_state = 'tasks_finished'
                        addon_logger.error('self.assets is None after fetching original asset ids')
                        raise Exception ('self.assets is None')
                        
                    self.assets_to_download = {asset['id']: (asset['name'], asset['size']) for asset in self.assets}
                    self.current_state = 'sync_original_assets'
                    self.future = None  # Reset the future so the next state can start its own task
                    self.task_manager.futures= []
            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error'

        elif self.current_state == 'sync_original_assets' and not self.requested_cancel:
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Initiating download...")
                    self.prog = 0
                    future_to_asset = {}
                    total_file_size = sum(int(file_size) for _, (_, file_size) in self.assets_to_download.items())
                    downloaded_sizes = {asset_id: 0 for asset_id in self.assets_to_download}   
                    progress.init(context,total_file_size,'Syncing assets...')

                    for asset_id,(asset_name, file_size) in self.assets_to_download.items():
                        if not self.requested_cancel:
                           
                            self.download_progress_dict[asset_name] = 0,'size:..'
                            future = download_assets(self,context,asset_id,asset_name,file_size,downloaded_sizes)
                            future_to_asset[future] = asset_name

                    self.future = None      
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_download'
                     
                   

            except Exception as error_message:
                print('an error occurred in download: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error'

        elif self.current_state == 'waiting_for_download':
            try:
                all_futures_done = all(future.done() for future in self.future_to_asset.keys())
                if all_futures_done:
                    print("all futures done")
                    for future, asset_name in self.future_to_asset.items():
                        self.downloaded_assets.append(future.result())
                        future = None
                    
                    progress.end(context)
        
                    self.future = None
                    self.future_to_asset = None  # Reset the futures
                    if self.isPremium:
                        self.current_state = 'append_to_current_scene'
                    else:
                        self.current_state = 'tasks_finished'
            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error'
                
        elif self.current_state == 'append_to_current_scene':
           
            try:
                if self.future is None:
                    future_to_asset = {}
                    print("appending to scene")
                    self.task_manager.update_task_status("appending to scene...")
                    for asset in self.selected_assets:
                        future = self.task_manager.executor.submit(append_to_scene,self, context, asset, self.target_lib,self.downloaded_assets)
                        future_to_asset[future] = asset
                        self.task_manager.futures.append(future)
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_append'
                    
                    
            except Exception as error_message:
                print('an error occurred in append: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'waiting_for_append':
            try:
                print('waiting_for_append')
                all_futures_done = all(future.done() for future in self.future_to_asset.keys())
                appended_assets = []
                if all_futures_done:
                    print("all futures done")
                    for future, asset_name in self.future_to_asset.items():
                        print('future Result ',future.result())
                        appended_assets.append(future.result())
                        future = None
                    self.future_to_asset = None  # Reset the futures
                    self.current_state = 'tasks_finished'
                    
            except Exception as error_message:
                print('an error occurred in waiting for append: ', error_message) 
                bpy.ops.error.custom_dialog('INVOKE_DEFAULT',title = 'Sync had error on append to scene!', error_message=str(error_message)) 
                addon_logger.error(error_message)
                self.current_state = 'error' 
        

        elif self.requested_cancel:
            self.current_state = 'tasks_finished'

        elif self.current_state == 'tasks_finished':
            if self.target_lib.name in self.premium_libs:
                bpy.ops.succes.custom_dialog('INVOKE_DEFAULT', title = 'Sync Complete!', succes_message=str(''),amount_new_assets=len(self.downloaded_assets),is_original=True)
            print('Tasks finished')
            self.future = None
            progress.end(context)

            self.set_done(True)
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)
            
            self.current_state = None

        elif self.current_state =='error':
            self.future = None
            progress.end(context)
            self.task_manager.update_task_status("Sync had error")
            self.set_done(True)
            self.task_manager.set_done(True)
            self.current_state = None

    def start_tasks(self,context):

        if self.current_state == 'fetch_assets'and not self.requested_cancel:
            self.task_manager.set_total_tasks(3)
            
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Fetching asset list...")
                    self.future = self.task_manager.executor.submit(fetch_asset_list)
                    self.task_manager.futures.append(self.future)
                elif self.future.done():
                    self.assets = self.future.result()
                    self.current_state = 'compare_assets'
                    self.future = None
            
            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error'             
            
        elif self.current_state == 'compare_assets'and not self.requested_cancel:
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Comparing assets...")
                    self.future = self.task_manager.executor.submit(compare_with_local_assets, self, context, self.assets, self.target_lib,self.isPremium)
                    self.task_manager.futures.append(self.future)
                elif self.future.done():
                    self.assets_to_download = self.future.result()
                    
                    if len(self.assets_to_download) > 0:
                        self.current_state = 'initiate_download'
                        self.future = None 
                    else:
                        self.current_state = 'tasks_finished'
            
            except Exception as error_message:
                print('Error Comparing assets: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'initiate_download'and not self.requested_cancel:
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Initiating download...")
                    self.prog = 0
                    future_to_asset = {}
                    total_file_size = sum(int(file_size) for _, (_, file_size) in self.assets_to_download.items())
                    downloaded_sizes = {asset_id: 0 for asset_id in self.assets_to_download}

                    progress.init(context,total_file_size,'Syncing assets...')
                    for asset_id,(asset_name, file_size) in self.assets_to_download.items():
                        if not self.requested_cancel:
                            self.download_progress_dict[asset_name] = 0,'size:..'
                            future = download_assets(self,context,asset_id,asset_name,file_size,downloaded_sizes)
                            future_to_asset[future] = asset_name
                            
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_downloads'
                    
            
            except Exception as error_message:
                print('Error downloading assets: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'waiting_for_downloads':
            try:
                
                all_futures_done = all(future.done() for future in self.future_to_asset.keys())
                if all_futures_done:
                    print("all futures done")
                    for future, asset_name in self.future_to_asset.items():
                        result = future.result()
                        future = None
                        self.downloaded_assets.append(asset_name)
                    progress.end(context)
                    self.future_to_asset = None
                    self.current_state = 'tasks_finished'
            except Exception as error_message:
                print('Error processing downloaded assets: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 
        
        elif self.requested_cancel:
            self.current_state = 'tasks_finished'
                
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            
            self.future = None
            progress.end(context)
            
            self.set_done(True)
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)
            if 'blender_assets.cats.zip' in self.downloaded_assets:
                succes_message = 'Catalog file updated'
                self.downloaded_assets.remove('blender_assets.cats.zip')
            succes_message = ''
            bpy.ops.succes.custom_dialog('INVOKE_DEFAULT', title = 'Sync Complete!', succes_message=succes_message,amount_new_assets=len(self.downloaded_assets),is_original=False)
            self.requested_cancel = False
            self.current_state = None

        elif self.current_state =='error':
            self.future = None
            progress.end(context)
            
            self.set_done(True)
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)
            self.requested_cancel = False
            self.current_state = None

    def sync_catalog_file(self,context):

        if self.current_state == 'fetch_catalog_file_id'and not self.requested_cancel:
            self.target_lib = addon_info.get_target_lib(context).path
            window,area = addon_info.get_asset_browser_window_area(context)
            if window and area:
                with context.temp_override(window=window, area=area):
                    current_library_name = version_handler.get_asset_library_reference(context)
                    if current_library_name != 'LOCAL':
                        version_handler.set_asset_library_reference(context,'LOCAL')
                        
            self.task_manager.set_total_tasks(2)
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Fetching catalog file id...")
                    self.future = self.task_manager.executor.submit(fetch_catalog_file_id)
                    self.task_manager.futures.append(self.future)
                
                elif self.future.done():  
                        self.catalog_file_info = self.future.result()
                        self.current_state = 'initiate_download'
                        self.future = None  

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error'   
       
        elif self.current_state == 'initiate_download'and not self.requested_cancel:
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Downloading catalog file...")
                    FileId = self.catalog_file_info.get('id')
                    fileName = self.catalog_file_info.get('name')
                    current_file_path = addon_info.get_current_file_location()
                    current_file_dir,blend_file = os.path.split(current_file_path)
                    self.future = self.task_manager.executor.submit(download_cat_file,self, context, FileId, fileName, current_file_dir,context.workspace)
                elif self.future.done():
                    catalog_file = self.future.result()
                    self.current_state = 'tasks_finished'
                    self.future = None  
                    
            except Exception as error_message:
                print('error: ',error_message)
                addon_logger.error(error_message)
                self.current_state = 'error'

        elif self.requested_cancel:
            self.current_state = 'tasks_finished'
                
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            self.future = None
            progress.end(context)
            
            self.set_done(True)
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)
        
        elif self.current_state =='error':
            self.future = None
            progress.end(context)
            self.set_done(True)
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)

    


    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done


def submit_task(self,text,function, *args, **kwargs):
    
    self.task_manager.update_task_status(text)
    task_with_args = partial(function, *args, **kwargs)
    self.future = self.task_manager.executor.submit(task_with_args)
    self.task_manager.futures.append(self.future)
    return self.future
    

def future_result(self):
    try:
        print('future done')
        return self.future.result()
    except Exception as error_message:
        print('Error: ', error_message)
        addon_logger.error(error_message)
        self.set_done(True)       

def fetch_asset_list():
    try:
        print("Fetching asset list...")
        addon_prefs = addon_info.get_addon_name().preferences
        ph_assets = network.get_asset_list(addon_prefs.download_folder_id_placeholders)
        og_assets = network.get_asset_list(addon_prefs.download_folder_id)
        return (ph_assets, og_assets)
    except Exception as e:
        print(f"A critical error occurred at (Fetching asset list): {str(e)}")

def fetch_original_asset_ids(selected_assets):
    try:
        print("Fetching original asset ids...")
        asset_list = network.get_assets_ids_by_name(selected_assets)
        return asset_list
    except TaskSpecificException as e:
        raise CriticalException(f"A critical error occurred at (Fetching original asset ids): {str(e)}")

    
def fetch_original_premium_asset_ids(selected_assets):
    try:
        print("Fetching original Premium asset ids...")
        return network.get_premium_assets_ids_by_name(selected_assets)
    except TaskSpecificException as e:
        raise CriticalException(f"A critical error occurred at (Fetching original Premium asset ids): {str(e)}")
    
def fetch_catalog_file_id():
    try:
        print("Fetching catalog id from server...")
        catalog_file_info = network.get_catfile_id_from_server()
        return catalog_file_info
    except Exception as error_message:
        print('an error occurred: ', error_message) 
        addon_logger.error(f'Critical Error fetch catalog id: {error_message}') 
       

def remove_deprecated_placeholders(target_lib,ph_assets):
    server_ph_asset_names = { asset['name'] for asset in ph_assets}
    for asset_dir, dirs, files in os.walk(target_lib.path):
        for file in files:
            if file.startswith('PH_') and file.endswith('.blend'):  
                asset_name = file.replace('.blend', '.zip')
                if asset_name not in server_ph_asset_names:
                    ph_asset_path = os.path.join(asset_dir, file)
                    if os.path.exists(ph_asset_path):
                        print(f'Removed preview file ({file}) as it was deprecated or outdated')	
                        shutil.rmtree(asset_dir)
                    

def handle_deprecated_og_files(target_lib,og_assets):
    try:
        deprecated_og_files=[]
        assets_to_remove =[]
        addon_prefs = addon_info.get_addon_prefs()
        server_og_asset_names = { asset['name'] for asset in og_assets}
        for asset_dir, dirs, files in os.walk(target_lib.path):
            for file in files:
                if not file.startswith('PH_') and file.endswith('.blend'):  
                    asset_name = file.replace('.blend', '.zip')
                    if asset_name not in server_og_asset_names:
                        asset_path = os.path.join(asset_dir, file)
                        if os.path.exists(asset_path):
                            deprecated_og_files.append(asset_path)
        if addon_prefs.remove_deprecated_assets:   
            print('deleting deprecated files')                     
            if deprecated_og_files:
                for asset_path in deprecated_og_files:
                    print('asset_path: ',asset_path)
                    asset_dir,filename = os.path.split(asset_path)
                    with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
                        if hasattr(data_from, 'texts'):
                           data_to.texts = data_from.texts
                    if "BU_OG_Asset_Info" in bpy.data.texts:
                        json_text = bpy.data.texts["BU_OG_Asset_Info"].as_string()
                        asset_info = json.loads(json_text)
                        asset_name = filename.replace('.blend', '')
                        asset_info_name = asset_info['BU_Asset']
                        if asset_name == asset_info_name:
                            print(f'Removed {asset_name} as it was outdated or deprecated')
                            # Remove the item and delete its directory
                            bpy.data.texts.remove(bpy.data.texts["BU_OG_Asset_Info"])
                            shutil.rmtree(asset_dir)
             
        else:
            if deprecated_og_files:
                deprecated_lib_name ='BU_AssetLibrary_Deprecated'
                deprecated_lib = os.path.join(addon_prefs.lib_path,deprecated_lib_name)
                if not os.path.exists(deprecated_lib):
                    os.mkdir(deprecated_lib)
                lib = bpy.context.preferences.filepaths.asset_libraries.get(deprecated_lib_name)
                if not lib:
                    bpy.ops.preferences.asset_library_add(directory = deprecated_lib, check_existing = True)
                    lib = bpy.context.preferences.filepaths.asset_libraries.get(deprecated_lib_name)
                for asset_path in deprecated_og_files:
                    asset_dir,filename = os.path.split(asset_path)
                    core_lib,folder = os.path.split(asset_dir)
                    cat_file_path = os.path.join(core_lib,'blender_assets.cats.txt')
                    if os.path.exists(cat_file_path):
                        shutil.copy2(cat_file_path, lib.path)
                    
                    dst=os.path.join(lib.path,folder)
                    print('asset_dir moved', dst)
                    shutil.copytree(asset_dir ,dst ,dirs_exist_ok=True)  
                    shutil.rmtree(asset_dir)
                    
                    print(f'Moved {filename} to ---> {deprecated_lib_name}')
        
    except Exception as e:
        print(f"A critical error occurred at (handle_deprecated_og_files): {str(e)}")
        raise Exception(f'Error in handle_deprecated_og_files: {e}')
   
def compare_with_local_assets(self,context,assets,target_lib,isPremium):
    print("comparing asset list...")
    try:
        addon_prefs = addon_info.get_addon_prefs()
        assets_to_download ={}
       
        ph_assets,og_assets = assets
        remove_deprecated_placeholders(target_lib,ph_assets)
        handle_deprecated_og_files(target_lib,og_assets)
        for asset in ph_assets:
            asset_id = asset['id']
            asset_name = asset['name']
            file_size = asset['size']
            g_m_time = asset['modifiedTime']

            ph_file_name = asset_name.removesuffix('.zip')
            base_name = ph_file_name.removeprefix('PH_')
            
            if asset_name == 'blender_assets.cats.zip':
                ph_asset_path = f'{target_lib.path}{os.sep}{base_name}.txt'
            else:
                ph_asset_path = f'{target_lib.path}{os.sep}{base_name}{os.sep}{ph_file_name}.blend'
            og_asset_path = f'{target_lib.path}{os.sep}{base_name}{os.sep}{base_name}.blend'
            
            if not os.path.exists(ph_asset_path) and not os.path.exists(og_asset_path):
                print('New asset: ',asset_name,' File Size: ',file_size)
                assets_to_download[asset_id] =  (asset_name, file_size)
                
            if os.path.exists(ph_asset_path) and not os.path.exists(og_asset_path):
                ph_m_time = os.path.getmtime(ph_asset_path)
                l_m_datetime,g_m_datetime = addon_info.convert_to_UTC_datetime(ph_m_time,g_m_time)
                if  l_m_datetime<g_m_datetime:
                    print(f'{asset_name} has update ', l_m_datetime, ' < ',g_m_datetime)
                    assets_to_download[asset_id] = (asset_name, file_size)

        for asset in og_assets:
            asset_id = asset['id']
            asset_name = asset['name']
            file_size = asset['size']
            g_m_time = asset['modifiedTime']
            base_name = asset_name.removesuffix('.zip')
            og_asset_path = f'{target_lib.path}{os.sep}{base_name}{os.sep}{base_name}.blend'
            if os.path.exists(og_asset_path):
                og_m_time = os.path.getmtime(og_asset_path)
                l_m_datetime,g_m_datetime = addon_info.convert_to_UTC_datetime(og_m_time,g_m_time)
                if l_m_datetime < g_m_datetime:
                    print(f'{asset_name} has update ', l_m_datetime, ' < ',g_m_datetime)
                    if addon_prefs.automaticly_update_original_assets:
                        assets_to_download[asset_id] = (asset_name, file_size)
                    else:
                        if asset not in self.assets_to_update:
                            self.assets_to_update.append(asset)
        return assets_to_download
    except Exception as e:
        raise Exception(f"Error trying to compare og assets: {str(e)}")
    


        
def append_to_scene(self, context, asset, target_lib, downloaded_assets):
    try:
        target_lib_path = target_lib.path
        print("Appending to scene...")
        original_name = asset.name
        blend_file_path = f"{target_lib_path}{os.sep}{asset.name}{os.sep}{asset.name}.blend"
        if f'{asset.name}.zip' not in downloaded_assets or not os.path.exists(blend_file_path):
            raise Exception('Asset not downloaded or blend file does not exist')
        ph_file = f'{target_lib_path}{os.sep}{asset.name}{os.sep}PH_{asset.name}.blend'
        asset_types =addon_info.type_mapping()

        result = addon_info.find_asset_by_name(asset.name)
        if asset.id_type not in asset_types:
            raise Exception(f"Invalid asset ID type: {asset.id_type}")

        to_replace,datablock = result
        if to_replace is not None and datablock is not None:
            print('to replace name ',to_replace.name)
            to_replace.name = f'{to_replace.name}_ph'
        else:
            print('No replace')

        
        data_type = asset_types[asset.id_type]
        with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):

            if data_type not in dir(data_from):
                raise Exception(f"Data type {data_type} not found in data_to")
            setattr(data_to, data_type, getattr(data_from, data_type))
        
        if to_replace:
            
            to_replace.user_remap(datablock[asset.name])
            datablock.remove(to_replace)
        else:
            print('No replace')
        os.remove(blend_file_path)
        print(f"Asset {asset.name} appended to scene")
        return f'{original_name}.blend' 
   
    except Exception as e:
        print('error happend in append')
        addon_logger.error(f"(Appending to scene) ERROR : {str(e)}")
        if os.path.exists(blend_file_path):
            os.remove(blend_file_path)
        if asset.name.endswith('_ph'):
            asset.name = original_name
        print(f"An error occurred in append_to_scene: {str(e)}")
        raise TaskSpecificException(f"(Appending to scene) ERROR : {str(e)}")

    

def download_assets(self,context,asset_id,asset_name,file_size,downloaded_sizes):
    try:
        isPlaceholder = True if asset_name.startswith('PH_') else False
        
        # return submit_task(self,'testfunction...',self.tempfunction)
        return submit_task(self,'Downloading assets...', DownloadFile, self, context, asset_id, asset_name,file_size,isPlaceholder, self.target_lib, context.workspace,downloaded_sizes)
    except Exception as error_message:
        addon_logger.error(error_message)
        print('Error: ', error_message)    

def DownloadFile(self, context, FileId, fileName, file_size,isPlaceholder,target_lib,workspace,downloaded_sizes ):

    try:
        target_lib_path = target_lib.path
        
        NUM_RETRIES = 3
        authService = network.google_service()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        chunk_size = addon_info.calculate_dynamic_chunk_size(int(file_size))
        
        downloader = MediaIoBaseDownload(file, request,chunksize=chunk_size)
        
        done = False
        while done is False:
            try:
                status, done = downloader.next_chunk(num_retries=NUM_RETRIES)
                
                if status:
                    current_progress = int(status.progress()*100)
                    downloaded_size_for_file = current_progress * int(file_size)/100
                    downloaded_sizes[FileId] = downloaded_size_for_file
                    total_downloaded = sum(downloaded_sizes.values())
                    size = f"size: {round(downloader._total_size/1024)}kb" if round(downloader._total_size/1024)<1000 else f"{fileName.removesuffix('.zip')} size: {round(downloader._total_size/1024/1024,2)}mb "
                    # size ="size:..."
                    self.download_progress_dict[fileName] =(current_progress,size)
                    progress.update(context, total_downloaded, "Syncing asset...", workspace)
            except HttpError as error:
                    raise Exception(f'HttpError in download_chunks: {error}')

        try:
            file.seek(0)
            with open(os.path.join(target_lib_path, fileName), 'wb') as f:
                f.write(file.read())
                f.close()

                if ".zip" in fileName:
                    fname = target_lib_path + os.sep + fileName
                    shutil.unpack_archive(fname, target_lib_path, 'zip')
                    if not isPlaceholder:
                        baseName = fileName.removesuffix('.zip')
                        ph_file = f'{target_lib_path}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
                        if os.path.exists(ph_file):
                            if not self.isPremium:
                                os.remove(ph_file)

                    os.remove(fname)
                    return fileName 
        except Exception as error:
            raise Exception(f'Error writing and unpacking: {error}')        
    except Exception as error:
        raise Exception(f'DownloadFile Error: {error}')


def download_cat_file(self, context, FileId, fileName, target_lib,workspace ):
    try:
        NUM_RETRIES = 3
        authService = network.google_service()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request,)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk(num_retries=NUM_RETRIES)
        file.seek(0)
        
        with open(os.path.join(target_lib, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            if ".zip" in fileName:
                fname = target_lib + os.sep + fileName
                shutil.unpack_archive(fname, target_lib, 'zip')
                os.remove(fname)
                self.prog += 1
                
                self.prog_text = f'{fileName} has been Synced to current file'
                return fileName         
    except HttpError as error:
        raise Exception(F'download_cat_file Error: {error}')
    


