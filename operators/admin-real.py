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
from bpy.types import Context, PropertyGroup,Operator,UIList
from .. import progress
from ..utils import addon_info
from .. import icons
from . import library_upload
from ..ui import statusbar
from bpy.props import BoolProperty,IntProperty,EnumProperty,StringProperty,PointerProperty,CollectionProperty



from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

log = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

KEY_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"

assets_to_download={}
folder_list ={}
folder_index = IntProperty()
selected_assets = []

class BUPrefLib(bpy.types.AddonPreferences):
    bl_idname = __package__

    admin_lib_path: StringProperty(
        name = "AssetLibrary directory",
        description = "Choose a directory to setup the Asset Library",
        maxlen = 1024,
        subtype = 'DIR_PATH'
    )

def Gservice():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)
    # Build the service object.
    service = build('drive', 'v3', credentials=credentials)
    return service
    # Call the Drive v3 API

def get_asset_list(folder_id):
    asset_list ={}
    try:
        authService = Gservice()
        # Build the service object.

    # Call the Drive v3 API
        page_token = None
        
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
                    print(f'found asset: {item["name"]}')
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
                    print(item)      

            request = authService.files().list_next(request, result)
        print(len(asset_list_m_time))
        return asset_list_m_time
    except HttpError as error:
        print(f'An error occurred: {error}')


def get_folder_list():
    
    try:
        authService = Gservice()
        # Build the service object.

    # Call the Drive v3 API
        page_token = None
        folder_id = '1MGjz9fKcP7tfpmZdCXS5DSezeLXoPpx8'
        request = authService.files().list(                
                q="'"+ folder_id + "' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='nextPageToken, ''files(id, name,trashed)',
                pageToken=page_token)
      
        while request is not None:
            result = request.execute()
            items = result.get('files', [])
            if not items:
                print('ERROR: No files found.')
            for item in items:
                if not item['id'] == '1MGjz9fKcP7tfpmZdCXS5DSezeLXoPpx8' and item['trashed'] == False:
                    folder_list[item['id']] = item['name']

            request = authService.files().list_next(request, result)
        return folder_list
    
    except HttpError as error:
        print(f'An error occurred: {error}')

def get_user_assets(user_folder_id):
    asset_list ={}
    try:
        authService = Gservice()
        # Build the service object.

    # Call the Drive v3 API
        page_token = None
        folder_id = user_folder_id
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
                if not item['id'] == folder_id  :
                    asset_list[item['id']] = item['name']

            request = authService.files().list_next(request, result)
        return asset_list
    
    except HttpError as error:
        print(f'An error occurred: {error}')



def get_admin_library():
    context = bpy.context
    addon_name = addon_info.get_addon_name()
    dir_path = addon_name.preferences.lib_path
    if dir_path == '':
        print('no path set')
        return
    else:
        if "BU_Admin_Library" in context.preferences.filepaths.asset_libraries:
            lib = context.preferences.filepaths.asset_libraries["BU_Admin_Library"]  
            if not Path(lib.path).exists():
                add_admin_library_path()
                lib = context.preferences.filepaths.asset_libraries["BU_Admin_Library"]  
                return lib
            return lib

        else:
            if "BU_AssetLibrary_Core" in context.preferences.filepaths.asset_libraries:
                add_admin_library_path()
                if "BU_Admin_Library" in context.preferences.filepaths.asset_libraries: 
                    lib = context.preferences.filepaths.asset_libraries["BU_Admin_Library"]   
                return lib


def add_admin_library_path():
    context = bpy.context
    addon_name = addon_info.get_addon_name()
    dir_path = addon_name.preferences.lib_path
    admin_lib_name = 'BU_Admin_Library'
    admin_dir_path =os.path.join(dir_path,admin_lib_name)  
    if dir_path == '' and "BU_AssetLibrary_Core" not in context.preferences.filepaths.asset_libraries:
        return
        
    else:
        # user_dir_path =bu_lib + lib_username
        if not os.path.isdir(str(admin_dir_path)): # checks whether the directory exists
            os.mkdir(str(admin_dir_path)) # if it does not yet exist, makes it
        if os.path.isdir(str(admin_dir_path)):
            if dir_path !='':
                print(admin_dir_path)
                bpy.ops.preferences.asset_library_add(directory=admin_dir_path)
                admin_lib =bpy.context.preferences.filepaths.asset_libraries["BU_Admin_Library"]
                # bpy.ops.wm.save_userpref()
                return admin_lib


class UserFolderProps(bpy.types.PropertyGroup):
    id: StringProperty()
    name: StringProperty()

class get_user_folder_list(bpy.types.Operator):
    bl_idname = "bu.get_user_folder_list"
    bl_label = "Get User Folder List"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        if is_pref_path_set(self,context)==False:
            return False
        user_folder = context.scene.user_folders
        if len(user_folder) ==0:
            return True

    def execute(self, context):
        user_folder_dict = get_folder_list()
        context.scene.user_folders.clear()
        admin_lib =get_admin_library()
        if admin_lib is not None:
            for folder_id,folder_name in user_folder_dict.items():  
                if folder_name not in context.scene.user_folders:
                    user_folder_add = context.scene.user_folders.add()
                    user_folder_add.id = folder_id
                    user_folder_add.name = folder_name
                    print(f'folder id: {user_folder_add.id}, folder name: {user_folder_add.name}')
        return {'FINISHED'}
def draw_admin_assetbrowser_menu(self, context):
    current_library_name = context.area.spaces.active.params.asset_library_ref
    if current_library_name == "BU_Admin_Library":
        i = icons.get_icons()
        self.layout.operator('wm.save_files', icon_value=i["bakeduniverse"].icon_id, text='Add to Core Library')
        statusbar.ui_titlebar_upload(self,context)

def is_pref_path_set(self,context):
    assetlibs = context.preferences.filepaths.asset_libraries
    admin_lib = get_admin_library()
    if admin_lib:
        if "BU_Admin_Library" not in assetlibs or admin_lib is None:
            self.poll_message_set("Please add a library path in the addon preferences!")
            return False
        else:
            return True

class BU_OT_Accept_To_Core_Library(bpy.types.Operator):
    bl_idname = "bu.accept_to_core_library"
    bl_label = "Accept To Core Library"
    bl_options = {'REGISTER'}
    item_index = IntProperty()
    
    @classmethod
    def poll(cls,context):
        if len(context.selected_asset_files)>0:
            return True
        cls.poll_message_set('Select assets below!')
        return False
    
    def execute(self, context):
        for idx,asset in enumerate(context.selected_asset_files):
            print(f'idx: {idx}, asset: {asset}')
            library_upload.copy_and_zip_catfile(asset)
        admin_lib =get_admin_library()
        return {'FINISHED'}

class BU_OT_test_operator(bpy.types.Operator):
    bl_idname = "bu.test_operator"
    bl_label = "Test Operator"
    bl_options = {'REGISTER'}
    item_index = IntProperty()
    def execute(self, context):
        file_to_remove ='1-5Qicag3wuyhIKAW7ZlraKo4Ez_aEnvm'
        lib = get_admin_library()
        print(lib.__dir__())
        return {'FINISHED'} 
    
class BU_OT_Delete_user_assets(bpy.types.Operator):
    bl_idname = "bu.delete_user_assets"
    bl_label = "Delete_user_assets"
    bl_options = {'REGISTER'}
    item_index:IntProperty()
    @classmethod
    def poll(self, context):
        if is_pref_path_set(self,context)==False:
            return False
        user_folder = context.scene.user_folders
        if len(user_folder) >0:
            return True
    def delete_from_server(self,context,file_id):
        service = Gservice()
        body = {'trashed': True}
        service.files().update(fileId=file_id, body=body).execute()
        service.files().emptyTrash().execute()
    def execute(self, context):
        user_folder = context.scene.user_folders[self.item_index]
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        print(user_folder.id)
        if dir_path !='':
            admin_lib = "BU_Admin_Library"
            admin_full_path =os.path.join(dir_path,admin_lib) 
            all_files = os.listdir(admin_full_path)
            catfile = 'blender_assets.cats.txt'
            
            #Remove server files
            user_server_assets = get_user_assets(user_folder.id).items()
            for file_id,file_name in user_server_assets:
                self.delete_from_server(context,file_id)
            file_id = user_folder.id
            self.delete_from_server(context,file_id)

            #Remove local files
            for file in all_files:
                if file == catfile :
                    cat_path = f'{admin_full_path}{os.sep}{catfile}'
                    os.remove(cat_path)
                elif file == catfile+'~':
                    cat_path = f'{admin_full_path}{os.sep}{catfile}~'
                    os.remove(cat_path)
                else:
                    file_folder_path = f'{admin_full_path}{os.sep}{file}'
                    shutil.rmtree(file_folder_path)
            context.scene.user_folders.remove(self.item_index)
        return {'FINISHED'} 
    
class BU_OT_Clear_User_Folder_List(bpy.types.Operator):
    bl_idname = "bu.clear_user_folder_list"
    bl_label = "Clear User Folder List"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        if is_pref_path_set(self,context)==False:
            return False
        user_folder = context.scene.user_folders
        if len(user_folder) >0:
            return True

    def execute(self, context):
        user_folder = context.scene.user_folders
        user_folder.clear()
    
        return {'FINISHED'} 
    
class BU_OT_download_user_assets(bpy.types.Operator):
    bl_idname = "bu.download_user_assets"
    bl_label = "Download User assets"
    bl_options = {'REGISTER'}
    
    item_index:IntProperty(options={'HIDDEN'})
    prog = 0
    prog_text = None
    num_downloaded = 0
    _timer = None
    th = None
    prog_downloaded_text = None


    @classmethod
    def poll(self, context):
        assetlibs = bpy.context.preferences.filepaths.asset_libraries
        admin_lib = get_admin_library()
        if "BU_Admin_Library" not in assetlibs or admin_lib is None:
            self.poll_message_set("Please add a library path in the addon preferences!")
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
        target_lib = get_admin_library()
        user_folders = context.scene.user_folders
        folder_name = user_folders[self.item_index].name
        folder_dir = os.path.join(target_lib.path,folder_name)
        # if not os.path.isdir(str(folder_dir)): # checks whether the directory exists
            # os.mkdir(str(folder_dir)) # if it does not yet exist, makes it
        
        id, name = list(folder_list.items())[self.item_index]
        global assets_to_download
        assets_to_download= get_asset_list(id).copy()
        assets = assets_to_download.items()
        
        self.th = threading.Thread(target=threadedDownload, args=(self,context,assets,target_lib))

        self.th.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)        
        return {"RUNNING_MODAL"}

def DownloadFile(FileId,fileName,target_lib):
    try:
        authService = Gservice()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print({"INFO"}, f"{fileName} has been dowloaded")
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
                        os.remove(fname)
                    else:
                        os.makedirs(foldername)
                        shutil.unpack_archive(fname, foldername, 'zip')
                        os.remove(fname)
                else:
                    shutil.unpack_archive(fname, target_lib.path, 'zip')
  
                    os.remove(fname)
                
    except HttpError as error:
        print(F'An error occurred: {error}')

    return fileName
def threadedDownload(self,context,assets,target_lib):
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
                        # if result == 'blender_assets.cats.zip':
                        #     for window in bpy.context.window_manager.windows:
                        #         screen = window.screen
                        #         for area in screen.areas:
                        #             if area.type == 'FILE_BROWSER':
                        #                 with bpy.context.temp_override(window=window, area=area):
                        #                     if bpy.context.space_data.params.asset_library_ref == 'BU_Admin_Library':
                        #                         bpy.ops.asset.catalog_new()
                        #                         bpy.ops.asset.catalogs_save()
                        #                         bpy.ops.asset.catalog_undo()
                        #                         bpy.ops.asset.catalogs_save()
                
                        # self.report( {"INFO"}, f"{result}{prog_word}")
                        
        if all(t._state == 'FINISHED' for t in threads):
            context.window_manager.bu_props.new_assets = 0
            context.window_manager.bu_props.updated_asset = 0
            break
        sleep(0.5)

class BU_OT_Enable_Admin_tools(bpy.types.Operator):
    bl_idname = "bu.enable_admin_tools"
    bl_label = "Enable Admin Tools"
    bl_options = {'REGISTER'}
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        add_admin_library_path()
        return {'FINISHED'}

class ASSETBROWSER_UL_Folder_list(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        folder = item
        # Make sure your code supports all 3 layout types if 
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            # layout.label(text='tag.tag_name', icon_value=icon)
            layout.prop(folder, "name", text='', emboss=False, icon_value=icon) 
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.prop(folder, "name", text='') 

def asset_statusbar (self,context,row):
    
    props = context.window_manager.bu_props
    if props.progress_total:
        row.label(text = f' Amount of assets to download: {round(props.progress_total) }')
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)
    else:
        if props.new_assets > 1:
            row.label(text = f' There are {props.new_assets}  new assets available for download!!' )
        elif props.new_assets == 1:
            row.label(text = f' There is {props.new_assets} new asset available for download!!' )
        elif props.new_assets == 0:
            row.label(text = f'' )
        elif props.updated_assets >=1:
            row.label(text = f' There are {props.updated_assets} that have updates!!' )
        elif props.updated_assets ==1:
            row.label(text = f'{props.updated_assets} has an update!!')



class AB_AdminPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_AB_ADMIN_PANEL"
    bl_label = 'Asset Browser Admin Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"

    def draw(self,context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        layout = self.layout
        row = layout.row()
        if  dir_path !='':
            if 'BU_Admin_Library' in bpy.context.preferences.filepaths.asset_libraries:
                row.operator("bu.get_user_folder_list", text = "Get User Folder List")
                row.operator("bu.clear_user_folder_list", text = "Clear User Folder List")
                row = layout.row()
                user_folders = context.scene.user_folders
                asset_statusbar(self,context,row)
                for idx,folder in enumerate(user_folders):
                    row = layout.row()
                    box = row.box()
                    split = box.split(factor=0.25)
                    row=split.row()
                    row.label(text=folder.name,icon='FILE_FOLDER')
                    row=split.row()
                    
                    row=split.row()
                    if len(user_folders) > 0:
                        row.operator('bu.download_user_assets', text = "Download User Assets").item_index= idx
                        row.operator('bu.delete_user_assets', text = "Delete User Assets").item_index= idx
                        # row.operator('bu.test_operator', text = "Test Operator")
            else:
                row.operator('bu.enable_admin_tools', text = "Enable Admin Tools")
                    

        else:
            row.label(text = 'Please set a library path in prefferences.', icon = 'ERROR')



        


classes = (
    BU_OT_Enable_Admin_tools,
    BU_OT_Accept_To_Core_Library,
    BU_OT_Delete_user_assets,
    BU_OT_Clear_User_Folder_List,
    BU_OT_test_operator,
    BU_OT_download_user_assets,
    ASSETBROWSER_UL_Folder_list,
    UserFolderProps,
    get_user_folder_list,
    AB_AdminPanel,
   
    
   
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
       
    bpy.types.Scene.user_folders = bpy.props.CollectionProperty(type=UserFolderProps)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(draw_admin_assetbrowser_menu)

    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.user_folders
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(draw_admin_assetbrowser_menu)
