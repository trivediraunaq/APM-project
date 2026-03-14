import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from PIL import Image

# --- DYNAMIC PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "player_data")
MAPS_FOLDER = os.path.join(BASE_DIR, "minimaps")

# --- CONFIGURATION & CONSTANTS ---
MAP_CONFIG = {
    "AmbroseValley": {
        "scale": 900, "origin_x": -370, "origin_z": -473, 
        "img": os.path.join(MAPS_FOLDER, "AmbroseValley_Minimap.png")
    },
    "GrandRift": {
        "scale": 581, "origin_x": -290, "origin_z": -290, 
        "img": os.path.join(MAPS_FOLDER, "GrandRift_Minimap.png")
    },
    "Lockdown": {
        "scale": 1000, "origin_x": -500, "origin_z": -500, 
        "img": os.path.join(MAPS_FOLDER, "Lockdown_Minimap.jpg")
    }
}

st.set_page_config(page_title="LILA BLACK Level Design Tool", layout="wide")

# --- COORDINATE MAPPING LOGIC ---
def world_to_pixel(x, z, config):
    u = (x - config['origin_x']) / config['scale']
    v = (z - config['origin_z']) / config['scale']
    pixel_x = u * 1024
    pixel_y = (1 - v) * 1024  
    return pixel_x, pixel_y

# --- DATA INGESTION ---
@st.cache_data
def load_all_data(root_path):
    all_frames = []
    day_folders = ["February_10", "February_11", "February_12", "February_13", "February_14"]
    
    for day in day_folders:
        day_path = os.path.join(root_path, day)
        if not os.path.exists(day_path): continue
            
        for filename in os.listdir(day_path):
            file_path = os.path.join(day_path, filename)
            try:
                df = pd.read_parquet(file_path)
                if 'event' in df.columns:
                    df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
                
                df['is_bot'] = df['user_id'].apply(lambda x: x.isdigit())
                df['day'] = day
                all_frames.append(df)
            except: continue
                
    return pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()

# --- APP UI ---
st.title("🎯 LILA BLACK: Player Journey Visualizer")

if not os.path.exists(DATA_FOLDER):
    st.error(f"Data folder not found at {DATA_FOLDER}. Ensure your repo structure is correct.")
else:
    df_raw = load_all_data(DATA_FOLDER)
    
    # Sidebar Filters
    st.sidebar.header("Global Filters")
    selected_map = st.sidebar.selectbox("Select Map", options=list(MAP_CONFIG.keys()))
    
    # Filter by Map
    df_map = df_raw[df_raw['map_id'] == selected_map]
    
    # Sidebar Filters for Day and Match
    selected_day = st.sidebar.multiselect("Filter by Day", options=df_map['day'].unique(), default=df_map['day'].unique())
    df_filtered_days = df_map[df_map['day'].isin(selected_day)]
    
    match_list = df_filtered_days['match_id'].unique()
    selected_match = st.sidebar.selectbox("Focus on Match ID", options=match_list)
    
    st.sidebar.markdown("---")
    st.sidebar.header("Visual Toggles")
    show_bots = st.sidebar.checkbox("Show Bots", value=True)
    show_heatmap = st.sidebar.checkbox("Show Heatmap (Global)", value=False)

    # Prepare specific match data
    df_match = df_filtered_days[df_filtered_days['match_id'] == selected_match].copy()
    if not show_bots:
        df_match = df_match[df_match['is_bot'] == False]

    # --- THE TIMELINE SLIDER (BULLETPROOF VERSION) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Match Playback")

    if not df_match.empty:
        # 1. Force 'ts' to be numeric, turning errors into 'NaN'
        df_match['ts'] = pd.to_numeric(df_match['ts'], errors='coerce')
        
        # 2. Drop rows where 'ts' is NaN
        df_match = df_match.dropna(subset=['ts'])
        
        if not df_match.empty:
            # 3. Use a safe min/max calculation
            min_ts = int(df_match['ts'].min())
            max_ts = int(df_match['ts'].max())
            
            if max_ts > min_ts:
                time_range = st.sidebar.slider(
                    "Current Match Time (ms)", 
                    min_value=min_ts, 
                    max_value=max_ts, 
                    value=max_ts, 
                    step=100
                )
            else:
                time_range = max_ts
                st.sidebar.info("Single-event match.")
            
            # Apply filter
            df_display = df_match[df_match['ts'] <= time_range].copy()
        else:
            st.sidebar.warning("Selected match has no valid timestamps.")
            df_display = pd.DataFrame()
    else:
        st.sidebar.warning("No data for these filters.")
        df_display = pd.DataFrame()

    # Apply Coordinates
    conf = MAP_CONFIG[selected_map]
    if not df_display.empty:
        df_display['px_x'], df_display['px_y'] = world_to_pixel(df_display['x'], df_display['z'], conf)

    # --- UI LAYOUT IMPROVEMENTS ---
    # Create two columns: one for the map (Large) and one for stats (Small)
    col_map, col_stats = st.columns([3, 1])

    with col_map:
        # --- VISUALIZATION ---
        # --- STABILIZED VIEWPORT ---
        
        # 1. Inject CSS to force the chart container to a specific height
        # This prevents the "shrinking" effect during browser zooming
        st.markdown("""
            <style>
            .stPlotlyChart {
                height: 800px !important;
                width: 800px !important;
                margin-left: auto;
                margin-right: auto;
            }
            </style>
        """, unsafe_allow_html=True)

        fig = go.Figure()

        # Add Minimap Background
        if os.path.exists(conf['img']):
            img = Image.open(conf['img'])
            fig.add_layout_image(
                dict(
                    source=img,
                    xref="x", yref="y",
                    x=0, y=0,
                    sizex=1024, sizey=1024,
                    sizing="stretch",
                    opacity=1,
                    layer="below"
                )
            )

        # ... [Keep your Heatmap, Paths, and Events code here] ...

        # LOCK THE COORDINATES
        fig.update_xaxes(range=[0, 1024], visible=False, fixedrange=True)
        fig.update_yaxes(range=[1024, 0], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)

        fig.update_layout(
            # We set these to fixed pixels to match the CSS
            width=800,
            height=800,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            autosize=False # CRITICAL: Tells Plotly NOT to listen to the browser resize
        )

        # Render with use_container_width=False to prevent Streamlit interference
        st.plotly_chart(fig, use_container_width=False, config={'staticPlot': False, 'responsive': False})