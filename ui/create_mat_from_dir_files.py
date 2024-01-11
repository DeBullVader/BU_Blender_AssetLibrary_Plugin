import bpy
import os
from bpy.types import Panel,PropertyGroup,Operator
from bpy.props import StringProperty,CollectionProperty
from rna_prop_ui import PropertyPanel
from bpy_extras.io_utils import ImportHelper
from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
)



class BU_MaterialButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and (context.engine in cls.COMPAT_ENGINES) and not mat.grease_pencil
    
class TextureProperties(PropertyGroup):
    texture_dir: StringProperty(
        name = "New AssetLibrary directory",
        description = "Choose a directory",
        maxlen = 1024,
        subtype = 'DIR_PATH',
    )

class WM_OT_CreateMaterialFromDir(Operator, ImportHelper):
    bl_idname = "wm.create_material_from_dir"
    bl_label = 'Create Material From Directory'
    bl_description = 'Create Material From Directory'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.png'

    filter_glob: StringProperty(
        default='*.png',
        options={'HIDDEN'},
    )

    # @classmethod
    # def poll(cls, context):
    #     scene = context.scene
    #     if scene.texture_dir != '':
    #         if os.path.exists(str(scene.texture_dir)):
    #             return True

    def execute(self, context):
        print('imported file: ', self.filepath)
        return {'FINISHED'}
    

def node_location(self, context):
    layout = self.layout
    col = layout.column(align=True)

    space_data = bpy.context.space_data
    act_node = space_data.node_tree.nodes.active

    col.label(text="Node Location:")
    col.label(text=f"X = {act_node.location.x}")
    col.label(text=f"Y = {act_node.location.y}")                 


class NODE_OT_CreateMaterialFromDir(Operator, ImportHelper):
    bl_idname = "node.create_material_from_dir"
    bl_label = 'Create Material From Directory'
    bl_description = 'Create Material From Directory'
    bl_options = {'REGISTER', 'UNDO'}

    files: CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH',)
    filename_ext = '.png'

    filter_glob: StringProperty(
        default='*.png',
        options={'HIDDEN','SKIP_SAVE'},
    )
    texture_paths =[]



    def execute(self, context):
 
        if bpy.context.space_data.type =="NODE_EDITOR":
            space = context.space_data
            node_tree = space.node_tree
            nodes = node_tree.nodes
        elif bpy.context.space_data.type =="PROPERTIES":
            new_mat = bpy.data.materials.new(name="BU_Material")
            ob =bpy.context.active_object
            ob.data.materials.append(new_mat)
                
            new_mat.use_nodes = True
            node_tree = new_mat.node_tree
            nodes = node_tree.nodes

        if nodes:
            bsdf = nodes.get("Principled BSDF")
            output = nodes.get("Material Output")
            tex_coord_node = nodes.get("Texture Coordinate")
            mapping_node = nodes.get("Mapping")
            if not bsdf:
                bsdf = nodes.new(type= "ShaderNodeBsdfPrincipled")
                bsdf.location =(-82, 160)
            if not output:
                output = nodes.new(type= "ShaderNodeOutputMaterial")
                output.location =(400, 200)
            
            if not tex_coord_node:
                tex_coord_node = nodes.new(type= 'ShaderNodeTexCoord')
                tex_coord_node.location =(-1400, 200)
            if not mapping_node:
                mapping_node = nodes.new(type= 'ShaderNodeMapping')
                mapping_node.location =(-1150, 230)

            node_tree.links.new(bsdf.outputs[0], output.inputs[0])
            node_tree.links.new(tex_coord_node.outputs["Object"], mapping_node.inputs[0])
            
            for file in self.files:

                filepath = os.path.join(self.directory, file.name)
                self.texture_paths.append(filepath)
                base_name=file.name.split('.')[0]
                if base_name.endswith('_BaseColor'):
                    Base_color_node = nodes.new(type= 'ShaderNodeTexImage')
                    Base_color_node.location =(-800, 600)
                    Base_color_node.image = bpy.data.images.load(filepath)
                    node_tree.links.new(Base_color_node.outputs[0], bsdf.inputs['Base Color'])
                    node_tree.links.new(mapping_node.outputs["Vector"], Base_color_node.inputs["Vector"])

                if base_name.endswith('_Roughness'):
                    roughness_node = nodes.new(type= 'ShaderNodeTexImage')
                    roughness_node.location =(-800, 300)
                    roughness_node.image = bpy.data.images.load(filepath)
                    roughness_node.image.colorspace_settings.name = 'Non-Color'
                    node_tree.links.new(roughness_node.outputs[0], bsdf.inputs['Metallic'])
                    node_tree.links.new(mapping_node.outputs["Vector"], roughness_node.inputs["Vector"])

                if base_name.endswith('_Metallic'):
                    metallic_node = nodes.new(type= 'ShaderNodeTexImage')
                    metallic_node.location =(-800, 0)
                    metallic_node.image = bpy.data.images.load(filepath)
                    metallic_node.image.colorspace_settings.name = 'Non-Color'
                    node_tree.links.new(metallic_node.outputs[0], bsdf.inputs['Roughness'])
                    node_tree.links.new(mapping_node.outputs["Vector"], metallic_node.inputs["Vector"])

                if base_name.endswith('_Normal'):
                    normal_node = nodes.new(type= 'ShaderNodeTexImage')
                    normal_node.location =(-800, -300)
                    normal_node.image = bpy.data.images.load(filepath)
                    normal_node.image.colorspace_settings.name = 'Non-Color'

                    normal_map_node = nodes.new(type= 'ShaderNodeNormalMap')
                    normal_map_node.location =(-500, -300)
                    normal_map_node.space = 'TANGENT'
                    node_tree.links.new(normal_node.outputs[0], normal_map_node.inputs['Color'])
                    node_tree.links.new(normal_map_node.outputs[0], bsdf.inputs['Normal'])
                    node_tree.links.new(mapping_node.outputs["Vector"], normal_node.inputs["Vector"])

                if base_name.endswith('_Displacement'):
                    tex_displacement_node = nodes.new(type= 'ShaderNodeTexImage')
                    tex_displacement_node.location =(-800, -600)
                    tex_displacement_node.image = bpy.data.images.load(filepath)
                    tex_displacement_node.image.colorspace_settings.name = 'Non-Color'

                    displacement_node = nodes.new(type= 'ShaderNodeDisplacement')
                    displacement_node.location =(15, -526)

                    node_tree.links.new(mapping_node.outputs[0], tex_displacement_node.inputs[0])
                    node_tree.links.new(tex_displacement_node.outputs[0], displacement_node.inputs[0])
                    node_tree.links.new(displacement_node.outputs["Displacement"], output.inputs["Displacement"])
            
        return {'FINISHED'}
# BSDF Input pins reference
# (0, 'Base Color')
# (1, 'Subsurface')
# (2, 'Subsurface Radius')
# (3, 'Subsurface Color')
# (4, 'Metallic')
# (5, 'Specular')
# (6, 'Specular Tint')
# (7, 'Roughness')
# (8, 'Anisotropic')
# (9, 'Anisotropic Rotation')
# (10, 'Sheen')
# (11, 'Sheen Tint')
# (12, 'Clearcoat')
# (13, 'Clearcoat Roughness')
# (14, 'IOR')
# (15, 'Transmission')
# (16, 'Transmission Roughness')
# (17, 'Emission')
# (18, 'Alpha')
# (19, 'Normal')
# (20, 'Clearcoat Normal')
# (21, 'Tangent')
  


# class NODE_MT_BU_ToolsMenu(bpy.types.Menu):
#     bl_space_type = 'NODE_EDITOR'
#     bl_label = "BU_Tools"
#     bl_order = 1
#     def draw(self, context):
#         layout = self.layout
#         box = layout.box()
#         box.label(text="Selected material options")
#         box.operator("bu.switch_assigned_material", text="Switch Assigned Material", icon='MATERIAL')
#         box = layout.box()
#         box.label(text="Create Materials")
#         box.operator("node.create_material_from_dir", text="Make Material From Directory Textures", icon='FILE_FOLDER')
        


 


class BU_OT_SwitchAssignedMaterial(Operator):
    bl_idname = "bu.switch_assigned_material"
    bl_label = "Switch assigned material"
    bl_description = "Switch assigned material"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        slot = obj.active_material
        if slot is None:
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        slot = obj.active_material

        if slot is not None:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.material_slot_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}


# class BU_PT_MaterialFromDir_Context_Material(BU_MaterialButtonsPanel,Panel):
#     bl_idname ="VIEW3D_BU_PT_MaterialFromDir_Context_Material"
#     bl_label = 'BU Material Tools'
#     bl_context = "material"
#     bl_order = 1
#     COMPAT_ENGINES = {'CYCLES','BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'BLENDER_WORKBENCH_NEXT'}

#     @classmethod
#     def poll(cls, context):
#         ob = context.object
#         mat = context.material

#         if (ob and ob.type == 'GPENCIL') or (mat and mat.grease_pencil):
#             return False

#         return (ob or mat) and (context.engine in cls.COMPAT_ENGINES)
    
#     def draw(self, context):
#         scene = context.scene
#         ob = context.object
#         if ob:
#             layout = self.layout
#             col = layout.column(align = True)
#             box = col.box()
#             row = box.row(align = True)
#             row.alignment = 'EXPAND'
#             row.label(text='Make Material From Directory Textures')
#             row.operator("node.create_material_from_dir", text="Choose Target folder", icon='FILE_FOLDER')
#             box = col.box()
#             row = box.row(align = True)
#             row.label(text="Switch Assigned Material")
#             row.operator("bu.switch_assigned_material", text="Switch Assigned Material", icon='MATERIAL')

class BU_PT_MatToolsMenu(BU_MaterialButtonsPanel,bpy.types.Panel):
    bl_label = "BU Material Tools"
    bl_order = 1
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES','BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'BLENDER_WORKBENCH_NEXT'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        mat = context.material

        if (ob and ob.type == 'GPENCIL') or (mat and mat.grease_pencil):
            return False

        return (ob or mat) and (context.engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Create Materials")
        icon = context.material.preview.icon_id
        box.operator("bu.switch_assigned_material", text="Set active material", icon_value=icon)
        box = layout.box()
        box.label(text="Selected material options")
        box.operator("node.create_material_from_dir", text="Make Material From Directory Textures", icon='FILE_FOLDER')
            

def draw_bu_mat_tools(self, context):
    layout = self.layout
    layout.operator('bu.switch_assigned_material',text='Selected as active',icon='MATSHADERBALL')
    layout.operator("node.create_material_from_dir", text="Make Material From Directory Textures", icon='FILE_FOLDER')


def draw_BU_ToolsMenu(self,context):
    layout = self.layout
    layout.menu('NODE_MT_BU_ToolsMenu')

    

classes =(
    TextureProperties,
    # NODE_MT_BU_ToolsMenu,
    BU_PT_MatToolsMenu,
    # BU_PT_MaterialFromDir_Context_Material,
    NODE_OT_CreateMaterialFromDir,
    BU_OT_SwitchAssignedMaterial,
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_PT_active_node_generic.append(node_location)
    # bpy.types.NODE_MT_editor_menus.append(draw_BU_ToolsMenu)
    # bpy.types.EEVEE_MATERIAL_PT_context_material.append(draw_bu_mat_tools)
    bpy.types.Scene.texture_props = bpy.props.PointerProperty(type=TextureProperties)
    # bpy.utils.register_module(__name__)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.NODE_PT_active_node_generic.remove(node_location)
    # bpy.types.NODE_MT_editor_menus.remove(draw_BU_ToolsMenu)
    # bpy.types.EEVEE_MATERIAL_PT_context_material.remove(draw_bu_mat_tools)
    del bpy.types.Scene.texture_props
    # bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
   pass 