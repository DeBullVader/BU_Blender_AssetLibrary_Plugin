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
    "name": "Blender Universe",
    "description": "Dynamically adds all Assets from Baked Universe into the Asset Browser",
    "author": "Baked Universe",
    "version": (0, 2, 91),
    "blender": (3, 5, 0),
    "location": "Asset Browser",
    "warning": "",
    "wiki_url": "https://github.com/DeBullVader/BU_Blender_AssetLibrary_Plugin/wiki",
    "tracker_url": "https://github.com/DeBullVader/BU_Blender_AssetLibrary_Plugin/issues",
    "category": "Import-Export",
}

from importlib import reload
from . import addon_updater_ops
from bpy.types import AddonPreferences
if "bpy" in locals():
    ui = reload(ui)
    operators = reload(operators)
    dependencies = reload(dependencies)
    icons = reload(icons)
    utils = reload(utils)
    
else:
    import bpy
    from . import dependencies
    from . import ui
    from . import operators
    from . import icons
    from . import utils

 
    
@addon_updater_ops.make_annotations
class AddonUpdate(AddonPreferences):
    bl_idname = __package__

    get_dev_updates= bpy.props.BoolProperty(
		name="Get development releases(USE AT OWN RISK!)",
		description="Only used to get development branches, wich are not production ready. USE AT OWN RISK!",
		default=False
        )

    auto_check_update= bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

    updater_interval_months= bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

    updater_interval_days= bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

    updater_interval_hours= bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

    updater_interval_minutes= bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)

class AllPrefs(ui.lib_preferences.BUPrefLib,AddonUpdate,utils.config.config_props):
    bl_idname = __package__

class BUProperties(bpy.types.PropertyGroup):
    progress_total: bpy.props.FloatProperty(default=0, options={"HIDDEN"})  
    progress_percent: bpy.props.IntProperty(
        default=0, min=0, max=100, step=1, subtype="PERCENTAGE", options={"HIDDEN"}
    )
    progress_word: bpy.props.StringProperty(options={"HIDDEN"})  
    progress_downloaded_text: bpy.props.StringProperty(options={"HIDDEN"})
    assets_to_upload: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
    new_assets: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
    updated_assets: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
    addon_name: bpy.props.StringProperty(options={"HIDDEN"})

classes = (BUProperties,AllPrefs)

dependencies.import_dependencies.get_addon_file_path(bl_info["name"])

def register():
    dependencies.register()
    addon_updater_ops.register(bl_info)
    addon_updater_ops.make_annotations(AddonUpdate)
    

    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    utils.register()
    ui.register()
    icons.previews_register()
    operators.register()
    
    bpy.types.WindowManager.bu_props = bpy.props.PointerProperty(type=BUProperties)
    bpy.context.preferences.use_preferences_save = True
    bpy.types.ASSETBROWSER_MT_editor_menus.append(ui.asset_lib_titlebar.draw_menu)
    
    
def unregister():
    dependencies.unregister()
    addon_updater_ops.unregister()
    # bpy.utils.unregister_class(AllPrefs)

    for cls in classes:
        bpy.utils.unregister_class(cls) 
    operators.unregister()
    icons.previews_unregister()
    ui.unregister()
    utils.unregister()
    
    
    
    del bpy.types.WindowManager.bu_props
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(ui.asset_lib_titlebar.draw_menu)

#     # This allows you to run the script directly from Blender's Text editor
#     # to test the add-on without having to install it.
if __name__ == "__main__":
    register()

