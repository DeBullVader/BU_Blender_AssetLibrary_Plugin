
# from __future__ import print_function
import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
import logging
import os
import textwrap
from bpy.types import Context
from .file_managment import AssetSync
from ..utils import addon_info,exceptions,progress,sync_manager
from . import task_manager
from ..utils.addon_logger import addon_logger

log = logging.getLogger(__name__)

class BU_OT_Download_Original_Library_Asset(bpy.types.Operator):
    bl_idname = "bu.download_original_asset"
    bl_label = "Download origiinal asset"
    bl_options = {"REGISTER"}
    
    _timer = None
    poll_message = ""
    requested_cancel = False
    
    @classmethod
    def poll(cls, context):
        selected_assets = context.selected_asset_files
        addon_prefs= addon_info.get_addon_name().preferences
        current_library_name = context.area.spaces.active.params.asset_library_ref
        payed = addon_prefs.payed
        if payed == False and current_library_name ==addon_info.get_lib_name(True,addon_prefs.debug_mode):
            cls.poll_message ='Please input a valid BUK premium license key'
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

            if self.requested_cancel or self.download_original_handler.is_done():
                
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
                self.download_original_handler.current_state ='fetch_original_asset_ids'
                bpy.ops.bu.show_download_progress('INVOKE_DEFAULT')
            else:
                print("cancelled")
                sync_manager.SyncManager.finish_sync(BU_OT_Download_Original_Library_Asset.bl_idname)
                self.download_original_handler.requested_cancel = True
                self.requested_cancel = True
                self.download_original_handler.reset()
       
        except Exception as e:
            print(f"An error occurred: {e}")
            addon_logger.error(e)
            self.shutdown(context)
            bpy.ops.error.custom_dialog("INVOKE_DEFAULT",error_message=f"An error occurred: {e}")
        return{'RUNNING_MODAL'}



    def shutdown(self, context):
        sync_manager.SyncManager.finish_sync(BU_OT_Download_Original_Library_Asset.bl_idname)
        taskmanager_cleanup(context,task_manager)
        progress.end(context)
        # self.cancel_download_progress_operator(context)
        self.cancel(context) 
        bpy.ops.asset.library_refresh()
        self.requested_cancel = False

    def cancel_download_progress_operator(self, context):
        wm = context.window_manager
        if 'download_progress_operator' in wm:
            download_progress_op = wm['download_progress_operator']
            # if isinstance(download_progress_op, BU_OT_ShowDownloadProgress):
            download_progress_op.cancel(context)
            print("Stored reference is correct")
            # Remove the reference after canceling
            del wm['download_progress_operator']
            # else:
            #     # Handle the case where it's not the correct type
            #     print("Stored reference is not the correct type.")
        else:
            # Handle the case where the reference doesn't exist
            print("Stored reference doesn't exist.")

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def taskmanager_cleanup(context,task_manager):
    if task_manager.task_manager_instance:
        task_manager.task_manager_instance.update_task_status('Sync complete')
        task_manager.task_manager_instance.set_done(True)
        task_manager.task_manager_instance.shutdown()
        task_manager.task_manager_instance = None

def draw_progress_bar(x, y, width, height, progress):
    # Define the vertices of the progress bar background and fill
    vertices_bg = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    vertices_fill = [(x, y), (x + width * progress, y), (x + width * progress, y + height), (x, y + height)]

    # Define shaders
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch_bg = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices_bg})
    batch_fill = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices_fill})

    # Draw background
    shader.bind()
    shader.uniform_float("color", (0.5, 0.5, 0.5, 1.0))  # Grey color
    batch_bg.draw(shader)

    # Draw fill
    shader.uniform_float("color", (0.0, 1.0, 0.0, 1.0))  # Green color
    batch_fill.draw(shader)

def draw_callback_px(self, context):
    # Your drawing logic here
    # For example, drawing the progress text
    asset_sync_instance = AssetSync.get_instance()
    x = 15
    y = 30
    text_height = 15
    progress_bar_width = 200
    progress_bar_height = 2
    
    blf.size(0, 15, 72)
    for asset_name, progress in asset_sync_instance.download_progress_dict.items():
        draw_progress_bar(x, y - text_height / 2, progress_bar_width, progress_bar_height, progress / 100.0)
        blf.position(0, x, y, 0)
        blf.color(0, 1.0, 1.0, 1.0,1.0)
        asset_name = asset_name.removesuffix('.zip')
        blf.draw(0, f"{asset_name}: {progress}%")
        
        y += text_height + 30 

class BU_OT_ShowDownloadProgress(bpy.types.Operator):
    bl_idname = "bu.show_download_progress"
    bl_label = "Show download progress"
    bl_options = {"REGISTER"}

    _handle = None
    

    @classmethod
    def poll(cls, context):

        return True
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            asset_sync_instance = AssetSync.get_instance()
            if(asset_sync_instance.is_done() or asset_sync_instance is None):
                self.cancel(context)
                return {'FINISHED'}
            # Force a redraw of the entire UI
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    area.tag_redraw()
                    
        return {'PASS_THROUGH'}
    
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        asset_sync_instance = AssetSync.get_instance()
        if asset_sync_instance.download_progress_dict:
            for asset_name, progress in asset_sync_instance.download_progress_dict.items():
                col.label(text=f"{asset_name}: {progress}%")
            
    
    def execute(self, context):

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):  
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)  # Adjust the interval as needed
        
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        wm.modal_handler_add(self)
        # wm['download_progress_operator'] = self
        # return context.window_manager.invoke_props_dialog(self, width= 400)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
class BU_OT_Remove_Library_Asset(bpy.types.Operator):
    """Remove library asset"""	
    bl_idname = "bu.remove_library_asset"
    bl_label = "Remove library asset"
    bl_options = {"REGISTER","UNDO"}

    @classmethod
    def poll(cls, context):
        if not context.selected_asset_files:
            return False
        return True

    def execute(self, context):
        addonprefs = addon_info.get_addon_name().preferences
        current_library_name = context.area.spaces.active.params.asset_library_ref
        bu_libs = addon_info.get_original_lib_names()
        if current_library_name in bu_libs:
            for asset in context.selected_asset_files:
                asset_path = f'{addonprefs.lib_path}{os.sep}{current_library_name}{os.sep}{asset.name}{os.sep}{asset.name}.blend'
                ph_path = f'{addonprefs.lib_path}{os.sep}{current_library_name}{os.sep}{asset.name}{os.sep}PH_{asset.name}.blend'
                if os.path.exists(asset_path):
                    os.remove(asset_path)
                    bpy.ops.asset.library_refresh()
                elif os.path.exists(ph_path):
                    os.remove(ph_path)
                    bpy.ops.asset.library_refresh()

                
        return {'FINISHED'}
    



        
    
class BU_OT_AppendToScene(bpy.types.Operator):
    bl_idname = "bu.append_to_scene"
    bl_label = "Append to scene"
    bl_options = {"REGISTER"}

    def execute(self, context):

       
        catfile = 'blender_assets.cats.txt'
        addon_prefs = addon_info.get_addon_name().preferences
        current_filepath = bpy.data.filepath
        current_filepath_cat_file = os.path.join(current_filepath,catfile)
        
        if current_filepath_cat_file:
            # for window in context.window_manager.windows:
            #     screen = window.screen
            # context
            for area in context.screen.areas:
                if area.type == 'FILE_BROWSER':
                    
                    with context.temp_override(window=context.window, area=area):
                            # context.space_data.params.asset_library_ref = 'BU_AssetLibrary_Core'
                        if context.space_data.params.asset_library_ref == 'BU_AssetLibrary_Premium':
                            bpy.ops.asset.catalog_new(parent_path="")
                            bpy.ops.asset.catalog_undo()
                            bpy.ops.asset.catalogs_save()     
        return {'FINISHED'} 



def draw_download_asset(self, context):
    if context.workspace.name == 'Layout':
        layout = self.layout
        bu_libs = addon_info.get_original_lib_names()
        if context.area.spaces.active.params.asset_library_ref in bu_libs:
            layout.operator(BU_OT_Download_Original_Library_Asset.bl_idname, text='Download original asset', icon='URL')
            layout.operator("bu.remove_library_asset", text='Remove library asset', icon='URL')
   

classes =(
    BU_OT_Download_Original_Library_Asset,
    BU_OT_ShowDownloadProgress,
    BU_OT_Remove_Library_Asset,
    BU_OT_AppendToScene
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.ASSETBROWSER_MT_context_menu.prepend(draw_download_asset)
        

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.ASSETBROWSER_MT_context_menu.remove(draw_download_asset)
        