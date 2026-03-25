import os
import io
import shutil
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import auth_utils
import dateutil.parser

# Configuration
DRIVE_FOLDER_NAME = "data app NPK"
LOCAL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
LOCAL_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
REQUIRED_DATA_PREFIXES = ("results_",)
REQUIRED_DATA_FILES = {"users.csv", "users"}

# User provided local path for Drive
USER_DRIVE_PATH = "/Users/inbaraharon/Library/CloudStorage/GoogleDrive-npkgilat@gmail.com/My Drive/WORKFLOWS/or/Inbar/data app NPK"

def ensure_dirs():
    if not os.path.exists(LOCAL_DATA_DIR):
        os.makedirs(LOCAL_DATA_DIR)
    if not os.path.exists(LOCAL_ASSETS_DIR):
        os.makedirs(LOCAL_ASSETS_DIR)


def is_required_data_csv(file_name):
    """Allow only the CSV files used by the dashboard."""
    name_lower = str(file_name).strip().lower()
    if name_lower in REQUIRED_DATA_FILES:
        return True
    return name_lower.endswith('.csv') and name_lower.startswith(REQUIRED_DATA_PREFIXES)


def should_download_remote(file_meta, dest_path):
    """Skip downloading when a local file is already up-to-date."""
    if not os.path.exists(dest_path):
        return True

    remote_modified = (file_meta or {}).get('modifiedTime')
    if not remote_modified:
        return False

    try:
        remote_ts = dateutil.parser.isoparse(remote_modified).timestamp()
        local_ts = os.path.getmtime(dest_path)
        return remote_ts > (local_ts + 1)
    except Exception:
        # If metadata cannot be parsed, prefer downloading to keep data fresh.
        return True

def sync_from_local_drive():
    """Syncs data and icons directly from the local Google Drive folder."""
    print(f"Checking local Drive path: {USER_DRIVE_PATH}")
    if not os.path.exists(USER_DRIVE_PATH):
        print("Local Drive path not found. Falling back to API (if implemented).")
        return False
        
    print("Found local Drive folder! Syncing via file copy...")
    ensure_dirs()
    
    # 1. Sync only required data files (users.csv + results_*.csv).
    data_count = 0
    for root, dirs, files in os.walk(USER_DRIVE_PATH):
        for file in files:
            if is_required_data_csv(file) and not file.startswith('.'):
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
    if not os.path.exists(dest):
        return True
    try:
        if os.path.getsize(src) != os.path.getsize(dest):
            return True
        return os.path.getmtime(src) > (os.path.getmtime(dest) + 1)
    except OSError:
        return True

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

        # Sequential download for stability
        downloaded_count = 0
        skipped_count = 0
        for f in final_icons:
            try:
                target_path = os.path.join(LOCAL_ASSETS_DIR, f['name'])
                if not should_download_remote(f, target_path):
                    skipped_count += 1
                    continue
                download_icon_wrapper(f)
                downloaded_count += 1
            except Exception as e:
                print(f"Failed to download icon {f['name']}: {e}")

        print(f"Icon sync complete. Downloaded: {downloaded_count}, skipped unchanged: {skipped_count}")

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
            return False, "No credentials found. Please check secrets."

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
            return False, f"Folder '{DRIVE_FOLDER_NAME}' not found in Drive. Please verify the folder name."
        
        root_folder_id = items[0]['id']

        def find_folder_id(parent_id, folder_name):
            resp = service.files().list(
                q=(
                    f"'{parent_id}' in parents and "
                    f"name = '{folder_name}' and "
                    "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                ),
                fields="files(id, name)",
            ).execute()
            found = resp.get('files', [])
            return found[0]['id'] if found else None

        # 2. Restrict search strictly to the app data folder:
        # DRIVE_FOLDER_NAME/GrowerNutritionMonitor/streamlit_app/data
        gnm_id = find_folder_id(root_folder_id, 'GrowerNutritionMonitor')
        if not gnm_id:
            return False, "Folder 'GrowerNutritionMonitor' not found under Drive root."

        streamlit_app_id = find_folder_id(gnm_id, 'streamlit_app')
        if not streamlit_app_id:
            return False, "Folder 'streamlit_app' not found under GrowerNutritionMonitor."

        data_folder_id = find_folder_id(streamlit_app_id, 'data')
        if not data_folder_id:
            return False, "Folder 'data' not found under streamlit_app."

        # 3. Collect only files inside streamlit_app/data.
        files_to_download = []
        page_token = None
        while True:
            kwargs = {
                'q': f"'{data_folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                'fields': "nextPageToken, files(id, name, mimeType, modifiedTime)",
            }
            if page_token:
                kwargs['pageToken'] = page_token

            resp = service.files().list(**kwargs).execute()
            for f in resp.get('files', []):
                name_lower = f['name'].lower()
                if name_lower == 'users.csv' or name_lower == 'users':
                    f['save_as'] = 'users.csv'
                    files_to_download.append(f)
                elif is_required_data_csv(f['name']):
                    files_to_download.append(f)

            page_token = resp.get('nextPageToken')
            if not page_token:
                break
        
        # Deduplicate
        unique_files = {}
        for f in files_to_download:
            # key by target filename!
            target_name = f.get('save_as', f['name'])
            if target_name not in unique_files:
                unique_files[target_name] = f
            else:
                # Decide based on mod time... logic needs original timestamps
                current = unique_files[target_name]
                current_time = current.get('modifiedTime')
                new_time = f.get('modifiedTime')
                if current_time and new_time:
                     dt_current = dateutil.parser.isoparse(current_time)
                     dt_new = dateutil.parser.isoparse(new_time)
                     if dt_new > dt_current:
                         unique_files[target_name] = f
        
        final_files_list = list(unique_files.values())
        print(f"Found {len(final_files_list)} unique API files to sync.")
        
        if not final_files_list:
             return False, "Found folder but no CSV files inside."

        # Sequential download to avoid SSL errors
        failures = []
        downloaded = 0
        skipped = 0
        for f in final_files_list:
             target_name = f.get('save_as', f['name'])
             try:
                 dest_path = os.path.join(LOCAL_DATA_DIR, target_name)
                 if not should_download_remote(f, dest_path):
                     skipped += 1
                     continue
                 download_file(service, f['id'], target_name, file_meta=f)
                 downloaded += 1
             except Exception as e:
                 print(f"Failed to download {target_name}: {e}")
                 failures.append(f"{target_name} ({e})")
        
        try:
             sync_icons_api(service)
        except Exception as e:
             print(f"Icon sync minor error: {e}")
        
        # Check if users.csv was found
        downloaded_names = [f.get('save_as', f['name']) for f in final_files_list]
        
        if failures:
             return True, f"Sync partial. Failed: {failures}. Downloaded: {downloaded}, skipped: {skipped}. Users found: {'users.csv' in downloaded_names}"

        if 'users.csv' not in downloaded_names:
            return True, f"Sync complete, BUT 'users.csv' was missing! Downloaded: {downloaded}, skipped: {skipped}. Found: {downloaded_names}"
            
        print("API Sync Completed Successfully.")
        return True, f"Sync completed successfully. Downloaded: {downloaded}, skipped unchanged: {skipped}."

    except Exception as e:
        print(f"API Sync Failed: {e}")
        return False, f"API Error: {str(e)}"

def download_file(service, file_id, file_name, dest_folder=LOCAL_DATA_DIR, file_meta=None):
    """Downloads a file from Drive."""
    """Downloads a file from Drive."""
    """Downloads a file from Drive."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if file_meta and file_meta.get('mimeType') == 'application/vnd.google-apps.spreadsheet':
                 # Export Google Sheet as CSV
                 request = service.files().export_media(fileId=file_id, mimeType='text/csv')
                 # Force .csv extension if missing
                 if not file_name.lower().endswith('.csv'):
                     file_name += '.csv'
            else:
                 # Standard download
                 request = service.files().get_media(fileId=file_id)
                 
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Save to disk
            filepath = os.path.join(dest_folder, file_name)
            with open(filepath, "wb") as f:
                f.write(fh.getbuffer())
            print(f"Downloaded: {file_name}")
            return # Success
        except Exception as e:
            print(f"Failed to download {file_name} (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise e
            import time
            time.sleep(1) # Wait before retry

if __name__ == "__main__":
    sync_data()
