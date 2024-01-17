import bpy
import os
from ..utils import addon_info
from .. import icons

addon_prefs =addon_info.get_addon_prefs()
def draw_marktool_default(self,context):
    switch_marktool = context.scene.switch_marktool
    layout = self.layout
    for idx,item in enumerate(context.scene.mark_collection):
        row = layout.row(align = True)
        row.alignment = 'EXPAND'

        box = row.box()
        draw_item_visibility_toggle(self,context,box,item)
        box = row.box()
        draw_item_isolation_toggle(self,context,box,item)
        box = row.box()
        remove_mt_op=box.operator('bu.remove_from_mark_tool', text = '', icon='CANCEL')
        remove_mt_op.idx = idx
        remove_mt_op.asset_name = item.asset.name
        box = row.box()
        if switch_marktool.switch_tabs == 'default':
            draw_types_settings(self,context,box,item)
        

        if item.types == 'Object':
            draw_name(self,context,box,item.asset)
            if switch_marktool.switch_tabs == 'default':
                box = row.box()
                
                draw_asset_mark(self,context,box,idx,item,item.asset.name)
            elif switch_marktool.switch_tabs == 'render_previews':
                box = row.box()
                preview_row= box.row(align = False)
                draw_has_previews(self,context,preview_row,idx,item,item.asset)
                draw_preview_render_settings(self,context,row,idx,item)
            elif switch_marktool.switch_tabs == 'metadata':
                box = row.box()
                draw_metadata(self,context,box,idx,item.asset)
        elif item.types == 'Material':
            row= box.row()
            draw_mat_add_all(self,context,row,item)
            draw_mat_remove_all(self,context,row,item)
            row= box.row(align = True)
            col = row.column(align = True)
            if item.asset.material_slots:
                for mat_idx,slot in enumerate(item.asset.material_slots):
                    if slot.material:
                        mat = slot.material
                        row= col.row(align = True)
                        row.alignment= 'EXPAND'
                        matching_mat = next((material for material in item.mats if mat.name == material.name), None)
                        if not matching_mat:
                            draw_mat_add_op(self,context,row,mat_idx,item,mat)
                        else:
                            draw_mat_remove_op(self,context,row,mat_idx,item,mat)
                        row.prop(mat, 'name', text ="",icon_value =mat.preview.icon_id)
                        if switch_marktool.switch_tabs == 'default':
                            draw_asset_mark(self,context,row,idx,item,mat.name)
                        elif switch_marktool.switch_tabs == 'render_previews':
                            row.alignment = 'EXPAND'
                            draw_has_previews(self,context,row,idx,item,mat)
                        elif switch_marktool.switch_tabs == 'metadata':
                            box = row.box()
                            draw_metadata(self,context,box,idx,mat)
                    else:
                        row.enabled
                        row.operator("bu.material_select", icon='MATERIAL', text="Select Material" )
                    row= col.row(align = True)
            else:
                row.label(text ="No Materials found !")
        elif item.types == 'Geometry_Node':
            geo_modifier = next((modifier for modifier in item.asset.modifiers.values() if modifier.type == 'NODES'), None)
            if geo_modifier:
                g_nodes = geo_modifier.node_group
                if g_nodes:
                    # col = box.column(align = True)
                    # row =col.row()
                    # box = row.box()
                    # preview_row= box.row(align = False)
                    box.prop(g_nodes, 'name', text ="", expand = True)
                    if switch_marktool.switch_tabs == 'default':
                        box = row.box()
                        draw_asset_mark(self,context,box,idx,item,g_nodes.name)
                    elif switch_marktool.switch_tabs == 'render_previews':
                        box = row.box()
                        preview_row= box.row(align = False)
                        row.alignment = 'EXPAND'
                        draw_has_previews(self,context,preview_row,idx,item,g_nodes)
                        draw_preview_render_settings(self,context,row,idx,item)
                    elif switch_marktool.switch_tabs == 'metadata':
                        box = row.box()
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

       

def draw_asset_mark(self,context,parent,idx,item,name):
    row = parent.row(align =True)
    if item.types =='Material':
        row.enabled = True if name in item.mats else False

    mark_op =row.operator('bu.mark_asset', text = "Mark Asset", icon = 'ASSET_MANAGER')
    mark_op.idx = idx
    mark_op.asset_name = name
    
    clear_op =row.operator('bu.clear_marked', text = "Clear Marked", icon = 'CANCEL')
    clear_op.idx = idx
    clear_op.asset_name = name

def draw_name(self,context,parent,item):
    parent.prop(item, 'name', text = "")


def draw_metadata(self,context,parent,idx,asset):
    addon_prefs = addon_info.get_addon_name().preferences
    item = context.scene.mark_collection[idx]
    parent.enabled = True if asset.asset_data else False
    text = "Metadata" if asset.asset_data else "Not Marked"
    target = item
    enabled = True
    if item.types == 'Material':
        matching_mat = next((material for material in item.mats if asset.name == material.name), None)
        if matching_mat:
            target = matching_mat
        else:
            enabled = False
            parent.label(text='Please enable the material first!')
    
    if enabled:
        parent.prop(target, 'draw_asset_data_settings', text=text, icon='TRIA_UP' if target.draw_asset_data_settings else 'TRIA_DOWN')
        if asset.asset_data:
            if target.draw_asset_data_settings:
                parent.alignment ='RIGHT'
                col = parent.column()
                row =col.row()
                col.prop(asset.asset_data, 'description')
                if addon_prefs.author =='':
                    col.prop(asset.asset_data, 'author')
                else:
                    col.prop(addon_prefs, 'author', text='Author (Globally set) : ')
                row =col.row()
                row.alignment = 'RIGHT'
                row.prop(item, 'draw_asset_tags', text= 'Show Tags',icon ='BOOKMARKS',toggle=True)
                if item.draw_asset_tags:
                    row =col.row()
                    row.alignment = 'RIGHT'
                    row.label(text="Tags:")
                    # row.alignment = 'RIGHT'
                    row.template_list("ASSETBROWSER_UL_metadata_tags", "asset_tags", asset.asset_data, "tags",asset.asset_data, "active_tag", rows=4)
                    col = row.column(align=True)
                    add_tag =col.operator('asset.add_tag', text='',icon='ADD',)
                    add_tag.idx =idx
                    add_tag.asset_name =asset.name
                    remove_tag =col.operator("asset.remove_tag", icon='REMOVE', text="")
                    remove_tag.idx =idx
                    remove_tag.asset_name =asset.name

def draw_has_previews(self, context,parent,idx,item,asset):
    # box = parent.box()
    # row=parent.row(align=True)
    
    # Iterate through asset's material slots and add them to mats
    asset_preview_path = addon_info.get_asset_preview_path()
    ph_asset_preview_path = addon_info.get_placeholder_asset_preview_path()
    path = f'{asset_preview_path}{os.sep}preview_{asset.name}.png'
    ph_path = f'{ph_asset_preview_path}{os.sep}PH_preview_{asset.name}.png'
    
    if os.path.exists(path) and os.path.exists(ph_path):
        parent.label(text ="",icon='IMAGE_RGB_ALPHA')
    else:
        parent.label(text ="",icon='SHADING_BBOX' )

    render_op_text = "Render *" if bpy.data.is_dirty else "Render"
    op = parent.operator("bu.render_previews_modal", icon='OUTPUT', text=render_op_text )
    op.idx = idx
    op.asset_name = asset.name

    if item.object_type == 'Collection':
        op.asset_type = 'collections'
    elif item.types == 'Geometry_Node':
        op.asset_type = 'node_groups'
        op.asset_name = item.asset.name
    else:
        data_type = item.types.lower()
        op.asset_type = f'{data_type}s'



def draw_preview_render_settings(self,context,parent,idx,item):

    i = icons.get_icons()
    box = parent.box()
    row = box.row(align = True)
    row.alignment = 'EXPAND'
    row.prop(item, 'render_bg', text="", icon='SCENE')
    row.prop(item, 'render_logo', text="", icon_value=i["BU_logo_v2"].icon_id)
    box = parent.box()
    col = box.column()
    row = col.row(align = True)
    if not item.override_camera:
        spawn_op = row.operator('bu.spawn_preview_camera', text="", icon='VIEW_CAMERA', depress =False)
        spawn_op.idx = idx
    else:
        remove_op = row.operator('bu.remove_preview_camera', text="", icon='CAMERA_DATA',depress =True)
        remove_op.idx = idx

    reset_op = row.operator('bu.reset_camera_transform', text="", icon='FILE_REFRESH')
    reset_op.idx = idx

    if item.override_camera:
        row.prop(item, 'draw_override_camera', text="", icon='TRIA_UP' if item.draw_override_camera else 'TRIA_DOWN')
        if item.draw_override_camera:
            row=col.row(align = True)
            row.prop(item, 'cam_loc', text="Location")
            row=col.row(align = True)
            row.prop(item, 'cam_rot', text="Rotation")
    else:
        row.label(text="",icon='TRIA_DOWN')
    box = parent.box()
    col = box.column()
    row = col.row(align=True)
    row.alignment = 'EXPAND'
    # if item.object_type == 'Collection':
    if not item.enable_offsets:
        prev_dim = row.operator('bu.object_to_preview_demensions',text="Asset Offsets")
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
    else:
        row.label(text="",icon='TRIA_DOWN')



def draw_types_settings(self,context,parent,item):
    if item.asset.bl_rna.identifier == 'Object':
        parent.prop(item,'types', text = '')
    elif item.asset.bl_rna.identifier == 'Collection':
        parent.label(text='Collection')
    else:
        parent.label(text='This type is not supported yet')

def draw_item_isolation_toggle(self,context,parent,item):
    obj = context.scene.objects.get(item.asset.name)
    parent.prop(item,'asset_isolation', text = '', icon ='SELECT_SET')
    if item.asset_isolation:
        if item.object_type == 'Object':
            item.asset.select_set(True)
        if item.object_type == 'Collection':
            for obj in item.asset.objects:
                obj.select_set(True) 
            
            # item.asset.objects.select_set(True)
        
        # bpy.ops.view3d.localview()

        
def draw_item_visibility_toggle(self,context,parent,item):
    if item.object_type == 'Object':
            name = item.asset.name
            obj = context.scene.objects.get(name)
            if obj:
                parent.prop(item,'viewport_visible', text = '', icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF',emboss=False)
                if item.viewport_visible:
                    obj.hide_set(True)
                else:
                    obj.hide_set(False)
    if item.object_type == 'Collection':
        if item.enable_offsets:
            col_instance= item.col_instance
            obj = context.scene.objects.get(col_instance.name)
            if obj:
                parent.prop(item,'viewport_visible', text = '', icon = 'HIDE_ON' if item.viewport_visible else 'HIDE_OFF',emboss=False)
                if item.viewport_visible:
                    obj.hide_set(True)
                else:
                    obj.hide_set(False)
        else:
            bpy.context.view_layer.update()
            
            collection =bpy.data.collections.get(item.asset.name)
            original_col =get_layer_collection(collection)
            if original_col:
                parent.prop(original_col,'hide_viewport', text = '', icon = 'HIDE_OFF',emboss=False)

def draw_mat_add_op(self,context,layout,idx,item,mat):
    op = layout.operator('bu.add_asset_to_mark_mat', text="", icon='MATERIAL')
    # op.item = item
    op.idx = idx
    op.name = item.asset.name
    op.mat_name = mat.name

def draw_mat_remove_op(self,context,layout,idx,item,mat):
    op = layout.operator('bu.remove_asset_to_mark_mat', text="", icon='MATERIAL',depress = True)
    # op.item = item
    op.idx = idx
    op.name = item.asset.name
    op.mat_name = mat.name

def draw_mat_add_all(self,context,row,item):
    op = row.operator('bu.add_all_mats', text="Select All", icon='ADD')
    # op.item = item
    op.name = item.asset.name

def draw_mat_remove_all(self,context,row,item):
    op = row.operator('bu.remove_all_mats', text="Deselect All", icon='REMOVE')
    # op.item = item
    op.name = item.asset.name

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
        if item.asset.name in context.view_layer.layer_collection.collection.objects:
            return context.view_layer.layer_collection.collection.objects.get(item.asset.name)
        else:
            for c in lc.children:
                if item.asset.name in c.collection.objects:
                    return c.collection.objects.get(item.asset.name)
                result = scan_children(c, result)
            return result

    return scan_children(bpy.context.view_layer.layer_collection)
    