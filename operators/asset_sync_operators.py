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
from ..utils import exceptions



class BU_OT_DownloadCatalogFile(bpy.types.Operator):
    '''Sync the catalog file to current file'''
    bl_idname = "bu.sync_catalog_file" 
    bl_label = "sync catalog file to local file"
    bl_options = {"REGISTER"}

    _timer = None
    asset_sync_instance = None
    prog = 0
    prog_text = None
    shutdown = False

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
        # elif catfile_handler.check_current_catalogs_file_exist():
        #     cls.poll_message_set('Catalog file already exists!')
        #     return False
        if BU_OT_DownloadCatalogFile.asset_sync_instance:
            return False
        else:
            return True
        
    def modal(self, context, event):
        if event.type == 'TIMER':

            if BU_OT_DownloadCatalogFile.asset_sync_instance:
                BU_OT_DownloadCatalogFile.asset_sync_instance.sync_catalog_file(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if BU_OT_DownloadCatalogFile.asset_sync_instance:
                if BU_OT_DownloadCatalogFile.asset_sync_instance.is_done():
                    print('asset_sync_instance is done')
                    
                    BU_OT_DownloadCatalogFile.asset_sync_instance = None
            if task_manager.task_manager_instance:
                if task_manager.task_manager_instance.is_done():
                    print('taskmanager is done')
                    task_manager.task_manager_instance.shutdown()
                    task_manager.task_manager_instance = None
            instances = (task_manager.task_manager_instance, BU_OT_DownloadCatalogFile.asset_sync_instance)
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
        addon_prefs = addon_info.get_addon_name().preferences
        try:
            # addon_info.set_drive_ids(context)
            bpy.ops.wm.initialize_task_manager()
            print('init task manager')
            if addon_prefs.is_admin:
                print(context.scene.upload_target_enum.switch_upload_target)
        except Exception as e:
            print(f"An error occurred init task manager: {e}")
        try:
            BU_OT_DownloadCatalogFile.asset_sync_instance = AssetSync()
            BU_OT_DownloadCatalogFile.asset_sync_instance.current_state = 'fetch_catalog_file_id'
            print('init asset_sync_instance')
        except Exception as e:
            print(f"An error occurred init asset sync: {e}")
            if task_manager.task_manager_instance:
                task_manager.task_manager_instance.set_done(True)
            if BU_OT_DownloadCatalogFile.asset_sync_instance:
                BU_OT_DownloadCatalogFile.asset_sync_instance.set_done(True)
                   
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def refresh(self, context):
        catfile = 'blender_assets.cats.txt'
        addon_prefs = addon_info.get_addon_name().preferences
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
                                print('called')
                                # bpy.ops.asset.library_refresh()


    def ErrorShutdown(self,context):
        self.shutdown = True
        if task_manager.task_manager_instance:
            task_manager.task_manager_instance.update_task_status('Error shutting down...')
            task_manager.task_manager_instance.set_done(True)
        if BU_OT_DownloadCatalogFile.asset_sync_instance:
            BU_OT_DownloadCatalogFile.asset_sync_instance.set_done(True)
        progress.end(context)
        self.cancel(context)



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
                WM_OT_AssetSyncOperator.asset_sync_instance = None
                BU_OT_Download_Original_Library_Asset.asset_sync_instance = None
                BU_OT_DownloadCatalogFile.asset_sync_instance= None
                if instance.futures:
                    all_futures_done = all(future.done() for future in instance.futures)
                    if all_futures_done:
                        instance.update_task_status('Cancelled')
                        instance.executor.shutdown(wait=False)
                        instance.executor = None
                        WM_OT_AssetSyncOperator.asset_sync_instance = None
                        BU_OT_Download_Original_Library_Asset.asset_sync_instance = None
                        BU_OT_DownloadCatalogFile.asset_sync_instance= None
                        instances = (WM_OT_AssetSyncOperator.asset_sync_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance,BU_OT_DownloadCatalogFile.asset_sync_instance)
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
    bl_options = {"REGISTER"}
    
    _timer = None
    asset_sync_instance = None
    prog = 0
    prog_text = None
    shutdown = False
    
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
    assets = []
    shutdown = False

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
            if not self.shutdown:
                WM_OT_SaveAssetFiles.asset_upload_sync_instance.sync_assets_to_server(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if self.shutdown == True:
                self.ErrorShutdown(context)
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
        addon_prefs = addon_info.get_addon_name().preferences
        thumst_path = addon_prefs.thumb_upload_path
        if not os.path.exists(thumst_path):
            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Asset thumbnail not found'))
            print("Please set a valid thumbnail path in the upload settings!")
            self.ErrorShutdown(context)
            return {'FINISHED'}
        try:
            self.assets = context.selected_asset_files
            for asset in self.assets:
                asset_thumb_path = file_upload_managment.get_asset_thumb_paths(asset)
                if os.path.exists(asset_thumb_path):
                    bpy.ops.wm.initialize_task_manager()
                    addon_info.set_drive_ids(context)
                    files_to_upload =self.create_and_zip(context)
                else:
                    self.ErrorShutdown(context)
                    bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(f'Asset thumbnail not found, Please make sure a tumbnail exists with the following name preview_{asset.name}.png or jpg'))
                    

            
            
        except Exception as e:
            print(f"An error occurred: {e}")
        try:
            if not self.shutdown:
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
    
    
    def ErrorShutdown(self,context):
        
        if task_manager.task_manager_instance:
            task_manager.task_manager_instance.update_task_status('Error shutting down...')
            task_manager.task_manager_instance.set_done(True)
        if WM_OT_SaveAssetFiles.asset_upload_sync_instance:
            WM_OT_SaveAssetFiles.asset_upload_sync_instance.set_done(True)
        progress.end(context)
        self.cancel(context)
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
        instance = WM_OT_SaveAssetFiles.asset_upload_sync_instance
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
                            file_upload_managment.ShowNoThumbsWarning("Please set a valid thumbnail path in the upload settings!")
                            print("Please set a valid thumbnail path in the upload settings!")
                            self.ErrorShutdown(context)
                            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str('Asset thumbnail not found'))  
                            
                    except Exception as e:
                        print(f"An error occurred in create_and_zip: {e}")       
                        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(e))   
            
                    print('zipped asset_orginal', zipped_original)
                    print('zipped asset_placeholder', zipped_placeholder)
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
        except Exception as e:
            print(f"An error occurred in create_and_zip: {e}")
            bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(e))  

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
        if self.amount_new_assets > 0:
            if self.is_original:
                self.layout.label(text=f"{self.amount_new_assets} original assets synced")
                self.layout.label(text="Premium assets are downloaded to the local library")
                self.layout.operator('asset_browser.switch_to_local_library', text="Switch to Local Library")
            else:
                self.layout.label(text=f"{self.amount_new_assets} new previews synced")
        intro_text = self.succes_message
        self._label_multiline(
        context=context,
        text=intro_text,
        parent=self.layout
        )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width= 300)
        
class BU_OT_SwitchToLocalLibrary(bpy.types.Operator):
    bl_idname = "asset_browser.switch_to_local_library"
    bl_label = "Switch to Local Library"
    bl_options = {"REGISTER"}

    def execute(self, context):
        context.space_data.params.asset_library_ref = 'LOCAL'
        return {'FINISHED'}




class ERROR_OT_custom_dialog(bpy.types.Operator):
    bl_idname = "error.custom_dialog"
    bl_label = "Error Message Dialog"
    error_message: bpy.props.StringProperty()


        
    def _label_multiline(self,context, text, parent):
        panel_width = int(context.region.width)   # 7 pix on 1 character
        uifontscale = 9 * context.preferences.view.ui_scale
        max_label_width = int(panel_width // uifontscale)
        wrapper = textwrap.TextWrapper(width=50 )
        text_lines = wrapper.wrap(text=text)
        for text_line in text_lines:
            parent.label(text=text_line,)

    def draw(self, context):
        intro_text = self.error_message
        self._label_multiline(
        context=context,
        text=intro_text,
        parent=self.layout
        )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width= 300)
    


classes =(
    BU_OT_CancelSync,
    WM_OT_AssetSyncOperator,
    WM_OT_SaveAssetFiles,
    BU_OT_UploadSettings,
    BU_OT_DownloadCatalogFile,
    ERROR_OT_custom_dialog,
    SUCCES_OT_custom_dialog,
    BU_OT_SwitchToLocalLibrary,
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.append(AssetSyncStatus.draw_progress)
    
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.remove(AssetSyncStatus.draw_progress)
