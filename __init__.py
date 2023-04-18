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
# import bpy, pip
# pip.main(['install', 'moralis', '--user'])
import math
# imports the __init__.py files from the folders. each init files holds the classes for that folder
from . import operators
from . import ui



from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from bpy.props import (
	StringProperty,
	BoolProperty,
	IntProperty,
	IntVectorProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty,
	PointerProperty,
)

class BUPrefWeb3Auth(AddonPreferences):
    bl_idname = __package__

    bsc_wallet_address: StringProperty(
        name="BSC Wallet address",
        description="Input wallet",
        default=""
        # 0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2
    )
    # 0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2
    def draw(self, context):
        
        layout = self.layout
        row = layout.row()
        row.label (text = context.scene.statustext)
        row = layout.row()
        row.prop(self, 'bsc_wallet_address')
        col = row.column()
        col.operator('bu.verify', text = context.scene.buttontext)
      

#
# Add additional functions here
#
 
classes = [BUPrefWeb3Auth] + ui.classes + operators.classes

def register():

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.buttontext = bpy.props.StringProperty(name="buttontext", default="Verify wallet")
    bpy.types.Scene.statustext = bpy.props.StringProperty(name="statustext", default="Please verify that you are a Piffle Puppet Holder")




def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.buttontext
    del bpy.types.Scene.statustext

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

