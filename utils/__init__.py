from . import config
def import_admin_tools():
   try:
      from . import admin_tools
      return admin_tools
   except:
      print('Could not register admin_tools')
      return None
admin_tools = import_admin_tools()
def register():
   admin_tools.register()

def unregister():
   admin_tools.unregister()


