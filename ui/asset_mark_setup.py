import bpy
import os
import shutil
from ..utils import addon_info,catfile_handler,sync_manager
import textwrap
import math
from . import asset_bbox_logic,marktool_tabs
from mathutils import Vector,Euler
from bpy.types import Context, PropertyGroup
from bpy.props import BoolProperty,IntProperty,EnumProperty,StringProperty,PointerProperty,CollectionProperty,FloatVectorProperty,FloatProperty
from .. import icons






def set_catalog_file_target(self,context):
    catalog_target = context.scene.catalog_target_enum.switch_catalog_target
    addon_prefs = addon_info.get_addon_name().preferences
    if catalog_target == 'core_catalog_file':
        addon_prefs.download_catalog_folder_id = addon_prefs.bl_rna.properties['upload_folder_id'].default if addon_prefs.debug_mode == False else "1Jnc45SV7-zK4ULQzmFSA0pK6JKc8z3DN"
    elif catalog_target == 'premium_catalog_file':
        addon_prefs.download_catalog_folder_id = "1FU-do5DYHVMpDO925v4tOaBPiWWCNP_9" if addon_prefs.debug_mode == False else "146BSw9Gw6YpC9jUA3Ehe7NKa2C8jf3e7"
    

class CatalogTargetProperty(bpy.types.PropertyGroup):
    switch_catalog_target: bpy.props.EnumProperty(
        name = 'catalog target',
        description = "get Core or Premium catalog file from server",
        items=[
            ('core_catalog_file', 'Core', '', '', 0),
            ('premium_catalog_file', 'Premium', '', '', 1)
        ],
        default='core_catalog_file',
        update=set_catalog_file_target
    )



class MaterialAssociation(PropertyGroup):
    material:PointerProperty(type=bpy.types.Material)
    name:StringProperty()
    has_previews:BoolProperty()
    draw_asset_data_settings:BoolProperty()


class MaterialBoolProperties(bpy.types.PropertyGroup):
    include:BoolProperty(name="Include", default=False, description="Include this material")


def update_asset_transform(self,context):
    item = context.scene.mark_collection[self.idx]
    if item.object_type == 'Object':
        obj = bpy.data.objects.get(item.asset.name)
        if obj:
           
            # obj.scale =(item.scale,item.scale,item.scale)
            self.location = obj.location
            self.rotation = obj.rotation_euler
            self.scale = (obj.scale.x + obj.scale.y + obj.scale.z) / 3.0
    elif item.object_type == 'Collection':
        source_col = bpy.data.collections.get(item.asset.name)
        item_instance = f'{item.asset.name}_instance'
        if item_instance in bpy.data.objects:
            obj = bpy.data.objects.get(item_instance)
            if obj:   
                # obj.scale = (item.scale,item.scale,item.scale)
                self.location = obj.location
                self.rotation = obj.rotation_euler
                self.scale = obj.scale
            # col_scale_factor =asset_bbox_logic.get_col_scale_factor(source_col,item.max_scale.x,item.max_scale.y,item.max_scale.z)
            # print('col_scale_factor',col_scale_factor)       
def get_mark_tool_obj(idx):
    item = bpy.context.scene.mark_collection[idx]
    if item.object_type == 'Object':
        return bpy.data.objects.get(item.asset.name)
    elif item.object_type == 'Collection':
        item_instance = f'{item.asset.name}_instance'
        if item_instance in bpy.data.objects:
            return bpy.data.objects.get(f'{item.asset.name}_instance')
    
def get_uniform_scale(self):
    obj = get_mark_tool_obj(self.idx)
    if obj:
        return (obj.scale.x + obj.scale.y + obj.scale.z) / 3.0
    return 1.0
def set_uniform_scale(self, value):
    obj = get_mark_tool_obj(self.idx)
    if obj:
        obj.scale = (value, value, value)

def get_mark_asset_obj_location(self):
    obj = get_mark_tool_obj(self.idx)
    if obj:
        return obj.location
    return (0.0,0.0,0.0)

def set_mark_asset_obj_location(self, value):
    obj = get_mark_tool_obj(self.idx)
    if obj:
        obj.location = value

def get_mark_asset_obj_rotation(self):
    obj = get_mark_tool_obj(self.idx)
    if obj:
        return obj.rotation_euler
    return (0.0,0.0,0.436332)

def set_mark_asset_obj_rotation(self, value):
    obj = get_mark_tool_obj(self.idx)
    if obj:
        obj.rotation_euler = value

def get_preview_camera_location(self):
    cam_name= ('Preview Camera')
    if cam_name in bpy.data.objects:
        return bpy.data.objects.get(cam_name).location
    return (0.0,-2.0,0.6)
def set_preview_camera_location(self, value):
    cam_name= ('Preview Camera')
    if cam_name in bpy.data.objects:
        bpy.data.objects.get(cam_name).location = value

def get_preview_camera_rotation(self):
    cam_name= ('Preview Camera')
    if cam_name in bpy.data.objects:
        return bpy.data.objects.get(cam_name).rotation_euler
    return (1.39626,0.0,0.0)

def set_preview_camera_rotation(self, value):
    cam_name= ('Preview Camera')
    if cam_name in bpy.data.objects:
        bpy.data.objects.get(cam_name).rotation_euler = value

class AssetsToMark(PropertyGroup): 
    asset: PointerProperty(type=bpy.types.ID)
    idx: IntProperty()
    obj: PointerProperty(type=bpy.types.Object)
    col_instance: PointerProperty(type=bpy.types.Object)
    viewport_visible: BoolProperty()
    asset_isolation: BoolProperty()
    mats:CollectionProperty(type=MaterialAssociation)
    override_type:BoolProperty()
    types: EnumProperty(items=addon_info.get_types() ,name ='Type', description='asset types')
    object_type: StringProperty()
    has_previews: BoolProperty()
    draw_render_settings: BoolProperty(default= False)
    draw_asset_data_settings: BoolProperty(default= False)
    draw_asset_tags: BoolProperty(default= False)
    render_bg: BoolProperty(default= True)
    render_logo: BoolProperty(default= True)
    override_camera: BoolProperty(default= False)
    draw_override_camera: BoolProperty(default= False)
    enable_cam_info: BoolProperty(default= False)
    cam_loc: FloatVectorProperty(default=(0.0,-2.0,0.8), size=3,subtype='XYZ',get=get_preview_camera_location,set=set_preview_camera_location)
    cam_rot: FloatVectorProperty(default=(1.39626,0.0,0.0), size=3,subtype='EULER',get=get_preview_camera_rotation,set=set_preview_camera_rotation)
    enable_offsets: BoolProperty(default= False)
    draw_enable_offsets: BoolProperty(default= False)
    location: FloatVectorProperty(default=(0.0,0.0,0.0),size=3,subtype='TRANSLATION',get=get_mark_asset_obj_location,set=set_mark_asset_obj_location)
    rotation: FloatVectorProperty(default=(0.0,0.0,0.436332), size=3,subtype='EULER',get=get_mark_asset_obj_rotation,set=set_mark_asset_obj_rotation)
    scale: FloatProperty(default=(1.0),precision=3,get=get_uniform_scale,set=set_uniform_scale)
    max_scale: FloatVectorProperty(default=(0.95,0.95,0.95), size=3,subtype='XYZ',precision=3,max=2.0)
    original_scale: FloatVectorProperty(default=(1.0,1.0,1.0), size=3,subtype='XYZ')

class ClearMarkTool(bpy.types.Operator):
    '''Clear the mark tool'''
    bl_idname = "wm.clear_mark_tool" 
    bl_label = "clear the mark tool"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls,context):
        if not context.scene.mark_collection:
            cls.poll_message_set('Mark Tool is empty!')
            return False
        return True
    def execute(self, context):
        for idx,item in enumerate(context.scene.mark_collection):
            bpy.ops.bu.reset_object_original_dimensions(idx=idx)
        bpy.ops.bu.remove_preview_camera()
        context.scene.mats_to_include.clear()
        context.scene.mark_collection.clear()
        return {'FINISHED'}

class BU_OT_Add_All_Mats(bpy.types.Operator):
    '''Add all materials to the include list'''
    bl_idname = "bu.add_all_mats" 
    bl_label = "Select all materials"
    bl_options = {"REGISTER",}

    name: bpy.props.StringProperty()

    
    def execute(self, context):
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.asset.name), None)
        if matching_item:
            matching_item.mats.clear()
            for slot in matching_item.asset.material_slots:
                mat = slot.material
                mat.make_local()
            # mat = matching_item.asset.material_slots[self.idx].material
                include_mat =matching_item.mats.add()
                include_mat.material = mat
                include_mat.name = mat.name
        return {'FINISHED'}  
    
class BU_OT_Remove_All_Mats(bpy.types.Operator):
    '''remove all materials from the include list'''
    bl_idname = "bu.remove_all_mats" 
    bl_label = "Select all materials"
    bl_options = {"REGISTER"}

    name: bpy.props.StringProperty()

    def execute(self, context):
        
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.asset.name), None)
        if matching_item:
            matching_item.mats.clear()
        return {'FINISHED'}  
    
class BU_OT_Add_AssetToMark_Mat(bpy.types.Operator):
    '''Add selected assets to the mark tool'''
    bl_idname = "bu.add_asset_to_mark_mat"
    bl_label = "Add selected assets to the to mark list"
    bl_options = {"REGISTER"}
    
    idx: bpy.props.IntProperty()
    name: bpy.props.StringProperty()
    mat_name: bpy.props.StringProperty()

   
    def execute(self,context):
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.asset.name), None)
        if matching_item:
            mat = bpy.data.materials.get(self.mat_name)
            mat.make_local()
            # mat = matching_item.asset.material_slots[self.idx].material
            include_mat =matching_item.mats.add()
            include_mat.material = mat
            include_mat.name = mat.name  
        return {'FINISHED'}

class Remove_AssetToMark_Mat(bpy.types.Operator):
    '''Add selected assets to the mark tool'''
    bl_idname = "bu.remove_asset_to_mark_mat"
    bl_label = "Remove selected material from to mark list"
    bl_options = {"REGISTER"}

    idx: bpy.props.IntProperty()
    name: bpy.props.StringProperty()
    mat_name: bpy.props.StringProperty()

    def execute(self,context):
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.asset.name), None)
        if matching_item:
            for idx,mat in enumerate(matching_item.mats):
                if mat.name == self.mat_name:
                    matching_item.mats.remove(idx)
                    break
        return {'FINISHED'}
    

   

class BU_OT_AddToMarkTool(bpy.types.Operator):
    '''Add selected assets to the mark tool'''
    bl_idname = "wm.add_to_mark_tool" 
    bl_label = "start the marking of assets process"
    bl_options = {"REGISTER","UNDO"}

    @classmethod
    def poll(cls,context):
        addon_prefs = addon_info.get_addon_name().preferences
        asset_preview_path = addon_info.get_asset_preview_path()
        if not bpy.data.filepath:
            cls.poll_message_set('Cant mark asset if file is not saved to disk!')
        
        return True
    


    def get_selected_ids(self,context):
        scr = bpy.context.screen
        areas = [area for area in scr.areas if area.type == 'OUTLINER']
        regions = [region for region in areas[0].regions if region.type == 'WINDOW']
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            return context.selected_ids

    def get_mats_list(self,context,item):
        mat_list = []
        
        for idx,slot in enumerate(item.material_slots):
            if slot.material:
                mat = slot.material
                mat_list.append(mat)
        return mat_list

    def execute(self, context):           
        selected_ids = self.get_selected_ids(context)
        for idx,id in enumerate(selected_ids):
            id.make_local()
            if id.name not in context.scene.mark_collection:
                markasset = context.scene.mark_collection.add()
                markasset.asset = id
                markasset.idx = idx
                object_type = id.bl_rna.identifier
                if object_type == 'Object':
                    markasset.object_type = id.bl_rna.identifier
                    markasset.original_scale = id.scale
                elif object_type == 'Collection':
                    markasset.object_type = id.bl_rna.identifier
        return {'FINISHED'}

class BU_OT_RemoveFromMarkTool(bpy.types.Operator):
    '''Remove selected assets from the mark tool'''
    bl_idname = "bu.remove_from_mark_tool" 
    bl_label = "Remove selected assets from the mark tool"
    bl_options = {"REGISTER"}

    idx: bpy.props.IntProperty()
    asset_name: bpy.props.StringProperty()

    def execute(self, context):
        matching_item = next((item for item in context.scene.mark_collection if self.asset_name == item.asset.name), None)
        print(self.asset_name)
        if matching_item:
            context.scene.mark_collection.remove(self.idx)
        return {'FINISHED'}

class BU_OT_MarkAsset(bpy.types.Operator):
    '''Mark this asset'''
    bl_idname = "bu.mark_asset" 
    bl_label = "Mark asset"
    bl_options = {"REGISTER"}

    idx: bpy.props.IntProperty()
    asset_name: bpy.props.StringProperty()
    

    def assign_previews(self,context,asset):
        asset_preview_path = addon_info.get_asset_preview_path()
        path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
        if os.path.exists(path):
            with bpy.context.temp_override(id=asset):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=path)

    def execute(self, context):
        addon_prefs = addon_info.get_addon_prefs()
        author_name = addon_prefs.author
        item = context.scene.mark_collection[self.idx]
        print(item.object_type)
        if item.types == 'Object' and item.object_type == 'Object':
            asset = bpy.data.objects.get(self.asset_name)
            if asset:
                asset.rotation_euler = Euler((0, 0, 0))
                asset.scale = Vector((1, 1, 1))
                asset.location = Vector((0, 0, 0))
            #pack images
            pack_object_mat_images_recursive(asset)

        elif item.types == 'Material':
            asset = bpy.data.materials.get(self.asset_name)
            pack_images(asset)

        elif item.types == 'Geometry_Node':
            asset = bpy.data.node_groups.get(self.asset_name)

        elif item.object_type == 'Collection':                
            asset = bpy.data.collections.get(self.asset_name)
            #pack images
            #get child collection objects and materials
            pack_col_mat_images_recursive(context,asset)
                

        if asset:
            asset.asset_mark()
            self.assign_previews(context,asset)
            if author_name != '':
                asset.asset_data.author = author_name
        return {'FINISHED'}

class BU_OT_ClearMarked(bpy.types.Operator):
    '''Clear Marked asset'''
    bl_idname = "bu.clear_marked" 
    bl_label = "Clear Marked"
    bl_options = {"REGISTER"}

    idx: bpy.props.IntProperty()
    asset_name: bpy.props.StringProperty()

    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
        if item.types == 'Object' and item.object_type == 'Object':
            asset = bpy.data.objects.get(self.asset_name)
        elif item.types == 'Material':
            asset = bpy.data.materials.get(self.asset_name)
        elif item.types == 'Geometry_Node':
            asset = bpy.data.node_groups.get(self.asset_name)
        elif item.object_type == 'Collection':
            asset = bpy.data.collections.get(self.asset_name)
        if asset:
            asset.asset_clear()
        

        return {'FINISHED'}

def pack_col_mat_images_recursive(context,asset):
    if asset.children_recursive:
        for col in asset.children_recursive:
            if col.objects:
                for obj in col.objects:
                    child_obj = addon_info.get_layer_object(context,obj)
                    material = has_materials(child_obj)
                    if material:
                        pack_images(material)
        #get child objects and materials          
        for obj in asset.objects:
            child_obj = addon_info.get_layer_object(context,obj)
            material = has_materials(child_obj)
            if material:
                pack_images(material)

def pack_object_mat_images_recursive(asset):
    material = has_materials(asset)
    if material:
        pack_images(material)
    if asset.children_recursive:
        for obj in asset.children_recursive:
            material = has_materials(obj)
            if material:
                pack_images(material)

def has_materials(obj):
    if obj.material_slots:
        for slot in obj.material_slots:
            material =slot.material
            if slot.material:
                return material
    return None
    
def pack_images(material):
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            if node.image:
                if node.image.packed_file == None:
                    node.image.pack()

class confirmMark(bpy.types.Operator):
    '''Add assets to Asset browser!'''
    bl_idname = "wm.confirm_mark" 
    bl_label = "Initialize mark for add process"
    bl_options = {"REGISTER",}

    @classmethod
    def poll(cls, context):
        if not context.scene.mark_collection:
            cls.poll_message_set('Mark Tool is empty!')
            return False
        return True
    
    def assign_previews(self,context,asset):
        asset_preview_path = addon_info.get_asset_preview_path()
        path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
        if os.path.exists(path):
            with bpy.context.temp_override(id=asset):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=path)

    def execute(self, context):
        bpy.ops.wm.save_userpref()
        addon_prefs = addon_info.get_addon_prefs()
        author_name = addon_prefs.author
        
        for item in context.scene.mark_collection:
            if item.types == 'Material':
                # for mat in items.mats:
                for idx,slot in enumerate(item.mats):
                    
                    material = slot.material
                    material.asset_mark()
                    self.assign_previews(context,material)
                    pack_images(material)
                    if author_name != '':
                        slot.material.asset_data.author = author_name 
            elif item.types == 'Geometry_Node':
                geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
                if geo_modifier:
                    g_nodes = geo_modifier.node_group
                    g_nodes.asset_mark()
                    self.assign_previews(context,g_nodes)
                    if author_name != '':
                        g_nodes.asset_data.author = author_name
            elif item.object_type == 'Object':
                obj = bpy.data.objects.get(item.asset.name)
                if obj:
                    obj.rotation_euler = Euler((0, 0, 0))
                    obj.scale = Vector((1, 1, 1))
                    obj.location = Vector((0, 0, 0))
                    obj.asset_mark()
                    self.assign_previews(context,obj)
                    if author_name != '':
                        obj.asset_data.author = author_name
                    pack_object_mat_images_recursive(obj)

            
            elif item.object_type == 'Collection':
                asset = item.asset
                asset.asset_mark()
                self.assign_previews(context,asset)
                #pack images
                pack_col_mat_images_recursive(context,asset)
                if author_name != '':
                    item.asset.asset_data.author = author_name
                
                    
        return {'FINISHED'}

    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        if addon_prefs.author != '':
            layout.label(text =f'Press "OK" to mark as asset ')
            layout.label(text =f'The Author will be set to: {addon_prefs.author}')
        else:
            layout.label(text = f'WARNING: Author is not set') 
            layout.label(text = f'All marked assets will be set to Anonymous')        
            row = layout.row()
            
            
            row.prop(addon_prefs,'author', text='Override Author: ')
            row = layout.row()


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width= 500)
        
    

class ClearMarkedAsset(bpy.types.Operator):
    '''Unmark selected assets from asset browser!'''
    bl_idname = "wm.clear_marked_assets" 
    bl_label = "The selected assets will be unmarked as assets "
    bl_options = {"REGISTER","UNDO"}

    

    @classmethod
    def poll(cls, context):
        selected_asset_files =addon_info.get_local_selected_assets(context)
        if not selected_asset_files:
            cls.poll_message_set('Select assets from the asset browser to unmark!')
            return False
        return True
       
    def execute(self, context):
        selected_asset_files =addon_info.get_local_selected_assets(context)
        for asset_file in selected_asset_files:
            asset_file.local_id.asset_clear()
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


    
def draw_mat_previews(self,context,box,item):
    row= box.row()
    images =[]
    addon_prefs = addon_info.get_addon_name().preferences
    for idx,slot in enumerate(item.asset.material_slots):
        mat = slot.material
        if mat:
            image_name =f'preview_{mat.name}.png'
            if image_name in bpy.data.images:
                img = bpy.data.images[image_name]
                
                # if img.preview.icon_id:
            #         row.template_icon(img.preview.icon_id,scale=3)
            # else:
            #     slot = item.asset.material_slots[idx]
            #     row.template_icon(icon_value=slot.material.preview.icon_id, scale=3)
        # box.template_preview(img)
        # if slot.material:
        #     
            
def draw_has_previews(self, context,row,idx,item,asset):
    addon_prefs = addon_info.get_addon_name().preferences
    if addon_prefs.toggle_experimental_BU_Render_Previews:
        # Iterate through asset's material slots and add them to mats
        asset_preview_path = addon_info.get_asset_preview_path()
        ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
        path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
        ph_path = f'{ph_asset_preview_path}{os.sep}PH_preview_{asset.name}.png'
        # if bpy.data.objects.is_updated:
        #     row.label(text ="Evaluated",)
        # else:
        #     row.label(text ="NOT Evaluated")
        if os.path.exists(path) and os.path.exists(ph_path):
            row.label(text ="",icon='IMAGE_RGB_ALPHA')
        else:
            row.label(text ="",icon='SHADING_BBOX' )
        render_op_text = "Render *" if bpy.data.is_dirty else "Render"
        op = row.operator("bu.render_previews_modal", icon='OUTPUT', text=render_op_text )
        op.idx = idx
        op.asset_name = asset.name
        if item.types != 'Material':
            row.prop(item, 'draw_render_settings', text="", icon='SETTINGS',toggle=True)
        if item.object_type == 'Collection':
            op.asset_type = 'collections'
        elif item.types == 'Geometry_Node':
            op.asset_type = 'node_groups'
        else:
            data_type = item.types.lower()
            op.asset_type = f'{data_type}s'
    

def get_asset_preview(self,context):
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    selected_assets = context.selected_asset_files
                    return selected_assets

def redraw(self,context):
    for area in context.screen.areas:
        if area.type == 'PROPERTIES':
            area.tag_redraw()
    print('redraw')


        

def draw_selected_properties(self,context,main_row,idx,item):
    
    if item.types == 'Object':
        box = main_row.box()
        # row = box.row(align = True)
        # row.label(text ="Asset Name")
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.prop(item.asset, 'name', text ="")
        # row = box.row(align=True)
        draw_has_previews(self,context,row,idx,item,item)
        # if item.draw_render_settings:
            # draw_preview_render_settings(self,context,main_row,idx,item)
        
        box = main_row.box()
        box.enabled = True if item.asset.asset_data else False
        box.prop(item, 'draw_asset_data_settings', text='Metadata', icon='TRIA_UP' if item.draw_asset_data_settings else 'TRIA_DOWN')
        if item.draw_asset_data_settings:
            draw_metadata(self,context,box,idx,item.asset)


    elif item.types == 'Material':
        main_row.alignment = 'LEFT'
        box = main_row.box()
        row= box.row(align = True)
        # draw_mat_add_all(self,context,row,item)
        # draw_mat_remove_all(self,context,row,item)
        row= box.row(align = True)
        col = row.column(align = True)
        
        if item.asset.material_slots:
            for mat_idx,slot in enumerate(item.asset.material_slots):
                if slot.material:
                    mat = slot.material
                    split = col.split(factor=0.5,align = True)
                    
                    row= split.row(align = True)
                    row.prop(mat, 'name', text ="",icon_value =mat.preview.icon_id)
                    row.alignment= 'EXPAND'

                    draw_has_previews(self,context,row,idx,item,mat)
                    metacol= split.column()
                    
                    # col = split.column(align=True)
                    if mat.name in item.mats:
                        target_mat_item = item.mats[mat.name]
                        metacol.enabled = True if mat.asset_data else False
                        metacol.prop(target_mat_item, 'draw_asset_data_settings', text='Metadata', icon='TRIA_UP' if target_mat_item.draw_asset_data_settings else 'TRIA_DOWN')
                        if target_mat_item.draw_asset_data_settings:
                            
                            box = metacol.box()
                            draw_metadata(self,context,box,idx,mat)       
                else:
                    row.enabled
                    row.operator("bu.material_select", icon='MATERIAL', text="Select Material" )
                row= col.row(align = True)
        else:
            row.label(text ="No Materials found !")
        


    elif item.types == 'Geometry_Node':
        box = main_row.box()          
        geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
        if geo_modifier:
            g_nodes = geo_modifier.node_group
            if g_nodes is not None:
                col = box.column(align = True)
                row =col.row()
                row.prop(g_nodes, 'name', text ="", expand = True)
                draw_has_previews(self,context,row,idx,item,g_nodes)
                
                box = main_row.box()
                box.enabled = True if g_nodes.asset_data else False
                box.prop(item, 'draw_asset_data_settings', text='Metadata', icon='TRIA_UP' if item.draw_asset_data_settings else 'TRIA_DOWN')
                if item.draw_asset_data_settings:
                    draw_metadata(self,context,box,idx,g_nodes)
            else:
                row = box.row(align = True)
                row.alignment = 'CENTER'
                text_block = (
                    "Geometry Nodes modifier found:",
                    "But no node group is assigned!"
                )
                for line in text_block:
                    row.label(text=line)
                    row = box.row(align = True)
                    row.alignment = 'CENTER'
        else:
            box.label(text ="Node Group Name")
            col = box.column(align = True)
            box.label(text ="No GeometryNodes modifier found !")



def get_layer_collection(collection):
    '''Returns the view layer LayerCollection for a specificied Collection'''
    def scan_children(lc, result=None):
        for c in lc.children:
            if c.collection == collection:
                return c
            result = scan_children(c, result)
        return result

    return scan_children(bpy.context.view_layer.layer_collection)




def draw_marked(self,context):
    layout = self.layout


    for idx,item in enumerate(context.scene.mark_collection):
        addon_prefs=addon_info.get_addon_name().preferences
        # box = layout.box()
        row = layout.row(align = True)
        # row.alignment = 'EXPAND' if addon_prefs.toggle_experimental_BU_Render_Previews else 'LEFT'
        row.alignment = 'EXPAND'
        box = row.box()
        if item.object_type == 'Object':
            name = item.asset.name
            obj = context.scene.objects.get(name)
            if obj:
                box.prop(item,'viewport_visible', text = '', icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF',emboss=False)
                if item.viewport_visible:
                    obj.hide_set(True)
                else:
                    obj.hide_set(False)
        if item.object_type == 'Collection':
            if item.enable_offsets:
                name = item.asset.name + '_instance'
                obj = context.scene.objects.get(name)
                if obj:
                    box.prop(item,'viewport_visible', text = '', icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF',emboss=False)
                    if item.viewport_visible:
                        obj.hide_set(True)
                    else:
                        obj.hide_set(False)
            else:
                collection =bpy.data.collections.get(item.asset.name)
                original_col =get_layer_collection(collection)
                box.prop(original_col,'hide_viewport', text = '', icon = 'HIDE_OFF',emboss=False)
        box = row.box()
 
        # box.label(text='Asset type')
        if item.asset.bl_rna.identifier == 'Object':
            box.prop(item,'types', text = '')
        
        elif item.asset.bl_rna.identifier == 'Collection':
            box.label(text='Collection')
        else:
            box.label(text='This type is not supported yet')
        draw_selected_properties(self,context,row,idx,item)




def draw_metadata(self,context,layout,idx,asset):
    addon_prefs = addon_info.get_addon_name().preferences

    if asset.asset_data:
        layout.alignment ='EXPAND'
        layout.prop(asset.asset_data, 'description')
        if addon_prefs.author =='':
            layout.prop(asset.asset_data, 'author')
        else:
            layout.prop(addon_prefs, 'author', text='Author (Globally set) : ')
        row =layout.row(align=True)
        row.label(text="Tags:")
        # row.alignment = 'EXPAND'
        row.template_list("ASSETBROWSER_UL_metadata_tags", "asset_tags", asset.asset_data, "tags",asset.asset_data, "active_tag", rows=4)
        col = row.column(align=True)
        add_tag =col.operator('asset.add_tag', text='',icon='ADD',)
        add_tag.idx =idx
        add_tag.asset_name =asset.name
        remove_tag =col.operator("asset.remove_tag", icon='REMOVE', text="")
        remove_tag.idx =idx
        remove_tag.asset_name =asset.name

def get_target_asset_type(self, context, item):
    if (item.object_type == 'Object' and item.types =='Object'):
        return item.asset
    elif (item.object_type == 'Collection' and item.types =='Object'):
        return item.asset
    elif item.types == 'Materials':
        return item.mats
    elif item.types == 'Geometry_Node':
        geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
        if geo_modifier:
            return geo_modifier.node_group    

class ASSETBROWSER_UL_metadata_tags(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        tag = item

        row = layout.row(align=True)
        # Non-editable entries would show grayed-out, which is bad in this specific case, so switch to mere label.
        if tag.is_property_readonly("name"):
            row.label(text=tag.name, icon_value=icon, translate=False)
        else:
            row.prop(tag, "name", text="", emboss=False, icon_value=icon)

def draw_disclaimer(self, context):
    disclaimer = 'By uploading your own assets, you confirm that you have the necessary rights and permissions to use and share the content. You understand that you are solely responsible for any copyright infringement or violation of intellectual property rights. We assume no liability for the content you upload. Please ensure you have the appropriate authorizations before proceeding.'
    wrapp = textwrap.TextWrapper(width=int(context.region.width/6) ) #50 = maximum length       
    wList = wrapp.wrap(text=disclaimer)
    box = self.layout.box()
    for text in wList:
        box.label(text=text)

class BU_OT_AssetAddTag(bpy.types.Operator):
    bl_idname = "asset.add_tag"
    bl_label = 'add tag to asset'
    bl_description = 'add tag to asset'
    bl_category = 'Asset Browser'
    bl_options = {'REGISTER'}

    idx: IntProperty()
    asset_name: StringProperty()
    def execute(self, context):
        
        item = context.scene.mark_collection[self.idx]
        asset = item.asset
        if item.types == 'Material':
            asset = bpy.data.materials.get(self.asset_name)
        elif item.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                asset = geo_modifier.node_group    
        asset.asset_data.tags.new('Tag')
        
        return {'FINISHED'}

class BU_OT_AssetRemoveTag(bpy.types.Operator):
    bl_idname = "asset.remove_tag"
    bl_label = 'Remove tag'
    bl_description = 'Remove tag form asset'
    bl_category = 'Asset Browser'
    bl_options = {'REGISTER'}

    idx: IntProperty()
    asset_name: StringProperty()

    def execute(self, context):
        item = context.scene.mark_collection[self.idx]
       
        asset = item.asset
        if item.types == 'Material':
            if self.asset_name in item.mats:
                asset = bpy.data.materials.get(self.asset_name)
            
        elif item.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                asset = geo_modifier.node_group 

        active_tag_index =asset.asset_data.active_tag
        if active_tag_index >= len(asset.asset_data.tags):
            active_tag_index =(len(asset.asset_data.tags)-1)

        
        if len(asset.asset_data.tags) > 0:
            active_tag = asset.asset_data.tags[active_tag_index]
            asset.asset_data.tags.remove(active_tag)
            active_tag_index = min(max(0,active_tag_index -1),len(asset.asset_data.tags)-1)
        return {'FINISHED'}     


def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)



  
class BU_PT_MarkAssetsMainPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_MARKASSETS"
    bl_label = 'Mark Assets'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self,context):
        layout = self.layout

        


class BU_PT_MarkTool(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_MARKTOOL"
    bl_label = 'Mark Tool'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_category = 'Blender Universe Kit'
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_name().preferences 
        # dir_path = addon_prefs.lib_path
        # if  dir_path !='':
        return True

    def draw(self,context): 
        layout = self.layout
        box = layout.box()
        text = 'Make sure to use descriptive names for assets you want to add!\n Example for a mesh: SM_Door_Damaged | Example for Material: M_Wood_Peeled_Paint'
        _label_multiline(
            context=context,
            text=text,
            parent=box
        )
        
        box = layout.box()
        row = box.row(align=True)
        row.label(text = 'Select assets in the outliner to add')
        addon_info.gitbook_link(row,'mark-asset-tools/mark-tool')
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.operator('wm.add_to_mark_tool', text=('Add to Tool'), icon ='ADD')
        row.operator('wm.clear_mark_tool', text=('Clear Tool'), icon = 'CANCEL')
        
        

        if len(context.scene.mark_collection)>0:
            # col.prop(addon_prefs, 'toggle_experimental_BU_Render_Previews', text = 'Toggle Render Previews',toggle=True,icon ='OUTPUT')
            switch_marktool = context.scene.switch_marktool
            layout = self.layout
            row = layout.row(align=True)
            
            for enum_item in switch_marktool.bl_rna.properties['switch_tabs'].enum_items:
                row.prop_enum(switch_marktool, "switch_tabs", enum_item.identifier, text=enum_item.name)
            
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.operator('bu.select_all_items', text='Select all assets', icon='RESTRICT_SELECT_OFF')
            is_local_view = context.space_data.local_view is not None
            row.operator('bu.isolate_selected', text='Isolate selected' if not is_local_view else 'Deisolate selected', icon='STICKY_UVS_LOC',depress= is_local_view)
            marktool_tabs.draw_marktool_default(self, context)
            
            
            row = layout.row()
            row.operator('wm.confirm_mark', text=('Mark all Assets'), icon='BLENDER')
            row.operator('wm.clear_marked_assets', text =('Bath unmark assets'), icon = 'CANCEL')

    
class MarkToolCatagories(bpy.types.PropertyGroup):
    switch_tabs: bpy.props.EnumProperty(
        name = 'mark tool catagories',
        description = "Switch between mark tool catagories",
        items=[
            ('default', 'Default', '', 'BLENDER', 0),
            ('render_previews', 'Render Previews', '', 'OUTPUT', 1),
            ('metadata', 'Asset Metadata', '', 'WORDWRAP_ON', 2)
        ],
        default='default',
    )

class BU_PT_PreviewRenderScene(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_PREVIEWRENDEROPTIONS"
    bl_label = 'Preview Render Scene'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_category = 'Blender Universe Kit'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        mainrow = box.row()
        col = mainrow.column()
        col.alignment = 'LEFT'
        col.label(text='Preview Render scene:')
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.operator("bu.append_preview_render_scene", text="Append", icon='APPEND_BLEND')
        row.operator("bu.remove_preview_render_scene", text="Remove", icon='REMOVE')
        col = mainrow.column()
        col.alignment = 'LEFT'
        
        
        col.label(text='Switch scenes:')
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        # row.operator("bu.switch_to_preview_render_scene", text="Switch Scene", icon='SCENE_DATA')
        window = context.window
        screen = context.screen
        scene = window.scene
        row.template_ID(window, "scene", new="scene.new",unlink="scene.delete")
        mainrow.alignment = 'RIGHT'
        addon_info.gitbook_link(mainrow,'mark-asset-tools/preview-render-scene')
        
class BU_OT_MarkTool_Info(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_MARKTOOLINFO"
    bl_label = 'Disclaimer'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_category = 'Blender Universe Kit'
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self,context):
        layout = self.layout
        layout.label(text = 'Please read the following disclaimer before using this tool:')
        draw_disclaimer(self, context)

class BU_PT_MarkTool_settings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_MARKTOOL_SETTINGS"
    bl_label = 'Mark Tool Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe Kit'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text = 'Mark asset tool settings: ')
        addon_info.gitbook_link(row,'add-on-settings-initial-setup/asset-browser-settings#mark-tool-settings')
        col = box.column()
        col.alignment = 'RIGHT'
        col.prop(addon_prefs, 'author', text = 'Global author name ')
        col.prop(addon_prefs, 'thumb_upload_path', text = 'Asset preview folder')
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        if addon_prefs.is_admin:
            row.label(text = 'Select a library catalog to download:')
            row = box.row()
            row.alignment = 'LEFT'
            scene = context.scene
            row.prop(scene.upload_target_enum, "switch_upload_target", text="")
        if sync_manager.SyncManager.is_sync_operator('bu.sync_catalog_file'):
            row.operator('bu.sync_catalog_file', text='Cancel Sync', icon='CANCEL')
        else:
            row.operator('bu.sync_catalog_file', text='Get catalog file' if not addon_prefs.debug_mode else 'Get test library catalog file', icon='OUTLINER')

        
class BU_MT_MaterialSelector(bpy.types.Operator):
    """ Material selection dropdown with search feature """
    bl_idname = "bu.material_select"
    bl_label = ""
    bl_property = "material"

    callback_strings = []

    def get_name_with_lib(datablock):
        """
        Format the name for display similar to Blender,
        with an "L" as prefix if from a library
        """
        text = datablock.name
        if datablock.library:
            # text += ' (Lib: "%s")' % datablock.library.name
            text = "L " + text
        return text

    def callback(self, context):
        items = []

        for index, mat in enumerate(bpy.data.materials):
            name = BU_MT_MaterialSelector.get_name_with_lib(mat)
            # We can not show descriptions or icons here unfortunately
            items.append((str(index), name, ""))

        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        BU_MT_MaterialSelector.callback_strings = items
        return items
    
    material: EnumProperty(name="Materials", items=callback)
    
    def poll_object(context):
        return context.object and not context.object.library
    

    
    @classmethod
    def poll(cls, context):
        return cls.poll_object(context)

    def execute(self, context):
        # Get the index of the selected material
        mat_index = int(self.material)
        mat = bpy.data.materials[mat_index]
        context.object.active_material = mat
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    
class BU_OT_Select_all_items(bpy.types.Operator):
    """ Select all Mark tool assets """
    bl_idname = "bu.select_all_items"
    bl_label = "Select all"
    bl_description = "Select all materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.scene.mark_collection:
            cls.poll_message_set('Mark Tool is empty!')
            return False
        return True
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        for item in context.scene.mark_collection:
            if item.object_type == 'Collection':
                for obj in item.asset.objects:
                    obj.select_set(True)
            else:
                item.asset.select_set(True)
        return {'FINISHED'}    

class BU_OT_Isolated_Selected(bpy.types.Operator):
    """ Isolate all selected assets """
    bl_idname = "bu.isolate_selected"
    bl_label = "Isolated selected"
    bl_description = "Isolate selected assets"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.scene.mark_collection:
            cls.poll_message_set('Mark Tool is empty!')
            return False
        return True
    def execute(self, context):
        bpy.ops.view3d.localview()
        return {'FINISHED'}


        


classes =(

    BU_PT_MarkAssetsMainPanel,
    BU_PT_MarkTool,
    BU_PT_PreviewRenderScene,
    BU_PT_MarkTool_settings,
    BU_OT_MarkTool_Info,
    BU_OT_Add_AssetToMark_Mat,
    Remove_AssetToMark_Mat,
    MaterialBoolProperties,
    MaterialAssociation,
    AssetsToMark,
    BU_OT_AddToMarkTool,
    BU_OT_RemoveFromMarkTool,
    ClearMarkTool,
    confirmMark,
    BU_OT_MarkAsset,
    BU_OT_ClearMarked,
    ClearMarkedAsset,
    CatalogTargetProperty,
    MarkToolCatagories,
    BU_MT_MaterialSelector,
    BU_OT_Add_All_Mats,
    BU_OT_Remove_All_Mats,
    BU_OT_AssetAddTag,
    BU_OT_AssetRemoveTag,
    BU_OT_Select_all_items,
    BU_OT_Isolated_Selected,
    
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.adjust = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.mats_to_include = bpy.props.CollectionProperty(type=MaterialAssociation)
    bpy.types.Scene.mark_collection = bpy.props.CollectionProperty(type=AssetsToMark)
    bpy.types.Scene.catalog_target_enum = bpy.props.PointerProperty(type=CatalogTargetProperty)
    bpy.types.Scene.switch_marktool = bpy.props.PointerProperty(type=MarkToolCatagories)
    # bpy.types.Scene.material_include_bools = bpy.props.CollectionProperty(type=MaterialBoolProperties)

def unregister():
    del bpy.types.Scene.mark_collection
    del bpy.types.Scene.mats_to_include
    del bpy.types.Scene.catalog_target_enum
    del bpy.types.Scene.switch_marktool
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    










