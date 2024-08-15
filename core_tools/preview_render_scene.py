import bpy
from ..utils.addon_info import gitbook_link_getting_started

class BU_PT_PreviewRenderScene(bpy.types.Panel):
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
        
        row.operator("bu.append_preview_render_scene", text="Append", icon='APPEND_BLEND')
        row.operator("bu.remove_preview_render_scene", text="Remove", icon='REMOVE')
        col = mainrow.column()
        col.alignment = 'LEFT'
        col.label(text='Switch scenes:')
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        window = context.window
        row.template_ID(window, "scene", new="scene.new",unlink="scene.delete")
        mainrow.alignment = 'RIGHT'
        gitbook_link_getting_started(mainrow,'mark-asset-tools/preview-render-scene','')

def register():
    bpy.utils.register_class(BU_PT_PreviewRenderScene)
    
def unregister():
    bpy.utils.unregister_class(BU_PT_PreviewRenderScene)