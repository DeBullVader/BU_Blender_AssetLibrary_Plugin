
# from __future__ import print_function
import bpy
import logging
from .file_managment import AssetSync
from ..utils import addon_info,exceptions,progress
from . import task_manager

log = logging.getLogger(__name__)

class BU_OT_Download_Original_Library_Asset(bpy.types.Operator):
    bl_idname = "bu.download_original_asset"
    bl_label = "Download origiinal asset"
    bl_options = {"REGISTER"}
    
    _timer = None
    asset_sync_instance = None
    prog = 0
    prog_text = None
    
    @classmethod
    def poll(cls, context):
        selected_assets = context.selected_asset_files
        addon_prefs= addon_info.get_addon_name().preferences
        current_library_name = context.area.spaces.active.params.asset_library_ref
        payed = addon_prefs.payed
        if payed == False and current_library_name ==addon_info.get_lib_name(True,addon_prefs.debug_mode):
            cls.poll_message_set('Please input a valid BUK premium license key')
            return False
        elif len(selected_assets)>10:
            cls.poll_message_set('Only 10 assets are allowed to can be downloaded at once.')
            return False
        elif BU_OT_Download_Original_Library_Asset.asset_sync_instance or task_manager.task_manager_instance:
            return False
        if addon_prefs.lib_path =='':
            cls.poll_message_set('Please input a valid library path. Go to Asset Browser settings in the BU side panel')
            return False
        return True
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            addon_prefs= addon_info.get_addon_name().preferences
            current_library_name = context.area.spaces.active.params.asset_library_ref
            if current_library_name == addon_info.get_lib_name(True,addon_prefs.debug_mode) :
                isPremium = True
            else:
                isPremium = False
            if BU_OT_Download_Original_Library_Asset.asset_sync_instance:
                BU_OT_Download_Original_Library_Asset.asset_sync_instance.sync_original_assets(context,isPremium)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if task_manager.task_manager_instance:
                if task_manager.task_manager_instance.is_done():
                    print('task_manager_instance is done')
                    task_manager.task_manager_instance.shutdown()
                    task_manager.task_manager_instance = None
                    if BU_OT_Download_Original_Library_Asset.asset_sync_instance:
                        print('asset_sync_instance is done')
                        BU_OT_Download_Original_Library_Asset.asset_sync_instance = None
                    bpy.ops.asset.library_refresh()
                    
            
            instances = (task_manager.task_manager_instance, BU_OT_Download_Original_Library_Asset.asset_sync_instance)
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
            BU_OT_Download_Original_Library_Asset.asset_sync_instance = AssetSync()
            BU_OT_Download_Original_Library_Asset.asset_sync_instance.current_state = 'fetch_original_asset_ids'
        except Exception as e:
            print(f"An error occurred: {e}")
        return{'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
     
def draw_download_asset(self, context):
    layout = self.layout
    layout.operator(BU_OT_Download_Original_Library_Asset.bl_idname, text='Download original asset', icon='URL')



classes =(
    BU_OT_Download_Original_Library_Asset,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.types.ASSETBROWSER_MT_context_menu.prepend(draw_download_asset)
        

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        bpy.types.ASSETBROWSER_MT_context_menu.remove(draw_download_asset)
        