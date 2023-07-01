import bpy
from pathlib import Path
import os
import shutil
import zipfile
import logging
import threading
import textwrap
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
    shutil.copy(os.path.join(current_filepath,catfile), os.path.join(upload_lib,catfile))
    upload_catfile = os.path.join(upload_lib,catfile)
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

def check_for_author_folder(self,context,folder_metadata):
    service = Gservice()
    author = get_author()
    files  = []
    page_token = None
    if service is not None:

        while True:
            response = service.files().list(
                q="name='" + author + "' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='nextPageToken,''files(id,name)',
                pageToken=page_token).execute()
            current_library_name = context.area.spaces.active.params.asset_library_ref
            if current_library_name == "LOCAL":
                parents_folder = '1MGjz9fKcP7tfpmZdCXS5DSezeLXoPpx8'

            else:
                parents_folder = '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ'
            
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        # Trash duplicate folders while testing
        if len(files)>0:
                for idx,file in enumerate(files):
                    if idx !=0:
                        print(f'file: {file}')
                        file_id = file.get('id')
                        body = {'trashed': True}
                        service.files().update(fileId=file_id, body=body).execute()
                        service.files().emptyTrash().execute()
            
        if len(files)>0:
            print("Folder ID_excists: ", files[0].get("name"))
            folder_id = files[0].get("id")
            return folder_id
        else:
            file = service.files().create(body=folder_metadata, fields="id").execute()
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
                if len(files)>0:
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

def zip_files(self,context,targetlib):
    files_to_upload =[]

    for obj in context.selected_asset_files:

        blend_file_path = f'{targetlib.path}{os.sep}{obj.name}{os.sep}{obj.name}.blend'
        print(obj.name)
        base_name = blend_file_path.replace('.blend','.zip')
        zipf = zipfile.ZipFile(base_name, 'w', zipfile.ZIP_DEFLATED)
        root_dir,blend_file = os.path.split(blend_file_path)
        os.chdir(root_dir) 
        zipf.write(blend_file)
        if base_name not in  files_to_upload:
            files_to_upload.append(base_name)
    return files_to_upload
    
def create_and_zip_files(self,context,uploadlib):
    files_to_upload =[]

    for obj in bpy.context.selected_asset_files:      
        blend_file_path = f'{uploadlib}{os.sep}{obj.name}.blend'
        
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



def upload_files(file_to_upload,folder_id,files):
# DEV NODE: this code needs to happen per asset. so get the id or name check if excists then upload. or do all at ones
    service = Gservice()
    root_dir,file_name = os.path.split(file_to_upload)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    updated_metadata={
         'name': file_name,
    }
    media = MediaFileUpload(file_to_upload, mimetype='application/zip')
    file =[
        file for file in files if file['name'] == file_name 
        and file['parents'][0] == folder_id
        and file['trashed'] == False 
        ]
    if len(file)>0:
        for idx,f in enumerate(file):
            if idx !=0:
                f_id = f['id']
                body = {'trashed': True}
                service.files().update(fileId=f_id, body=body).execute()
                service.files().emptyTrash().execute()
                print(f'{f.get("name")} had dubble files. Removed index larger then 0')
    if len(file)>0:
        # print(f'n_file = {n_file} file_name = {file_name}')
        file_id = file[0].get('id')
        updated_files = service.files().update(fileId=file_id,body=updated_metadata, media_body=media).execute()
        if updated_files:
            print(f'File with id: {updated_files.get("id")} uploaded and updated.')
            # return updated_files

    else:
        print(f'file not found: {file_name} {file}')
        media = MediaFileUpload(file_to_upload, mimetype='application/zip')
        created_file = service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        if created_file:
            print(f'File with id: {created_file.get("id")} was created and uploaded')
            # return created_file
    return 

#  Args: FOR UPDATE GOOGLE DRIVE API
#     service: Drive API service instance.
#     file_id: ID of the file to update.
#     new_title: New title for the file.
#     new_description: New description for the file.
#     new_mime_type: New MIME type for the file.
#     new_filename: Filename of the new content to upload.
#     new_revision: Whether or not to create a new revision for this file.
#   Returns:
#     Updated file metadata if successful, None otherwise.
#   """



    


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
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        elif context.selected_asset_files:
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
            
            service = Gservice()
            files  = []
            request = service.files().list(pageSize= 20, fields="nextPageToken, files(id,name,parents,trashed)")
            if service is not None:
                while request is not None:
                    result = request.execute()
                    files.extend(result.get('files', []))
                    request = service.files().list_next(request, result)
            
            executor = ThreadPoolExecutor(max_workers=20)
            threads = []
            count = 0
            
            for file_to_upload in files_to_upload:
                t=executor.submit(upload_files,file_to_upload,folder_id,files)
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
                                # print(result)
                                self.num_uploaded += 1
                                prog_word = result.get('id') + ' Has been saved and zipped'
                                self.prog_text = f"{prog_word} "
                                context.window_manager.bu_props.progress_uploaded_text = f"{prog_word} "
                        
                                # self.report( {"INFO"}, f"{result}{prog_word}")
                                
                if all(t._state == 'FINISHED' for t in threads):
                    context.window_manager.bu_props.assets_to_upload = 0
                    break
                sleep(0.5)

        current_library_name = context.area.spaces.active.params.asset_library_ref
        if current_library_name == "LOCAL":
            parents_folder = '1MGjz9fKcP7tfpmZdCXS5DSezeLXoPpx8'
        else:
            parents_folder = '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ'
        folder_metadata = {
        "name": get_author(),
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parents_folder]
        }

        current_library_name = context.area.spaces.active.params.asset_library_ref
        if current_library_name == "LOCAL":
            folder_id = check_for_author_folder(self,context,folder_metadata)
            uploadlib = addon_info.get_upload_asset_library()
            files_to_upload = create_and_zip_files(self,context,uploadlib)
            # Clear_same_file_on_server(folder_id,files_to_upload)
        else:
            uploadlib = context.preferences.filepaths.asset_libraries[current_library_name]
            files_to_upload = zip_files(self,context,uploadlib)
            folder_id = '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ'
            # Clear_same_file_on_server(folder_id,files_to_upload)
        catfile =copy_and_zip_catfile()
        files_to_upload.append(catfile)
        
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

