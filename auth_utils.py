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
    # 1. Check st.secrets (for Cloud Deployment)
    try:
        if hasattr(st, "secrets") and "google_auth" in st.secrets:
            # Convert to dict to ensure compatibility
            # st.secrets might behave like a dict or AttrDict
            secrets_data = st.secrets["google_auth"]
            # Ensure it is a dictionary
            if hasattr(secrets_data, "to_dict"):
                 token_info = secrets_data.to_dict()
            else:
                 token_info = dict(secrets_data)

            creds = Credentials.from_authorized_user_info(info=token_info, scopes=SCOPES)
            # Do NOT return immediately; we need to check expiry/refresh below
    except Exception as e:
        # Show the error so we can debug it in Cloud logs
        # Use st.warning instead of st.error to avoid stopping execution if fallback exists
        print(f"DEBUG: Error loading secrets: {e}")
        st.warning(f"Secrets Error: {e}")
        pass

    # 2. Check local file (token.json) - Only if creds not found yet
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
            st.warning(f"Error refreshing creds: {e}")
            # If refresh fails, we might still try to return creds or set to None?
            # Usually if refresh fails, the token is useless.
            # But let's return it and let the API call fail if it must, or maybe set to None.
            # For now, let's keep it, but warn.
            pass
    
    return creds
