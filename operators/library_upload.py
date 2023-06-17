import bpy
from pathlib import Path
import os
import shutil
import zipfile
import logging
import threading
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from .. import icons
from ..utils import addon_info,catfile_handler
from .. import progress

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

log = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/drive']
KEY_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"

def copy_catalog_file():
    upload_lib = addon_info.get_upload_asset_library()
    current_filepath,catfile = os.path.split(catfile_handler.get_current_file_catalog_filepath())
    shutil.copy(os.path.join(current_filepath,catfile), os.path.join(upload_lib.path,catfile))
    upload_catfile = os.path.join(upload_lib.path,catfile)
    return upload_catfile

def get_author():
    author = addon_info.get_addon_name().preferences.author
    if author == '':
        author = 'Anonymous'
    return author

def Gservice():
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)
        # Build the service object.
        service = build('drive', 'v3', credentials=credentials)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
    # Call the Drive v3 API

def check_for_author_folder(folder_metadata):
    service = Gservice()
    author = get_author()
    files  = []
    page_token = None
    if service is not None:
        print(f'this is service: {service}')
        while True:
            response = service.files().list(
                q="name='" + author + "' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='nextPageToken, ''files(id, name)',
                pageToken=page_token).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        # Trash duplicate folders while testing
        # print(f'This is Response: {response}')
        # if len(response)>0:
        #     for file in files:
        #         file_id = file.get('id')
        #         body = {'trashed': True}
        #         service.files().update(fileId=file_id, body=body).execute()
        #         service.files().emptyTrash().execute()
        # print(response.get('id'))
        if len(files)>0:
            print(response)
            print("Folder ID_excists: ", files[0].get("name"))
            folder_id = files[0].get("id")
            return folder_id
        else:
            # create the folder
            file = service.files().create(body=folder_metadata, fields="id").execute()
            # get the folder id
            folder_id = file.get("id")
            print("Folder ID created: ", folder_id)
            return folder_id

def Clear_same_file_on_server(folder_id,files_to_upload):
    service = Gservice()
    files  = []
    new_files_to_upload =[]
    page_token = None
    if service is not None:
        while True:
            response = service.files().list(
                q="'"+ folder_id + "' in parents and mimeType='application/zip' and trashed=false",
                spaces='drive',
                fields='nextPageToken, ''files(id, name,parents,trashed)',
                pageToken=page_token).execute()
            if response is not None:
                files.extend(response.get('files', []))
                for file in files:
                    file_id = file.get('id')
                    body = {'trashed': True}
                    service.files().update(fileId=file_id, body=body).execute()
                    service.files().emptyTrash().execute()
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
            
        return 

def copy_and_zip_catfile():
        uploadlib = addon_info.get_upload_asset_library()
        catfile = copy_catalog_file()
        print(catfile)
        base_name = catfile.replace('.txt','.zip')
        zipf = zipfile.ZipFile(base_name, 'w', zipfile.ZIP_DEFLATED)
        root_dir,cfile = os.path.split(catfile)
        os.chdir(root_dir) 
        zipf.write(cfile)
        return base_name

def create_and_zip_files(self,context,uploadlib):
    files_to_upload =[]
    for obj in context.selected_asset_files:
        blend_file_path = f'{uploadlib.path}{os.sep}{obj.name}.blend'
        
        #Local id is the local datablock this asset represents
        datablock ={obj.local_id}
        bpy.data.libraries.write(blend_file_path, datablock)
        #Zip and compress the blend file
        base_name = blend_file_path.replace('.blend','.zip')
        zipf = zipfile.ZipFile(base_name, 'w', zipfile.ZIP_DEFLATED)
        root_dir,blend_file = os.path.split(blend_file_path)
        os.chdir(root_dir) 
        zipf.write(blend_file)
        os.remove(blend_file_path)
        if base_name not in  files_to_upload:
            files_to_upload.append(base_name)
    return files_to_upload

def upload_files(file_to_upload,folder_id):
    service = Gservice()
    root_dir,file_name = os.path.split(file_to_upload)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_to_upload, mimetype='application/zip')
    created_file = service.files().create(body=file_metadata, media_body=media,fields='id').execute()
    if created_file:
        print(f'File with id: {created_file.get("id")} uploaded.')
        return created_file

    


class WM_OT_SaveAssetFiles(bpy.types.Operator):
    bl_idname = "wm.save_files"
    bl_label = "Upload to BBPS Server"
    bl_description = "Upload assets to the Baked Blender Pro Suite upload server."
    bl_options = {"REGISTER", "UNDO"}
    
    prog = 0
    prog_text = None
    
    num_uploaded = 0
    _timer = None
    th = None
    prog_downloaded_text = None

    @classmethod
    def poll(cls, context):
        if context.selected_asset_files:
            return True, context.window_manager.bu_props.progress_total == 0
        return False

    def modal(self, context, event):
        if event.type == "TIMER":
            progress.update(context, self.prog, self.prog_text)
            if not self.th.is_alive():
                log.debug("FINISHED ALL THREADS")
                progress.end(context)
                self.th.join()
                prog_word = "Downloaded"
                self.report(
                    {"INFO"}, f"{prog_word} {self.num_uploaded} asset{'s' if self.num_uploaded != 1 else ''}"
                ) 
                try:
                    bpy.ops.asset.library_refresh()
                except RuntimeError:
                    # Context has changed
                    pass
                return {"FINISHED"}

        return {"PASS_THROUGH"}
    def execute(self, context):
        def threadedUpload(self,files_to_upload):

            executor = ThreadPoolExecutor(max_workers=20)
            threads = []
            count = 0
            
            for file_to_upload in files_to_upload:
                t=executor.submit(upload_files,file_to_upload,folder_id)
                threads.append(t)
                count +=1
            progress.init(context, count, word = "Saving and Zipping")
            finished_threads =[]
            while True:
                for thread in threads:
                    if thread._state == "FINISHED":
                        if thread not in finished_threads:
                            finished_threads.append(thread)
                            self.prog += 1
                            result = thread.result()
                    
                            if result is not None:
                                if context.window_manager.bu_props.assets_to_upload > 0:
                                    context.window_manager.bu_props.assets_to_upload -=1
                                print(result)
                                self.num_uploaded += 1
                                prog_word = result.get('id') + ' Has been saved and zipped'
                                self.prog_text = f"{prog_word} "
                                context.window_manager.bu_props.progress_uploaded_text = f"{prog_word} "
                        
                                # self.report( {"INFO"}, f"{result}{prog_word}")
                                
                if all(t._state == 'FINISHED' for t in threads):
                    context.window_manager.bu_props.assets_to_upload = 0
                    catfile = copy_catalog_file()
                    files_to_upload.append(catfile)
                    break
                sleep(0.5)
        try:
 
            folder_metadata = {
            "name": get_author(),
            "mimeType": "application/vnd.google-apps.folder",
            "parents": ['1MGjz9fKcP7tfpmZdCXS5DSezeLXoPpx8']
            }
        except HttpError as error:
            print(f'An error occurred: {error}')

        folder_id = check_for_author_folder(folder_metadata)
        
        uploadlib = addon_info.get_upload_asset_library()
        files_to_upload = create_and_zip_files(self,context,uploadlib)
        base_name =copy_and_zip_catfile()
        files_to_upload.append(base_name)
        Clear_same_file_on_server(folder_id,files_to_upload)
        context.window_manager.bu_props.assets_to_upload = len(files_to_upload)
        self.th = threading.Thread(target=threadedUpload, args=(self,files_to_upload))

        self.th.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)        
        return {"RUNNING_MODAL"}

    

    




classes = (
    WM_OT_SaveAssetFiles,
    )
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
  

    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

