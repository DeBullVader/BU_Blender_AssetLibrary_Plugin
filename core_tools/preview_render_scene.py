import bpy
from bpy.utils import register_classes_factory
from ..utils.addon_info import gitbook_link_getting_started

class UB_PT_PreviewRenderScene(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_PREVIEWRENDEROPTIONS"
    bl_label = 'Preview Render Scene'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BU_CORE_TOOLS"
    bl_category = 'UniBlend'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        mainrow = box.row()
        mainrow.alignment = 'LEFT'
        col = mainrow.column()
        
        col.label(text='Preview Render scene:')
        row = col.row(align=True)
        
        row.operator("ub.append_preview_render_scene", text="Append", icon='APPEND_BLEND')
        row.operator("ub.remove_preview_render_scene", text="Remove", icon='REMOVE')
        col = mainrow.column()
        col.alignment = 'LEFT'
        col.label(text='Switch scenes:')
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        window = context.window
        row.template_ID(window, "scene", new="scene.new",unlink="scene.delete")
        mainrow.alignment = 'RIGHT'
        gitbook_link_getting_started(mainrow,'mark-asset-tools/preview-render-scene','')

class UB_OT_Append_Preview_Render_Scene(bpy.types.Operator):
    '''Append preview render scene to current file'''
    bl_idname = "ub.append_preview_render_scene"
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

    
class UB_OT_Remove_Preview_Render_Scene(bpy.types.Operator):
    '''Remove preview render scene from current file'''
    bl_idname = "ub.remove_preview_render_scene"
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

class UB_OT_Switch_To_Preview_Render_Scene(bpy.types.Operator):
    '''Switch to preview render scene'''
    bl_idname = "ub.switch_to_preview_render_scene"
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
    UB_OT_Append_Preview_Render_Scene,
    UB_OT_Remove_Preview_Render_Scene,
    UB_OT_Switch_To_Preview_Render_Scene
)

register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
   
def unregister():
    unregister_classes()