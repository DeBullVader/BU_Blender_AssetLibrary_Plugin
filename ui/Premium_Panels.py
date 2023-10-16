import bpy
import textwrap


class Premium_Assets_Preview(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Premium_Assets_Preview"
    bl_label = 'Premium assets previews'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Premium'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='Previews will be shown here')
    
class Premium_Main_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_Premium"
    bl_label = 'Blender Universe Premium'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Premium'

    def draw_disclaimer(self,context):
        disclaimer = 'This is the Blender Universe Premium section. You can verify your license in the premium settings. For more info see the link below.'
        wrapp = textwrap.TextWrapper(width=100) #50 = maximum length       
        wList = wrapp.wrap(text=disclaimer)
        box = self.layout.box()
        for text in wList:
            row = box.row(align=True)
            row.alignment = 'CENTER'
            row.label(text=text)
        gitbook = box.operator('wm.url_open',text='Gitbook',icon='INFO')
        gitbook.url= 'https://bakeduniverse.gitbook.io/baked-blender-pro-suite/introduction/welcome-to-baked-blender-pro-suite'

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        self.draw_disclaimer(context)





classes =(
    Premium_Main_Panel,
    
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
       