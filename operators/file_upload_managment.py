import bpy
import os
import shutil
import zipfile
import logging
import threading
import functools
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from ..utils import addon_info
from . import network
from . import task_manager
from ..utils import progress
from .folder_management import find_author_folder
from . import generate_placeholder_previews
from ..utils.exceptions import UploadException

class TaskSpecificException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)

class CriticalException(Exception):
    def __init__(self, message="A critical error occurred"):
        super().__init__(message)

class AssetUploadSync:
    def __init__(self):
        self.task_manager = task_manager.task_manager_instance
        self.is_done_flag = False
        self.current_state = 'initiate_upload'
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
        self.workspace = None
    def sync_assets_to_server(self,context):
        self.selected_assets = context.selected_asset_files
        if self.current_state == 'initiate_upload':
            if self.future is None:
                self.task_manager.update_task_status("Initiating upload...")
                self.future = self.task_manager.executor.submit(find_author_folder)
                
            elif self.future.done():
                author_folder,ph_folder_id,self.new_author = self.future.result()
                self.folder_ids = (author_folder,ph_folder_id)
                if self.new_author:
                    self.existing_assets =[]
                    
                    self.current_state = 'start_uploading_assets'
                else:
                    self.current_state = 'check_for_existing_assets'
                self.future = None
     
        # elif self.current_state == 'create_assets_and_placeholders':
        #     if self.selected_assets != None:
        #         self.task_manager.update_task_status("creating assets...")
        #         print(self.selected_assets)
        #         for obj in self.selected_assets:
        #             zipped_original,zipped_placeholder = create_and_zip_files(self,context,obj)
        #             if zipped_original not in  self.files_to_upload:
        #                 self.files_to_upload.append(zipped_original)
        #                 print('zipped asset', zipped_original)
        #             if zipped_placeholder not in  self.files_to_upload:
        #                 self.files_to_upload.append(zipped_placeholder)
        #                 print('zipped asset', zipped_placeholder)
        #         if self.new_author:
        #             self.existing_assets =[]
        #             self.current_state = 'start_uploading_assets'
        #         else:
        #             self.current_state = 'check_for_existing_assets'
        #         self.future = None
        elif self.current_state == 'check_for_existing_assets':
            if self.future is None:
                self.task_manager.update_task_status("fetching existing assets...")
               
                self.future =self.task_manager.executor.submit(network.get_excisting_assets_from_author,self.folder_ids)
            elif self.future.done():
                self.existing_assets = self.future.result()
                self.current_state = 'start_uploading_assets'
                self.future = None
        
        elif self.current_state == 'start_uploading_assets':
            print('Inside start_uploading_assets')
            if self.future is None:
                self.task_manager.update_task_status("Uploading assets...")
                print(len(self.files_to_upload))
                progress.init(context,len(self.files_to_upload),'Syncing...')
                future_to_asset = {}
                
                for file_to_upload in self.files_to_upload:
                    # print(file_to_upload)
                    author_folder,ph_folder_id = self.folder_ids
                    self.workspace = context.workspace
                    path,file_name = os.path.split(file_to_upload)
                    if file_name.startswith('PH_') or file_name == 'blender_assets.cats.zip':
                        upload_folder = ph_folder_id
                    else:
                        upload_folder = author_folder
                    try:
                        self.task_manager.update_task_status(f"Uploading {file_name} ...")
                        future = self.task_manager.executor.submit(network.upload_files,self,context,file_to_upload,upload_folder,self.existing_assets,self.prog,self.workspace)
                        future_to_asset[future] = file_to_upload
                        self.prog += 1
                    except Exception as error_message:
                        print('upload_files failed! Reason:',error_message) 
                    
                self.current_state = 'waiting_for_upload'
                self.future_to_asset = future_to_asset
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
            self.future = None
            self.task_manager.update_task_status("Sync completed")
            self.set_done(True)
            self.task_manager.set_done(True)

    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done

def create_file(self,service,media,file_metadata):
    try:
        service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        
        print(f"File : {file_metadata['name']}was created and uploaded.")
    except UploadException as e:
        print( f'create_file failed! {e}')

def generate_placeholder_blend_file(self,obj,asset_thumb_path):
    try:
        # generate placeholder preview via compositor
        placeholder_thumb_path = generate_placeholder_previews.composite_placeholder_previews(asset_thumb_path)

        asset_thumb_dir = os.path.dirname(asset_thumb_path)
        uploadlib = addon_info.get_upload_asset_library()
        addon_path = addon_info.get_addon_path()
    
        placeholder_blendfile_path = f'{addon_path}{os.sep}BU_plugin_assets{os.sep}blend_files{os.sep}PlaceholderFile.blend'
        # upload_asset_file_path = f'{uploadlib}{os.sep}{obj.name}{os.sep}{obj.name}.blend'
        # upload_asset_dir,blend_file = os.path.split(upload_asset_file_path)
        upload_placeholder_file_path = f'{uploadlib}{os.sep}Placeholders{os.sep}{obj.name}{os.sep}PH_{obj.name}.blend'
        asset_placeholder_dir,placeholder_file = os.path.split(upload_placeholder_file_path)
        #create paths
        
        os.makedirs(asset_placeholder_dir, exist_ok=True)
        os.makedirs(f'{asset_thumb_dir}' , exist_ok=True)
        print('in generate_placeholder_blend_file')
        #load in placeholder file
        with bpy.data.libraries.load(placeholder_blendfile_path) as (data_from, data_to):
            data_to.objects = data_from.objects

        # for object in data_to.objects:
        object = data_to.objects[0]
        object.asset_mark()
        original_name = obj.name
        object.name = obj.name
        attributes_to_copy = ['copyright', 'catalog_id', 'description', 'tags','license', 'author',]
        # Copy metadata
        for attr in attributes_to_copy:
            if hasattr(obj.asset_data, attr):
                setattr(object.asset_data, attr, getattr(obj.asset_data, attr))
        #set placeholder thumb
        # print(object)
        if object != None:
            bpy.ops.ed.lib_id_load_custom_preview(
                {"id": object}, 
                filepath = placeholder_thumb_path
            )
        #save and remove object    
        datablock = {object}
        bpy.data.libraries.write(upload_placeholder_file_path, datablock)
        bpy.data.objects.remove(object)
        obj.local_id.name = original_name
        print('done generate_placeholder_blend_file')
        return 'done'
    except Exception as e:
        print('error in composite_placeholder_previews',e)

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

def get_asset_thumb_paths(obj,current_file_path):
    base_filename = obj.name
    thumbs_directory = f"{current_file_path}{os.sep}thumbs"
    print(f'{thumbs_directory}{os.sep}{base_filename}.png')
    if os.path.exists(f'{thumbs_directory}{os.sep}{base_filename}.png'):
        asset_thumb_path= f'{thumbs_directory}{os.sep}{base_filename}.png'
    elif os.path.exists(f'{thumbs_directory}{os.sep}{base_filename}.jpg'):
        asset_thumb_path=f'{thumbs_directory}{os.sep}{base_filename}.jpg'
    else:
        asset_thumb_path = ''
        print(asset_thumb_path)
    return asset_thumb_path

            
   




def create_and_zip_files(self,context,obj):
    try:
        # print(obj.name)
        files_to_upload=[]
        current_file_path = os.path.dirname(bpy.data.filepath)
        uploadlib = addon_info.get_upload_asset_library()
        asset_upload_file_path = f"{uploadlib}{os.sep}{obj.name}{os.sep}{obj.name}.blend"
        placeholder_folder_file_path = f"{uploadlib}{os.sep}Placeholders{os.sep}{obj.name}{os.sep}PH_{obj.name}.blend"
        asset_thumb_path = get_asset_thumb_paths(obj,current_file_path)
        #make the asset folder with the objects name (obj.name)
        
        if not os.path.exists(asset_thumb_path):
            ShowNoThumbsWarning("Could not find the thumbs folder or the thumbnail in the current file location make sure it exists with the same name!", 'ERROR')
            print('Could not find the thumbs folder or the thumbnail in the current file location make sure it exists with the same name!')
            # raise UploadException("Could not find the thumbs folder or the thumbnail in the current file location make sure it exists with the same name!")
        else:
            try:
                asset_folder_dir = os.path.dirname(asset_upload_file_path)
                asset_placeholder_folder_dir = os.path.dirname(placeholder_folder_file_path)
                os.makedirs(asset_folder_dir, exist_ok=True)
                os.makedirs(asset_placeholder_folder_dir, exist_ok=True)
                # save only the selected asset to a new clean blend file
                datablock ={obj.local_id}
                bpy.data.libraries.write(asset_upload_file_path, datablock)

                
                #generate placeholder files and thumbnails
                generate_placeholder_blend_file(self,obj,asset_thumb_path)

                zipped_original =zip_directory(asset_folder_dir)
                zipped_placeholder =zip_directory(asset_placeholder_folder_dir)

            except Exception as e:
                print(f'create_and_zip_files failed! {e}')
                
        return (zipped_original,zipped_placeholder)
    except Exception as e:
        print(f'create_and_zip_files failed! {e}')