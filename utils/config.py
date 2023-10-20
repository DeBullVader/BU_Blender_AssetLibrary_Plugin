import bpy
from . import addon_info
class config_props(bpy.types.AddonPreferences):
    
    upload_parent_folder_id: bpy.props.StringProperty(
        name="Parent Folder",
        description="Google Drive Parent Folder ID",
        default="1Jtt91WrtRciaE7bPoknAQVqTIbs31Onq" #Core actual
        
    )

    download_folder_id: bpy.props.StringProperty(
        name="Download Folder ID",
        description="Google Drive Download Folder ID",
        default="1kjapdI8eWFHg7kgUwP6JGQebBwNNcIAQ" #Core 
        
    )

    download_folder_id_placeholders: bpy.props.StringProperty(
        name="Placeholder Download Folder ID",
        description="Google Drive Placeholder Download Folder ID",
        default="12VlRZmZ9yE_Pwg6PWk2_0fOihCL7e-jo" #Core original
        
    )
    
    get_catalog_file: bpy.props.StringProperty(
        name="Gets the catalog file for current file",
        description="Get the catalog file from the server",
        default="wm.copy_catalog_file"
    )
    
    download_target_lib: bpy.props.StringProperty(
        name="Download target",
        description="Target librarie we try to download to",  
    )

    debug_mode: bpy.props.BoolProperty(
        name="Debug mode",
        description="Enable debug mode",
        default=True,
    )