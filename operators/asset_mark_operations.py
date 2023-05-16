import bpy
import os
from pathlib import Path
from bpy.types import Context, Event, Operator

class FilterTypes(bpy.types.PropertyGroup):
    meshes: bpy.props.BoolProperty(name="Meshes",default=False,)
    materials: bpy.props.BoolProperty(name="Materials", default=False)
    # collections: bpy.props.BoolProperty(name="Collections", default=False)

bpy.utils.register_class(FilterTypes)
bpy.types.Scene.filter_props = bpy.props.PointerProperty(type=FilterTypes)

def get_asset_types(self,context):
    asset_types = bpy.context.scene.filter_props
    return asset_types

class WM_OT_asset_mark_process(Operator):
    bl_idname = "wm.asset_mark_process" 
    bl_label = "what type of asset do you want to mark"

    def execute(self, context):
        asset_types = bpy.context.scene.filter_props

        return {'FINISHED'}
       

