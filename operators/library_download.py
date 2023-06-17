from __future__ import print_function
import bpy
import logging
import io
import os
import datetime
from dateutil import parser
import shutil
import threading
import platform
from bpy.app.handlers import persistent

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from tempfile import NamedTemporaryFile
from bpy.types import Operator
from .. import progress
from ..utils.addon_info import get_core_asset_library,get_upload_asset_library

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

log = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

KEY_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"

assets_to_download={}



def Gservice():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)
    # Build the service object.
    service = build('drive', 'v3', credentials=credentials)
    return service
    # Call the Drive v3 API



def get_asset_list():
    asset_list ={}
    try:
        authService = Gservice()
        # Build the service object.

    # Call the Drive v3 API
        page_token = None
        folder_id = '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ'
        request = authService.files().list(                
                q="'"+ folder_id + "' in parents and mimeType='application/zip' and trashed=false",
                spaces='drive',
                fields='nextPageToken, ''files(id, name)',
                pageToken=page_token)
      
        while request is not None:
            result = request.execute()
            items = result.get('files', [])
            if not items:
                print('ERROR: No files found.')
            for item in items:
                if not item['id'] == '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ':
                    asset_list[item['id']] = item['name']

            request = authService.files().list_next(request, result)
        return asset_list
    
    except HttpError as error:
      
        print(f'An error occurred: {error}')

def get_asset_list_m_time():
    asset_list_m_time ={}
    try:
        authService = Gservice()
        # Build the service object.

    # Call the Drive v3 API
        page_token = None
        folder_id = '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ'
        request = authService.files().list(                
                q="'"+ folder_id + "' in parents and mimeType='application/zip' and trashed=false",
                spaces='drive',
                fields='nextPageToken, ''files(id,modifiedTime)',
                pageToken=page_token)
                    

        while request is not None:
            result = request.execute()
            items = result.get('files', [])
            if not items:
                print('ERROR: No files found.')
            for item in items:
                if not item['id'] == '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ':
                    asset_list_m_time[item['id']] = item['modifiedTime']

            request = authService.files().list_next(request, result)
        return asset_list_m_time
    
    except HttpError as error:
      
        print(f'An error occurred: {error}')

def FileMetadataById(AsetListId):
    authService = Gservice()      
    try:
       
        request = authService.files().get(fileId=AsetListId, fields="id, name, modifiedTime").execute()
        return request
    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

def BULibPath():
    assetlibs = bpy.context.preferences.filepaths.asset_libraries
    UploadFolder = "BU_User_Upload"
    for lib in assetlibs:
        if lib.name == "BU_AssetLibrary_Core":
            lib_path = lib.path
            # print (lib_path)
        if lib.name == "BU_User_Upload":
            upload_path = lib.path
            return lib_path,upload_path

def DownloadFile(FileId,fileName):
    # libpaths = BULibPath()
    core_lib = get_core_asset_library(bpy.context)

    try:
        authService = Gservice()

                # pylint: disable=maybe-no-member
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print({"INFO"}, f"{fileName} has been dowloaded")
        file.seek(0)

        
        with open(os.path.join(core_lib.path, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            if ".zip" in fileName:
                fname = core_lib.path + os.sep + fileName
                
        
                if not fileName == "blender_assets.cats.zip":
                    foldername = str.removesuffix(fname,'.zip')
                    if os.path.exists(foldername):
                        shutil.unpack_archive(fname, foldername, 'zip')
                        os.remove(fname)
                    else:
                        os.makedirs(foldername)
                        shutil.unpack_archive(fname, foldername, 'zip')
                        os.remove(fname)
                else:
                    shutil.unpack_archive(fname, core_lib.path, 'zip')
                    os.remove(fname)
                    

           
                    
    except HttpError as error:
        print(F'An error occurred: {error}')
    
    # file = None
    return fileName



 #  "19ODT1rdTbfZjpGLXs_fj21C9FOIj_p-N" # File ID of Blender_assets_cat
class WM_OT_downloadAll(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadall"
    bl_label = "Download Baked Universe asset library"
    bl_description = "Updates the local asset library with new assets from Baked Universe"
    bl_options = {"REGISTER", "UNDO"}

    prog = 0
    prog_text = None
    
    num_downloaded = 0
    _timer = None
    th = None
    prog_downloaded_text = None


    @classmethod
    def poll(self, context):
        assetlibs = bpy.context.preferences.filepaths.asset_libraries
        if "BU_AssetLibrary_Core" not in assetlibs :
            return False
        else:
            return True, context.window_manager.bu_props.progress_total == 0

    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)
    
    def modal(self, context, event):
        if event.type == "TIMER":
            progress.update(context, self.prog, self.prog_text)
            # ephemeral.recently_downloaded = self.recently_downloaded

            if not self.th.is_alive():
                log.debug("FINISHED ALL THREADS")
                progress.end(context)
                self.th.join()
                prog_word = "Downloaded"
                self.report(
                    {"INFO"}, f"{prog_word} {self.num_downloaded} asset{'s' if self.num_downloaded != 1 else ''}"
                ) 
                try:
                    bpy.ops.asset.library_refresh()
                except RuntimeError:
                    # Context has changed
                    pass
                return {"FINISHED"}

        return {"PASS_THROUGH"}
    
    def execute(self, context):
        
        def threadedDownload(self,assets):

            
            executor = ThreadPoolExecutor(max_workers=20)
            threads = []
            count = 0
            for asset_id,asset_name in assets:
            #     core_lib = get_core_asset_library(context)
            # # fileSavepath,fileUploadpath = BULibPath()
                blend_file = get_unpacked_names(asset_name)
            #     asset_path = os.path.join(core_lib.path,folder_name)
            #     blend_file_path = os.path.join(asset_path,blend_file)

            #     if not asset_name == "blender_assets.cats.zip":
            #         asset_path = core_lib.path + os.sep + folder_name
            #     else:
            #         asset_path = core_lib.path
            #     if check_excist(asset_name, asset_path):
            #         print(f" {asset_path}{asset_name} already exists ")
                # if not is_server_asset_updated(asset_id,asset_path):
                #     asset_update =False
                #     print(f" {blend_file} is up-to-date")
                        
                        
                    
                # else:
                t=executor.submit(DownloadFile, asset_id,asset_name)
                threads.append(t)
                count +=1
            progress.init(context, count, word = "Downloading")
            finished_threads =[]
            while True:
                for thread in threads:
                    if thread._state == "FINISHED":
                        if thread not in finished_threads:
                            finished_threads.append(thread)
                            self.prog += 1
                            result = thread.result()
                            
                            # if error:
                            #     self.report({"ERROR"}, error)
                            if result is not None:
                                if context.window_manager.bu_props.new_assets > 0:
                                    context.window_manager.bu_props.new_assets -=1
                                if context.window_manager.bu_props.updated_assets >0:
                                    context.window_manager.bu_props.updated_assets -=1
                                self.num_downloaded += 1
                                # prog_word = result + ' has been Updated' if asset_update else ' has been Downloaded'
                                prog_word = result + ' has been Updated has been Downloaded'
                                self.prog_text = f"{prog_word} "
                                context.window_manager.bu_props.progress_downloaded_text = f"{prog_word} "
                        
                                # self.report( {"INFO"}, f"{result}{prog_word}")
                                
                if all(t._state == 'FINISHED' for t in threads):
                    context.window_manager.bu_props.new_assets = 0
                    context.window_manager.bu_props.updated_asset = 0
                    copy_cats_file(context)
                    break
                sleep(0.5)
        global assets_to_download
        assets = assets_to_download.items()
        # print(assets)
        # if error:
        #     self.report({'ERROR'}, error)
        #     return {'CANCELLED'}

        # gives to many values to unpack error needs checking
        
        self.th = threading.Thread(target=threadedDownload, args=(self, assets))

        self.th.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)        
        return {"RUNNING_MODAL"}
            
        
def copy_cats_file(context):
    upload_lib = get_upload_asset_library(context)
    core_lib = get_core_asset_library(context)    
    file = 'blender_assets.cats.txt'
    # source = os.path.join(core_lib.path,file)
    # dest = upload_lib.path
    shutil.copy(os.path.join(core_lib.path,file), os.path.join(upload_lib.path,file))
# def get_bu_asset_library(context):

#     for lib in context.preferences.filepaths.asset_libraries:
#         if lib.name == "BU_AssetLibrary_Core":
#             return lib

#     return None

def get_unpacked_names(fileName):
    catsfile = "blender_assets.cats.zip"
    if fileName  == catsfile:
        checkfile = str(fileName.replace(".zip",".txt")) 
    else:
        checkfile = str(fileName.replace(".zip",".blend")) 
    return checkfile

def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def is_server_asset_updated(asset_id,blend_file_path,):
    dt = modification_date(blend_file_path)
    sdt = parser.isoparse(asset_id)
    local_asset = dt.strftime('%Y-%m-%d %H:%M:%S')
    server_asset = sdt.strftime('%Y-%m-%d %H:%M:%S')
    if server_asset > local_asset:
        return True
    else:
        return False



def check_excist (fileName, fileSavepath):
    checkfile = get_unpacked_names(fileName)
    file = fileSavepath + os.sep + checkfile 
    exists = os.path.exists(file)

    return exists

def check_for_new_assets(context):
    context.window_manager.bu_props.new_assets = 0
    context.window_manager.bu_props.updated_asset = 0
    bu_asset_lib = get_core_asset_library(context)
    if bu_asset_lib is None:
        return
    if not Path(bu_asset_lib.path).exists():
        return

    assets = get_asset_list().items()
    assets_m_time = get_asset_list_m_time()
    global assets_to_download
    
    for asset_id,asset_name in assets:
        core_lib = get_core_asset_library(context)
        folder_name = asset_name.removesuffix('.zip')
        blend_file = get_unpacked_names(asset_name)
        asset_path = os.path.join(core_lib.path,folder_name)
        catfile = 'blender_assets.cats.txt'
        blend_file_path = os.path.join(asset_path,blend_file)
        # if blend_file != catfile:
        #     dt = modification_date(blend_file_path)
        #     sdt = parser.isoparse(assets_m_time[asset_id])

            # print(f'server asset {asset_name} m time = date = {sdt.date()} and time = {sdt.time()}')
            # print(f'{blend_file} modified-time =  date = {lfd} and time = {lft}')
        if check_excist(asset_name,core_lib.path):
            if blend_file != catfile:
                if not os.path.exists(asset_path):
                    os.mkdir(asset_path)
                    shutil.copy(os.path.join(core_lib.path,blend_file),os.path.join(asset_path,blend_file))
                else:
                    shutil.copy(os.path.join(core_lib.path,blend_file),os.path.join(asset_path,blend_file))
            
        
            #print(f" {asset_name} new item")
        if blend_file != catfile:
            if not check_excist(asset_name,asset_path):
                context.window_manager.bu_props.new_assets += 1
                assets_to_download[asset_id]=asset_name
                print(f" {asset_name} new item")
            else:
                if is_server_asset_updated(assets_m_time[asset_id],blend_file_path):
                    context.window_manager.bu_props.updated_assets += 1
                    print(f" {asset_name} item has update")
                    assets_to_download[asset_id]=asset_name
                
        else:
            if not check_excist('blender_assets.cats.zip',core_lib.path):
                context.window_manager.bu_props.new_assets += 1
                assets_to_download[asset_id]=asset_name
                print(f" {asset_name} new item")
            else:
                if is_server_asset_updated(assets_m_time[asset_id],os.path.join(core_lib.path,blend_file)):
                    context.window_manager.bu_props.updated_assets += 1
                    assets_to_download[asset_id]=asset_name
                    print(f" {asset_name} item has update")
        if check_excist(blend_file,core_lib.path) and check_excist(blend_file,asset_path):
            os.remove(os.path.join(core_lib.path,blend_file))
        

        



class WM_OT_downloadLibrary(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadlibrary"
    bl_label = "Download the current library from url after pressing ok"

    def execute(self, context):
        DownloadFile(DriveFileId ='19ODT1rdTbfZjpGLXs_fj21C9FOIj_p-N', fileName='blender_assets.cats.txt')
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)






@persistent
def hand_check_new_assets(dummy):
    threading.Thread(target=check_for_new_assets, args=(bpy.context,)).start()
    
class WM_OT_check_lib_update(Operator):
    """CHECK IF THERE ARE UPDATES FOR OUR LIBRARY"""
    bl_idname = "wm.checklibupdate"
    bl_label = "Check of there are new assets available for download"

    def execute(self,context):
        if "BU_AssetLibrary_Core" in context.preferences.filepaths.asset_libraries:
            context.space_data.params.asset_library_ref = "BU_AssetLibrary_Core"
        hand_check_new_assets(self)
        return {'FINISHED'}
    
classes = (
    WM_OT_downloadAll,
    WM_OT_downloadLibrary,
    WM_OT_check_lib_update,
    )





def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(hand_check_new_assets)
    bpy.app.handlers.save_post.append(hand_check_new_assets)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    bpy.app.handlers.load_post.remove(hand_check_new_assets)
    bpy.app.handlers.save_post.remove(hand_check_new_assets)
     