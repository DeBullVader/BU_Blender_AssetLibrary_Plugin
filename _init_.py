bl_info = {
    "name": "Baked Universe Asset Library",
    "description": "Dynamically adds all Assets from Baked Universe into the Asset Browser",
    "author": "Baked Universe",
    "version": (1, 0, 0),
    "blender": (3, 5, 0),
    "location": "Asset Browser",
    "warning": "",
    "wiki_url": "https://github.com/DeBullVader/BU_Blender_AssetLibrary_Plugin/wiki",
    "tracker_url": "https://github.com/DeBullVader/BU_Blender_AssetLibrary_Plugin/issues",
    "category": "Import-Export",
}

import bpy

#
# Add additional functions here
#

def register():
    from . import properties
    from . import ui
    properties.register()
    ui.register()

def unregister():
    from . import properties
    from . import ui
    properties.unregister()
    ui.unregister()


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()