import bpy
import os
import shutil
from ..utils import addon_info,catfile_handler,sync_manager
import textwrap
from bpy.types import PropertyGroup
from bpy.props import BoolProperty,IntProperty,EnumProperty,StringProperty,PointerProperty,CollectionProperty







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

class MaterialBoolProperties(bpy.types.PropertyGroup):
    include:BoolProperty(name="Include", default=False, description="Include this material")


            


class AssetsToMark(PropertyGroup): 
    asset: PointerProperty(type=bpy.types.ID)
    name: StringProperty()
    obj: PointerProperty(type=bpy.types.Object)
    mats:CollectionProperty(type=MaterialAssociation)
    override_type:BoolProperty()
    types: EnumProperty(items=addon_info.get_types() ,name ='Type', description='asset types')
    object_type: StringProperty()
    has_previews: BoolProperty()
 
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
        if not bpy.data.filepath:
            cls.poll_message_set('Cant mark asset if file is not saved to disk!')
        if not catfile_handler.check_current_catalogs_file_exist():
            cls.poll_message_set('Please get the core catalog file first!')
            return False
        if addon_prefs.thumb_upload_path =='':
            cls.poll_message_set('Please set the thumbnail upload path first!')
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
        for id in selected_ids:
            if id.name not in context.scene.mark_collection:
                markasset = context.scene.mark_collection.add()
                markasset.asset = id
                markasset.name = id.name
                
                object_type = id.bl_rna.identifier
                
                if object_type != 'Object':
                    markasset.object_type = object_type
                else:
                    markasset.object_type = id.type
                    # matlist = self.get_mats_list(context,id)
                    
                    # for mat in matlist:
                    #     include_list = markasset.mats.add()
                    #     include_list.material = mat
                    #     include_list.name = mat.name
                    #     include_list.include = False

        return {'FINISHED'}


class confirmMark(bpy.types.Operator):
    '''Add assets to Asset browser!'''
    bl_idname = "wm.confirm_mark" 
    bl_label = "Initialize mark for add process"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.save_userpref()
        addon_prefs = addon_info.get_addon_name().preferences
        author_name = addon_prefs.author
        preview_dir = addon_prefs.thumb_upload_path
        for item in context.scene.mark_collection:
            if item.types == 'Material':
                # for mat in items.mats:
                for idx,slot in enumerate(item.mats):
                    
                    
                    slot.material.asset_mark()
                    path = f'{preview_dir}{os.sep}preview_{slot.material.name}.png'
                    if os.path.exists(path):
                        with bpy.context.temp_override(id=slot.material):
                            bpy.ops.ed.lib_id_load_custom_preview(filepath=path)
                    if author_name != '':
                        slot.material.asset_data.author = author_name
                    else:
                        slot.material.asset_data.author = 'Anonymous'   
            elif item.types == 'Geometry_Node':
                for item in item.asset.modifiers.values():
                    if item.type =='NODES':
                        item.node_group.asset_mark()
                        if author_name != '':
                            item.node_group.asset_data.author = author_name
                        else:
                            item.node_group.asset_data.author = 'Anonymous'
            else:
                item.asset.asset_mark()
                if author_name != '':
                    item.asset.asset_data.author = author_name
                else:
                    item.asset.asset_data.author = 'Anonymous'
                    
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

def draw_mat_add_op(self,context,split,idx,item,mat):
    op = split.operator('bu.add_asset_to_mark_mat', text="", icon='MATERIAL')
    # op.item = item
    op.idx = idx
    op.name = item.name
    op.mat_name = mat.name

def draw_mat_remove_op(self,context,split,idx,item,mat):
    op = split.operator('bu.remove_asset_to_mark_mat', text="", icon='MATERIAL',depress = True)
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
            
def draw_has_previews(self, context,row,asset):

    # Iterate through asset's material slots and add them to mats
        addon_prefs = addon_info.get_addon_name().preferences
        preview_dir = addon_prefs.thumb_upload_path
        path = f'{preview_dir}{os.sep}preview_{asset.name}.png'
        ph_path = f'{preview_dir}{os.sep}PH_preview_{asset.name}.png'
        
        if os.path.exists(path) and os.path.exists(ph_path):
            row.label(text ="",icon='IMAGE_RGB_ALPHA')
        else:
            row.label(text ="",icon='OUTPUT')
            # row.operator("bu.render_previews", icon='OUTPUT', text="" )
        
def draw_selected_properties(self,context,split,item):
    material_names = []
    scene = context.scene
    if item.types == 'Object':
        box = split.box()
        box.label(text ="Asset Name")
        col = box.column(align = True)
        # col.template_icon_view(item.asset, 'preview',scale=2)
        row = col.row()
        row.prop(item.asset, 'name', text ="")
        draw_has_previews(self,context,row,item)
        



    if item.types == 'Material':
        box = split.box()
        row= box.row(align = True)
        row.label(text ="Material Name(s)")
        row = box.row(align = True)
        draw_mat_add_all(self,context,row,item)
        draw_mat_remove_all(self,context,row,item)
        col = box.column(align = True)
        row= col.row(align = True)
        
        if item.asset.material_slots:
            for idx,slot in enumerate(item.asset.material_slots):
                if slot.material:
                    mat = slot.material
                    if mat.name not in material_names:
                        material_names.append(mat.name)
                        row.prop(mat, 'name', text ="",icon_value =mat.preview.icon_id)
                        row.alignment = 'EXPAND'
                        matching_mat = next((item for item in item.mats if mat.name == item.name), None)
                        if not matching_mat:
                            draw_mat_add_op(self,context,row,idx,item,mat)
                        else:
                            draw_mat_remove_op(self,context,row,idx,item,mat)
                        
                        if matching_mat:
                            draw_has_previews(self,context,row,matching_mat)
                        else:
                            row.label(text ="",icon='SHADING_BBOX' )
                else:
                    row.enabled
                    row.alignment = 'EXPAND'
                    row.operator("bu.material_select", icon='MATERIAL', text="Select Material" )
                row= col.row(align = True)
        else:
            row.label(text ="No Materials found !")
        
        # draw_mat_previews(self,context,box,item)    
                # mat = slot
                # mat_include = item.mats[self.idx]
                # box.label(text ="No Materials found !")


    if item.types == 'Geometry_Node':
        box = split.box()
        if 'GeometryNodes' in item.asset.modifiers.keys():
            g_nodes = item.asset.modifiers['GeometryNodes'].node_group
            if g_nodes is not None:
                box.label(text ="Node Group Name")
                col = box.column(align = True)
                row =col.row()
                row.prop(g_nodes, 'name', text ="", expand = True)
                draw_has_previews(self,context,row,g_nodes)
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
        row = box.row(align = True)
        split = row.split(factor =0.2,align = True)
        box = split.box()
       
        box.label(text= 'Object type')
        
        box.label(text= item.object_type)
        box = split.box()
        box.label(text='Asset type')
        if item.asset.bl_rna.identifier == 'Object':
            box.prop(item,'types', text = '')
        elif item.asset.bl_rna.identifier == 'Collection':
            box.label(text='Collection')
        else:
            box.label(text='This type is not supported yet')
        draw_selected_properties(self,context,split,item)
        


def draw_disclaimer(self, context):
    disclaimer = 'By uploading your own assets, you confirm that you have the necessary rights and permissions to use and share the content. You understand that you are solely responsible for any copyright infringement or violation of intellectual property rights. We assume no liability for the content you upload. Please ensure you have the appropriate authorizations before proceeding.'
    wrapp = textwrap.TextWrapper(width=int(context.region.width/6) ) #50 = maximum length       
    wList = wrapp.wrap(text=disclaimer)
    box = self.layout.box()
    for text in wList:
        box.label(text=text)

       


def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)


#seperate this in new file
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

def draw_lib_path_info(self,context, addon_prefs,lib_names):
    
    layout = self.layout
    # col = row.column()
    box = layout.box()
    row = box.row()
    row.label(text='Library Paths Info')
    
    # box.label(text=f' Author: Author not set',icon='ERROR')
    row = box.row(align = True)
    row.alignment = 'LEFT'              
    row.label(text="Set Author",icon='CHECKMARK' if addon_prefs.author != '' else 'ERROR')
    row.prop(addon_prefs,'author', text='')
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

    
    
class BU_PT_MarkAssetsMainPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_MARKASSETS"
    bl_label = 'Mark Assets'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self,context):
        draw_disclaimer(self, context)
    
def get_asset_preview(self,context):
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    selected_assets = context.selected_asset_files
                    return selected_assets

class BU_PT_MarkTool(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_MARKTOOL"
    bl_label = 'Mark Tool'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_MARKASSETS"
    bl_category = 'Blender Universe Kit'
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
        layout.label(text = addon_prefs.author if addon_prefs.author !='' else 'Author name not set', icon='CHECKMARK' if addon_prefs.author !='' else 'ERROR')
        layout.label(text = addon_prefs.thumb_upload_path if addon_prefs.thumb_upload_path !='' else 'preview images folder not set', icon='CHECKMARK' if addon_prefs.thumb_upload_path !='' else 'ERROR')
        row = layout.row()
        # row.operator('bu.test_op', text = 'test', icon='ERROR')

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
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self,context):
        addon_prefs = addon_info.get_addon_name().preferences
        layout = self.layout
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text = 'Set author name')
        row.prop(addon_prefs, 'author', text = '')
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text='Set asset preview images folder')
        row.prop(addon_prefs, 'thumb_upload_path', text = '')

#Move this to a seperate file as Core panel
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
        
        


classes =(
    BU_OT_Add_AssetToMark_Mat,
    Remove_AssetToMark_Mat,
    MaterialBoolProperties,
    MaterialAssociation,
    AssetsToMark,
    AddToMarkTool,
    ClearMarkTool,
    confirmMark,
    BU_PT_AssetBrowser_Tools_Panel,
    BU_PT_AssetBrowser_settings,
    BU_PT_MarkAssetsMainPanel,
    BU_PT_MarkTool_settings,
    BU_PT_MarkTool,
    ClearMarkedAsset,
    CatalogTargetProperty,
    BU_MT_MaterialSelector,
    BU_OT_Add_All_Mats,
    BU_OT_Remove_All_Mats,
    
    
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
    










