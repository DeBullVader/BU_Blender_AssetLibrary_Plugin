import bpy
import numpy as np
import functools
import time
import os
from bpy.types import Header, Panel, Menu, UIList
import shutil
from bpy_extras import (
    asset_utils,
)
# from ..utils import space_filebrowser
from bpy.types import Context, Event
# from ..operators import library_download
from ..utils import addon_info,catfile_handler
from pathlib import Path
import textwrap
from bpy.types import PropertyGroup,Operator
from bpy.props import BoolProperty,IntProperty,EnumProperty,StringProperty,PointerProperty,CollectionProperty
from collections import Counter
from itertools import chain
# from ..operators import library_download
# from ..operators import library_download



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

# def DownloadFile(FileId,fileName,target_lib):
#     # libpaths = BULibPath()
#     try:
#         authService = Gservice()

#                 # pylint: disable=maybe-no-member
#         request = authService.files().get_media(fileId=FileId)
#         file = io.BytesIO()
#         downloader = MediaIoBaseDownload(file, request)
#         done = False
#         while done is False:
#             status, done = downloader.next_chunk()
#             print({"INFO"}, f"{fileName} has been dowloaded")
#         file.seek(0)
        
#         with open(os.path.join(target_lib.path, fileName), 'wb') as f:
#             f.write(file.read())
#             f.close()
#             if ".zip" in fileName:
#                 fname = target_lib.path + os.sep + fileName
                
        
#                 if not fileName == "blender_assets.cats.zip":
#                     foldername = str.removesuffix(fname,'.zip')
#                     if os.path.exists(foldername):
#                         shutil.unpack_archive(fname, foldername, 'zip')
#                         os.remove(fname)
#                     else:
#                         os.makedirs(foldername)
#                         shutil.unpack_archive(fname, foldername, 'zip')
#                         os.remove(fname)
#                 else:
#                     shutil.unpack_archive(fname, target_lib.path, 'zip')
#                     os.remove(fname)
                    

           
                    
#     except HttpError as error:
#         print(F'An error occurred: {error}')
    
#     # file = None
#     return fileName


class CopyCatalogFile(bpy.types.Operator):
    '''Copy the catalog file'''
    bl_idname = "wm.copy_catalog_file" 
    bl_label = "Copy core catalog file"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls,context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        if  dir_path =='':
            cls.poll_message_set('Please set a library path in prefferences.')
            return False
        if not bpy.data.filepath:
            cls.poll_message_set('Please make sure your file is saved')
        # elif catfile_handler.check_current_catalogs_file_exist():
        #     cls.poll_message_set('Catalog file already exists!')
        #     return False
        else:
            return True
        
    
    def execute(self, context):
        file_id = '1xS4Q2BG4SqwTKuCHIW_jXfa93XiWu8TC'
        file_name ='blender_assets.cats.zip'
        current_file_dir = bpy.data.filepath
        core_lib = addon_info.get_core_asset_library()
        # print(core_lib.__dir__())
        # library_download.DownloadFile(file_id,file_name,core_lib)
        catfile = 'blender_assets.cats.txt'

        current_filepath,blendfile = os.path.split(bpy.data.filepath)
        shutil.copy(os.path.join(core_lib.path,catfile), os.path.join(current_filepath,catfile))
        current_filepath_cat_file = os.path.join(current_filepath,catfile)

        if current_filepath_cat_file:
            for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'FILE_BROWSER':
                        with context.temp_override(window=window, area=area):
                            context.space_data.params.asset_library_ref = 'LOCAL'
                            if context.space_data.params.asset_library_ref == 'LOCAL':
                                bpy.ops.asset.catalog_new()
                                bpy.ops.asset.catalogs_save()
                                bpy.ops.asset.catalog_undo()
                                bpy.ops.asset.catalogs_save()
                                
                                
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
        if not catfile_handler.check_current_catalogs_file_exist():
            cls.poll_message_set('Please get the core catalog file first!')
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
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.save_userpref()
        assets =[]
        addon_name = addon_info.get_addon_name()
        author_name = addon_name.preferences.author
        for item in context.scene.mark_collection:
            if item.types == 'Material':
                for idx,slot in enumerate(item.asset.material_slots):
                    if item.mats[idx].include != False:
                        assets.append(slot.material) # old code?
                        slot.material.asset_mark()
                        if author_name != '':
                            slot.material.asset_data.author = author_name
                        else:
                            slot.material.asset_data.author = 'Anonymous'    
            else:
                assets.append(item.asset)# old code?
                item.asset.asset_mark()
                if author_name != '':
                    item.asset.asset_data.author = author_name
                else:
                    item.asset.asset_data.author = 'Anonymous'

                

        # for window in context.window_manager.windows:
        #     screen = window.screen
        #     for area in screen.areas:
        #         if area.type == 'FILE_BROWSER':
        #             with context.temp_override(window=window, area=area):
        #                 context.space_data.params.asset_library_ref = "LOCAL"
                        

    
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
        for idx,slot in enumerate(item.asset.material_slots):
            mat = slot.material
            mat_include = item.mats[idx]
            split = row.split(factor = 0.9)
            row_mat_include = split.row()
            row_mat_include.prop(mat, 'name', text ="")
            split.prop(mat_include, 'include', icon = 'MATERIAL', toggle = True, icon_only = True)
            row_mat_include.enabled = mat_include.include
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
    # if item.types == 'Texture':
    #     textures=[]
    #     box = split.box()
    #     box.label(text ="Materials")
    #     for slot in item.asset.material_slots:
    #         if slot.material:
    #             row = box.row(align = True)
    #             row.prop(slot.material, 'name', text ="", expand = True)
    #             row.prop(item,'mat',text="",icon ='MATERIAL',toggle =True)
    #             if item.mat == True:
    #                 if slot.material.node_tree:
    #                     for nodes in slot.material.node_tree.nodes:
    #                         if nodes.type=='TEX_IMAGE':
    #                             textures.append(nodes.image)
    #     box = split.box()
    #     box.label(text ="Texture Names")
    #     col = box.column(align = True)
    #     for t in textures:
    #         col.prop(t, 'name', text ="", expand = True)

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



def draw_disclaimer(self, context):
    disclaimer = 'By uploading your own assets, you confirm that you have the necessary rights and permissions to use and share the content. You understand that you are solely responsible for any copyright infringement or violation of intellectual property rights. We assume no liability for the content you upload. Please ensure you have the appropriate authorizations before proceeding.'
    wrapp = textwrap.TextWrapper(width=100) #50 = maximum length       
    wList = wrapp.wrap(text=disclaimer)
    box = self.layout.box()
    for text in wList:
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text=text)

       


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
            row = box.row(align=True)
            row.label(text="Asset Upload Settings")
            row = box.row(align=True)
            addon_prefs = addon_info.get_addon_name().preferences
            row.label(text=f'Author: {addon_info.get_addon_name().preferences.author}')
            row = box.row(align=True)
            row.label(text="Set Author")
            row.prop(addon_prefs,'author', text='')

            dir_path = addon_info.get_addon_name().preferences.lib_path
            if dir_path == '' or 'BU_AssetLibrary_Core' not in bpy.context.preferences.filepaths.asset_libraries:
                box = layout.box()
                row = box.row(align=True)
                row.label(text="Library file path setting")
                row = box.row()
                row.label(text=f' Choose Library_Path: {addon_info.get_addon_name().preferences.lib_path}')
                row.prop(addon_prefs,'lib_path', text='')
                row = box.row(align=True)
                row.operator('bu.addlibrarypath', text = 'Add Library paths', icon='ERROR')
                row = box.row(align=True)
                
            if 'BU_AssetLibrary_Core' in bpy.context.preferences.filepaths.asset_libraries and dir_path !='':
                box = layout.box()
                row_tooltip = box.row()
                box = row_tooltip.box()
                row = box.row()
                row.label(text="How to download the library!!")
                row = box.row()
                row.label(text="To download the library open the asset browser, Navigate to the Core Library.")
                row = box.row()
                row.label(text="Then Click the 'Check for updates' button.")
                row = box.row()
                row.label(text="Then press update library to initiate the download process")
                row=box.row(align=True)
                split = row.split(factor =0.6)
                lib_path = addon_info.get_addon_name().preferences.lib_path
                row.label(text=f'Current Library Path: {lib_path}')
                row.operator('bu.removelibrary', text = 'Remove Entire Library', icon='ERROR')
                row=box.row()
                row.label(text="Change to a new Library directory")
                row=box.row()
                split = row.split(factor= 0.6)
                col = split.column()
                col.prop(addon_info.get_addon_name().preferences,"new_lib_path", text ='')
                col = split.column()
                col.operator('bu.changelibrarypath', text = 'Change library directory')
            row = layout.row()
            row.operator('bu.confirmsetting', text = 'save preferences')

        
class MarkAssetsPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_MARKASSETS"
    bl_label = 'Mark Assets'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"


    def draw(self,context):
        addon_name = addon_info.get_addon_name()
        dir_path = addon_name.preferences.lib_path
        layout = self.layout
        row = layout.row()
        if  dir_path !='':
            row.label(text = 'Tool to batch mark assets')
            row = layout.row()
            row.operator('wm.copy_catalog_file', text=('Get core catalog file'))
            row = layout.row()
            row.operator('wm.add_to_mark_tool', text=('Prepare to Mark Asset'))
            row.operator('wm.clear_mark_tool', text=('Clear Marked Assets'))
            if len(context.scene.mark_collection)>0:
                draw_marked(self, context)
                row = layout.row()
                row.operator('wm.confirm_mark', text=('Mark Assets'))
                row.operator('wm.clear_marked_assets', text =('Unmark assets'))
        else:
            row.label(text = 'Please set a library path in preferences.', icon = 'ERROR')

class AssetBrowser_Tools_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_label = 'Baked Suite asset browser tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Tools'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        draw_disclaimer(self, context)


classes =(
    IncludeMatList,
    AssetsToMark,
    CopyCatalogFile,
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
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    










