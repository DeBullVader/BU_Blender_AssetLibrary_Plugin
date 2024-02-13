import bpy,os
from ..utils import addon_info,addon_logger,progress
from . import task_manager,network
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
        self.asset_author = ''
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
        self.asset_author = ''
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
            self.task_manager.update_task_status("Sync had error")
            self.task_manager.set_done(True)

    def handle_author_folder(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        try:
            author = addon_info.get_author()
            if author == 'Anonymous':
                author = self.asset_author if self.asset_author != '' else 'Anonymous'
            if addon_prefs.debug_mode == False:
                files =[]

                author_folder,ph_folder_id, self.new_author = find_author_folder(author)
                
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




            
   