import os
import io
import shutil
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import auth_utils
import setup_auth
import concurrent.futures
import dateutil.parser
import datetime

# Configuration
DRIVE_FOLDER_NAME = "data app NPK"
LOCAL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
LOCAL_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

# User provided local path for Drive
USER_DRIVE_PATH = "/Users/inbaraharon/Library/CloudStorage/GoogleDrive-npkgilat@gmail.com/My Drive/WORKFLOWS/or/Inbar/data app NPK"

def ensure_dirs():
    if not os.path.exists(LOCAL_DATA_DIR):
        os.makedirs(LOCAL_DATA_DIR)
    if not os.path.exists(LOCAL_ASSETS_DIR):
        os.makedirs(LOCAL_ASSETS_DIR)

def sync_from_local_drive():
    """Syncs data and icons directly from the local Google Drive folder."""
    print(f"Checking local Drive path: {USER_DRIVE_PATH}")
    if not os.path.exists(USER_DRIVE_PATH):
        print("Local Drive path not found. Falling back to API (if implemented).")
        return False
        
    print("Found local Drive folder! Syncing via file copy...")
    ensure_dirs()
    
    # 1. Sync Data (CSVs)
    # Recursively find CSVs in the local Drive folder
    # We want CSVs from 'GrowerNutritionMonitor' folder mainly? Or root?
    # Previous logic searched recursively from root.
    
    # Let's walk the USER_DRIVE_PATH
    data_count = 0
    for root, dirs, files in os.walk(USER_DRIVE_PATH):
        for file in files:
            if file.endswith('.csv') and not file.startswith('.'):
                src_path = os.path.join(root, file)
                dest_path = os.path.join(LOCAL_DATA_DIR, file)
                
                # Copy if newer or missing
                if should_copy(src_path, dest_path):
                    try:
                        shutil.copy2(src_path, dest_path)
                        print(f"Copied Data: {file}")
                        data_count += 1
                    except Exception as e:
                        print(f"Error copying {file}: {e}")
    
    print(f"Synced {data_count} data files.")

    # 2. Sync Icons from 'GrowerNutritionMonitor/www'
    # We need to find where 'www' is relative to USER_DRIVE_PATH
    # USER_DRIVE_PATH ends in 'data app NPK'
    # The structure is 'data app NPK' -> 'GrowerNutritionMonitor' -> 'www'
    
    www_path = os.path.join(USER_DRIVE_PATH, 'GrowerNutritionMonitor', 'www')
    if os.path.exists(www_path):
        icon_count = 0
        for file in os.listdir(www_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and not file.startswith('.'):
                src_path = os.path.join(www_path, file)
                dest_path = os.path.join(LOCAL_ASSETS_DIR, file)
                
                if should_copy(src_path, dest_path):
                    try:
                        shutil.copy2(src_path, dest_path)
                        print(f"Copied Icon: {file}")
                        icon_count += 1
                    except Exception as e:
                        print(f"Error copying icon {file}: {e}")
        print(f"Synced {icon_count} icons.")
    else:
        print(f"Warning: 'www' folder not found at {www_path}")

    return True

def should_copy(src, dest):
    """Returns True if src is newer or dest is missing."""
    # For local sync, we want to enforce the source as truth, especially if dimensions/content changed but mtime is older on source (e.g. restored file).
    # Also to fix the issue where a previous download created a 'newer' file than the source.
    # To be safe and ensure 'Reload' actually reloads:
    return True
    
    # Original logic was:
    # if not os.path.exists(dest):
    #    return True
    # return os.path.getmtime(src) > os.path.getmtime(dest)

# Wrapper functions for compatibility with app.py calls
# Wrapper functions for compatibility with app.py calls
def sync_icons_only(creds=None):
    """Syncs only icons using API."""
    if not creds:
        creds = auth_utils.get_creds()
    
    if creds:
        try:
            service = build('drive', 'v3', credentials=creds)
            sync_icons_api(service)
            return True
        except Exception as e:
            print(f"Icon Only Sync Failed: {e}")
            return False
    return False

def sync_data(creds=None):
    """Syncs data using API."""
    return sync_data_api(creds)

# --- API SYNC IMPLEMENTATION ---
def sync_icons_api(service):
    """Syncs icons from Drive using API with parallel downloads."""
    print("Syncing icons via API...")
    try:
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

        # 4. List images with modifiedTime
        results = service.files().list(q=f"'{www_id}' in parents and (mimeType contains 'image/')", fields="files(id, name, modifiedTime)").execute()
        files = results.get('files', [])
        
        # Deduplicate icons (Use newest version)
        unique_icons = {}
        for f in files:
            name = f['name']
            if name not in unique_icons:
                unique_icons[name] = f
            else:
                 current_time = unique_icons[name].get('modifiedTime')
                 new_time = f.get('modifiedTime')
                 if current_time and new_time:
                     dt_current = dateutil.parser.isoparse(current_time)
                     dt_new = dateutil.parser.isoparse(new_time)
                     if dt_new > dt_current:
                         unique_icons[name] = f
        
        final_icons = list(unique_icons.values())
        if not os.path.exists(LOCAL_ASSETS_DIR):
            os.makedirs(LOCAL_ASSETS_DIR)

        def download_icon_wrapper(f):
             download_file(service, f['id'], f['name'], dest_folder=LOCAL_ASSETS_DIR, file_meta=f)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(download_icon_wrapper, final_icons)

    except Exception as e:
        print(f"Icon API Sync Failed: {e}")

def sync_data_api(creds=None):
    """Syncs data from Google Drive using API with parallel downloads."""
    print("Starting API Data Sync...")
    ensure_dirs()
    
    if not creds:
        creds = auth_utils.get_creds()
        if not creds:
            print("No credentials found. Please log in.")
            return False

    try:
        service = build('drive', 'v3', credentials=creds)
        
        # 1. Find root folder
        results = service.files().list(
            q=f"name = '{DRIVE_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        items = results.get('files', [])
        
        if not items:
            print(f"Folder '{DRIVE_FOLDER_NAME}' not found.")
            return False
        
        root_folder_id = items[0]['id']
        
        # 2. Collect files to download
        files_to_download = []

        def process_folder(folder_id):
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            files = results.get('files', [])
            
            for f in files:
                if f['mimeType'] == 'application/vnd.google-apps.folder':
                    process_folder(f['id'])
                elif f['name'] == 'users.csv' or (f['name'].endswith('.csv') and 'users' not in f['name']):
                     files_to_download.append(f)

        process_folder(root_folder_id)
        
        # Deduplicate
        unique_files = {}
        for f in files_to_download:
            name = f['name']
            if name not in unique_files:
                unique_files[name] = f
            else:
                current_time = unique_files[name].get('modifiedTime')
                new_time = f.get('modifiedTime')
                if current_time and new_time:
                     dt_current = dateutil.parser.isoparse(current_time)
                     dt_new = dateutil.parser.isoparse(new_time)
                     if dt_new > dt_current:
                         unique_files[name] = f
        
        final_files_list = list(unique_files.values())
        print(f"Found {len(final_files_list)} unique API files to sync.")

        def download_item(f):
             download_file(service, f['id'], f['name'], file_meta=f) # dest defaults to LOCAL_DATA_DIR

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(download_item, final_files_list)
        
        sync_icons_api(service)
        
        print("API Sync Completed Successfully.")
        return True

    except Exception as e:
        print(f"API Sync Failed: {e}")
        return False

if __name__ == "__main__":
    sync_data()
