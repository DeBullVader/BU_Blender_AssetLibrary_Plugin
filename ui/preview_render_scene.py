import bpy,os
from ..utils import addon_info
class BU_OT_Append_Preview_Render_Scene(bpy.types.Operator):
    '''Append preview render scene to current file'''
    bl_idname = "bu.append_preview_render_scene"
    bl_label = "Append preview render scene to current file"
    bl_description = "Append the preview render scene to the current blend file. For rendering custom previews"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if 'PreviewRenderScene' in bpy.data.scenes:
            return False
        return True
    
    def execute(self, context):
        addon_path = addon_info.get_addon_path()
        preview_render_file_path = os.path.join(addon_path,'BU_plugin_assets','blend_files','Preview_Rendering.blend')
        with bpy.data.libraries.load(preview_render_file_path) as (data_from, data_to):
            data_to.scenes = data_from.scenes

        if 'PreviewRenderScene' in bpy.data.scenes:
            print('Preview Render Scene has been added to the current blend file')
        return {'FINISHED'}

    
class BU_OT_Remove_Preview_Render_Scene(bpy.types.Operator):
    '''Remove preview render scene from current file'''
    bl_idname = "bu.remove_preview_render_scene"
    bl_label = "Remove preview render scene from current file"
    bl_description = "Remove the preview render scene from the current blend file. For rendering custom previews"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if 'PreviewRenderScene' not in bpy.data.scenes:
            return False
        return True
    
    def execute(self, context):
        bpy.data.scenes.remove(bpy.data.scenes['PreviewRenderScene'])
        bpy.data.orphans_purge(do_recursive=True)
        return {'FINISHED'}

class BU_OT_Switch_To_Preview_Render_Scene(bpy.types.Operator):
    '''Switch to preview render scene'''
    bl_idname = "bu.switch_to_preview_render_scene"
    bl_label = "Switch to preview render scene"
    bl_description = "Switch to the preview render scene"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if 'PreviewRenderScene' not in bpy.data.scenes:
            return False
        return True
    
    def execute(self, context):
        
            
        if context.scene.name != 'PreviewRenderScene':
            context.window.scene = bpy.data.scenes['PreviewRenderScene']
        else:
            for scene in bpy.data.scenes:
                if scene.name != 'PreviewRenderScene':
                    context.window.scene = scene
                    break
        return {'FINISHED'}
    
classes=(
    BU_OT_Append_Preview_Render_Scene,
    BU_OT_Remove_Preview_Render_Scene,
    BU_OT_Switch_To_Preview_Render_Scene
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)