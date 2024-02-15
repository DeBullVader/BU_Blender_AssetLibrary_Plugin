import bpy
import os
from .utils import addon_info,version_handler,sync_manager
from mathutils import Vector
from .ui.library_tools_ui import BU_PT_AB_LibrarySection



def drawUploadTarget(self,context):
    addon_prefs=addon_info.get_addon_name().preferences
    current_library_name = version_handler.get_asset_library_reference(context)
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
    addon_prefs.gumroad_premium_licensekey = '' #Temporary test key


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
#
def switch_bu_libs_debug_mode(dir_path,lib_name):
    addon_prefs = addon_info.get_addon_prefs()
    if addon_prefs.debug_mode:
        lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
        if lib:
            lib.path = os.path.join(dir_path,'TEST_'+lib_name)
            if not os.path.exists(lib.path):
                os.mkdir(lib.path)
            lib.name = 'TEST_'+lib_name
    else:
        test_lib_name = 'TEST_'+lib_name
        lib =bpy.context.preferences.filepaths.asset_libraries.get(test_lib_name)
        if lib:
            lib.path = os.path.join(dir_path,lib_name)
            lib.name = lib_name

class BU_OT_DebugMode(bpy.types.Operator):
    '''Testing operator Debug mode'''
    bl_idname = "bu.debug_mode"
    bl_label = "Debug mode"
    bl_description = "Debug mode"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_prefs()
        if addon_prefs.lib_path == '':
            cls.poll_message_set('Please first setup your librarie paths')
            return False
        return True

    def execute(self, context):
        BU_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium')
        addon_prefs=addon_info.get_addon_name().preferences
        addon_prefs.debug_mode = not addon_prefs.debug_mode
        addon_prefs.is_admin = addon_prefs.debug_mode
        # print('debug_mode',addon_prefs.debug_mode)
        # print('is_admin',addon_prefs.is_admin)
        dir_path = addon_prefs.lib_path
        for lib_name in BU_lib_names:
            test_lib_name = 'TEST_'+lib_name
            if addon_prefs.debug_mode:
                switched = addon_info.try_switch_to_library(dir_path,lib_name,test_lib_name)
                if not switched:
                    addon_info.remove_library_from_blender(lib_name)
                    addon_info.add_library_to_blender(dir_path,test_lib_name)
            else:
                switched = addon_info.try_switch_to_library(dir_path,test_lib_name,lib_name)
                if not switched:
                    addon_info.remove_library_from_blender(test_lib_name)
                    addon_info.add_library_to_blender(dir_path,lib_name)
        addon_info.set_upload_target(self,context)
        addon_info.set_drive_ids(context)
        scr = bpy.context.screen
        areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
        regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            print('refresh library test')
            bpy.ops.asset.library_refresh()      
        return {'FINISHED'}
    
def draw_debug(self,context):
    bu_lib = addon_info.get_bu_lib_names()
    bu_lib = bu_lib +('LOCAL',)
    if version_handler.get_asset_library_reference(context).removeprefix('TEST_') in bu_lib:
        addon_prefs =addon_info.get_addon_name().preferences
        row = self.layout.row()
        row.alignment = 'LEFT'
        row.operator("bu.debug_mode", text="Debug mode", depress=True if addon_prefs.debug_mode else False, icon='SYSTEM',)

class AdminPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Admin"
    bl_label = 'Admin panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe'
    bl_options = {'DEFAULT_CLOSED'}
    

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
        scr = bpy.context.screen
        areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
        regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):

            current_library_name = version_handler.get_asset_library_reference(context)
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

            box.operator('bu.test_op', text='Test set operator')
            # box.operator('bu.test_op2', text='test_op2')
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
        
from .comms import validator
    
def new_GeometryNodes_group():
    ''' Create a new empty node group that can be used
        in a GeometryNodes modifier.
    '''
    node_group = bpy.data.node_groups.new('GeometryNodes', 'GeometryNodeTree')
    inNode = node_group.nodes.new('NodeGroupInput')
   
    outNode = node_group.nodes.new('NodeGroupOutput')
    node_group.outputs.new('NodeSocketGeometry', 'Geometry')
    node_group.inputs.new('NodeSocketGeometry', 'Geometry')

    node_group.links.new(inNode.outputs['Geometry'], outNode.inputs['Geometry'])
    inNode.location = Vector((-1.5*inNode.width, 0))
    outNode.location = Vector((1.5*outNode.width, 0))
    return node_group

class BU_OT_TEST_OP2(bpy.types.Operator):
    '''Testing operator'''
    bl_idname = "bu.test_op2"
    bl_label = "Test operator"
    bl_description = "Test operator"
    bl_options = {'REGISTER'}

    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    input: bpy.props.StringProperty()
    test2 ='bla2'
    def execute(self, context):
        depsgraph = bpy.context.evaluated_depsgraph_get()

        scr = bpy.context.screen
        areas = [area for area in scr.areas if area.type == 'OUTLINER']
        regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            selected_ids = context.selected_ids
        
        for asset in selected_ids:
            if hasattr(asset, 'material_slots'):
                for slot in asset.material_slots:
                    print(slot.material.__dir__())
                    mat_eval = slot.material.evaluated_get(depsgraph)
                    print(mat_eval)
            
            # print(asset.full_path)

        # geonode = new_GeometryNodes_group()
        # geonode.name ='ItsATestBro'
        return {'FINISHED'}
    
    
class BU_OT_TEST_OP(bpy.types.Operator):
    '''Testing operator'''
    bl_idname = "bu.test_op"
    bl_label = "Test operator"
    bl_description = "Test operator"
    bl_options = {'REGISTER'}

    l_input: bpy.props.StringProperty(default='bla1')

    test = 'bla'
    
    def execute(self, context):

        for area in bpy.context.screen.areas:
            if area.ui_type == 'ASSETS':
                for region in area.regions:
                    print(region.type)
                print('refresh library')
                # area.spaces.active.params.asset_library_reference = current_lib_name
                with bpy.context.temp_override(area=area):
                    bpy.ops.asset.library_refresh()
        # scr = bpy.context.screen
        # areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
        # regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        # with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            
        #     print('refresh library')
        #     bpy.ops.asset.library_refresh()
        return {'FINISHED'}
    
    # def draw(self, context):
    #     layout = self.layout
    #     layout.prop(self, "l_input")

    # def invoke(self, context, event):
    #     return context.window_manager.invoke_props_dialog(self, width= 300)

def draw_test_op(self, context):
    layout = self.layout
    layout.operator('bu.test_op2')


 
classes =(
    AdminPanel,
    # BU_PT_AB_AdminPanel,
    DownloadSettings_Panel,
    BU_OT_DebugMode,
    BU_OT_TEST_OP,
    BU_OT_TEST_OP2,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(draw_debug)

    # BU_PT_AB_LibrarySection.prepend(draw_debug)
    # bpy.types.ASSETBROWSER_MT_editor_menus.append(draw_test_op) # test operator
    
    defaults()

def unregister():
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(draw_debug)
    # BU_PT_AB_LibrarySection.remove(draw_debug)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        

    