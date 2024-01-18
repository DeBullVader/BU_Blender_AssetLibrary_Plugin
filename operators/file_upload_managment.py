import bpy
import os
import shutil
import zipfile
import json
import datetime
from ..ui import generate_previews
from ..utils import addon_info,exceptions,addon_logger
from . import network
from . import task_manager
from ..utils import progress,version_handler
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
        self.upload_progress_dict = {}
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
        self.upload_progress_dict = {}
        self.future_to_asset=[]
        self.current_file_path = addon_info.get_current_file_location()
        self.uploadlib = addon_info.get_upload_asset_library()
        self.asset_thumb_paths =[]
        self.asset_and_thumbs = {}
        self.new_author = False
        self.requested_cancel = False

    def sync_assets_to_server(self, context):
        addon_prefs = addon_info.get_addon_name().preferences

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
                progress.init(context, len(self.files_to_upload), 'Syncing...')
                future_to_asset = {}
                self.prog = 0
                main_folder, ph_folder_id = self.folder_ids
                try:
                    for file_to_upload in self.files_to_upload:
                        path,file_name =os.path.split(file_to_upload)
                        self.upload_progress_dict[file_name]='Status:Uploading...'
                        
                        
                        # print('file_name',file_name)
                        if file_name.startswith('PH_') or file_name == 'blender_assets.cats.zip':
                            folderid = ph_folder_id
                        else:
                            folderid = main_folder
                    
                        future = self.task_manager.executor.submit(network.upload_files,self,context,file_to_upload,folderid,self.existing_assets,self.prog,context.workspace)
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
                print(author_folder,ph_folder_id, self.new_author)
                self.folder_ids = (author_folder,ph_folder_id)
                if self.new_author:
                    return files
                else:
                    files = network.get_excisting_assets_from_author(self.folder_ids)
                return files
            else:
                
                self.folder_ids =(addon_prefs.upload_folder_id,addon_prefs.upload_placeholder_folder_id)
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
        self.is_done_flag = is_done



def create_file(self,service,media,file_metadata):
    try:
        service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        
        print(f"File : {file_metadata['name']}was created and uploaded.")
    except UploadException as e:
        addon_logger.addon_logger.error(f'create_file failed! {e}')
        print( f'create_file failed! {e}')

def generate_placeholder_blend_file(self,context,asset,asset_thumb_path):
    try:
        datablock = None
        upload_placeholder_file_path = ''
        # generate placeholder preview via compositor
        thumb_dir,preview_file = os.path.split(asset_thumb_path)
        ph_preview_file = f"PH_{preview_file}"
        placeholder_thumb_path = os.path.join(thumb_dir,'Placeholder_Previews', ph_preview_file)
        
        if os.path.exists(asset_thumb_path):  
            if not os.path.exists(placeholder_thumb_path):
                ph_preview_file = f"PH_{preview_file}"
                placeholder_thumb_path = os.path.join(asset_thumb_path, ph_preview_file)
                if not os.path.exists(placeholder_thumb_path):
                    placeholder_thumb_path = generate_previews.composite_placeholder_previews(asset_thumb_path)
        asset_thumb_dir = os.path.dirname(asset_thumb_path)
        uploadlib = addon_info.get_upload_asset_library()
        asset_types =addon_info.type_mapping()
        ph_blend_file_name =f'PH_{asset.name}.blend'
        upload_placeholder_file_path = os.path.join(uploadlib, 'Placeholders', asset.name,ph_blend_file_name)
        asset_placeholder_dir,placeholder_file = os.path.split(upload_placeholder_file_path)
        #create paths
        
        os.makedirs(asset_placeholder_dir, exist_ok=True)
        os.makedirs(asset_thumb_dir , exist_ok=True)

        #load in placeholder file, temporarily rename original file and name the placeholder as the original

        if asset.id_type in asset_types:
            tempname = f'temp_{asset.name}'
            original_name = asset.name
            
            data_collection = getattr(bpy.data, asset_types[asset.id_type])
            if asset.id_type == 'NODETREE':
                nodetype = asset.local_id.bl_idname
                ph_asset = data_collection.new(f'PH_{original_name}',nodetype)
            elif asset.id_type == 'OBJECT':
                ph_asset = data_collection.new(f'PH_{original_name}',None)
            else:
                ph_asset = data_collection.new(f'PH_{original_name}')
        else:
            print('asset_type not supported')

        real_asset =data_collection.get(asset.name)
        real_asset.name = tempname
        ph_original_name = ph_asset.name
        ph_asset.asset_mark()
        ph_asset.name = original_name
        if version_handler.latest_version(context):
            ph_metadata = ph_asset.asset_data
            asset_metadata = asset.metadata
        else:
            ph_metadata = ph_asset.asset_data
            asset_metadata = asset.asset_data
        attributes_to_copy = ['copyright', 'catalog_id', 'description', 'tags','license', 'author',]
        # Copy metadata
        for attr in attributes_to_copy:
            if attr =='tags':
                if version_handler.latest_version(context):
                    if '4.0 asset' not in asset_metadata.tags:
                        asset_metadata.tags.new(name='4.0 asset')
                if 'Original' not in asset_metadata.tags:
                    asset_metadata.tags.new(name='Original')
                if 'Placeholder' not in ph_metadata.tags:
                    ph_metadata.tags.new(name='Placeholder')
            if hasattr(asset_metadata, attr) and getattr(asset_metadata, attr):
                if attr == 'tags':
                    # Copy each tag individually
                    for tag in getattr(asset_metadata, attr):
                        if tag.name != 'Original':
                            ph_metadata.tags.new(name=tag.name)  
                else:
                    setattr(ph_metadata, attr, getattr(asset_metadata, attr))

        #set placeholder thumb
        assign_custom_preview_ph_asset(self,context,ph_asset,placeholder_thumb_path)
        
        #Create Placeholder Asset info JSON data
        asset_info = {
            "BU_Asset": ph_original_name,
            "Asset_type": asset.id_type,
            "Placeholder": True
            }
        creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        asset_info['creation_time'] = creation_time
        json_data = json.dumps(asset_info, indent=4)
        BU_Json_Text = bpy.data.texts.get("BU_PH_Asset_Info")
        if BU_Json_Text is None:
            BU_Json_Text = bpy.data.texts.new("BU_PH_Asset_Info")
        BU_Json_Text = bpy.data.texts.new("BU_PH_Asset_Info")
        BU_Json_Text.write(json_data)

        datablock = {ph_asset, BU_Json_Text}
        bpy.data.libraries.write(upload_placeholder_file_path, datablock)
        bpy.data.texts.remove(BU_Json_Text)
        ph_asset.name = ph_original_name 
        real_asset.name = original_name

        return ph_asset
    except Exception as e:
        addon_logger.addon_logger.error(f'error in generating previews: {e}')
        print('error in  generating previews: ',e)
        raise Exception(f'error in  generating previews: {e}')
    


def assign_custom_preview_ph_asset(self,context,ph_asset,file_path):
        asset =ph_asset
        if bpy.app.version >= (4,0,0):
            if os.path.exists(file_path):

                with bpy.context.temp_override(id=asset):
                    bpy.ops.ed.lib_id_load_custom_preview(filepath = file_path)
                
        else:
            bpy.ops.ed.lib_id_load_custom_preview(
                {"id": ph_asset}, 
                filepath = file_path
                )
            
    

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

            
   