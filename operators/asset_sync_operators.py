import bpy
import os
import shutil
import zipfile
import textwrap
from bpy.types import Context
from .file_managment import AssetSync
from .file_upload_managment import AssetUploadSync,create_and_zip_files
from . import task_manager
from .download_library_files import BU_OT_Download_Original_Library_Asset
from ..utils import addon_info,progress,catfile_handler
from ..ui import statusbar
from . import file_upload_managment
from ..utils import exceptions,sync_manager
from ..utils.addon_logger import addon_logger
from .handle_asset_updates import SyncPremiumPreviews,UpdatePremiumAssets

class BU_OT_Update_Assets(bpy.types.Operator):
    bl_idname = "bu.update_assets"
    bl_label = "Update Premium Assets"
    bl_description = "Update Premium Assets"
    bl_options = {"REGISTER"}

    _timer = None
    requested_cancel = False

    @classmethod
    def poll(cls, context):
        addon_prefs= addon_info.get_addon_name().preferences
        isPremium = addon_info.is_lib_premium()
        current_library_name = context.area.spaces.active.params.asset_library_ref
        payed = addon_prefs.payed
        assets_to_update = context.scene.premium_assets_to_update if isPremium else context.scene.assets_to_update
        if not any( asset.selected for asset in assets_to_update):
            cls.poll_message_set ('Please select at least one asset to update')
            return False
        if payed == False and current_library_name ==addon_info.get_lib_name(True,addon_prefs.debug_mode):
            cls.poll_message_set('Please input a valid BUK premium license key')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            # Enable the operator if it's the one currently running the sync
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
            self.update_premium_handler = UpdatePremiumAssets.get_instance()
            if self.update_premium_handler.current_state is None and not self.requested_cancel:
                addon_info.set_drive_ids(context)
                bpy.ops.wm.initialize_task_manager()
                self.update_premium_handler.reset()
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
                
                self.sync_preview_handler.reset()
                wm = context.window_manager
                self._timer = wm.event_timer_add(0.5, window=context.window)
                wm.modal_handler_add(self)
                self.sync_preview_handler.current_state = 'fetch_assets'

            else:
                print("cancelled")
                self.sync_preview_handler.requested_cancel = True
                self.requested_cancel = True
                self.sync_preview_handler.reset()
            
        except Exception as e:
            print(f"An error occurred: {e}")
        
  
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            self.sync_preview_handler.perform_sync(context)
            
            if self.requested_cancel:
                print('requested cancelled')
                self.sync_preview_handler.set_done(True)
            
            if self.requested_cancel or self.sync_preview_handler.is_done():
                self.shutdown(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}
    

    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_SyncPremiumAssets.bl_idname)
        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context)
        bpy.ops.asset.library_refresh()
        
        self.requested_cancel = False

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

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
                self.shutdown(context)

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
                BU_OT_DownloadCatalogFile.asset_sync_instance
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
        bpy.ops.asset.library_refresh()
        
        self.requested_cancel = False

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
  

    def refresh(self, context):
        catfile = 'blender_assets.cats.txt'
        current_filepath = bpy.data.filepath
        current_filepath_cat_file = os.path.join(current_filepath,catfile)

        if current_filepath_cat_file:
            for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'FILE_BROWSER':
                        with context.temp_override(window=window, area=area):
                            context.space_data.params.asset_library_ref = 'LOCAL'
                            if context.space_data.params.asset_library_ref == 'LOCAL':
                                bpy.ops.asset.catalog_new()
                                bpy.ops.asset.catalogs_save()
                                bpy.ops.asset.catalog_undo()
                                bpy.ops.asset.catalogs_save()
    

class WM_OT_AssetSyncOperator(bpy.types.Operator):
    bl_idname = "wm.sync_assets"
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

            if self.requested_cancel or self.asset_sync_handler.is_done():
                self.shutdown(context)
                return {'FINISHED'}


        return {'PASS_THROUGH'}

    def execute(self, context):
        sync_manager.SyncManager.start_sync(WM_OT_AssetSyncOperator.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        try:
            self.asset_sync_handler = AssetSync.get_instance()
            print('self.requested_cancel ',self.requested_cancel)
            print('self.asset_sync_handler.current_state ',self.asset_sync_handler.current_state)
            if self.asset_sync_handler.current_state is None and not self.requested_cancel:

                addon_info.set_drive_ids(context)
                bpy.ops.wm.initialize_task_manager()
                if task_manager.task_manager_instance:
                    self.asset_sync_handler.reset()
                    self.asset_sync_handler.current_state = 'fetch_assets'
            else:
                print("cancelled")
                self.asset_sync_handler.requested_cancel = True
                self.requested_cancel = True
                self.asset_sync_handler.reset()

        except Exception as e:
            print(f"An error occurred: {e}")
            addon_logger.error(e)
            self.shutdown(context)
     
        return {'RUNNING_MODAL'}


    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(WM_OT_AssetSyncOperator.bl_idname)
        self.asset_sync_handler.reset()
        taskmanager_cleanup(context,task_manager)
        progress.end(context) 
        self.cancel(context) 
        bpy.ops.asset.library_refresh()
       
        self.requested_cancel = False

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
 


class WM_OT_SaveAssetFiles(bpy.types.Operator):
    bl_idname = "wm.save_files"
    bl_label = "Upload to BUK Server"
    bl_description = "Upload assets to the Blender Universe Kit upload folder on the server."
    bl_options = {"REGISTER"}

    _timer = None
    assets = []


    @classmethod
    def poll(cls, context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        thumb_path = addon_name.preferences.thumb_upload_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        elif not os.path.exists(thumb_path):
            cls.poll_message_set('Please set a thumb upload path in prefferences.')
            return False
        if sync_manager.SyncManager.is_sync_in_progress():
            # Enable the operator if it's the one currently running the sync
            if sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                cls.poll_message_set('Already processing uploads please wait')
                return False
        return True
         
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                self.upload_asset_handler.sync_assets_to_server(context)
            except Exception as error_message:
                print(f"An error occurred: {error_message}")
                addon_logger.error(error_message)
                self.shutdown(context)

            if self.upload_asset_handler.is_done():
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
                    self.upload_asset_handler.reset()
                    return {'FINISHED'}
                
                self.assets = context.selected_asset_files
                for asset in self.assets:
                    asset_thumb_path = file_upload_managment.get_asset_thumb_paths(asset) 
                    if not asset_thumb_path or not os.path.exists(asset_thumb_path):
                        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(f'Asset thumbnail not found, Please make sure a tumbnail exists with the following name preview_{asset.name}.png or jpg'))
                        print("Please set a valid thumbnail path in the upload settings!")
                        self.upload_asset_handler.reset()
                        return {'FINISHED'}
         

                
                bpy.ops.wm.initialize_task_manager()
                addon_info.set_drive_ids(context)
                files =self.create_and_zip(context)
                if files:  
                    self.upload_asset_handler.reset()
                    self.upload_asset_handler.files_to_upload = files
                    self.upload_asset_handler.current_state = 'initiate_upload'
            else:
                self.upload_asset_handler.reset()
                
                return {'FINISHED'}


        except Exception as error_message:
            addon_logger.error(error_message)
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
        assets = context.selected_asset_files
        progress.init(context,len(assets),'creating and zipping files...')
        task_manager.task_manager_instance.update_task_status("creating and zipping files...")
        
        prog = 0
        files_to_upload=[]
        try:
            if assets != None:
                # self.task_manager.update_task_status("creating assets...")
                # print(self.selected_assets)
                for obj in assets:
                    
                    try:
                        
                        asset_thumb_path = file_upload_managment.get_asset_thumb_paths(obj)
                        if os.path.exists(asset_thumb_path):
                            zipped_original,zipped_placeholder = create_and_zip_files(self,context,obj,asset_thumb_path)
                        else:
                            # file_upload_managment.ShowNoThumbsWarning("Please set a valid thumbnail path in the upload settings!")
                            print("Please set a valid thumbnail path in the upload settings!")
                            self.shutdown = True
                            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Please set a valid thumbnail path in the upload settings!'))  
                            
                    except Exception as e:
                        print(f"An error occurred in create_and_zip: {e}")       
                        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(e))

            
                    if zipped_original not in  files_to_upload:
                        files_to_upload.append(zipped_original)
                        
                    if zipped_placeholder not in  files_to_upload:
                        files_to_upload.append(zipped_placeholder)
                        
                    text = f"{len(files_to_upload)}/{len(assets)}"
                    progress.update(context,prog,text,context.workspace)
                catfile =self.copy_and_zip_catfile()
                if catfile not in  files_to_upload:
                    files_to_upload.append(catfile)
                    print('zipped catfile', catfile)
                progress.end(context)
            return files_to_upload
        except Exception as e:
            print(f"An error occurred in create_and_zip: {e}")
            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(e))  


class BU_OT_CancelSync(bpy.types.Operator):
    bl_idname = "bu.cancel_sync"
    bl_label = "Cancel Sync"
    bl_description = "Cancel Sync"
    bl_options = {"REGISTER"}

    _timer = None

    
    @classmethod
    def poll(cls, context):
        instances = (WM_OT_AssetSyncOperator.asset_sync_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance,BU_OT_DownloadCatalogFile.asset_sync_instance)
        return any(instances)
    
    def cancel_tasks(self, instance):
        if instance:
            instance.requested_cancel = True
            # Cancel futures
            if hasattr(instance, 'future') and instance.future:
                instance.future.cancel()
                instance.future = None
            if hasattr(instance, 'future_to_assets') and instance.future_to_assets:
                instance.future_to_assets.cancel()
                instance.future_to_assets = None
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            tm_instance = task_manager.task_manager_instance
            instances = (WM_OT_AssetSyncOperator.asset_sync_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance,BU_OT_DownloadCatalogFile.asset_sync_instance)
            if tm_instance:
                if tm_instance.executor:  
                    if tm_instance.futures:
                        all_futures_done = all(future.done() for future in tm_instance.futures)
                        if all_futures_done:
                            tm_instance.update_task_status('Cancelled')
                            task_manager.task_manager_instance.executor.shutdown(wait=False)
                            tm_instance.executor = None
                            WM_OT_AssetSyncOperator.asset_sync_instance = None
                            BU_OT_Download_Original_Library_Asset.asset_sync_instance = None
                            BU_OT_DownloadCatalogFile.asset_sync_instance = None
                            
                            if all(instance is None for instance in instances): #Double check because of threading
                                progress.end(context)
                                task_manager.task_manager_instance = None
                                self.cancel(context)
                                
                                return {'FINISHED'}
            else:
                WM_OT_AssetSyncOperator.asset_sync_instance = None
                BU_OT_Download_Original_Library_Asset.asset_sync_instance = None
                BU_OT_DownloadCatalogFile.asset_sync_instance = None
                if not tm_instance: #Double check because of threading
                    if all(instance is None for instance in instances):
                        progress.end(context)
                        self.cancel(context)
                        
                        return {'FINISHED'}
                    
        return {'PASS_THROUGH'}

    #TODO: Does not work yet have to figure out how to cancel everything and shut down sync
    def execute(self, context):
        instances = (WM_OT_AssetSyncOperator.asset_sync_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance,BU_OT_DownloadCatalogFile.asset_sync_instance)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)

              
        for instance in instances:
            if instance:
                self.cancel_tasks(instance)
                

        if task_manager.task_manager_instance:
            instance = task_manager.task_manager_instance
            instance.requested_cancel = True
            instance.update_task_status('cancelling.. please wait')

 
        return {'RUNNING_MODAL'}
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class BU_OT_SelectAllPremiumAssetUpdates(bpy.types.Operator):
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
    bl_idname = "bu.assets_to_update"
    bl_label = "Assets to Update"
    bl_description = "Assets to Update"
    bl_options = {"REGISTER"}

    
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Select which assets you want to update:")
        
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
    bl_idname = "bu.upload_settings"
    bl_label = "Upload Settings"
    panel_idname = "VIEW3D_PT_BU_Premium"
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        self.layout.label(text = addon_prefs.author if addon_prefs.author !='' else 'Author name not set', icon='CHECKMARK' if addon_prefs.author !='' else 'ERROR')
        self.layout.label(text = addon_prefs.thumb_upload_path if addon_prefs.thumb_upload_path !='' else 'Preview images folder not set', icon='CHECKMARK' if addon_prefs.thumb_upload_path !='' else 'ERROR')
        row =self.layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text="Set Author")
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
    # new_asset_names: bpy.props.CollectionProperty(type=bpy.types.StringProperty)


        
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
    bl_idname = "asset_browser.switch_to_local_library"
    bl_label = "Switch to Local Library"
    bl_options = {"REGISTER"}

    def execute(self, context):
        context.space_data.params.asset_library_ref = 'LOCAL'
        return {'FINISHED'}





    


classes =(
    BU_OT_CancelSync,
    WM_OT_AssetSyncOperator,
    WM_OT_SaveAssetFiles,
    BU_OT_UploadSettings,
    BU_OT_DownloadCatalogFile,
    SUCCES_OT_custom_dialog,
    BU_OT_SwitchToLocalLibrary,
    BU_OT_AssetsToUpdate,
    UpdateableAssets,
    UpdateablePremiumAssets,
    BU_OT_SelectAllPremiumAssetUpdates,
    BU_OT_DeselectAllPremiumAssetUpdates,
    BU_OT_UpdateSelectedAssets,
    BU_OT_SyncPremiumAssets,
    BU_OT_Update_Assets,
    
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