from bpy.utils import register_classes_factory
from . import connect_vertices_node


modules=[
    connect_vertices_node,
]   

def register():
    for module in modules:
        module.register()
    

def unregister():
    for module in reversed(modules):
        module.unregister()