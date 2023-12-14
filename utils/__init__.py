import bpy
from . import config
from . import addon_info
from . import exceptions
from . import addon_logger
def import_admin_tools():
   try:
      from . import admin_tools
      return admin_tools
   except:
      print('Could not register admin_tools')
      return None
   
admin_tools = import_admin_tools()


def register():
   addon_info.register()
   exceptions.register()
   if admin_tools is not None:
      admin_tools.register()


def unregister():
   if admin_tools is not None:
      admin_tools.unregister()
   addon_logger.unregister()
   exceptions.unregister()
   addon_info.unregister()
   



