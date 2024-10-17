
from . import asset_manager,preview_render_scene,custom_nodes,dynamic_geo_group_input

modules=[
    asset_manager,
    preview_render_scene,
    custom_nodes,
    #dynamic_geo_group_input
]   

def register():
    for module in modules:
        module.register()
    

def unregister():
    for module in reversed(modules):
        module.unregister()