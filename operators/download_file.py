import os
import io
import shutil

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from .sync_ui_progress_handler import updateFileProgress
from ..utils import addon_info,progress
from . import network
from ..utils.addon_logger import addon_logger



    

def DownloadFile(self, context, FileId, fileName, file_size,isPlaceholder,target_lib,workspace,downloaded_sizes ):

    try:
        target_lib_path = target_lib.path
        downloaded_sizes[FileId]=0
        
        NUM_RETRIES = 3
        authService = network.google_service()
        request = authService.files().get_media(fileId=FileId)
        file = io.BytesIO()
        chunk_size = addon_info.calculate_dynamic_chunk_size(int(file_size))
        
        downloader = MediaIoBaseDownload(file, request,chunksize=chunk_size)
        
        done = False
        while done is False:
            try:
                status, done = downloader.next_chunk(num_retries=NUM_RETRIES)
                
                if status:
                    current_progress = int(status.progress()*100)
                    downloaded_size_for_file = current_progress * int(file_size)/100
                    downloaded_sizes[FileId] = downloaded_size_for_file
                    total_downloaded = sum(downloaded_sizes.values())
                    size = f"size: {round(downloader._total_size/1024)}kb" if round(downloader._total_size/1024)<1000 else f"size: {round(downloader._total_size/1024/1024,2)}mb "
                    # print(current_progress)
                    asset_name = fileName.removesuffix('.zip')
                    updateFileProgress(context,asset_name,current_progress,size)
                    progress.update(context, total_downloaded, "Syncing asset...", workspace)
            except HttpError as error:
                    raise Exception(f'HttpError in download_chunks: {error}')

        try:
            file.seek(0)
            with open(os.path.join(target_lib_path, fileName), 'wb') as f:
                f.write(file.read())
                f.close()

                if ".zip" in fileName:
                    fname = target_lib_path + os.sep + fileName
                    shutil.unpack_archive(fname, target_lib_path, 'zip')
                    if not isPlaceholder:
                        baseName = fileName.removesuffix('.zip')
                        ph_file = f'{target_lib_path}{os.sep}{baseName}{os.sep}PH_{baseName}.blend'
                        if os.path.exists(ph_file):
                            if not self.is_premium:
                                os.remove(ph_file)

                    os.remove(fname)
                    return fileName 
        except Exception as error:
            raise Exception(f'Error writing and unpacking: {error}')        
    except Exception as error:
        raise Exception(f'DownloadFile Error: {error}')