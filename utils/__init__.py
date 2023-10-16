import bpy
from . import config
from . import admin_tools
def import_admin_tools():
   try:
      from . import admin_tools
      return admin_tools
   except:
      print('Could not register admin_tools')
      return None
admin_tools = import_admin_tools()
def register():
   # if admin_tools is not None:
   admin_tools.register()
      
   
   # bpy.utils.register_class(space_filebrowser)

def unregister():
   # if admin_tools is not None:
   admin_tools.unregister()
      
   
   # bpy.utils.unregister_class(space_filebrowser)

