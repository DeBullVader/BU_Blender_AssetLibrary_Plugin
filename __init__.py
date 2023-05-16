# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

#check how these guys did it!!!
# https://github.com/cgtinker/BlendArMocap/tree/main/src/cgt_mediapipe


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


from importlib import reload
if "bpy" in locals():
    # bu_dependencies = reload(bu_dependencies)
    ui = reload(ui)
    operators = reload(operators)
    dependencies = reload(dependencies)
    icons = reload(icons)
    utils = reload(utils)
else:
    import bpy
    from . import dependencies
    # from . import bu_dependencies
    from . import ui
    from . import operators
    from . import icons
    from . import utils
 
    

class AllPrefs(ui.lib_preferences.BUPrefLib):
    bl_idname = __package__

class BUProperties(bpy.types.PropertyGroup):
    progress_total: bpy.props.FloatProperty(default=0, options={"HIDDEN"})  
    progress_percent: bpy.props.IntProperty(
        default=0, min=0, max=100, step=1, subtype="PERCENTAGE", options={"HIDDEN"}
    )
    progress_word: bpy.props.StringProperty(options={"HIDDEN"})  
    progress_downloaded_text: bpy.props.StringProperty(options={"HIDDEN"})
    new_assets: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
    addon_name: bpy.props.StringProperty(options={"HIDDEN"})

classes = (AllPrefs,BUProperties)

dependencies.import_dependencies.get_addon_file_path(bl_info["name"])

def register():
    dependencies.register()
    ui.register()
    icons.previews_register()
    
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.bu_props = bpy.props.PointerProperty(type=BUProperties)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(ui.asset_lib_titlebar.draw_menu)
    operators.register()
    
def unregister():
    # dependencies.unregister()
    dependencies.unregister()
    ui.unregister()
    icons.previews_unregister()
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.bu_props
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(ui.asset_lib_titlebar.draw_menu)
    operators.unregister()
    
#       
# Add additional functions here
#



# imports the __init__.py files from the folders. each init files holds the classes for that folder


           
# classes =(ui.classes)

# pref_classes =(install_deps.BU_OT_install_dependencies)

# def register():

#     for cls in pref_classes:
#             bpy.utils.register_class(cls)
    
#     if install_deps.TryLoadModules() is True:

#         for cls in classes:
#             bpy.utils.register_class(cls)
#         bpy.types.Scene.buttontext = bpy.props.StringProperty(name="buttontext", default="Verify wallet")
#         bpy.types.Scene.statustext = bpy.props.StringProperty(name="statustext", default="Please verify that you are a Piffle Puppet Holder")
#         bpy.context.preferences.use_preferences_save = True

# def unregister():
#     for cls in classes:
#             bpy.utils.register_class(cls)

#     for cls in classes:
#         bpy.utils.unregister_class(cls)
#     del bpy.types.Scene.buttontext
#     del bpy.types.Scene.statustext

#     # This allows you to run the script directly from Blender's Text editor
#     # to test the add-on without having to install it.
if __name__ == "__main__":
    register()

