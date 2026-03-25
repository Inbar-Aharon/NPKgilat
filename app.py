import streamlit as st

# --- CONFIGURATION (Must be first) ---
st.set_page_config(page_title="Grower Nutrition Monitor", layout="wide", page_icon="🌿")

# --- IMPORTS WITH ERROR HANDLING ---
try:
    import pandas as pd
    import numpy as np
    import plotly.express as px
    from PIL import Image
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    import auth_utils
    import setup_auth
    import os
    import glob
    import sync_data
    import traceback
    import base64
    from urllib.parse import quote
    from html import escape
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
IS_STREAMLIT_CLOUD = os.path.exists("/mount/src") or os.environ.get("HOME") == "/home/adminuser"
REPO_ASSET_BASE_URL = "https://raw.githubusercontent.com/Inbar-Aharon/NPKgilat/main/assets"

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
        "show_raw_data": "Show Raw Data Table",
        "plot_binding_help": "Each point is linked to a single lab record. Click a point to open its history and inspect the linked data.",
        "history_title": "Point History",
        "history_record": "Selected Record",
        "history_logs": "Linked History",
        "history_hint": "Click any point in the charts to inspect its linked history.",
        "history_site": "Site",
        "history_sample": "Sample",
        "history_id": "Record ID",
        "history_date": "Date",
        "history_close": "Close History",
        "history_reset": "Clear Selection",
        "history_focus": "History for selected site",
        "history_scope": "Showing linked records for the same sample across all dates.",
        "sample_selection_help": "Select any sample point to display all records for that sample across all dates.",
        "history_none": "No linked history was found for the selected record.",
        "trend_overview": "Overview Trend",
        "history_open": "Open History",
        "granular_data": "Granular Data",
        "selected_point": "Selected point"
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
        "show_raw_data": "הצג נתונים גולמיים",
        "plot_binding_help": "כל נקודה מקושרת לרשומת מעבדה אחת. לחצו על נקודה כדי לפתוח את ההיסטוריה ולבדוק את הנתונים המקושרים.",
        "history_title": "היסטוריית נקודה",
        "history_record": "רשומה נבחרת",
        "history_logs": "היסטוריה מקושרת",
        "history_hint": "לחצו על נקודה באחד הגרפים כדי לראות את כל הנתונים על אותה נקודה",
        "history_site": "חלקה",
        "history_sample": "דגימה",
        "history_id": "מזהה רשומה",
        "history_date": "תאריך",
        "history_close": "סגור היסטוריה",
        "history_reset": "נקה בחירה",
        "history_focus": "היסטוריה עבור החלקה שנבחרה",
        "history_scope": "מוצגות רשומות מקושרות של אותה דגימה לאורך כל התאריכים.",
        "sample_selection_help": "בחרו נקודת דגימה כדי להציג את כל הנתונים של אותה דגימה לאורך כל התאריכים.",
        "history_none": "לא נמצאה היסטוריה מקושרת לרשומה שנבחרה.",
        "trend_overview": "מגמת סקירה",
        "history_open": "פתח היסטוריה",
        "granular_data": "נתונים מפורטים",
        "selected_point": "נקודה נבחרת"
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

# # --- DATA LOADING ---
@st.cache_data(ttl=600)
def load_data():
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # 1. טעינת משתמשים מה-Secrets בלבד
    users_df = pd.DataFrame()
    if "users" in st.secrets:
        try:
            users_raw = st.secrets["users"]
            if hasattr(users_raw, "to_dict"):
                users_raw = users_raw.to_dict()

            parsed_users = []
            if isinstance(users_raw, dict):
                # Format A: {"demo": "1234", ...}
                if all(not isinstance(v, (dict, list, tuple)) for v in users_raw.values()):
                    parsed_users = [{"username": str(k), "password": str(v)} for k, v in users_raw.items()]
                # Format B: {"username": "demo", "password": "1234"}
                elif "username" in users_raw and "password" in users_raw:
                    parsed_users = [{"username": str(users_raw.get("username")), "password": str(users_raw.get("password"))}]
                # Format C: {"demo": {"password": "1234"}, ...}
                else:
                    for key, value in users_raw.items():
                        if hasattr(value, "to_dict"):
                            value = value.to_dict()
                        if isinstance(value, dict) and "password" in value:
                            uname = value.get("username", key)
                            parsed_users.append({"username": str(uname), "password": str(value.get("password"))})
            elif isinstance(users_raw, (list, tuple)):
                # Format D: [{"username": "demo", "password": "1234"}, ...]
                for item in users_raw:
                    if hasattr(item, "to_dict"):
                        item = item.to_dict()
                    if isinstance(item, dict):
                        uname = item.get("username", item.get("user"))
                        pwd = item.get("password")
                        if uname is not None and pwd is not None:
                            parsed_users.append({"username": str(uname), "password": str(pwd)})

            users_df = pd.DataFrame(parsed_users)
            if not users_df.empty:
                users_df["username"] = users_df["username"].astype(str).str.strip()
                users_df["password"] = users_df["password"].astype(str).str.strip()
            else:
                st.error("🚨 users ב-secrets.toml בפורמט לא נתמך.")
        except Exception as e:
            st.error(f"🚨 שגיאה בטעינת users מ-secrets.toml: {e}")
            users_df = pd.DataFrame()
    else:
        st.error("🚨 לא נמצאו משתמשים ב-secrets.toml!")

    # 2. טעינת נתוני הגידולים מה-CSV
    if not os.path.exists(DATA_DIR):
        return users_df, pd.DataFrame()

    all_csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    # Prefer only dashboard datasets to avoid parsing unrelated test CSV files.
    all_files = [
        f for f in all_csv_files
        if os.path.basename(f).lower().startswith("results_")
    ]
    if not all_files:
        all_files = [
            f for f in all_csv_files
            if os.path.basename(f).lower() not in ("users.csv", "users")
        ]
    data_frames = []
    
    for f in all_files:
        if 'users.csv' in f: continue  # מדלג על הקובץ הישן אם הוא קיים
        try:
            df = pd.read_csv(f)
            df.columns = df.columns.str.strip()
            if 'user' in df.columns:
                df.rename(columns={'user': 'username'}, inplace=True)
                
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
            data_frames.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    final_df = pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()
    
    # 3. ניקוי נתונים (חשוב!)
    if not final_df.empty:
        final_df = final_df.drop_duplicates()
        cols = ['N', 'P', 'K']
        if all(c in final_df.columns for c in cols):
             final_df = final_df.dropna(subset=cols)
             
    return users_df, final_df
# Legacy sync_icons removed. Using sync_data.py implementation.


def prepare_crop_icon(icon_path, target_size=160):
    """Trim transparent padding and center the icon in a fixed square for crisp display."""
    if IS_STREAMLIT_CLOUD:
        return icon_path
    try:
        with Image.open(icon_path) as img:
            img = img.convert("RGBA")
            alpha = img.split()[-1]
            bbox = alpha.getbbox()
            if bbox:
                img = img.crop(bbox)

            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
            img.thumbnail((target_size, target_size), resample)

            canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
            x = (target_size - img.width) // 2
            y = (target_size - img.height) // 2
            canvas.paste(img, (x, y), img)
            return canvas
    except Exception:
        return icon_path


def image_file_to_data_uri(file_path, max_size=260):
    """Return a base64 data URI for the image, resized to max_size×max_size to keep the URI short."""
    if IS_STREAMLIT_CLOUD:
        return None
    try:
        img = Image.open(file_path).convert("RGBA")
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None


def cloud_asset_url(file_name):
    """Public GitHub raw URL so Streamlit Cloud renders images in the browser."""
    return f"{REPO_ASSET_BASE_URL}/{quote(str(file_name))}"


def render_crop_selection(crops, t):
    lang = st.session_state.get('lang', 'en')
    selected_crop = str(st.session_state.get('selected_crop', '')).strip().lower()
    crop_title_size = "2.45rem" if lang == 'he' else "3rem"

    st.markdown(
        f"<h2 style='text-align:center;color:#1F2937;margin-bottom:0.2rem;font-size:{crop_title_size};'>{t['select_crop_title']}</h2>",
        unsafe_allow_html=True,
    )
    crop_subtitle = "בחרו גידול כדי להיכנס ללוח הנתונים" if lang == 'he' else "Tap a crop to enter its dashboard"
    st.markdown(
        f"<p style='text-align:center;color:#475569;font-size:0.96rem;margin-top:-4px;margin-bottom:24px;font-weight:500'>{crop_subtitle}</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        [data-testid="column"] {
            background: #F8FAFC;
            border-radius: 14px;
            border: 1px solid rgba(15,23,42,0.10);
            box-shadow: 0 4px 16px rgba(15,23,42,0.07);
            padding: 18px 12px 14px 12px !important;
        }
        [data-testid="column"]:hover {
            box-shadow: 0 8px 24px rgba(23,54,92,0.14);
        }
        [data-testid="column"] button[kind="secondary"] {
            width: 100% !important;
            border: none !important;
            background: transparent !important;
            color: #1F2937 !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
        }
        [data-testid="column"] button[kind="secondary"]:hover {
            color: #17365C !important;
        }
        [data-testid="column"]:has(button[kind="primary"]) {
            background: #17365C !important;
            border-color: #17365C !important;
            box-shadow: 0 10px 28px rgba(23,54,92,0.22) !important;
        }
        [data-testid="column"] button[kind="primary"] {
            width: 100% !important;
            background: transparent !important;
            border: none !important;
            color: #FFFFFF !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 4, 1])
    with center:
        ncols = min(len(crops), 3)
        crop_cols = st.columns(ncols, gap="medium")
        for i, crop_name in enumerate(crops):
            crop_key = crop_name.lower()
            display_name = CROP_NAMES.get(lang, {}).get(crop_key, crop_name.capitalize())
            is_selected = crop_key == selected_crop
            btn_type = "primary" if is_selected else "secondary"

            icon_path = os.path.join(ASSETS_DIR, f"{crop_name}.png")
            if not os.path.exists(icon_path):
                for f in os.listdir(ASSETS_DIR):
                    if f.lower() == f"{crop_name}.png".lower():
                        icon_path = os.path.join(ASSETS_DIR, f)
                        break

            with crop_cols[i % ncols]:
                if IS_STREAMLIT_CLOUD:
                    icon_url = cloud_asset_url(os.path.basename(icon_path))
                    st.markdown(
                        f"<img src='{icon_url}' style='width:100%;height:auto;border-radius:10px;' alt='' />",
                        unsafe_allow_html=True,
                    )
                elif os.path.exists(icon_path):
                    st.image(icon_path, use_container_width=True)
                else:
                    st.markdown("<div style='font-size:3rem;text-align:center'>🌿</div>", unsafe_allow_html=True)
                if st.button(display_name, key=f"crop_pick_{crop_name}", use_container_width=True, type=btn_type):
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
    if os.path.exists(logo_path) and not IS_STREAMLIT_CLOUD:
        st.sidebar.image(logo_path, use_container_width=True)

# --- MAIN UI ---
def main():
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'he'
    
    # Global CSS
    direction = 'rtl' if st.session_state['lang'] == 'he' else 'ltr'
    font_url = "https://fonts.googleapis.com/css2?family=Assistant:wght@400;500;600;700;800&family=Heebo:wght@400;500;700;800&display=swap"
    base_font = 'Heebo' if st.session_state['lang'] == 'he' else 'Assistant'
    
    st.markdown(f"""
    <style>
    @import url('{font_url}');
    
    html, body, [class*="css"] {{
        font-family: '{base_font}', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
    
    /* Sidebar Styling - Flat Navy Premium */
    [data-testid="stSidebar"] {{
        background-color: #132E55;
        border-right: 1px solid #224572;
        padding-top: 0.75rem;
    }}
    [data-testid="stSidebar"] * {{
        color: #F8FAFC;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: #E2E8F0 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stImage"] img {{
        background: #FFFFFF;
        border-radius: 12px;
        padding: 8px;
        box-shadow: 0 8px 18px rgba(9, 20, 38, 0.28);
    }}

    .npk-brand-wrap {{
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 16px;
        padding: 14px 14px 10px 14px;
        margin-bottom: 16px;
        box-shadow: 0 8px 18px rgba(9, 20, 38, 0.30);
    }}
    .npk-brand-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(40px, 1fr));
        gap: 6px;
        margin-bottom: 8px;
    }}
    .npk-cell {{
        height: 52px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
    }}
    .npk-n {{ background: #79C874; }}
    .npk-p {{ background: #F1A46A; }}
    .npk-k {{ background: #F3D05E; }}
    .npk-brand-label {{
        background: #8BD4F2;
        border-radius: 10px;
        color: #0F172A;
        text-align: center;
        font-weight: 800;
        letter-spacing: 0.06em;
        font-size: 2rem;
        line-height: 1.2;
        padding: 4px 8px;
    }}
    
    /* Specific Sidebar Button Styling */
    [data-testid="stSidebar"] button {{
        background-color: transparent !important;
        color: #F8FAFC !important;
        border: 1px solid #37567E !important;
        border-radius: 12px !important;
        min-height: 42px;
        transition: all 0.2s ease;
    }}
    [data-testid="stSidebar"] button:hover {{
        background-color: #224572 !important;
        border-color: #8FB6DE !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 14px rgba(9, 20, 38, 0.35);
    }}

    /* Sidebar Separator */
    [data-testid="stSidebar"] hr {{
        border-color: #365983;
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
    /* Chemical Element Icons */
    .chemical-symbol {{
        width: 45px;
        height: 45px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 1.4rem;
        color: white;
        margin: 0 auto 5px auto; /* Center in card */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    .symbol-n {{ background: linear-gradient(135deg, #10B981, #059669); }} /* Emerald */
    .symbol-p {{ background: linear-gradient(135deg, #F59E0B, #D97706); }} /* Amber */
    .symbol-k {{ background: linear-gradient(135deg, #8B5CF6, #7C3AED); }} /* Violet */
    
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

    /* --- MOBILE OPTIMIZATION --- */
    @media only screen and (max-width: 768px) {{
        /* Reduce padding in cards */
        div.css-card {{
            padding: 1rem;
            margin-bottom: 15px;
        }}
        
        /* Smaller Headers */
        h1 {{
            font-size: 2rem !important;
        }}
        h2 {{
            font-size: 1.5rem !important;
        }}
        h3 {{
            font-size: 1.25rem !important;
        }}
        
        /* Adjust KPI values */
        .kpi-value {{
            font-size: 1.8rem;
        }}
        .kpi-container {{
            padding: 10px;
        }}
        
        /* Hide sidebar toggle if possible or adjust? Streamlit controls this mostly.
           We can adjust the main block padding though. */
        .block-container {{
            padding-top: 3rem !important; /* Reduce top padding */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        
        /* Make filters stack better */
        [data-testid="stPills"] {{
            justify-content: center;
        }}
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
        if IS_STREAMLIT_CLOUD:
            st.markdown(
                f"<img src='{cloud_asset_url('logo.png')}' style='width:100%;height:auto;margin-bottom:8px;' alt='NPK GILAT' />",
                unsafe_allow_html=True,
            )
            st.write("")
        elif os.path.exists(logo_path):
            try:
                st.image(logo_path, use_container_width=True)
            except TypeError:
                st.image(logo_path, use_column_width=True)
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
                        st.error("Could not load user database from secrets.toml.")
        st.stop()


    # --- DASHBOARD ---
    
    # 1. Load Data
    with st.spinner("Loading Data..."):
        _, main_data = load_data()

    if 'auto_data_sync_attempted' not in st.session_state:
        st.session_state['auto_data_sync_attempted'] = False

    if main_data is None or main_data.empty:
        if not st.session_state['auto_data_sync_attempted']:
            st.session_state['auto_data_sync_attempted'] = True
            with st.spinner("Syncing data from Google Drive..."):
                import concurrent.futures
                sync_ok = False
                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(sync_data.sync_data, creds)
                        result = future.result(timeout=30)
                        sync_ok = result[0] if isinstance(result, tuple) else bool(result)
                except concurrent.futures.TimeoutError:
                    sync_ok = False
                except Exception:
                    sync_ok = False

            if sync_ok:
                st.cache_data.clear()
                st.rerun()

        # Fallback UI only if auto-sync failed.
        st.warning("Could not load data automatically.")
        if st.button("Retry Data Sync", use_container_width=True, key='bootstrap_download_start'):
            with st.spinner("Retrying sync..."):
                try:
                    result = sync_data.sync_data(creds)
                    sync_ok = result[0] if isinstance(result, tuple) else bool(result)
                except Exception as sync_err:
                    sync_ok = False
                    st.error(f"Sync error: {sync_err}")

                if sync_ok:
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Sync failed. Please verify Google auth secrets.")
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

    pick_crop_param = st.query_params.get("pick_crop")
    if isinstance(pick_crop_param, list):
        pick_crop_param = pick_crop_param[0] if pick_crop_param else None
    if pick_crop_param:
        pick_crop_normalized = str(pick_crop_param).strip().lower()
        matched_crop = next((c for c in available_crops if str(c).strip().lower() == pick_crop_normalized), None)
        if matched_crop:
            st.session_state['selected_crop'] = matched_crop
            try:
                del st.query_params["pick_crop"]
            except Exception:
                pass
            st.rerun()

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
    if 'ID' in crop_data.columns:
        crop_data['record_key'] = crop_data['ID'].fillna('').astype(str)
        missing_record_key = crop_data['record_key'].eq('')
        crop_data.loc[missing_record_key, 'record_key'] = (
            crop_data.loc[missing_record_key, 'site'].fillna('').astype(str)
            + '_'
            + crop_data.loc[missing_record_key, 'sample'].fillna('').astype(str)
            + '_'
            + crop_data.loc[missing_record_key, 'date_fmt'].fillna('').astype(str)
        )
    else:
        crop_data['record_key'] = (
            crop_data['site'].fillna('').astype(str)
            + '_'
            + crop_data['sample'].fillna('').astype(str)
            + '_'
            + crop_data['date_fmt'].fillna('').astype(str)
        )

    crop_key = selected_crop.lower()
    display_title = CROP_NAMES.get(st.session_state['lang'], {}).get(crop_key, selected_crop.capitalize())
    crop_icon_path = os.path.join(ASSETS_DIR, f"{selected_crop}.png")
    if not os.path.exists(crop_icon_path):
        for f in os.listdir(ASSETS_DIR):
            if f.lower() == f"{selected_crop}.png".lower():
                crop_icon_path = os.path.join(ASSETS_DIR, f)
                break

    ui_text = {
        'dashboard': 'Dashboard' if st.session_state['lang'] == 'en' else 'לוח בקרה',
        'crop': 'Crop' if st.session_state['lang'] == 'en' else 'גידול',
        'account': 'Account' if st.session_state['lang'] == 'en' else 'חשבון',
        'refresh': 'Refresh' if st.session_state['lang'] == 'en' else 'רענון',
        'export': 'Export CSV' if st.session_state['lang'] == 'en' else 'ייצוא CSV',
        'analytics': 'Nutrient Analytics' if st.session_state['lang'] == 'en' else 'אנליטיקת יסודות הזנה',
        'samples_selected': 'Selected samples' if st.session_state['lang'] == 'en' else 'דגימות נבחרות',
        'target_zone': 'Target zone' if st.session_state['lang'] == 'en' else 'טווח יעד',
        'trend_line': 'Trend line' if st.session_state['lang'] == 'en' else 'קו מגמה',
        'sample_points': 'Sample points' if st.session_state['lang'] == 'en' else 'נקודות דגימה',
        'current_snapshot': 'Current snapshot' if st.session_state['lang'] == 'en' else 'תמונת מצב נוכחית',
        'range_ok': 'In target range' if st.session_state['lang'] == 'en' else 'בתוך הטווח',
        'range_out': 'Out of target range' if st.session_state['lang'] == 'en' else 'מחוץ לטווח',
        'records': 'records' if st.session_state['lang'] == 'en' else 'רשומות',
        'date_filter_label': 'Collection dates' if st.session_state['lang'] == 'en' else 'תאריכי דגימה',
        'plot_filter_label': 'Plot' if st.session_state['lang'] == 'en' else 'בחר חלקה',
        'plot_all': 'All Plots' if st.session_state['lang'] == 'en' else 'כל החלקות',
        'selection_empty': 'No data matches the selected filters.' if st.session_state['lang'] == 'en' else 'לא נמצאו נתונים עבור הסינון שנבחר.',
        'view_history': 'History' if st.session_state['lang'] == 'en' else 'היסטוריה',
        'clear_focus': 'Clear' if st.session_state['lang'] == 'en' else 'נקה',
        'status_ready': 'Ready for review' if st.session_state['lang'] == 'en' else 'מוכן לסקירה',
        'status_focus': 'Focused sample' if st.session_state['lang'] == 'en' else 'דגימה במיקוד',
        'raw_table': 'Raw data' if st.session_state['lang'] == 'en' else 'נתונים גולמיים'
    }

    palette = {
        'N': '#16A34A',
        'P': '#F59E0B',
        'K': '#7C3AED',
        'slate': '#475569',
        'teal': '#0F766E',
        'danger': '#DC2626'
    }
    element_labels = {
        'N': 'Nitrogen' if st.session_state['lang'] == 'en' else 'חנקן',
        'P': 'Phosphorus' if st.session_state['lang'] == 'en' else 'זרחן',
        'K': 'Potassium' if st.session_state['lang'] == 'en' else 'אשלגן'
    }

    icon_uri = None
    if os.path.exists(crop_icon_path):
        icon_uri = cloud_asset_url(os.path.basename(crop_icon_path)) if IS_STREAMLIT_CLOUD else image_file_to_data_uri(crop_icon_path, max_size=320)
    crop_icon_markup = f"<img src='{icon_uri}' alt='' class='dashboard-crop-hero-icon' />" if icon_uri else "<div class='dashboard-crop-hero-fallback'>🌿</div>"

    dashboard_css = """
    <style>
    .block-container {
        padding-top: 2.5rem !important;
        padding-left: 2.4rem !important;
        padding-right: 2.4rem !important;
        padding-bottom: 2.5rem !important;
    }
    .stApp {
        background: linear-gradient(180deg, #F8FBFF 0%, #EFF4F9 100%);
    }
    section[data-testid="stSidebar"] {
        width: 19rem !important;
        min-width: 19rem !important;
        max-width: 19rem !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.07) !important;
        padding: 0.65rem 0.75rem;
    }
    div[data-testid="stMetric"] {
        background: transparent;
        border-radius: 12px;
    }
    .dashboard-hero-card {
        display: flex;
        align-items: center;
        gap: 22px;
        padding: 10px 6px;
    }
    .dashboard-crop-hero-media {
        width: 124px;
        min-width: 124px;
        height: 124px;
        border-radius: 24px;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid rgba(148, 163, 184, 0.18);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
    }
    .dashboard-crop-hero-icon {
        max-width: 78%;
        height: auto;
        display: block;
    }
    .dashboard-crop-hero-fallback {
        font-size: 3rem;
    }
    .dashboard-eyebrow {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #64748B;
        margin-bottom: 0.35rem;
    }
    .dashboard-title {
        font-size: clamp(2.2rem, 4vw, 3.7rem);
        line-height: 1;
        font-weight: 800;
        color: #0F172A;
        margin: 0;
    }
    .dashboard-title-he {
        font-size: clamp(1.9rem, 3.1vw, 2.85rem);
        line-height: 1.05;
    }
    .dashboard-subtitle {
        color: #64748B;
        font-size: 0.98rem;
        margin-top: 0.45rem;
        max-width: 56rem;
    }
    .dashboard-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem;
        margin-top: 1rem;
    }
    .dashboard-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.55rem 0.9rem;
        border-radius: 999px;
        background: #F8FAFC;
        border: 1px solid rgba(148, 163, 184, 0.22);
        color: #334155;
        font-size: 0.86rem;
        font-weight: 600;
    }
    .dashboard-chip-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #0F766E;
    }
    .dashboard-kpi-card {
        background: #FFFFFF;
        border-radius: 15px;
        border-top: 4px solid #CBD5E1;
        padding: 1.15rem 1rem 1.05rem 1rem;
        min-height: 168px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        text-align: center;
    }
    .dashboard-kpi-label {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #64748B;
        text-align: center;
    }
    .dashboard-kpi-value {
        margin-top: 0.82rem;
        font-size: 2rem;
        line-height: 1;
        font-weight: 800;
        color: #0F172A;
        text-align: center;
    }
    .dashboard-kpi-meta {
        margin-top: 0.6rem;
        color: #64748B;
        font-size: 0.9rem;
        text-align: center;
        display: none;
    }
    .dashboard-kpi-status {
        margin-top: 0.95rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        color: #334155;
        font-size: 0.86rem;
        font-weight: 600;
        width: 100%;
    }
    .dashboard-status-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        display: inline-block;
    }
    .dashboard-panel-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.15rem;
    }
    .dashboard-chart-head {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin-bottom: 0.9rem;
    }
    .dashboard-chart-dot {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        flex-shrink: 0;
    }
    .dashboard-chart-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0;
    }
    .dashboard-selection-note {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.25rem;
    }
    .dashboard-selection-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 700;
        color: #64748B;
        margin-bottom: 0.4rem;
    }
    .dashboard-selection-value {
        font-size: 1.02rem;
        font-weight: 700;
        color: #0F172A;
    }
    .dashboard-inline-actions {
        display: flex;
        gap: 0.6rem;
        width: 100%;
    }
    .dashboard-inline-actions > div {
        flex: 1;
    }
    .dashboard-sidebar-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 15px;
        padding: 0.85rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 22px rgba(7, 14, 24, 0.24);
    }
    .dashboard-sidebar-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.7rem 0.8rem;
        border-radius: 12px;
        color: #E2E8F0;
        margin-bottom: 0.45rem;
        border-left: 3px solid transparent;
    }
    .dashboard-sidebar-item.active {
        background: rgba(143, 182, 222, 0.16);
        border-left-color: #8FB6DE;
        color: #FFFFFF;
    }
    .dashboard-sidebar-icon {
        width: 18px;
        height: 18px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: currentColor;
        flex-shrink: 0;
    }
    .dashboard-sidebar-icon svg {
        width: 18px;
        height: 18px;
        stroke: currentColor;
        fill: none;
        stroke-width: 1.9;
        stroke-linecap: round;
        stroke-linejoin: round;
    }
    .dashboard-sidebar-label {
        font-size: 0.92rem;
        font-weight: 700;
    }
    .dashboard-sidebar-meta {
        color: #BFDBFE;
        font-size: 0.82rem;
        margin-top: -0.1rem;
    }
    [data-testid="stSidebar"] button {
        border-radius: 999px !important;
        border: 1px solid rgba(143, 182, 222, 0.34) !important;
        background: rgba(255, 255, 255, 0.06) !important;
        color: #F8FAFC !important;
        font-weight: 700 !important;
        min-height: 40px;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] button:hover {
        background: rgba(143, 182, 222, 0.16) !important;
        border-color: #8FB6DE !important;
    }
    .stButton button,
    .stDownloadButton button {
        border-radius: 999px !important;
        font-weight: 700 !important;
        min-height: 40px;
    }
    @media only screen and (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        section[data-testid="stSidebar"] {
            width: auto !important;
            min-width: auto !important;
            max-width: none !important;
        }
        .dashboard-hero-card {
            flex-direction: column;
            align-items: flex-start;
        }
        .dashboard-crop-hero-media {
            width: 100px;
            min-width: 100px;
            height: 100px;
        }
        .dashboard-selection-note {
            flex-direction: column;
            align-items: flex-start;
        }
    }
    /* Data Table Styling */
    .stDataFrame {
        width: 100% !important;
    }
    .stDataFrame [data-testid="stDataFrameTable"] {
        overflow-y: auto !important;
        max-height: 600px;
    }
    /* Sticky Header for Data Tables */
    thead {
        position: sticky;
        top: 0;
        background: linear-gradient(180deg, #F1F5F9 0%, #E8EFF7 100%) !important;
        z-index: 10;
    }
    thead th {
        background: transparent !important;
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        padding: 0.9rem 0.8rem !important;
        border-bottom: 2px solid #CBD5E1 !important;
        white-space: nowrap;
    }
    tbody td {
        padding: 0.7rem 0.8rem !important;
        border-bottom: 1px solid #E2E8F0 !important;
    }
    tbody tr:hover {
        background: #F8FAFC !important;
    }
    tbody tr:last-child td {
        border-bottom: none !important;
    }
    </style>
    """
    st.markdown(dashboard_css, unsafe_allow_html=True)

    dashboard_icon_svg = "<svg viewBox='0 0 24 24'><path d='M3 12l9-8 9 8'></path><path d='M5 10v10h14V10'></path></svg>"
    crop_icon_svg = "<svg viewBox='0 0 24 24'><path d='M12 21V9'></path><path d='M12 12c-4 0-7-3-7-7 4 0 7 3 7 7Z'></path><path d='M12 15c4 0 7-3 7-7-4 0-7 3-7 7Z'></path></svg>"
    account_icon_svg = "<svg viewBox='0 0 24 24'><path d='M20 21a8 8 0 0 0-16 0'></path><circle cx='12' cy='8' r='4'></circle></svg>"

    with st.sidebar:
        st.markdown(
            f"""
            <div class='dashboard-sidebar-card'>
                <div class='dashboard-sidebar-item active'>
                    <span class='dashboard-sidebar-icon'>{dashboard_icon_svg}</span>
                    <div>
                        <div class='dashboard-sidebar-label'>{ui_text['dashboard']}</div>
                        <div class='dashboard-sidebar-meta'>{display_title}</div>
                    </div>
                </div>
                <div class='dashboard-sidebar-item'>
                    <span class='dashboard-sidebar-icon'>{crop_icon_svg}</span>
                    <div>
                        <div class='dashboard-sidebar-label'>{ui_text['crop']}</div>
                        <div class='dashboard-sidebar-meta'>{display_title}</div>
                    </div>
                </div>
                <div class='dashboard-sidebar-item'>
                    <span class='dashboard-sidebar-icon'>{account_icon_svg}</span>
                    <div>
                        <div class='dashboard-sidebar-label'>{ui_text['account']}</div>
                        <div class='dashboard-sidebar-meta'>{st.session_state['user']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(f"↻ {ui_text['refresh']}", key='sidebar_refresh_btn', use_container_width=True):
            with st.spinner("Syncing data & icons from Drive..."):
                success = sync_data.sync_data(creds)
                if success:
                    st.success("Sync Complete!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Sync Failed. Check logs.")

        if st.button(f"↺ {t['change_crop']}", key='sidebar_change_crop_btn', use_container_width=True):
            st.session_state['selected_crop'] = None
            st.rerun()

        if st.button(f"⇥ {t['logout']}", key='sidebar_logout_btn', use_container_width=True):
            st.session_state['user'] = None
            st.session_state['selected_crop'] = None
            st.rerun()

        st.markdown("---")
        st.caption("v1.1.0")

    all_dates = sorted(crop_data['date'].unique()) if 'date' in crop_data.columns else []
    formatted_dates = [pd.to_datetime(d).strftime('%d/%m/%y') for d in all_dates]
    date_map = dict(zip(formatted_dates, all_dates))

    with st.container(border=True):
        st.markdown(
            f"""
            <div class='dashboard-hero-card'>
                <div class='dashboard-crop-hero-media'>{crop_icon_markup}</div>
                <div>
                    <div class='dashboard-eyebrow'>{ui_text['dashboard']}</div>
                    <h1 class='dashboard-title{' dashboard-title-he' if st.session_state['lang'] == 'he' else ''}'>{display_title}</h1>
                    <div class='dashboard-subtitle'>{t['welcome']} {st.session_state['user']}</div>
                    <div class='dashboard-chip-row'>
                        <span class='dashboard-chip'><span class='dashboard-chip-dot'></span>{ui_text['current_snapshot']}</span>
                        <span class='dashboard-chip'>{len(crop_data)} {t['samples_count'].lower() if st.session_state['lang'] == 'en' else t['samples_count']}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        filter_col, toggle_col = st.columns([6, 2])
        with filter_col:
            st.markdown(f"<div class='dashboard-panel-title'>{ui_text['date_filter_label']}</div>", unsafe_allow_html=True)
        with toggle_col:
            use_all_dates = st.toggle(t['select_all'], value=True, key='dashboard_use_all_dates')

        if use_all_dates:
            selected_dates_fmt = formatted_dates
            st.caption(f"{t['select_all']} • {len(formatted_dates)}")
        else:
            try:
                selected_dates_fmt = st.pills(
                    t['select_dates'],
                    options=formatted_dates,
                    selection_mode='multi',
                    label_visibility='collapsed',
                    key='dashboard_date_pills'
                )
            except AttributeError:
                selected_dates_fmt = st.multiselect(
                    t['select_dates'],
                    options=formatted_dates,
                    default=formatted_dates,
                    label_visibility='collapsed',
                    key='dashboard_date_multiselect'
                )

        st.markdown("<hr style='margin:0.6rem 0 0.8rem 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)
        plot_label_col, plot_select_col = st.columns([2, 5])
        with plot_label_col:
            st.markdown(f"<div class='dashboard-panel-title' style='padding-top:0.55rem;'>{ui_text['plot_filter_label']}</div>", unsafe_allow_html=True)
        with plot_select_col:
            all_plots = sorted(crop_data['site'].dropna().unique().tolist()) if 'site' in crop_data.columns else []
            plot_options = [ui_text['plot_all']] + all_plots
            selected_plot = st.selectbox(
                t['select_plot'],
                options=plot_options,
                index=0 if len(all_plots) != 1 else 1,
                label_visibility='collapsed',
                key='dashboard_plot_filter',
                disabled=(len(all_plots) <= 1)
            )

    if not selected_dates_fmt:
        filtered_df = pd.DataFrame(columns=crop_data.columns)
    else:
        selected_timestamps = [date_map[fmt] for fmt in selected_dates_fmt]
        filtered_df = crop_data[crop_data['date'].isin(selected_timestamps)].copy()

    if selected_plot != ui_text['plot_all'] and 'site' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['site'] == selected_plot].copy()

    csv_export = filtered_df.sort_values('date').to_csv(index=False).encode('utf-8-sig') if not filtered_df.empty else b''

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        action_info_col, action_button_col = st.columns([5, 3])
        with action_info_col:
            st.markdown(f"<div class='dashboard-panel-title'>{ui_text['samples_selected']}: {len(filtered_df)}</div>", unsafe_allow_html=True)
        with action_button_col:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"↻ {ui_text['refresh']}", key='header_refresh_btn', use_container_width=True):
                    with st.spinner("Syncing data & icons from Drive..."):
                        success = sync_data.sync_data(creds)
                        if success:
                            st.success("Sync Complete!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Sync Failed. Check logs.")
            with btn_col2:
                st.download_button(
                    label=f"⤓ {ui_text['export']}",
                    data=csv_export,
                    file_name=f"{selected_crop}_filtered_data.csv",
                    mime='text/csv',
                    disabled=filtered_df.empty,
                    use_container_width=True,
                    key='header_export_btn'
                )

    def render_status_dot(ok, neutral=False):
        color = '#94A3B8' if neutral else ('#16A34A' if ok else '#DC2626')
        return f"<span class='dashboard-status-dot' style='background:{color};'></span>"

    def render_kpi_card(col, label, value, meta, color, ok=True, neutral=False):
        status_label = ui_text['status_ready'] if neutral else (ui_text['range_ok'] if ok else ui_text['range_out'])
        with col:
            st.markdown(
                f"""
                <div class='dashboard-kpi-card' style='border-top-color:{color};'>
                    <div class='dashboard-kpi-label'>{label}</div>
                    <div class='dashboard-kpi-value'>{value}</div>
                    <div class='dashboard-kpi-meta'>{meta}</div>
                    <div class='dashboard-kpi-status'>{render_status_dot(ok, neutral)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    def prepare_dataframe_for_display(df):
        """Format dataframe for display: select whitelisted columns and format date."""
        # Whitelisted columns in preferred order
        whitelisted_cols = ['sample', 'date', 'crop', 'part', 'site', 'soil', 'N', 'P', 'K', 'username', 'variety']
        # Select only columns that exist in the dataframe
        available_cols = [col for col in whitelisted_cols if col in df.columns]
        display_df = df[available_cols].copy()
        
        # Format date column to YYYY-MM-DD if it exists
        if 'date' in display_df.columns:
            display_df['date'] = pd.to_datetime(display_df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        return display_df

    if filtered_df.empty:
        st.warning(ui_text['selection_empty'])
    else:
        mean_n = filtered_df['N'].mean()
        mean_p = filtered_df['P'].mean()
        mean_k = filtered_df['K'].mean()
        n_ok = OPTIMAL_RANGES['N'][0] <= mean_n <= OPTIMAL_RANGES['N'][1]
        p_ok = OPTIMAL_RANGES['P'][0] <= mean_p <= OPTIMAL_RANGES['P'][1]
        k_ok = OPTIMAL_RANGES['K'][0] <= mean_k <= OPTIMAL_RANGES['K'][1]
        all_opt = (
            filtered_df['N'].between(OPTIMAL_RANGES['N'][0], OPTIMAL_RANGES['N'][1])
            & filtered_df['P'].between(OPTIMAL_RANGES['P'][0], OPTIMAL_RANGES['P'][1])
            & filtered_df['K'].between(OPTIMAL_RANGES['K'][0], OPTIMAL_RANGES['K'][1])
        )
        pct_optimal = (all_opt.sum() / len(filtered_df)) * 100 if len(filtered_df) else 0

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5, gap='large')
        render_kpi_card(k1, element_labels['N'], f"{mean_n:.2f}", f"ppm • {len(filtered_df)} {ui_text['records']}", palette['N'], n_ok)
        render_kpi_card(k2, element_labels['P'], f"{mean_p:.3f}", f"ppm • {len(filtered_df)} {ui_text['records']}", palette['P'], p_ok)
        render_kpi_card(k3, element_labels['K'], f"{mean_k:.2f}", f"ppm • {len(filtered_df)} {ui_text['records']}", palette['K'], k_ok)
        render_kpi_card(k4, t['kpi_total'], f"{len(filtered_df)}", f"{t['kpi_selected']}: {len(filtered_df)}", palette['slate'], True, neutral=True)
        render_kpi_card(k5, t['kpi_optimal_pct'], f"{pct_optimal:.0f}%", t['kpi_in_range'], palette['teal'], pct_optimal >= 70)

    config = {'displaylogo': False}

    if not filtered_df.empty:
        import plotly.graph_objects as go

        if 'selected_record_key' not in st.session_state:
            st.session_state['selected_record_key'] = None
        if 'history_dialog_open' not in st.session_state:
            st.session_state['history_dialog_open'] = False
        if 'plot_selection_nonce' not in st.session_state:
            st.session_state['plot_selection_nonce'] = 0

        def text_series(df, column_name):
            if column_name in df.columns:
                return df[column_name].fillna('').astype(str)
            return pd.Series([''] * len(df), index=df.index, dtype='object')

        def get_linked_history(record_row):
            sample_value = str(record_row.get('sample', '')).strip()
            history_df = crop_data[crop_data['sample'].fillna('').astype(str).str.strip() == sample_value].copy()
            return history_df.sort_values('date')

        selected_record = None
        selected_history_df = pd.DataFrame()
        selected_record_key = st.session_state.get('selected_record_key')
        if selected_record_key:
            record_matches = crop_data[crop_data['record_key'].astype(str) == str(selected_record_key)].copy()
            if not record_matches.empty:
                selected_record = record_matches.sort_values('date').iloc[-1]
                selected_history_df = get_linked_history(selected_record)
            else:
                st.session_state['selected_record_key'] = None
                st.session_state['history_dialog_open'] = False

        def build_customdata(df):
            return np.stack([
                text_series(df, 'record_key'),
                text_series(df, 'site'),
                text_series(df, 'sample'),
                text_series(df, 'date_fmt'),
                text_series(df, 'ID')
            ], axis=-1)

        def extract_record_key(event):
            if event and 'selection' in event and 'points' in event['selection']:
                points = event['selection']['points']
                if points:
                    customdata = points[0].get('customdata')
                    if isinstance(customdata, (list, tuple, np.ndarray)) and len(customdata) > 0:
                        return str(customdata[0])
            return None

        def plot_element_composed(element, color, limits, chart_key):
            min_lim, max_lim = limits
            base_df = filtered_df.sort_values('date').copy()
            if base_df.empty:
                return None

            trend_df = base_df.groupby('date', as_index=False)[element].mean().sort_values('date')
            current_key = str(st.session_state.get('selected_record_key') or '')
            selected_mask = base_df['record_key'].astype(str) == current_key
            in_range_mask = base_df[element].between(min_lim, max_lim)

            fig = go.Figure()
            fig.add_hrect(
                y0=min_lim,
                y1=max_lim,
                fillcolor=color,
                opacity=0.15,
                line_width=0,
                layer='below'
            )
            fig.add_trace(go.Scatter(
                x=trend_df['date'],
                y=trend_df[element],
                mode='lines',
                name=ui_text['trend_line'],
                line=dict(color=color, width=3.2, shape='spline'),
                hovertemplate=f"<b>{ui_text['trend_line']}</b><br><b>{t['axis_date']}:</b> %{{x|%d/%m/%y}}<br><b>{element}:</b> %{{y:.3f}}<extra></extra>"
            ))
            fig.add_trace(go.Scatter(
                x=base_df['date'],
                y=base_df[element],
                mode='markers',
                name=ui_text['sample_points'],
                customdata=build_customdata(base_df),
                marker=dict(
                    color=np.where(in_range_mask, color, palette['danger']),
                    size=np.where(selected_mask, 15, 10),
                    opacity=np.where(selected_mask, 1.0, 0.82),
                    symbol=np.where(selected_mask, 'diamond', 'circle'),
                    line=dict(color='white', width=1.4)
                ),
                hovertemplate=(
                    f"<b>{element_labels[element]}</b><br>"
                    f"<b>{t['axis_date']}:</b> %{{customdata[3]}}<br>"
                    f"<b>Value:</b> %{{y:.3f}}<br>"
                    f"<b>Plot ID:</b> %{{customdata[1]}}<br>"
                    f"<b>{t['history_sample']}:</b> %{{customdata[2]}}<extra></extra>"
                )
            ))
            if selected_record is not None:
                fig.add_vline(x=selected_record['date'], line_width=2, line_dash='dot', line_color='#0F172A')

            fig.update_layout(
                margin=dict(l=50, r=8, t=8, b=18),
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                clickmode='event+select',
                dragmode='pan',
                showlegend=False,
                hovermode='closest',
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickformat='%d/%m/%y', title=None),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title=None)
            )

            return st.plotly_chart(
                fig,
                use_container_width=True,
                config=config,
                on_select='rerun',
                selection_mode=['points'],
                key=f"{chart_key}_{st.session_state['plot_selection_nonce']}"
            )

        @st.dialog(t['history_title'], width='large')
        def render_history_dialog(record_row, history_df):
            st.caption(t['history_scope'])

            meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
            meta_col1.metric(t['history_site'], str(record_row.get('site', '')))
            meta_col2.metric(t['history_sample'], str(record_row.get('sample', '')))
            meta_col3.metric(t['history_date'], str(record_row.get('date_fmt', '')))
            meta_col4.metric(t['history_id'], str(record_row.get('ID', '')))

            st.markdown(f"#### {t['history_record']}")
            record_details = record_row.to_frame().T.copy()
            preferred_columns = [col for col in ['date_fmt', 'site', 'sample', 'ID', 'part', 'variety', 'contact', 'N', 'P', 'K'] if col in record_details.columns]
            st.dataframe(record_details[preferred_columns], use_container_width=True, hide_index=True)

            st.markdown(f"#### {t['history_logs']}")
            if history_df.empty:
                st.info(t['history_none'])
            else:
                def render_history_mineral_plot(nutrient, color, limits, plot_key):
                    min_lim, max_lim = limits
                    dialog_fig = go.Figure()
                    dialog_fig.add_hrect(y0=min_lim, y1=max_lim, fillcolor=color, opacity=0.15, line_width=0)
                    dialog_fig.add_trace(go.Scatter(
                        x=history_df['date'],
                        y=history_df[nutrient],
                        mode='lines+markers',
                        name=nutrient,
                        line=dict(color=color, width=2.5, shape='spline'),
                        marker=dict(size=7)
                    ))
                    dialog_fig.add_vline(x=record_row['date'], line_width=2, line_dash='dot', line_color='#0F172A')
                    dialog_fig.update_layout(
                        title=nutrient,
                        height=280,
                        margin=dict(l=50, r=10, t=34, b=30),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        showlegend=False,
                        xaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickformat='%d/%m/%y', autorange=True),
                        yaxis=dict(showgrid=True, gridcolor='#E2E8F0', autorange=True, title=nutrient)
                    )
                    st.plotly_chart(dialog_fig, use_container_width=True, config=config, key=plot_key)

                n_col, p_col, k_col = st.columns(3)
                with n_col:
                    render_history_mineral_plot('N', palette['N'], OPTIMAL_RANGES['N'], 'history_n_plot')
                with p_col:
                    render_history_mineral_plot('P', palette['P'], OPTIMAL_RANGES['P'], 'history_p_plot')
                with k_col:
                    render_history_mineral_plot('K', palette['K'], OPTIMAL_RANGES['K'], 'history_k_plot')

                history_columns = [col for col in ['date_fmt', 'site', 'sample', 'ID', 'N', 'P', 'K', 'part', 'variety', 'contact'] if col in history_df.columns]
                st.dataframe(
                    history_df.sort_values('date', ascending=False)[history_columns],
                    use_container_width=True,
                    hide_index=True
                )

            if st.button(t['history_close'], key='history_close_btn', use_container_width=True):
                st.session_state['history_dialog_open'] = False
                st.rerun()

        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            sel_info_col, sel_action_col = st.columns([5, 2])
            with sel_info_col:
                if selected_record is not None:
                    point_label = f"{selected_record.get('site', '')} • {selected_record.get('date_fmt', '')} • {selected_record.get('ID', '')}"
                    st.markdown(
                        f"""
                        <div class='dashboard-selection-note'>
                            <div>
                                <div class='dashboard-selection-title'>{ui_text['status_focus']}</div>
                                <div class='dashboard-selection-value'>{point_label}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class='dashboard-selection-note'>
                            <div>
                                <div class='dashboard-selection-title'>{ui_text['current_snapshot']}</div>
                                <div class='dashboard-selection-value'>{t['history_hint']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.caption(t['sample_selection_help'])
            with sel_action_col:
                if selected_record is not None:
                    st.markdown("<div class='dashboard-inline-actions'>", unsafe_allow_html=True)
                    focus_btn_col1, focus_btn_col2 = st.columns(2, gap='small')
                    with focus_btn_col1:
                        if st.button(f"⟳ {ui_text['view_history']}", key='open_history_again', use_container_width=True):
                            st.session_state['history_dialog_open'] = True
                            st.rerun()
                    with focus_btn_col2:
                        if st.button(f"✕ {ui_text['clear_focus']}", key='reset_record_selection', use_container_width=True):
                            st.session_state['selected_record_key'] = None
                            st.session_state['history_dialog_open'] = False
                            st.session_state['plot_selection_nonce'] += 1
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        st.markdown(f"### {ui_text['analytics']}")

        chart_col1, chart_col2, chart_col3 = st.columns(3, gap='large')
        with chart_col1:
            with st.container(border=True):
                st.markdown(
                    f"<div class='dashboard-chart-head'><span class='dashboard-chart-dot' style='background:{palette['N']};'></span><h4 class='dashboard-chart-title'>{element_labels['N']} (N)</h4></div>",
                    unsafe_allow_html=True,
                )
                event_n = plot_element_composed('N', palette['N'], OPTIMAL_RANGES['N'], 'chart_npk_n')
        with chart_col2:
            with st.container(border=True):
                st.markdown(
                    f"<div class='dashboard-chart-head'><span class='dashboard-chart-dot' style='background:{palette['P']};'></span><h4 class='dashboard-chart-title'>{element_labels['P']} (P)</h4></div>",
                    unsafe_allow_html=True,
                )
                event_p = plot_element_composed('P', palette['P'], OPTIMAL_RANGES['P'], 'chart_npk_p')
        with chart_col3:
            with st.container(border=True):
                st.markdown(
                    f"<div class='dashboard-chart-head'><span class='dashboard-chart-dot' style='background:{palette['K']};'></span><h4 class='dashboard-chart-title'>{element_labels['K']} (K)</h4></div>",
                    unsafe_allow_html=True,
                )
                event_k = plot_element_composed('K', palette['K'], OPTIMAL_RANGES['K'], 'chart_npk_k')

        new_record_key = extract_record_key(event_n) or extract_record_key(event_p) or extract_record_key(event_k)
        if new_record_key and new_record_key != st.session_state.get('selected_record_key'):
            st.session_state['selected_record_key'] = new_record_key
            st.session_state['history_dialog_open'] = True
            st.rerun()

        if selected_record is not None and st.session_state.get('history_dialog_open'):
            render_history_dialog(selected_record, selected_history_df)

    with st.expander(f"{ui_text['raw_table']} / {t['show_raw_data']}"):
        # Export button above the table
        export_col1, export_col2 = st.columns([4, 1])
        with export_col2:
            st.download_button(
                label="⤓ CSV",
                data=csv_export,
                file_name=f"{selected_crop}_data_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                disabled=filtered_df.empty,
                use_container_width=True,
                key='raw_table_export_btn'
            )
        
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        
        # Display formatted dataframe with selected columns only
        if not filtered_df.empty:
            display_df = prepare_dataframe_for_display(filtered_df)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data to display")

if __name__ == "__main__":
    main()
