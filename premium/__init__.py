import bpy

from . import premium_ui, premium_logic

files = (
    premium_ui,
    premium_logic
)

def register():
    premium_ui.register()
    premium_logic.register()
    # for file in files:
    #     file.register()
     
def unregister():
    premium_ui.unregister()
    premium_logic.unregister()
    # for file in files:
    #     file.unregister()
     

