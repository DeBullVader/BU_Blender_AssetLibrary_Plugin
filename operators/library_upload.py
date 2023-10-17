import bpy
import os
import shutil
import zipfile
import logging
import threading

from time import sleep
from concurrent.futures import ThreadPoolExecutor
from ..utils import addon_info,catfile_handler
from ..utils import progress
from . import generate_placeholder_previews
from ..utils.exceptions import UploadException

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from .folder_management import find_author_folder
from .network import google_service

log = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/drive']
KEY_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"


    

def clear_same_file_on_server(folder_id,files_to_upload):
    service = google_service()
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


def testFunction(self,context):
    parent_folder = context.scene.upload_parent_folder_id
    print(f'parent folder is {parent_folder}')





def generate_placeholder_blend_file(obj,asset_thumb_path):
    asset_thumb_dir = os.path.dirname(asset_thumb_path)
    asset_thumb_file = os.path.basename(asset_thumb_path)
    uploadlib = addon_info.get_upload_asset_library()
    #generate placeholder preview via compositor
    placeholder_thumb_path = generate_placeholder_previews.composite_placeholder_previews(asset_thumb_path)

    addon_path = addon_info.get_addon_path()
    placeholder_blendfile_path = f'{addon_path}{os.sep}BU_plugin_assets{os.sep}blend_files{os.sep}PlaceholderFile.blend'
    upload_asset_file_path = f'{uploadlib}{os.sep}{obj.name}{os.sep}{obj.name}.blend'
    upload_asset_dir,blend_file = os.path.split(upload_asset_file_path)
    upload_placeholder_file_path = f'{uploadlib}{os.sep}Placeholders{os.sep}{obj.name}{os.sep}PH_{obj.name}.blend'
    asset_placeholder_dir,placeholder_file = os.path.split(upload_placeholder_file_path)
    #create paths
    
    os.makedirs(asset_placeholder_dir, exist_ok=True)
    os.makedirs(f'{asset_thumb_dir}' , exist_ok=True)

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


def copy_and_zip_catfile():
    #copy catfile from current
    upload_lib = addon_info.get_upload_asset_library()
    current_filepath,catfile = os.path.split(catfile_handler.get_current_file_catalog_filepath())
    shutil.copy(os.path.join(current_filepath,catfile), os.path.join(upload_lib,catfile))
    upload_catfile = os.path.join(upload_lib,catfile)
    #zip catfile
    zipped_cat_path = upload_catfile.replace('.txt','.zip')
    zipf = zipfile.ZipFile(zipped_cat_path, 'w', zipfile.ZIP_DEFLATED)
    root_dir,cfile = os.path.split(upload_catfile)
    os.chdir(root_dir) 
    zipf.write(cfile)
    return zipped_cat_path

def ShowNoThumbsWarning(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
        
def zip_and_append(file_path, files_to_upload):
    zipped_asset = zip_directory(file_path)
    if zipped_asset not in  files_to_upload:
        files_to_upload.append(zipped_asset)
    
def create_and_zip_files(self,context):
    try:
        files_to_upload =[]
        selected_assets = context.selected_asset_files
        current_file_path = addon_info.get_current_file_location()
        uploadlib = addon_info.get_upload_asset_library()

        if selected_assets != None:
            for obj in selected_assets:
                asset_upload_file_path = f"{uploadlib}{os.sep}{obj.name}{os.sep}{obj.name}.blend"
                current_file_path = os.path.dirname(bpy.data.filepath)
                asset_thumb_path= f"{current_file_path}{os.sep}thumbs{os.sep}{obj.name}.png"
                placeholder_folder_file_path = f"{uploadlib}{os.sep}Placeholders{os.sep}{obj.name}{os.sep}PH_{obj.name}.blend"

                #make the asset folder with the objects name (obj.name)
                asset_folder_dir = os.path.dirname(asset_upload_file_path)
                asset_placeholder_folder_dir = os.path.dirname(placeholder_folder_file_path)
                os.makedirs(asset_folder_dir, exist_ok=True)
                os.makedirs(asset_placeholder_folder_dir, exist_ok=True)
                
                if not os.path.exists(asset_thumb_path):
                    ShowNoThumbsWarning("Could not find the thumbs folder or the thumbnail in the current file locationn make sure it exists with the same name!", 'ERROR')
                else:
                    # save only the selected asset to a new clean blend file
                    datablock ={obj.local_id}
                    bpy.data.libraries.write(asset_upload_file_path, datablock)
                    
                    #generate placeholder files and thumbnails
                    generate_placeholder_blend_file(obj,asset_thumb_path)
                    zip_and_append(asset_folder_dir, files_to_upload)
                    zip_and_append(asset_placeholder_folder_dir, files_to_upload)

            return files_to_upload
    except UploadException as e:
         self.report({"ERROR"}, f'create_and_zip_files failed! {e}')

def create_file(self,service,media,file_metadata):
    try:
        service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        self.report({"INFO"},f"File : {file_metadata['name']}was created and uploaded.")
    except UploadException as e:
        self.report({"ERROR"}, f'create_file failed! {e}')

def update_file(self,service,file_id,media,updated_metadata):
    try:
        service.files().update(fileId=file_id,body=updated_metadata, media_body=media).execute()
        self.report({"INFO"},f"File : {updated_metadata['name']} uploaded and updated.")
    except UploadException as e:
        self.report({"ERROR"}, f'update_file failed! {e}')

def trash_duplicate_files(service,file):
    for idx,f in enumerate(file):
            if idx !=0:
                f_id = f['id']
                body = {'trashed': True}
                service.files().update(fileId=f_id, body=body).execute()
                service.files().emptyTrash().execute()
                print(f'{f.get("name")} had double files. Removed index larger then 0')

def upload_files(self,file_to_upload,folder_id,files):
    print(f'processing uploads')
    service = google_service()
    root_dir,file_name = os.path.split(file_to_upload)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    updated_metadata={
         'name': file_name,
    }
    media = MediaFileUpload(file_to_upload, mimetype='application/zip')
    file =[file for file in files if file['name'] == file_name]
    
    if len(file)>0:
        trash_duplicate_files(service,file)
        file_id = file[0].get('id')
        update_file(self,service,file_id,media,updated_metadata)
    else:
        create_file(self,service,media,file_metadata)
    return 


def threaded_upload(self,context,files_to_upload,folder_ids):
    
    service = google_service()
    files  = []
    pageSize = 1000
    author_folder_id,ph_folder_id = folder_ids
    query = f"('{author_folder_id}' in parents or '{ph_folder_id}' in parents) and (mimeType='application/zip') and (trashed=false)"
    request = service.files().list(q=query, pageSize=pageSize, fields="nextPageToken, files(id,name)")
    while request is not None:
        try:
            response = request.execute()
            files.extend(response.get('files', []))
            if len(response.get('files', [])) < pageSize:
                break 
            request = service.files().list_next(request, response)
        except HttpError as error:
            self.report({"ERROR"},f'An HTTP error occurred in threaded_upload: {error}')
            raise UploadException(f"Failed to fetch due to HTTP Error: {error}") from error
    
    executor = ThreadPoolExecutor(max_workers=20)
    threads = []
    count = 0
    
    for file_to_upload in files_to_upload:
        folder,ph_folder = folder_ids
        path,file_name = os.path.split(file_to_upload)
        if file_name.startswith('PH_'):
            upload_folder = ph_folder
        else:
            upload_folder = folder

        t=executor.submit(upload_files,self,file_to_upload,upload_folder,files)
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
                        self.report( {"INFO"}, f"{result}{prog_word}")
                        
        if all(t._state == 'FINISHED' for t in threads):
            context.window_manager.bu_props.assets_to_upload = 0
            break
        sleep(0.5)
    


class WM_OT_SaveAssetFiles(bpy.types.Operator):
    bl_idname = "wm.save_files"
    bl_label = "Upload to BUK Server"
    bl_description = "Upload assets to the Blender Universe Kit upload folder on the server."
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
            return True
        return False
    
    def modal(self, context, event):
        if event.type == "TIMER":
            progress.update(context, self.prog, self.prog_text,context.workspace)
            if not self.th.is_alive():
                self.report({"INFO"},"FINISHED ALL THREADS")
                progress.end(context)
                self.th.join()
                context.scene.status_text = 'Upload completed!'
                self.report({"INFO"}, f"Number of files uploaded: {self.num_uploaded}") 
                bpy.ops.asset.library_refresh()

                return {"FINISHED"}

        return {"PASS_THROUGH"}
    def execute(self, context):
        try:
            folder_ids = find_author_folder(self)
            files_to_upload = create_and_zip_files(self,context)
            catfile =copy_and_zip_catfile()
            files_to_upload.append(catfile)
        
            context.window_manager.bu_props.assets_to_upload = len(files_to_upload)
            self.th = threading.Thread(target=threaded_upload, args=(self,context,files_to_upload,folder_ids))
            self.th.start()
        except UploadException as e:
            self.report({"ERROR"}, e.message)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)        
        return {"RUNNING_MODAL"}
    

class CustomException(Exception):
    def __init__(self, message, origin):
        super().__init__(message)
        self.origin = origin

classes = (
    WM_OT_SaveAssetFiles,
    )
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
  

    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

