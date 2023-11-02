import os
import requests
import json
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from . import file_managment
from ..utils import addon_info,exceptions
from ..utils import progress

def google_service():
    try:
        scope = ['https://www.googleapis.com/auth/drive']
        # print('google service called')
        key_file = os.path.dirname(os.path.abspath(__file__)) + os.sep +"bakeduniverseassetlibrary-5b6b936e6c00.json"
        # print(key_file)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scopes=scope)
        # Build the service object.
        service = build('drive', 'v3', credentials=credentials)
        # print('credentials ', credentials)
        # print('service ',service)
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
        raise file_managment.TaskSpecificException(f"Failed to fetch due to HTTP Error {error}") from error
    
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
                # if len(response['files']) < pageSize:
                #     break   
            request = authService.files().list_next(request, response)
        print('Fetching by asset name complete .. ')
        print('all_files', all_files)
        print('request', request)
        return all_files
    # except HttpError as error:
    #     print(f'An HTTP error occurred in get_asset_list: {error}')
    #     raise file_managment.TaskSpecificException("Failed to fetch due to HTTP Error") from error
    except Exception as e:
        print(f"An error occurred in get_assets_ids_by_name: {str(e)}")
        raise e
    


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
            'selectedAssets': names,
            'debugMode': addon_prefs.debug_mode
        })

        response = requests.post(url, headers=headers, data=payload)
        response_json = json.loads(response.text)
        statusCode = response_json.get('statusCode', None)
        if statusCode == 200:
            print("Successfully recieved file data from server")
            data = json.loads(response.text)['body']
            print( json.loads(data))
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


def get_catfile_id_from_server():
    catfile = 'blender_assets.cats.zip'
    try:
        while True:
            authService = google_service()
            addon_prefs = addon_info.get_addon_name().preferences
            query = (f"name='{catfile}' and trashed=false and '{addon_prefs.download_catalog_folder_id}' in parents")
            response = authService.files().list(q=query,spaces='drive',fields='files(id,name)').execute()
            print('response: ',response)
            print('response files: ',response['files'])
            if response['files']>0:
                file = response['files'][0]
                if file:
                    return file
                else:  
                    print('File not found.') 
            print('File not found.')    
    except HttpError as error:
        print(f'An error occurred: {error}')

def get_excisting_assets_from_author(folder_ids):
    try:
        Allfiles = []
        pageSize = 1000
        authService = google_service()

        author_folder_id,ph_folder_id = folder_ids
        print("author_folder_id: ", author_folder_id)
        print("ph_folder_id: ",ph_folder_id)
        query = f"('{author_folder_id}' in parents or '{ph_folder_id}' in parents) and (mimeType='application/zip') and (trashed=false)"
        request = authService.files().list(q=query, pageSize=pageSize, fields="nextPageToken, files(id,name)")
        print(request)
        while request is not None:
            response = request.execute()
            if 'files' in response:
                Allfiles.extend(response['files'])
                if len(response['files']) < pageSize:
                    break  
            request = authService.files().list_next(request, response)
        return Allfiles
    except HttpError as error:
        print(f'An http error occurred in get_excisting_assets_from_author: {error}')
        raise exceptions.UploadException(f"Failed to fetch due to HTTP Error: {error}") from error



def create_file(self,service,media,file_metadata):
    try:
        service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        print(f"File : {file_metadata['name']}was created and uploaded.")
        return file_metadata['name']
        # self.report({"INFO"},f"File : {file_metadata['name']}was created and uploaded.")
    except HttpError as error:
        raise exceptions.UploadException(f"Failed to fetch due to HTTP Error: {error}") from error

def update_file(self,service,file_id,media,updated_metadata):
    try:
        service.files().update(fileId=file_id,body=updated_metadata, media_body=media).execute()
        print(f"File : {updated_metadata['name']} uploaded and updated.")
        return updated_metadata['name']
    except HttpError as error:
        raise exceptions.UploadException(f"Failed to fetch due to HTTP Error: {error}") from error

def trash_duplicate_files(service,file):
    for idx,f in enumerate(file):
            if idx !=0:
                f_id = f['id']
                body = {'trashed': True}
                service.files().update(fileId=f_id, body=body).execute()
                service.files().emptyTrash().execute()
                print(f'{f.get("name")} had double files. Removed index larger then 0')

def upload_files(self,context,file_to_upload,folder_id,files,prog,workspace):
    try:
        print(f'processing uploads')
        # print('This is files: ',files)
        # print('file_to_upload: ',file_to_upload)
        print('folder_id: ',folder_id)
        service = google_service()
        root_dir,file_name = os.path.split(file_to_upload)
        print('This is file name: ',file_name)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        updated_metadata={
            'name': file_name,
        }
        media = MediaFileUpload(file_to_upload, mimetype='application/zip')
        if len(files)>0:
            file =[file for file in files if file['name'] == file_name]
            print('file: ',file)
            if len(file)>0:
                trash_duplicate_files(service,file)
                print('updating existing file ',file_name)
                file_id = file[0].get('id')
                filename = update_file(self,service,file_id,media,updated_metadata)  
            else:
                print('creating new file ',file_name)
                filename = create_file(self,service,media,file_metadata)
        else:
            print('creating new file ',file_name)
            filename = create_file(self,service,media,file_metadata)
            
        
        prog_text =f'Uploaded {filename}'
        progress.update(context, prog, prog_text,workspace)
        return filename
    except Exception as error_message:
        print('error inside upload_files ',error_message)
        raise exceptions.UploadException(f"Failed to fetch due to HTTP Error: {error_message}")

