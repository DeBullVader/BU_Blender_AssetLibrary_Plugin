import bpy
from bpy.types import Panel
#
# Add additional functions here
#
        
       
# testing panel menu within render tab
class MyPanel(Panel):
    bl_label = 'My Awesome Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type= 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        row = self.layout.row()
        row.prop(context.scene, 'my_property')
        # self.layout.operator("mesh.add_cube_sample", icon='MESH_CUBE', text="Add Cube")

def register():
    bpy.utils.register_class(MyPanel)

def unregister():
    bpy.utils.unregister_class(MyPanel)