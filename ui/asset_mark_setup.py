import bpy
import numpy as np
import functools
import time

from bpy.types import Header, Panel, Menu, UIList

from bpy_extras import (
    asset_utils,
)
# from ..utils import space_filebrowser
from bpy.types import Context, Event
from ..operators.asset_mark_operations import get_asset_types
from ..utils import addon_info,catfile_handler
from pathlib import Path
import textwrap
from bpy.types import PropertyGroup,Operator
from bpy.props import BoolProperty,IntProperty,EnumProperty,StringProperty,PointerProperty,CollectionProperty
from collections import Counter
from itertools import chain



# flags_enum = iter(range(1, 100, 1))
asset_types = [
    # ("actions", "Actions", "Action", "ACTION", 2 ** 1),
    ("Object", "Object", "Object", "OBJECT_DATA", 2 ** 1),
    ("Material", "Materials", "Materials", "MATERIAL", 2 ** 2),
    # ("worlds", "Worlds", "Worlds", "WORLD", 2 ** 4),
    ("Geometry_Node", "Geometry Nodes", "Node Trees", "NODETREE", 2 ** 5),
    # ("Collection", "Collection", "Collection", "OUTLINER_COLLECTION", 2 ** 6),
    # ("hair_curves", "Hairs", "Hairs", "CURVES_DATA", 2 ** 7),
    # ("brushes", "Brushes", "Brushes", "BRUSH_DATA", 2 ** 8),
    # ("cache_files", "Cache Files", "Cache Files", "FILE_CACHE", 2 ** 9),
    # ("linestyles", "Freestyle Linestyles", "", "LINE_DATA", 2 ** 10),
    # ("images", "Images", "Images", "IMAGE_DATA", 2 ** 11),
    # ("masks", "Masks", "Masks", "MOD_MASK", 2 ** 13),
    # ("movieclips", "Movie Clips", "Movie Clips", "FILE_MOVIE", 2 **14),
    # ("paint_curves", "Paint Curves", "Paint Curves", "CURVE_BEZCURVE", 2 ** 15),
    # ("palettes", "Palettes", "Palettes", "COLOR", 2 ** 16),
    # ("particles", "Particle Systems", "Particle Systems", "PARTICLES", 2 ** 17),
    # ("scenes", "Scenes", "Scenes", "SCENE_DATA", 2 ** 18),
    # ("sounds", "Sounds", "Sounds", "SOUND", 2 ** 19),
    # ("Text", "Texts", "Texts", "TEXT", 2 ** 20),
    # ("Texture", "Textures", "Textures", "TEXTURE_DATA", 2 ** 21),
    # ("workspaces", "Workspaces", "Workspaces", "WORKSPACE", 2 ** 22),

    ]
# asset_types.sort(key=lambda t: t[0])
def get_types(*args, **kwargs):
    return asset_types



def get_object_type():
    return[
        ("ARMATURE", "Armature", "Armature", "ARMATURE_DATA", 2 ** 1),
        ("CAMERA", "Camera", "Camera", "CAMERA_DATA", 2 ** 2),
        ("CURVE", "Curve", "Curve", "CURVE_DATA", 2 ** 3),
        ("EMPTY", "Empty", "Empty", "EMPTY_DATA", 2 ** 4),
        ("GPENCIL", "Grease Pencil", "Grease Pencil", "OUTLINER_DATA_GREASEPENCIL", 2 ** 5),
        ("LIGHT", "Light", "Light", "LIGHT", 2 ** 6),
        ("LIGHT_PROBE", "Light Probe", "Light Probe", "OUTLINER_DATA_LIGHTPROBE", 2 ** 7),
        ("LATTICE", "Lattice", "Lattice", "LATTICE_DATA", 2 ** 8),
        ("MESH", "Mesh", "Mesh", "MESH_DATA", 2 ** 9),
        ("META", "Metaball", "Metaball", "META_DATA", 2 ** 10),
        ("POINTCLOUD", "Point Cloud", "Point Cloud", "POINTCLOUD_DATA", 2 ** 11),
        ("SPEAKER", "Speaker", "Speaker", "OUTLINER_DATA_SPEAKER", 2 ** 12),
        ("SURFACE", "Surface", "Surface", "SURFACE_DATA", 2 ** 13),
        ("VOLUME", "Volume", "Volume", "VOLUME_DATA", 2 ** 14),
        ("FONT", "Text", "Text", "FONT_DATA", 2 ** 15),
    ]



class IncludeMatList(PropertyGroup):
    material:PointerProperty(type=bpy.types.Material)
    name:StringProperty()
    include:BoolProperty()



class AssetsToMark(PropertyGroup): 
    asset: PointerProperty(type=bpy.types.ID)
    obj: PointerProperty(type=bpy.types.Object)
    mats:CollectionProperty(type=IncludeMatList)
    override_type:BoolProperty()
    types: EnumProperty(items=get_types() ,name ='Type', description='asset types')
    asset_type: StringProperty()
 
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
        context.scene.mats_to_include.clear()
        context.scene.mark_collection.clear()
        return {'FINISHED'}

class AddToMarkTool(bpy.types.Operator):
    '''Add selected assets to the mark tool'''
    bl_idname = "wm.add_to_mark_tool" 
    bl_label = "start the marking of assets process"
    bl_options = {"REGISTER","UNDO"}

    @classmethod
    def poll(cls,context):
        if not bpy.data.filepath:
            cls.poll_message_set('Cant mark asset if file is not saved to disk!')
            return False
        
        return True
    def get_selected_ids(self,context):
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'OUTLINER':
                    with context.temp_override(window=window, area=area):
                # selected_collections = [c for c in context.selected_ids if c.bl_rna.identifier == "Collection"]
                        return context.selected_ids

    def get_mats_list(self,context,item):
        mat_list = []
        
        for slot in item.material_slots:
            mat = slot.material
            mat_list.append(mat)
        return mat_list

    def execute(self, context):           
        context.scene.mats_to_include.clear()
        context.scene.mark_collection.clear()
        selected_ids = self.get_selected_ids(context)
        for id in selected_ids:
            if id.name not in context.scene.mark_collection:
                markasset = context.scene.mark_collection.add()
                markasset.asset = id
                atype = id.bl_rna.identifier
                if atype != 'Object':
                    markasset.asset_type = atype
                else:
                    markasset.asset_type = id.type
                    matlist = self.get_mats_list(context,id)
                    
                    for mat in matlist:
                        include_list = markasset.mats.add()
                        include_list.material = mat
                        include_list.name = mat.name
                        include_list.include = False

        return {'FINISHED'}
    

class confirmMark(bpy.types.Operator):
    '''Add assets to Asset browser!'''
    bl_idname = "wm.confirm_mark" 
    bl_label = "Initialize mark for add process"
    bl_options = {"REGISTER","UNDO"}

    def execute(self, context):
        assets =[]
        for item in context.scene.mark_collection:
            if item.types == 'Material':
                for mat in item.mats:
                    if mat.include != False:
                        assets.append(mat.material)
                        mat.material.asset_mark()
            else:
                assets.append(item.asset)
                item.asset.asset_mark()

        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        context.space_data.params.asset_library_ref = "LOCAL"
    
        return {'FINISHED'}   
              
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    

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


def draw_selected_properties(self,context,split,item):
    if item.types == 'Object':
        box = split.box()
        box.label(text ="Asset Name")
        col = box.column(align = True)
        col.prop(item.asset, 'name', text ="")

    if item.types == 'Material':
        box = split.box()
        box.label(text ="Material Name(s)")
        col = box.column(align = True)
        row= col.row()
        mats = item.mats
        if mats:
            for mat in mats:
                split = row.split(factor = 0.9)
                row_mat_include = split.row()
                row_mat_include.prop(mat, 'name', text ="", expand = True)
                split.prop(mat, 'include', icon = 'MATERIAL', toggle = True, icon_only = True)
                row_mat_include.enabled = mat.include
                row= col.row()
        else:
            box.label(text ="No Materials found !")


    if item.types == 'Geometry_Node':
        box = split.box()
        if 'GeometryNodes' in item.asset.modifiers.keys():
            g_nodes = item.asset.modifiers['GeometryNodes'].node_group
            
            box.label(text ="Node Group Name")
            col = box.column(align = True)
            col.prop(g_nodes, 'name', text ="", expand = True)
        else:
            box.label(text ="Node Group Name")
            col = box.column(align = True)
            box.label(text ="No GeometryNodes modifier found !")
   
   #Needs work
    if item.types == 'Texture':
        textures=[]
        box = split.box()
        box.label(text ="Materials")
        for slot in item.asset.material_slots:
            if slot.material:
                row = box.row(align = True)
                row.prop(slot.material, 'name', text ="", expand = True)
                row.prop(item,'mat',text="",icon ='MATERIAL',toggle =True)
                if item.mat == True:
                    if slot.material.node_tree:
                        for nodes in slot.material.node_tree.nodes:
                            if nodes.type=='TEX_IMAGE':
                                textures.append(nodes.image)
        box = split.box()
        box.label(text ="Texture Names")
        col = box.column(align = True)
        for t in textures:
            col.prop(t, 'name', text ="", expand = True)

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
        box = layout.box()
        row = box.row()
        split = row.split(factor =0.1)
        box = split.box()

        box.label(text ="Asset type")
        col = box.column(align = True)
        col.label(text= item.asset_type)

        box = split.box()
        col = box.column()
        col.enabled = True if item.asset.bl_rna.identifier == 'Object' else False
        row = col.row()

        row.label(text='Override type')
        row.prop(item, 'override_type',text ='Override', toggle =True)
        row = col.row()
        
        row.enabled = item.override_type
        row.prop(item,'types', text = '')
        draw_selected_properties(self,context,split,item)



        


def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

class BU_AssetBrowser_settings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_SETTINGS"
    bl_label = 'Asset Browser Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"

    def draw(self,context):
            layout = self.layout
            box = layout.box()
            row = box.row()
            row.label(text="Asset Upload Settings")
            row = box.row()
            addon_prefs = addon_info.get_addon_name().preferences
            row.label(text=f'Author: {addon_info.get_addon_name().preferences.author}')
            split = box.split(factor =0.1)
            row = split.row(align=True)
            row.label(text="Set Author")
            row = split.row()
            row.prop(addon_prefs,'author', text='')
            row.operator('bu.confirmsetting', text = 'save')
            row = split.row()
            


class MarkAssetsPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_MARKASSETS"
    bl_label = 'Mark Assets'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text = 'Tool to batch mark assets')
        row = layout.row()
        row.operator('wm.add_to_mark_tool', text=('Prepare to Mark Asset'))
        row.operator('wm.clear_mark_tool', text=('Clear Marked Assets'))
        if context.scene.mark_collection:
            draw_marked(self, context)
            row = layout.row()
            row.operator('wm.confirm_mark', text=('Mark Assets'))
            row.operator('wm.clear_marked_assets', text =('Unmark assets'))

class AssetBrowser_Tools_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_label = 'Baked Suite asset browser tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Tools'

    def draw(self, context):
        layout = self.layout
        row = layout.row()


classes =(
    IncludeMatList,
    AssetsToMark,
    AddToMarkTool,
    ClearMarkTool,
    confirmMark,
    AssetBrowser_Tools_Panel,
    BU_AssetBrowser_settings,
    MarkAssetsPanel,
    ClearMarkedAsset,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mats_to_include = bpy.props.CollectionProperty(type=IncludeMatList)
    bpy.types.Scene.mark_collection = bpy.props.CollectionProperty(type=AssetsToMark)


def unregister():
    del bpy.types.Scene.mark_collection
    del bpy.types.Scene.mats_to_include
    for cls in classes:
        bpy.utils.unregister_class(cls)
    










