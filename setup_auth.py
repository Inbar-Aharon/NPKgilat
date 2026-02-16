import os
from google_auth_oauthlib.flow import InstalledAppFlow

# MUST match the scopes in auth_utils.py
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def setup():
    print("--- Google Drive Auth Setup for Streamlit ---")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(base_dir, 'token.json')
    creds_file = os.path.join(base_dir, 'credentials.json')
    
    if os.path.exists(token_path):
        print("token.json already exists. Delete it if you want to re-authenticate.")
        return

    # Check for client secrets file
    if not os.path.exists(creds_file):
        print("\nERROR: credentials.json not found.")
        print(f"Expected at: {creds_file}")
        print("---------------------------------------------------")
        print("To run this app, you need to provide OAuth 2.0 Client IDs.")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com")
        print("2. Create a Project (or use existing).")
        print("3. Enable 'Google Drive API'.")
        print("4. Go to Credentials > Create Credentials > OAuth Client ID.")
        print("5. Choose 'Desktop App'.")
        print("6. Download the JSON file, rename it to 'credentials.json' and place it in this folder.")
        print("---------------------------------------------------\n")
        return

    # Run Auth Flow
    try:
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
        creds = flow.run_local_server(port=0)
    except Exception as e:
        print(f"Auth flow failed: {e}")
        return
    
    # Save the credentials
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print("\nSuccess! 'token.json' created.")
    print("You can now run the Streamlit app.")

if __name__ == "__main__":
    setup()
