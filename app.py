import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from PIL import Image
from datetime import datetime

# --- CONFIGURATION & CONSTANTS ---
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473, "img": "minimaps/AmbroseValley_Minimap.png"},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290, "img": "minimaps/GrandRift_Minimap.png"},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500, "img": "minimaps/Lockdown_Minimap.jpg"}
}

st.set_page_config(page_title="LILA BLACK Level Design Tool", layout="wide")

# --- HELPER: COORDINATE MAPPING ---
def world_to_pixel(x, z, config):
    u = (x - config['origin_x']) / config['scale']
    v = (z - config['origin_z']) / config['scale']
    pixel_x = u * 1024
    pixel_y = (1 - v) * 1024  # Invert Y for top-left origin
    return pixel_x, pixel_y

# --- DATA LOADING ---
@st.cache_data
def load_match_data(folder_path):
    all_data = []
    # Supporting the structure Feb 10-14
    days = ["February_10", "February_11", "February_12", "February_13", "February_14"]
    
    for day in days:
        path = os.path.join(folder_path, day)
        if not os.path.exists(path): continue
        
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            try:
                df = pd.read_parquet(file_path)
                # Decode event bytes to string
                df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
                # Identify bots by user_id
                df['is_bot'] = df['user_id'].apply(lambda x: x.isdigit())
                all_data.append(df)
            except Exception as e:
                continue
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

# --- UI LAYOUT ---
st.title("🎯 LILA BLACK: Player Journey Visualizer")
st.markdown("A specialized tool for Level Designers to analyze map flow and combat zones. [cite: 17, 42]")

# Hardcoded data path - replace with your local path or upload logic
DATA_PATH = "player_data" 

if not os.path.exists(DATA_PATH):
    st.error(f"Data folder '{DATA_PATH}' not found. Please ensure the player_data zip is extracted here.")
else:
    df_raw = load_match_data(DATA_PATH)

    # --- SIDEBAR FILTERS [cite: 34, 88] ---
    st.sidebar.header("Filters")
    selected_map = st.sidebar.selectbox("Select Map", options=list(MAP_CONFIG.keys()))
    
    # Filter by Map first to narrow down matches
    df_map = df_raw[df_raw['map_id'] == selected_map]
    
    unique_matches = df_map['match_id'].unique()
    selected_match = st.sidebar.selectbox("Select Specific Match", options=unique_matches)
    
    show_bots = st.sidebar.checkbox("Show Bots", value=True) [cite: 32, 86]
    show_heatmap = st.sidebar.checkbox("Overlay Heatmap (Kills/Deaths)", value=False) [cite: 36, 90]

    # --- DATA PROCESSING ---
    # Apply filters
    df_match = df_map[df_map['match_id'] == selected_match]
    if not show_bots:
        df_match = df_match[df_match['is_bot'] == False]

    # Map Coordinates [cite: 31, 85]
    config = MAP_CONFIG[selected_map]
    df_match['px_x'], df_match['px_y'] = world_to_pixel(df_match['x'], df_match['z'], config)

    # --- TIMELINE SLIDER [cite: 35, 89] ---
    max_ts = int(df_match['ts'].max())
    time_range = st.sidebar.slider("Match Timeline (ms)", 0, max_ts, max_ts)
    df_filtered = df_match[df_match['ts'] <= time_range]

    # --- VISUALIZATION [cite: 31, 33] ---
    fig = go.Figure()

    # 1. Add Minimap Background
    img_path = config['img']
    if os.path.exists(img_path):
        img = Image.open(img_path)
        fig.add_layout_image(
            dict(source=img, x=0, sx=1024, y=0, sy=1024, 
                 xref="x", yref="y", sizing="stretch", opacity=1, layer="below")
        )

    # 2. Add Player Paths 
    for user in df_filtered['user_id'].unique():
        user_data = df_filtered[df_filtered['user_id'] == user]
        is_bot = user_data['is_bot'].iloc[0]
        
        fig.add_trace(go.Scatter(
            x=user_data['px_x'], y=user_data['px_y'],
            mode='lines',
            line=dict(width=2, dash='dot' if is_bot else 'solid'),
            name=f"{'Bot' if is_bot else 'Player'}: {user[:8]}",
            hoverinfo='name'
        ))

    # 3. Add Event Markers [cite: 33, 87]
    events_to_show = ['Kill', 'Killed', 'Loot', 'KilledByStorm', 'BotKill', 'BotKilled']
    df_events = df_filtered[df_filtered['event'].isin(events_to_show)]
    
    event_colors = {
        'Kill': 'green', 'Killed': 'red', 'Loot': 'gold', 
        'KilledByStorm': 'purple', 'BotKill': 'lightgreen', 'BotKilled': 'orange'
    }

    for event_type in df_events['event'].unique():
        ev_data = df_events[df_events['event'] == event_type]
        fig.add_trace(go.Scatter(
            x=ev_data['px_x'], y=ev_data['px_y'],
            mode='markers',
            marker=dict(size=10, color=event_colors.get(event_type, 'white'), symbol='x'),
            name=event_type
        ))

    # 4. Heatmap Overlay (Optional) [cite: 36]
    if show_heatmap:
        fig.add_trace(go.Histogram2dContour(
            x=df_map['px_x'], y=df_map['px_y'],
            colorscale='Hot', ncontours=20, opacity=0.4, showscale=False
        ))

    # Update Layout
    fig.update_xaxes(range=[0, 1024], showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(range=[1024, 0], showgrid=False, zeroline=False, visible=False) # Inverted Y
    fig.update_layout(width=1000, height=1000, margin=dict(l=0, r=0, t=0, b=0))

    st.plotly_chart(fig, use_container_width=True)

    # --- INSIGHTS PREVIEW ---
    st.subheader("Quick Match Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Players", len(df_match[df_match['is_bot'] == False]['user_id'].unique()))
    col2.metric("Total Bots", len(df_match[df_match['is_bot'] == True]['user_id'].unique()))
    col3.metric("Deaths in Storm", len(df_match[df_match['event'] == 'KilledByStorm']))