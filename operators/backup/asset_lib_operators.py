import bpy
import os
from pathlib import Path
from bpy.types import Context, Event, Operator
from ...utils.addon_info import get_addon_name, get_upload_asset_library
from time import sleep
# def dump(obj, text):
#     for attr in dir(obj):
#         print("%r.%s = %s" % (obj, attr, getattr(obj, attr)))

# types = bpy.context.object.bl_rna.properties['type'].enum_items

# for t in types:
#     print('type %s: %s' %(t.identifier, t.name))


class FilterTypes(bpy.types.PropertyGroup):
    meshes: bpy.props.BoolProperty(name="Meshes",default=False,)
    materials: bpy.props.BoolProperty(name="Materials", default=False)
    # collections: bpy.props.BoolProperty(name="Collections", default=False)

bpy.utils.register_class(FilterTypes)
bpy.types.Scene.filter_props = bpy.props.PointerProperty(type=FilterTypes)
class WM_OT_upload_files(Operator):
    """CHECK IF THERE ARE UPDATES FOR OUR LIBRARY"""
    bl_idname = "wm.uploadfiles"
    bl_label = "Check of there are new assets available for download"

    def execute(self, context):
       
        return {'FINISHED'}
    

class WM_OT_unmark_as_baked_asset(Operator):
    bl_idname = "wm.unmarkasbuasset"
    bl_label = "Unmark selected assets"

    @classmethod
    def poll(cls, context):
        # cls.poll_message_set("Not available yet. Adding to bu library is beeing worked on!!")
        # return False
        if get_upload_asset_library(context) is not None:
            return context.active_object is not None  
        cls.poll_message_set("Couldnt find BU asset libraries. Please set one in addon preferences")

    def execute(self, context):
        pass




class WM_OT_mark_filter(Operator):
    bl_idname = "wm.markfilter" 
    bl_label = "what type of asset do you want to mark"

    def execute(self, context):
        asset_types = context.scene.filter_props
        # for object in context.selected_objects:
        #     mark_filtered_types(self,context,asset_types, object)
            
        # for item in asset_types.__annotations__.items():
            
        #     # print(item[0])
        # area = bpy.context.area
        # t = area.type
        # area.type = 'VIEW_3D'
        # bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        # area.type = t

            
        return {'FINISHED'}
       
    def invoke(self, context, event):
        # return context.window_manager.invoke_confirm(self)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        asset_types = scene.filter_props
        for item in asset_types.__annotations__.items():
            layout.prop(asset_types,item[0], toggle=True)

def mark_filtered_types(self, context,asset_types, object):

    if asset_types.materials == True:
        print( f'asset_type materials = {asset_types.materials}')
        for mat in object.material_slots:
            mat.material.asset_mark()
            
    if asset_types.meshes == True:
        print( f'asset_type meshes = {asset_types.meshes}')
        object.asset_mark()
        

    return 


def register():
#   bpy.utils.register_class(FilterTypes)
#   bpy.types.Scene.filter_props = bpy.props.PointerProperty(type=FilterTypes)
  pass  
   
   
def unregister():
    del  bpy.types.Scene.filter_props

