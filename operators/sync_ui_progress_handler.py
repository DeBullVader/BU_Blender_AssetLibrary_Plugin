import bpy,gpu,blf
from gpu_extras.batch import batch_for_shader
from ..utils import addon_info,sync_manager


class fileSyncProgress(bpy.types.PropertyGroup):
    file_name: bpy.props.StringProperty()
    current_progress: bpy.props.IntProperty()
    size: bpy.props.StringProperty()

def clearFilesProgress(context):
    context.scene.files_sync_progress.clear()

def addFileProgress(context,file_name,current_progress,size):
    file_progress =context.scene.files_sync_progress.add()
    file_progress.file_name = file_name
    file_progress.current_progress = current_progress
    file_progress.size = size
    print('progress added: ',file_progress.file_name)

def updateFileProgress(context,file_name,current_progress,size):
    print('updating progress: ',file_name)
    for file_progress in context.scene.files_sync_progress:
        if file_progress.file_name == file_name:
            file_progress.current_progress = current_progress
            file_progress.size = size
            print('progress updated: ',file_progress)
            break
            

def getFileProgress(context,file_name):
    for file_progress in context.scene.files_sync_progress:
        if file_progress.file_name == file_name:
            return file_progress

def draw_progress_bar(x, y, width, height, progress):
    # Define the vertices of the progress bar background and fill
    vertices_bg = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    vertices_fill = [(x, y), (x + width * progress, y), (x + width * progress, y + height), (x, y + height)]

    # Define shaders
    if bpy.app.version >= (4,0,0):
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch_bg = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices_bg})
    batch_fill = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices_fill})

    # Draw background
    shader.bind()
    shader.uniform_float("color", (0.5, 0.5, 0.5, 1.0))  # Grey color
    batch_bg.draw(shader)

    # Draw fill
    shader.uniform_float("color", (0.0, 0.6, 1.0, 0.5))  # LightBlue
    batch_fill.draw(shader)

def draw_callback_px(self, context):
    
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
    blf.position(0, x, status_y,20)
    blf.draw(0, f'{context.scene.TM_Props.status_text}')
    for item in context.scene.files_sync_progress:

        draw_progress_bar(x, y - text_height / 2, progress_bar_width, progress_bar_height, item.current_progress / 100.0)
        blf.position(0, x, y, 50)
        blf.color(0, 1.0, 1.0, 1.0,1.0)
        blf.draw(0, f"{item.file_name} | {item.size}: {item.current_progress}%")
        y += text_height + 30


class BU_OT_DisplaySyncProgress(bpy.types.Operator):
    bl_idname = "bu.display_sync_progress"
    bl_label = "Display's sync progress in the viewport"
    bl_options = {"REGISTER"}

    _timer = None
    _handle = None
    def modal(self, context, event):
        if event.type == 'TIMER':
            if not sync_manager.SyncManager.is_sync_in_progress():
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
        try:
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        except Exception as e:
            print('Error in draw_callback_px: ', e)
            return{'CANCELLED'}
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None

classes=(
    BU_OT_DisplaySyncProgress,
    fileSyncProgress,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.files_sync_progress = bpy.props.CollectionProperty(type=fileSyncProgress)
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.files_sync_progress