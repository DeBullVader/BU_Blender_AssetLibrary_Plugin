import bpy
import os
import shutil
import zipfile
import logging
import threading
import functools
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from ..ui import generate_previews
from ..utils import addon_info,exceptions,addon_logger
from . import network
from . import task_manager
from ..utils import progress
from .folder_management import find_author_folder
from ..utils.exceptions import UploadException

class TaskSpecificException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)

class CriticalException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)

class AssetUploadSync:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.task_manager = task_manager.task_manager_instance
        self.is_done_flag = False
        self.current_state = None
        self.future = None
        self.selected_assets = None
        self.folder_ids = None
        self.existing_assets = None
        self.assets_to_upload = []
        self.prog = 0
        self.prog_text = None
        self.files_to_upload =[]
        self.assets_uploaded = []
        self.future_to_asset=[]
        self.current_file_path = addon_info.get_current_file_location()
        self.uploadlib = addon_info.get_upload_asset_library()
        self.asset_thumb_paths =[]
        self.asset_and_thumbs = {}
        self.new_author = False
        self.requested_cancel = False

    def reset(self):
        self.task_manager = task_manager.task_manager_instance
        self.is_done_flag = False
        self.current_state = None
        self.future = None
        self.selected_assets = None
        self.folder_ids = None
        self.existing_assets = None
        self.assets_to_upload = []
        self.prog = 0
        self.prog_text = None
        self.files_to_upload =[]
        self.assets_uploaded = []
        self.future_to_asset=[]
        self.current_file_path = addon_info.get_current_file_location()
        self.uploadlib = addon_info.get_upload_asset_library()
        self.asset_thumb_paths =[]
        self.asset_and_thumbs = {}
        self.new_author = False
        self.requested_cancel = False

    def sync_assets_to_server(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        self.selected_assets = context.selected_asset_files
    
        if self.current_state == 'initiate_upload':
            self.task_manager.update_task_status("Initiating upload...")
            if self.future is None:
                self.task_manager.update_task_status("checking for existing assets...")
                self.future = self.task_manager.executor.submit(self.handle_author_folder,context)
                
            elif self.future.done():
                self.existing_assets = self.future.result()
                self.current_state = 'start_uploading_assets'
                self.future = None
        
        elif self.current_state == 'start_uploading_assets':
           
            
            if self.future is None:
                self.task_manager.update_task_status("Uploading assets...")
                print(len(self.files_to_upload))
                progress.init(context, len(self.files_to_upload), 'Syncing...')
                future_to_asset = {}
                prog = 0
                main_folder, ph_folder_id = self.folder_ids
                try:
                    for file_to_upload in self.files_to_upload:
                        path,file_name =os.path.split(file_to_upload)
                        if addon_prefs.debug_mode:
                            # print('file_name',file_name)
                            if file_name.startswith('PH_') or file_name == 'blender_assets.cats.zip':
                                folderid = ph_folder_id
                            else:
                                folderid = main_folder
                        else:
                            folderid = main_folder
                        prog+=1
                        print('prog',prog)
                        future = self.task_manager.executor.submit(network.upload_files,self,context,file_to_upload,folderid,self.existing_assets,prog,context.workspace)
                        future_to_asset[future] = file_to_upload
                    
                    self.future_to_asset = future_to_asset
                    self.current_state = 'waiting_for_upload'   
                    
          
                except Exception as error_message:
                    print('an error occurred: ', error_message) 
                    addon_logger.addon_logger.error(f'Error Uploading{error_message}')
                    self.current_state = 'error'  
                    
        
        elif self.current_state == 'waiting_for_upload':
            all_futures_done = all(future.done() for future in self.future_to_asset.keys())
            
            if all_futures_done:
                print("all futures done")
                self.task_manager.update_task_status(f"Uploaded {len(self.future_to_asset)} assets! ")
                self.prog = 0
                self.current_state = 'tasks_finished'
                self.future_to_asset = None 
                
        elif self.current_state == 'tasks_finished':
            progress.end(context)
            print('Tasks finished')
            self.reset()
            self.future = None
            self.task_manager.update_task_status("Sync completed")
            self.set_done(True)
            self.task_manager.set_done(True)

        elif self.requested_cancel:
            self.current_state = 'tasks_finished'

        elif self.current_state =='error':
            self.reset()
            self.future = None
            self.set_done(True)
            self.task_manager.increment_completed_tasks()
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)

    def handle_author_folder(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        try:
            if addon_prefs.debug_mode == False:
                files =[]
                author_folder,ph_folder_id, self.new_author = find_author_folder()
                self.folder_ids = (author_folder,ph_folder_id)
                if self.new_author:
                    return files
                else:
                    files = network.get_excisting_assets_from_author(self.folder_ids)
                return files
            else:
                
                print(addon_prefs.test_upload_folder_id)
                print(addon_prefs.test_upload_placeholder_folder_id)
                self.folder_ids =(addon_prefs.test_upload_folder_id,addon_prefs.test_upload_placeholder_folder_id)
                files = network.get_excisting_assets_from_author(self.folder_ids)
                return files
        except Exception as e:
            addon_logger.addon_logger.error(f"handle_author_folder Error: {e}")
            print(f"handle_author_folder Error: {e}")
            # raise exceptions.FolderManagementException(message=f"handle_author_folder Error: {e}")

    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done\



def create_file(self,service,media,file_metadata):
    try:
        service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        
        print(f"File : {file_metadata['name']}was created and uploaded.")
    except UploadException as e:
        addon_logger.addon_logger.error(f'create_file failed! {e}')
        print( f'create_file failed! {e}')

def generate_placeholder_blend_file(self,asset,asset_thumb_path):
    try:
        # generate placeholder preview via compositor
        thumb_dir,preview_file = os.path.split(asset_thumb_path)
        ph_preview_file = f"PH_preview_{asset.name}.png"
        placeholder_thumb_path = os.path.join(thumb_dir,'Placeholder_Previews', ph_preview_file)
        print('placeholder_thumb_path',placeholder_thumb_path)
        # if not os.path.exists(placeholder_thumb_path):
        #     ph_preview_file = f"PH_preview_{asset.name}.jpg"
        #     placeholder_thumb_path = os.path.join(asset_thumb_path, ph_preview_file)
        #     if not os.path.exists(placeholder_thumb_path):
        #         raise Exception('Placeholder preview not found please rerender asset in the mark tool')
        if os.path.exists(asset_thumb_path):  
            if not os.path.exists(placeholder_thumb_path):
                ph_preview_file = f"PH_preview_{asset.name}.jpg"
                placeholder_thumb_path = os.path.join(asset_thumb_path, ph_preview_file)
                if not os.path.exists(placeholder_thumb_path):
                    placeholder_thumb_path = generate_previews.composite_placeholder_previews(asset_thumb_path)
        asset_thumb_dir = os.path.dirname(asset_thumb_path)
        uploadlib = addon_info.get_upload_asset_library()
        addon_path = addon_info.get_addon_path()
        asset_types =addon_info.type_mapping()
        
        # upload_asset_file_path = f'{uploadlib}{os.sep}{obj.name}{os.sep}{obj.name}.blend'
        # upload_asset_dir,blend_file = os.path.split(upload_asset_file_path)
        upload_placeholder_file_path = f'{uploadlib}{os.sep}Placeholders{os.sep}{asset.name}{os.sep}PH_{asset.name}.blend'
        asset_placeholder_dir,placeholder_file = os.path.split(upload_placeholder_file_path)
        #create paths
        
        os.makedirs(asset_placeholder_dir, exist_ok=True)
        os.makedirs(f'{asset_thumb_dir}' , exist_ok=True)
        
        #load in placeholder file

        if asset.id_type in asset_types:
            data_collection = getattr(bpy.data, asset_types[asset.id_type])
            if asset.id_type == 'NODETREE':
                nodetype = asset.local_id.bl_idname
                ph_asset = data_collection.new(f'PH_{asset.name}',nodetype)
            elif asset.id_type == 'OBJECT':
                ph_asset = data_collection.new(f'PH_{asset.name}',None)
            else:
                ph_asset = data_collection.new(f'PH_{asset.name}')
    
        
        ph_asset.asset_mark()
        original_name = asset.name
        ph_asset.name = asset.name
        attributes_to_copy = ['copyright', 'catalog_id', 'description', 'tags','license', 'author',]
        # Copy metadata
        for attr in attributes_to_copy:
            if hasattr(asset.asset_data, attr) and getattr(asset.asset_data, attr):
                if attr == 'tags':

                    # Copy each tag individually
                    for tag in getattr(asset.asset_data, attr):
                        new_tag = ph_asset.asset_data.tags.new(name=tag.name)
                        
                else:
                    setattr(ph_asset.asset_data, attr, getattr(asset.asset_data, attr))
        #set placeholder thumb
        if ph_asset != None:
            bpy.ops.ed.lib_id_load_custom_preview(
                {"id": ph_asset}, 
                filepath = placeholder_thumb_path
            )
        #save and remove ph_asset    
        datablock = {ph_asset}
        bpy.data.libraries.write(upload_placeholder_file_path, datablock)
        data_collection.remove(ph_asset)
        asset.local_id.name = original_name
        print('done generate_placeholder_blend_file')
        return 'done'
    except Exception as e:
        addon_logger.addon_logger.error(f'error in generating previews: {e}')
        print('error in  generating previews: ',e)

def zip_directory(folder_path):
    root_dir,asset_folder = os.path.split(folder_path)
    if root_dir.endswith(f'{os.sep}Placeholders'):
        zip_path = os.path.join(root_dir,f'PH_{asset_folder}.zip')
    else:
        zip_path = os.path.join(root_dir,f'{asset_folder}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                zipf.write(full_path, rel_path)
                
    # Remove the original folder
    shutil.rmtree(folder_path)
    return zip_path
def ShowNoThumbsWarning(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
        
def zip_and_append(file_path, files_to_upload):
    zipped_asset = zip_directory(file_path)
    return zipped_asset

def get_asset_thumb_paths(asset):
    addon_prefs = addon_info.get_addon_name().preferences
        
    thumbs_directory = addon_prefs.thumb_upload_path
    base_filename = asset.name
    
    asset_thumb_path = ''
    if os.path.exists(f'{thumbs_directory}{os.sep}preview_{base_filename}.png'):
        asset_thumb_path= f'{thumbs_directory}{os.sep}preview_{base_filename}.png'
    elif os.path.exists(f'{thumbs_directory}{os.sep}preview_{base_filename}.jpg'):
        asset_thumb_path=f'{thumbs_directory}{os.sep}preview_{base_filename}.jpg'
    return asset_thumb_path

            
   




def create_and_zip_files(self,context,asset,asset_thumb_path):
    try:
        # print(obj.name)
        files_to_upload=[]
        current_file_path = os.path.dirname(bpy.data.filepath)
        uploadlib = addon_info.get_upload_asset_library()
        asset_upload_file_path = f"{uploadlib}{os.sep}{asset.name}{os.sep}{asset.name}.blend"
        placeholder_folder_file_path = f"{uploadlib}{os.sep}Placeholders{os.sep}{asset.name}{os.sep}PH_{asset.name}.blend"
        asset_thumb_path = get_asset_thumb_paths(asset)
        #make the asset folder with the objects name (obj.name)
        
        asset_folder_dir = os.path.dirname(asset_upload_file_path)
        asset_placeholder_folder_dir = os.path.dirname(placeholder_folder_file_path)
        os.makedirs(asset_folder_dir, exist_ok=True)
        os.makedirs(asset_placeholder_folder_dir, exist_ok=True)
        # save only the selected asset to a new clean blend file
        datablock ={asset.local_id}
        bpy.data.libraries.write(asset_upload_file_path, datablock)

        
        #generate placeholder files and thumbnails
        generate_placeholder_blend_file(self,asset,asset_thumb_path)

        zipped_original =zip_directory(asset_folder_dir)
        zipped_placeholder =zip_directory(asset_placeholder_folder_dir)

        if zipped_original and zipped_placeholder:    
            return (zipped_original,zipped_placeholder)
        else:
            raise Exception('couldnt zip files')
    except Exception as e:
        addon_logger.addon_logger.error(f'create_and_zip_files failed: {e}')
        print(f'create_and_zip_files failed! {e}')