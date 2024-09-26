import bpy
from bpy.props import *
from bpy.utils import register_classes_factory
from .asset_manager_utils import *
from ...utils import addon_info

class UB_OT_AssetMetadata(bpy.types.Operator):
    """Set metadata for this asset"""
    bl_idname = "ub.asset_metadata"
    bl_label = "Asset Metadata"
    bl_options = {'REGISTER', 'UNDO'}
    
    global selected_assets
    idx: IntProperty()
    asset = PointerProperty(type=bpy.types.ID)
    asset_name: StringProperty(name='Asset Name')
    asset_type: StringProperty(name='Asset Type')
    author: StringProperty(name='Author')
    use_global_author: BoolProperty(name='Global Author',default=True)
    tags: StringProperty(name='')
    new_tag: StringProperty(name='New tag name')
    update_tag: BoolProperty(name='Update Tags',description='Updates asset tags from comma seperated to asset_data.tags',default=False)
    add_tag: BoolProperty(default=False)
    remove_tag: BoolProperty(default=False)
    
    
    def execute(self, context):
        addon_prefs = addon_info.get_addon_prefs()
        if self.asset:
            if self.use_global_author:
                self.asset.asset_data.author = addon_prefs.author
            else:
                self.asset.asset_data.author = self.author
        return {'FINISHED'}

    def invoke(self, context, event):
        asset = get_asset_from_datatype(self.asset_name,self.asset_type)
        self.asset = asset
        self.tags = ','.join(tag.name.strip() for tag in asset.asset_data.tags)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self,context):
        addon_prefs = addon_info.get_addon_prefs()
        asset_data = self.asset.asset_data
        layout = self.layout
        row = layout.row(align=True)
        if not self.use_global_author:
            row.prop(self, 'author',text='Override Author: ')
        else:
            row.prop(addon_prefs, 'author',text='Author')
        row.prop(self, 'use_global_author', text='',icon='USER', toggle=True)
  
        layout.prop(asset_data, 'description',text='Description')

        layout.label(text="Asset Tags:")
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text='Tags (comma separated)')
        row = layout.row(align=True)
        row.alignment = 'EXPAND'

        row.prop(self, 'tags')
        row.prop(self, "update_tag",text='', icon='FILE_REFRESH', toggle=True)
        
        layout.template_list("ASSETBROWSER_UL_metadata_tags", "asset_tags", asset_data, "tags",asset_data, "active_tag", rows=2)
        row = layout.row(align=True)
        row.prop(self,'new_tag',text='')
        row.prop(self,'add_tag',text='Add',icon='ADD',toggle=True)
        row.prop(self,'remove_tag',text='Remove',icon='FILE_REFRESH',toggle=True)
        
        
        if self.asset:
            if self.update_tag:
                for tag_name in self.tags.split(','):
                    tag_name = tag_name.strip()
                    if tag_name not in [t.name for t in asset_data.tags]:
                        asset_data.tags.new(tag_name)
                
                tag_names = self.tags.split(',')
                for tag in asset_data.tags:
                    if tag.name not in self.tags:
                        asset_data.tags.remove(tag)
                self.tags = ','.join(tag.name.strip() for tag in asset_data.tags)
                self.update_tag = False  
            
            if self.add_tag:
                new_tag=self.new_tag if self.new_tag else 'Tag'
                tag = asset_data.tags.new(new_tag)
                if tag.name not in self.tags.split(','):
                    self.tags += ','+tag.name if len(asset_data.tags) > 1 else tag.name
                self.add_tag = False
                self.new_tag = ''

            if self.remove_tag:
                active_tag_index =asset_data.active_tag
                if active_tag_index >= len(asset_data.tags):
                    active_tag_index =(len(asset_data.tags)-1)

                if len(asset_data.tags) > 0:
                    active_tag = asset_data.tags[active_tag_index]
                    tag_names = self.tags.split(',')
                    self.tags = ','.join(tag_name.strip() for tag_name in tag_names if tag_name.strip() != active_tag.name)
                    asset_data.tags.remove(active_tag)
                    active_tag_index = min(max(0,active_tag_index -1),len(asset_data.tags)-1)
                self.remove_tag = False
    
class UB_OT_ExcludeAllChildren(bpy.types.Operator):
    bl_idname = "ub.exclude_all_children"
    bl_label = "Exclude all children"
    bl_description = "Exclude all child assets from list"
    bl_options = {'REGISTER', 'UNDO'}

    exclude_all: bpy.props.BoolProperty()
    children_names: bpy.props.StringProperty()

    def execute(self, context):
        nameslist = [name.strip() for name in self.children_names.split(',')]
        if not self.exclude_all:
            for child_name in nameslist:
                if child_name not in AssetOperations.exclude_list:
                    AssetOperations.exclude_list.append(child_name)
            self.exclude_all = True
        else:
            for child_name in nameslist:
                if child_name in AssetOperations.exclude_list:
                    AssetOperations.exclude_list.remove(child_name)
            self.exclude_all = False
        return {'FINISHED'}


class UB_OT_MarkAllChildren(bpy.types.Operator):
    bl_idname = "ub.mark_all_children"
    bl_label = "Mark all children"
    bl_description = "Mark all children"
    bl_options = {'REGISTER', 'UNDO'}
  
    marked_all: bpy.props.BoolProperty()
    asset_name: bpy.props.StringProperty()
    asset_type: bpy.props.StringProperty()
    children_names: bpy.props.StringProperty()

    def execute(self, context):
        nameslist = [name.strip() for name in self.children_names.split(',')]
       
        if not self.marked_all:
            for child_name in nameslist:
                if child_name not in AssetOperations.exclude_list:
                    asset = get_asset_from_datatype(child_name, self.asset_type)
                    asset.asset_mark()
                    pack_images(asset)
                    assign_previews(context,asset)
            self.marked_all = True
        else:
            for child_name in nameslist:
                if child_name not in AssetOperations.exclude_list:
                    asset = get_asset_from_datatype(child_name, self.asset_type)
                    asset.asset_clear()
            self.marked_all = False

        return {'FINISHED'}

class UB_OT_MarkOrClearAsset(bpy.types.Operator):
    bl_idname = "ub.mark_or_clear_asset"
    bl_label = "Mark Asset"
    
    asset_name: bpy.props.StringProperty()
    asset_type: bpy.props.StringProperty()

    def execute(self, context):
        asset = get_asset_from_datatype(self.asset_name,self.asset_type)
        if asset:
            if not asset.asset_data:
                asset.asset_mark()
                pack_images(asset)
                assign_previews(context,asset)
            else:
                asset.asset_clear()
        return {'FINISHED'}

class UB_OT_MarkAssets(bpy.types.Operator):
    """Mark all selected assets"""
    bl_idname = "ub.mark_assets"
    bl_label = "Mark Assets"

    def execute(self, context):
        asset_props = context.scene.asset_props
        selected_assets = get_selected_assets()
        for asset in selected_assets:
            if asset_props.asset_types =='Materials':
                if hasattr(asset,'material_slots'):
                    for slot in asset.material_slots:
                        if slot.material.name not in AssetOperations.exclude_list:
                            pack_images(slot.material)
                            slot.material.asset_mark()
                            assign_previews(context,slot.material)
            else:
                if asset.name not in AssetOperations.exclude_list:
                        pack_object_mat_images_recursive(asset)
                        asset.asset_mark()
                        assign_previews(context,asset)
        return {'FINISHED'}

class UB_OT_UnMarkAssets(bpy.types.Operator):
    """Unmark all selected assets"""
    bl_idname = "ub.unmark_assets"
    bl_label = "UnMark Assets"
    
    def execute(self, context):
        asset_props = context.scene.asset_props
        selected_assets = get_selected_assets()

        for idx,asset in enumerate(selected_assets):
     
            if asset_props.asset_types =='Materials':
                for mat_idx,slot in enumerate(asset.material_slots):
                    if mat_idx not in AssetOperations.exclude_list:
                            slot.material.asset_clear()
            else:
                if idx not in AssetOperations.exclude_list:
                    asset.asset_clear()
        return {'FINISHED'}
    
class ClearObjectParent():
    def clear_parent(self,context,parent,asset_type):
        selected_assets = get_selected_assets()
        assets_to_clear = [c for c in parent.children if c in selected_assets]
        parent_col_parts_name = parent.name+'_Parts'
        if parent_col_parts_name in context.scene.collection.children:
            parent_named_col = context.scene.collection.children[parent_col_parts_name]
        else:
            parent_named_col = bpy.data.collections.new(parent_col_parts_name)
            context.scene.collection.children.link(parent_named_col)
        for asset in assets_to_clear:
            if asset and asset_type == 'Objects' and asset.parent_type == 'OBJECT':
                for idx,sel_asset in enumerate(selected_assets):
                    if sel_asset.name == asset.name:
                        selected_assets.pop(idx)
                        obj_copy = self.duplicate(asset,data=True,actions=False,collection =parent_named_col)
                        selected_assets.insert(idx,obj_copy)
                        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                        obj_copy.location =(0,0,0)
                        asset.select_set(False)
                        obj_copy.select_set(True)    
                bpy.context.view_layer.update()
                
    def duplicate(self,obj, data=True, actions=True, collection=None):
        obj_copy = obj.copy()
        if data:
            obj_copy.data = obj_copy.data.copy()
        if actions and obj_copy.animation_data:
            obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
        collection.objects.link(obj_copy)
        obj_copy.parent = None
        return obj_copy

        
     
class UB_OT_ClearParent(bpy.types.Operator,ClearObjectParent):
    '''Create a copy of the child assets, unlink it from the parent object'''
    bl_idname = "ub.object_clear_parent"
    bl_label = "Clear Parent"
    bl_options = {'REGISTER'}

    asset_name: bpy.props.StringProperty()
    asset_type: bpy.props.StringProperty()

    def execute(self, context):
        
        asset = get_asset_from_datatype(self.asset_name,self.asset_type)
        self.clear_parent(context,asset,self.asset_type)
        bpy.ops.ed.undo_push() 
        
        return {'FINISHED'}
    


    
classes = (
    UB_OT_AssetMetadata,
    UB_OT_MarkAllChildren,
    UB_OT_MarkAssets,
    UB_OT_UnMarkAssets,
    UB_OT_MarkOrClearAsset,
    UB_OT_ExcludeAllChildren,
    UB_OT_ClearParent,

)
register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
   
def unregister():
    unregister_classes()
