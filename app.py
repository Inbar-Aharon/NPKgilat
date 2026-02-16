import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import auth_utils
import setup_auth
import os
import glob
import sync_data

# --- ASSETS PATH ---
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# --- CONFIGURATION ---
st.set_page_config(page_title="Grower Nutrition Monitor", layout="wide", page_icon="🌿")
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
        "distribution": "Distribution"
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
        "trend_selector": "בחר חלקה להצגת מגמה:",
        "axis_date": "תאריך",
        "distribution": "התפלגות"
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
            # Card styling wrapper
            st.markdown(f"""
            <div style="
                background-color: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                text-align: center;
                margin-bottom: 20px;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            """, unsafe_allow_html=True)
            
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
                st.image(icon_path, use_container_width=True)
            else:
                st.write("🌿") # Simple emoji placeholder if missing
            
            # Button
            if st.button(crop_name.capitalize(), key=f"btn_{crop_name}", use_container_width=True):
                st.session_state['selected_crop'] = crop_name
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)


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
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.image(logo_path, width=200)

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
    </style>
    """, unsafe_allow_html=True)

    # --- SHOW LOGO ---
    render_logo()

    creds = auth_utils.get_creds()
    # ... (Auth logic remains same) ...
    if not creds:
        with st.spinner("Initiating Google Authentication... Check your browser."):
            try:
                setup_auth.setup()
                creds = auth_utils.get_creds() # Reload after setup
            except Exception as e:
                st.error(f"Authentication failed: {e}")

    # Sync icons on startup if we have creds
    # Sync icons on startup if we have creds
    if creds and 'icons_synced' not in st.session_state:
        with st.spinner("Syncing assets from Drive... (Optimized)"):
            try:
                sync_data.sync_icons_only(creds)
                st.session_state['icons_synced'] = True
            except Exception as e:
                print(f"Icon sync warning: {e}")

    if not creds:
        st.warning("Authentication failed or cancelled. Please check console logs or run `python3 setup_auth.py` manually.")
        st.stop()
        
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    if 'selected_crop' not in st.session_state:
        st.session_state['selected_crop'] = None

    t = TRANSLATIONS[st.session_state['lang']]

    # --- SIDEBAR LANGUAGE SELECTION ---
    with st.sidebar:
        # Language Toggle
        lang_choice = st.radio("Language / שפה", ["English", "עברית"], index=1 if st.session_state['lang'] =='he' else 0, horizontal=True)
        if (lang_choice == "עברית" and st.session_state['lang'] != 'he') or (lang_choice == "English" and st.session_state['lang'] != 'en'):
            st.session_state['lang'] = 'he' if lang_choice == "עברית" else 'en'
            t = TRANSLATIONS[st.session_state['lang']] # Update immediately
            st.rerun()
        
        # Reload/Sync Button
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
        st.title(t['login_title'])
        with st.form("login_form"):
            username = st.text_input(t['username'])
            password = st.text_input(t['password'], type="password")
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
    
    # Filter out non-crop items (like 'logo', 'icon', etc if they accidentally get in data or similar checks)
    # The user specifically mentioned 'logo' appearing as a crop.
    # This might happen if there is a CSV with 'logo' as crop name, OR if the previous code was inferring crops from filenames.
    # The current code reads 'crop' column from CSVs.
    # If 'logo.png' is in assets, it shouldn't be in the CSV 'crop' column unless data is wrong.
    # Let's inspect data... but regardless, let's safe guard.
    excluded_crops = ['logo', 'icon', 'unknown', 'nan', 'none']
    available_crops = [
        c for c in available_crops 
        if str(c).lower() not in excluded_crops and pd.notna(c)
    ]
    
    # 2. Crop Selection Screen
    if st.session_state['selected_crop'] is None:
        with st.sidebar:
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
    with st.sidebar:
        st.subheader("Controls")
        st.info(f"User: {st.session_state['user']}")
        
        st.markdown("### Navigation")
        if st.button(t['change_crop'], use_container_width=True):
            st.session_state['selected_crop'] = None
            st.rerun()
        if st.button(t['logout'], use_container_width=True):
            st.session_state['user'] = None
            st.session_state['selected_crop'] = None
            st.rerun()
        st.markdown("---")


    # --- HEADER & FILTERS ---
    # Container for Header and Top Level Filters
    with st.container():
        # Using a unified container style for the top bar
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        
        # Header Row
        col_header, col_sample = st.columns([3, 1])
        with col_header:
            st.title(f"{selected_crop.capitalize()}")
            st.caption(f"Grower Nutrition Monitor • {t['welcome']} {st.session_state['user']}")
            
        with col_sample:
            # Placeholder for sample count, updated later
            pass

        st.markdown("---")

        # Filters Row
        f_col1, f_col2 = st.columns([1, 3])
        
        with f_col1:
            # Toggle for All Dates
            use_all_dates = st.checkbox("Select All Dates / כל התאריכים", value=True)
        
        with f_col2:
             # Date Multiselect
            all_dates = sorted(crop_data['date'].unique())
            formatted_dates = [pd.to_datetime(d).strftime('%d/%m/%y') for d in all_dates]
            date_map = dict(zip(formatted_dates, all_dates))

            if use_all_dates:
                selected_dates_fmt = formatted_dates
                st.multiselect("Select Dates / בחר תאריכים", options=formatted_dates, default=formatted_dates, disabled=True, label_visibility="collapsed")
            else:
                selected_dates_fmt = st.multiselect("Select Dates / בחר תאריכים", options=formatted_dates, default=formatted_dates, label_visibility="collapsed")

        st.markdown('</div>', unsafe_allow_html=True) # End Top Card


    # Filter Data Logic
    if not selected_dates_fmt:
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
        k_col1, k_col2, k_col3, k_col4 = st.columns(4)
        
        def render_kpi(col, label, value, sub_label, icon, color_class=""):
            with col:
                st.markdown(f"""
                <div class="css-card kpi-container">
                    <div style="font-size: 1.5rem; margin-bottom: 5px;">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub_label}</div>
                </div>
                """, unsafe_allow_html=True)

        render_kpi(k_col1, t['kpi_optimal_pct'], f"{pct_optimal:.0f}%", t['kpi_in_range'], "🏆")
        render_kpi(k_col2, f"{t['kpi_avg']} P", f"{mean_p:.3f}", f"{t['kpi_target']}: {OPTIMAL_RANGES['P'][0]}-{OPTIMAL_RANGES['P'][1]}", "🌱")
        render_kpi(k_col3, f"{t['kpi_avg']} N", f"{mean_n:.2f}", f"{t['kpi_target']}: {OPTIMAL_RANGES['N'][0]}-{OPTIMAL_RANGES['N'][1]}", "🌿")
        render_kpi(k_col4, t['kpi_total'], f"{len(filtered_df)}", f"{t['kpi_selected']}: {len(filtered_df)}", "📊")

    
    # --- VISUALIZATIONS GRID ---
    
    # Helper for Plotly config
    config = {'displayModeBar': False}

    if not filtered_df.empty:
        import plotly.graph_objects as go
        
        # --- ROW 1: DISTRIBUTIONS ---
        st.markdown("### Distributions / התפלגות")
        
        # Wrap all distributions in one card-like visuals or separate cards? 
        # Separate cards for each nutrient usually looks cleaner on wide screens.
        
        d_col1, d_col2, d_col3 = st.columns(3)
        
        def plot_jitter_modern(element, limits):
            min_lim, max_lim = limits
            vals = filtered_df[element]
            dates = filtered_df['date']
            dates_fmt = filtered_df['date_fmt']
            is_in = vals.between(min_lim, max_lim)
            
            fig = go.Figure()
            
            # Optimal
            if not vals[is_in].empty:
                fig.add_trace(go.Scatter(
                    x=dates[is_in], y=vals[is_in],
                    mode='markers',
                    marker=dict(color='#10B981', size=10, opacity=0.8, line=dict(width=1, color='white')), # Modern Green
                    name=t['plot_optimal'],
                    text=dates_fmt[is_in], hovertemplate='%{text}: %{y:.2f}'
                ))
            
            # Out
            if not vals[~is_in].empty:
                fig.add_trace(go.Scatter(
                    x=dates[~is_in], y=vals[~is_in],
                    mode='markers',
                    marker=dict(color='#EF4444', size=10, opacity=0.8, line=dict(width=1, color='white')), # Modern Red/Orange
                    name=t['plot_out_range'],
                    text=dates_fmt[~is_in], hovertemplate='%{text}: %{y:.2f}'
                ))

            # Limit Lines
            fig.add_hline(y=min_lim, line_width=1, line_dash="dash", line_color="#10B981", opacity=0.6)
            fig.add_hline(y=max_lim, line_width=1, line_dash="dash", line_color="#10B981", opacity=0.6)

            fig.update_layout(
                title=dict(text=f"{element} {t['distribution']}", font=dict(size=14, color="#374151")),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=40, b=20),
                height=320,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(showgrid=True, gridcolor='#F3F4F6'),
                yaxis=dict(showgrid=True, gridcolor='#F3F4F6')
            )
            return fig

        with d_col1:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_jitter_modern('N', OPTIMAL_RANGES['N']), use_container_width=True, config=config)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with d_col2:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_jitter_modern('P', OPTIMAL_RANGES['P']), use_container_width=True, config=config)
            st.markdown('</div>', unsafe_allow_html=True)

        with d_col3:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_jitter_modern('K', OPTIMAL_RANGES['K']), use_container_width=True, config=config)
            st.markdown('</div>', unsafe_allow_html=True)


        # --- ROW 2: TRENDS ---
        st.markdown("### Trends / מגמות")
        
        # Trend Controls in a smaller separate card or just above? 
        # Let's put it above the trend grid.
        trend_sites = sorted(filtered_df['site'].unique())
        
        # Use a container for alignment
        with st.container():
            col_sel, _ = st.columns([1, 3])
            with col_sel:
                selected_trend_site = st.selectbox(t['trend_selector'], trend_sites, key='trend_site_sel')

        t_col1, t_col2, t_col3 = st.columns(3)

        def plot_trend_modern(element, color, limits, site):
             s_data = filtered_df[filtered_df['site'] == site].sort_values('date')
             s_data_agg = s_data.groupby('date')[element].mean().reset_index()
             
             fig = go.Figure()
             fig.add_trace(go.Scatter(
                 x=s_data_agg['date'], y=s_data_agg[element],
                 mode='lines+markers',
                 line=dict(color=color, width=3, shape='spline'), # Spline for smoother look
                 marker=dict(size=8, color='white', line=dict(width=2, color=color)),
                 name=site
             ))
             
             # Limits
             fig.add_hline(y=limits[1], line_width=1, line_dash="dash", line_color="#10B981")
             fig.add_hline(y=limits[0], line_width=1, line_dash="dash", line_color="#10B981")
             
             fig.update_layout(
                 title=dict(text=f"{element} - {site}", font=dict(size=14, color="#374151")),
                 height=300,
                 margin=dict(l=20, r=20, t=40, b=20),
                 plot_bgcolor='white',
                 paper_bgcolor='white',
                 xaxis=dict(showgrid=True, gridcolor='#F3F4F6', tickformat="%d/%m"),
                 yaxis=dict(showgrid=True, gridcolor='#F3F4F6')
             )
             return fig

        with t_col1:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_trend_modern('N', '#3B82F6', OPTIMAL_RANGES['N'], selected_trend_site), use_container_width=True, config=config) # Blue
            st.markdown('</div>', unsafe_allow_html=True)

        with t_col2:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_trend_modern('P', '#F59E0B', OPTIMAL_RANGES['P'], selected_trend_site), use_container_width=True, config=config) # Amber/Orange
            st.markdown('</div>', unsafe_allow_html=True)

        with t_col3:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_trend_modern('K', '#10B981', OPTIMAL_RANGES['K'], selected_trend_site), use_container_width=True, config=config) # Green
            st.markdown('</div>', unsafe_allow_html=True)

            
    # Raw Data Expander
    with st.expander("Show Raw Data Table / הצג נתונים גולמיים"):
        st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
