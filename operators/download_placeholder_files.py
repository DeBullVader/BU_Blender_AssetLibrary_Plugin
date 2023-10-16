
# from __future__ import print_function
import bpy
import logging
import io
import os
import shutil
import threading






from concurrent.futures import ThreadPoolExecutor
from time import sleep

from .. import progress
from ..utils import addon_info
from ..ui import statusbar
# import datetime

# import shutil

# from bpy.app.handlers import persistent
# from dateutil import parser
# from pathlib import Path

# from time import sleep
# from bpy.types import Operator

# from ..utils.addon_info import get_core_asset_library,get_upload_asset_library,get_addon_name
# from ..utils import catfile_handler

import os





log = logging.getLogger(__name__)










def threadedDownload(self,context,assets,target_lib):

    executor = ThreadPoolExecutor(max_workers=20)
    threads = []
    count = 0

    assets_to_download = compare_with_local_assets(self,context)
    # global assets_to_download
    assets = assets_to_download.items()

    for asset_id,asset_name in assets:
        # blend_file = get_unpacked_names(asset_name)
        t=executor.submit(DownloadFile, asset_id,asset_name,target_lib)
        threads.append(t)
        count +=1
    progress.init(context, count, word = "Downloading")
    finished_threads =[]
    while True:
        for thread in threads:
            if thread._state == "FINISHED":
                if thread not in finished_threads:
                    finished_threads.append(thread)
                    self.prog += 1
                    result = thread.result()
                    if result is not None:
                        self.report({"INFO"}, "we got result")
                        print(f'this is result {result}')
                        if context.window_manager.bu_props.new_assets > 0:
                            context.window_manager.bu_props.new_assets -=1
                        if context.window_manager.bu_props.updated_assets >0:
                            context.window_manager.bu_props.updated_assets -=1
                        self.num_downloaded += 1
    
                        prog_word = result + ' has been Updated has been Downloaded'
                        self.prog_text = f"{prog_word} "
                        context.window_manager.bu_props.progress_downloaded_text = f"{prog_word} "
                                
        if all(t._state == 'FINISHED' for t in threads):
            self.report({"INFO"}, "All Threads finished")
            print('all treads finished')
            context.window_manager.bu_props.new_assets = 0
            context.window_manager.bu_props.updated_asset = 0
            break    
        sleep(0.5)
 
class Download_Placeholder_Assets(bpy.types.Operator):
    """DOWNLOAD ALL PLACEHOLDER ASSETS"""
    bl_idname = "bu.download_placeholder_assets"
    bl_label = "Download placeholder assets"
    bl_description = "Downloads the library preview files"
    bl_options = {"REGISTER"}

    prog = 0
    prog_text = None
    
    num_downloaded = 0
    _timer = None
    th = None
    prog_downloaded_text = None

    @classmethod
    def poll(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
        dir_path = addon_prefs.lib_path
        if dir_path == '':
            self.poll_message_set('Please add a file path in the addon preferences')
            return False
        assetlibs = bpy.context.preferences.filepaths.asset_libraries
        if "BU_AssetLibrary_Core" not in assetlibs :
            return False
        else:
            return True, context.window_manager.bu_props.progress_total == 0
    
    def modal(self, context, event):
        if event.type == "TIMER":
            progress.update(context, self.prog, self.prog_text)
            try:
                bpy.ops.asset.library_refresh()
            except RuntimeError:
                # Context has changed
                pass

            if not self.th.is_alive():
                log.debug("FINISHED ALL THREADS")
                progress.end(context)
                self.th.join()
                prog_word = "Downloaded"
                self.report(
                    {"INFO"}, f"{prog_word}"
                )
                self.report(
                    {"INFO"}, f"{prog_word} {self.num_downloaded} asset{'s' if self.num_downloaded != 1 else ''}"
                )
                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        ShowDownloadStatus("Downloading preview asset",'Status')
        get_catfile_from_server()
        
        target_lib = addon_info.get_target_lib()
        assets_to_download = compare_with_local_assets(self,context)
        assets = assets_to_download.items()

        self.th = threading.Thread(target=threadedDownload, args=(self,context,assets,target_lib))

        self.th.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)        
        return {"RUNNING_MODAL"}
    
def ShowDownloadStatus(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
     



classes =(
    Download_Placeholder_Assets,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
