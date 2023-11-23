import os
import io
import shutil
import bpy
import functools
import tempfile
from functools import partial
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError


from ..utils import addon_info
from . import network
from . import task_manager
from ..utils import progress
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
        self.total_assets_to_sync = 0
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
        self.assets_to_update = None
        self.prog = 0
        self.prog_text = None
        self.catalog_file_info={}
        self.lib_ref = bpy.context.area.spaces.active.params.asset_library_ref
        self.premium_libs = ("BU_AssetLibrary_Premium", "TEST_BU_AssetLibrary_Premium")
        self.core_libs = ("BU_AssetLibrary_Core", "TEST_BU_AssetLibrary_Core")
        self.isPremium = True if self.lib_ref in self.premium_libs else False
        self.isPlaceholder = False

    def reset(self):
        self.task_manager = task_manager.task_manager_instance
        self.total_assets_to_sync = 0
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
        self.assets_to_update = None
        self.prog = 0
        self.prog_text = None
        self.catalog_file_info={}
        self.lib_ref = bpy.context.area.spaces.active.params.asset_library_ref
        self.premium_libs = ("BU_AssetLibrary_Premium", "TEST_BU_AssetLibrary_Premium")
        self.core_libs = ("BU_AssetLibrary_Core", "TEST_BU_AssetLibrary_Core")
        self.isPremium = True if self.lib_ref in self.premium_libs else False
        self.isPlaceholder = False

    def sync_original_assets(self,context):

        if self.current_state == 'fetch_original_asset_ids'and not self.requested_cancel: 
            self.selected_assets = context.selected_asset_files
            self.target_lib = addon_info.get_target_lib().path 
            try:    
                if self.future is None:
                    isPremium = True if addon_info.is_lib_premium() else False
                    if isPremium:
                        self.future = self.task_manager.executor.submit(fetch_original_premium_asset_ids, self.selected_assets)
                    else:
                        self.future = self.task_manager.executor.submit(fetch_original_asset_ids, self.selected_assets)
                    self.task_manager.futures.append(self.future)

                elif self.future.done():
                    
                    self.assets = self.future.result()
                    if self.assets == None:
                        self.current_state = 'tasks_finished'
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
                    # for asset in self.assets:
                    #     asset_id = asset['id']
                    #     zipped_asset_name = asset['name']
                    #     file_size = asset['size']
                    #     self.prog_text = f'Synced {zipped_asset_name.removesuffix(".zip")}'
                    #     asset_name =zipped_asset_name.removesuffix(".zip")
                    for asset_id,(asset_name, file_size) in self.assets_to_download.items():
                        if not self.requested_cancel:
                            # self.isPlaceholder = False
                            future = download_assets(self,context,asset_id,asset_name,file_size,total_file_size,downloaded_sizes)
                            # future = self.task_manager.executor.submit(DownloadFile, self, context, asset_id, zipped_asset_name, file_size,self.isPlaceholder,self.isPremium, self.target_lib, context.workspace,total_file_size,downloaded_sizes)
                            future_to_asset[future] = asset_name
                    self.future = None      
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_download'
                     
                   

            except Exception as error_message:
                print('an error occurred: ', error_message) 
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
                    print('self.isPremium: ',self.isPremium)
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
                    print('append_to_current_scene')
                    self.task_manager.update_task_status("appending to scene...")
                    for asset in self.selected_assets:
                        future = self.task_manager.executor.submit(append_to_scene,self, context, asset, self.target_lib,self.downloaded_assets)
                        future_to_asset[future] = asset
                        self.task_manager.futures.append(future)
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_append'
                    
                    
            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'waiting_for_append':
            try:
                all_futures_done = all(future.done() for future in self.future_to_asset.keys())
                appended_assets = []
                if all_futures_done:
                    print("all futures done")
                    for future, asset_name in self.future_to_asset.items():
                        appended_assets.append(future.result())
                        future = None
                    self.future_to_asset = None  # Reset the futures
                    self.current_state = 'tasks_finished'
                    
            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 
        

        elif self.requested_cancel:
            self.current_state = 'tasks_finished'

        elif self.current_state == 'tasks_finished':
            if self.isPremium:
                bpy.ops.succes.custom_dialog('INVOKE_DEFAULT', title = 'Sync Complete!', succes_message=str(''),amount_new_assets=len(self.downloaded_assets),is_original=True)
            print('Tasks finished')
            self.future = None
            progress.end(context)
            self.reset()
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)
            
            self.current_state = None

        elif self.current_state =='error':
            self.future = None
            progress.end(context)
            self.reset()
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)
            self.current_state = None

    def start_tasks(self,context):

        if self.current_state == 'fetch_assets'and not self.requested_cancel:
            self.task_manager.set_total_tasks(3)
            self.target_lib = addon_info.get_target_lib().path
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Fetching asset list...")
                    self.future = self.task_manager.executor.submit(fetch_asset_list)
                    self.task_manager.futures.append(self.future)
                elif self.future.done():
                    self.assets = self.future.result()
                    self.task_manager.increment_completed_tasks()
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
                    self.task_manager.increment_completed_tasks()
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
                    print("total file size: ", total_file_size)
                    print("downloaded sizes: ", downloaded_sizes)  
                    progress.init(context,total_file_size,'Syncing assets...')
                    for asset_id,(asset_name, file_size) in self.assets_to_download.items():
                        if not self.requested_cancel:
                            future = download_assets(self,context,asset_id,asset_name,file_size,total_file_size,downloaded_sizes)
                            # future = self.task_manager.executor.submit(DownloadFile, self, context, asset_id, asset_name,file_size,self.isPlaceholder,self.isPremium, self.target_lib, context.workspace,total_file_size,downloaded_sizes)
                            future_to_asset[future] = asset_name
                            
                    self.future_to_asset = future_to_asset
                    print(self.future_to_asset)
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
                    bpy.ops.asset.library_refresh()
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
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)
            bpy.ops.succes.custom_dialog('INVOKE_DEFAULT', title = 'Sync Complete!', succes_message=str('Please reopen blender to compleet the sync'),amount_new_assets=len(self.downloaded_assets),is_original=False)
            self.requested_cancel = False
            self.current_state = None

        elif self.current_state =='error':
            self.future = None
            progress.end(context)
            
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)
            self.requested_cancel = False
            self.current_state = None

    def sync_catalog_file(self,context):

        if self.current_state == 'fetch_catalog_file_id'and not self.requested_cancel:
            self.target_lib = addon_info.get_target_lib().path
            self.task_manager.set_total_tasks(2)
            try:
                if self.future is None:
                    self.task_manager.update_task_status("Fetching catalog file id...")
                    self.future = self.task_manager.executor.submit(fetch_catalog_file_id)
                    self.task_manager.futures.append(self.future)
                
                elif self.future.done():  
                        self.catalog_file_info = self.future.result()
                        self.task_manager.increment_completed_tasks()
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
                    isPremium = context.scene.catalog_target_enum.switch_catalog_target
                    self.future = self.task_manager.executor.submit(download_cat_file,self, context, FileId, fileName, current_file_dir,context.workspace)
                elif self.future.done():
                    catalog_file = self.future.result()
                    self.task_manager.increment_completed_tasks()
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
            self.reset()
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)
        
        elif self.current_state =='error':
            self.future = None
            self.reset()
            progress.end(context)
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
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
        self.task_manager.increment_completed_tasks()
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
        # print("Fetching original asset ids...")
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
    except TaskSpecificException as e:
        raise CriticalException(f"A critical error occurred at (Fetching asset list): {str(e)}")  



   
def compare_with_local_assets(self,context,assets,target_lib,isPremium):
   
    print("comparing asset list...")
    context.scene.assets_to_update.clear()
    assets_to_download ={} 
    ph_assets,og_assets = assets
    for asset in ph_assets:
        asset_id = asset['id']
        asset_name = asset['name']
        file_size = asset['size']
        g_m_time = asset['modifiedTime']

        ph_file_name = asset_name.removesuffix('.zip')
        base_name = ph_file_name.removeprefix('PH_')
        og_name = asset_name.removeprefix('PH_')
        if asset_name == 'blender_assets.cats.zip':
            ph_asset_path = f'{target_lib}{os.sep}{base_name}.txt'
        else:
            ph_asset_path = f'{target_lib}{os.sep}{base_name}{os.sep}{ph_file_name}.blend'
        og_asset_path = f'{target_lib}{os.sep}{base_name}{os.sep}{base_name}.blend'
        

        if not os.path.exists(ph_asset_path) and not os.path.exists(og_asset_path):
            # print(f'asset_path does not exist = {asset_path}')
            assets_to_download[asset_id] =  (asset_name, file_size)
            print(f" {asset_name} new item")
        
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
        og_asset_path = f'{target_lib}{os.sep}{base_name}{os.sep}{base_name}.blend'
        if os.path.exists(og_asset_path):
            og_m_time = os.path.getmtime(og_asset_path)
            l_m_datetime,g_m_datetime = addon_info.convert_to_UTC_datetime(og_m_time,g_m_time)
            if l_m_datetime < g_m_datetime:
                print(f'{asset_name} has update ', l_m_datetime, ' < ',g_m_datetime)
                asset_has_update = context.scene.assets_to_update.add()
                asset_has_update.name = asset_name
                asset_has_update.id = asset_id
                asset_has_update.size = int(file_size)
                asset_has_update.is_placeholder = False
            
      
       
    if len(context.scene.assets_to_update) > 0:
        self.task_manager.update_subtask_status(f'Some assets have updates: {len(context.scene.assets_to_update)}')
        print(f'Some assets have updates: {len(context.scene.assets_to_update)}')
    else:
        self.task_manager.update_subtask_status('All assets are already synced')
        print(('All assets are already synced'))
    return assets_to_download


        
def append_to_scene(self, context, asset, target_lib, downloaded_assets):
    try:
        print("Appending to scene...")
        original_name = asset.name
        blend_file_path = f"{target_lib}{os.sep}{asset.name}{os.sep}{asset.name}.blend"
        if f'{asset.name}.zip' not in downloaded_assets or not os.path.exists(blend_file_path):
            raise Exception('Asset not downloaded or blend file does not exist')
        ph_file = f'{target_lib}{os.sep}{asset.name}{os.sep}PH_{asset.name}.blend'
        asset_types =addon_info.type_mapping()
        result = addon_info.find_asset_by_name(asset.name)

        if asset.id_type not in asset_types:
            raise Exception(f"Invalid asset ID type: {asset.id_type}")

        if result:
            to_replace,datablock = result
            to_replace.name = f'{to_replace.name}_ph'
        
        data_type = asset_types[asset.id_type]
        with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
            print('data_type',data_type)
            print('data_from',dir(data_from))

            if data_type not in dir(data_from):
                raise Exception(f"Data type {data_type} not found in data_to")
            setattr(data_to, data_type, getattr(data_from, data_type))
        
        if to_replace:
            to_replace.user_remap(datablock[asset.name])
            datablock.remove(to_replace)
        os.remove(blend_file_path)
        return f'{original_name}.blend' 
   
    except Exception as e:
        addon_logger.error(f"(Appending to scene) ERROR : {str(e)}")
        if os.path.exists(blend_file_path):
            os.remove(blend_file_path)
        asset.name = original_name
        print(f"An error occurred in append_to_scene: {str(e)}")
        raise TaskSpecificException(f"(Appending to scene) ERROR : {str(e)}")

    

def download_assets(self,context,asset_id,asset_name,file_size,total_file_size,downloaded_sizes):
    try:
        isPlaceholder = True if asset_name.startswith('PH_') else False
        isPremium = True if addon_info.is_lib_premium() else False
            
        # return submit_task(self,'testfunction...',self.tempfunction)
        return submit_task(self,'Downloading premium assets...', DownloadFile, self, context, asset_id, asset_name,file_size,isPlaceholder,isPremium, self.target_lib, context.workspace,total_file_size,downloaded_sizes)
    except Exception as error_message:
        addon_logger.error(error_message)
        print('Error: ', error_message)    

def DownloadFile(self, context, FileId, fileName, file_size,isPlaceholder,isPremium,target_lib,workspace,total_file_size,downloaded_sizes ):
    try:
        authService = network.google_service()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        chunksize =256 * 1024
        downloader = MediaIoBaseDownload(file, request,chunksize=chunksize)
        
        done = False
        while done is False:
            
            status, done = downloader.next_chunk()
            
            if status:
                print('status', status)
                current_progress = int(status.progress()*100)
                downloaded_size_for_file = current_progress * int(file_size)/100
                downloaded_sizes[FileId] = downloaded_size_for_file
                total_downloaded = sum(downloaded_sizes.values())
                progress.update(context, total_downloaded, "Syncing asset...", workspace)
                task_manager.task_manager_instance.update_task_status(f"{fileName.removesuffix('.zip')} size: {round(downloader._total_size/1024)}kb" if round(downloader._total_size/1024)<1000 else f"{fileName.removesuffix('.zip')} size: {round(downloader._total_size/1024/1024,2)}mb ")
                print('downloader.total_size: ',downloader._total_size)
                print('current_progress: ',current_progress)
                print('downloaded_size_for_file: ',downloaded_size_for_file)
                print('total_file_size: ',total_file_size)
                print('total_downloaded: ',total_downloaded)
                print("Download %d%%." % int(status.progress() * 100))

                # print('downloader._total_size: ',int(file_size))
        print ("Download Complete!")

        
        
        # task_manager.task_manager_instance.update_task_status(overall_progress)
        file.seek(0)
        
        with open(os.path.join(target_lib, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            print('fileName: ',fileName)
            print('target_lib: ',target_lib)
            if ".zip" in fileName:
                fname = target_lib + os.sep + fileName
                shutil.unpack_archive(fname, target_lib, 'zip')
                if not isPlaceholder:
                    
                    baseName = fileName.removesuffix('.zip')
                    print('baseName: ',baseName)
                    ph_file = f'{target_lib}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
                    if os.path.exists(ph_file):
                        if not isPremium:
                            # os.rename(ph_file, ph_file.removesuffix('.blend'))
                                os.remove(ph_file)

                os.remove(fname)
                
                return fileName         
    except HttpError as error:
        print(F'An error occurred: {error}')


def download_cat_file(self, context, FileId, fileName, target_lib,workspace ):
    try:
        authService = network.google_service()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        
        done = False

        while done is False:
            status, done = downloader.next_chunk()
            # print('status', status)
            # print({"INFO"}, f"{fileName} has been Synced")
        file.seek(0)
        
        with open(os.path.join(target_lib, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            if ".zip" in fileName:
                fname = target_lib + os.sep + fileName
                shutil.unpack_archive(fname, target_lib, 'zip')
                os.remove(fname)
                self.prog += 1
                print('updating progress ', self.prog)
                self.prog_text = f'{fileName} has been Synced to current file'
                return fileName         
    except HttpError as error:
        print(F'An error occurred: {error}')
    


