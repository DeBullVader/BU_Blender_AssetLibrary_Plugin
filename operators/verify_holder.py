import bpy
import moralis
from moralis import evm_api
from bpy.types import Operator
from ..ui import lib_preferences

api_key = "ER1lNNyhbyOogmIGbZAgjK35jxn6wp7rbmvG5A4XYWBuRLl02FGJN5AcOaJMu2XQ"

#Extract nested values from a JSON tree.


def json_extract(obj, key):
   # """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
       # """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values

def wallet_address(adres):
  def verify(address):
    params = {
      "chain": "bsc",
      #"address": "0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2"
      "address": address
    }
    result = evm_api.nft.get_wallet_nft_collections(
      api_key=api_key,
      params=params,
    )
    currentowners = json_extract(result, 'token_address')
    for puppets in currentowners:
      if puppets == "0xda931d11239b4b5f1e149a1c4b2449aaa98f461a":
        check = any("0xda931d11239b4b5f1e149a1c4b2449aaa98f461a" == element for element in currentowners)
        return check
  checked = verify(adres)
  return checked


# wallet_address("0x15a5E70166a7cbea9Eb597BB1048515d041AbAB2")




class BU_OT_Verify(Operator):
    """Verify that your wallet address has a piffle puppet"""
    bl_idname = "bu.verify"
    bl_label = "Verify wallet"

    bpy.types.AddonPreferences.walletstatus = bpy.props.StringProperty()
    bpy.types.AddonPreferences.walletbutton = bpy.props.StringProperty()
    bpy.types.AddonPreferences.walletbutton = "Verify wallet"
    bpy.types.AddonPreferences.walletstatus = 'Please verify that you are a Piffle Puppet Holder'
    
    def execute(self, context):
      if bpy.context.preferences.active_section == "ADDONS": 
        address = context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.bsc_wallet_address
        if address != '':
            if wallet_address(address) == True:
                print( wallet_address(address))
                
                bpy.types.AddonPreferences.walletbutton = "Succes!"
                bpy.types.AddonPreferences.walletstatus = 'You have succesfully verified that you are a Piffle Puppet Holder'
            else:
                print( wallet_address(address))
                bpy.types.AddonPreferences.walletbutton = "Verify wallet"
                bpy.types.AddonPreferences.walletstatus = 'This wallet is not a Piffle Puppet Holder! Get one at mint.bakeduniverse.com'
        else:
            bpy.types.AddonPreferences.walletbutton = "Verify wallet"
            bpy.types.AddonPreferences.walletstatus = 'Please verify that you are a Piffle Puppet Holder'
        return {'FINISHED'}

classes = (
  BU_OT_Verify,
  )   
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print('VerifyHolders REGISTERED')    

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)