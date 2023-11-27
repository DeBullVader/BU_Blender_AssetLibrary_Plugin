

from . import lib_preferences
from . import statusbar
from . import asset_lib_titlebar
from . import asset_mark_setup
from . import bu_main_panels
from . import premium_settings
from . import Premium_Panels
from . import create_mat_from_dir_files
from . import generate_previews




def register():
    bu_main_panels.register()
    Premium_Panels.register()
    premium_settings.register()
    asset_mark_setup.register()
    create_mat_from_dir_files.register()
    generate_previews.register()
    
def unregister():
    generate_previews.unregister()
    create_mat_from_dir_files.unregister()
    asset_mark_setup.unregister()
    premium_settings.unregister()
    Premium_Panels.unregister()
    bu_main_panels.unregister()
    
    
    
    

# import pkgutil
# import importlib
# import sys
# from pathlib import Path

# def register():
#     # Get the path of the current file (i.e., __init__.py of the 'ui' package)
#     package_path = Path(__file__).parent

#     # Iterate over all .py files in the directory
#     for (_, module_name, _) in pkgutil.iter_modules([package_path]):
#         # Import the module
#         module = importlib.import_module('.' + module_name, package=__name__)
        
#         # Check if the module has 'register' attribute, and call it if it exists
#         if hasattr(module, 'register'):
#             module.register()

# def unregister():
#     # Get the path of the current file
#     package_path = Path(__file__).parent

#     # Iterate over all .py files in the directory in reverse order
#     for (_, module_name, _) in pkgutil.iter_modules([package_path]):
#         # Import the module
#         module = importlib.import_module('.' + module_name, package=__name__)
        
#         # Check if the module has 'unregister' attribute, and call it if it exists
#         if hasattr(module, 'unregister'):
#             module.unregister()

#     # Remove imported modules from sys.modules
#     for module_name in list(sys.modules):
#         if module_name.startswith(__name__):
#             del sys.modules[module_name]