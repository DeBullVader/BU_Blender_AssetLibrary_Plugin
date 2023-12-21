import bpy
import os
import math
from bpy.types import Context
from . import addon_info
from bpy.app.handlers import persistent
from ..ui import generate_previews,asset_bbox_logic
from mathutils import Vector




def drawUploadTarget(self,context):
    addon_prefs=addon_info.get_addon_name().preferences
    current_library_name = context.area.spaces.active.params.asset_library_ref
    if current_library_name == "LOCAL":
        layout = self.layout
        row= layout.row()
        # addon_info.set_upload_target(self,context)
        row.label(text=' ') # adding some space to menu
        scene = context.scene
        row.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
    
        row.label(text='|') # adding some space to menu

def defaults():
    addon_prefs = addon_info.get_addon_name().preferences
    lib_names = addon_info.get_original_lib_names()
    addon_info.find_lib_path(addon_prefs,lib_names)
    addon_prefs.is_admin = True
    



def get_test_lib_paths():
    libs =[]
    lib_names = ['TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium']
    addon_prefs = addon_info.get_addon_name().preferences
    dir_path = addon_prefs.lib_path
    for lib_name in lib_names:
        lib_path = os.path.join(dir_path,lib_name)
        if dir_path !='':
            if lib_name in bpy.context.preferences.filepaths.asset_libraries:
                lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
                if lib.path != lib_path:
                    lib.path = lib_path
                    libs.append(lib)
                else:
                    libs.append(lib)
    return libs


    
class BU_OT_DebugMode(bpy.types.Operator):
    '''Testing operator Debug mode'''
    bl_idname = "bu.debug_mode"
    bl_label = "Debug mode"
    bl_description = "Debug mode"
    bl_options = {'REGISTER'}



    def execute(self, context):
        addon_prefs=addon_info.get_addon_name().preferences
        addon_prefs.debug_mode = not addon_prefs.debug_mode
        addon_prefs.is_admin = addon_prefs.debug_mode
        print('debug_mode',addon_prefs.debug_mode)
        print('is_admin',addon_prefs.is_admin)
        addon_info.set_upload_target(self,context)
        addon_info.set_drive_ids(context)
        # addon_info.set_upload_target(self,context)
        addon_info.add_library_paths()
        return {'FINISHED'}
    
class AdminPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Admin"
    bl_label = 'Admin panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Admin'
    

    def draw(self,context):
        test_lib_names = ('TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium')
        real_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium')
        addon_prefs =addon_info.get_addon_name().preferences
        
        layout = self.layout
        layout.label(text='Switch to test folders debug')
        layout.label(text='Enable to switch to test server folders')
        layout.operator("bu.debug_mode", text="Debug mode", depress=True if addon_prefs.debug_mode else False)
        # layout.prop(self.addonprefs, "debug_mode", text="Server Debug mode", toggle= True,)
        box = layout.box()
        
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        current_library_name = bpy.context.area.spaces.active.params.asset_library_ref
                        # print(current_library_name)
                        
                        if current_library_name in test_lib_names:
                            box.label(text='Core Test Library' if current_library_name == test_lib_names[0] else 'Premium Test Library', icon='FILE_FOLDER' )
                            box.label(text=f' download folder id: {addon_prefs.download_folder_id}' if current_library_name == test_lib_names[0] else 'download folder id: Handled in AWS')
                            box.label(text=f' download folder id placeholder: {addon_prefs.download_folder_id_placeholders}')
                        
                        elif current_library_name in real_lib_names:
                            box.label(text='Core Library' if current_library_name == real_lib_names[0] else 'Premium Library', icon='FILE_FOLDER' )
                            box.label(text=f' download folder id: {addon_prefs.download_folder_id}' if current_library_name == real_lib_names[0] else 'download folder id: Handled in AWS')
                            box.label(text=f' download folder id placeholder: {addon_prefs.download_folder_id_placeholders}')
                        elif current_library_name == 'LOCAL': 
                            box.label(text='Upload to Library', icon='FILE_NEW')
                            scene = context.scene
                            
                            box.prop(scene.upload_target_enum, "switch_upload_target", text="Upload Target")
                            box.label(text= 'Upload drive folder IDs: Test Folders' if addon_prefs.debug_mode else 'Upload drive folder IDs: Real Folders')
                            # box.label(text= 'Core'if scene.upload_target_enum.switch_upload_target == 'core_upload' else 'Premium')
                            box.label(text=f' Main folder ID: {addon_prefs.upload_folder_id}')
                            if addon_prefs.debug_mode:
                                box.label(text=f' Placeholder ID placeholder: {addon_prefs.upload_placeholder_folder_id}')
                        

                        else:
                            box.label(text = 'select CORE,Premium or current file to display folder ids')
        # layout = self.layout
        # layout.operator('bu.upload_settings', text='Upload Settings',icon='SETTINGS')

class DownloadSettings_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_DownloadSettings"
    bl_label = 'Download Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'VIEW3D_PT_BU_Admin'
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        layout.prop(addon_prefs, "min_chunk_size", text="Min Chunk Size")
        layout.prop(addon_prefs, "max_chunk_size", text="Max Chunk Size")
        layout.prop(addon_prefs, "chunk_size_percentage", text=f"Chunk Size: {addon_prefs.chunk_size_percentage}%",slider=True)

class BU_OT_TEST_OP2(bpy.types.Operator):
    '''Testing operator'''
    bl_idname = "bu.test_op2"
    bl_label = "Test operator"
    bl_description = "Test operator"
    bl_options = {'REGISTER'}

    def execute(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        debug_mode = addon_prefs.debug_mode

        obj = context.active_object
        camera = bpy.data.objects['Camera_Objects']
        scene = context.scene
        generate_previews.reset_object_scale_location(obj, scene.original_scale, scene.original_location) 
        generate_previews.adjust_object_z_location(obj)                           
        return {'FINISHED'}
    
class BU_OT_TEST_OP(bpy.types.Operator):
    '''Testing operator'''
    bl_idname = "bu.test_op"
    bl_label = "Test operator"
    bl_description = "Test operator"
    bl_options = {'REGISTER'}

    def execute(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        debug_mode = addon_prefs.debug_mode
        # for window in context.window_manager.windows:
        #     screen = window.screen
        #     for area in screen.areas:
        #         if area.type == 'FILE_BROWSER':
        #             with context.temp_override(window=window, area=area):
        #                 for item in context.scene.mark_collection:
        #                     print(item.asset.__dir__())

        obj =context.active_object
        world_bbox_corners = asset_bbox_logic.get_obj_world_bbox_corners(obj)
        print('obj world bbox corners: ',world_bbox_corners)
        for item in context.scene.mark_collection:
            max_scale = Vector(item.max_scale)
            z_rotation = math.radians(item.z_rotation)
            
            col_scale_factor =asset_bbox_logic.get_col_scale_factor(collection=item.asset,target_x_size=max_scale.x,target_y_size=max_scale.y,target_z_size=max_scale.z)
            asset_bbox_logic.scale_collection_for_render(item.asset,col_scale_factor)
            asset_bbox_logic.set_object_location_to_zero(item.asset)
            asset_bbox_logic.set_col_z_rotation(item.asset,z_rotation)
            asset_bbox_logic.set_front_lower_to_floor(item.asset)

            # print('col world bbox corners: ',world_collection_bbox_corners)
            # asset_bbox_logic.get_col_world_bbox_size(world_collection_bbox_corners)

        # # generate_previews.reset_object_scale_location(obj, obj.scale,obj.location) 
        # context.scene.original_scale = obj.scale.copy()
        # context.scene.original_location = obj.location.copy()
        # camera = bpy.data.objects['Camera_Objects']   
        # scene = context.scene           
        # # generate_previews.object_scaling(self,context, obj, camera,False)
        # scale_factor = generate_previews.get_scale_factor(obj)
                               
        # generate_previews.scale_object_for_render(obj,scale_factor)
        # generate_previews.adjust_object_z_location(obj)                               
        return {'FINISHED'}

    def execute2(self, context):
        assets = context.selected_asset_files
        asset_types =addon_info.type_mapping()
        self.data_type = None
        target_lib = addon_info.get_target_lib(context).path 
        baseName = 'NG_DispersionGlass'
        blend_file_path = f"{target_lib}{os.sep}{baseName}{os.sep}{baseName}.blend"
        result = addon_info.find_asset_by_name(baseName)
        if result:
            to_replace,datablock = result
            to_replace.name = f'{to_replace.name}_ph'
            print('to_replace',to_replace.name)
        for asset in assets:
            if asset.name == baseName:
                selected_asset = asset
                print('selected_asset',selected_asset.id_type)
                if selected_asset.id_type in asset_types:
                    self.data_type = asset_types[selected_asset.id_type]
             
        if self.data_type:
            with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
                if self.data_type in dir(data_to):
                    setattr(data_to, self.data_type, getattr(data_from, self.data_type))
            to_replace.user_remap(datablock[baseName])
            datablock.remove(to_replace)


        
   
        return {'FINISHED'}

def draw_test_op(self, context):
    layout = self.layout
    layout.operator('bu.test_op')
    
 
classes =(
    AdminPanel,
    DownloadSettings_Panel,
    BU_OT_DebugMode,
    BU_OT_TEST_OP,
    BU_OT_TEST_OP2
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # bpy.types.ASSETBROWSER_MT_editor_menus.append(draw_test_op) # test operator
    
    defaults()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # bpy.types.ASSETBROWSER_MT_editor_menus.remove(draw_test_op)
