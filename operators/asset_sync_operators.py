import bpy
import os
import shutil
import zipfile
from bpy.types import Context
from .file_managment import AssetSync
from .file_upload_managment import AssetUploadSync,create_and_zip_files
from . import task_manager

from ..utils import addon_info,progress,catfile_handler
from ..ui import statusbar

class CancelSync(bpy.types.Operator):
    bl_idname = "wm.cancel_sync"
    bl_label = "Cancel Sync"
    bl_description = "Cancel Sync"
    bl_options = {"REGISTER", "UNDO"}

    #TODO: Does not work yet have to figure out how to cancel everything and shut down sync
    def execute(self, context):
        task_manager.task_manager_instance.shutdown()
        WM_OT_AssetSyncOperator.asset_sync_instance = None
        task_manager.task_manager_instance = None
        return {'FINISHED'}

class AssetSyncOriginals(bpy.types.Operator):
    bl_idname = "wm.sync_original_assets"
    bl_label = "Sync Orginal Assets"
    bl_description = "Syncs original assets from the server"
    bl_options = {"REGISTER", "UNDO"}
    
    _timer = None
    asset_sync_instance = None
    prog = 0
    prog_text = None

    @classmethod
    def poll(cls, context):
        if WM_OT_AssetSyncOperator.asset_sync_instance:
            return False
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            WM_OT_AssetSyncOperator.asset_sync_instance.sync_original_assets(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            if task_manager.task_manager_instance.is_done():
                print('taskmanager is done')
                task_manager.task_manager_instance.shutdown()
                task_manager.task_manager_instance = None
            # Check if the AssetSync tasks are done
            if WM_OT_AssetSyncOperator.asset_sync_instance.is_done() or WM_OT_AssetSyncOperator.asset_sync_instance is None:
                WM_OT_AssetSyncOperator.asset_sync_instance = None
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
            WM_OT_AssetSyncOperator.asset_sync_instance.current_state = 'sync_original_assets'
            
            # bpy.ops.wm.sync_assets_status('INVOKE_DEFAULT')
            # WM_OT_AssetSyncOperator.asset_sync_instance.start_tasks()
        except Exception as e:
            print(f"An error occurred: {e}")
        
     
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
        if WM_OT_AssetSyncOperator.asset_sync_instance:
            return False
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            WM_OT_AssetSyncOperator.asset_sync_instance.start_tasks(context)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if task_manager.task_manager_instance.is_done():
                print('taskmanager is done')
                task_manager.task_manager_instance.shutdown()
                task_manager.task_manager_instance = None
            if WM_OT_AssetSyncOperator.asset_sync_instance.is_done():
                bpy.ops.asset.library_refresh()
                WM_OT_AssetSyncOperator.asset_sync_instance = None
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
            task_manager.task_manager_instance.set_done(True)
            WM_OT_AssetSyncOperator.asset_sync_instance.set_done(True)
     
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class WM_OT_AssetSyncStatus(bpy.types.Operator):
    bl_idname = "wm.sync_assets_status"
    bl_label = "Sync Status"
    bl_description = "Show sync status"
    bl_options = {"REGISTER"}


    @classmethod
    def poll(cls, context):
        if not WM_OT_AssetSyncOperator.asset_sync_instance:
            cls.poll_message_set('Nothing is being processed.')
            return False
        elif WM_OT_AssetSyncOperator.asset_sync_instance.is_done():
            cls.poll_message_set('Synced.')
            return False
        else:
            return True
        # cls.poll_message_set('Debugging without ui update.')
        # return False
        
    def modal(self, context, event):
        if event.type == 'TIMER':
            # Force redraw to update UI
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            
            if task_manager.task_manager_instance.is_done():
                print('taskmanager is done')
                task_manager.task_manager_instance.shutdown()
                task_manager.task_manager_instance = None
                self.cancel(context)
                return {'FINISHED'}
                
        return {'PASS_THROUGH'}

    def draw(self, context):
        layout = self.layout
        layout.label(text='Asset Sync Status')
        row = layout.row()
        col = row.column()
        if task_manager.task_manager_instance:
            col.label(text=f"Task Status: {bpy.context.scene.status_text}")
            col.label(text=f"Tasks Total: {bpy.context.scene.completed_tasks}/{bpy.context.scene.total_tasks}")
            col.label(text=f"Subtask Status: {bpy.context.scene.status_subtask_text}")
            col.label(text=f"Subtask Total: {bpy.context.scene.completed_sub_tasks}/{bpy.context.scene.total_sub_tasks}")
        else:
            bpy.context.scene.status_text = "Nothing is being processed."
            

    def invoke(self, context, event):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        return {'RUNNING_MODAL'}
        
    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)

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
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        elif context.selected_asset_files:
            return True
        elif WM_OT_SaveAssetFiles.asset_upload_sync_instance:
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
            if task_manager.task_manager_instance.is_done():
                print('taskmanager is done')
                task_manager.task_manager_instance.shutdown()
                task_manager.task_manager_instance = None
            if WM_OT_SaveAssetFiles.asset_upload_sync_instance.is_done():
                bpy.ops.asset.library_refresh()
                WM_OT_SaveAssetFiles.asset_upload_sync_instance = None
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
            task_manager.task_manager_instance.set_done(True)
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


classes =(
    WM_OT_AssetSyncOperator,
    WM_OT_AssetSyncStatus,
    WM_OT_SaveAssetFiles,
    CancelSync,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.append(AssetSyncStatus.draw_progress)
    
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.remove(AssetSyncStatus.draw_progress)
