import bpy
import os
import shutil
from ..utils import addon_info,catfile_handler,sync_manager
import textwrap
import math
from . import asset_bbox_logic
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
        obj = bpy.data.objects.get(item.name)
        if obj:
           
            # obj.scale =(item.scale,item.scale,item.scale)
            self.location = obj.location
            self.rotation = obj.rotation_euler
            self.scale = (obj.scale.x + obj.scale.y + obj.scale.z) / 3.0
    elif item.object_type == 'Collection':
        source_col = bpy.data.collections.get(item.name)
        item_instance = f'{item.name}_instance'
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
        return bpy.data.objects.get(item.name)
    elif item.object_type == 'Collection':
        item_instance = f'{item.name}_instance'
        if item_instance in bpy.data.objects:
            return bpy.data.objects.get(f'{item.name}_instance')
    
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
    name: StringProperty()
    idx: IntProperty()
    obj: PointerProperty(type=bpy.types.Object)
    viewport_visible: BoolProperty()
    mats:CollectionProperty(type=MaterialAssociation)
    override_type:BoolProperty()
    types: EnumProperty(items=addon_info.get_types() ,name ='Type', description='asset types')
    object_type: StringProperty()
    has_previews: BoolProperty()
    draw_render_settings: BoolProperty(default= False)
    draw_asset_data_settings: BoolProperty(default= False)
    render_bg: BoolProperty(default= True)
    render_logo: BoolProperty(default= True)
    override_camera: BoolProperty(default= False)
    draw_override_camera: BoolProperty(default= False)
    enable_cam_info: BoolProperty(default= False)
    cam_loc: FloatVectorProperty(default=(0.0,-2.0,0.9), size=3,subtype='XYZ',get=get_preview_camera_location,set=set_preview_camera_location)
    cam_rot: FloatVectorProperty(default=(1.39626,0.0,0.0), size=3,subtype='EULER',get=get_preview_camera_rotation,set=set_preview_camera_rotation)
    enable_offsets: BoolProperty(default= False)
    draw_enable_offsets: BoolProperty(default= False)
    location: FloatVectorProperty(default=(0.0,0.0,0.0),size=3,subtype='TRANSLATION',get=get_mark_asset_obj_location,set=set_mark_asset_obj_location)
    rotation: FloatVectorProperty(default=(0.0,0.0,0.436332), size=3,subtype='EULER',get=get_mark_asset_obj_rotation,set=set_mark_asset_obj_rotation)
    scale: FloatProperty(default=(1.0),precision=3,get=get_uniform_scale,set=set_uniform_scale)
    max_scale: FloatVectorProperty(default=(1.20,1.20,1.20), size=3,subtype='XYZ',precision=3,max=2.0)
    original_scale: FloatVectorProperty(default=(1.0,1.0,1.0), size=3,subtype='XYZ')

class ClearMarkTool(bpy.types.Operator):
    '''Clear the mark tool'''
    bl_idname = "wm.clear_mark_tool" 
    bl_label = "clear the mark tool"
    bl_options = {"REGISTER","UNDO"}

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
    bl_options = {"REGISTER","UNDO"}

    name: bpy.props.StringProperty()

    
    def execute(self, context):
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.name), None)
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
    bl_options = {"REGISTER","UNDO"}

    name: bpy.props.StringProperty()

    def execute(self, context):
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.name), None)
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
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.name), None)
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
    bl_options = {"REGISTER","UNDO"}

    idx: bpy.props.IntProperty()
    name: bpy.props.StringProperty()
    mat_name: bpy.props.StringProperty()

    def execute(self,context):
        matching_item = next((item for item in context.scene.mark_collection if self.name == item.name), None)
        if matching_item:
            for idx,mat in enumerate(matching_item.mats):
                if mat.name == self.mat_name:
                    matching_item.mats.remove(idx)
                    break
        return {'FINISHED'}
    

   

class AddToMarkTool(bpy.types.Operator):
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
        if not catfile_handler.check_current_catalogs_file_exist():
            cls.poll_message_set('Please get the core catalog file first!')
            return False
        if asset_preview_path =='':
            cls.poll_message_set('Please set the thumbnail upload path first!')
            return False
        if context.scene.mark_collection:
            cls.poll_message_set('Please clear the mark tool first!')
            return False
        
        return True
    


    def get_selected_ids(self,context):
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'OUTLINER':
                    with context.temp_override(window=window, area=area):
                        return context.selected_ids

    def get_mats_list(self,context,item):
        mat_list = []
        
        for idx,slot in enumerate(item.material_slots):
            if slot.material:
                mat = slot.material
                mat_list.append(mat)
        return mat_list

    def execute(self, context):           
        context.scene.mats_to_include.clear()
        context.scene.mark_collection.clear()
        selected_ids = self.get_selected_ids(context)
        for idx,id in enumerate(selected_ids):
            id.make_local()
            if id.name not in context.scene.mark_collection:
                markasset = context.scene.mark_collection.add()
                markasset.asset = id
                markasset.name = id.name
                markasset.idx = idx
                object_type = id.bl_rna.identifier
                if object_type == 'Object':
                    markasset.object_type = id.bl_rna.identifier
                    markasset.original_scale = id.scale
                elif object_type == 'Collection':
                    markasset.object_type = id.bl_rna.identifier
                    


        return {'FINISHED'}


class confirmMark(bpy.types.Operator):
    '''Add assets to Asset browser!'''
    bl_idname = "wm.confirm_mark" 
    bl_label = "Initialize mark for add process"
    bl_options = {"REGISTER"}

    def assign_previews(self,context,asset):
        asset_preview_path = addon_info.get_asset_preview_path()
        path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
        if os.path.exists(path):
            with bpy.context.temp_override(id=asset):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=path)

    def execute(self, context):
        bpy.ops.wm.save_userpref()
        addon_prefs = addon_info.get_addon_name().preferences
        author_name = addon_prefs.author
        
        for item in context.scene.mark_collection:
            if item.types == 'Material':
                # for mat in items.mats:
                for idx,slot in enumerate(item.mats):
                    
                    material = slot.material
                    material.asset_mark()
                    self.assign_previews(context,material)
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
            elif item.types == 'Object':
                obj = bpy.data.objects.get(item.name)
                if obj:
                    obj.rotation_euler = Euler((0, 0, 0))
                    obj.scale = Vector((1, 1, 1))
                    obj.location = Vector((0, 0, 0))
                asset = item.asset
                asset.asset_mark()
                self.assign_previews(context,asset)
                if author_name != '':
                    item.asset.asset_data.author = author_name
            
            elif item.object_type == 'Collection':
                asset = item.asset
                asset.asset_mark()
                self.assign_previews(context,asset)
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

       
    def execute(self, context):
        w= bpy.context.window
        a=[a for a in w.screen.areas if a.type == 'FILE_BROWSER']
        for area in bpy.context.screen.areas:
            if area.type == 'FILE_BROWSER':
                space_data = area.spaces.active
        if space_data.params.asset_library_ref == 'LOCAL':
    
            with bpy.context.temp_override(window=w,area=a[0]):
                for asset_file in context.selected_asset_files:
                    name = asset_file.name
                    if asset_file.id_type == 'MATERIAL':
                        bpy.data.materials[name].asset_clear()
                    if asset_file.id_type == 'OBJECT':
                        bpy.data.objects[name].asset_clear()

        for asset in context.selected_objects:
            if asset.asset_data:
                asset.asset_clear()

        return {'FINISHED'}
    

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

def draw_mat_add_op(self,context,layout,idx,item,mat):
    op = layout.operator('bu.add_asset_to_mark_mat', text="", icon='MATERIAL')
    # op.item = item
    op.idx = idx
    op.name = item.name
    op.mat_name = mat.name

def draw_mat_remove_op(self,context,layout,idx,item,mat):
    op = layout.operator('bu.remove_asset_to_mark_mat', text="", icon='MATERIAL',depress = True)
    # op.item = item
    op.idx = idx
    op.name = item.name
    op.mat_name = mat.name

def draw_mat_add_all(self,context,row,item):
    op = row.operator('bu.add_all_mats', text="Select All", icon='ADD')
    # op.item = item
    op.name = item.name

def draw_mat_remove_all(self,context,row,item):
    op = row.operator('bu.remove_all_mats', text="Deselect All", icon='REMOVE')
    # op.item = item
    op.name = item.name
    
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

def draw_preview_render_settings(self,context,main_row,idx,item):
    addon_prefs = addon_info.get_addon_name().preferences
    if addon_prefs.toggle_experimental_BU_Render_Previews:
        box = main_row.box()
        row = box.row()
        
        i = icons.get_icons()
        row.prop(item, 'render_bg', text="", icon='SCENE')
        row.prop(item, 'render_logo', text="", icon_value=i["BU_logo_v2"].icon_id)

        box = main_row.box()
        col = box.column()
        row = col.row()
        if not item.override_camera:
            spawn_op = row.operator('bu.spawn_preview_camera', text="", icon='VIEW_CAMERA', depress =False)
            spawn_op.idx = idx
        else:
            remove_op = row.operator('bu.remove_preview_camera', text="", icon='CAMERA_DATA',depress =True)
            remove_op.idx = idx
        # apply_op = box.operator('bu.apply_camera_transform', text="Apply", icon='LOCKED')
        # apply_op.idx = idx
        reset_op = row.operator('bu.reset_camera_transform', text="", icon='FILE_REFRESH')
        reset_op.idx = idx
        if item.override_camera :
            row.prop(item, 'draw_override_camera', text="", icon='TRIA_UP' if item.draw_override_camera else 'TRIA_DOWN')
            if item.draw_override_camera:
                row=col.row(align = True)
                row.prop(item, 'cam_loc', text="Location")
                row=col.row(align = True)
                row.prop(item, 'cam_rot', text="Rotation")

        box = main_row.box()
        col = box.column()
        row = col.row()
        row.alignment = 'EXPAND'
        # if item.object_type == 'Collection':
        if not item.enable_offsets:
            prev_dim = row.operator('bu.object_to_preview_demensions',text="Enable Offsets")
            prev_dim.idx = idx
        else:
            reset_dim =row.operator('bu.reset_object_original_dimensions',text="Reset to Original")
            reset_dim.idx = idx

        if item.enable_offsets:
            row.prop(item, 'draw_enable_offsets', text="", icon='TRIA_UP' if item.draw_enable_offsets else 'TRIA_DOWN')
            if item.draw_enable_offsets:
                row=col.row(align = True)
                row.prop(item,'location',text="Location Offset",)
                row=col.row(align = True)
                row.prop(item,'rotation',text="Rotation",)
                row=col.row(align = True)
                row.prop(item,'scale',text="Scale",)
                row=col.row(align = True)
                row=col.row(align = True)
        

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
        if item.draw_render_settings:
            draw_preview_render_settings(self,context,main_row,idx,item)
        
        box = main_row.box()
        box.enabled = True if item.asset.asset_data else False
        box.prop(item, 'draw_asset_data_settings', text='Metadata', icon='TRIA_UP' if item.draw_asset_data_settings else 'TRIA_DOWN')
        if item.draw_asset_data_settings:
            draw_metadata(self,context,box,idx,item.asset)


    elif item.types == 'Material':
        main_row.alignment = 'LEFT'
        box = main_row.box()
        row= box.row(align = True)
        draw_mat_add_all(self,context,row,item)
        draw_mat_remove_all(self,context,row,item)
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
                    matching_mat = next((item for item in item.mats if mat.name == item.name), None)
                    if not matching_mat:
                        draw_mat_add_op(self,context,row,mat_idx,item,mat)
                    else:
                        draw_mat_remove_op(self,context,row,mat_idx,item,mat)

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

def get_layer_object(context,item):
    '''Returns the view layer LayerCollection for a specificied Collection'''
    def scan_children(lc, result=None):
        if item.name in context.view_layer.layer_collection.collection.objects:
            return context.view_layer.layer_collection.collection.objects.get(item.name)
        else:
            for c in lc.children:
                if item.name in c.collection.objects:
                    return c.collection.objects.get(item.name)
                result = scan_children(c, result)
            return result

    return scan_children(bpy.context.view_layer.layer_collection)

def draw_marked(self,context):
    layout = self.layout
    row = layout.row()
    text = 'Make sure to use descriptive names for assets you want to add!\n Example for a mesh: SM_Door_Damaged | Example for Material: M_Wood_Peeled_Paint'
    _label_multiline(
        context=context,
        text=text,
        parent=layout
    )
    layout =self.layout

    for idx,item in enumerate(context.scene.mark_collection):
        addon_prefs=addon_info.get_addon_name().preferences
        box = layout.box()
        row = box.row(align = True)
        row.alignment = 'EXPAND' if addon_prefs.toggle_experimental_BU_Render_Previews else 'LEFT'
        box = row.box()
        if item.object_type == 'Object':
            name = item.name
            obj = context.scene.objects.get(name)
            if obj:
                box.prop(item,'viewport_visible', text = '', icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF',emboss=False)
                if item.viewport_visible:
                    obj.hide_set(True)
                else:
                    obj.hide_set(False)
        if item.object_type == 'Collection':
            if item.enable_offsets:
                name = item.name + '_instance'
                obj = context.scene.objects.get(name)
                if obj:
                    box.prop(item,'viewport_visible', text = '', icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF',emboss=False)
                    if item.viewport_visible:
                        obj.hide_set(True)
                    else:
                        obj.hide_set(False)
            else:
                collection =bpy.data.collections.get(item.name)
                original_col =get_layer_collection(collection)
                box.prop(original_col,'hide_viewport', text = '', icon = 'HIDE_OFF',emboss=False)
                
    # icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF'
    # icon = 'HIDE_ON' if original_col.hide_viewport == False else 'HIDE_OFF'
        # if  item.object_type == 'Collection':
        #     collection =bpy.data.collections.get(item.name)
        #     original_col =get_layer_collection(collection)
        #     # original_col.hide_viewport = True
        #     
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
            asset = item.mats.get(self.asset_name).material
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
                asset = item.mats.get(self.asset_name).material
            
        elif item.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                asset = geo_modifier.node_group 

        active_tag_index =asset.asset_data.active_tag
        if active_tag_index >= len(asset.asset_data.tags):
            active_tag_index =(len(asset.asset_data.tags)-1)

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


class BU_PT_AssetBrowser_Tools_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_label = 'Blender Universe asset browser tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Universe Kit'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        

class BU_PT_AssetBrowser_settings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_SETTINGS"
    bl_label = 'Asset Browser Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}

    addon_prefs = addon_info.get_addon_name().preferences
    
    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences     
        layout = self.layout
        lib_names = addon_info.get_original_lib_names()
        row = layout.row()
        row.label(text="Library file path setting")
        draw_lib_path_info(self,context,addon_prefs,lib_names)
        BU_PT_MarkTool_settings.draw(self,context)

def draw_lib_path_info(self,context, addon_prefs,lib_names):
    
    layout = self.layout
    # col = row.column()
    box = layout.box()
    row = box.row()
    row.label(text='Library Paths Info')
    
    # box.label(text=f' Author: Author not set',icon='ERROR')
    # row = box.row(align = True)
    # row.alignment = 'LEFT'              
    # row.label(text="Set Author",icon='CHECKMARK' if addon_prefs.author != '' else 'ERROR')
    # row.prop(addon_prefs,'author', text='')
    if context.scene.adjust ==False and addon_prefs.lib_path != '':
        row = box.row(align = True)
        row.alignment = 'LEFT'              
        
        row.label(text=f' Library Location: {addon_prefs.lib_path}',icon='CHECKMARK')
        row.prop(context.scene,'adjust', text = 'Unlock',toggle=True,icon='UNLOCKED')
    else:
        # box.label(text=f' Library path: Not set',icon='ERROR')
        row = box.row(align = True)
        row.alignment = 'LEFT'
        row.label(text=f'Library Location:',icon='ERROR' if addon_prefs.lib_path == '' else 'CHECKMARK')
        row.prop(addon_prefs,'lib_path', text='')
        row.prop(context.scene,'adjust', text = 'Lock',toggle=True,icon='LOCKED',invert_checkbox=True)
    if not any(lib_name in bpy.context.preferences.filepaths.asset_libraries for lib_name in lib_names):
        row = box.row(align = True)
        row.alignment = 'LEFT'
        row.label(text="We need to generate library paths",icon='ERROR')
        row.operator('bu.addlibrarypath', text = 'Generate Library paths', icon='NEWFOLDER')    
    for lib_name in lib_names:
        if lib_name in bpy.context.preferences.filepaths.asset_libraries:
            box.label(text=lib_name, icon='CHECKMARK')
    if any(lib_name in bpy.context.preferences.filepaths.asset_libraries for lib_name in lib_names):
        row = box.row(align = True)
        row.operator('bu.removelibrary', text = 'Clear library paths', icon='TRASH',)   
  
class BU_PT_MarkAssetsMainPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_MARKASSETS"
    bl_label = 'Mark Assets'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self,context):
        draw_disclaimer(self, context)
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.alignment = 'RIGHT'
        row.label(text='Append preview render scene for to create custom preview renders')
        row.operator("bu.append_preview_render_scene", text="Append Preview Render scene", icon='APPEND_BLEND')
    


class BU_PT_MarkTool(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_MARKTOOL"
    bl_label = 'Mark Tool'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_category = 'Blender Universe Kit'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        addon_prefs = addon_info.get_addon_name().preferences 
        dir_path = addon_prefs.lib_path
        if  dir_path !='':
            return True

    def draw(self,context): 
        
        addon_prefs = addon_info.get_addon_name().preferences 
        layout = self.layout
        asset_preview_path = addon_info.get_asset_preview_path()
        
        # layout.label(text = addon_prefs.author if addon_prefs.author !='' else 'Author name not set', icon='CHECKMARK' if addon_prefs.author !='' else 'ERROR')
        # layout.label(text = asset_preview_path if asset_preview_path !='' else 'preview images folder not set', icon='CHECKMARK' if asset_preview_path !='' else 'ERROR')
        
       
        row = layout.row()
        row.label(text = 'Tool to batch mark assets')
        row = layout.row()
        box = row.box()
        if addon_prefs.is_admin:
            scene = context.scene
            box.prop(scene.upload_target_enum, "switch_upload_target", text="")
        if sync_manager.SyncManager.is_sync_operator('bu.sync_catalog_file'):
            box.operator('bu.sync_catalog_file', text='Cancel Sync', icon='CANCEL')
        else:
            box.operator('bu.sync_catalog_file', text='Get catalog file', icon='OUTLINER')
       
        box = row.box()
        box.operator('wm.clear_mark_tool', text=('Clear Marked Assets'), icon = 'CANCEL')
        box.operator('wm.add_to_mark_tool', text=('Prepare to Mark Asset'), icon ='ADD')

        if len(context.scene.mark_collection)>0:
            draw_marked(self, context)
            row = layout.row()
            row.operator('wm.confirm_mark', text=('Mark Assets'), icon='BLENDER')
            row.operator('wm.clear_marked_assets', text =('Unmark assets'), icon = 'CANCEL')



class BU_PT_MarkTool_settings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_MARKTOOL_SETTINGS"
    bl_label = 'Mark Tool Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_category = 'Blender Universe Kit'
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        box = layout.box()
        box.label(text = 'Mark asset tool settings: ')
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text = 'Set author name')
        row.prop(addon_prefs, 'author', text = '')
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text='Set asset preview images folder')
        row.prop(addon_prefs, 'thumb_upload_path', text = '')
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.alert=True
        row.label(text = 'Experimental: Use at own risk! ')
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.prop(addon_prefs, 'toggle_experimental_BU_Render_Previews', text = 'Toggle Render Previews',toggle=True,icon ='OUTPUT')

        
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

    
    




        


classes =(
    BU_PT_AssetBrowser_Tools_Panel,
    BU_PT_AssetBrowser_settings,
    BU_PT_MarkAssetsMainPanel,
    BU_PT_MarkTool,
    BU_PT_MarkTool_settings,
    BU_OT_Add_AssetToMark_Mat,
    Remove_AssetToMark_Mat,
    MaterialBoolProperties,
    MaterialAssociation,
    AssetsToMark,
    AddToMarkTool,
    ClearMarkTool,
    confirmMark,
    ClearMarkedAsset,
    CatalogTargetProperty,
    BU_MT_MaterialSelector,
    BU_OT_Add_All_Mats,
    BU_OT_Remove_All_Mats,
    BU_OT_AssetAddTag,
    BU_OT_AssetRemoveTag,
    
    
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.adjust = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.mats_to_include = bpy.props.CollectionProperty(type=MaterialAssociation)
    bpy.types.Scene.mark_collection = bpy.props.CollectionProperty(type=AssetsToMark)
    bpy.types.Scene.catalog_target_enum = bpy.props.PointerProperty(type=CatalogTargetProperty)
    # bpy.types.Scene.material_include_bools = bpy.props.CollectionProperty(type=MaterialBoolProperties)

def unregister():
    del bpy.types.Scene.mark_collection
    del bpy.types.Scene.mats_to_include
    del bpy.types.Scene.catalog_target_enum
   
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    










