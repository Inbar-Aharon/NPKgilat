import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

@st.cache_resource
def get_creds():
    """Gets valid user credentials from local storage or st.secrets."""
    creds = None
    
    # 1. Check st.secrets (for Cloud Deployment)
    try:
        if hasattr(st, "secrets") and "google_auth" in st.secrets:
            # Assuming st.secrets["google_auth"] contains the token json directly
            # or we reconstruct it.
            # Simple way: Streamlit Cloud usually suggests putting the token json content in secrets.
            token_info = st.secrets["google_auth"]
            creds = Credentials.from_authorized_user_info(info=token_info, scopes=SCOPES)
            return creds # If creds are found in secrets, return them immediately
    except Exception:
        # Secrets not found or invalid - safely ignore and try local file
        pass

    # 2. Check local file (token.json)
    if not creds and os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading token.json: {e}")

    # 3. Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save the refreshed creds locally if possible (not possible in cloud usually, but harmless to try)
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
        except Exception as e:
            print(f"Error refreshing creds: {e}")
            creds = None
    
    return creds
