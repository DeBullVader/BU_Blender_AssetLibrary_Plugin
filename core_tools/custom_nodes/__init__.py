from . import geometry_nodes
modules=[
    geometry_nodes,
]   

def register():
    for module in modules:
        module.register()
    

def unregister():
    for module in reversed(modules):
        module.unregister()