from __future__ import print_function
import bpy
import io
import os
from bpy.types import Operator
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
KEY_FILE_LOCATION = 'bakeduniverseassetlibrary-5b6b936e6c00.json'


def Gservice():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)
    # Build the service object.
    service = build('drive', 'v3', credentials=credentials)
    return service
    # Call the Drive v3 API


def ReadandDownloadAllfiles():
    
    try:
        authService = Gservice()
        # Build the service object.

    # Call the Drive v3 API
        results = authService.files().list( # q="'1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ' in parents'",
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        print(results)
        if not items:
            print('No files found.')
        else:
            print('Files:')
        for item in items:
            if item['id'] == '1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ':
                print("skip folder id")
            else:
                DownloadFile(item['id'],item['name'])
                print(u'{0} ({1})'.format(item['name'], item['id']))
        return items
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
        
def DownloadFile(DriveFileId,fileName):
    
    authService = Gservice()
    try:
        fileSavepath = BULibPath()
        file_id = DriveFileId
                # pylint: disable=maybe-no-member
        request = authService.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')

        file.seek(0)
        with open(os.path.join(fileSavepath, fileName), 'wb') as f:
            f.write(file.read())
            f.close()
    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None


 #  "19ODT1rdTbfZjpGLXs_fj21C9FOIj_p-N" # File ID of Blender_assets_cat
class WM_OT_downloadAll(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadall"
    bl_label = "Download the current library from url after pressing ok"
    def execute(self, context):
        # ReadGfiles()
        ReadandDownloadAllfiles()

        return {'FINISHED'}
    
    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)
    
class WM_OT_downloadLibrary(Operator):
    """OPENS THE CONFIRM DOWNLOAD DIALOG BOX"""
    bl_idname = "wm.downloadlibrary"
    bl_label = "Download the current library from url after pressing ok"
    def execute(self, context):
        # ReadGfiles()
        DownloadFile(DriveFileId ='19ODT1rdTbfZjpGLXs_fj21C9FOIj_p-N', fileName='blender_assets.cats.txt')
        # dir_path = bpy.context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.lib_path
        # lib_name = 'BU_AssetLibrary_Core'
        # if dir_path != "":
        #     bpy.ops.preferences.asset_library_add(directory =dir_path, check_existing = True)
        #     new_library = bpy.context.preferences.filepaths.asset_libraries[-1]
        #     new_library.name = lib_name
            
        return {'FINISHED'}
    
    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)
     