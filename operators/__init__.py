from ..dependencies import import_dependencies
from . import add_lib_path

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
        # print(moralis.__version__)
        # print(oauth2client.__version__)
        # print(api_version)
        return {"FINISHED"}
    


def importDependantFiles():


    from . import task_manager,asset_sync_operators,download_library_files,download_original_asset,sync_ui_progress_handler
    classes = (task_manager,asset_sync_operators,download_library_files,download_original_asset,sync_ui_progress_handler)
    return classes


class BU_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "wm.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        # Deactivate when dependencies have been installed
       
        return not import_dependencies.dependencies_installed

    def execute(self, context):
        try:
            for dependency in import_dependencies.required_dependencies:
                import_dependencies.import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        import_dependencies.dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        
        for clas in importDependantFiles():
            clas.register()
 
        return {"FINISHED"}


classes = {
    add_lib_path.BU_OT_AddLibraryPath,
    add_lib_path.BU_OT_RemoveLibrary,
    add_lib_path.BU_OT_ConfirmSetting,
    EXAMPLE_OT_dummy_operator,
    }


def register():
    import_dependencies.dependencies_installed = False
    bpy.utils.register_class(BU_OT_install_dependencies)

    try:
        for dependency in import_dependencies.required_dependencies:
            import_dependencies.import_module(module_name=dependency.module, global_name=dependency.name)
        import_dependencies.dependencies_installed = True
    except ModuleNotFoundError:
        # Don't register other panels, operators etc.
        return

    for cls in importDependantFiles():
        cls.register()  
    for cls in classes:
        bpy.utils.register_class(cls)
    


def unregister():
    bpy.utils.unregister_class(BU_OT_install_dependencies)
    if import_dependencies.dependencies_installed:
       
        for cls in importDependantFiles():
            cls.unregister()
        for cls in classes:
            bpy.utils.unregister_class(cls)
    



