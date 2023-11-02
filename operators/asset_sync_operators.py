import bpy
import os
import shutil
import zipfile
from bpy.types import Context
from .file_managment import AssetSync
from .file_upload_managment import AssetUploadSync,create_and_zip_files
from . import task_manager
from .download_library_files import BU_OT_Download_Original_Library_Asset
from ..utils import addon_info,progress,catfile_handler
from ..ui import statusbar



class WM_OT_DownloadCatalogFile(bpy.types.Operator):
    '''Sync the catalog file to current file'''
    bl_idname = "wm.sync_catalog_file" 
    bl_label = "sync catalog file to local file"
    bl_options = {"REGISTER"}

    _timer = None
    asset_sync_instance = None
    prog = 0
    prog_text = None

    @classmethod
    def poll(cls,context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        if not bpy.data.filepath:
            cls.poll_message_set('Please make sure your file is saved')
        # elif catfile_handler.check_current_catalogs_file_exist():
        #     cls.poll_message_set('Catalog file already exists!')
        #     return False
        else:
            return True
        
    def modal(self, context, event):
        if event.type == 'TIMER':

            if WM_OT_DownloadCatalogFile.asset_sync_instance:
                WM_OT_DownloadCatalogFile.asset_sync_instance.sync_catalog_file(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if WM_OT_DownloadCatalogFile.asset_sync_instance:
                if WM_OT_DownloadCatalogFile.asset_sync_instance.is_done():
                    print('asset_sync_instance is done')
                    
                    WM_OT_DownloadCatalogFile.asset_sync_instance = None
            if task_manager.task_manager_instance:
                if task_manager.task_manager_instance.is_done():
                    print('taskmanager is done')
                    task_manager.task_manager_instance.shutdown()
                    task_manager.task_manager_instance = None
            instances = (task_manager.task_manager_instance, WM_OT_DownloadCatalogFile.asset_sync_instance)
            if all(instance is None for instance in instances):
                progress.end(context)
                self.cancel(context)
                
                self.refresh(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        try:
            # addon_info.set_drive_ids(context)
            bpy.ops.wm.initialize_task_manager()
            print('init task manager')
        except Exception as e:
            print(f"An error occurred init task manager: {e}")
        try:
            WM_OT_DownloadCatalogFile.asset_sync_instance = AssetSync()
            WM_OT_DownloadCatalogFile.asset_sync_instance.current_state = 'fetch_catalog_file_id'
            print('init asset_sync_instance')
        except Exception as e:
            print(f"An error occurred init asset sync: {e}")
            if task_manager.task_manager_instance:
                task_manager.task_manager_instance.set_done(True)
            if WM_OT_DownloadCatalogFile.asset_sync_instance:
                WM_OT_DownloadCatalogFile.asset_sync_instance.set_done(True)
                   
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def refresh(self, context):
        catfile = 'blender_assets.cats.txt'
        addon_prefs = addon_info.get_addon_name().preferences
        current_filepath = bpy.data.filepath
        download_catalog_folder_id =addon_prefs.download_catalog_folder_id
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
                                # bpy.ops.asset.library_refresh()

class BU_OT_CancelSync(bpy.types.Operator):
    bl_idname = "bu.cancel_sync"
    bl_label = "Cancel Sync"
    bl_description = "Cancel Sync"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None
    
    # @classmethod
    # def poll(cls, context):
    #     instances = (WM_OT_AssetSyncOperator.asset_sync_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance)
    #     return any(instances)
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            instance = task_manager.task_manager_instance
            if instance:
                if instance.futures:
                    all_futures_done = all(future.done() for future in instance.futures)
                    if all_futures_done:
                        instance.update_task_status('Cancelled')
                        instance.executor.shutdown(wait=False)
                        instance.executor = None
                        WM_OT_AssetSyncOperator.asset_sync_instance = None
                        BU_OT_Download_Original_Library_Asset.asset_sync_instance = None
                        WM_OT_DownloadCatalogFile.asset_sync_instance= None
                        instances = (WM_OT_AssetSyncOperator.asset_sync_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance,WM_OT_DownloadCatalogFile.asset_sync_instance)
                        if all(instance is None for instance in instances):
                            progress.end(context)
                            task_manager.task_manager_instance = None
                            self.cancel(context)
                            return {'FINISHED'}
        return {'PASS_THROUGH'}

    #TODO: Does not work yet have to figure out how to cancel everything and shut down sync
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        def cancel_tasks(instance):
            if instance:
                instance.requested_cancel = True
                # Cancel futures
                if hasattr(instance, 'future') and instance.future:
                    instance.future.cancel()
                    instance.future = None
                if hasattr(instance, 'future_to_assets') and instance.future_to_assets:
                    instance.future_to_assets = None
                

        if BU_OT_Download_Original_Library_Asset.asset_sync_instance:
            cancel_tasks(BU_OT_Download_Original_Library_Asset.asset_sync_instance)
            print('requested_cancel download', BU_OT_Download_Original_Library_Asset.asset_sync_instance.requested_cancel)
            BU_OT_Download_Original_Library_Asset.asset_sync_instance = None

        if WM_OT_AssetSyncOperator.asset_sync_instance:
            cancel_tasks(WM_OT_AssetSyncOperator.asset_sync_instance)
            print('requested_cancel placeholder download', WM_OT_AssetSyncOperator.asset_sync_instance.requested_cancel)
            WM_OT_AssetSyncOperator.asset_sync_instance = None

        if task_manager.task_manager_instance:
            instance = task_manager.task_manager_instance
            instance.requested_cancel = True
            instance.update_task_status('cancelling.. please wait')

 
        return {'RUNNING_MODAL'}
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class WM_OT_AssetSyncOperator(bpy.types.Operator):
    bl_idname = "wm.sync_assets"
    bl_label = "Sync Assets"
    bl_description = "Syncs preview assets from the server"
    bl_options = {"REGISTER", "UNDO"}
    
    _timer = None
    asset_sync_instance = None
    prog = 0
    prog_text = None

    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_name().preferences
        if WM_OT_AssetSyncOperator.asset_sync_instance or BU_OT_Download_Original_Library_Asset.asset_sync_instance:
            return False
        if addon_prefs.lib_path =='':
            cls.poll_message_set('Please input a valid library path. Go to Asset Browser settings in the BU side panel')
            return False
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            if WM_OT_AssetSyncOperator.asset_sync_instance:
                WM_OT_AssetSyncOperator.asset_sync_instance.start_tasks(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if WM_OT_AssetSyncOperator.asset_sync_instance:
                if WM_OT_AssetSyncOperator.asset_sync_instance.is_done():
                    print('asset_sync_instance is done')
                    bpy.ops.asset.library_refresh()
                    WM_OT_AssetSyncOperator.asset_sync_instance = None
            if task_manager.task_manager_instance:
                if task_manager.task_manager_instance.is_done():
                    print('taskmanager is done')
                    task_manager.task_manager_instance.shutdown()
                    task_manager.task_manager_instance = None
            instances = (task_manager.task_manager_instance, WM_OT_AssetSyncOperator.asset_sync_instance)
            if all(instance is None for instance in instances):
                progress.end(context)
                self.cancel(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        try:
            addon_info.set_drive_ids(context)
            bpy.ops.wm.initialize_task_manager()
        except Exception as e:
            print(f"An error occurred: {e}")
        try:
            WM_OT_AssetSyncOperator.asset_sync_instance = AssetSync()
            WM_OT_AssetSyncOperator.asset_sync_instance.current_state = 'fetch_assets'
        except Exception as e:
            print(f"An error occurred: {e}")
            if task_manager.task_manager_instance:
                task_manager.task_manager_instance.set_done(True)
            if WM_OT_AssetSyncOperator.asset_sync_instance:
                WM_OT_AssetSyncOperator.asset_sync_instance.set_done(True)
     
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)



class WM_OT_SaveAssetFiles(bpy.types.Operator):
    bl_idname = "wm.save_files"
    bl_label = "Upload to BUK Server"
    bl_description = "Upload assets to the Blender Universe Kit upload folder on the server."
    bl_options = {"REGISTER", "UNDO"}

    _timer = None
    asset_upload_sync_instance = None
    prog = 0
    prog_text = None

    @classmethod
    def poll(cls, context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        thumb_path = addon_name.preferences.thumb_upload_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        elif context.selected_asset_files:
            return True
        elif WM_OT_SaveAssetFiles.asset_upload_sync_instance:
            return False
        if thumb_path =='':
            cls.poll_message_set('Please set a thumb upload path in prefferences.')
            return False
        return True
         
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            
            WM_OT_SaveAssetFiles.asset_upload_sync_instance.sync_assets_to_server(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            
            if task_manager.task_manager_instance and task_manager.task_manager_instance.is_done():
                    print('taskmanager is done')
                    task_manager.task_manager_instance.shutdown()
                    task_manager.task_manager_instance = None
            if WM_OT_SaveAssetFiles.asset_upload_sync_instance:
                if WM_OT_SaveAssetFiles.asset_upload_sync_instance.is_done():
                    bpy.ops.asset.library_refresh()
                    WM_OT_SaveAssetFiles.asset_upload_sync_instance = None
                    
            instances = (task_manager.task_manager_instance, WM_OT_SaveAssetFiles.asset_upload_sync_instance)
            if all(instance is None for instance in instances):
                progress.end(context)
                self.cancel(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}
    
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        try:
            bpy.ops.wm.initialize_task_manager()
            addon_info.set_drive_ids(context)
            files_to_upload =self.create_and_zip(context)
            
        except Exception as e:
            print(f"An error occurred: {e}")
        try:
            WM_OT_SaveAssetFiles.asset_upload_sync_instance = AssetUploadSync()
            WM_OT_SaveAssetFiles.asset_upload_sync_instance.files_to_upload = files_to_upload
            WM_OT_SaveAssetFiles.asset_upload_sync_instance.current_state = 'initiate_upload'
        except Exception as e:
            print(f"An error occurred: {e}")
            if task_manager.task_manager_instance:
                task_manager.task_manager_instance.set_done(True)
            if WM_OT_SaveAssetFiles.asset_upload_sync_instance:
                WM_OT_SaveAssetFiles.asset_upload_sync_instance.set_done(True)

        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)



    
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
        if assets != None:
            # self.task_manager.update_task_status("creating assets...")
            # print(self.selected_assets)
            for obj in assets:
                zipped_original,zipped_placeholder = create_and_zip_files(self,context,obj)
                if zipped_original not in  files_to_upload:
                    files_to_upload.append(zipped_original)
                    print('zipped asset', zipped_original)
                if zipped_placeholder not in  files_to_upload:
                    files_to_upload.append(zipped_placeholder)
                    print('zipped asset', zipped_placeholder)
                text = f"{len(files_to_upload)}/{len(assets)}"
                progress.update(context,prog,text,context.workspace)
            catfile =self.copy_and_zip_catfile()
            if catfile not in  files_to_upload:
                files_to_upload.append(catfile)
                print('zipped catfile', catfile)
            progress.end(context)
        return files_to_upload
    
class BU_OT_UploadSettings(bpy.types.Operator):
    bl_idname = "bu.upload_settings"
    bl_label = "Upload Settings"
    panel_idname = "VIEW3D_PT_BU_Premium"
    def execute(self, context):
        for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        with context.temp_override(window=window, area=area):
                            # print(context.space_data.__dir__())
                            bpy.ops.wm.context_toggle(data_path='space_data.show_region_ui')
                            print(area.spaces[0].__dir__())
                            
                            # for p in dir(bpy.types):
                            #     cls = getattr(bpy.types, p)
                            #     if (issubclass(cls, bpy.types.Panel)
                            #         and getattr(cls, "bl_space_type", "") == 'VIEW_3D'):
                            #             p, getattr(cls, "bl_category", "No Category")
                            # bpy.ops.wm.context_set_id(data_path=self.panel_idname)
                            # bpy.ops.wm.context_toggle(data_path=self.panel_idname)
        return {'FINISHED'}


classes =(
    BU_OT_CancelSync,
    WM_OT_AssetSyncOperator,
    WM_OT_SaveAssetFiles,
    BU_OT_UploadSettings,
    WM_OT_DownloadCatalogFile,
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.append(AssetSyncStatus.draw_progress)
    
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.remove(AssetSyncStatus.draw_progress)
