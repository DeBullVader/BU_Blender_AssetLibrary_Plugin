import bpy,os,json
from . import network,task_manager,file_managment
from .download_file import DownloadFile
from .sync_ui_progress_handler import addFileProgress,clearFilesProgress
from ..utils import addon_info,sync_manager,drag_drop_handler,progress,version_handler,addon_logger
from functools import partial
from bpy.types import Operator




class BU_OT_DownloadOriginalCore(Operator):
    bl_idname = "bu.download_original_core"
    bl_label = "Download Original"
    bl_description = "Download Original"
    bl_options = {"REGISTER"}

    asset_name: bpy.props.StringProperty()
    is_placeholder: bpy.props.BoolProperty()
    is_premium: bpy.props.BoolProperty()
    is_dragged: bpy.props.BoolProperty()
    asset_server_data = {}
    downloaded_sizes = {}
    future = None
    
    def execute(self, context):
        print('called download original')
        self.target_lib = addon_info.get_target_lib(context)
        clearFilesProgress(context)
        bpy.ops.wm.initialize_task_manager()
        self.task_manager = task_manager.task_manager_instance
        if self.is_dragged:
            self.task_manager.update_task_status('Placeholder dropped initiate download process..')
        sync_manager.SyncManager.start_sync(BU_OT_DownloadOriginalCore.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, window=context.window)
        wm.modal_handler_add(self)
        # self.asset_name = self.asset_name.removesuffix('_p')
        if not self.task_manager:
            print('failed to initialize task manager')
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                if not self.asset_server_data:
                    if self.future == None:
                        # print('self.asset_name: ',self.asset_name)
                        if not self.is_premium:
                            print('fetching original core asset id...')
                            self.future = submit_task(self,'Fetching original core asset id...',network.get_asset_id_by_name,self.asset_name)
                        else:
                            print('fetching original premium asset id...')
                            self.future = submit_task(self,'Fetching original premium asset id...',network.get_premium_asset_id_by_name,self.asset_name)
                    elif self.future.done():
                        
                        self.asset_server_data = self.future.result()
                        
                        if self.is_premium:
                            if self.asset_server_data:
                                self.asset_server_data =self.asset_server_data[0]
                                # print('self.asset_server_data: ',self.asset_server_data)
                            else:
                                print(f'no premium asset found with name: {self.asset_name}')
                                self.cancel(context)
                        self.future = None
                    return{'PASS_THROUGH'}
                if self.asset_server_data: 
                    
                    original_id = self.asset_server_data['id']
                    size = int(self.asset_server_data['size'])
                    asset_name = self.asset_server_data['name']
                    asset_size=f"size: {round(size/1024)}kb" if round(size/1024)<1000 else f"size: {round(size/1024/1024,2)}mb "
                    if self.future == None:
                        print('downloading original asset...')
                        progress.init(context,float(size),'Syncing assets...')
                        addFileProgress(context,self.asset_name,0,asset_size)
                        bpy.ops.bu.display_sync_progress('INVOKE_DEFAULT')
                        self.future = submit_task(self,'Downloading original asset...',DownloadFile,self,context,original_id,asset_name,size,self.is_placeholder,self.target_lib,context.workspace,self.downloaded_sizes)
                        
                    elif self.future.done():
                        print('download done...')
                        file_name = self.future.result()
                        print(f'Downloaded original file: {file_name}')
                        context.view_layer.update()
                        # self.refresh_library()
                        # bpy.ops.bu.refresh_library('EXEC_DEFAULT')
                        wm = context.window_manager
                        wm.event_timer_remove(self._timer)
                        self.future = None
                        # self.redraw(context)
                        
                        sync_manager.SyncManager.finish_sync(BU_OT_DownloadOriginalCore.bl_idname)
                        self.task_manager.update_task_status(f"Downloaded original asset: {self.asset_name}")
                        self.taskmanager_cleanup(context,self.task_manager)       
                        drag_drop_handler.replace_placeholder_asset(context,self.asset_name)

                        progress.end(context)
                    
                        return {'FINISHED'}
                
            except Exception as e:
                print(f"An error occurred: {e}")
                addon_logger.addon_logger.error(e)
                bpy.ops.error.custom_dialog('INVOKE_DEFAULT',title='Error in downloading original asset', error_message=str(e))
                self.cancel(context)
                
        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self._timer is not None:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
        sync_manager.SyncManager.finish_sync(BU_OT_DownloadOriginalCore.bl_idname)
        if self.task_manager:
            self.taskmanager_cleanup(context,self.task_manager)
        return {'FINISHED'}


    def taskmanager_cleanup(self,context,task_manager_instance):
        if task_manager_instance:
            task_manager_instance.update_task_status(f'')
            task_manager_instance.set_done(True)
            task_manager_instance.shutdown()
            task_manager_instance = None

    def redraw(self, context):
        scr = bpy.context.screen
        areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
        regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            areas[0].tag_redraw()

    def refresh_library(self):
        scr = bpy.context.screen
        areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
        regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            print('refresh library')
            bpy.ops.asset.library_refresh()


def submit_task(self,text,function, *args, **kwargs):
    
    self.task_manager.update_task_status(text)
    task_with_args = partial(function, *args, **kwargs)
    self.future = self.task_manager.executor.submit(task_with_args)
    self.task_manager.futures.append(self.future)
    return self.future

classes=(
    BU_OT_DownloadOriginalCore,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)