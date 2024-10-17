from . import asset_manager_render_previews, asset_manager_asset_data,asset_manager_ui,asset_manager_utils,asset_manager_light_setups
# from .asset_manager_utils import AssetManagerPrefs
modules=[
    asset_manager_utils,
    asset_manager_light_setups,
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