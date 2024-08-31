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
        row.prop(self,'remove_tag',text='Remove',icon='REMOVE',toggle=True)
        
        
        if self.asset:
            if self.update_tag:
                for tag_name in self.tags.split(','):
                    tag_name = tag_name.strip()
                    if tag_name not in [t.name for t in asset_data.tags]:
                        asset_data.tags.new(tag_name)
                
                tag_names = self.tags.split(',')
                for tag in asset_data.tags:
                    if tag.name not in self.tags:
                        print('remove',tag.name)
                        asset_data.tags.remove(tag)
                self.tags = ','.join(tag.name.strip() for tag in asset_data.tags)
                self.update_tag = False  
            
            if self.add_tag:
                new_tag=self.new_tag if self.new_tag else 'Tag'
                tag = asset_data.tags.new(new_tag)
                if tag.name not in self.tags.split(','):
                    self.tags += ','+tag.name if len(asset_data.tags) > 0 else tag.name
                self.add_tag = False
                self.new_tag = ''

            if self.remove_tag:
                active_tag_index =asset_data.active_tag
                if active_tag_index >= len(asset_data.tags):
                    active_tag_index =(len(asset_data.tags)-1)

                if len(self.asset_data.tags) > 0:
                    # print(self.tags.__dir__())
                    active_tag = asset_data.tags[active_tag_index]
                    tag_names = self.tags.split(',')
                    self.tags = ','.join(tag_name.strip() for tag_name in tag_names if tag_name.strip() != active_tag.name)
                    asset_data.tags.remove(active_tag)
                    active_tag_index = min(max(0,active_tag_index -1),len(asset_data.tags)-1)
                self.remove_tag = False


class UB_OT_AssetAddTag(bpy.types.Operator):
    bl_idname = "ub.asset_add_tag"
    bl_label = 'add tag to asset'
    bl_description = 'add tag to asset'
    bl_category = 'Asset Browser'
    bl_options = {'REGISTER'}

    global selected_assets
    idx: IntProperty()
    asset_name: StringProperty()
    asset_type: StringProperty()

    def execute(self, context):
        props = context.scene.asset_props
        get_asset_from_datatype(self.asset_name, props.types)
        asset = selected_assets[self.idx]
        if asset_props.types == 'Material':
            asset = bpy.data.materials.get(self.asset_name)
        elif asset_props.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                asset = geo_modifier.node_group    
        asset.asset_data.tags.new('Tag')
        return {'FINISHED'}

class UB_OT_AssetRemoveTag(bpy.types.Operator):
    bl_idname = "ub.asset_remove_tag"
    bl_label = 'Remove tag'
    bl_description = 'Remove tag form asset'
    bl_category = 'Asset Browser'
    bl_options = {'REGISTER'}

    idx: IntProperty()
    asset_name: StringProperty()
    asset_type: StringProperty()

    def execute(self, context):
        asset_props = context.scene.asset_props
        asset = selected_assets[self.idx]
       
        if asset_props.types == 'Material':
            if asset.name in asset_props.mats:
                asset = bpy.data.materials.get(asset.name)
            
        elif asset_props.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in asset_props.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                asset = geo_modifier.node_group 

        active_tag_index =asset.asset_data.active_tag
        if active_tag_index >= len(asset.asset_data.tags):
            active_tag_index =(len(asset.asset_data.tags)-1)

        if len(asset.asset_data.tags) > 0:
            # print(self.tags.__dir__())
            active_tag = asset.asset_data.tags[active_tag_index]
            tag_names = self.tags.split(',')
            self.tags = ','.join(tag_name.strip() for tag_name in tag_names if tag_name.strip() != active_tag.name)
            asset.asset_data.tags.remove(active_tag)
            active_tag_index = min(max(0,active_tag_index -1),len(asset.asset_data.tags)-1)

        return {'FINISHED'}     

class UB_OT_UpdateTags(bpy.types.Operator):
    bl_idname = "ub.update_tags"
    bl_label = "Update Tags"
    bl_description = "Update tags for the selected asset"
    bl_category = "Asset Browser"

    idx: bpy.props.IntProperty()
    tags:bpy.props.StringProperty()

    def execute(self, context):
        asset_props = context.scene.asset_props
        asset = selected_assets[self.idx]

        if asset_props.types == 'Material':
            if asset.name in asset_props.mats:
                asset = bpy.data.materials.get(asset.name)

        elif asset_props.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in asset_props.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                asset = geo_modifier.node_group

        for tag_name in self.tags.split(','):
            tag_name = tag_name.strip()
            if tag_name not in [t.name for t in asset.asset_data.tags]:
                asset.asset_data.tags.new(tag_name)

        for tag in asset.asset_data.tags:
            if tag.name not in self.tags.split(','):
                asset.asset_data.tags.remove(tag)

        return {'FINISHED'}
    

    
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
        print(selected_assets)
        for asset in selected_assets:
            if asset_props.asset_types =='Object':
                if asset.name not in AssetOperations.exclude_list:
                    pack_object_mat_images_recursive(asset)
                    asset.asset_mark()
                    assign_previews(context,asset)
            if asset_props.asset_types =='Material':
                if hasattr(asset,'material_slots'):
                    for slot in asset.material_slots:
                        if slot.material.name not in AssetOperations.exclude_list:
                            pack_images(slot.material)
                            slot.material.asset_mark()
                            assign_previews(context,slot.material)
        return {'FINISHED'}

class UB_OT_UnMarkAssets(bpy.types.Operator):
    """Unmark all selected assets"""
    bl_idname = "ub.unmark_assets"
    bl_label = "UnMark Assets"
    
    def execute(self, context):
        asset_props = context.scene.asset_props
        selected_assets = get_selected_assets()

        for idx,asset in enumerate(selected_assets):
            if asset_props.asset_types =='Object':
                if idx not in AssetOperations.exclude_list:
                    asset.asset_clear()
            if asset_props.asset_types =='Material':
                for mat_idx,slot in enumerate(asset.material_slots):
                    if mat_idx not in AssetOperations.exclude_list:
                            slot.material.asset_clear()
        return {'FINISHED'}
    
classes = (
    UB_OT_AssetMetadata,
    UB_OT_AssetAddTag,
    UB_OT_AssetRemoveTag,
    UB_OT_UpdateTags,
    UB_OT_MarkAllChildren,
    UB_OT_MarkAssets,
    UB_OT_UnMarkAssets,
    UB_OT_MarkOrClearAsset,
    UB_OT_ExcludeAllChildren,

)
register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
   
def unregister():
    unregister_classes()
