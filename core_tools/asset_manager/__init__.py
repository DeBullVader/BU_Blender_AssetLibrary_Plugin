from . import asset_manager_render_previews, asset_manager_asset_data,asset_manager_ui,asset_manager_utils

modules=[
    asset_manager_utils,
    asset_manager_ui,
    asset_manager_render_previews,
    asset_manager_asset_data,
]   

def register():
    for module in modules:
        module.register()
    

def unregister():
    for module in reversed(modules):
        module.unregister()