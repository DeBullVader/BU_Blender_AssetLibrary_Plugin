import bpy
import textwrap

class DownloadException(Exception):
    """Raised when an error occurs during downloading."""
    def __init__(self, message="An error occurred during downloading"):
        self.message = message
        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
        super().__init__(self.message)

class UploadException(Exception):
    """Raised when an error occurs during uploading."""
    def __init__(self, message="An error occurred during upload"):
        self.message = message
        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
        super().__init__(self.message)

class SyncException(Exception):
    """Raised when an error occurs during syncing."""
    def __init__(self, message="An error occurred during syncing"):
        self.message = message
        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
        super().__init__(self.message)

class FolderManagementException(Exception):
    """Raised when an error occurs during syncing."""
    def __init__(self, message="An error occurred during Folder management"):
        self.message = message
        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
        super().__init__(self.message)

class LicenseException(Exception):
    """Raised when an error occurs during license validation."""
    def __init__(self, message="An error occurred during license validation"):
        self.message = message
        # bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
        super().__init__(self.message)

class GoogleServiceException(Exception):
    """Raised when an error occurs during google service creation."""
    def __init__(self, message="An error occurred during google service creation"):
        self.message = message
        bpy.ops.error.custom_dialog('INVOKE_DEFAULT', error_message=str(message)) 
        super().__init__(self.message)

class ERROR_OT_custom_dialog(bpy.types.Operator):
    bl_idname = "error.custom_dialog"
    bl_label = "Error Message Dialog"
    error_message: bpy.props.StringProperty()
    title: bpy.props.StringProperty()

        
    def _label_multiline(self,context, text, parent):
        wrapper = textwrap.TextWrapper(width=50 )
        text_lines = wrapper.wrap(text=text)
        for text_line in text_lines:
            parent.label(text=text_line,)

    def draw(self, context):
        self.layout.label(text=self.title)
        intro_text = self.error_message
        self._label_multiline(
        context=context,
        text=intro_text,
        parent=self.layout
        )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width= 300)
    
classes =(
    ERROR_OT_custom_dialog,
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    