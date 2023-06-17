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
from . import usefull_info_panel
from . import cats_and_tags





def register():
    usefull_info_panel.register()
    asset_mark_setup.register()
    cats_and_tags.register()
    pass


def unregister():
    usefull_info_panel.unregister()
    asset_mark_setup.unregister()
    cats_and_tags.unregister()
    pass