
import os
import setup_auth
import auth_utils
from googleapiclient.discovery import build

def inspect_drive():
    creds = auth_utils.get_creds()
    if not creds:
        print("No credentials found. running setup...")
        setup_auth.setup()
        creds = auth_utils.get_creds()

    service = build('drive', 'v3', credentials=creds)
    
    FOLDER_NAME = "data app NPK"
    
    print(f"Searching for folder: {FOLDER_NAME}")
    results = service.files().list(
        q=f"name = '{FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    
    folders = results.get('files', [])
    if not folders:
        print("Folder not found.")
        return

    folder_id = folders[0]['id']
    print(f"Found folder ID: {folder_id}")
    
    # Recursive helper
    def list_folder(f_id, indent=""):
        results = service.files().list(
            q=f"'{f_id}' in parents and trashed = false",
            fields="files(id, name, mimeType)"
        ).execute()
        files = results.get('files', [])
        for f in files:
            print(f"{indent} - {f['name']} ({f['mimeType']}) ID: {f['id']}")
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                list_folder(f['id'], indent + "   ")

    list_folder(folder_id)

if __name__ == "__main__":
    inspect_drive()
