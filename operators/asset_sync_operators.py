import bpy
from bpy.types import Context

from .file_managment import AssetSync
from . import task_manager
from . import file_managment
from ..utils import addon_info
from ..ui import statusbar

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
        if AssetSyncOperator.asset_sync_instance:
            return False
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            AssetSyncOperator.asset_sync_instance.sync_original_assets(context)

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
            if AssetSyncOperator.asset_sync_instance.is_done():
                AssetSyncOperator.asset_sync_instance = None
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
        except Exception as e:
            print(f"An error occurred: {e}")
        try:
            AssetSyncOperator.asset_sync_instance = AssetSync()
            AssetSyncOperator.asset_sync_instance.current_state = 'sync_original_assets'
            
            # bpy.ops.wm.sync_assets_status('INVOKE_DEFAULT')
            # AssetSyncOperator.asset_sync_instance.start_tasks()
        except Exception as e:
            print(f"An error occurred: {e}")
        
     
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class AssetSyncOperator(bpy.types.Operator):
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
        if AssetSyncOperator.asset_sync_instance:
            return False
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            AssetSyncOperator.asset_sync_instance.start_tasks(context)

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
            if AssetSyncOperator.asset_sync_instance.is_done():
                bpy.ops.asset.library_refresh()
                AssetSyncOperator.asset_sync_instance = None
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
        except Exception as e:
            print(f"An error occurred: {e}")
        try:
            AssetSyncOperator.asset_sync_instance = AssetSync()
            AssetSyncOperator.asset_sync_instance.current_state = 'fetch_assets'
        except Exception as e:
            print(f"An error occurred: {e}")
        
     
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class AssetSyncStatus(bpy.types.Operator):
    bl_idname = "wm.sync_assets_status"
    bl_label = "Sync Status"
    bl_description = "Show sync status"
    bl_options = {"REGISTER"}


    @classmethod
    def poll(cls, context):
        if not AssetSyncOperator.asset_sync_instance:
            cls.poll_message_set('Nothing is being processed.')
            return False
        elif AssetSyncOperator.asset_sync_instance.is_done():
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
        # Get progress and text to display
        # asset_sync_instance = AssetSyncOperator.asset_sync_instance
        # print(f'async instance = { task_manager.task_manager_instance}')
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

classes =(
    AssetSyncOperator,
    AssetSyncStatus
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.append(AssetSyncStatus.draw_progress)
    
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.remove(AssetSyncStatus.draw_progress)
