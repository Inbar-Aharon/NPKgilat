
import os
from googleapiclient.discovery import build
import auth_utils

# Configuration
DRIVE_FOLDER_NAME = "data app NPK"

def debug_icon_list():
    creds = auth_utils.get_creds()
    if not creds:
        print("No creds")
        return

    service = build('drive', 'v3', credentials=creds)
    
    # 1. Find root
    results = service.files().list(q=f"name = '{DRIVE_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder'", fields="files(id)").execute()
    if not results.get('files'): return
    root_id = results.get('files')[0]['id']

    # 2. Find GrowerNutritionMonitor
    results = service.files().list(q=f"'{root_id}' in parents and name = 'GrowerNutritionMonitor' and mimeType = 'application/vnd.google-apps.folder'", fields="files(id)").execute()
    if not results.get('files'): return
    gnm_id = results.get('files')[0]['id']

    # 3. Find www
    results = service.files().list(q=f"'{gnm_id}' in parents and name = 'www' and mimeType = 'application/vnd.google-apps.folder'", fields="files(id)").execute()
    if not results.get('files'): return
    www_id = results.get('files')[0]['id']

    # 4. List images
    results = service.files().list(q=f"'{www_id}' in parents", fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    
    print(f"Found {len(files)} files in 'www':")
    for f in files:
        print(f"  - {f['name']} ({f['mimeType']})")

if __name__ == "__main__":
    debug_icon_list()
