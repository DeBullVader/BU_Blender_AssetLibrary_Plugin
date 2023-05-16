

import bpy
import os
import sys
import subprocess
import importlib
from . import operators
from collections import namedtuple
from os import environ, makedirs, path, pathsep


py_dir = path.join(sys.prefix, 'bin', 'python.exe')
target = path.join(sys.prefix, 'lib', 'site-packages')

Dependency = namedtuple("Dependency", ["module", "package", "name"])

# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of your Python add-on, import them as usual with an
# "import" statement.

if sys.platform == 'win32':
    required_dependencies = [
        Dependency(module="moralis", package="moralis", name="moralis"),
        Dependency(module="googleapiclient", package="google-api-python-client", name="googleapiclient"),
        Dependency(module="oauth2client", package="oauth2client", name=None)
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


def install_pip():
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    :return:
    """
    bpy.ops.wm.console_toggle()

    print('THE CURRENT PYTHON DIR IS : ' + py_dir)
    try:
        # Check if pip is already installed
        subprocess.call([py_dir, "-m", "pip", "--version"])

    except subprocess.CalledProcessError:
        subprocess.call([py_dir, "-m", "ensurepip"])
        subprocess.call([py_dir, "-m", "pip", "install", "--upgrade", "pip"])


def install_and_import_module(module_name, package_name=None, global_name=None):
    """
    Installs the package through pip and attempts to import the installed module.
    :param module_name: Module to import.
    :param package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """
    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    subprocess.call([py_dir, "-m", "pip","install", package_name,'-t', target])
    # subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True, env=environ_copy)

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)





class EXAMPLE_PT_panel(bpy.types.Panel):
    bl_label = "Example Panel"
    bl_category = "Example Tab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        for dependency in required_dependencies:
            if dependency.name is None and hasattr(globals()[dependency.module], "__version__"):
                layout.label(text=f"{dependency.module} {globals()[dependency.module].__version__}")
            elif hasattr(globals()[dependency.name], "__version__"):
                layout.label(text=f"{dependency.module} {globals()[dependency.name].__version__}")
            else:
                layout.label(text=f"{dependency.module}")

        layout.operator(operators.EXAMPLE_OT_dummy_operator.bl_idname)


class EXAMPLE_PT_warning_panel(bpy.types.Panel):
    bl_label = "Example Warning"
    bl_category = "Example Tab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(self, context):
        return not dependencies_installed

    def draw(self, context):
        layout = self.layout

        lines = [f"Please install the missing dependencies for the BakedUniverse add-on.",
                 f"1. Open the preferences (Edit > Preferences > Add-ons).",
                 f"2. Search for the BakedUniverse add-on.",
                 f"3. Open the details section of the add-on.",
                 f"4. Click on the \"{operators.BU_OT_install_dependencies.bl_label}\" button.",
                 f"   This will download and install the missing Python packages, if Blender has the required",
                 f"   permissions.",
                 f"If you're attempting to run the add-on from the text editor, you won't see the options described",
                 f"above. Please install the add-on properly through the preferences.",
                 f"1. Open the add-on preferences (Edit > Preferences > Add-ons).",
                 f"2. Press the \"Install\" button.",
                 f"3. Search for the add-on file.",
                 f"4. Confirm the selection by pressing the \"Install Add-on\" button in the file browser."]

        for line in lines:
            layout.label(text=line)

def register():
    global dependencies_installed
    dependencies_installed = False
    bpy.utils.register_class(EXAMPLE_PT_warning_panel)

    try:
        for dependency in required_dependencies:
            import_module(module_name=dependency.module, global_name=dependency.name)
        dependencies_installed = True
        print('dependencies_installed= ' + str(dependencies_installed))
    except ModuleNotFoundError:
        # Don't register other panels, operators etc.
        return

    bpy.utils.register_class(EXAMPLE_PT_panel)


def unregister():
    bpy.utils.unregister_class(EXAMPLE_PT_warning_panel)

    if dependencies_installed:
        bpy.utils.unregister_class(EXAMPLE_PT_panel)
