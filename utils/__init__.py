import bpy
import os
from importlib import reload
from . import config
from . import addon_info
from . import exceptions
from . import addon_logger
from . import drag_drop_handler
def try_import_admin_tool():
   try:
      from . import admin_tool
      return admin_tool
   except Exception as e:
      return None
   
admin_tool=try_import_admin_tool()
if bpy in locals():
   if "admin_tool" in locals():
      print('admin tool found')
      admin_tool = reload(admin_tool)
   else:
      try:
         from . import admin_tool
      except:
         print('admin tool not found')
         pass

def register():
   addon_info.register()
   exceptions.register()
   drag_drop_handler.register()
   if admin_tool:
      admin_tool.register()
   else:
      addon_prefs = addon_info.get_addon_prefs()
      addon_prefs.debug_mode = False
      addon_prefs.get_dev_updates = False

               


def unregister():
   drag_drop_handler.unregister()
   addon_logger.unregister()
   exceptions.unregister()
   addon_info.unregister()
   if admin_tool is not None:
      admin_tool.unregister()
   



