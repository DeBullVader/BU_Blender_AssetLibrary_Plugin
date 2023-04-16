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
import owners #Does not work in addon? missing moralis moodule check moralisSDK or venv
import bpy
import math


#from . import auto_load


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

#
# Add additional functions here
#
 

class inputWalletAdress(bpy.types.AddonPreferences):
    bl_idname = __name__

    bsc_wallet_address: bpy.props.StringProperty(
        name="BSC Wallet address",
        description="Input wallet",
        default=""
    )


    def draw(self, context):
            layout = self.layout
            layout.label(text='Verify your piffle puppet')
            row = layout.row()
            row.prop(self, 'bsc_wallet_address')
    
  
#print(wallet_address(inputWalletAdress.bsc_wallet_address))  
# classes = (
# 			Panel_Preferences,

# )
def register():

    # from bpy.utils import register_class
    # for cls in classes:
    #     register_class(cls)
    import properties
    import ui
    import owners
    currentAddress = "0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2"
    print(owners.wallet_address(currentAddress))
    properties.register()
    ui.register()
    bpy.utils.register_class(inputWalletAdress)



def unregister():
    
    # from bpy.utils import unregister_classF
    # for cls in reversed(classes):
    #     unregister_class(cls)
    import properties
    import ui
    properties.unregister()
    ui.unregister()
    bpy.utils.unregister_class(inputWalletAdress)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

