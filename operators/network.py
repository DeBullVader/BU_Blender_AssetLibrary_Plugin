import bpy
import os
import requests
import json
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from . import file_managment
from ..utils import addon_info,exceptions
from ..utils import progress
from ..utils.addon_logger import addon_logger
from .. import icons

def google_service():
    try:
        addon_prefs = addon_info.get_addon_prefs()
        if not is_token_valid(addon_prefs):
            get_acces_token_from_lambda(addon_prefs)   
        credentials = Credentials(token=addon_prefs.accessToken)
        service = build('drive', 'v3', credentials=credentials)
        addon_logger.info('Service created successfully')
        return service
    except HttpError as e:
        if e.resp.status in [401, 403]:  # Token expired or invalid
            print('Token expired. Refreshing token and retrying...')
            addon_logger.info('Token expired. Refreshing token and retrying...')
            get_acces_token_from_lambda(addon_prefs)  # Refresh the token
            credentials = Credentials(token=addon_prefs.accessToken)  # Update credentials
            service = build('drive', 'v3', credentials=credentials)  # Rebuild the service
            return service
        else:
            raise  # Re-raise the exception if it's not a token expiry issue
    except Exception as e:
        print('error creating service',e)
        addon_logger.error(f'error creating service: {e}')
        raise exceptions.GoogleServiceException(f'error creating service: {e}')
    
def is_token_valid(addon_prefs):
    token_timestamp = float(addon_prefs.accessToken_timestamp)
    token_age = time.time() - token_timestamp
    return token_age < 3600  # 3600 seconds = 1 hour

def get_acces_token_from_lambda(addon_prefs):
    try:
        addon_logger.info("Getting access token from server")
        url = 'https://bdzu1thiy3.execute-api.us-east-1.amazonaws.com/dev/BUK_PremiumFileManager'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            'requestType': 'Free',
        })

        response = requests.post(url, headers=headers, data=payload)
        response_json = json.loads(response.text)
        statusCode = response_json.get('statusCode', None)
        addon_logger.info(f"statusCode: {statusCode}")
        if statusCode == 200:
            print("Successfully recieved access token from server")
            addon_logger.info("Successfully recieved access token from server")
            data = json.loads(response.text)['body']
            
            jsondata = json.loads(data)
            new_token = jsondata['accessToken']
            addon_prefs.accessToken = new_token
            addon_prefs.accessToken_timestamp = float(time.time())
            return new_token
        elif statusCode == 400:
            print('Invalid request type!' )
            addon_logger.error("Invalid request type!")
            raise exceptions.GoogleServiceException("StatusCode 400: Invalid request type!")
        elif statusCode == 500:
            addon_logger.error("Internal server error at getting acces token from server. Please try again or contact support")
            print(f"Internal server error at getting acces token from server. Please try again or contact support")
            raise exceptions.GoogleServiceException("StatusCode 500: Internal server error at getting acces token from server. Please try again or contact support")

    except Exception as e:
        addon_logger.error(f"An error occurred fetching access token from lambda: {e}")
        print(f"An error occurred fetching access token from lambda: {e}")
        raise exceptions.LicenseException(f"An error occurred: {e}")


def get_asset_list(folder_id):
    
    all_files =[]
    pageSize = 1000
    try:
        addon_logger.info("Fetching assets list")
        authService = google_service()
        # Call the Drive v3 API
        query = f"('{folder_id}' in parents) and (trashed = false) and (mimeType='application/zip')"
        request = authService.files().list(
            q=query, pageSize= pageSize, fields="nextPageToken, files(id,name,size,modifiedTime)")
            
        while request is not None:
            response = request.execute()
            if 'files' in response:
                all_files.extend(response['files'])
                if len(response['files']) < pageSize:
                    break   
            request = authService.files().list_next(request, response) 
        print('Fetching complete .. ')
        addon_logger.info('Fetching complete .. ')
        return all_files

    except HttpError as error:
        print(f'An HTTP error occurred in get_asset_list: {error}')
        addon_logger.error(f'An HTTP error occurred in get_asset_list: {error}')
        raise file_managment.TaskSpecificException(f"Failed to fetch due to HTTP Error {error}") from error
    
def get_assets_ids_by_name(selected_assets):
    all_files =[]
    pageSize = 1000
    try:
        addon_logger.info("Fetching assets list by name")
        authService = google_service()
        # Call the Drive v3 API
        addon_prefs = addon_info.get_addon_name().preferences
        folder_id = addon_prefs.download_folder_id
        names = " or ".join([f"name='{asset.name.removeprefix('PH_')}.zip'" for asset in selected_assets])
        query = f"({names}) and ('{folder_id}' in parents) and (trashed = false) and (mimeType != 'application/vnd.google-apps.folder')"
        request = authService.files().list(
            q=query, pageSize= pageSize, fields="nextPageToken, files(id,name,size)")
            
        while request is not None:
            response = request.execute()
            if 'files' in response:
                all_files.extend(response['files'])
                # if len(response['files']) < pageSize:
                #     break   
            request = authService.files().list_next(request, response)
        print('Fetching by asset name complete .. ')
        addon_logger.info('Fetching by asset name complete .. ')
        return all_files
    except Exception as e:
        error =f"An error occurred in get_assets_ids_by_name: {str(e)}"
        addon_logger.error(error)
        print(error)
        raise error
    


def get_premium_assets_ids_by_name(selectedAssets):
    try:
        addon_logger.info('Fetching premium assets list by name')
        addon_prefs = addon_info.get_addon_name().preferences
        if addon_prefs.web3_gumroad_switch == 'premium_gumroad_license':
            userId = addon_prefs.gumroad_premium_licensekey
            licenseType = 'gumroad'
        else:
            userId = addon_prefs.userID
            licenseType = 'web3'
        uuid = addon_prefs.premium_licensekey
        names = [{"name": asset.name.removeprefix('PH_') + '.zip' if not asset.name.endswith('.zip') else asset.name.removeprefix('PH_')} for asset in selectedAssets]
        url = 'https://bdzu1thiy3.execute-api.us-east-1.amazonaws.com/dev/BUK_PremiumFileManager'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            'requestType': 'Premium',
            'userId': userId,
            'uuid': uuid,
            'licenseType': licenseType,
            'selectedAssets': names,
            'debugMode': addon_prefs.debug_mode
        })

        response = requests.post(url, headers=headers, data=payload)
        response_json = json.loads(response.text)

        statusCode = response_json.get('statusCode', None)
        addon_logger.info('Response status code:', statusCode)
        if statusCode == 200:
            addon_logger.info("Successfully recieved file data from server")
            data = json.loads(response.text)['body']
            return json.loads(data)
        
        elif statusCode == 401:
            error ="StatusCode 401: User License was not valid!"
            addon_logger.error(error)
            data = json.loads(response.text)['body']
            print(error)
            raise error
        elif statusCode == 500:
            error ="StatusCode 500: Internal server error at getting server file ids. Please try again or contact support"
            addon_logger.error(error)
            print(error)
            raise error

    except Exception as e:
        error =f"Error Fetching premium assets by name: {e}"
        addon_logger.error(error)
        raise error


def get_catfile_id_from_server():
    catfile = 'blender_assets.cats.zip'
    files =[]
    try:
        while True:
            print('Fetching catalog file id from server..')
            addon_logger.info('Fetching catalog file id from server..')
            authService = google_service()
            addon_prefs = addon_info.get_addon_name().preferences
            query = (f"name='{catfile}' and trashed=false and '{addon_prefs.download_catalog_folder_id}' in parents")
            response = authService.files().list(q=query,spaces='drive',fields='files(id,name,size,createdTime, modifiedTime)').execute()
            files = response['files']
            if len(files)>0:
                file = response['files'][0]
                return file
            else:
                print('File not found.')
                addon_logger.info('File not found.')
                raise HttpError('File not found.')
    except HttpError as error:
        error_message = f'An http error occurred in get_catfile_id_from_server: {error}'
        addon_logger.error(error_message)
        print(error_message)
        raise error_message

def get_excisting_assets_from_author(folder_ids):
    try:
        addon_logger.info('Fetching existing assets from author folder')
        Allfiles = []
        pageSize = 1000
        authService = google_service()
        author_folder_id,ph_folder_id = folder_ids
        info_message=f'Author folder id: {author_folder_id} Placeholder folder id: {ph_folder_id}'
        addon_logger.info(info_message)
        query = f"('{author_folder_id}' in parents or '{ph_folder_id}' in parents) and (mimeType='application/zip') and (trashed=false)"
        request = authService.files().list(q=query, pageSize=pageSize, fields="nextPageToken, files(id,name,size)")
    
        while request is not None:
            response = request.execute()
            if 'files' in response:
                Allfiles.extend(response['files'])
                if len(response['files']) < pageSize:
                    break  
            request = authService.files().list_next(request, response)
        return Allfiles
    except HttpError as error:
        error_message = f'An http error occurred in get_excisting_assets_from_author: {error}'
        print(error_message)
        addon_logger.error(error_message)
        raise error_message



def create_file(self,service,media,file_metadata):
    try:
        service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        addon_logger.info(f"File : {file_metadata['name']}was created and uploaded.")
        return file_metadata['name']
    except HttpError as error:
        print(f"Failed to fetch due to HTTP Error: {error}")
        addon_logger.error(f"Failed to fetch due to HTTP Error: {error}")
        raise error

def update_file(self,service,file_id,media,updated_metadata):
    try:
        service.files().update(fileId=file_id,body=updated_metadata, media_body=media).execute()
        addon_logger.info(f"File : {updated_metadata['name']} uploaded and updated.")
        return updated_metadata['name']
    except HttpError as error:
        error_message = f"Failed to fetch due to HTTP Error: {error}"
        print(error_message)
        addon_logger.error(error_message)
        raise error_message

def trash_duplicate_files(service,file):
    for idx,f in enumerate(file):
            if idx !=0:
                file_id = f['id']
                # body = {'trashed': True}
                # service.files().update(fileId=f_id, body=body).execute()
                # service.files().emptyTrash().execute()
                service.files().delete(fileId=file_id).execute()
                print(f'{f.get("name")} had double files. Removed index larger then 0')

def upload_files(self,context,file_to_upload,folder_id,files,prog,workspace):
    try:
       
        service = google_service()
        root_dir,file_name = os.path.split(file_to_upload)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        updated_metadata={
            'name': file_name,
        }
        addon_logger.info(f'Uploading file {file_name}')
        media = MediaFileUpload(file_to_upload, mimetype='application/zip')
        if len(files)>0:
            file =[file for file in files if file['name'] == file_name]
            if len(file)>0:
                trash_duplicate_files(service,file)
                print('updating existing file ',file_name)
                addon_logger.info(f'Updating existing file {file_name}')
                file_id = file[0].get('id')
                self.upload_progress_dict[file_name]='Status:Update Uploaded!'
                filename = update_file(self,service,file_id,media,updated_metadata)  
            else:
                print('creating new file ',file_name)
                addon_logger.info(f'Creating new file {file_name}')
                self.upload_progress_dict[file_name]='Status:New Uploaded!'
                filename = create_file(self,service,media,file_metadata)
        else:
            print('creating new file ',file_name)
            addon_logger.info(f'Creating new file {file_name}')
            self.upload_progress_dict[file_name]='Status:New Uploaded!'
            filename = create_file(self,service,media,file_metadata)
            
        prog_text =f'Uploaded {filename}'
        self.prog+=1
        progress.update(context, self.prog, prog_text,workspace)
        return filename
    except Exception as error:
        error_message = f"Error in upload_files: {error}"
        print(error_message)
        addon_logger.error(error_message)
        raise error_message
