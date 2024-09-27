import math
import bpy
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import threading
from bpy.props import *
task_manager_instance = None 

class TaskManager:
    def __init__(self):
        self.lock = Lock()  # A lock to ensure thread safety when updating task status
        self.is_done_flag = False
        self.executor = ThreadPoolExecutor(max_workers=20)  # Initialize the ThreadPoolExecutor here
        self.update_ui_task = None
        self.futures = []
        self.requested_cancel = False
        self.active_threads = []

        self.status_text = 'Initializing tasks...'
        self.status_subtask_text = 'Initializing subtasks...'
        self.total_tasks = 0
        self.completed_tasks = 0
        self.total_sub_tasks = 0
        self.completed_sub_tasks = 0
        self.progress_percent = 0

    def set_progress_subtasks_values(self):
        self.progress_percent = math.floor(self.completed_sub_tasks / max(1, self.total_sub_tasks) * 100)
    
    def update_task_status(self, status_text):
        with self.lock:
            self.status_text = status_text

    def get_active_threads(self):
        """Get information about active threads."""
        with self.lock:
            return self.active_threads

    def increment_active_threads(self):
        """Increment the count of active threads."""
        with self.lock:
            self.active_threads.append(threading.currentThread().getName())

    def decrement_active_threads(self):
        """Decrement the count of active threads."""
        with self.lock:
            if threading.currentThread().getName() in self.active_threads:
                self.active_threads.remove(threading.currentThread().getName())
    # ---- Currently not used yet --------------------------        
    def update_subtask_status(self, status_subtask_text):
        with self.lock:
            self.status_subtask_text = status_subtask_text

    def set_total_tasks(self, tasks):
        with self.lock:
            self.total_tasks = tasks

    def increment_completed_tasks(self):
        with self.lock:
            self.completed_tasks += 1
    
    def reset_subtasks_count(self):
        self.total_sub_tasks = 0
        self.completed_sub_tasks = 0
    def set_total_sub_tasks(self, tasks):
        with self.lock:
            self.total_sub_tasks += tasks

    def increment_completed_sub_tasks(self):
        with self.lock:
            self.completed_sub_tasks += 1
     # ---- Above functions Currently not used yet --------------------------        
    def shutdown(self):
        print("Shutting down TaskManager...")
        self.executor.shutdown(wait=False)

    def is_done(self):
        """Check if all tasks are done."""
        return self.is_done_flag
    
    def set_done(self, is_done):
        self.is_done_flag = is_done

    def is_cancelled(self):
        return self.requested_cancel


class InitializeTaskManagerOperator(bpy.types.Operator):
    bl_idname = "wm.initialize_task_manager"
    bl_label = "Initialize Task Manager"

    def execute(self, context):
        try:
            global task_manager_instance 
            task_manager_instance = TaskManager()
            print("TaskManager initialized.")
        except Exception as e:
            print(f"An error occurred during TaskManager initialization: {e}")
        return {'FINISHED'}


classes=(
    InitializeTaskManagerOperator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
# Don't forget to unregister these properties when you're done
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
   

    