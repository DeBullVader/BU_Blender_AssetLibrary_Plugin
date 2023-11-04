
# from __future__ import print_function
import bpy
import logging
import os
from bpy.types import Context
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
        if len(selected_assets)>10:
            cls.poll_message_set('Only 10 assets are allowed to can be downloaded at once.')
            return False
        if BU_OT_Download_Original_Library_Asset.asset_sync_instance or task_manager.task_manager_instance:
            cls.poll_message_set('an instance is already running. Please wait or cancel it.')
            return False
        if addon_prefs.lib_path =='':
            cls.poll_message_set('Please input a valid library path. Go to Asset Browser settings in the BU side panel')
            return False
        if not context.selected_asset_files:
            cls.poll_message_set('Please select assets to download')
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
            # BU_OT_Download_Original_Library_Asset.asset_sync_instance.current_state = 'sync_original_assets'
        except Exception as e:
            print(f"An error occurred: {e}")
            bpy.ops.bu.c
        return{'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
     


class BU_OT_Remove_Library_Asset(bpy.types.Operator):
    bl_idname = "bu.remove_library_asset"
    bl_label = "Remove library asset"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        if not context.selected_asset_files:
            return False
        return True
        
    def execute(self, context):
        addonprefs = addon_info.get_addon_name().preferences
        current_library_name = context.area.spaces.active.params.asset_library_ref
       
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
        target_lib = addon_info.get_target_lib().path
        baseName = "Coffeeplant_Small.001"
        ph_file = f'{target_lib}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
        print(ph_file)
        # if os.path.exists(ph_file):
        #     os.rename(ph_file, ph_file.removesuffix('.blend'))
               
        if baseName in bpy.context.blend_data.objects:
            obj = bpy.context.blend_data.objects.get(baseName)
            
            bpy.context.scene.collection.objects.link(obj)
            # local.asset_mark()
            bpy.ops.asset.library_refresh()
            # if obj.name == "Coffeeplant_Small.001":
            #     # local = obj.make_local()
            #     target_lib = addon_info.get_target_lib().path
                
            #     ph_file = f'{target_lib}{os.sep}{obj.name}{os.sep}PH_{obj.name}.blend'
            #     print(ph_file)
            #     if os.path.exists(ph_file):

            #         os.rename(ph_file, ph_file.removesuffix('.blend'))
            #         bpy.ops.asset.library_refresh()
                        
                
                # bpy.context.scene.collection.objects.link(obj)
                # print(local.__dir__())
                # print(obj.__dir__()) 
        return {'FINISHED'} 
     
def draw_download_asset(self, context):
    layout = self.layout
    layout.operator(BU_OT_Download_Original_Library_Asset.bl_idname, text='Download original asset', icon='URL')
    layout.operator("bu.remove_library_asset", text='Remove library asset', icon='URL')
    layout.operator("bu.append_to_scene", text='Append to scene', icon='URL')

classes =(
    BU_OT_Download_Original_Library_Asset,
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
        