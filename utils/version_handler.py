import bpy
def latest_version(context):
    if bpy.app.version >= (4,0,0):
        return True
    return False


def get_asset_library_reference(context):
    try:   
        if latest_version(context):
            return context.space_data.params.asset_library_reference
        else:
            # print(context.space_data.__dir__())
            return context.space_data.params.asset_library_ref
    except:
        try:
            current_library_name = get_asset_library_reference_override(context)
            return current_library_name
        except Exception as e:
            print(f'Error in getting asset library ref: {e}')
            raise Exception(e)

def set_asset_library_reference(context,lib_name):
    try:
        if latest_version(context):
            context.space_data.params.asset_library_reference = lib_name
        else:
            context.space_data.params.asset_library_ref = lib_name
    except Exception as e:
        print(f'Error in setting asset library ref: {e}')
        raise Exception(e)

def get_asset_library_reference_override(context):
    for area in context.screen.areas:
        if area.ui_type == 'ASSETS':
            with context.temp_override(area=area):
                current_library_name = get_asset_library_reference(context)
                if current_library_name:
                    return current_library_name
                else:
                    raise Exception('something went wrong getting asset library ref')
    


def get_selected_assets(context):
    try:
        if latest_version(context):
            return context.selected_assets
        else:
            return context.selected_asset_files
    except Exception as e:
        print(f'Error in get_selected_assets: {e}')
        raise Exception(e)

        
    