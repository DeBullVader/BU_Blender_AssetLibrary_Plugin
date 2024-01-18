import bpy
import blf
import os
import shutil
import zipfile
import textwrap
import datetime
import json
from bpy.types import Context
from .file_managment import AssetSync
from .file_upload_managment import AssetUploadSync
from . import task_manager
from .download_library_files import BU_OT_Download_Original_Library_Asset
from ..utils import addon_info,progress,catfile_handler
from ..ui import statusbar
from . import file_upload_managment
from ..utils import exceptions,sync_manager
from ..utils.addon_logger import addon_logger
from .handle_asset_updates import SyncPremiumPreviews,UpdatePremiumAssets
from ..utils import version_handler

class BU_OT_Update_Assets(bpy.types.Operator):
    """Update original assets that are not automatically updated"""
    bl_idname = "bu.update_assets"
    bl_label = "Update Premium Assets"
    bl_description = "Update Premium Assets"
    bl_options = {"REGISTER"}

    _timer = None
    requested_cancel = False
    current_library_name = ''

    @classmethod
    def poll(cls, context):
        addon_prefs= addon_info.get_addon_name().preferences
        isPremium = addon_info.is_lib_premium()
        current_library_name = version_handler.get_asset_library_reference(context)
        payed = addon_prefs.payed
        assets_to_update = context.scene.premium_assets_to_update if isPremium else context.scene.assets_to_update
        if assets_to_update is not None:
            if not any( asset.selected for asset in assets_to_update):
                cls.poll_message_set ('Please select at least one asset to update')
                return False
        if payed == False and current_library_name ==addon_info.get_lib_name(True,addon_prefs.debug_mode):
            cls.poll_message_set('Please input a valid BUK premium license key')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            if not sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                cls.poll_message_set('Another sync operation is already running. Please wait or cancel it.')
                return False
        return True

    def execute(self, context):
        sync_manager.SyncManager.start_sync(BU_OT_Update_Assets.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        try:
            self.current_library_name = version_handler.get_asset_library_reference(context)
            self.update_premium_handler = UpdatePremiumAssets.get_instance()
            if self.update_premium_handler.current_state is None and not self.requested_cancel:
                addon_info.set_drive_ids(context)
                bpy.ops.wm.initialize_task_manager()
                self.update_premium_handler.reset()
                self.update_premium_handler.target_lib = addon_info.get_target_lib(context)
                self.update_premium_handler.current_state ='perform_update' 
            else:
                print("cancelled")
                self.update_premium_handler.requested_cancel = True
                self.requested_cancel = True
                self.update_premium_handler.reset()

        except Exception as e:
            print(f"An error occurred: {e}")
            addon_logger.error(e)
            self.shutdown(context)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                self.update_premium_handler.perform_update(context)
            except Exception as error_message:
                print(f"An error occurred: {error_message}")
                addon_logger.error(error_message)
                self.shutdown(context)
            
            if self.requested_cancel or self.update_premium_handler.is_done():
                self.shutdown(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_Update_Assets.bl_idname)
        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context) 
        bpy.ops.asset.library_refresh()
        
        self.requested_cancel = False
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
 

def taskmanager_cleanup(context,task_manager):
    if task_manager.task_manager_instance:
        task_manager.task_manager_instance.update_task_status('Sync complete')
        task_manager.task_manager_instance.set_done(True)
        task_manager.task_manager_instance.shutdown()
        task_manager.task_manager_instance = None
        

class BU_OT_SyncPremiumAssets(bpy.types.Operator):
    """Sync premium assets from the server"""
    bl_idname = "bu.sync_premium_assets"
    bl_label = "Sync Premium Assets previews"
    bl_description = "Syncs premium preview assets from the server"
    bl_options = {"REGISTER"}
    
    _timer = None
    requested_cancel = False
    # sync_preview_handler= None
    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_name().preferences
        
        if addon_prefs.lib_path =='':
            cls.poll_message_set('Please input a valid library path. Go to Asset Browser settings in the BU side panel')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            # Enable the operator if it's the one currently running the sync
            if sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                return True
            else:
                cls.poll_message_set('Another sync operation is already running. Please wait or cancel it.')
                return False
        return True



    def execute(self, context):
        sync_manager.SyncManager.start_sync(BU_OT_SyncPremiumAssets.bl_idname)
        
        try:
            self.sync_preview_handler = SyncPremiumPreviews.get_instance()
            if self.sync_preview_handler.current_state is None and not self.sync_preview_handler.requested_cancel:
                addon_info.set_drive_ids(context)
                bpy.ops.wm.initialize_task_manager()
                if len(context.scene.assets_to_update) > 0:
                    bpy.context.view_layer.update()
                    print("clearing assets_to_update...")
                    context.scene.assets_to_update.clear()
                self.sync_preview_handler.reset()
                wm = context.window_manager
                self._timer = wm.event_timer_add(0.5, window=context.window)
                wm.modal_handler_add(self)
                self.sync_preview_handler.target_lib = addon_info.get_target_lib(context)
                self.sync_preview_handler.current_state = 'fetch_assets'

            else:
                print("cancelled")
                self.sync_preview_handler.requested_cancel = True
                self.requested_cancel = True
                
            
        except Exception as e:
            print(f"An error occurred: {e}")
        
  
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            addon_logger.info('Syncing premium previews...')
            self.sync_preview_handler.perform_sync(context)
            
            if self.requested_cancel:
                print('requested cancelled')
                self.sync_preview_handler.set_done(True)
            
            if self.sync_preview_handler.is_done():
                addon_prefs = addon_info.get_addon_prefs()
                if bpy.data.filepath:
                    target_lib =self.sync_preview_handler.target_lib
                    self.refresh(context)
                self.shutdown(context)
      
                return {'FINISHED'}
            
            if self.requested_cancel:
                addon_logger.info('Sync cancelled')
                self.shutdown(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}
    
    def redraw(self, context):
        if context.screen is not None:
            for a in context.screen.areas:
                if a.type == 'FILE_BROWSER':
                    a.tag_redraw()

    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_SyncPremiumAssets.bl_idname)
        bpy.ops.asset.library_refresh()

        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context)
        self.requested_cancel = False

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


    def refresh(self, context):
        addon_prefs = addon_info.get_addon_prefs()
        asset_lib_ref =version_handler.get_asset_library_reference(context)
        lib_name = addon_info.get_lib_name(True,addon_prefs)
        if asset_lib_ref != lib_name:
            version_handler.set_asset_library_reference(context,lib_name)
        bpy.ops.asset.catalog_new()
        bpy.ops.asset.catalogs_save()
        lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
        path = os.path.join(lib.path, 'blender_assets.cats.txt')
        uuid = addon_info.get_catalog_trick_uuid(path)
        if uuid:
            bpy.ops.asset.catalog_delete(catalog_id=uuid)
        # library_name = os.path.basename(lib_path)
        # for window in context.window_manager.windows:
        #     screen = window.screen
        #     for area in screen.areas:
        #         if area.type == 'FILE_BROWSER':
        #             asset_lib_ref = version_handler.get_asset_library_reference(context)
        #             if asset_lib_ref == library_name:
        #                 bpy.ops.asset.catalog_new()
        #                 bpy.ops.asset.catalogs_save()
        #                 lib = bpy.context.preferences.filepaths.asset_libraries[library_name]
        #                 path = os.path.join(lib.path, 'blender_assets.cats.txt')
        #                 uuid = addon_info.get_catalog_trick_uuid(path)
        #                 if uuid:
        #                     bpy.ops.asset.catalog_delete(catalog_id=uuid)


class BU_OT_DownloadCatalogFile(bpy.types.Operator):
    '''Sync the catalog file to current file'''
    bl_idname = "bu.sync_catalog_file" 
    bl_label = "sync catalog file to local file"
    bl_options = {"REGISTER"}

    _timer = None
    requested_cancel = False
    
    @classmethod
    def poll(cls,context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        if not bpy.data.filepath:
            cls.poll_message_set('Please make sure your file is saved')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            # Enable the operator if it's the one currently running the sync
            if not sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                cls.poll_message_set('Another sync operation is already running. Please wait or cancel it.')
                return False
        return True
        
    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                self.download_catalog_file_handler.sync_catalog_file(context)
            except Exception as error_message:
                print(f"An error occurred: {error_message}")
                addon_logger.error(error_message)
                self.requested_cancel = True

            if self.requested_cancel or self.download_catalog_file_handler.is_done():
                self.shutdown(context)
                self.refresh(context)
                self.redraw(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}
    
    def redraw(self, context):
        if context.screen is not None:
            for a in context.screen.areas:
                if a.type == 'FILE_BROWSER':
                    a.tag_redraw()
    
    def execute(self, context):
        sync_manager.SyncManager.start_sync(BU_OT_DownloadCatalogFile.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        try:
            self.download_catalog_file_handler = AssetSync.get_instance()
            if self.download_catalog_file_handler.current_state is None and not self.requested_cancel:
                bpy.ops.wm.initialize_task_manager()
                self.download_catalog_file_handler.reset()
                self.download_catalog_file_handler.current_state = 'fetch_catalog_file_id'
            else:
                print("cancelled")
                self.download_catalog_file_handler.requested_cancel = True
                self.requested_cancel = True
                self.download_catalog_file_handler.reset()
                

        except Exception as e:
            print(f"An error occurred: {e}")
            addon_logger.error(e)
            self.shutdown(context)
                   
        return {'RUNNING_MODAL'}
    
    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_DownloadCatalogFile.bl_idname)
        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context) 
        
        
        self.requested_cancel = False

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
  

    def refresh(self, context):
        catfile = 'blender_assets.cats.txt'
        asset_path = bpy.data.filepath
        asset_dir,file_name = os.path.split(asset_path)
        cat_path = os.path.join(asset_dir,catfile)
        if cat_path:
            for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'FILE_BROWSER':
                        with context.temp_override(window=window, area=area):
                            version_handler.set_asset_library_reference(context,'LOCAL')
                            asset_lib_ref = version_handler.get_asset_library_reference(context)
                            if asset_lib_ref == 'LOCAL':
                                bpy.ops.asset.catalog_new()
                                bpy.ops.asset.catalogs_save()
                                uuid = addon_info.get_catalog_trick_uuid(cat_path)
                                if uuid:
                                    bpy.ops.asset.catalog_delete(catalog_id=uuid)
    

class BU_OT_AssetSyncOperator(bpy.types.Operator):
    '''Syncs preview assets from the server, check for deprecated assets and updates in the library'''
    bl_idname = "bu.sync_assets"
    bl_label = "Sync Assets"
    bl_description = "Syncs preview assets from the server"
    bl_options = {"REGISTER"}
    
    _timer = None
    requested_cancel = False
    
    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_name().preferences
        if addon_prefs.lib_path =='':
            cls.poll_message_set('Please input a valid library path. Go to Asset Browser settings in the BU side panel')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            # Enable the operator if it's the one currently running the sync
            if not sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                cls.poll_message_set('Another sync operation is already running. Please wait or cancel it.')
                return False
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                self.asset_sync_handler.start_tasks(context)
            except Exception as error_message:
                print(f"An error occurred: {error_message}")
                addon_logger.error(error_message)
                self.shutdown(context)

            if self.asset_sync_handler.is_done():
                print('number of assets to update',len(self.asset_sync_handler.assets_to_update))
                if len(self.asset_sync_handler.assets_to_update)>0:
                    self.process_assets_to_update(context)
                self.shutdown(context)
                return {'FINISHED'}
            if self.requested_cancel:
                addon_logger.info('Asset sync cancelled')
                self.shutdown(context)
                return {'FINISHED'}


        return {'PASS_THROUGH'}
    
    def process_assets_to_update(self, context):
        for asset in self.asset_sync_handler.assets_to_update:
            asset_has_update = context.scene.assets_to_update.add()
            asset_has_update.name = asset['name']
            asset_has_update.id = asset['id']
            file_size =asset['size']
            asset_has_update.size = int(file_size)
            asset_has_update.is_placeholder = False 

    def execute(self, context):
        sync_manager.SyncManager.start_sync(BU_OT_AssetSyncOperator.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        try:
            self.asset_sync_handler = AssetSync.get_instance()
            if self.asset_sync_handler.current_state is None and not self.requested_cancel:
                addon_info.set_drive_ids(context)
                bpy.ops.wm.initialize_task_manager()
                if task_manager.task_manager_instance:
                    self.asset_sync_handler.reset()
                    context.scene.assets_to_update.clear()
                    self.asset_sync_handler.target_lib =addon_info.get_target_lib(context)
                    self.asset_sync_handler.current_state = 'fetch_assets'
            else:
                print("cancelled")
                self.asset_sync_handler.requested_cancel = True
                self.requested_cancel = True
                #dont return {'FINISHED'} here as modal returns it


        except Exception as e:
            print(f"An error occurred: {e}")
            addon_logger.error(e)
            self.shutdown(context)
     
        return {'RUNNING_MODAL'}


    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_AssetSyncOperator.bl_idname)
        # addon_info.refresh(self,context,self.asset_sync_handler.target_lib)
        bpy.ops.asset.library_refresh()
        if bpy.data.filepath:
            addon_info.refresh(self,context,self.asset_sync_handler.target_lib)
        self.asset_sync_handler.reset()
        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context)       
        self.requested_cancel = False


    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

#TODO: Move progress to own file?
def draw_upload_callback_px(self, context):

    asset_sync_instance = AssetUploadSync.get_instance()
    status_y = 15
    x = 15
    y = status_y + 30
    text_height = 10
    progress_bar_width = 200
    progress_bar_height = 5
    if version_handler.latest_version(context):
        blf.size(0, 15)
    else:
        blf.size(0, 15 , 72)
    blf.color(0, 1.0, 1.0, 1.0,1.0)
    blf.position(0, x, status_y, 0)
    blf.draw(0, f'{context.scene.status_text}')
    if len(asset_sync_instance.files_to_upload)>0:
        progress.draw_progress_bar(x, y-10 - text_height / 2, progress_bar_width, progress_bar_height, asset_sync_instance.prog / len(asset_sync_instance.files_to_upload))
    for asset_name,status in asset_sync_instance.upload_progress_dict.items():
        if version_handler.latest_version(context):
            blf.size(0, 10)
        else:
            blf.size(0, 10, 72)
        blf.position(0, x, y, 0)
        blf.color(0, 1.0, 1.0, 1.0,1.0)
        blf.draw(0, f"{asset_name} : {status}")
        
        y += text_height + 30

#TODO: Move progress to own file?
class BU_OT_ShowUploadProgress(bpy.types.Operator):
    bl_idname = "bu.show_upload_progress"
    bl_label = "Show upload progress"
    bl_options = {"REGISTER"}

    _timer = None
    _handle = None
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            self.upload_handler = AssetUploadSync.get_instance()
            if(self.upload_handler.is_done() or self.upload_handler is None):
                self.cancel(context)
                return {'FINISHED'}
            # Force a redraw of the entire UI
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    area.tag_redraw()           
        return {'PASS_THROUGH'}  
    
    def execute(self, context):
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):  
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)  # Adjust the interval as needed
        
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_upload_callback_px, args, 'WINDOW', 'POST_PIXEL')
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        if self._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None

class WM_OT_SaveAssetFiles(bpy.types.Operator):
    """Upload assets to the Blender Universe Kit upload folder on the server."""
    bl_idname = "wm.save_files"
    bl_label = "Upload to BUK Server"
    bl_description = "Upload assets to the Blender Universe Kit upload folder on the server."
    bl_options = {"REGISTER"}

    _timer = None
    assets = []
    requested_cancel = False

    @classmethod
    def poll(cls, context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        thumb_path = addon_name.preferences.thumb_upload_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        if not os.path.exists(thumb_path):
            cls.poll_message_set('Please set a thumb upload path in prefferences.')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            if sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                cls.poll_message_set('Already processing uploads please wait')
                return False
        if not catfile_handler.check_current_catalogs_file_exist():
            cls.poll_message_set('Please get the catalog definition from the mark tool or create your own catalog file')
            return False
        return True
         
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                self.upload_asset_handler = AssetUploadSync.get_instance()
                self.upload_asset_handler.sync_assets_to_server(context)
            except Exception as error_message:
                print(f"An error occurred: {error_message}")
                addon_logger.error(error_message)
                self.shutdown(context)

            if self.upload_asset_handler.is_done():
                self.shutdown(context)
                self.redraw(context)
                return {'FINISHED'}
            
            if self.requested_cancel:
                self.shutdown(context)
                self.redraw(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}
    
    def execute(self, context):
        sync_manager.SyncManager.start_sync(WM_OT_SaveAssetFiles.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        addon_prefs = addon_info.get_addon_name().preferences
        thumst_path = addon_prefs.thumb_upload_path

        try:
            self.upload_asset_handler = AssetUploadSync.get_instance()
            if self.upload_asset_handler.current_state is None:
                
                if not os.path.exists(thumst_path):
                    bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Please set a valid thumbnail path in the upload settings!'))
                    print("Please set a valid thumbnail path in the upload settings!")
                    sync_manager.SyncManager.finish_sync(WM_OT_SaveAssetFiles.bl_idname)
                    self.upload_asset_handler.reset()
                    return {'FINISHED'}
                self.assets = context.selected_assets if version_handler.latest_version(context) else context.selected_asset_files
                for asset in self.assets:
                    asset_thumb_path = file_upload_managment.get_asset_thumb_paths(asset)
                    if not asset_thumb_path or not os.path.exists(asset_thumb_path):
                        bpy.ops.error.custom_dialog('INVOKE_DEFAULT',title ='Asset thumbnail not found', error_message=str(f'Please make sure a tumbnail exists with the following name preview_{asset.name}.png or jpg'))
                        addon_logger.info(f'Asset thumbnail not found for {asset.name}, terminated upload sync')
                        sync_manager.SyncManager.finish_sync(WM_OT_SaveAssetFiles.bl_idname)
                        self.upload_asset_handler.reset()
                        return {'FINISHED'}
                try:   
                    files =self.create_and_zip(context)
                except Exception as error_message:
                    full_message =f'Error in Uploading assets: {error_message}'
                    addon_logger.error(full_message)
                    print('Error: ', full_message)
                    bpy.ops.error.custom_dialog('INVOKE_DEFAULT',title='Error in Uploading assets', error_message=str(full_message))
                    self.upload_asset_handler.is_done = True
                    self.upload_asset_handler.reset()
                    self.shutdown(context)
                    return {'FINISHED'}

                if files:
                    bpy.ops.wm.initialize_task_manager()
                    bpy.ops.bu.show_upload_progress('INVOKE_DEFAULT')
                    self.upload_asset_handler.reset()
                    self.upload_asset_handler.files_to_upload = files
                    self.upload_asset_handler.current_state = 'initiate_upload'
                    addon_logger.info('Initiate upload')
            else:
                self.upload_asset_handler.reset()
                self.requested_cancel = True
                print("cancelled")
                self.asset_sync_handler.requested_cancel = True
                self.requested_cancel = True
                self.asset_sync_handler.reset()

        except Exception as error_message:
            addon_logger.error(error_message)
            sync_manager.SyncManager.finish_sync(WM_OT_SaveAssetFiles.bl_idname)
            print('Error: ', error_message)

        return {'RUNNING_MODAL'}
    
    
    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(WM_OT_SaveAssetFiles.bl_idname)
        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context)
        bpy.ops.asset.library_refresh() 
    

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def redraw(self, context):
        if context.screen is not None:
            for a in context.screen.areas:
                if a.type == 'FILE_BROWSER':
                    a.tag_redraw()

    
    def copy_and_zip_catfile(self):
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

    def create_and_zip(self, context):
    
        assets = context.selected_assets if version_handler.latest_version(context) else context.selected_asset_files

        progress.init(context,len(assets),'creating and zipping files...')
        # task_manager.task_manager_instance.update_task_status("creating and zipping files...")
        
        prog = 0
        files_to_upload=[]
        ph_assets_to_remove =[]
        try:
            if assets != None:
                for asset in assets:
                    try:
                        asset_thumb_path = file_upload_managment.get_asset_thumb_paths(asset)
                        if os.path.exists(asset_thumb_path):
                            # zipped_original,zipped_placeholder = create_and_zip_files(self,context,asset,asset_thumb_path)

                            
                            uploadlib = addon_info.get_upload_asset_library()
                            asset_upload_file_path = f"{uploadlib}{os.sep}{asset.name}{os.sep}{asset.name}.blend"
                            placeholder_folder_file_path = f"{uploadlib}{os.sep}Placeholders{os.sep}{asset.name}{os.sep}PH_{asset.name}.blend"
                            
                            #make the asset folder with the objects name (obj.name)
                            asset_folder_dir = os.path.dirname(asset_upload_file_path)
                            asset_placeholder_folder_dir = os.path.dirname(placeholder_folder_file_path)
                            os.makedirs(asset_folder_dir, exist_ok=True)
                            os.makedirs(asset_placeholder_folder_dir, exist_ok=True)
                            # save only the selected asset to a new clean blend file

                            asset_info = {
                                "BU_Asset": asset.name,
                                "Asset_type": asset.id_type,
                                "Placeholder": False
                                }
                            creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            asset_info['creation_time'] = creation_time
                            json_data = json.dumps(asset_info, indent=4)
                            BU_Json_Text = bpy.data.texts.get("BU_OG_Asset_Info")
                            if BU_Json_Text is None:
                                BU_Json_Text = bpy.data.texts.new("BU_OG_Asset_Info")
                            BU_Json_Text.write(json_data)
                            
                            # save only the selected asset to a new clean blend file and its Asset info as JSON
                            # bpy.ops.file.pack_all()
                            
                            datablock ={asset.local_id, BU_Json_Text}
                            bpy.data.libraries.write(asset_upload_file_path, datablock)
                            # bpy.ops.file.unpack_all(method='USE_ORIGINAL')
                            bpy.data.texts.remove(BU_Json_Text)
                            #generate placeholder files and thumbnails
                            
                            ph_asset_to_remove =file_upload_managment.generate_placeholder_blend_file(self,context,asset,asset_thumb_path)
                            if ph_asset_to_remove:
                                ph_assets_to_remove.append(ph_asset_to_remove)
                            zipped_original =file_upload_managment.zip_directory(asset_folder_dir)
                            zipped_placeholder =file_upload_managment.zip_directory(asset_placeholder_folder_dir)


                        else:
                            addon_logger.error('No valid thumbnail path found, shutdown sync')
                            print("Please set a valid thumbnail path in the upload settings!")
                            self.shutdown(context)
                            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Please set a valid thumbnail path in the upload settings!'))
                            raise Exception(f'Asset thumbnail not found, Please make sure a tumbnail exists with the following name preview_{asset.name}.png or jpg')
                            
                    except Exception as e:
                        print(f"An error occurred in generating files: {e}")
                        addon_logger.error(f"An error occurred in generating files(create_and_zip): {e}")
                        addon_logger.info(f"Removing placeholder asset because there was an error")
                        for ph_asset in ph_assets_to_remove:
                            data_collection = getattr(bpy.data, asset_types[ph_asset.id_type])
                            data_collection.remove(ph_asset)
                        self.shutdown(context)
                        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', title='An error occurred in create_and_zip: ',error_message=str(e))
                        raise Exception(f"An error occurred in generating files: {e}")
                    
                    if zipped_original not in  files_to_upload:
                        files_to_upload.append(zipped_original)

                    if zipped_placeholder not in  files_to_upload:
                        files_to_upload.append(zipped_placeholder)
                        
                    text = f"{len(files_to_upload)}/{len(assets)}"
                    progress.update(context,prog,text,context.workspace)
                
                catfile =self.copy_and_zip_catfile()
                if catfile not in  files_to_upload:
                    files_to_upload.append(catfile)
                progress.end(context)
                asset_types =addon_info.type_mapping()
                for ph_asset in ph_assets_to_remove:
                    data_collection = getattr(bpy.data, asset_types[ph_asset.bl_rna.identifier])
                    data_collection.remove(ph_asset)

            return files_to_upload
        except Exception as e:
            print(f"An error occurred in create_and_zip end: {e}")
            


class BU_OT_SelectAllAssetUpdates(bpy.types.Operator):
    """Select all assets in the asset has update list"""
    bl_idname = "bu.select_all_asset_updates"
    bl_label = "Select all assets to update"
    bl_description = "Select all assets to update"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if addon_info.is_lib_premium():
            for asset in context.scene.premium_assets_to_update:
                asset.selected = True
        else:
            for asset in context.scene.assets_to_update:
                asset.selected = True
        return {'FINISHED'}
    
class BU_OT_DeselectAllPremiumAssetUpdates(bpy.types.Operator):
    """Deselect all assets in the asset has update list"""
    bl_idname = "bu.deselect_all_asset_updates"
    bl_label = "deselect all assets to update"
    bl_description = "deselect all assets to update"
    bl_options = {"REGISTER"}


    def execute(self, context):
        if addon_info.is_lib_premium():
            for asset in context.scene.premium_assets_to_update:
                asset.selected = False
        else:
            for asset in context.scene.assets_to_update:
                asset.selected = False
        return {'FINISHED'}
    
class BU_OT_UpdateSelectedAssets(bpy.types.Operator):
    """Update selected assets in the asset has update list"""
    bl_idname = "bu.update_selected_assets"
    bl_label = "Update Assets"
    bl_description = "Update Assets"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        assets_to_update = context.scene.assets_to_update
        return any(asset.selected for asset in assets_to_update)

    def execute(self, context):
        if BU_OT_Download_Original_Library_Asset.poll(bpy.context):
            assets_to_update = context.scene.assets_to_update
            for asset in assets_to_update:
                if asset.selected and not asset.is_placeholder:
                    placeholder_name = f'PH_{asset.name}'
                    placeholder_asset = next((ph_asset for ph_asset in assets_to_update if ph_asset.name == placeholder_name), None)
                    if placeholder_asset:
                        placeholder_asset.selected = True
            bpy.ops.bu.download_original_asset('EXEC_DEFAULT', isUpdate=True)
        else:
            message = BU_OT_Download_Original_Library_Asset.bl_rna.get_poll_message()
            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=message)
            return {'CANCELLED'}
        return {'FINISHED'}
    

class UpdateableAssets(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    id: bpy.props.StringProperty()
    size: bpy.props.IntProperty()
    selected: bpy.props.BoolProperty()
    is_placeholder: bpy.props.BoolProperty()

class UpdateablePremiumAssets(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    id: bpy.props.StringProperty()
    size: bpy.props.IntProperty()
    selected: bpy.props.BoolProperty()
    is_placeholder: bpy.props.BoolProperty()



class BU_OT_AssetsToUpdate(bpy.types.Operator):
    """Show dialog box with a list of assets that have an update"""
    bl_idname = "bu.assets_to_update"
    bl_label = "Assets to Update"
    bl_description = "Assets to Update"
    bl_options = {"REGISTER"}

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        
        row.label(text="Select which assets you want to update:")
        addon_info.gitbook_link(row,'how-to-use-the-asset-browser/update-assets')
        row = layout.row(align=True)
        if sync_manager.SyncManager.is_sync_in_progress():
            statusbar.draw_progress(self,context)
        else:
            row.label(text="")
        row = layout.row(align=True)
        row.alignment = 'EXPAND'          
        row.operator('bu.select_all_asset_updates', text="Select All", icon='KEYTYPE_MOVING_HOLD_VEC')
        row.operator('bu.deselect_all_asset_updates', text="Deselect All", icon='HANDLETYPE_FREE_VEC')
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        # grod = layout.grid_flow(columns=7, align=True,even_columns=False,row_major=True)
        if addon_info.is_lib_premium():
            update_list = context.scene.premium_assets_to_update
        else:
            update_list = context.scene.assets_to_update
            
        non_placeholder_items = [item for item in update_list if not item.is_placeholder]
        box = layout.box()
        for item in non_placeholder_items:
            self.draw_item(box, item)
        row = layout.row()
        if sync_manager.SyncManager.is_sync_operator('bu.update_assets'):
            row.operator('bu.update_assets', text='Cancel Sync', icon='CANCEL')
        else:
            row.operator('bu.update_assets', text='Update Selected', icon='URL')
            
       
    def draw_item(self, box,item):
        if item.size>0:
            converted_size = f"{round(item.size/1024)}kb" if round(item.size/1024)<1000 else f"{round(item.size/1024/1024,2)}mb"
        else:
            converted_size = ""
        grid = box.grid_flow(columns=7, align=True,even_columns=False)
        grid.alignment = 'EXPAND'
        grid.label(text=item.name.replace('.zip',''))
        grid.alignment = 'LEFT'
        grid.label(text=converted_size)
        grid.alignment = 'RIGHT'
        grid.prop(item, "selected", text=" ",icon="KEYTYPE_MOVING_HOLD_VEC" if item.selected else "HANDLETYPE_FREE_VEC")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width= 300)
    
    
class BU_OT_UploadSettings(bpy.types.Operator):
    """Open the upload settings as dialog box"""
    bl_description = "Upload Settings"
    bl_idname = "bu.upload_settings"
    bl_label = "Upload Settings"
    panel_idname = "VIEW3D_PT_BU_Premium"
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        self.layout.label(text = addon_prefs.author if addon_prefs.author !='' else 'Global Author name not set', icon='CHECKMARK' if addon_prefs.author !='' else 'ERROR')
        self.layout.label(text = addon_prefs.thumb_upload_path if addon_prefs.thumb_upload_path !='' else 'Preview images folder not set', icon='CHECKMARK' if addon_prefs.thumb_upload_path !='' else 'ERROR')
        row =self.layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text="Set Author Global (Optional)")
        row.prop(addon_prefs, "author", text="")
        row =self.layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text="Set Thumbnail Upload Path")
        row.prop(addon_prefs, "thumb_upload_path", text="")
       
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class SUCCES_OT_custom_dialog(bpy.types.Operator):
    bl_idname = "succes.custom_dialog"
    bl_label = "Success Message Dialog"
    title: bpy.props.StringProperty()
    succes_message: bpy.props.StringProperty()
    amount_new_assets: bpy.props.IntProperty()
    is_original: bpy.props.BoolProperty()

    def _label_multiline(self,context, text, parent):
        panel_width = int(context.region.width)   # 7 pix on 1 character
        uifontscale = 9 * context.preferences.view.ui_scale
        max_label_width = int(panel_width // uifontscale)
        wrapper = textwrap.TextWrapper(width=50 )
        text_lines = wrapper.wrap(text=text)
        for text_line in text_lines:
            parent.label(text=text_line,)

    def draw(self, context):
        self.layout.label(text=self.title)
        intro_text = self.succes_message
        self._label_multiline(
        context=context,
        text=intro_text,
        parent=self.layout
        )
        if self.amount_new_assets > 0:
            if self.is_original:
                
                self.layout.label(text="Premium assets are downloaded to the local library")
                self.layout.operator('asset_browser.switch_to_local_library', text="Switch to Local Library")
                self.layout.label(text=f"{self.amount_new_assets} original assets synced")
            else:
                self.layout.label(text=f"{self.amount_new_assets} new previews synced")


    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self, width= 400)
        
class BU_OT_SwitchToLocalLibrary(bpy.types.Operator):
    """Switch the asset library reference to LOCAL"""
    bl_idname = "asset_browser.switch_to_local_library"
    bl_label = "Switch to Local Library"
    bl_options = {"REGISTER"}

    def execute(self, context):
        version_handler.set_asset_library_reference(context,'LOCAL')
        return {'FINISHED'}





    


classes =(
    BU_OT_AssetSyncOperator,
    WM_OT_SaveAssetFiles,
    BU_OT_UploadSettings,
    BU_OT_DownloadCatalogFile,
    SUCCES_OT_custom_dialog,
    BU_OT_SwitchToLocalLibrary,
    BU_OT_AssetsToUpdate,
    UpdateableAssets,
    UpdateablePremiumAssets,
    BU_OT_SelectAllAssetUpdates,
    BU_OT_DeselectAllPremiumAssetUpdates,
    BU_OT_UpdateSelectedAssets,
    BU_OT_SyncPremiumAssets,
    BU_OT_Update_Assets,
    BU_OT_ShowUploadProgress,
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.assets_to_update = bpy.props.CollectionProperty(type=UpdateableAssets)
    bpy.types.Scene.premium_assets_to_update = bpy.props.CollectionProperty(type=UpdateablePremiumAssets)
    bpy.types.Scene.asset_update_index = bpy.props.IntProperty()
    bpy.types.Scene.premium_asset_update_index = bpy.props.IntProperty()
    
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.assets_to_update
    del bpy.types.Scene.asset_update_index
    del bpy.types.Scene.premium_assets_to_update
    del bpy.types.Scene.premium_asset_update_index