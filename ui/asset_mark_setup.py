import bpy
from bpy.types import Context, Event
from ..operators.asset_mark_operations import get_asset_types
from ..utils import addon_info,CatalogsHelper
from pathlib import Path
import textwrap

    

def update_cats(self,context):
    
    cats = CatalogsHelper.get_catalogs()
    cats_ennum =[]
    props = bpy.props.operator("wm.confirm_mark")
    # cats_ennum.append(('UNASSIGNED','Unassigned','Choose this if for default (Unassigned)'))
    print(context.scene.mark_collection[0].catalog)
    return cats
def update_uuid(self, context):
    
    self.catalog_uuid= self.catalog

class AssetsToMark(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    only_mat: bpy.props.BoolProperty()
    catalog: bpy.props.EnumProperty(items= CatalogsHelper.get_catalogs,name ='Catalog',update =update_uuid)
    catalog_uuid: bpy.props.StringProperty()
    catalog_name: bpy.props.StringProperty()

bpy.utils.register_class(AssetsToMark)
bpy.types.Scene.mark_collection = bpy.props.CollectionProperty(type=AssetsToMark)

# bpy.types.EnumProperty.catprop = bpy.props.PointerProperty(type=bpy.types.Scene.mark_collection.catalog)


def draw_asset_types(self, context, asset_types):
    asset_types = get_asset_types(self, context)
    layout = self.layout
    scene = context.scene
    asset_types = scene.filter_props
    for item in asset_types.__annotations__.items():
        layout.prop(asset_types,item[0], toggle=True)


def Check_prefix(context):
    enable = False
    for item in context.scene.mark_collection:
        if not item.obj.name.startswith('SM_'):
            enable = True
        for slot in item.obj.material_slots:
            if not slot.material.name.startswith('M_'): 
                enable = True
    return enable

class AddMissingPrefixes(bpy.types.Operator):
    bl_idname = "wm.add_missing_prefixes" 
    bl_label = "start the marking of assets process"
    bl_options = {"REGISTER","UNDO"}

    @classmethod
    def poll(cls, context):
        if Check_prefix(context):
            return True
        
    def execute(self, context):
        for item in context.scene.mark_collection:
            if not item.obj.name.startswith('SM_'):
                item.obj.name = f'SM_{item.obj.name}'

            for slot in item.obj.material_slots:
                if not slot.material.name.startswith('M_'):
                    slot.material.name = f'M_{slot.material.name}'
        return {'FINISHED'}
    # def invoke (self,context, event):
    #     pass

def set_catalog_for_asset(self,item):
    uuid,tree,name =CatalogsHelper.catalog_info_from_uuid(self=CatalogsHelper,uuid=item.catalog)
    CatalogsHelper.ensure_catalog_exists(self=CatalogsHelper,catalog_uuid=uuid, catalog_tree= tree,catalog_name =name)
    
class confirmMark(bpy.types.Operator):
    bl_idname = "wm.confirm_mark" 
    bl_label = "Initialize mark for add process"
    bl_options = {"REGISTER","UNDO"}

    @classmethod
    def poll(self,context):
        if not Check_prefix(context):
            return True
    
    def execute(self, context):
      
        for item in context.scene.mark_collection:
            if item.only_mat:
                for slot in item.obj.material_slots:
                    mat = slot.material
                    mat.asset_mark()
                    mat.asset_generate_preview()
                    mat.asset_data.catalog_id = item.catalog
                    set_catalog_for_asset(self,item)
                  
            else:
                item.obj.asset_mark()
                item.obj.asset_generate_preview()
                item.obj.asset_data.catalog_id = item.catalog
                set_catalog_for_asset(self,item)
            props = get_enum(self,context)
            
        return {'FINISHED'}   
              
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    


class MarkSelected(bpy.types.Operator):
    bl_idname = "wm.mark_selected" 
    bl_label = "start the marking of assets process"
    bl_options = {"REGISTER","UNDO"}

    def execute(self, context):
        
        context.scene.mark_collection.clear()
        assets = context.selected_objects
        for asset in assets:
            if asset.name not in context.scene.mark_collection:
                markasset = context.scene.mark_collection.add()
                markasset.obj = asset
        
        asset_types = bpy.context.scene.filter_props

        return {'FINISHED'}
    
class AddNewCatalog(bpy.types.Operator):
    bl_idname = "wm.mark_selected" 
    bl_label = "start the marking of assets process"
    bl_options = {"REGISTER","UNDO"}

    def execute(self,context):
        pass

    def invoke(self,context):
        pass

class AddCatalogPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_Add_catalog'
    bl_label = 'Baked Universe Tools'

    main_catalog: bpy.props.EnumProperty(items=None, name ='main_catalogs',discription ='')

    def draw(self, context):
        layout = self.layout
        layout.label( text = "Add new catalogs")
        row = layout.row()


       

def draw_marked(self,context):
    
    layout = self.layout
    row = layout.row()
    
    row.operator('wm.add_missing_prefixes',text ="Fix pre-fixes",icon ='ERROR'if AddMissingPrefixes.poll else 'CHECKMARK')
    row.separator()
    text = 'Make sure to use descriptive names for both meshes and materials! Example for a mesh: SM_Door_Damaged | Example for Material: M_Wood_Peeled_Paint'
    _label_multiline(
        context=context,
        text=text,
        parent=layout
    )
    box = layout.box()
    row = box.row()
    split = row.split()
    col = split.column(align = True)
    col.label(text ="Only materials")
    col = split.column(align = True)
    col.label(text ="Mesh Naming")
    col = split.column(align = True)
    col.label(text ="Material Naming")
    col = split.column(align = True)
    col.label(text ="Catagories")

    layout =self.layout
    box = layout.box()

    for item in context.scene.mark_collection:
        row = box.row()
        split = row.split(factor =0.25)
        # col only mats
        col = split.column(align = True)
        col.prop(item,'only_mat',toggle = True, icon_only=True ,icon ='MATERIAL')

        #col Mesh Names
        col = split.column(align = True)
        col.prop(item.obj, 'name', text ="")
        col.enabled = False if item.only_mat else True

        #col Material Names
        col = split.column(align = True)
        for slot in item.obj.material_slots:
            mat = slot.material
            col.prop(mat, 'name', text ="", expand = True)
            col.enabled = True if item.only_mat else False

        #Catagories
        col = split.column(align = True)
        cat = col.prop(item,'catalog')
        


def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)




class Main_BU_Tools_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_Main_BU_UI"
    bl_label = 'Baked Universe Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Tools'

    def draw(self, context):
        layout = self.layout
        layout.label( text = "Baked Universe Tools")
        row = layout.row()
        row.label(text = 'Marking assets is in development! Use only to test!', icon='ERROR')
        row = layout.row()
        row.operator('wm.mark_selected', text=('Prepare to Mark Asset'), icon='ERROR')
        if len(context.scene.mark_collection)>0:
            draw_marked(self, context)
            row = layout.row()
            row.operator('wm.confirm_mark', text=('Confirm Mark Assets'))



bpy.utils.register_class(MarkSelected)
bpy.utils.register_class(confirmMark)
bpy.utils.register_class(Main_BU_Tools_Panel)
bpy.utils.register_class(AddMissingPrefixes)

# def register():
    

    

# def unregister():
#     del bpy.types.Scene.collection
#     bpy.utils.unregister_class(AssetsToMark)
#     bpy.utils.unregister_class(MarkSelected)
#     bpy.utils.unregister_class(Main_BU_Tools_Panel)









