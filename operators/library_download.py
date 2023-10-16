from __future__ import print_function
import bpy
import logging
import io
import os
import datetime

import shutil
import threading
from bpy.app.handlers import persistent
from dateutil import parser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from bpy.types import Operator
from .. import progress
from ..utils import addon_info
from ..utils import catfile_handler
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
        addon_prefs = addon_info.get_addon_name().preferences
        folder_id = addon_prefs.download_folder_id_placeholders
        #  request = authService.files().list( )
        request = authService.files().list( # q="'1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ' in parents'", Querries do not seem to work properly
            pageSize= 20, fields="nextPageToken, files(id,name,parents,trashed)")
              
       
        while request is not None:
            result = request.execute()
            items = result.get('files', [])
            if not items:
                print('ERROR: No files found.')
            for item in items:
                parent = item.get('parents')
                if parent is not None and parent[0] == folder_id and item['trashed'] == False:
                    
                # if item['parents'] == folder_id:
                    asset_list[item['id']] = item['name']
                    

            request = authService.files().list_next(request, result)

        return asset_list
            # request = authService.files().list_next(request, result)
                
    
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
        #  request = authService.files().list( )
        request = authService.files().list( # q="'1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ' in parents'",
            pageSize= 20, fields="nextPageToken, files(id,modifiedTime,parents,trashed)")
              
       
        while request is not None:
            result = request.execute()
            items = result.get('files', [])
            if not items:
                print('ERROR: No files found.')
            for item in items:
                parent = item.get('parents')
                if parent is not None and parent[0] == folder_id and item['trashed'] == False:
                    
                # if item['parents'] == folder_id:
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

def DownloadFile(FileId,fileName,target_lib):
    # libpaths = BULibPath()
    try:
        authService = Gservice()

                # pylint: disable=maybe-no-member
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print({"INFO"}, f"{fileName} has been dowloaded With file_id: {FileId}")
        file.seek(0)

        with open(os.path.join(target_lib.path, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            if ".zip" in fileName:
                fname = target_lib.path + os.sep + fileName
                
        
                if not fileName == "blender_assets.cats.zip":
                    foldername = str.removesuffix(fname,'.zip')
                    if os.path.exists(foldername):
                        shutil.unpack_archive(fname, foldername, 'zip')
                        # os.remove(fname)
                    else:
                        os.makedirs(foldername)
                        shutil.unpack_archive(fname, foldername, 'zip')
                        # os.remove(fname)
                else:
                    shutil.unpack_archive(fname, target_lib.path, 'zip')
                    # os.remove(fname)
                    

           
                    
    except HttpError as error:
        print(F'An error occurred: {error}')
    
    # file = None
    return fileName


def threadedDownload(self,context,assets,target_lib,is_lib):

    
    executor = ThreadPoolExecutor(max_workers=20)
    threads = []
    count = 0
    for asset_id,asset_name in assets:
        # blend_file = get_unpacked_names(asset_name)
        t=executor.submit(DownloadFile, asset_id,asset_name,target_lib)
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
            break    
        sleep(0.5)
    copy_cats_file(context)
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
        addon_prefs = addon_info.get_addon_name().preferences
        dir_path = addon_prefs.lib_path
        if dir_path == '':
            self.poll_message_set('Please add a file path in the addon preferences')
            return False
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
        target_lib = addon_info.get_core_asset_library()
        global assets_to_download
        assets = assets_to_download.items()
        # print(assets)
        # if error:
        #     self.report({'ERROR'}, error)
        #     return {'CANCELLED'}

        # gives to many values to unpack error needs checking
        is_lib = True
        self.th = threading.Thread(target=threadedDownload, args=(self,context,assets,target_lib,is_lib))

        self.th.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)        
        return {"RUNNING_MODAL"}
            
        
def copy_cats_file(context):
    upload_lib = addon_info.get_upload_asset_library()
    core_lib = addon_info.get_core_asset_library()    
    file = 'blender_assets.cats.txt'
    if check_excist(file,core_lib.path):
        shutil.copy(os.path.join(core_lib.path,file), os.path.join(upload_lib,file))

def get_unpacked_names(fileName):
    catsfile = "blender_assets.cats.zip"
    if fileName == catsfile:
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
    bu_asset_lib = addon_info.get_core_asset_library()
    if bu_asset_lib is None:
        return
    if not Path(bu_asset_lib.path).exists():
        return

    assets = get_asset_list().items()
    assets_m_time = get_asset_list_m_time()
    global assets_to_download
    
    for asset_id,asset_name in assets:
        core_lib = addon_info.get_core_asset_library()
        folder_name = asset_name.removesuffix('.zip')
        catfile = 'blender_assets.cats.txt'
        blend_file = get_unpacked_names(asset_name)
        if blend_file != catfile:
            asset_path = os.path.join(core_lib.path,folder_name)
            if not os.path.isdir(asset_path):
                os.mkdir(asset_path)
            blend_file_path = os.path.join(asset_path,blend_file)
        addon_prefs = addon_info.get_addon_name().preferences
        dir_path = addon_prefs.lib_path
        
        # check if asset folders are in root folder(lib_path). if so then copy them to core lib folder
        assets_in_root_dir = os.path.join(dir_path,folder_name)
        if check_excist(asset_name,assets_in_root_dir):
            if blend_file != catfile:
                shutil.copy(os.path.join(assets_in_root_dir,blend_file),os.path.join(asset_path,blend_file))
                shutil.rmtree(assets_in_root_dir)
        if os.path.exists(os.path.join(dir_path,catfile)):
            shutil.copy(os.path.join(dir_path,catfile),os.path.join(core_lib.path,catfile))
            os.remove(os.path.join(dir_path,catfile))

        # Check if asset folder exists in core lib folder       
        if check_excist(asset_name,core_lib.path):
            if blend_file != catfile:
                if not os.path.exists(asset_path):
                    os.mkdir(asset_path)
                    shutil.copy(os.path.join(core_lib.path,blend_file),os.path.join(asset_path,blend_file))
                else:
                    shutil.copy(os.path.join(core_lib.path,blend_file),os.path.join(asset_path,blend_file))
            
        
            #print(f" {asset_name} new item")
        if blend_file != catfile:
            if check_excist(asset_name,asset_path):
                if is_server_asset_updated(assets_m_time[asset_id],blend_file_path):
                    context.window_manager.bu_props.updated_assets += 1
                    print(f" {asset_name} item has update")
                    assets_to_download[asset_id]=asset_name

            else:
                context.window_manager.bu_props.new_assets += 1
                assets_to_download[asset_id]=asset_name
                print(f" {asset_name} new item")

                
        else:
            context.window_manager.bu_props.new_assets += 1
            assets_to_download[asset_id]=asset_name
            print(f" {asset_name} item has update")
            # check = check_excist('blender_assets.cats.zip',core_lib.path)
            print('catalog file asset name = ' , asset_name)
            
            # if check:
            #     if is_server_asset_updated(assets_m_time[asset_id],os.path.join(core_lib.path,blend_file)):
            #         context.window_manager.bu_props.updated_assets += 1
            #         assets_to_download[asset_id]=asset_name
            #         print(f" {asset_name} item has update")
            # else:
            #     context.window_manager.bu_props.new_assets += 1
            #     assets_to_download[asset_id]=asset_name
            #     print(f" {asset_name} new item")
               
        if check_excist(blend_file,core_lib.path) and check_excist(blend_file,dir_path):
            os.remove(os.path.join(core_lib.path,blend_file))
        

        




class WM_OT_downloadLibrary(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadlibrary"
    bl_label = "Download the current library from url after pressing ok"

    def execute(self, context):
        target_lib = addon_info.get_core_asset_library()
        DownloadFile(DriveFileId ='19ODT1rdTbfZjpGLXs_fj21C9FOIj_p-N', fileName='blender_assets.cats.txt',target_lib=target_lib)
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
   
    @classmethod
    def poll (self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        dir_path = addon_prefs.lib_path
        if dir_path == '':
            self.poll_message_set('Please add a file path in the addon preferences!')
            return False
        return True

    def execute(self,context):
        context.scene.status_text = "Checking for new assets..."
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
     