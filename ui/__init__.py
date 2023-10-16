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
from . import premium_settings
from . import cats_and_tags
from . import Premium_Panels
from . import testing_panel






def register():
    Premium_Panels.register()
    usefull_info_panel.register()
    premium_settings.register()
    asset_mark_setup.register()

  
    testing_panel.register()
    


def unregister():
    Premium_Panels.unregister()
    usefull_info_panel.unregister()
    premium_settings.unregister()
    asset_mark_setup.unregister()

    # bpy.types.ASSETBROWSER_MT_editor_menus.remove(asset_lib_titlebar.draw_menu)
    testing_panel.unregister()
    
    