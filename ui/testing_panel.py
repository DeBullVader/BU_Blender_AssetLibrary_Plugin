import bpy
from ..utils import addon_info

class TestUploadPremium(bpy.types.Operator):
    bl_idname = "wm.test_upload" 
    bl_label = "Test Upload" 
    bl_description = "Test Upload"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # download_placeholder_files.get_catfile_from_server(self,context)
        return{'FINISHED'}
    
# class BU_PT_TestPremium_Panel(bpy.types.Panel):
#     bl_idname = "VIEW3D_PT_TEST_PREMIUM_PANEL" 
#     bl_label = "Test Premium Panel" 
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = 'BU Premium'

#     def draw (self, context):
#         layout = self.layout
#         row = layout.row()
#         row.operator('wm.test_upload', text="Test Button")

def drawTestButton (self, context):
    layout = self.layout
    row = layout.row()
    layout.operator('wm.test_upload', text="Test Button")

classes = (
    TestUploadPremium,
    # BU_PT_TestPremium_Panel,    
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(drawTestButton)
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(drawTestButton)