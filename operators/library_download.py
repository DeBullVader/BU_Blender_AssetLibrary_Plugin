from __future__ import print_function
import bpy
import logging
import io
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from tempfile import NamedTemporaryFile
from bpy.types import Operator
from .. import progress

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


log = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']
KEY_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + "\\bakeduniverseassetlibrary-5b6b936e6c00.json"
# directory = os.path.realpath(__package__)

print("location of the JSON file = " + KEY_FILE_LOCATION)

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
        
        request = authService.files().list( # q="'1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ' in parents'",
            pageSize=10, fields="nextPageToken, files(id, name)")
      
        while request is not None:
            result = request.execute()
            items = result.get('files', [])
            if not items:
                print('No files found.')
            else:
                print('Files have been found')
            for item in items:
                if not item['id'] == '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ':
                    asset_list[item['id']] = item['name']

            request = authService.files().list_next(request, result)
        return asset_list
    
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
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
    for lib in assetlibs:
        if lib.name == "BU_AssetLibrary_Core":
            return lib.path

def DownloadFile(FileId,fileName):
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

        fileSavepath = BULibPath()
        with open(os.path.join(fileSavepath, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
            if ".zip" in fileName:
                fname =fileSavepath + "\\" + fileName
                shutil.unpack_archive(fname, fileSavepath, 'zip')
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
        if bpy.app.version_string < "3.4.0":
            
            return False
        return context.window_manager.bu_props.progress_total == 0

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
        
       
        def threadedDownload(self, assets):
            # assets_to_download = {}
            # for asset in assets:
            #     if not asset['id'] == '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ':
            #         assets_to_download[asset['id']] = asset['name']
            progress.init(context, len(assets), word = "Downloading")
            executor = ThreadPoolExecutor(max_workers=20)
            threads = []

            for asset_id,asset_name in assets:
                t=executor.submit(DownloadFile, asset_id,asset_name)
                threads.append(t)

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
                                self.num_downloaded += 1
                                prog_word = f"{result}  has been Downloaded"
                                self.prog_text = f"{result}{prog_word} "
                                context.window_manager.bu_props.progress_downloaded_text = f"{result}{prog_word} "
                                
                                # self.report( {"INFO"}, f"{result}{prog_word}")
                                
                if all(t._state == 'FINISHED' for t in threads):

                    break
                sleep(0.5)
        
        assets = get_asset_list().items()
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
            
        

  





class WM_OT_downloadLibrary(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadlibrary"
    bl_label = "Download the current library from url after pressing ok"

    def execute(self, context):
        DownloadFile(DriveFileId ='19ODT1rdTbfZjpGLXs_fj21C9FOIj_p-N', fileName='blender_assets.cats.txt')
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

classes = (
    WM_OT_downloadAll,
    WM_OT_downloadLibrary,
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print('lib_download REGISTERED')

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
     