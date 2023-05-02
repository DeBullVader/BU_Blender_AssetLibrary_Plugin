import importlib.util
import importlib.machinery
from .. import bu_dependencies
from .add_lib_path import BU_OT_AddLibraryPath
import subprocess
import bpy




class EXAMPLE_OT_dummy_operator(bpy.types.Operator):
    bl_idname = "example.dummy_operator"
    bl_label = "Dummy Operator"
    bl_description = "This operator tries to use Moralis."
    bl_options = {"REGISTER"}
    
    def execute(self, context):
        from googleapiclient import version
        api_version = version .__version__
        print(moralis.__version__)
        print(oauth2client.__version__)
        print(api_version)
        return {"FINISHED"}
    


def importDependantFiles():
    from . import library_download,verify_holder
    classes = (library_download,verify_holder)
    print('lib and verify  REGISTEREd')
    return classes
# def is_installed(dependency: bu_dependencies.Dependency) -> bool:
#     """ Checks if dependency is installed. """
#     try:
#         spec = importlib.util.find_spec(dependency.name)
#     except (ModuleNotFoundError, ValueError, AttributeError):
#         return False

#     # only accept it as valid if there is a source file for the module - not bytecode only.
#     if issubclass(type(spec), importlib.machinery.ModuleSpec):
#         return True
#     return False
# dependencies_installed = [is_installed(dependency) for dependency in bu_dependencies.required_dependencies]   

class BU_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "example.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        # Deactivate when dependencies have been installed
       
        return not bu_dependencies.dependencies_installed

    def execute(self, context):
        try:
            bu_dependencies.install_pip()
            for dependency in bu_dependencies.required_dependencies:
                bu_dependencies.install_and_import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        bu_dependencies.dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        
        bpy.utils.register_class(EXAMPLE_OT_dummy_operator)
        
        for clas in importDependantFiles():
            clas.register()
 
        return {"FINISHED"}

def register():
    bu_dependencies.dependencies_installed = False
    bpy.utils.register_class(BU_OT_install_dependencies)
    bpy.utils.register_class(BU_OT_AddLibraryPath)
    print(str(bu_dependencies.dependencies_installed))
    print('BU_OT_install_dependencies  REGISTEREd')
    try:
        for dependency in bu_dependencies.required_dependencies:
            bu_dependencies.import_module(module_name=dependency.module, global_name=dependency.name)
        bu_dependencies.dependencies_installed = True
        print('dependencies_installed= ' + str(bu_dependencies.dependencies_installed))
    except ModuleNotFoundError:
        # Don't register other panels, operators etc.
        return


    bpy.utils.register_class(EXAMPLE_OT_dummy_operator)
    for cls in importDependantFiles():
        cls.register()

def unregister():
    bpy.utils.unregister_class(BU_OT_install_dependencies)
    bpy.utils.unregister_class(BU_OT_AddLibraryPath)
    if bu_dependencies.dependencies_installed:
        bpy.utils.unregister_class(EXAMPLE_OT_dummy_operator)
        
        for cls in importDependantFiles():
            cls.unregister()


