from importlib import reload

if "bpy" in locals():
    import_dependencies = reload(import_dependencies)

else:
    import bpy
    from . import import_dependencies


def register():
    import_dependencies.try_import()


def unregister():
    pass
    

