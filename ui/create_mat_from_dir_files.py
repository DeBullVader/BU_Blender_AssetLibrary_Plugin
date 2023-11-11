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
            if context.scene.new_material:
                new_mat = bpy.data.materials.new(name="BU_Material")
                ob =bpy.context.active_object
                ob.data.materials.append(new_mat)
                    
                new_mat.use_nodes = True
                node_tree = new_mat.node_tree
                nodes = node_tree.nodes
            else:
                context.material.use_nodes = True
                node_tree = context.material.node_tree
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
            node_tree.links.new(tex_coord_node.outputs["UV"], mapping_node.inputs[0])
            
            for file in self.files:

                filepath = os.path.join(self.directory, file.name)
                self.texture_paths.append(filepath)
                base_name=file.name.split('.')[0]
                if base_name.endswith('_BaseColor'):
                    Base_color_node = nodes.new(type= 'ShaderNodeTexImage')
                    Base_color_node.location =(-800, 600)
                    Base_color_node.image = bpy.data.images.load(filepath)
                    node_tree.links.new(Base_color_node.outputs[0], bsdf.inputs[0])
                    node_tree.links.new(mapping_node.outputs["Vector"], Base_color_node.inputs["Vector"])

                if base_name.endswith('_Roughness'):
                    roughness_node = nodes.new(type= 'ShaderNodeTexImage')
                    roughness_node.location =(-800, 300)
                    roughness_node.image = bpy.data.images.load(filepath)
                    roughness_node.image.colorspace_settings.name = 'Non-Color'
                    node_tree.links.new(roughness_node.outputs[0], bsdf.inputs[7])
                    node_tree.links.new(mapping_node.outputs["Vector"], roughness_node.inputs["Vector"])

                if base_name.endswith('_Metallic'):
                    metallic_node = nodes.new(type= 'ShaderNodeTexImage')
                    metallic_node.location =(-800, 0)
                    metallic_node.image = bpy.data.images.load(filepath)
                    metallic_node.image.colorspace_settings.name = 'Non-Color'
                    node_tree.links.new(metallic_node.outputs[0], bsdf.inputs[4])
                    node_tree.links.new(mapping_node.outputs["Vector"], metallic_node.inputs["Vector"])

                if base_name.endswith('_Normal'):
                    normal_node = nodes.new(type= 'ShaderNodeTexImage')
                    normal_node.location =(-800, -300)
                    normal_node.image = bpy.data.images.load(filepath)
                    normal_node.image.colorspace_settings.name = 'Non-Color'
                    node_tree.links.new(normal_node.outputs[0], bsdf.inputs[19])
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
        

class NODE_MT_BU_ToolsMenu(bpy.types.Menu):
    bl_space_type = 'NODE_EDITOR'
    bl_label = "BU_Tools"

    def draw(self, context):
        layout = self.layout
        # snode = context.space_data
        # if snode.tree_type == 'GeometryNodeTree':
        layout.operator("node.create_material_from_dir", text="Make Material From Directory Textures", icon='FILE_FOLDER')

# class Material_PT_FromDir(BU_MaterialButtonsPanel,PropertyPanel,Panel):
#     bl_label = 'Create Material From Directory'
#     bl_options = {'DEFAULT_CLOSED'}
#     COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'BLENDER_WORKBENCH_NEXT'}
#     def draw(self, context):
#         layout = self.layout
#         layout.label(text = 'Create Material From Directory')
#         layout.operator('node.create_material_from_dir')

class BU_PT_MaterialFromDir_Context_Material(BU_MaterialButtonsPanel,Panel):
    bl_label = 'Create Material From Directory'
    bl_context = "material"
    bl_order = 8
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'BLENDER_WORKBENCH_NEXT'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        mat = context.material

        if (ob and ob.type == 'GPENCIL') or (mat and mat.grease_pencil):
            return False

        return (ob or mat) and (context.engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        scene = context.scene
        ob = context.object
        if ob:
            layout = self.layout
            row = layout.row(align = True)
            row.alignment = 'LEFT'
            row.prop(scene, "new_material", toggle=True,)
            row.label(text = '--->')
            row.alignment = 'RIGHT'
            row.operator('node.create_material_from_dir')

def draw_BU_ToolsMenu(self,context):
    layout = self.layout
    layout.menu('NODE_MT_BU_ToolsMenu')

classes =(
    TextureProperties,
    NODE_MT_BU_ToolsMenu,
    # Material_PT_FromDir,
    BU_PT_MaterialFromDir_Context_Material,
    NODE_OT_CreateMaterialFromDir,
    
    
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_PT_active_node_generic.append(node_location)
    bpy.types.NODE_MT_editor_menus.append(draw_BU_ToolsMenu)
    bpy.types.Scene.texture_props = bpy.props.PointerProperty(type=TextureProperties)
    bpy.types.Scene.new_material = bpy.props.BoolProperty(name="New Material?", default=True)
    # bpy.utils.register_module(__name__)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.NODE_PT_active_node_generic.remove(node_location)
    bpy.types.NODE_MT_editor_menus.remove(draw_BU_ToolsMenu)
    del bpy.types.Scene.texture_props
    # bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
   pass 