import os
import requests
import json
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from . import file_managment
from ..utils import addon_info,exceptions


def google_service():
    try:
        scope = ['https://www.googleapis.com/auth/drive']
        print('google service called')
        key_file = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"
        credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scopes=scope)
        # Build the service object.
        service = build('drive', 'v3', credentials=credentials)
        print('credentials ', credentials)
        print('service ',service)
        return service
    except Exception as e:
        print('error in google_service',e)
        raise exceptions.GoogleServiceException('error in google_service',e)



def get_asset_list():
    
    all_files =[]
    pageSize = 1000
    try:
        authService = google_service()
        # Call the Drive v3 API
        addon_prefs = addon_info.get_addon_name().preferences
        folder_id = addon_prefs.download_folder_id_placeholders
        query = f"('{folder_id}' in parents) and (trashed = false)"
        request = authService.files().list(
            q=query, pageSize= pageSize, fields="nextPageToken, files(id,name)")
            
        while request is not None:
            response = request.execute()
            print('Request complete, processing results...')
            if 'files' in response:
                print('files in response' ,response)
                all_files.extend(response['files'])
                if len(response['files']) < pageSize:
                    break   
            request = authService.files().list_next(request, response)
        print('Fetching complete .. ')
        return all_files

    except HttpError as error:
        print(f'An HTTP error occurred in get_asset_list: {error}')
        raise file_managment.TaskSpecificException("Failed to fetch due to HTTP Error") from error
    
def get_assets_ids_by_name(selected_assets):
    all_files =[]
    pageSize = 1000
    try:
        authService = google_service()
        # Call the Drive v3 API
        addon_prefs = addon_info.get_addon_name().preferences
        folder_id = addon_prefs.download_folder_id
        names = " or ".join([f"name='{asset.name.removeprefix('PH_')}.zip'" for asset in selected_assets])
        
        # print('this is the name',names)
        query = f"({names}) and ('{folder_id}' in parents) and (trashed = false) and (mimeType != 'application/vnd.google-apps.folder')"
        request = authService.files().list(
            q=query, pageSize= pageSize, fields="nextPageToken, files(id,name)")
            
        while request is not None:
            response = request.execute()
            print('Request complete, processing results...')
            if 'files' in response:
                all_files.extend(response['files'])
                if len(response['files']) < pageSize:
                    break   
            request = authService.files().list_next(request, response)
        print('Fetching complete .. ')
        # print(all_files)
        return all_files
    except HttpError as error:
        print(f'An HTTP error occurred in get_asset_list: {error}')
        raise file_managment.TaskSpecificException("Failed to fetch due to HTTP Error") from error
    


def get_premium_assets_ids_by_name(selectedAssets):
    try:
        addon_prefs = addon_info.get_addon_name().preferences
        if addon_prefs.web3_gumroad_switch == 'premium_gumroad_license':
            userId = addon_prefs.gumroad_premium_licensekey
            licenseType = 'gumroad'
        else:
            userId = addon_prefs.userID
            licenseType = 'web3'
        uuid = addon_prefs.premium_licensekey
        names = [{"name": asset.name.removeprefix('PH_') + '.zip'} for asset in selectedAssets]
        url = 'https://bdzu1thiy3.execute-api.us-east-1.amazonaws.com/dev/BUK_PremiumFileManager'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            'userId': userId,
            'uuid': uuid,
            'licenseType': licenseType,
            'selectedAssets': names
        })

        response = requests.post(url, headers=headers, data=payload)
        response_json = json.loads(response.text)
        statusCode = response_json.get('statusCode', None)
        if statusCode == 200:
            print("Successfully recieved file data from server")
            data = json.loads(response.text)['body']
            return json.loads(data)
        elif statusCode == 401:
            print("User License was not valid!")
            data = json.loads(response.text)['body']
            raise exceptions.LicenseException("StatusCode 401: User License was not valid!")
        elif statusCode == 500:
            print(f"Internal server error at getting server file ids. Please try again or contact support")
            raise exceptions.LicenseException("StatusCode 500: Internal server error at getting server file ids. Please try again or contact support")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise exceptions.LicenseException(f"An error occurred: {e}")


def get_catfile_from_server():
    catfile = 'blender_assets.cats.zip'
    files  = []
    page_token = None
    try:
        while True:
            authService = google_service()
            addon_prefs = addon_info.get_addon_name().preferences
            query = (f"name='{catfile}' and trashed=false and '{addon_prefs.download_folder_id}' in parents")
            response = authService.files().list(q=query,spaces='drive',fields='nextPageToken,''files(id,name)',pageToken=page_token).execute()
            files.extend(response.get('files', []))
            file = response['files'][0]
            
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return file
        
        
    except HttpError as error:
        print(f'An error occurred: {error}')


