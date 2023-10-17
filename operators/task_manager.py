import math
import bpy
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
task_manager_instance = None 

class TaskManager:
    def __init__(self):
        self.lock = Lock()  # A lock to ensure thread safety when updating task status
        self.is_done_flag = False
        self.executor = ThreadPoolExecutor(max_workers=20)  # Initialize the ThreadPoolExecutor here
        self.update_ui_task = None
     
    def set_status_default_values(self,context):
        bpy.context.scene.status_text = 'Initializing tasks...'
        bpy.context.scene.completed_tasks = 0
        bpy.context.scene.total_tasks = 0
        bpy.context.scene.status_subtask_text ='Initializing subtasks...'
        bpy.context.scene.completed_sub_tasks = 0
        bpy.context.scene.total_sub_tasks = 0

    def set_progress_subtasks_values(self):
        bpy.context.scene.progress_percent = math.floor(bpy.context.scene.completed_sub_tasks / max(1, bpy.context.scene.total_sub_tasks) * 100)
    def update_task_status(self, status_text):
        with self.lock:
            bpy.context.scene.status_text = status_text
            
    def update_subtask_status(self, status_subtask_text):
        with self.lock:
            bpy.context.scene.status_subtask_text = status_subtask_text

    def set_total_tasks(self, tasks):
        with self.lock:
            bpy.context.scene.total_tasks = tasks

    def increment_completed_tasks(self):
        with self.lock:
            bpy.context.scene.completed_tasks += 1
    
    def reset_subtasks_count(self):
        bpy.context.scene.total_sub_tasks = 0
        bpy.context.scene.completed_sub_tasks = 0
    def set_total_sub_tasks(self, tasks):
        with self.lock:
            bpy.context.scene.total_sub_tasks += tasks

    def increment_completed_sub_tasks(self):
        with self.lock:
            bpy.context.scene.completed_sub_tasks += 1

    def shutdown(self):
        self.executor.shutdown(wait=False)

    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done

class InitializeTaskManagerOperator(bpy.types.Operator):
    bl_idname = "wm.initialize_task_manager"
    bl_label = "Initialize Task Manager"

    def execute(self, context):
        global task_manager_instance 
        task_manager_instance = TaskManager()
        try:
            task_manager_instance.set_status_default_values(context)
        except Exception as e:
            print(f"An error occurred: {e}")
        return {'FINISHED'}
    

def register():
    bpy.utils.register_class(InitializeTaskManagerOperator)
    bpy.types.Scene.status_text = bpy.props.StringProperty(
        name="Status Text",
        description="Text to display the current status",
        default=""
    )

    bpy.types.Scene.completed_tasks = bpy.props.IntProperty(
        name="Completed Tasks",
        description="Number of completed tasks",
        default=0
    )

    bpy.types.Scene.total_tasks = bpy.props.IntProperty(
        name="Total Tasks",
        description="Total number of tasks",
        default=0
    )

    bpy.types.Scene.status_subtask_text = bpy.props.StringProperty(
        name="Status Subtask Text",
        description="Text to display the status of the subtask",
        default=""
    )

    bpy.types.Scene.completed_sub_tasks = bpy.props.IntProperty(
        name="Completed Subtasks",
        description="Number of completed subtasks",
        default=0
    )

    bpy.types.Scene.total_sub_tasks = bpy.props.IntProperty(
        name="Total Subtasks",
        description="Total number of subtasks",
        default=0
    )

    bpy.types.Scene.progress_percent = bpy.props.IntProperty(
        name="Progress", 
        description="Progression subtasks",
        default=0) 

# Don't forget to unregister these properties when you're done
def unregister():
    bpy.utils.unregister_class(InitializeTaskManagerOperator)
    del bpy.types.Scene.status_text
    del bpy.types.Scene.completed_tasks
    del bpy.types.Scene.total_tasks
    del bpy.types.Scene.status_subtask_text
    del bpy.types.Scene.completed_sub_tasks
    del bpy.types.Scene.total_sub_tasks
    del bpy.types.Scene.progress_percent

    