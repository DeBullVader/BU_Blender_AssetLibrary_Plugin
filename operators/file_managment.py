import os
import io
import shutil
import bpy
import functools
import tempfile
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError


from ..utils import addon_info
from . import network
from . import task_manager
from ..utils import progress

class TaskSpecificException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)

class CriticalException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)
#important to not use any blender API (bpy) functions during threading.
#if needed set it below in the init so the instance has the information it needs

def show_error_popup(context,e):
    print(e)
    layout = context.layout
    layout.label(text="An error occurred:", icon='ERROR')
    # layout.label(text=e)

def construct_error(error_message):
    bpy.context.window_manager.popup_menu(functools.partial(show_error_popup, e='error_message'), title="Error", icon='ERROR')

class AssetSync:
    def __init__(self, target_lib=None):
        self.task_manager = task_manager.task_manager_instance
        self.total_assets_to_sync = 0
        self.target_lib = target_lib or addon_info.get_target_lib().path
        self.is_done_flag = False
        self.requested_cancel = False
        self.current_state = 'fetch_assets'
        self.future = None
        self.assets = []
        self.downloaded_assets = []
        self.assets_to_download = None
        self.prog = 0
        self.isPremium = addon_info.is_lib_premium(bpy.context)
        self.prog_text = None
        self.catalog_file_info={}


    def sync_original_assets(self,context,isPremium):
        
        selected_assets = context.selected_asset_files
        if self.current_state == 'fetch_original_asset_ids'and not self.requested_cancel:
            # Start the fetch_assets task if it's not started
            
            if self.future is None:
                if isPremium:
                    self.future = self.task_manager.executor.submit(fetch_original_premium_asset_ids, selected_assets)
                else:
                    self.future = self.task_manager.executor.submit(fetch_original_asset_ids, selected_assets)
                self.task_manager.futures.append(self.future)

            elif self.future.done():
                
                print('self future done')
                # print('Future result: ', self.future.result())
                try:
                    self.assets = self.future.result()
                    if self.assets == None:
                        self.current_state = 'tasks_finished'
                        raise Exception ('self.assets is None')
                        
                    print('assets before: ',self.assets)
                    self.current_state = 'sync_original_assets'
                    self.future = None  # Reset the future so the next state can start its own task
                    self.task_manager.futures= []
                except Exception as error_message:
                    print('an error occurred: ', error_message)  

        elif self.current_state == 'sync_original_assets' and not self.requested_cancel:
            for asset in self.assets:
                print('asset = ', asset)
            #     # print('asset id = ', asset['id'])
            #     # print('asset name = ', asset['name'])

            if self.future is None:
                print('len assets:', self.assets)
                self.task_manager.update_task_status("Initiating download...")
                progress.init(context,len(self.assets),'Syncing assets...')
                self.prog = 0
                future_to_asset = {}
                # for asset in selected_assets:
                    
                #     print('asset: ', asset.name)
                for asset in self.assets:
                    asset_id = asset['id']
                    zipped_asset_name = asset['name']
                    self.prog_text = f'Synced {zipped_asset_name.removesuffix(".zip")}'
                    asset_name =zipped_asset_name.removesuffix(".zip")

                    if not self.requested_cancel:
                        origin_asset = f'original_{asset_name}'
                        if asset_name in bpy.context.blend_data.objects:
                            print(asset_name)
                            asset = bpy.context.blend_data.objects.get(asset_name)
                            copied_asset =asset.copy()
                            bpy.context.scene.collection.objects.link(copied_asset)
                        else: 
                            isPlaceholder = False
                            future = self.task_manager.executor.submit(DownloadFile, self, context, asset_id, zipped_asset_name, self.target_lib, isPlaceholder, self.isPremium, context.workspace)
                            
                            future_to_asset[future] = asset_name
                            self.task_manager.futures.append(future)
                self.current_state = 'waiting_for_download'
                self.future_to_asset = future_to_asset  # Storing the futures so that we can check their status later
                print('this is current_state', self.current_state)
        elif self.current_state == 'waiting_for_download':
            all_futures_done = all(future.done() for future in self.future_to_asset.keys())
            
            if all_futures_done:
                print("all futures done")
                for future, asset_name in self.future_to_asset.items():
                    try:
                        self.downloaded_assets.append(future.result())
                        future = None
                        progress.end(context)
                    except Exception as error_message:
                        print(error_message)   

                self.current_state = 'append_to_current_scene'
                self.future_to_asset = None  # Reset the futures
                
        elif self.current_state == 'append_to_current_scene' and not self.requested_cancel:
            if self.future is None:
                future_to_asset = {}
                
                self.task_manager.update_task_status("appending to scene...")
                for object in self.downloaded_assets:
                     future = self.task_manager.executor.submit(append_to_scene,self, context, object, self.target_lib,context.workspace)
                     future_to_asset[future] = object
                     self.task_manager.futures.append(future)
                self.current_state = 'waiting_for_append'
                self.future_to_asset = future_to_asset
                print('this is current_state', self.current_state)
        elif self.current_state == 'waiting_for_append':
            all_futures_done = all(future.done() for future in self.future_to_asset.keys())
            appended_assets = []
            if all_futures_done:
                print("all futures done")
                for future, asset_name in self.future_to_asset.items():
                    try:
                        appended_assets.append(future.result())
                        print(appended_assets)
                        future = None
                        progress.end(context)
                    except Exception as error_message:
                        print(error_message)
                self.current_state = 'tasks_finished'
                self.future_to_asset = None  # Reset the futures   
        
        
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            self.task_manager.update_task_status("Sync completed")
            self.set_done(True)
            self.task_manager.set_done(True)

        

    def start_tasks(self,context):
       
        self.task_manager.set_total_tasks(3)
        if self.current_state == 'fetch_assets'and not self.requested_cancel:
            # Start the fetch_assets task if it's not started
            
            if self.future is None:
                self.task_manager.update_task_status("Fetching asset list...")
                self.future = self.task_manager.executor.submit(fetch_asset_list)
                self.task_manager.futures.append(self.future)
            elif self.future.done():
                try:
                    self.assets = self.future.result()
                    self.task_manager.increment_completed_tasks()
                    self.current_state = 'compare_assets'
                    self.future = None  # Reset the future so the next state can start its own task
                except Exception as error_message:
                    print(error_message) 
                    

        elif self.current_state == 'compare_assets'and not self.requested_cancel:
            
            if self.future is None:
                self.task_manager.update_task_status("Comparing assets...")
                self.future = self.task_manager.executor.submit(compare_with_local_assets, self, context, self.assets, self.target_lib)
                self.task_manager.futures.append(self.future)
            elif self.future.done():
                try:
                    self.assets_to_download = self.future.result()
                    self.task_manager.increment_completed_tasks()
                    if len(self.assets_to_download) > 0:
                        self.current_state = 'initiate_download'
                        self.future = None  # Reset the future
                    else:
                        self.current_state = 'tasks_finished'
                except Exception as error_message:
                    print(error_message) 
                    

        elif self.current_state == 'initiate_download'and not self.requested_cancel:
            if self.future is None:
                self.task_manager.update_task_status("Initiating download...")
                progress.init(context,len(self.assets_to_download.items()),'Syncing assets...')
                self.prog = 0
                future_to_asset = {}
                
                for asset_id, asset_name in self.assets_to_download.items():
                    if not self.requested_cancel:
                        isPlaceholder = True
                        future = self.task_manager.executor.submit(DownloadFile, self, context, asset_id, asset_name, self.target_lib, isPlaceholder,self.isPremium, context.workspace)
                        future_to_asset[future] = asset_name
                        self.task_manager.futures.append(future)
                self.current_state = 'waiting_for_downloads'
                self.future_to_asset = future_to_asset  # Storing the futures so that we can check their status later

        elif self.current_state == 'waiting_for_downloads':
            all_futures_done = all(future.done() for future in self.future_to_asset.keys())
            
            if all_futures_done:
                print("all futures done")
                for future, asset_name in self.future_to_asset.items():
                    try:
                        result = future.result()
                        future = None
                        bpy.ops.asset.library_refresh()
                    except Exception as error_message:
                        print(error_message) 
                self.future_to_asset = None  # Reset the futures
                self.current_state = 'tasks_finished'
                
                    
        
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            self.future = None
            
            progress.end(context)
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)

    def sync_catalog_file(self,context):
       
        self.task_manager.set_total_tasks(2)
        
        
        if self.current_state == 'fetch_catalog_file_id'and not self.requested_cancel:
            # Start the fetch_assets task if it's not started
            if self.future is None:
                self.task_manager.update_task_status("Fetching catalog id...")
                self.future = self.task_manager.executor.submit(fetch_catalog_file_id)
                self.task_manager.futures.append(self.future)
            elif self.future.done():
                try:
                    print('called')
                    self.catalog_file_info = self.future.result()
                    print(self.catalog_file_info)
                    self.task_manager.increment_completed_tasks()
                    self.current_state = 'initiate_download'
                    self.future = None  # Reset the future so the next state can start its own task
                except Exception as error_message:
                    print(error_message)
       
        elif self.current_state == 'initiate_download'and not self.requested_cancel:
            if self.future is None:
                addon_prefs = addon_info.get_addon_name().preferences
                self.task_manager.update_task_status("Initiating download...")
                progress.init(context,1,'Syncing assets...')
                print('getid', self.catalog_file_info.get('id'))
                print('info ',self.catalog_file_info)
                print(self.catalog_file_info.__dir__())
                FileId = self.catalog_file_info.get('id')
                fileName = self.catalog_file_info.get('name')
                current_file_path = addon_info.get_current_file_location()
                current_file_dir,blend_file = os.path.split(current_file_path)
                isPremium = context.scene.catalog_target_enum.switch_catalog_target
                self.future = self.task_manager.executor.submit(download_cat_file,self, context, FileId, fileName, current_file_dir,context.workspace)
            elif self.future.done():
                try:
                    catalog_file = self.future.result()
                    print(catalog_file)
                    self.task_manager.increment_completed_tasks()
                    self.current_state = 'tasks_finished'
                    self.future = None  # Reset the future so the next state can start its own task
                except Exception as error_message:
                    print(error_message)
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            self.future = None
            progress.end(context)
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.task_manager.set_done(True)

    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done


        

def fetch_asset_list():
    try:
        print("Fetching asset list...")
        assets = network.get_asset_list()
        return assets
    except TaskSpecificException as e:
        raise CriticalException(f"A critical error occurred at (Fetching asset list): {str(e)}")

def fetch_original_asset_ids(selected_assets):
    try:
        # print("Fetching original asset ids...")
        asset_list = network.get_assets_ids_by_name(selected_assets)
        print("asset_list = ", asset_list)
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

def compare_with_local_assets(self,context,assets, target_lib):
    print("comparing asset list...")
    assets_to_download ={} 
    for asset in assets:
        asset_id = asset['id']
        asset_name = asset['name']
        ph_file_name = asset_name.removesuffix('.zip')
        base_name = ph_file_name.removeprefix('PH_')
        if asset_name == 'blender_assets.cats.zip':
            ph_asset_path = f'{target_lib}{os.sep}{base_name}.txt'
        else:
            ph_asset_path = f'{target_lib}{os.sep}{base_name}{os.sep}{ph_file_name}.blend'
        og_asset_path = f'{target_lib}{os.sep}{base_name}{os.sep}{base_name}.blend'
        # print(f'asset_path = {ph_asset_path}')
        # print(f'asset_path = {og_asset_path}')
        if not os.path.exists(ph_asset_path) and not os.path.exists(og_asset_path):
            # print(f'asset_path does not exist = {asset_path}')
            assets_to_download[asset_id] = asset_name
            print(f" {asset_name} new item")    
               
    if len(assets_to_download) > 0:
        self.task_manager.update_subtask_status(f'Total Assets to Sync: {len(assets_to_download)}')
        print(f'Total Assets to Sync: {len(assets_to_download)}')
    else:
        self.task_manager.update_subtask_status('All assets are already synced')
        print(('All assets are already synced'))
    return assets_to_download



        
def append_to_scene(self, context, object_name, target_lib,workspace ):
    try:
        baseName = object_name.removesuffix('.zip')
        blend_file_path = f'{target_lib}{os.sep}{baseName}{os.sep}{baseName}.blend'
        ph_file = f'{target_lib}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
        if os.path.exists(blend_file_path):
            with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
                data_to.objects = data_from.objects
                obj = data_to.objects[0]
            if baseName in bpy.context.blend_data.objects:
                obj = bpy.context.blend_data.objects.get(baseName)
                bpy.context.scene.collection.objects.link(obj)
                os.remove(blend_file_path)
                
        return obj.name
    except Exception as e:
        print(f"An error occurred in append_to_scene: {str(e)}")
        raise TaskSpecificException(f"(Appending to scene) ERROR : {str(e)}")

    

    

def DownloadFile(self, context, FileId, fileName, target_lib, isPlaceholder,isPremium,workspace ):
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
                if not isPlaceholder:
                    baseName = fileName.removesuffix('.zip')
                    print('baseName: ',baseName)
                    ph_file = f'{target_lib}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
                    if os.path.exists(ph_file):
                        if isPremium:
                            pass
                        else:
                            os.rename(ph_file, ph_file.removesuffix('.blend'))
                            # os.remove(ph_file)

                os.remove(fname)
                self.prog += 1
                print('updating progress ', self.prog)
                self.prog_text = f'{fileName} has been Synced' if isPlaceholder else f'{fileName} has been Downloaded'
                progress.update(context, self.prog, self.prog_text, workspace) 
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
                progress.update(context, self.prog, self.prog_text, workspace) 
                return fileName         
    except HttpError as error:
        print(F'An error occurred: {error}')
    


