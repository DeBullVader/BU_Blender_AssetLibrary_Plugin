import os
import sys
import importlib
from collections import namedtuple


def get_addon_file_path(bu_name):
    filepath = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(filepath + '/windows')


Dependency = namedtuple("Dependency", ["module", "package", "name"])

# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of your Python add-on, import them as usual with an
# "import" statement.


required_dependencies = [

    Dependency(module="googleapiclient", package="google-api-python-client", name="googleapiclient"),
    Dependency(module="oauth2client", package="oauth2client", name=None),
]


dependencies_installed = False


def import_module(module_name, global_name=None, reload=True):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    if global_name is None:
        global_name = module_name

    if global_name in globals():
        importlib.reload(globals()[global_name])
    else:
        # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
        # the given name, just like the regular import would.
        globals()[global_name] = importlib.import_module(module_name)
def try_import():
    global dependencies_installed
    dependencies_installed = False
    try:
        for dependency in required_dependencies:
            import_module(module_name=dependency.module, global_name=dependency.name)
        dependencies_installed = True
    except ModuleNotFoundError:
        
        return

