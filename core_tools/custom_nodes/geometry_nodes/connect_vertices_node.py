import bpy
from bpy.types import Node, NodeSocket, NodeTree,NodeCustomGroup
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from mathutils import Vector
from bpy.utils import register_classes_factory

class MyCustomTree(NodeTree):
    # Description string
    '''A custom node tree type that will show up in the editor type list'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'CustomTreeType'
    # Label for nice name display
    bl_label = "Custom Node Tree"
    # Icon identifier
    bl_icon = 'NODETREE'

class ConnectVerticesNode(Node):
  bl_idname = "GeometryNodeConnectVertices"
  bl_label = "Connect Vertices"
  bl_icon = 'NODE'
  
  def init(self, context):
      self.inputs.new('NodeSocketGeometry', "Geometry")
      self.outputs.new('NodeSocketGeometry', "Geometry")

  def update(self):
      # Get the input geometry
      input_geo = self.inputs[0].default_value
      
      # Create a new mesh to store connected vertices
      new_mesh = bpy.data.meshes.new("ConnectedMesh")
      new_obj = bpy.data.objects.new("ConnectedObject", new_mesh)
      
      # Link the new object to the scene
      bpy.context.collection.objects.link(new_obj)
      
      # Get selected vertices
      selected_verts = [v for v in input_geo.vertices if v.select]
      
      # Create edges between selected vertices
      edges = [(i, j) for i in range(len(selected_verts)) for j in range(i + 1, len(selected_verts))]
      
      # Create the mesh
      new_mesh.from_pydata([v.co for v in selected_verts], edges, [])
      new_mesh.update()
      
      # Set the output geometry
      self.outputs[0].default_value = new_obj.data

class MyCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'CustomTreeType'



classes=(
    ConnectVerticesNode,
)

register_classes, unregister_classes = register_classes_factory(classes)

def register():
    register_classes()

def unregister():
    unregister_classes()