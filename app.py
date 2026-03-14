import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from PIL import Image

# --- DYNAMIC PATH SETUP ---
# This ensures the code finds folders regardless of whose computer it is on
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
    pixel_y = (1 - v) * 1024  # Y is flipped because image origin is top-left
    return pixel_x, pixel_y

# --- DATA INGESTION ---
@st.cache_data
def load_all_data(root_path):
    all_frames = []
    day_folders = ["February_10", "February_11", "February_12", "February_13", "February_14"]
    
    for day in day_folders:
        day_path = os.path.join(root_path, day)
        if not os.path.exists(day_path):
            continue
            
        for filename in os.listdir(day_path):
            file_path = os.path.join(day_path, filename)
            try:
                # Read parquet (works even for .nakama-0 files)
                df = pd.read_parquet(file_path)
                
                # Decode event column from bytes
                if 'event' in df.columns:
                    df['event'] = df['event'].apply(
                        lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
                    )
                
                # Identify bots: numeric IDs are bots, UUIDs are humans
                df['is_bot'] = df['user_id'].apply(lambda x: x.isdigit())
                df['day'] = day
                all_frames.append(df)
            except:
                continue
                
    return pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()

# --- APP UI ---
st.title("🎯 LILA BLACK: Player Journey Visualizer")

if not os.path.exists(DATA_FOLDER):
    st.error(f"Data folder not found at {DATA_FOLDER}. Please check your repo structure.")
else:
    df_raw = load_all_data(DATA_FOLDER)
    
    # Sidebar Filters
    st.sidebar.header("Global Filters")
    selected_map = st.sidebar.selectbox("Select Map", options=list(MAP_CONFIG.keys()))
    selected_day = st.sidebar.multiselect("Filter by Day", options=df_raw['day'].unique(), default=df_raw['day'].unique())
    
    # Filter data based on sidebar
    df_filtered = df_raw[(df_raw['map_id'] == selected_map) & (df_raw['day'].isin(selected_day))]
    
    match_list = df_filtered['match_id'].unique()
    selected_match = st.sidebar.selectbox("Focus on Match ID", options=match_list)
    
    show_bots = st.sidebar.checkbox("Show Bots", value=True)
    
    # Final match dataframe
    df_match = df_filtered[df_filtered['match_id'] == selected_match]
    if not show_bots:
        df_match = df_match[df_match['is_bot'] == False]

    # Apply Coordinate Mapping
    conf = MAP_CONFIG[selected_map]
    df_match['px_x'], df_match['px_y'] = world_to_pixel(df_match['x'], df_match['z'], conf)

    # Visualization
    fig = go.Figure()

    # Add Map Background
    if os.path.exists(conf['img']):
        img = Image.open(conf['img'])
        fig.add_layout_image(
            dict(source=img, x=0, sx=1024, y=0, sy=1024, 
                 xref="x", yref="y", sizing="stretch", opacity=1, layer="below")
        )

    # Plot Player Paths
    for user in df_match['user_id'].unique():
        user_data = df_match[df_match['user_id'] == user]
        is_bot = user_data['is_bot'].iloc[0]
        fig.add_trace(go.Scatter(
            x=user_data['px_x'], y=user_data['px_y'],
            mode='lines',
            line=dict(width=2, dash='dot' if is_bot else 'solid'),
            name=f"{'Bot' if is_bot else 'Player'} {user[:5]}"
        ))

    # Plot Events (Kills, Deaths, Loot)
    event_markers = {'Kill': 'green', 'Killed': 'red', 'Loot': 'gold', 'KilledByStorm': 'purple'}
    for ev, color in event_markers.items():
        ev_df = df_match[df_match['event'] == ev]
        if not ev_df.empty:
            fig.add_trace(go.Scatter(
                x=ev_df['px_x'], y=ev_df['px_y'],
                mode='markers', marker=dict(color=color, size=10, symbol='x'),
                name=ev
            ))

    fig.update_xaxes(range=[0, 1024], visible=False)
    fig.update_yaxes(range=[1024, 0], visible=False) # Flipped for top-down
    fig.update_layout(width=900, height=900)

    st.plotly_chart(fig, use_container_width=True)