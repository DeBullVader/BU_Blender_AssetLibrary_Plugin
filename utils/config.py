import bpy
from . import addon_info
from .constants import (
    core_lib_folder_id, 
    ph_core_lib_folder_id,
    test_core_lib_folder_id,
    ph_test_core_lib_folder_id,
    user_upload_folder_id
)
    
class config_props(bpy.types.AddonPreferences):
    addon_prefs = addon_info.get_addon_name().preferences

    upload_folder_id: bpy.props.StringProperty(
        name="Parent Folder",
        description="Google Drive Parent Folder ID",
        default=user_upload_folder_id
    )



    upload_placeholder_folder_id: bpy.props.StringProperty(
        name="Parent Folder",
        description="Google Drive Parent Folder ID",
        default=ph_test_core_lib_folder_id 
    )

    test_upload_folder_id: bpy.props.StringProperty(
        name="Parent Folder",
        description="Google Drive Parent Folder ID",
        default=test_core_lib_folder_id
    )
    test_upload_placeholder_folder_id: bpy.props.StringProperty(
        name="Parent Folder",
        description="Google Drive Parent Folder ID",
        default=ph_test_core_lib_folder_id
    )

    download_folder_id: bpy.props.StringProperty(
        name="Download Folder ID",
        description="Google Drive Download Folder ID",
        default=core_lib_folder_id 
        
    )


    download_folder_id_placeholders: bpy.props.StringProperty(
        name="Placeholder Download Folder ID",
        description="Google Drive Placeholder Download Folder ID",
        default=ph_core_lib_folder_id 
        
    )
    download_catalog_folder_id: bpy.props.StringProperty(
        name="Placeholder Download Folder ID",
        description="Google Drive Placeholder Download Folder ID",
        default=ph_core_lib_folder_id    
    )

    download_target_lib: bpy.props.StringProperty(
        name="Download target",
        description="Target librarie we try to download from",  
    )

    debug_mode: bpy.props.BoolProperty(
        name="Debug mode",
        description="Enable debug mode",
        default=False,
    )

    min_chunk_size: bpy.props.IntProperty(
        name="Min Chunk Size",
        description="Min Chunk Size",
        default=256,
    )

    max_chunk_size: bpy.props.IntProperty(
        name="Max Chunk Size",
        description="Max Chunk Size",
        default=1024,
    )

    chunk_size_percentage: bpy.props.FloatProperty(
        name="Chunk Size Percentage",
        description="Chunk Size Percentage",
        min=1,
        max=100,
        default=20,
    )

