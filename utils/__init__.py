import bpy
import os
from . import config
from . import addon_info
from . import exceptions
from . import addon_logger

def import_admin_tools():
   try:
      from . import admin_tools
      return admin_tools
   except:

      return None
   
admin_tools = import_admin_tools()


def register():
   addon_info.register()
   exceptions.register()
   if admin_tools:
      admin_tools.register()
   else:
      addon_prefs = addon_info.get_addon_prefs()
      addon_prefs.debug_mode = False
      addon_prefs.get_dev_updates = False

               


def unregister():

   addon_logger.unregister()
   exceptions.unregister()
   addon_info.unregister()
   if admin_tools is not None:
      admin_tools.unregister()
   



