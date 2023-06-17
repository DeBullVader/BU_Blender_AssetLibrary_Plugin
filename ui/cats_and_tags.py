import bpy
from bpy_extras import (
    asset_utils,
)
from bpy.types import Context, Event,Header, Panel, Menu, UIList
from ..utils import addon_info,catfile_handler
from pathlib import Path
import textwrap
from bpy.types import PropertyGroup,Operator
from bpy.props import BoolProperty,IntProperty,EnumProperty,StringProperty,PointerProperty,CollectionProperty

selected_assets = []
def get_main_cats():
    cats = catfile_handler.get_current_file_catalogs()
    main_cats_list={}
    for uuid,tree,name in cats:
        main_cats_list[tree]=uuid
        
    return main_cats_list

class TagsList(PropertyGroup):
    tag_name:StringProperty(name="Name",description= 'tag to add',default='New Tag')

class CatsAndTags(PropertyGroup):

    def get_subcats(self,context):
        if self.select_catalog !='NONE':
            self.catalog_path = self.catalog_path + self.select_catalog+'/'
            self.get_and_add_subcatalogs(context)
        
    def get_and_add_subcatalogs(self,context):
        main_cats_dict = get_main_cats()
        main_cats_list = list(main_cats_dict.keys())
        count=0
        catalogs = []
        cat_dict={}
        cat_dict['None'] =('NONE','None','','OUTLINER',count)
        cats =[]
        items =[]
        cat_depth =0
        max_depth = max(main_cats_list,key=lambda x: x.count('/')).count('/')+1
        
        while cat_depth != max_depth:
            for catalog_string in main_cats_list:
                catalog_parts = catalog_string.split("/")
                if catalog_parts[cat_depth if cat_depth ==0 else cat_depth:] not in catalogs:
                    if catalog_string.count('/') == cat_depth:
                        count+=1
                        catalog = catalog_parts[cat_depth if cat_depth ==0 else cat_depth:][0]
                        catalog_item = (catalog,catalog,'','OUTLINER',count)
                        cat_dict[catalog_string]=catalog_item
            if cat_depth==max_depth:
                break
            else:
                cat_depth+=1
        
        dict = cat_dict
        catalog_path = self.catalog_path
        select_cat_depth = catalog_path.count('/')

        if catalog_path =='':
            cats = [dict[key] for key in dict.keys() if '/' not in key]
            items.clear()
            items.extend(cats)
            return items
        else:
            items.clear()
            keys_list = list(dict.keys())
            item_index = keys_list.index(catalog_path.removesuffix('/'))
            cats = [dict[key] for key in dict.keys() if str(catalog_path) in key and key.count('/') == select_cat_depth ]
            if len(cats) !=0:
                items.append(('NONE','Choose a subcatalog','','OUTLINER',item_index))
                items.extend(cats)
            return items
    asset_name:StringProperty()
    select_catalog: EnumProperty(items=get_and_add_subcatalogs,name='Catalogs',description='Catalogs',update=get_subcats)
    asset_type:StringProperty()
    m_object:PointerProperty(type=bpy.types.Object)
    m_material:PointerProperty(type=bpy.types.Material)
    catalog_uuid: StringProperty()
    catalog_name: StringProperty()
    catalog_path:StringProperty()
    tags:CollectionProperty(type=TagsList)
    tags_list_index:IntProperty(name = "tags list index", default = 0)



# class confirmMark(bpy.types.Operator):
#     '''Add assets to Assetbrowser!'''
#     bl_idname = "wm.confirm_mark" 
#     bl_label = "Initialize mark for add process"
#     bl_options = {"REGISTER","UNDO"}

#     def execute(self, context):
#         assets =[]
#         main_cat_dict = get_main_cats()
#         for item in context.scene.mark_collection:
 
#             if item.catalog_path !='':
#                 item.catalog_uuid = main_cat_dict[item.catalog_path.removesuffix('/')]
                
#                 tree = item.catalog_path.removesuffix('/')
#                 item.catalog_name =tree.replace('/','-')
#                 if item.types == 'Material':
#                     for mat in item.mats:
#                         if mat.include != False:
#                             assets.append(mat.material)
#                             mat.material.asset_mark()
                           
                            # MOVE THIS TO NEW FILE
                            # if  mat.material.asset_data:
                            #     mat.material.asset_data.catalog_id = item.catalog_uuid
                            #     set_catalog_for_asset(item.catalog_uuid,tree,item.catalog_name)
                            #     set_tags_for_asset(context,mat.material)
       
                # else:
                #     assets.append(item.asset)
                #     item.asset.asset_mark()

                    # MOVE THIS TO NEW FILE
                    # if item.asset.asset_data:
                        # item.asset.asset_data.catalog_id = item.catalog_uuid
                        # set_catalog_for_asset(item.catalog_uuid,tree,item.catalog_name)
                        # set_tags_for_asset(context,item.asset)


        #     else:
        #         pass
        # for window in context.window_manager.windows:
        #     screen = window.screen
        #     for area in screen.areas:
        #         if area.type == 'FILE_BROWSER':
        #             with context.temp_override(window=window, area=area):
        #                 context.space_data.params.asset_library_ref = "LOCAL"
        
        # # currently crashed blender. 
        # #sleep_until_previews_are_done(assets, message_end)

        # return {'FINISHED'}   



class ResetCatalog(Operator):
    bl_idname = "wm.reset_catalog" 
    bl_label = "Select what catalog the asset should be placed in"
    bl_options = {"REGISTER"}
    item_index:IntProperty()
       
    def execute(self, context):
        context.scene.cats_and_tags[self.item_index].catalog_path = ''
        return {'FINISHED'}
    
class AddNewCatalog(bpy.types.Operator):
    bl_idname = "wm.add_new_catalog" 
    bl_label = "Add a new catalog at current location"
    bl_options = {"REGISTER"}
    item_index:IntProperty()
    new_catalog:StringProperty()

    def execute(self,context):
        item = context.scene.cats_and_tags[self.item_index]
        main_cats_dict = get_main_cats()
        self.new_catalog = item.catalog_path+self.new_catalog
        if self.new_catalog not in main_cats_dict and self.new_catalog != '':
            uuid =catfile_handler.ensure_or_create_catalog_definition(tree=self.new_catalog)
            main_cats_dict[self.new_catalog] = uuid
            item.catalog_path = self.new_catalog+'/'
            item.catalog_uuid = uuid
            item.catalog_name = self.new_catalog.replace('/','-')
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        context.space_data.params.asset_library_ref = "ALL"
                        context.space_data.params.asset_library_ref = "LOCAL"
                        bpy.ops.asset.catalog_new()
                        bpy.ops.asset.catalog_undo()
        self.new_catalog = ''

        return {'FINISHED'}
    
    def draw(self,context):
        item = context.scene.cats_and_tags[self.item_index]
        layout = self.layout
        
        row = layout.row()
        row.label(text=f"{item.catalog_path+self.new_catalog}")
        row.prop(self,"new_catalog", text="Insert New Catalog")

    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self)

def get_added_cat_items(context):
    get_added_cat_items.added_items =[]
    cats = catfile_handler.compare_catalogs()
    keys = cats.keys()
    for idx,key in enumerate(keys):
        if key not in get_added_cat_items.added_items:
            get_added_cat_items.added_items.append((key,key,'Added catalogs','OUTLINER',idx))
    # get_added_cat_items.user_cats.extend(added_items)
    return get_added_cat_items.added_items
get_added_cat_items.added_items=[]

class GetUserAddedCats(PropertyGroup):
 added_cats:EnumProperty(
        # options={"ENUM_FLAG"},
        items=lambda self, context: get_added_cat_items.added_items,
        name="Added Catalogs",
        description='Remove added catalogs',
    )

class RemoveNewCatalog(bpy.types.Operator):
    bl_idname = "wm.remove_new_catalog" 
    bl_label = "start the marking of assets process"
    bl_options = {"REGISTER"}

    item_index:IntProperty()
    
    def execute(self,context):
        uuid_to_remove =[]
        user_cats = context.scene.user_added_cats
        cats = catfile_handler.compare_catalogs()

        catalog_filepath = catfile_handler.get_current_file_catalog_filepath()
        keys = [key for key in cats.keys() if user_cats.added_cats in key]
        for key in keys:
            catfile_handler.remove_catalog_by_uuid(catalog_filepath,cats[key])
        return {'FINISHED'}
    
    def draw(self,context):
        layout = self.layout
        col = layout.column()
        user_cats = context.scene.user_added_cats
        get_added_cat_items(context)
        col.prop(user_cats,'added_cats',text ='')
        
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self)


 




class LIST_OT_NewItem(Operator):
    """Add a new item to the list.""" 
    bl_idname = "tags_list.new_item" 
    bl_label = "Add a new item" 
    bl_options = {"REGISTER"}

    item_index:IntProperty()
    def execute(self, context):
        asset = selected_assets[self.item_index]
        asset_list = context.scene.cats_and_tags[self.item_index]

        new_tag= asset_list.tags.add()
        new_tag.tag_name = 'New Tag'
        # new_tag.tag = 'New Tag'
        return{'FINISHED'}
    
class LIST_OT_DeleteItem(Operator): 
    """Delete the selected item from the list.""" 
    bl_idname = "tags_list.delete_item" 
    bl_label = "Deletes an item"
    bl_options = {"REGISTER"}

    item_index:IntProperty()
    # @classmethod 
    # def poll(self, context):
    #     if context.scene.mark_collection[self.item_index].tags:
    #         return True
    #     else:
    #         return False
    def execute(self, context): 
        asset_tags = context.scene.cats_and_tags[self.item_index].tags
        index = context.scene.cats_and_tags[self.item_index].tags_list_index 
        asset_tags.remove(index) 
        index = min(max(0,index -1),len(asset_tags)-1)
        return{'FINISHED'}

class GeneratePreview(bpy.types.Operator):
    bl_idname = "wm.generate_preview" 
    bl_label = "Generate preview"
    bl_options = {"REGISTER"}

    item_index: IntProperty()
    @classmethod
    def poll(cls,context):
        if not selected_assets:
            cls.poll_message_set('No asset browser assets selected!')
            return False
        return True 
    def execute(self, context):
       
        asset = selected_assets[self.item_index]
            
        asset.local_id.asset_generate_preview()
        return{'RUNNING_MODAL'}

class ASSETBROWSER_UL_asset_tags(UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        tag = item
        # Make sure your code supports all 3 layout types if 
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            # layout.label(text='tag.tag_name', icon_value=icon)
            layout.prop(tag, "tag_name", text='', emboss=False, icon_value=icon) 
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.prop(tag, "tag_name", text='') 


def set_catalog_for_asset(uuid,tree,name):
    catfile_handler.ensure_catalog_exists(catalog_uuid=uuid, catalog_tree= tree,catalog_name =name) 

def set_tags_for_asset(context,idx,m_asset,datatype):
    for tag in m_asset.tags:
        if tag.tag_name not in datatype.asset_data.tags:
            datatype.asset_data.tags.new(tag.tag_name)

class BU_OT_Confirm_Cats_And_Tags(bpy.types.Operator):
    bl_idname = "wm.confirm_cats_and_tags"
    bl_label = 'Confirm Metadata'
    bl_options = {'REGISTER'}
    bl_description = 'Confirm Metadata'
    bl_category = 'Asset Browser'
    @classmethod
    def poll(cls,context):
        if not context.scene.cats_and_tags:
            cls.poll_message_set('No asset browser assets selected!')
            return False
        return True 
    def execute(self, context):
        main_cat_dict = get_main_cats()
        for idx,asset in enumerate(selected_assets):
            
            m_asset = context.scene.cats_and_tags[idx]
            print( m_asset.catalog_path)
            if m_asset.catalog_path !='':
                m_asset.catalog_uuid = main_cat_dict[m_asset.catalog_path.removesuffix('/')]
                    
                tree = m_asset.catalog_path.removesuffix('/')
                m_asset.catalog_name =tree.replace('/','-')
            # print(asset.asset_data.__dir__())
                print(m_asset.catalog_uuid)
                set_catalog_for_asset(m_asset.catalog_uuid,tree,m_asset.catalog_name)
                asset.asset_data.catalog_id = m_asset.catalog_uuid
            set_tags_for_asset(context,idx,m_asset,asset)
        return {'FINISHED'}

class BU_OT_Remove_Asset_From_List(bpy.types.Operator):
    bl_idname = "wm.remove_asset_from_list"
    bl_label = 'Remove Selected asset from list'
    bl_options = {'REGISTER'}
    bl_description = 'Remove Asset browser assets from list'
    bl_category = 'Asset Browser'

    @classmethod
    def poll(cls,context):
        if not context.scene.cats_and_tags:
            cls.poll_message_set('List is already Empty!')
            return False
        return True  
    def execute(self, context):
        context.scene.cats_and_tags.clear()
        return {'FINISHED'}


class BU_OT_Add_Assets_To_List(bpy.types.Operator):
    bl_idname = "wm.add_assets_to_list"
    bl_label = 'Add Selected assets to list'
    bl_options = {'REGISTER'}
    bl_description = 'Add Asset browser assets to list'
    bl_category = 'Asset Browser'

    @classmethod
    def poll(cls,context):
         for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        if context.selected_asset_files:
                            # selected_assets.clear()
                            return True
                        cls.poll_message_set('No asset browser assets selected')
                        return False  
    def execute(self, context):
        selected_assets.clear()
        context.scene.cats_and_tags.clear()
        catfile_handler.get_current_file_catalog_filepath()    
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    with context.temp_override(window=window, area=area):
                        # if filepath != '':
                        #     bpy.ops.asset.catalog_new()
                        #     bpy.ops.asset.catalog_undo()
                        if context.selected_asset_files:
                            for asset in context.selected_asset_files:
                                asset.asset_data.author = addon_info.get_addon_name().preferences.author
                                selected_assets.append(asset)
                                
                                asset_list = context.scene.cats_and_tags.add()
                                asset_list.asset_name = asset.name
                                asset_list.asset_type =asset.id_type
                                if asset.id_type == 'OBJECT':
                                    asset_list.m_object = asset.local_id
                                elif asset.id_type == 'MATERIAL':
                                    asset_list.m_material = asset.local_id
                                          
                        return {'FINISHED'}  

class CatsAndTagsPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_CATS_AND_TAGS"
    bl_label = 'Set Catalogs and Tags'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_ASSETBROWSER_TOOLS"

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text = 'Select Assets from Current file Asset Library')
        box = layout.row()
        row = box.row()
        row.operator('wm.add_assets_to_list', text = 'Set Catalogs and Tags')
        row = box.row()
        row.operator('wm.confirm_cats_and_tags', text = 'Confirm Cats And Tags')
        row.operator('wm.remove_asset_from_list', text = 'Remove Assets from List')
        draw_assets(self,context,layout,row)

def draw_assets(self,context,layout,row):
    box = layout.box()
    row = box.row()
    split = row.split(factor = 0.25)
    row = split.row(align = True)
    row.alignment = 'CENTER'
    row.label(text ="Asset Metadata")
    row = split.row(align = True)
    row.alignment = 'CENTER'
    row.label(text ="Asset Preview")
    row = split.row(align = True)
    row.alignment = 'CENTER'
    row.label(text ="Choose Catalog")
    row = split.row(align = True)
    row.alignment = 'CENTER'
    row.label(text ="Set Tags")
    
    for idx,asset in enumerate(context.scene.cats_and_tags):
        # box = layout.box()
        row = box.row()
        split = row.split()
        row = split.row()
        col = row.column(align = True)
        for index, m_asset in enumerate(selected_assets):
            if index == idx:

                col.prop(m_asset, 'name')
                col.prop(m_asset.asset_data, 'description')
                col.prop(m_asset.asset_data, 'author')
                # print(m_asset.asset_data.__dir__())
        draw_preview(self,context,split,idx,asset)
        draw_catalogs(self,context,split,idx,asset)
        draw_meta_data(self,context,split,idx,asset)

    
def draw_catalogs(self,context,split,idx,asset):
    row = split.row(align = True)
    col = row.column(align = True)
    row = col.row(align = True)
    row.operator('wm.add_new_catalog',text ='',icon ='ADD').item_index = idx	
    row.operator('wm.remove_new_catalog',text ='',icon ='REMOVE').item_index = idx
    
    row = col.row(align = True)
    asset.get_and_add_subcatalogs(context)
    row.prop(asset,'select_catalog',text = '')
    row.enabled = True if len(asset.get_and_add_subcatalogs(context)) >0 else False
    row = col.row(align = True)
    col = row.column(align = True)
    row.operator('wm.reset_catalog',text ='',icon ='CANCEL').item_index = idx
    col.prop(asset,'catalog_path',text = '')
    col.enabled = False


def draw_meta_data(self,context,split,idx,asset):
    row = split.row()
    if selected_assets:
        row.template_list("ASSETBROWSER_UL_asset_tags",'', asset, 'tags', asset, "tags_list_index",rows =2)  
        col = row.column()
        col.operator('tags_list.new_item', text='', icon='ADD').item_index = idx	
        col.operator('tags_list.delete_item', text='', icon='REMOVE').item_index = idx	


        
    
def draw_preview(self,context,split,idx,asset):
    row = split.row(align = True)
    col = row.column(align = True)
    
    if selected_assets:
        m_asset = selected_assets[idx]
        box = col.box()
        box.template_icon(icon_value=m_asset.preview_icon_id, scale=3.0)
       
    #  Crashed Blender
    #col = row.column(align=True)
    #col.operator("ed.lib_id_load_custom_preview", icon='FILEBROWSER', text="")
    #col.separator()
    #col.operator("wm.generate_preview", icon='FILE_REFRESH', text="").item_index = idx
    #col.menu("ASSETBROWSER_MT_metadata_preview_menu", icon='DOWNARROW_HLT', text="")

classes =(
    TagsList,
    LIST_OT_NewItem,
    LIST_OT_DeleteItem,
    ASSETBROWSER_UL_asset_tags,
    GetUserAddedCats,
    ResetCatalog,
    AddNewCatalog,
    GeneratePreview,
    RemoveNewCatalog,
    CatsAndTags,
    CatsAndTagsPanel,
    BU_OT_Add_Assets_To_List,
    BU_OT_Remove_Asset_From_List,
    BU_OT_Confirm_Cats_And_Tags,
    
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    selected_assets.clear()
    
        # bpy.types.ASSETBROWSER_PT_metadata_preview.draw
    # bpy.types.Scene.tags_list_index = IntProperty(name = "tags list index", default = 0)
    bpy.types.Scene.asset_tags = bpy.props.CollectionProperty(type=TagsList)
    bpy.types.Scene.user_added_cats = bpy.props.PointerProperty(type=GetUserAddedCats)
    bpy.types.Scene.cats_and_tags= bpy.props.CollectionProperty(type=CatsAndTags)
    # bpy.context.scene.mark_collection.to_mark_operators = 'wm.reset_cat_path'

def unregister():
    del bpy.types.Scene.asset_tags
    del bpy.types.Scene.user_added_cats
    del bpy.types.Scene.cats_and_tags
    for cls in classes:
        bpy.utils.unregister_class(cls)
    