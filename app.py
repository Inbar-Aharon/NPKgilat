import streamlit as st
import streamlit as st

# --- CONFIGURATION (Must be first) ---
st.set_page_config(page_title="Grower Nutrition Monitor", layout="wide", page_icon="🌿")

# --- IMPORTS WITH ERROR HANDLING ---
try:
    import pandas as pd
    import numpy as np
    import plotly.express as px
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    import auth_utils
    import setup_auth
    import os
    import glob
    import sync_data
    import traceback
except Exception as e:
    st.error(f"🚨 Critical Import Error: {e}")
    # We might need traceback here too if it exists in base python
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# --- ASSETS PATH ---
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

DRIVE_FOLDER_NAME = "data app NPK"

# --- TRANSLATIONS (Ported from R) ---
TRANSLATIONS = {
    "en": {
        "title": "Grower Nutrition Monitor",
        "login_title": "System Access",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "welcome": "Welcome",
        "logout": "Logout",
        "crop_label": "Select Crop:",
        "view_mode": "View Mode:",
        "mode_date": "Plots by Date",
        "mode_plot": "Trends by Plot",
        "mode_table": "Full Data Table",
        "reload_btn": "Reload Data",
        "date_tooltip": "Examination Date",
        "dist_title": "Distribution - Date: ",
        "trend_title": "Trend - Plot: ",
        "select_crop_title": "Select your Crop:",
        "change_crop": "Change Crop",
        "samples_count": "Samples",
        "kpi_optimal_pct": "Optimal %",
        "kpi_in_range": "Samples in Range",
        "kpi_avg": "Avg",
        "kpi_target": "Target",
        "kpi_total": "Total Samples",
        "kpi_selected": "Selected",
        "plot_optimal": "Optimal",
        "plot_out_range": "Out of Range",
        "plot_min": "Min",
        "plot_max": "Max",
        "trend_selector": "Select Plot for Trends:",
        "axis_date": "Date",
        "distribution": "Distribution",
        "filters": "Filters",
        "select_all": "Select All",
        "select_dates": "Select Dates",
        "select_plot": "Select Plot",
        "trends_header": "Trends",
        "dist_header": "Distributions",
        "show_raw_data": "Show Raw Data Table"
    },
    "he": {
        "title": "מערכת ניטור דישון",
        "login_title": "כניסה למערכת",
        "username": "שם משתמש",
        "password": "סיסמה",
        "login_btn": "התחבר",
        "welcome": "ברוך הבא",
        "logout": "יציאה",
        "crop_label": "בחר גידול:",
        "view_mode": "תצוגה:",
        "mode_date": "התפלגות לפי תאריך",
        "mode_plot": "מגמות לפי חלקה",
        "mode_table": "טבלת נתונים מלאה",
        "reload_btn": "רענן נתונים",
        "date_tooltip": "תאריך בדיקה",
        "dist_title": "התפלגות - תאריך: ",
        "trend_title": "מגמה - חלקה: ",
        "select_crop_title": "בחר גידול:",
        "change_crop": "החלף גידול",
        "samples_count": "דגימות",
        "kpi_optimal_pct": "% מיטבי",
        "kpi_in_range": "דגימות בטווח",
        "kpi_avg": "ממוצע",
        "kpi_target": "יעד",
        "kpi_total": "סה״כ דגימות",
        "kpi_selected": "נבחרו",
        "plot_optimal": "מיטבי",
        "plot_out_range": "חריגה",
        "plot_min": "מינימום",
        "plot_max": "מקסימום",
        "trend_selector": "בחר חלקה:",
        "axis_date": "תאריך",
        "distribution": "התפלגות",
        "filters": "סינון",
        "select_all": "בחר הכל",
        "select_dates": "בחר תאריכים",
        "select_plot": "בחר חלקה",
        "trends_header": "מגמות",
        "dist_header": "התפלגויות",
        "show_raw_data": "הצג נתונים גולמיים"
    }
}

# --- CROP TRANSLATIONS ---
CROP_NAMES = {
    "en": {
        "avocado": "Avocado",
        "cucumber": "Cucumber",
        "palm": "Palm",
        "pepper": "Pepper",
        "potato": "Potato",
        "tomato": "Tomato",
        "vine": "Vine",
        "wheat": "Wheat"
    },
    "he": {
        "avocado": "אבוקדו",
        "cucumber": "מלפפון",
        "palm": "תמר",
        "pepper": "פלפל",
        "potato": "תפוח אדמה",
        "tomato": "עגבניה",
        "vine": "גפן",
        "wheat": "חיטה"
    }
}

# --- DATA LOADING ---
# --- DATA LOADING ---
@st.cache_data(ttl=600)
def load_data():
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(DATA_DIR):
        return pd.DataFrame(), pd.DataFrame()

    # Load Users
    users_path = os.path.join(DATA_DIR, 'users.csv')
    users_df = pd.DataFrame()
    if os.path.exists(users_path):
        try:
            users_df = pd.read_csv(users_path)
        except Exception as e:
            st.error(f"Error loading users: {e}")
    else:
        # DEBUG: List files to see what WAS downloaded
        files_in_data = os.listdir(DATA_DIR)
        st.error(f"Could not load user database. 'users.csv' not found in {DATA_DIR}.")
        st.write(f"Files found in data folder: {files_in_data}")

    # Load Data
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    data_frames = []
    
    for f in all_files:
        if 'users.csv' in f: continue
        try:
            df = pd.read_csv(f)
            # Normalize columns
            df.columns = df.columns.str.strip()
            if 'user' in df.columns:
                df.rename(columns={'user': 'username'}, inplace=True)
                
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
            data_frames.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    final_df = pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()
    
    if not final_df.empty:
        final_df = final_df.drop_duplicates()
        cols = ['N', 'P', 'K']
        if all(c in final_df.columns for c in cols):
             final_df = final_df.dropna(subset=cols)
             
    return users_df, final_df

# Legacy sync_icons removed. Using sync_data.py implementation.


def render_crop_selection(crops, t):
    st.markdown(f"<h2 style='text-align: center; color: #1B5E20;'>{t['select_crop_title']}</h2>", unsafe_allow_html=True)
    
    # Spacers to center the grid
    # If 1 crop, use [1, 2, 1]
    # If 2 crops, use [1, 2, 2, 1] etc.
    # For now, simplistic centering:
    
    n_crops = len(crops)
    cols = st.columns(n_crops + 2) # +2 for side spacers
    
    # Iterate crops and place in middle columns
    for i, crop_name in enumerate(crops):
        with cols[i+1]:
            # Use Streamlit container for card-like grouping
            with st.container(border=True):
                # Icon
                icon_path = os.path.join(ASSETS_DIR, f"{crop_name}.png")
                # Try case-insensitive lookup if strict match fails
                if not os.path.exists(icon_path):
                     # Check for any casing
                     for f in os.listdir(ASSETS_DIR):
                         if f.lower() == f"{crop_name}.png".lower():
                             icon_path = os.path.join(ASSETS_DIR, f)
                             break
                
                if os.path.exists(icon_path):
                    st.image(icon_path, width=350)
                else:
                    st.write("🌿") # Simple emoji placeholder if missing
                
                # Button
                # Get translated name
                lang = st.session_state.get('lang', 'en')
                crop_key = crop_name.lower()
                display_name = CROP_NAMES.get(lang, {}).get(crop_key, crop_name.capitalize())
                
                if st.button(display_name, key=f"btn_{crop_name}", use_container_width=True):
                    st.session_state['selected_crop'] = crop_name
                    st.rerun()


# --- CONSTANTS ---
OPTIMAL_RANGES = {
    'N': (1.6, 2.2),
    'P': (0.06, 0.12),
    'K': (0.6, 1.0)
}

# --- LOGO RENDERER ---
def render_logo():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../www/logo.png')
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)

# --- MAIN UI ---
def main():
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'he'
    
    # Global CSS
    direction = 'rtl' if st.session_state['lang'] == 'he' else 'ltr'
    font_url = "https://fonts.googleapis.com/css2?family=Internal:wght@300;400;600;700&display=swap"
    
    st.markdown(f"""
    <style>
    @import url('{font_url}');
    
    html, body, [class*="css"] {{
        font-family: 'Internal', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        direction: {direction}; 
    }}
    
    /* Global Background */
    .stApp {{
        background-color: #F0F2F5; /* Softer, modern gray */
    }}
    
    /* Modern Card Style */
    div.css-card {{
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); /* Subtle shadow */
        border: 1px solid #E5E7EB;
        margin-bottom: 20px;
    }}
    
    /* KPI Metric Styling */
    .kpi-container {{
        text-align: center;
        padding: 10px;
    }}
    .kpi-value {{
        font-size: 2.2rem;
        font-weight: 700;
        color: #111827; /* Dark gray for readability */
        margin: 5px 0;
    }}
    .kpi-label {{
        font-size: 0.9rem;
        color: #6B7280; /* Muted gray */
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}
    .kpi-sub {{
        font-size: 0.8rem;
        color: #9CA3AF;
    }}

    /* Section Headers */
    h1, h2, h3 {{
        color: #111827;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    h3 {{
        font-size: 1.25rem;
        margin-bottom: 1rem;
    }}
    
    /* Custom divider */
    hr {{
        margin: 2rem 0;
        border-color: #E5E7EB;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-{ 'left' if direction == 'rtl' else 'right' }: 1px solid #E5E7EB;
    }}
    
    /* Hide Streamlit default top branding if desired */
    /* header {{visibility: hidden;}} */
    
    /* PILLES STYLING (Targeting Streamlit's st.pills) */
    [data-testid="stPills"] {{
        gap: 8px;
        display: flex;
        flex-wrap: wrap;
    }}
    
    /* General Pill Button */
    [data-testid="stPills"] button {{
        border-radius: 20px !important;
        border: 1px solid #E5E7EB !important;
        background-color: white !important;
        color: #374151 !important;
        padding: 4px 16px !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }}

    /* Hover State */
    [data-testid="stPills"] button:hover {{
        border-color: #10B981 !important; /* Green hover */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}

    /* Active/Selected State (Streamlit uses aria-selected or similar, strict targeting is hard without exact class)
       We will try to rely on Streamlit's internal 'primary' styling but force overrides if possible.
       Usually selected buttons have a specific class. 
       Let's assume default Streamlit behavior puts a background. We want to OVERRIDE it to be OUTLINED.
    */
    /* Target the active element - roughly guessing the attribute or class structure 
       Streamlit active pills usually have a higher specificity background color. 
       We try to target standard streamlit active class fragments if known, but attributes are safer.
       [aria-selected="true"] is common.
    */
    [data-testid="stPills"] button[aria-selected="true"] {{
        background-color: #ECFDF5 !important; /* Very light green bg */
        border: 2px solid #10B981 !important; /* Bold Green Border */
        color: #065F46 !important; /* Dark Green Text */
    }}
    
    /* Fallback if aria-selected isn't used (Streamlit often uses specialized classes) */
    /* We can't easily guess the class name (e.g. st-emotion-cache-...) */
    
    /* --- GLOBAL & SAAS STYLING --- */
    
    /* Global Background */
    .stApp {{
        background-color: #F1F5F9; /* Slate 100 - Clean Light Gray */
    }}
    
    /* Sidebar Styling - Dark Navy */
    [data-testid="stSidebar"] {{
        background-color: #0F172A; /* Slate 900 - Dark Navy */
        border-right: 1px solid #1E293B;
    }}
    [data-testid="stSidebar"] * {{
        color: #F8FAFC; /* White text for text elements */
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: #F8FAFC !important;
    }}
    
    /* Specific Sidebar Button Styling */
    [data-testid="stSidebar"] button {{
        background-color: transparent !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important; /* Slate 700 */
        transition: all 0.2s ease;
    }}
    [data-testid="stSidebar"] button:hover {{
        background-color: #1E293B !important; /* Slate 800 */
        border-color: #94A3B8 !important; /* Slate 400 */
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    /* Sidebar Separator */
    [data-testid="stSidebar"] hr {{
        border-color: #334155;
    }}
    
    /* Modern Card Style (General) */
    div.css-card {{
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* Soft Shadow */
        border: none; /* No border */
        margin-bottom: 20px;
    }}
    
    /* KPI Metric Styling */
    .kpi-container {{
        text-align: center;
        padding: 15px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .kpi-value {{
        font-size: 2.5rem; /* Larger numbers */
        font-weight: 800;
        color: #0F172A; /* Slate 900 */
        margin: 10px 0;
        font-family: 'Segoe UI', sans-serif;
    }}
    .kpi-label {{
        font-size: 0.85rem;
        color: #64748B; /* Slate 500 */
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }}
    .kpi-sub {{
        font-size: 0.8rem;
        color: #94A3B8;
    }}
    
    /* Progress Bar */
    .progress-bg {{
        background-color: #E2E8F0;
        border-radius: 9999px;
        height: 8px;
        width: 100%;
        margin-top: 10px;
        overflow: hidden;
    }}
    .progress-fill {{
        background-color: #10B981; /* Emerald 500 */
        height: 100%;
        border-radius: 9999px;
        transition: width 0.5s ease-in-out;
    }}
    
    /* Section Headers */
    h1, h2, h3 {{
        color: #0F172A;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    
    /* Login Page Overrides (Keep previous specialized styling) */
    [data-testid="stForm"] {{
        background-color: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: none;
        max-width: 400px;
        margin: 0 auto;
    }}
    </style>
    """, unsafe_allow_html=True)
 
    # --- SHOW LOGO REMOVED (Handled in Sidebar block now) ---

    creds = auth_utils.get_creds()
    # ... (Auth logic remains same) ...
    if not creds:
        with st.spinner("Initiating Google Authentication... Check your browser."):
            try:
                setup_auth.setup()
                creds = auth_utils.get_creds() # Reload after setup
            except Exception as e:
                st.error(f"Authentication failed: {e}")


    # Commented out to prevent startup timeout
    # if 'icons_synced' not in st.session_state:
    #     try:
    #         sync_data.sync_icons_only(creds)
    #         st.session_state['icons_synced'] = True
    #     except Exception:
    #         pass

    # --- MANUAL SYNC TRIGGER (For Cloud Deployment) ---
    # Check if data folder is valid (must have users.csv)
    users_csv_path = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')
    
    if not os.path.exists(users_csv_path):

        st.warning("⚠️ Data not found locally.")
        st.info("Since this is a cloud deployment, we need to fetch data from Google Drive.")
        
        if st.button("Download Data from Drive & Start App"):
             if creds:
                 with st.spinner("Downloading data... this may take 1-2 minutes..."):
                     try:
                         # Now expecting a tuple (success, message)
                         result = sync_data.sync_data(creds)
                         if isinstance(result, tuple):
                             success, msg = result
                         else:
                             # Fallback if old version of sync_data is loaded (unlikely but safe)
                             success, msg = result, "Unknown error"
                         
                         if success:
                             st.success(f"{msg}")
                             st.session_state['icons_synced'] = True # Assume icons also came
                             st.cache_data.clear()
                             st.rerun()
                         else:
                             st.error(f"Download failed: {msg}")
                     except Exception as e:
                         st.error(f"Critical Error: {e}")

             else:
                 st.error("Authentication credentials not found.")
        
        # STOP execution here so the app renders the button and doesn't crash trying to load missing data
        st.stop()

    if not creds:
        st.warning("Authentication failed or cancelled. Please check console logs or run `python3 setup_auth.py` manually.")
        st.stop()
        
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    if 'selected_crop' not in st.session_state:
        st.session_state['selected_crop'] = None

    t = TRANSLATIONS[st.session_state['lang']]
    
    # --- SIDEBAR (Global) ---
    with st.sidebar:
        # 1. LOGO (Top Priority)
        logo_path = os.path.join(ASSETS_DIR, "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
            st.write("") 
        else:
            st.markdown("## NPK GILAT", unsafe_allow_html=True)
        
        # 2. Language Toggle
        lang_choice = st.radio("Language / שפה", ["English", "עברית"], index=1 if st.session_state['lang'] =='he' else 0, horizontal=True)
        if (lang_choice == "עברית" and st.session_state['lang'] != 'he') or (lang_choice == "English" and st.session_state['lang'] != 'en'):
            st.session_state['lang'] = 'he' if lang_choice == "עברית" else 'en'
            t = TRANSLATIONS[st.session_state['lang']] # Update immediately
            st.rerun()
            
        # 3. Reload/Sync
        if st.button(t['reload_btn'], use_container_width=True):
            with st.spinner("Syncing data & icons from Drive..."):
                 success = sync_data.sync_data(creds)
                 if success:
                     st.success("Sync Complete!")
                     st.cache_data.clear()
                     st.rerun()
                 else:
                     st.error("Sync Failed. Check logs.")            
        st.markdown("---")

    # --- LOGIN SCREEN ---
    if st.session_state['user'] is None:
        # Centering layout
        l_col1, l_col2, l_col3 = st.columns([1, 2, 1])
        
        with l_col2:
            st.markdown(f"<h1 style='text-align: center; font-family: serif; margin-bottom: 30px;'>{t['login_title']}</h1>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                # Using emojis as icons in labels since we can't easily put icons inside input in pure Streamlit
                username = st.text_input(f"👤 {t['username']}")
                password = st.text_input(f"🔒 {t['password']}", type="password")
                
                # Spacer
                st.write("")
                
                submitted = st.form_submit_button(t['login_btn'])
                
                if submitted:
                    # Load users to verify
                    with st.spinner("Authenticating..."):
                       users_db, _ = load_data()
                    
                    if users_db is not None and not users_db.empty:
                        users_db['username'] = users_db['username'].astype(str).str.strip()
                        users_db['password'] = users_db['password'].astype(str).str.strip()
                        
                        user_match = users_db[
                            (users_db['username'] == str(username).strip()) & 
                            (users_db['password'] == str(password).strip())
                        ]
                        if not user_match.empty:
                            st.session_state['user'] = username
                            st.success(f"{t['welcome']} {username}")
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password")
                    else:
                        st.error("Could not load user database.")
        st.stop()


    # --- DASHBOARD ---
    
    # 1. Load Data
    with st.spinner("Loading Data..."):
        _, main_data = load_data()

    if main_data is None or main_data.empty:
         st.warning("No data found.")
         st.stop()
         
    # Filter by User
    user_data = main_data[main_data['username'] == st.session_state['user']]
    available_crops = user_data['crop'].unique().tolist()
    
    # Filter out non-crop items
    excluded_crops = ['logo', 'icon', 'unknown', 'nan', 'none']
    available_crops = [
        c for c in available_crops 
        if str(c).lower() not in excluded_crops and pd.notna(c)
    ]
    
    # 2. Crop Selection Screen
    if st.session_state['selected_crop'] is None:
        with st.sidebar:
             # Just add user info and logout here, simplified as logo/lang is already up
             st.write(f"{t['welcome']}, **{st.session_state['user']}**")
             if st.button(t['logout'], use_container_width=True):
                st.session_state['user'] = None
                st.session_state['selected_crop'] = None
                st.rerun()
                
        render_crop_selection(available_crops, t)
        st.stop()
        
    # 3. Main Dashboard (Crop Selected) - MODERN LAYOUT
    selected_crop = st.session_state['selected_crop']
    crop_data = user_data[user_data['crop'] == selected_crop].copy()
    
    # Format dates
    if 'date' in crop_data.columns:
        crop_data['date'] = pd.to_datetime(crop_data['date'])
        crop_data['date_fmt'] = crop_data['date'].dt.strftime('%d/%m/%y')

    # --- SIDEBAR (Controls) ---
    # Append to existing sidebar
    with st.sidebar:
        st.caption(f"Logged in as: {st.session_state['user']}")
        
        st.markdown("### Navigation")
        if st.button(f"🌿 {t['change_crop']}", use_container_width=True):
            st.session_state['selected_crop'] = None
            st.rerun()
            
        if st.button(f"🚪 {t['logout']}", use_container_width=True):
            st.session_state['user'] = None
            st.session_state['selected_crop'] = None
            st.rerun()
            
        st.markdown("---")
        st.caption("v1.0.2 • SaaS Edition")


    # --- HEADER & FILTERS ---
    # Container for Header and Top Level Filters
    # --- HEADER & FILTERS ---
    # Container for Header and Top Level Filters
    with st.container():
        # Using a unified container style for the top bar
        
        # Header Row
        col_header, col_sample = st.columns([3, 1])
        with col_header:
            # Translated Title with custom styling wrapper if needed, but h1 global should suffice
            crop_key = selected_crop.lower()
            display_title = CROP_NAMES.get(st.session_state['lang'], {}).get(crop_key, selected_crop.capitalize())
            
            # Use raw HTML for finer control over title appearance in the SaaS theme
            st.markdown(f"<h1 style='font-size: 3rem; margin-bottom: 0;'>{display_title}</h1>", unsafe_allow_html=True)
            st.caption(f"Grower Nutrition Monitor • {t['welcome']} {st.session_state['user']}")
            
        with col_sample:
            # Placeholder 
            pass

        st.markdown("---")

        # --- DATE FILTER BAR ---
        # Moving Date Selection to a clearer "Bar"
        with st.container(border=True):
            # Layout: Icon/Title left, Pills right
            # We want "Select Dates" label + Icon, then pills.
            # User image shows: [Calendar Icon] [Pill] [Pill]
            
            d_col_icon, d_col_pills = st.columns([1, 15]) 
            
            with d_col_icon:
                st.markdown("<div style='font-size: 1.8rem; padding-top: 5px; text-align: center;'>📅</div>", unsafe_allow_html=True)
                
            with d_col_pills:
                st.caption(f"{t['filters']}")
                
                # Filters
                all_dates = sorted(crop_data['date'].unique())
                formatted_dates = [pd.to_datetime(d).strftime('%d/%m/%y') for d in all_dates]
                date_map = dict(zip(formatted_dates, all_dates))
                
                # Helper layout
                ctrl_col1, ctrl_col2 = st.columns([2, 8])
                with ctrl_col1:
                    use_all_dates = st.toggle(t['select_all'], value=True)
                    
                with ctrl_col2:
                     if use_all_dates:
                         st.info(f"{t['select_all']} ({t['filters']})")
                         selected_dates_fmt = formatted_dates
                     else:
                         try:
                             # Using new key
                             selected_dates_fmt = st.pills(t['select_dates'], options=formatted_dates, selection_mode="multi", label_visibility="collapsed", key="date_pills")
                         except AttributeError:
                             # Fallback
                             selected_dates_fmt = st.multiselect(t['select_dates'], options=formatted_dates, default=formatted_dates, label_visibility="collapsed")
            # Fallback logic simplified for brevity in edit, assuming correct replacement.

        # st.markdown('</div>', unsafe_allow_html=True) # REMOVED: End Top Card


    # Filter Data Logic
    if not selected_dates_fmt:
        # If pills return None (when nothing selected), we might want to default to nothing or all?
        # Usually nothing.
        filtered_df = pd.DataFrame(columns=crop_data.columns)
    else:
        selected_timestamps = [date_map[fmt] for fmt in selected_dates_fmt]
        filtered_df = crop_data[crop_data['date'].isin(selected_timestamps)]

    # Update Sample Count in Top Bar (visually tricky without rerun, so we display it in KPI section or just below)
    # Actually, let's keep it simple and put it in the KPI section or a specific status bar.


    # --- KPI SECTION ---
    if not filtered_df.empty:
        # Calculate Metrics
        mean_n = filtered_df['N'].mean()
        mean_p = filtered_df['P'].mean()
        
        n_opt = filtered_df['N'].between(OPTIMAL_RANGES['N'][0], OPTIMAL_RANGES['N'][1])
        p_opt = filtered_df['P'].between(OPTIMAL_RANGES['P'][0], OPTIMAL_RANGES['P'][1])
        k_opt = filtered_df['K'].between(OPTIMAL_RANGES['K'][0], OPTIMAL_RANGES['K'][1])
        all_opt = n_opt & p_opt & k_opt
        pct_optimal = (all_opt.sum() / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        
        # KPI Grid
        # k_col1, k_col2, k_col3, k_col4 = st.columns(4) # Old equal columns
        # Use gap for spacing
        k_col1, k_col2, k_col3, k_col4 = st.columns(4, gap="medium")
        
        def render_kpi(col, label, value, sub_label, icon, progress=None):
            with col:
                # Progress Bar HTML
                progress_html = ""
                if progress is not None:
                    # CLAMP 0-100
                    p_val = max(0, min(100, progress))
                    # Use single line to avoid markdown code block interpretation (4 spaces indentation issue)
                    progress_html = f'<div class="progress-bg"><div class="progress-fill" style="width: {p_val}%;"></div></div>'
                
                st.markdown(f"""
                <div class="css-card kpi-container">
                    <div style="font-size: 2rem; margin-bottom: 5px;">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub_label}</div>
                    {progress_html}
                </div>
                """, unsafe_allow_html=True)

        render_kpi(k_col1, t['kpi_optimal_pct'], f"{pct_optimal:.0f}%", t['kpi_in_range'], "🏆", progress=pct_optimal)
        render_kpi(k_col2, f"{t['kpi_avg']} P", f"{mean_p:.3f}", f"{t['kpi_target']}: {OPTIMAL_RANGES['P'][0]}-{OPTIMAL_RANGES['P'][1]}", "🌱")
        render_kpi(k_col3, f"{t['kpi_avg']} N", f"{mean_n:.2f}", f"{t['kpi_target']}: {OPTIMAL_RANGES['N'][0]}-{OPTIMAL_RANGES['N'][1]}", "🌿")
        render_kpi(k_col4, t['kpi_total'], f"{len(filtered_df)}", f"{t['kpi_selected']}: {len(filtered_df)}", "📊")

    
    # --- VISUALIZATIONS GRID ---
    
    # Helper for Plotly config
    config = {'displayModeBar': False}

    if not filtered_df.empty:
        import plotly.graph_objects as go
        
        # --- ROW 1: DISTRIBUTIONS ---
        st.markdown(f"### {t['dist_header']}")
        
        d_col1, d_col2, d_col3 = st.columns(3)
        
        if 'clicked_site' not in st.session_state:
            st.session_state['clicked_site'] = None
        if 'clicked_date' not in st.session_state:
            st.session_state['clicked_date'] = None

        def plot_jitter_modern(element, limits, chart_key, highlight_site=None):
            min_lim, max_lim = limits
            
            # Helper to create traces
            def add_traces(fig, subset_df, is_highlighted, is_background):
                if subset_df.empty: return

                vals = subset_df[element]
                dates = subset_df['date']
                dates_fmt = subset_df['date_fmt']
                sites = subset_df['site']
                sample_names = subset_df['sample']
                is_in = vals.between(min_lim, max_lim)
                
                # Styles
                if is_background:
                    opacity = 0.1
                    size = 8
                    color_in = '#9CA3AF' # Gray
                    color_out = '#9CA3AF'
                    line_width = 0
                elif is_highlighted:
                    opacity = 1.0
                    size = 14
                    color_in = '#10B981' # Green
                    color_out = '#EF4444' # Red
                    line_width = 2 # Bold border
                else: # Default (No selection)
                    opacity = 0.7
                    size = 10
                    color_in = '#10B981'
                    color_out = '#EF4444'
                    line_width = 1

                # Customdata for all points [Site, Sample]
                c_data = np.stack((sites, sample_names), axis=-1)

                # Optimal Trace
                if not vals[is_in].empty:
                    fig.add_trace(go.Scatter(
                        x=dates[is_in], y=vals[is_in],
                        mode='markers',
                        marker=dict(color=color_in, size=size, opacity=opacity, line=dict(width=line_width, color='white' if not is_background else 'transparent')), 
                        name=t['plot_optimal'] if not is_background else None,
                        customdata=c_data[is_in],
                        text=dates_fmt[is_in],
                        hovertemplate='<b>Site:</b> %{customdata[0]}<br><b>Sample:</b> %{customdata[1]}<br><b>Date:</b> %{text}<br><b>Val:</b> %{y:.2f}<extra></extra>' if not is_background else None,
                        showlegend=not is_background and not is_highlighted # Only show legend for default view to avoid clutter
                    ))
                
                # Out Trace
                if not vals[~is_in].empty:
                    fig.add_trace(go.Scatter(
                        x=dates[~is_in], y=vals[~is_in],
                        mode='markers',
                        marker=dict(color=color_out, size=size, opacity=opacity, line=dict(width=line_width, color='white' if not is_background else 'transparent')), 
                        name=t['plot_out_range'] if not is_background else None,
                        customdata=c_data[~is_in],
                        text=dates_fmt[~is_in],
                        hovertemplate='<b>Site:</b> %{customdata[0]}<br><b>Sample:</b> %{customdata[1]}<br><b>Date:</b> %{text}<br><b>Val:</b> %{y:.2f}<extra></extra>' if not is_background else None,
                        showlegend=not is_background and not is_highlighted
                    ))

            fig = go.Figure()

            if highlight_site:
                # 1. Plot Background (All other sites)
                bg_df = filtered_df[filtered_df['site'] != highlight_site]
                add_traces(fig, bg_df, is_highlighted=False, is_background=True)
                
                # 2. Plot Highlight (Selected site)
                hl_df = filtered_df[filtered_df['site'] == highlight_site]
                add_traces(fig, hl_df, is_highlighted=True, is_background=False)
            else:
                # Plot All Normal
                add_traces(fig, filtered_df, is_highlighted=False, is_background=False)

            # Limit Lines
            fig.add_hline(y=min_lim, line_width=1, line_dash="dash", line_color="#10B981", opacity=0.6)
            fig.add_hline(y=max_lim, line_width=1, line_dash="dash", line_color="#10B981", opacity=0.6)

            fig.update_layout(
                showlegend=False, # cleaner look
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=40, t=40, b=40),
                height=320,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(showgrid=True, gridcolor='#F3F4F6', automargin=True, tickformat='%d/%m/%y', tickangle=0),
                yaxis=dict(showgrid=True, gridcolor='#F3F4F6', automargin=True),
                dragmode='select', 
                clickmode='event+select'
            )
            
            # Key must remain static to preserve selection state across reruns
            event = st.plotly_chart(fig, use_container_width=True, config=config, on_select="rerun", selection_mode="points", key=chart_key)
            return event

        # Handle Events
        current_highlight = st.session_state.get('clicked_site', None)

        with d_col1:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center; margin-bottom: 0;'>{t['distribution']} N</h3>", unsafe_allow_html=True)
                event_n = plot_jitter_modern('N', OPTIMAL_RANGES['N'], 'chart_n', current_highlight)
            
        with d_col2:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center; margin-bottom: 0;'>{t['distribution']} P</h3>", unsafe_allow_html=True)
                event_p = plot_jitter_modern('P', OPTIMAL_RANGES['P'], 'chart_p', current_highlight)

        with d_col3:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center; margin-bottom: 0;'>{t['distribution']} K</h3>", unsafe_allow_html=True)
                event_k = plot_jitter_modern('K', OPTIMAL_RANGES['K'], 'chart_k', current_highlight)
        
        # Process Clicks
        # Check which event has selection
        new_site = None
        new_date = None
        
        def extract_selection(event):
            if event and event.selection and event.selection.points:
                pt = event.selection.points[0]
                # customdata should be [Site, Sample]
                if 'customdata' in pt:
                    data = pt['customdata']
                    # Check if it's a list/array and get first element
                    if isinstance(data, (list, tuple, np.ndarray)) and len(data) > 0:
                        return data[0], pt['x']
                    return data, pt['x'] # Fallback if just string
            return None, None

        s_n, d_n = extract_selection(event_n)
        s_p, d_p = extract_selection(event_p)
        s_k, d_k = extract_selection(event_k)
        
        if s_n: 
            new_site, new_date = s_n, d_n
        elif s_p: 
            new_site, new_date = s_p, d_p
        elif s_k: 
            new_site, new_date = s_k, d_k
            
        if new_site:
            st.session_state['clicked_site'] = new_site
            st.session_state['clicked_date'] = new_date
            # Rerun to update highlights immediately
            st.rerun()
            
        
        # --- ROW 2: TRENDS ---
        st.markdown("---")
        st.markdown(f"### {t['trends_header']}")
        
        # Trend Controls
        
        # Dedicated Bar for Plot Selection
        with st.container(border=True):
             # Layout: Icon left, Pills right
             t_col_icon, t_col_pills = st.columns([1, 15])
             
             with t_col_icon:
                  st.markdown("<div style='font-size: 1.8rem; padding-top: 5px; text-align: center;'>📍</div>", unsafe_allow_html=True)
             
             with t_col_pills:
                 if st.session_state['clicked_site']:
                     st.markdown(f"**Active Selection:** `{st.session_state['clicked_site']}`")
                     if st.button("Reset Selection"):
                         st.session_state['clicked_site'] = None
                         st.session_state['clicked_date'] = None
                         st.rerun()
                 else:
                     st.caption("Click any point above to highlight its history.")
             
        # Trend Plotting Logic
        # Return to clean 'Daily Mean' aesthetic
        
        def plot_trend_modern(element, color, limits):
                min_lim, max_lim = limits
                
                fig = go.Figure()

                # Determine Data Source
                if st.session_state['clicked_site']:
                    # Specific Site
                    hl_site = st.session_state['clicked_site']
                    # Daily Mean for Site
                    plot_df = crop_data[crop_data['site'] == hl_site].groupby('date')[['N', 'P', 'K']].mean().reset_index().sort_values('date')
                    plot_name = hl_site
                    style_dict = dict(color=color, width=3, shape='spline')
                else:
                    # Global Average
                    plot_df = crop_data.groupby('date')[['N', 'P', 'K']].mean().reset_index().sort_values('date')
                    plot_name = "Global Avg"
                    style_dict = dict(color=color, width=3, shape='spline') # Treat global same as site style-wise for consistent look

                fig.add_trace(go.Scatter(
                    x=plot_df['date'], y=plot_df[element],
                    mode='lines+markers',
                    line=style_dict,
                    marker=dict(size=8, color='white', line=dict(width=2, color=color)),
                    name=plot_name,
                    hovertemplate='%{x|%d/%m/%y}: %{y:.2f}'
                ))

                # Limits
                fig.add_hline(y=min_lim, line_width=1, line_dash="dash", line_color="#10B981")
                fig.add_hline(y=max_lim, line_width=1, line_dash="dash", line_color="#10B981")
                
                # Reference Line for Clicked Date
                if st.session_state['clicked_date']:
                    fig.add_vline(x=st.session_state['clicked_date'], line_width=2, line_dash="dot", line_color="#EF4444")

                fig.update_layout(
                    margin=dict(l=40, r=40, t=10, b=40),
                    height=280, 
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(showgrid=True, gridcolor='#F3F4F6', tickformat='%d/%m/%y'),
                    yaxis=dict(showgrid=True, gridcolor='#F3F4F6'),
                    showlegend=True
                )
                return fig

        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
                st.plotly_chart(plot_trend_modern('N', '#3B82F6', OPTIMAL_RANGES['N']), use_container_width=True, config=config) # Blue
        with t_col2:
                st.plotly_chart(plot_trend_modern('P', '#F59E0B', OPTIMAL_RANGES['P']), use_container_width=True, config=config) # Amber
        with t_col3:
                st.plotly_chart(plot_trend_modern('K', '#10B981', OPTIMAL_RANGES['K']), use_container_width=True, config=config) # Green

            
    # Raw Data Expander
    with st.expander("Show Raw Data Table / הצג נתונים גולמיים"):
        st.dataframe(filtered_df, use_container_width=True)

import traceback

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("🚨 Fatal Error during execution:")
        st.code(traceback.format_exc())
