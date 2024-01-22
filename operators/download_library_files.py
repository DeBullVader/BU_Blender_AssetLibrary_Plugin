
# from __future__ import print_function
import bpy,blf,os,shutil,math
from bpy.types import Context
from .file_managment import AssetSync
from ..utils import addon_info,exceptions,progress,sync_manager
from . import task_manager
from ..utils.addon_logger import addon_logger
from ..utils import version_handler



class BU_OT_Download_Original_Library_Asset(bpy.types.Operator):
    """Download the original asset of the selected previews (max 5)"""
    bl_idname = "bu.download_original_asset"
    bl_label = "Download origiinal asset"
    bl_options = {"REGISTER"}
    
    _timer = None
    poll_message = ""
    requested_cancel = False
    selected_asset = None
    
    @classmethod
    def poll(cls, context):
        selected_assets = context.selected_assets if version_handler.latest_version(context) else context.selected_asset_files
        addon_prefs= addon_info.get_addon_name().preferences
        current_library_name = version_handler.get_asset_library_reference(context)
        payed = addon_prefs.payed
        if payed == False and current_library_name ==addon_info.get_lib_name(True,addon_prefs.debug_mode):
            cls.poll_message ='Please input a valid BUK premium license key'
            cls.poll_message_set(cls.poll_message)
            return False
        if not selected_assets:
            cls.poll_message ='Please select at least one asset to download'
            cls.poll_message_set(cls.poll_message)
            return False
        if selected_assets:
            if len(selected_assets)>5:
                cls.poll_message ='Only 5 assets are allowed to can be downloaded at once.'
                cls.poll_message_set(cls.poll_message)
                return False
        if sync_manager.SyncManager.is_sync_in_progress():
            # Enable the operator if it's the one currently running the sync
            if not sync_manager.SyncManager.is_sync_operator(cls.bl_idname):
                cls.poll_message ='Another sync operation is already running. Please wait or cancel it.'
                cls.poll_message_set(cls.poll_message)
                return False
        if addon_prefs.lib_path =='':
            cls.poll_message ='Please input a valid library path. Go to Asset Browser settings in the BU side panel'
            cls.poll_message_set(cls.poll_message)
            return False
       
        return True
    
    def get_poll_message(cls):
        return cls.poll_message
    
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                self.download_original_handler.sync_original_assets(context)
            except Exception as error_message:
                print(f"An error occurred: {error_message}")
                addon_logger.error(error_message)
                self.shutdown(context)
            if self.download_original_handler.is_done():
                self.shutdown(context)
                return {'FINISHED'}

            if self.requested_cancel:
                addon_logger.info('Cancelling download')
                self.shutdown(context)
                return {'FINISHED'}
            
        return {'PASS_THROUGH'}             
        
    def execute(self, context):
        sync_manager.SyncManager.start_sync(BU_OT_Download_Original_Library_Asset.bl_idname)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        try:
            self.download_original_handler = AssetSync.get_instance()
            if self.download_original_handler.current_state is None and not self.requested_cancel:
                addon_info.set_drive_ids(context)
                bpy.ops.wm.initialize_task_manager()
                self.download_original_handler.reset()
                premium_libs = ("BU_AssetLibrary_Premium", "TEST_BU_AssetLibrary_Premium")
                self.download_original_handler.target_lib = addon_info.get_target_lib(context)
                scr = bpy.context.screen
                areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
                regions = [region for region in areas[0].regions if region.type == 'WINDOW']
                with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
                    self.download_original_handler.selected_assets = context.selected_assets if bpy.app.version >= (4, 0, 0) else context.selected_asset_files
                    self.download_original_handler.isPremium = True if self.download_original_handler.target_lib.name in premium_libs else False

                self.download_original_handler.current_state ='fetch_original_asset_ids'
                bpy.ops.bu.show_download_progress('INVOKE_DEFAULT')
                addon_logger.info('Download original asset started')
            else:
                addon_logger.info('Download original asset cancelled')
                sync_manager.SyncManager.finish_sync(BU_OT_Download_Original_Library_Asset.bl_idname)
                self.download_original_handler.requested_cancel = True
                self.requested_cancel = True
                self.download_original_handler.reset()
                #Dont return {'FINISHED'} here as its handled in modal
       
        except Exception as e:
            message=(f"An error occurred trying to download original asset: {e}")
            addon_logger.error(message)
            self.shutdown(context)
            bpy.ops.error.custom_dialog("INVOKE_DEFAULT",title = "Error downloading original assets",error_message=str(e))
        return{'RUNNING_MODAL'}


    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_Download_Original_Library_Asset.bl_idname)
        taskmanager_cleanup(context,task_manager)
        progress.end(context)
        self.cancel(context) 
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


#TODO: Move progress to own file?
def draw_callback_px(self, context):
    asset_sync_instance = AssetSync.get_instance()
    status_y = 15
    x = 15
    y = status_y + 30
    text_height = 10
    progress_bar_width = 200
    progress_bar_height = 2
    
    if bpy.app.version >= (4,0,0):
        blf.size(0, 15)
    else:
        blf.size(0, 15 , 72)
        
    blf.color(0, 1.0, 1.0, 1.0,1.0)
    blf.position(0, x, status_y, 0)
    blf.draw(0, f'{context.scene.status_text}')

    for asset_name,(asset_progress,size) in asset_sync_instance.download_progress_dict.items():
        asset_name = asset_name.removesuffix('.zip')
        progress.draw_progress_bar(x, y - text_height / 2, progress_bar_width, progress_bar_height, asset_progress / 100.0)
        blf.position(0, x, y, 0)
        blf.color(0, 1.0, 1.0, 1.0,1.0)
        blf.draw(0, f"{asset_name} {size}: {asset_progress}%")
        y += text_height + 30

#TODO: Move progress to own file?
class BU_OT_ShowDownloadProgress(bpy.types.Operator):
    bl_idname = "bu.show_download_progress"
    bl_label = "Show download progress"
    bl_options = {"REGISTER"}

    _timer = None
    _handle = None
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            asset_sync_instance = AssetSync.get_instance()
            if asset_sync_instance.current_state == None:
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
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None

class BU_OT_Remove_Library_Asset(bpy.types.Operator):
    """Remove selected asses from the current library"""	
    bl_idname = "bu.remove_library_asset"
    bl_label = "Remove library asset"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        selected_assets = context.selected_assets if version_handler.latest_version(context) else context.selected_asset_files
        if not selected_assets:
            return False
        return True

    def execute(self, context):
        addonprefs = addon_info.get_addon_name().preferences
        current_library_name = version_handler.get_asset_library_reference(context)
        lib = context.preferences.filepaths.asset_libraries[current_library_name]
        bu_libs = addon_info.get_original_lib_names()
        if current_library_name in bu_libs:
            selected_assets =context.selected_assets if version_handler.latest_version(context) else context.selected_asset_files
            for asset in selected_assets:
                asset_dir = os.path.join(lib.path,asset.name)
                asset_path =os.path.join(asset_dir,asset.name+'.blend')
                ph_path =os.path.join(asset_dir,'PH_'+asset.name+'.blend')
                if os.path.exists(asset_path):
                    print('Removing ',asset.name+'.blend')
                    shutil.rmtree(asset_dir)
                    
                elif os.path.exists(ph_path):
                    print('Removing ','PH_'+asset.name+'.blend')
                    shutil.rmtree(asset_dir)
                bpy.ops.asset.library_refresh()
            if current_library_name == 'BU_AssetLibrary_Deprecated':
                deprecated_assets = os.listdir(lib.path)
                deprecated_blend_files = [asset for asset in deprecated_assets if asset.endswith('.blend')]
                if deprecated_blend_files:
                    return {'FINISHED'}
                lib_index =context.preferences.filepaths.asset_libraries.find('BU_AssetLibrary_Deprecated')
                if lib_index > -1:
                    version_handler.set_asset_library_reference(context,'ALL')
                    bpy.ops.preferences.asset_library_remove(index=lib_index)
        return {'FINISHED'}

def draw_download_asset(self, context):
    # if context.workspace.name == 'Layout':
    layout = self.layout
    bu_libs = addon_info.get_original_lib_names()
    asset_lib_ref = version_handler.get_asset_library_reference(context)
    if asset_lib_ref in bu_libs:
        layout.operator(BU_OT_Download_Original_Library_Asset.bl_idname, text='Download original asset', icon='URL')
        layout.operator("bu.remove_library_asset", text='Remove library asset', icon='URL')
   

classes =(
    BU_OT_Download_Original_Library_Asset,
    BU_OT_ShowDownloadProgress,
    BU_OT_Remove_Library_Asset,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.ASSETBROWSER_MT_context_menu.prepend(draw_download_asset)
        

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.ASSETBROWSER_MT_context_menu.remove(draw_download_asset)
        