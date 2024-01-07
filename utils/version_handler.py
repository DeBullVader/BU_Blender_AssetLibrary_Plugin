import bpy
def latest_version(context):
    if bpy.app.version >= (4,0,0):
        return True
    return False


def get_asset_library_reference(context):
    if latest_version(context):
        return context.space_data.params.asset_library_reference
    else:
        return context.space_data.params.asset_library_ref

def set_asset_library_reference(context,lib_name):
    if latest_version(context):
        context.space_data.params.asset_library_reference = lib_name
    else:
        context.space_data.params.asset_library_ref = lib_name
    