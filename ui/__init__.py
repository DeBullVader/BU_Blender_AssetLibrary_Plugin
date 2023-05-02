from importlib import reload
if "bpy" in locals():
    lib_preferences = reload(lib_preferences)
    statusbar = reload(statusbar)


else:
    import bpy
    from . import lib_preferences
    from . import statusbar



def register():
    pass


def unregister():
    pass