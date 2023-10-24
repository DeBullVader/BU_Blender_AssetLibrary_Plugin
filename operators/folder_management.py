from ..utils import addon_info
from .network import google_service
from ..utils.exceptions import FolderManagementException


def create_folder_on_server(service, folder_name, folder_id):
    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [folder_id]
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return folder

def find_author_folder():
    # Function to find the author folder
    addon_prefs = addon_info.get_addon_name().preferences
    upload_parent_folder = addon_prefs.upload_parent_folder_id
    author = addon_info.get_author()
    service = google_service()
    try:
        if service is not None:
            query = (f"name='{author}' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{upload_parent_folder}' in parents")
            response = service.files().list(q=query,spaces='drive',fields='files(id,name,parents)').execute()
            # There should only be one folder so we get the first one
            if 'files' in response and len(response['files']) > 0:
                print( f'Author folder with name {author} found!')
                author_folder_id = response['files'][0].get('id')
                print(response['files'][0].get('parents'))
                ph_folder_id = find_or_create_placeholder(service,author_folder_id)
                new_author = False
                return (author_folder_id,ph_folder_id,new_author)
            else:
                # Handle the case where no folders were found in the response
                folder_name = addon_info.get_author()
                print( f'Author folder with name {folder_name} not found!, creating one')
                author_folder = create_folder_on_server(service, folder_name, upload_parent_folder)
                author_folder_id = author_folder.get('id')
                ph_folder = create_folder_on_server(service, 'Placeholders', author_folder_id)
                ph_folder_id = ph_folder.get('id')
                new_author = True
                return (author_folder_id,ph_folder_id,new_author)
    except FolderManagementException as e:
        print(f'find_author_folder Error: {e}')
            


def trash_duplicate_folder(service,files):
    # Trash duplicate folders. This is not used curretly. See Trello needs to be refactored to unique folder ids
    print(f'this is author folder {files} ')
    if len(files)>0:
        for idx,file in enumerate(files):
            if idx !=0:
                print(f'file: {file}')
                file_id = file.get('id')
                body = {'trashed': True}
                service.files().update(fileId=file_id, body=body).execute()
                service.files().emptyTrash().execute()   

def find_or_create_placeholder(service, author_folder_id):
    query = (f"name='Placeholders' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{author_folder_id}' in parents")
    response = service.files().list(q=query,spaces='drive',fields='files(id,name)').execute()
    if 'files' in response and len(response['files']) > 0:
        ph_folder_id = response['files'][0].get('id')
        return ph_folder_id
    else:
        # Handle the case where no Placeholders folders were found in the response
        folder_name = 'Placeholders'
        folder = create_folder_on_server(service, folder_name, author_folder_id)
        ph_folder_id = folder.get('id')
        return ph_folder_id

def check_for_author_folder():
    try:
        addon_prefs = addon_info.get_addon_name().preferences
        upload_parent_folder = addon_prefs.upload_parent_folder_id
        service = google_service()
        author = addon_info.get_author()
        
        folder_id = find_author_folder(service, author, upload_parent_folder)
        if folder_id is not None:
            print( f'Author folder with name {author} found')
        else:
            folder_id = create_folder_on_server(service, author, upload_parent_folder)
            print( f'Author folder with name {author} created')
        
        ph_folder_id = find_or_create_placeholder(service, folder_id)

        return folder_id, ph_folder_id

    except Exception as e:
        print(f'check_for_author_folder Error: {e}')