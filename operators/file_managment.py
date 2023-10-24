import os
import io
import shutil
import bpy
import functools
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
        self.assets = None
        self.assets_to_download = None
        self.prog = 0
        self.prog_text = None
    


    def sync_original_assets(self,context,isPremium):
        selected_assets = context.selected_asset_files
        if self.current_state == 'fetch_original_asset_ids':
            # Start the fetch_assets task if it's not started
            if self.future is None:
                if isPremium:
                    self.future = self.task_manager.executor.submit(fetch_original_premium_asset_ids, selected_assets)
                else:
                    self.future = self.task_manager.executor.submit(fetch_original_asset_ids, selected_assets)
                print(f'isPremium = {isPremium}')
                print('Future done: ', self.future.done())
            elif self.future.done():
                print('Future done: ', self.future.done())
                print('Future result: ', self.future.result())
                try:
                    self.assets = self.future.result()
                    print('self.assets = ', self.assets)
                    self.current_state = 'sync_original_assets'
                    self.future = None  # Reset the future so the next state can start its own task
                except Exception as error_message:
                    print(error_message)
                    

        elif self.current_state == 'sync_original_assets':
            for asset in self.assets:
                print('asset = ', asset)
                print('asset id = ', asset['id'])
                print('asset name = ', asset['name'])
            if self.future is None:
                self.task_manager.update_task_status("Initiating download...")
                progress.init(context,len(self.assets),'Syncing assets...')
                self.prog = 0
                future_to_asset = {}
                for asset in self.assets:
                    asset_id = asset['id']
                    asset_name = asset['name']
                    self.prog_text = f'Synced {asset_name.removesuffix(".zip")}'
                    future = self.task_manager.executor.submit(DownloadFile, self, context, asset_id, asset_name, self.target_lib, False, context.workspace)
                    future_to_asset[future] = asset_name

                self.current_state = 'waiting_for_downloads'
                self.future_to_asset = future_to_asset  # Storing the futures so that we can check their status later

        elif self.current_state == 'waiting_for_downloads':
            all_futures_done = all(future.done() for future in self.future_to_asset.keys())
            
            if all_futures_done:
                print("all futures done")
                for future, asset_name in self.future_to_asset.items():
                    try:
                        self.zip_files = future.result()
                    except Exception as error_message:
                        print(error_message)   

                self.current_state = 'tasks_finished'
                self.future_to_asset = None  # Reset the futures
        
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            progress.end(context)
            self.task_manager.update_task_status("Sync completed")
            self.set_done(True)
            self.task_manager.set_done(True)
        
    

    def start_tasks(self,context):
        # print(f'task manager = {self.task_manager}')
        self.task_manager.set_total_tasks(3)
        if self.current_state == 'fetch_assets':
            # Start the fetch_assets task if it's not started
            
            if self.future is None:
                self.task_manager.update_task_status("Fetching asset list...")
                self.future = self.task_manager.executor.submit(fetch_asset_list)
            elif self.future.done():
                try:
                    self.assets = self.future.result()
                    self.task_manager.increment_completed_tasks()
                    self.current_state = 'compare_assets'
                    self.future = None  # Reset the future so the next state can start its own task
                except Exception as error_message:
                    print(error_message) 
                    

        elif self.current_state == 'compare_assets':
            
            if self.future is None:
                self.task_manager.update_task_status("Comparing assets...")
                self.future = self.task_manager.executor.submit(compare_with_local_assets, self, context, self.assets, self.target_lib)
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
                    

        elif self.current_state == 'initiate_download':
            if self.future is None:
                self.task_manager.update_task_status("Initiating download...")
                progress.init(context,len(self.assets_to_download.items()),'Syncing assets...')
                self.prog = 0
                future_to_asset = {}
                
                for asset_id, asset_name in self.assets_to_download.items():
                    future = self.task_manager.executor.submit(DownloadFile, self, context, asset_id, asset_name, self.target_lib, True, context.workspace)
                    future_to_asset[future] = asset_name

                self.current_state = 'waiting_for_downloads'
                self.future_to_asset = future_to_asset  # Storing the futures so that we can check their status later

        elif self.current_state == 'waiting_for_downloads':
            all_futures_done = all(future.done() for future in self.future_to_asset.keys())
            
            if all_futures_done:
                print("all futures done")
                for future, asset_name in self.future_to_asset.items():
                    try:
                        future.result()
                    except Exception as error_message:
                        print(error_message) 
                self.future_to_asset = None  # Reset the futures
                self.current_state = 'tasks_finished'
                
                    
        
        elif self.current_state == 'tasks_finished':
            print('Tasks finished')
            self.future = None
            
            progress.end(context)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.set_done(True)
            self.task_manager.set_done(True)
  
    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done


        

def fetch_asset_list():
    # try:
    print("Fetching asset list...")
    assets = network.get_asset_list()
    return assets
    # except TaskSpecificException as e:
        # raise CriticalException(f"A critical error occurred at (Fetching asset list): {str(e)}")

def fetch_original_asset_ids(selected_assets):
    try:
        print("Fetching original asset ids...")
        return network.get_assets_ids_by_name(selected_assets)
    except TaskSpecificException as e:
        raise CriticalException(f"A critical error occurred at (Fetching original asset ids): {str(e)}")  
    
def fetch_original_premium_asset_ids(selected_assets):
    try:
        print("Fetching original Premium asset ids...")
        return network.get_premium_assets_ids_by_name(selected_assets)
    except TaskSpecificException as e:
        raise CriticalException(f"A critical error occurred at (Fetching original Premium asset ids): {str(e)}")      

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

def to_the_fucking_moon(avax):
    pass

class StarsArena():
    def __init__(self):
        print("GM Stars Arena,")
        print("another beautiful day to build!")
        self.avax = 10
        
    def update(self, context):
        self.avax += 1
        to_the_fucking_moon(self.avax)


        


    

def DownloadFile(self, context, FileId, fileName, target_lib, isPlaceholder,workspace ):
    try:
        authService = network.google_service()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        
        done = False

        while done is False:
            status, done = downloader.next_chunk()
            print({"INFO"}, f"{fileName} has been Synced")
        file.seek(0)
        
        with open(os.path.join(target_lib, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            if ".zip" in fileName:
                fname = target_lib + os.sep + fileName
                shutil.unpack_archive(fname, target_lib, 'zip')
                if not isPlaceholder:
                    baseName = fileName.removesuffix('.zip')
                    ph_file = f'{target_lib}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
                    if os.path.exists(ph_file):
                        os.remove(ph_file)
                os.remove(fname)

                self.prog += 1
                print('updating progress ', self.prog)
                progress.update(context, self.prog, self.prog_text, workspace)          
    except HttpError as error:
        print(F'An error occurred: {error}')
    return fileName


