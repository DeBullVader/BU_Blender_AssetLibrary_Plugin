

from . import lib_preferences
from . import statusbar
from . import asset_lib_titlebar
from . import asset_mark_setup
from . import usefull_info_panel
from . import premium_settings

from . import Premium_Panels



def register():
    Premium_Panels.register()
    usefull_info_panel.register()
    premium_settings.register()
    asset_mark_setup.register()

    
def unregister():
    Premium_Panels.unregister()
    usefull_info_panel.unregister()
    premium_settings.unregister()
    asset_mark_setup.unregister()

    
    