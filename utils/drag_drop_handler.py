import bpy,io,os
from bpy.app.handlers import persistent,depsgraph_update_post
from bpy.types import Context, Event,bpy_prop_collection
from bpy_extras import view3d_utils
from . import sync_manager,addon_info,progress,version_handler
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        UIList,
        AddonPreferences,
        )
from bpy.props import (
        IntProperty,
        PointerProperty,
        CollectionProperty,
        StringProperty,
        )


                
class BU_OT_original_example(bpy.types.Operator):
    """Access original object and do something with it"""
    bl_label = "DEG Access Original Object"
    bl_idname = "bu.original_example"
    
    text =''

    @staticmethod
    def get_main_region(context):
        for region in context.area.regions:
            print(region.type)
            if region.type == 'WINDOW':
                return region
        return None
    def modal(self, context, event):
        context.view_layer.update()
        region = self.get_main_region(context)
        if not region:
            return {'FINISHED'}


        if self.text:
            print(self.text)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        print('called')
        

        # context.view_layer.update()
        selected_assets =get_selected_assets(bpy.context)
        if selected_assets:
            print('asset ',selected_assets)
            deselect_all()
        bpy.app.timers.register(asset_placeholder_check)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width= 300)



def check_for_placeholders(asset):
    if asset:
        metadata = asset.metadata if bpy.app.version >= (4,0,0) else asset.asset_data
        if 'Placeholder' in metadata.tags:
            print(f'this is a placeholder {asset.name} ')
            return True
        return False
            
def deselect_all():
    for window in bpy.context.window_manager.windows:
        scr = window.screen
        for area in scr.areas:
            if area.type == 'FILE_BROWSER':
                with bpy.context.temp_override(window=window, area=area):
                    print('deselect all')
                    bpy.ops.file.select_all(action='DESELECT')
def refresh_library(context):
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        print('refresh library test')
        bpy.ops.asset.library_refresh()

def redraw(context):
    if context.screen is not None:
        for a in context.screen.areas:
            if a.type == 'FILE_BROWSER':
                print('redraw')
                a.tag_redraw()

def search(ID):
    def users(col):
        ret =  tuple(repr(o) for o in col if o.user_of_id(ID))
        return ret if ret else None
    return filter(None, (
        users(getattr(bpy.data, p)) 
        for p in  dir(bpy.data) 
        if isinstance(
                getattr(bpy.data, p, None), 
                bpy_prop_collection
                )                
        )
        )
def replace_placeholder_asset(context,asset_name,asset_path):
    try:
        asset_dir,ph_asset_name = os.path.split(asset_path)
        asset_original_path = os.path.join(asset_dir,asset_name+'.blend')
        print('called replace placeholder asset')

        for asset in bpy.context.scene.selected_bu_assets:
            if asset_name in asset.name:
                
                if asset.id_type == 'OBJECT':
                    print('called obj')
                    to_replace = bpy.context.scene.objects.get(asset.name+'_ph')
                    blend_dir =os.path.join(asset_original_path,'Object')
                    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_name,clear_asset_data=True,active_collection=True)
                    original_asset = bpy.data.objects[asset.name]
                    original_asset.matrix_world = to_replace.matrix_world
                    bpy.context.collection.objects.unlink(to_replace)
                    bpy.context.view_layer.update()

                if asset.id_type == 'MATERIAL':
                    to_replace = bpy.data.materials[asset.name+'_ph']
                    blend_dir =os.path.join(asset_original_path,'Material')
                    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_name,clear_asset_data=True)
                    original_mat = bpy.data.materials[asset.name]
                    user_map = bpy.data.user_map(subset=[to_replace])
                    users = user_map.get(to_replace, None)
                    for user in users:
                        obj = bpy.data.objects.get(user.name)
                        for slot in obj.material_slots:
                            if slot.material == to_replace:
                                slot.material = original_mat

                if asset.id_type == 'COLLECTION':
                    #TODO add option how to handle collections: instance or as collection
                    instanced_ph = bpy.data.objects[asset_name+'_instance_ph']
                    if not instanced_ph:
                        raise Exception(f'Could not find Instanced object: {asset_name}')
                    col_ph = bpy.data.collections[asset_name+'_ph']
                    parent_col =instanced_ph.users_collection[0]
                
                    blend_dir =os.path.join(asset_original_path,'Collection')
                    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_name,clear_asset_data=True,autoselect=True)
                    
                    original_asset = bpy.data.collections[asset_name]
                    # parent_col.children.link(original_asset)
                    original_asset_top_level =[obj for obj in original_asset.all_objects if obj.parent is None]
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in original_asset_top_level:
                        obj.matrix_world.translation = instanced_ph.matrix_world.to_translation()
                    for obj in original_asset.all_objects:
                        obj.select_set(True)
                    parent_col.objects.unlink(instanced_ph)
  
                if asset.id_type == 'NODETREE':
                    to_replace = bpy.data.node_groups[asset_name+'_ph']
                    blend_dir =os.path.join(asset_original_path,'NodeTree')
                    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_name,clear_asset_data=True)
                    original_asset = bpy.data.node_groups[asset_name]
                    user_map = bpy.data.user_map(subset=[to_replace])
                    users = user_map.get(to_replace, None)
                    for user in users:
                        obj = bpy.data.objects.get(user.name)
                        obj.modifiers[asset.name].node_group = original_asset
        #reset timer
        reasign_ph_check_timer()
    except Exception as e:
        print(f"An error occurred replacing: {e}")
        reasign_ph_check_timer()
@persistent
def reasign_ph_check_timer():
    if bpy.app.timers.is_registered(asset_placeholder_check):
        bpy.app.timers.unregister(asset_placeholder_check)
    bpy.app.timers.register(asset_placeholder_check)

def get_asset_full_path(asset):
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'FILE_BROWSER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        if bpy.app.version >= (4,0,0):
            return asset.full_library_path
        else:
            wm = bpy.context.window_manager
            return wm.asset_path_dummy

def get_selected_assets(context):
    # scr = bpy.context.screen
    # areas = [area for area in scr.areas if area.type == 'FILE_BROWSER' and area.ui_type =='ASSETS']
    # regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    # with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
    for area in bpy.context.screen.areas:
        if area.ui_type == 'ASSETS':
            # area.spaces.active.params.asset_library_reference = current_lib_name
            with bpy.context.temp_override(area=area):
                current_library_name =version_handler.get_asset_library_reference(context)
                bu_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium','TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium','ALL')
                if current_library_name in bu_lib_names:
                    assets = context.selected_assets if bpy.app.version >= (4, 0, 0) else context.selected_asset_files
                    if assets:
                        return assets
                return None

def asset_placeholder_check():
    try:
        if bpy.context.scene.selected_bu_assets:
            bpy.context.scene.selected_bu_assets.clear()
        
        selected_assets =get_selected_assets(bpy.context)
        if selected_assets:
            data_collections = {
                'OBJECT': bpy.data.objects,
                'MATERIAL': bpy.data.materials,
                'NODETREE': bpy.data.node_groups,
                'COLLECTION': bpy.data.collections,
            }
            for asset in selected_assets:
                collection = data_collections.get(asset.id_type)
                asset_path =get_asset_full_path(asset)
            
                if collection and asset.name in collection: 
                    ph_asset = collection[asset.name]
                    isplaceholder =check_for_placeholders(asset)
                    if isplaceholder:
                        bu_selected_assets =bpy.context.scene.selected_bu_assets.add()
                        bu_selected_assets.name = asset.name
                        bu_selected_assets.id_type = asset.id_type
                        ph_asset.name = f'{asset.name}_ph'
                    
                        if asset.id_type == 'COLLECTION':
                            if asset.name not in bpy.data.objects:
                                bpy.ops.object.collection_external_asset_drop(use_instance=True,collection=asset.name+'_ph')
                            
                            instanced_ph = bpy.data.objects[asset.name]
                            instanced_ph.name = f'{asset.name}_instance_ph'
                        bpy.ops.bu.download_original_core('EXEC_DEFAULT',asset_name=asset.name,asset_path=asset_path)
                        return None           
        return 1
    except Exception as e:
        deselect_all()
        print(f"An error occurred in asset_placeholder_check: {e}")
        print('deselected asset and restarted timer')
        return 1

class selected_bu_assets(PropertyGroup):
    asset_name: StringProperty()
    id_type: StringProperty()
    asset_path:StringProperty(subtype='DIR_PATH')

class BU_OT_RefreshLibrary(bpy.types.Operator):
    bl_idname = "bu.refresh_library"
    bl_label = "Refresh library"

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.ui_type == 'ASSETS':
                # area.spaces.active.params.asset_library_reference = current_lib_name
                with bpy.context.temp_override(area=area):
                    # area.spaces.active.params.asset_library_reference ='LOCAL'
                    # area.spaces.active.params.asset_library_reference ='BU_AssetLibrary_Core'
                    print('refresh library')
                    bpy.ops.asset.library_refresh()
        return {'FINISHED'}

            
def register():

    # bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    if not bpy.app.timers.is_registered(asset_placeholder_check):
        bpy.app.timers.register(asset_placeholder_check)
    bpy.utils.register_class(selected_bu_assets)
    bpy.utils.register_class(BU_OT_RefreshLibrary)
    bpy.types.Scene.selected_bu_assets = bpy.props.CollectionProperty(type=selected_bu_assets)

def unregister():
    bpy.utils.unregister_class(BU_OT_RefreshLibrary)
    bpy.utils.unregister_class(selected_bu_assets)
    if bpy.app.timers.is_registered(asset_placeholder_check):
        bpy.app.timers.unregister(asset_placeholder_check)
    del bpy.types.Scene.selected_bu_assets



