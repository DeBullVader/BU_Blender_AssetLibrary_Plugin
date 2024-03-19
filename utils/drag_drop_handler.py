import bpy,os
from bpy.app.handlers import persistent
from bpy.types import bpy_prop_collection
from . import version_handler
from bpy.types import PropertyGroup
from . import addon_info,addon_logger

        
from bpy.props import StringProperty,PointerProperty,BoolProperty
  
def deselect_all():
    for window in bpy.context.window_manager.windows:
        scr = window.screen
        for area in scr.areas:
            if area.type == 'FILE_BROWSER':
                with bpy.context.temp_override(window=window, area=area):
                    # print('deselect all')
                    bpy.ops.file.select_all(action='DESELECT')
                    # bpy.ops.asset.library_refresh()

def refresh_library(context):
    

    window = bpy.context.window
    scr = window.screen
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'FILE_BROWSER' and area.ui_type == 'ASSETS']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override( area=areas[0]):
        current_library_name = version_handler.get_asset_library_reference(bpy.context)
        print('current_library_name ',current_library_name)
        bpy.ops.asset.library_refresh()
        

def redraw(context):
    if context.screen is not None:
        for a in context.screen.areas:
            if a.type == 'FILE_BROWSER':
                if a.ui_type == 'ASSETS':
                    a.tag_redraw()
                    with bpy.context.temp_override(area=a):
                        bpy.ops.asset.library_refresh()

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
  
def replace_placeholder_asset(context,asset_name):
    try:
        
        for asset_entry in context.scene.selected_bu_assets:
            if asset_entry.asset_name == asset_name:
                asset_dir,ph_asset_name = os.path.split(asset_entry.asset_path)
                asset_original_path = os.path.join(asset_dir,asset_name+'.blend')  
                
                if asset_entry.id_type == 'OBJECT':
                    handle_replace_object(asset_entry,asset_original_path)

                if asset_entry.id_type == 'MATERIAL':
                    handle_replace_material(asset_entry,asset_original_path)
                    
                if asset_entry.id_type == 'COLLECTION':
                    handle_replace_collection(asset_entry,asset_original_path)

                if asset_entry.id_type == 'NODETREE':
                    handle_replace_nodetree(asset_entry,asset_original_path)
                if asset_entry.is_premium:
                    if os.path.exists(asset_original_path):
                        os.remove(asset_original_path)
                # else:
                #     print(asset_entry.asset_path)
                #     if os.path.exists(asset_entry.asset_path):
                #         pass
                #         # os.remove(asset_entry.asset_path)

        bpy.context.scene.selected_bu_assets.clear()
        bpy.context.view_layer.update()
        redraw(bpy.context)

    except Exception as e:
        error_message =f"An error occurred replacing: {e}"
        print(error_message)
        addon_logger.addon_logger.error(error_message)
        for asset_entry in context.scene.selected_bu_assets:
            asset_dir,ph_asset_name = os.path.split(asset_entry.asset_path)
            asset_original_path = os.path.join(asset_dir,asset_name+'.blend')
            if os.path.exists(asset_original_path) and asset_entry.is_premium:
                os.remove(asset_original_path)
                
            bpy.context.scene.selected_bu_assets.clear()

def handle_replace_object(asset_entry,asset_original_path):
    print('Replacing Object...')
    placeholder_asset = asset_entry.asset
    if placeholder_asset is None:
        print("Placeholder object not found in the PropertyGroup entry.")
        return

    placeholder_obj = bpy.data.objects.get(asset_entry.asset_scene_name)
    # print('placeholder_obj in handle_replace_object: ',placeholder_obj)
    blend_dir =os.path.join(asset_original_path,'Object/')
    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_entry.asset_name,clear_asset_data=True,link=False,autoselect=True)
    original_obj = bpy.data.objects.get(asset_entry.asset_scene_name.removesuffix('_ph'))
    # print('original_obj in handle_replace_object: ',original_obj)
    original_obj.matrix_world = placeholder_obj.matrix_world

    bpy.context.collection.objects.unlink(placeholder_obj)
    bpy.context.view_layer.update()
    add_asset_too_previous_states(original_obj)
    return


def handle_replace_material(asset_entry,asset_original_path):
    print('Replacing Material...')
    placeholder_mat = asset_entry.asset
    # print('placeholder_mat ',placeholder_mat)
    if not placeholder_mat:
        error =f"Placeholder material '{ asset_entry.asset.name}' not found."
        print(error)
        raise Exception(error)

    blend_dir =os.path.join(asset_original_path,'Material/')
    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_entry.asset_name,clear_asset_data=True)
    original_mat = bpy.data.materials.get(asset_entry.asset_scene_name.removesuffix('_ph'))
    
    if not original_mat:
        error = f"Original material '{asset_entry.asset_scene_name}' not found."
        print(error)
        raise Exception(error)
    user_map = bpy.data.user_map(subset=[placeholder_mat])
    users = user_map.get(placeholder_mat, None)
    
    for user in users:
        obj = bpy.data.objects.get(user.name)
        if obj:
            for slot in obj.material_slots:
                if slot.material:
                    if slot.material.name == placeholder_mat.name:
                        slot.material = original_mat
                        add_asset_too_previous_states(original_mat)


def handle_replace_collection(asset_entry,asset_original_path):
    print('Replacing Collection...')
    #TODO add option how to handle collections: instance or as collection
    instanced_ph = bpy.data.objects[asset_entry.asset_scene_name]
    if not instanced_ph:
        raise Exception(f'Could not find Instanced object: {asset_entry.asset_name}')
    
    col_ph = bpy.data.collections[asset_entry.asset_scene_name.removesuffix('_instance')]
    if not col_ph:
        col_ph_name =asset_entry.asset_scene_name.removesuffix('_instance')
        raise Exception(f'Could not find Collection: {col_ph_name}')
    parent_col =instanced_ph.users_collection[0]

    blend_dir =os.path.join(asset_original_path,'Collection/')
    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_entry.asset_name,clear_asset_data=True,autoselect=True)
    
    original_asset = bpy.data.collections[asset_entry.asset_scene_name.removesuffix('_ph_instance')]
    if not original_asset:
        raise Exception(f'Could not find Original Collection: {asset_entry.asset_scene_name.removesuffix("_ph_instance")}')

    original_asset_top_level =[obj for obj in original_asset.all_objects if obj.parent is None]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_asset_top_level:
        obj_origin_loc = obj.matrix_world.translation
        instance_world_translate=instanced_ph.matrix_world.to_translation()
        obj.matrix_world.translation = instance_world_translate+obj_origin_loc
    add_asset_too_previous_states(original_asset)
    for obj in original_asset.all_objects:
        obj.select_set(True)
    parent_col.objects.unlink(instanced_ph)



def handle_replace_nodetree(asset_entry,asset_original_path):
    print('Replacing Node Group...')
    placeholder_ng = bpy.data.node_groups[asset_entry.asset_scene_name]
    # print('placeholder_ng ',placeholder_ng)
    blend_dir =os.path.join(asset_original_path,'NodeTree/')
    bpy.ops.wm.append(filepath=asset_original_path,directory=blend_dir,filename=asset_entry.asset_name,clear_asset_data=True)
    original_asset = bpy.data.node_groups[asset_entry.asset_scene_name.removesuffix('_ph')]
    user_map = bpy.data.user_map(subset=[placeholder_ng])
    users = user_map.get(placeholder_ng, None)
    if placeholder_ng.type == 'GEOMETRY':
        for user in users:
            if hasattr(user, 'modifiers'):
                ng_mod = user.modifiers.get(placeholder_ng.name)
                if ng_mod:
                    user.modifiers.remove(ng_mod)
                    mod =user.modifiers.new(original_asset.name,'NODES')
                    mod.node_group=original_asset
                    add_asset_too_previous_states(original_asset)
                    break
    if placeholder_ng.type == 'SHADER':
        for user in users:
            if hasattr(user, 'node_tree'):
                ng_node_tree = user.node_tree
                if ng_node_tree:
                    for node in ng_node_tree.nodes:
                        if hasattr(node,'node_tree'):
                            print('node.node_tree.name ',node.node_tree.name)
                            print('asset_entry.asset_scene_name ',asset_entry.asset_scene_name)
                            if node.node_tree.name == asset_entry.asset_scene_name:
                                node.node_tree = original_asset
                                add_asset_too_previous_states(original_asset)
                                break
                    break
    if placeholder_ng.type == 'COMPOSITING':
        
        placeholder_ng.user_remap(original_asset)

            
def add_asset_too_previous_states(original_asset):
    for asset_type_key, asset_set in addon_info.previous_states.items():
        if original_asset not in asset_set:
            asset_set.add(original_asset)
            addon_info.previous_states[asset_type_key] = asset_set
            break  



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

    for area in bpy.context.screen.areas:
        if area.ui_type == 'ASSETS':
            with bpy.context.temp_override(area=area):
                current_library_name =version_handler.get_asset_library_reference(context)
                bu_lib_names = ('BU_AssetLibrary_Core','BU_AssetLibrary_Premium','TEST_BU_AssetLibrary_Core','TEST_BU_AssetLibrary_Premium','ALL')
                if current_library_name in bu_lib_names:
                    assets = context.selected_assets if bpy.app.version >= (4, 0, 0) else context.selected_asset_files
                    if assets:
                        return assets
                return None

def get_selected_ids(self,context):
    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'OUTLINER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']
    with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
        return context.selected_ids



def initialize_previous_states():
    addon_info.previous_states = {
        'OBJECT': set(bpy.data.objects),
        'MATERIAL': set(bpy.data.materials),
        'NODETREE': set(bpy.data.node_groups),
        'COLLECTION': set(bpy.data.collections),
    }
    print('addon_info.previous_states: ',addon_info.previous_states)

def is_name_variation(base_name, variant_name):
    # Check if variant_name is a variation of base_name (e.g., 'name.001' is a variation of 'name')
    if variant_name.startswith(base_name) and (variant_name == base_name or variant_name[len(base_name):].startswith(".")):
        return True
    return False

def handle_collection_asset_drop(placeholder_browser,new_scene_asset):
    if placeholder_browser.id_type == 'COLLECTION':
        col_ph = bpy.data.collections[new_scene_asset.name.removesuffix('_ph')]
        col_ph.name+='_ph'
        if new_scene_asset.name not in bpy.data.objects:
            bpy.ops.object.collection_external_asset_drop(use_instance=True,collection=new_scene_asset.name, location=bpy.context.scene.cursor.location)
        instanced_ph = bpy.data.objects[new_scene_asset.name]
        instanced_ph.name = f'{new_scene_asset.name}_instance'

    
def detect_and_filter_new_assets(context):
    
    addon_prefs = addon_info.get_addon_prefs()
    try:
        current_library_name = version_handler.get_asset_library_reference_override(bpy.context)
        print('current_library_name: ',current_library_name)
    except Exception as error:
        print(error)
        return None
    if current_library_name!='LOCAL':
        new_scene_assets =[]
        selected_assets = get_selected_assets(context)
        if selected_assets:
            new_scene_assets = detect_new_assets(context.scene) 
            placeholder_selected = False
            context.scene.selected_bu_assets.clear()
            placeholders_in_browser = [asset for asset in selected_assets if is_placeholder(asset)]
            relevant_new_assets = []
            is_premium = False
            if new_scene_assets:
                for placeholder_browser in placeholders_in_browser:
                    for new_scene_asset in new_scene_assets:
                        is_premium = is_asset_premium(placeholder_browser)
                        if is_name_variation(placeholder_browser.name, new_scene_asset.name):
                            if current_library_name =='ALL':
                                if is_premium:
                                    addon_info.set_premium_download_server_ids()
                                else:
                                    addon_info.set_core_download_server_ids()
                            addon_logger.addon_logger.info(f'New placeholder found, initiating download original for asset: {new_scene_asset.name} of type: {placeholder_browser.id_type}')
                            new_scene_asset.name+='_ph'
                            handle_collection_asset_drop(placeholder_browser,new_scene_asset)
                            new_asset_entry = context.scene.selected_bu_assets.add()
                            new_asset_entry.asset = new_scene_asset
                            new_asset_entry.asset_name = placeholder_browser.name
                            new_asset_entry.asset_scene_name = new_scene_asset.name
                            
                            new_asset_entry.id_type = placeholder_browser.id_type
                            new_asset_entry.asset_path = get_asset_full_path(placeholder_browser)  # Ensure this function returns the correct path
                            new_asset_entry.is_premium = is_premium
                            placeholder_selected = True
                            relevant_new_assets.append(new_scene_asset)
                            break
                    if placeholder_selected:
                        break 
                if relevant_new_assets:
                    print('relevant_new_assets found: ',relevant_new_assets)
                    deselect_all()
                    for placeholder_browser in placeholders_in_browser:

                        if is_premium:
                            if addon_prefs.payed==False:
                                for asset_entry in context.scene.selected_bu_assets:
                                    remove_placeholder_asset(asset_entry)
                                bpy.ops.error.custom_dialog('INVOKE_DEFAULT',title='Did not download original asset', error_message='Please validate your premium license and try again.')
                                bpy.context.scene.selected_bu_assets.clear()
                                return None
                    # return None
                    return relevant_new_assets
    return None

def detect_new_assets(scene):
    
    new_assets = []
    # Define data types to check
    data_types = {
        'OBJECT': bpy.data.objects,
        'MATERIAL': bpy.data.materials,
        'NODETREE': bpy.data.node_groups,
        'COLLECTION': bpy.data.collections,
    }
    updated_states = {}
    for asset_type_key, data_type in data_types.items():
        current_assets = set(data_type)
        previous_assets = addon_info.previous_states.get(asset_type_key, set())
        detected_new_assets = current_assets - previous_assets
        # print(detected_new_assets)
        if detected_new_assets:
            for asset in detected_new_assets:
                if asset not in addon_info.previous_states:
                    if not is_original(asset):
                        new_assets.append(asset)
        
        updated_states[asset_type_key] = current_assets
    addon_info.previous_states = updated_states 
    return new_assets


def update_previous_states(new_assets):
    # Assuming new_assets is a list of assets, and each asset has a property to determine its type
    for new_asset in new_assets:
        asset_type_key = new_asset.id_type  # or however you determine the asset's type
        if asset_type_key in addon_info.previous_states:
            addon_info.previous_states[asset_type_key].add(new_asset)
        else:
            addon_info.previous_states[asset_type_key] = {new_asset}

def is_placeholder(asset):
    # print('asset check placeholder ',asset)
    metadata = get_asset_metadata(asset)
    if metadata:
        if 'Placeholder' in metadata.tags:
            info =f'found a placeholder: {asset.name} type: {asset.id_type}' 
            addon_logger.addon_logger.info(info)
            print(info)
            return True
    return False

def get_asset_metadata(asset):
    metadata = None
    if bpy.app.version >= (4,0,0):
        if hasattr(asset,'metadata'):
            metadata =  asset.metadata
    else:
        if hasattr(asset,'asset_data'):
            metadata =  asset.asset_data
    if metadata:
        return metadata
    return None

def is_asset_premium(asset):
    metadata = get_asset_metadata(asset)
    if metadata:
        if 'Premium' in metadata.tags:
            return True
    return False  

def is_original(asset):
    # print('asset check placeholder ',asset)
    metadata = get_asset_metadata(asset)
    if metadata:
        if 'Original' in metadata.tags:
            print(f'this is a Original {asset.name} ')
            return True
    return False  

    
def get_asset_data_type(asset_id_type):
    data_types = {
        'OBJECT': bpy.data.objects,
        'MATERIAL': bpy.data.materials,
        'NODETREE': bpy.data.node_groups,
        'COLLECTION': bpy.data.collections,
    }
    return data_types[asset_id_type]

def get_asset_by_data_type(asset_entry):
    data_type =get_asset_data_type(asset_entry.id_type)
    return data_type.get(asset_entry.asset_name)

def remove_placeholder_asset(asset_entry):
    data_type =get_asset_data_type(asset_entry.id_type)
    if data_type:
        asset = data_type.get(asset_entry.asset_scene_name)
        if asset:
            data_type.remove(asset)

@persistent
def asset_added_handler(dummy):
    scene = bpy.context.scene
    if len(scene.selected_bu_assets) ==0:
        new_assets = detect_and_filter_new_assets(bpy.context)
        if new_assets:
            new_asset_names = [asset.name for asset in new_assets]
            # print('assets to process: ',bpy.context.scene.selected_bu_assets)
            for asset_entry in bpy.context.scene.selected_bu_assets:
                # print('asset_entry ',asset_entry.asset_name)
                # print('new_assets ',new_asset_names)
                for asset_name in new_asset_names:
                    if asset_entry.asset_name in asset_name:
                        bpy.ops.bu.download_original_core('EXEC_DEFAULT',asset_name=asset_entry.asset_name,is_premium=asset_entry.is_premium,is_dragged=True)
                    break
                break


def force_asset_browser_refresh():
    # Store the current area
    current_area = bpy.context.area.type
    
    # Find an asset browser area
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'ASSETS':
                # Temporarily change the area type
                area.type = 'INFO'
                bpy.context.window_manager.update_tag()  # Request redraw
                area.type = 'ASSETS'
                bpy.context.window_manager.update_tag()  # Request redraw
                break

    # Restore the original area type if needed
    bpy.context.area.type = current_area   

class BUSelectedAssets(PropertyGroup):
    asset: PointerProperty(type=bpy.types.ID)
    asset_name: StringProperty()
    asset_scene_name: StringProperty()
    id_type: StringProperty()
    asset_path:StringProperty(subtype='DIR_PATH')
    is_premium:BoolProperty(default=False)

class BU_OT_RefreshLibrary(bpy.types.Operator):
    bl_idname = "bu.refresh_library"
    bl_label = "Refresh library"

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.ui_type == 'ASSETS':
                with bpy.context.temp_override(area=area):
                    print('refresh library')
                    bpy.ops.asset.library_refresh()
        return {'FINISHED'}
    
classes = (
    BUSelectedAssets,
    BU_OT_RefreshLibrary,
    
)

@persistent
def on_load_post_handler(dummy):
    initialize_previous_states()

def register_handlers():
    try:
        if on_load_post_handler not in bpy.app.handlers.load_post:
            print('registering on_load_post_handler')
            bpy.app.handlers.load_post.append(on_load_post_handler)
        if asset_added_handler not in bpy.app.handlers.depsgraph_update_post:
            print('registering asset_added_handler')
            bpy.app.handlers.depsgraph_update_post.append(asset_added_handler)
    except Exception as e:
        print(e)

def unregister_handlers():
    try:
        if on_load_post_handler in bpy.app.handlers.load_post:
            print('unregistering on_load_post_handler')
            bpy.app.handlers.load_post.remove(on_load_post_handler)
        if asset_added_handler in bpy.app.handlers.depsgraph_update_post:
            print('unregistering asset_added_handler')
            bpy.app.handlers.depsgraph_update_post.remove(asset_added_handler)
    except Exception as e:
        print(e)
            
def register():
    # if not bpy.app.timers.is_registered(asset_placeholder_check):
    #     bpy.app.timers.register(asset_placeholder_check)
    
    for cls in classes:
        bpy.utils.register_class(cls)
    register_handlers()
    bpy.types.Scene.selected_bu_assets = bpy.props.CollectionProperty(type=BUSelectedAssets, options={'HIDDEN'})
   

def unregister():
    unregister_handlers()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # if bpy.app.timers.is_registered(asset_placeholder_check):
    #     bpy.app.timers.unregister(asset_placeholder_check)
    del bpy.types.Scene.selected_bu_assets
    



