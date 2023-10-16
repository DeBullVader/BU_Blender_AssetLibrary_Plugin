
# from __future__ import print_function
import bpy
import logging
import io
import os
from .file_managment import AssetSync
from ..utils import addon_info,exceptions
from . import task_manager
log = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

KEY_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"

assets_to_download={}

class Download_Original_Library_Asset(bpy.types.Operator):
    bl_idname = "bu.download_original_asset"
    bl_label = "Download origiinal asset"
    bl_options = {"REGISTER"}
    

    @classmethod
    def poll(cls, context):
        selected_assets = context.selected_asset_files
        addon_prefs = addon_info.get_addon_name().preferences
        uuid = addon_prefs.premium_licensekey
        if uuid == '':
            cls.poll_message_set('Please input a valid BUK premium license key')
            return False
        elif len(selected_assets)>10:
            cls.poll_message_set('Only 10 assets are allowed to can be downloaded at once.')
            return False
        return True
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            current_library_name = context.area.spaces.active.params.asset_library_ref
            if current_library_name == "BU_AssetLibrary_Premium":
                isPremium = True
            else:
                isPremium = False
            Download_Original_Library_Asset.asset_sync_instance.sync_original_assets(context,isPremium)

            # Update the UI elements or trigger a redraw.
            if context.screen is not None:
                for a in context.screen.areas:
                    if a.type == 'FILE_BROWSER':
                        a.tag_redraw()
            # Check if the AssetSync tasks are done
            if task_manager.task_manager_instance.is_done():
                task_manager.task_manager_instance.shutdown()
                task_manager.task_manager_instance = None
                Download_Original_Library_Asset.asset_sync_instance = None
                bpy.ops.asset.library_refresh()
                self.cancel(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        try:
            addon_info.set_drive_ids()
            bpy.ops.wm.initialize_task_manager()
            Download_Original_Library_Asset.asset_sync_instance = AssetSync()
            Download_Original_Library_Asset.asset_sync_instance.current_state = 'fetch_original_asset_ids'
        except Exception as e:
            print(f"An error occurred: {e}")
        # self.asset_sync_instance.sync_original_assets(context)
        return{'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
     
def draw_download_asset(self, context):
    # current_library_name = context.area.spaces.active.params.asset_library_ref
    # if current_library_name == "BU_Premium_Library":
    layout = self.layout
    layout.operator(Download_Original_Library_Asset.bl_idname, text='Download asset', icon='URL')



classes =(
    Download_Original_Library_Asset,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.types.ASSETBROWSER_MT_context_menu.prepend(draw_download_asset)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        bpy.types.ASSETBROWSER_MT_context_menu.remove(draw_download_asset)
