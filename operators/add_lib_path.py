import bpy
from bpy.types import Operator


class BU_OT_AddLibraryPath(Operator):
    bl_idname = "bu.addlibrary"
    bl_label = "add library to preference filepaths"
   
    def execute(self, context):
        
        dir_path = bpy.context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.lib_path
        lib_name = 'BU_AssetLibrary_Core'
        if dir_path != "":
            bpy.ops.preferences.asset_library_add(directory =dir_path, check_existing = True)
            new_library = bpy.context.preferences.filepaths.asset_libraries[-1]
            new_library.name = lib_name
        bpy.ops.wm.save_userpref()
        # win_active = bpy.context.window
        # win_other = None
        # for win_iter in context.window_manager.windows:
        #     if win_iter != win_active:
        #         win_other = win_iter
        #     break

        # with context.temp_override(window=win_other):
        #     if bpy.context.window.workspace != bpy.data.workspaces['Layout']:
        #         bpy.context.window.workspace = bpy.data.workspaces['Layout']
        #     for area in bpy.data.screens["Layout"].areas:
        #         print(area.type)
        #         if area.type == 'DOPESHEET_EDITOR':

        #             area.ui_type = 'ASSETS'
        #             area.spaces.active.params.asset_library_ref = 'BU_AssetLibrary_Core'
        #         else:
                    # if area.type == 'VIEW_3D':
                    #     area = bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.3)
                        
                        
                        # new_area =  bpy.data.screens['Layout'].areas[0]
                        # new_area.ui_type ='ASSETS'
                        # new_area.spaces.active.params.asset_library_ref = 'BU_AssetLibrary_Core'

            

                    # new_area.spaces.active.params.asset_library_ref = 'LOCAL'
            
            
                        
                        
                    

                        #  bpy.types.fileassetselectparams.asset_library_ref['BU_AssetLibrary_Core']
                         

            # if win_iter.workspace.name != 'Layout':
                # 
                
        # for area in bpy.data.screens["Layout"].areas:
        #     if area.type == 'VIEW 3D':
        #         print(area)
        #         new_area =  bpy.data.screens['Layout'].areas[-1]
        #         
        # bpy.types.fileassetselectparams.asset_library_ref['BU_AssetLibrary_Core']
        return {'FINISHED'} 
