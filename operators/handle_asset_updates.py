import os
import io
import shutil
import bpy
import functools
import tempfile
from functools import partial
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from ..utils.addon_logger import addon_logger

from ..utils import addon_info
from . import network
from . import task_manager
from ..utils import progress
from . import file_managment


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

class SyncPremiumPreviews:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.task_manager = task_manager.task_manager_instance
        
        self.is_done_flag = False
        self.requested_cancel = False
        self.future = None
        self.server_assets = None
        self.current_state = None
        self.assets_to_download = []
        self.downloaded_assets = []
        self.download_progress_dict = {}
        self.target_lib = None

    def reset(self):
        self.task_manager = task_manager.task_manager_instance
        self.is_done_flag = False
        self.requested_cancel = False
        self.future = None
        self.server_assets = None
        self.current_state = None
        self.assets_to_download = []
        self.downloaded_assets = []   
        self.download_progress_dict = {} 
        self.target_lib = None

    def perform_sync(self,context):
       
        if self.current_state == 'fetch_assets' and not self.requested_cancel:
            try:
                if self.future is None:
                    self.fetch_asset_ids()
                elif self.future.done():
                    self.server_assets = future_result(self)
                    self.current_state = 'compare_assets'
                    self.future = None
            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'compare_assets' and not self.requested_cancel:
            try:
                if self.future is None:
                    self.compare_assets_to_local(context)
                elif self.future.done():
                    self.assets_to_download = future_result(self)
                    if self.assets_to_download:
                        if len(self.assets_to_download) > 0:
                            self.current_state = 'initiate_download'
                            self.future = None
                    else:
                        self.current_state = 'tasks_finished'

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'initiate_download' and not self.requested_cancel:
            try:
                if self.future is None:
                    future_to_asset = {}
                    total_file_size = sum(int(file_size) for _, (_, file_size) in self.assets_to_download.items())
                    downloaded_sizes = {asset_id: 0 for asset_id in self.assets_to_download}
                    for asset_id,(asset_name, file_size) in self.assets_to_download.items():
                        if not self.requested_cancel:
                            future = self.download_previews(context,asset_id,asset_name,file_size,downloaded_sizes)
                            future_to_asset[future] = asset_name
                    self.current_state = 'waiting_for_downloads'
                    self.future_to_asset = future_to_asset

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'waiting_for_downloads':
            try:
                all_futures_done = all(future.done() for future in self.future_to_asset.keys())
                if all_futures_done:
                    print("all futures done")
                    for future, asset_name in self.future_to_asset.items():
                        try:
                            result = future.result()
                            future = None
                            self.downloaded_assets.append(asset_name)
                            
                        except Exception as error_message:
                            print('Error: ',error_message)
                    self.future_to_asset = None
                    self.current_state = 'tasks_finished' 

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 
            
        elif self.current_state == 'tasks_finished':
            self.future = None
            self.is_done_flag = True

            if not self.requested_cancel:
                self.set_done(True)
                bpy.ops.succes.custom_dialog('INVOKE_DEFAULT', 
                    title = 'Sync Complete!', 
                    succes_message=str('If the catalogs dont update, please reopen blender or open a new file'),
                    amount_new_assets=len(self.downloaded_assets),
                    is_original=False
                        )
                self.task_manager.increment_completed_tasks()
                self.task_manager.update_task_status("Sync completed")
            else:
                self.task_manager.update_task_status("Sync cancelled")
            self.reset()
            self.set_done(True)
            

        elif self.requested_cancel:
            self.current_state = 'tasks_finished'

        elif self.current_state =='error':
            self.reset()
            self.future = None
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)
           
            

        
    def fetch_asset_ids(self):
        try:
            submit_task(self,'Fetching premium asset list...',file_managment.fetch_asset_list)
        except Exception as error_message:
            addon_logger.error(error_message)
            print('Error: ', error_message)

    def compare_assets_to_local(self,context):
        try:
            submit_task(self,'Comparing premium assets...', compare_premium_assets_to_local, self, context, self.server_assets, self.target_lib)
        except Exception as error_message:
            addon_logger.error(error_message)
            print('Error: ', error_message)  
    
    
    def download_previews(self,context,asset_id,asset_name,file_size,downloaded_sizes):
        try:
            return submit_task(self,'Comparing premium assets...', file_managment.DownloadFile, self, context, asset_id, asset_name,file_size,True, self.target_lib, context.workspace,downloaded_sizes) 
        except Exception as error_message:
            addon_logger.error(error_message)
            print('Error: ', error_message) 
    
    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done    



class UpdatePremiumAssets:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.task_manager = task_manager.task_manager_instance
        self.isPremium = True if addon_info.is_lib_premium() else False
        self.is_done_flag = False
        self.requested_cancel = False
        self.future = None
        self.assets = None
        self.current_state = None
        self.ph_assets = None
        self.premium_local = None
        self.premium_assets = None
        self.assets_to_download = {}
        self.download_progress_dict = {}
        self.downloaded_assets = []

    def reset(self):
        self.task_manager = task_manager.task_manager_instance
        self.isPremium = True if addon_info.is_lib_premium() else False
        self.is_done_flag = False
        self.requested_cancel = False
        self.future = None
        self.assets = None
        self.current_state = None
        self.ph_assets = None
        self.premium_local = None
        self.premium_assets = None
        self.assets_to_download = {}
        self.download_progress_dict = {}
        self.downloaded_assets = []


    
    def perform_update(self,context):

        if self.current_state == 'perform_update' and not self.requested_cancel:
            self.target_lib = addon_info.get_target_lib(context).path
            self.task_manager.set_total_tasks(3)
            try:
                if not self.isPremium:
                    if self.future is None:
                        assets = [asset for asset in context.scene.assets_to_update if asset.selected]
                        self.assets_to_download={asset.id:(asset.name,asset.size) for asset in assets}
                        self.current_state = 'initiate_download'
                else:
                    self.assets = context.scene.premium_assets_to_update
                    if self.future is None:
                        self.ph_assets =[asset for asset in self.assets if asset.is_placeholder]
                        self.premium_local =[asset for asset in self.assets if not asset.is_placeholder and asset.selected]

                        
                        self.fetch_premium_asset_ids()
                    elif self.future.done():
                        self.premium_assets = future_result(self)
                        if self.premium_assets:
                            if len(self.premium_assets) > 0:
                                premium_names = [asset['name'] for asset in self.premium_assets]
                                #add premium assets to download dict
                                for asset in self.premium_assets:
                                    self.assets_to_download[asset['id']] = (asset['name'],asset['size'])
                                
                                #add premium placeholder assets to download dict
                                for asset in self.ph_assets:
                                    base_name = asset.name.removeprefix('PH_')
                                    if base_name in premium_names:
                                        asset.selected = True
                                        self.assets_to_download[asset.id] = (asset.name,asset.size)
                                self.current_state = 'initiate_download'
                                self.future = None
                        else:
                            print('no premium assets found')
                            self.current_state = 'tasks_finished'

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error'



        elif self.current_state == 'initiate_download' and not self.requested_cancel:
            try:
                if self.future is None:
                    future_to_asset = {}
                    total_file_size = sum(int(file_size) for _, (_, file_size) in self.assets_to_download.items())
                    downloaded_sizes = {asset_id: 0 for asset_id in self.assets_to_download}  
                    progress.init(context,total_file_size,'Syncing assets...')
                    
                    for asset_id,(asset_name, file_size) in self.assets_to_download.items():
                        if not self.requested_cancel:
                            future = self.downloads_assets(context,asset_id,asset_name,file_size,total_file_size,downloaded_sizes)
                            future_to_asset[future] = asset_name
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_downloads'

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'waiting_for_downloads':
            try:
                all_futures_done = all(future.done() for future in self.future_to_asset.keys())
                if all_futures_done:
                    print("all futures done")
                    for future, asset_name in self.future_to_asset.items():
                        self.downloaded_assets.append(future.result())
                        future = None
                    bpy.ops.asset.library_refresh()
                    progress.end(context)
                    self.future = None
                    self.future_to_asset = None
                    if self.isPremium:
                        self.current_state = 'append_to_current_scene'
                    else:
                        self.current_state = 'finish_update'

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'append_to_current_scene':
            try:
                if self.future is None:
                    future_to_asset = {}
                    self.task_manager.update_task_status("appending to scene...")
                    print('self.downloaded_assets: ',self.downloaded_assets)
                    for asset in self.downloaded_assets:
                        print('asset: ',asset)
                        if not asset.startswith('PH_'):
                            future = self.append_and_replace(context,asset)
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
                    for future, asset in self.future_to_asset.items():
                        appended_assets.append(future.result())
                        future = None
                    self.current_state = 'finish_update'
                    self.future_to_asset = None

            except Exception as error_message:
                print('an error occurred: ', error_message) 
                addon_logger.error(error_message)
                self.current_state = 'error' 

        elif self.current_state == 'finish_update': 
            assets_to_update = context.scene.premium_assets_to_update if self.isPremium else context.scene.assets_to_update
            if len(assets_to_update)>0:
                indices_to_remove = [index for index, asset in enumerate(assets_to_update) if asset.name in self.downloaded_assets]
                # Remove items in reverse order so we don't mess up the indices as we go
                for index in sorted(indices_to_remove, reverse=True):
                    if self.isPremium:
                        context.scene.premium_assets_to_update.remove(index)
                    else:
                        context.scene.assets_to_update.remove(index)
                self.current_state = 'tasks_finished'

        elif self.current_state == 'tasks_finished':
            self.future = None
            self.is_done_flag = True
            progress.end(context)
            bpy.ops.succes.custom_dialog('INVOKE_DEFAULT', 
                title = 'Sync Complete!', 
                succes_message=str(''),
                amount_new_assets=len(self.downloaded_assets),
                is_original=False
                    )
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync completed")
            self.reset()
            self.set_done(True)
            self.current_state = None

        elif self.requested_cancel:
            self.current_state = 'tasks_finished'

        elif self.current_state =='error':
            self.future = None
            progress.end(context)
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)
            self.current_state = None

    def fetch_premium_asset_ids(self):
        try:
            
            submit_task(self,'Fetching premium asset ids...',network.get_premium_assets_ids_by_name,self.premium_local)
            # submit_task(self,'testfunction...',self.tempfunction)
        except Exception as error_message:
            addon_logger.error(error_message)
            print('Error: ', error_message)
        
    def tempfunction(self):
        for asset in self.premium_local:
            print('self.premium_assets ',asset)
        for asset in self.ph_assets:
            print('self.ph_assets ',asset)

    def downloads_assets(self,context,asset_id,asset_name,file_size,total_file_size,downloaded_sizes):
        try:
            # return submit_task(self,'testfunction...',self.tempfunction)
            return submit_task(self,'Downloading assets...', file_managment.DownloadFile, self, context, asset_id, asset_name,file_size,True,True, self.target_lib, context.workspace,total_file_size,downloaded_sizes)
        except Exception as error_message:
            addon_logger.error(error_message)
            print('Error: ', error_message)

    def append_and_replace(self,context, asset_name):
        try:
            print('asset_name ',asset_name)
            return submit_task(self,'Appending and replacing outdated premium asset...', file_managment.append_to_scene, self,context, asset_name, self.target_lib,context.workspace)
        except Exception as error_message:
            addon_logger.error(error_message)
            print('Error: ', error_message)

    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done 

def compare_premium_assets_to_local(self,context,assets,target_lib):
    context.scene.premium_assets_to_update.clear()
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
            catfile =asset_name.replace('.zip','.txt')
            ph_asset_path = f'{target_lib}{os.sep}{catfile}'
        else:
            ph_asset_path = f'{target_lib}{os.sep}{base_name}{os.sep}{ph_file_name}.blend'
       
            
        print(ph_asset_path)              
            #if preview does not exist in local add it to downloads
        if not os.path.exists(ph_asset_path):
            assets_to_download[asset_id] =  (asset_name, file_size)
            print(f" {asset_name} new item")
        else:
            
            #if premium asset is present in blendfile
            isAssetLocal = addon_info.find_asset_by_name(base_name)  
            #we check if server file is newer
            l_m_time = os.path.getmtime(ph_asset_path)
            g_m_time = asset['modifiedTime'] 
            l_m_datetime,g_m_datetime = addon_info.convert_to_UTC_datetime(l_m_time,g_m_time)
            if l_m_datetime<g_m_datetime:
                if not isAssetLocal:
                    assets_to_download[asset_id] =  (asset_name, file_size)
                    print(f" {asset_name} preview file has update")
                else:
                    print(f'OG{og_name} has update ', l_m_datetime, ' < ',g_m_datetime)
                    file_size = int(asset['size'])
                    add_ph_asset = context.scene.premium_assets_to_update.add()
                    add_ph_asset.name = asset_name
                    add_ph_asset.id = asset_id
                    add_ph_asset.size = file_size
                    add_ph_asset.is_placeholder = True

                    add_orginal_asset = context.scene.premium_assets_to_update.add()
                    add_orginal_asset.name = og_name 
                    add_orginal_asset.id = ''
                    add_orginal_asset.size = 0
                    add_orginal_asset.is_placeholder = False
            else:
                print(f'OG{og_name} is up to date ')
            

    return assets_to_download