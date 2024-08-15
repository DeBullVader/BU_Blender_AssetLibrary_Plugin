from . import asset_manager,preview_render_scene
modules=[
    asset_manager,
    preview_render_scene,
]   

def register():
    for module in modules:
        module.register()
    

def unregister():
    for module in reversed(modules):
        module.unregister()