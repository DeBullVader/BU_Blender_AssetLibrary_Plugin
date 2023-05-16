# from importlib import reload
# if "bpy" in locals():
#     lib_preferences = reload(lib_preferences)
#     statusbar = reload(statusbar)
#     asset_lib_titlebar = reload(asset_lib_titlebar)


# else:
import bpy
from bpy.types import Header, Menu, Panel
from . import lib_preferences
from . import statusbar
from . import asset_lib_titlebar
from . import asset_mark_setup





def register():
    # asset_mark_setup.register()
    bpy.utils.register_class(asset_lib_titlebar.AssetLibraryOperations)
    pass


def unregister():
    # asset_mark_setup.unregister()
    bpy.utils.unregister_class(asset_lib_titlebar.AssetLibraryOperations)
    pass