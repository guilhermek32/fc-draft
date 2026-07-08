import streamlit as st
import pandas as pd
import random
import io
import html as html_lib
import os
import json
import base64
import urllib.request

# Set page configurations
st.set_page_config(
    page_title="EA FC 26 Draft Board",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Custom Styling -----------------
st.markdown("""
<style>
/* App-wide background and font adjustments */
.stApp {
    background-color: #0b140f;
    color: #e0e0e0;
    font-family: 'Outfit', 'Inter', sans-serif;
}

/* Glassmorphism panel container */
.glass-panel {
    background: rgba(18, 30, 22, 0.65);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(46, 125, 50, 0.25);
    border-radius: 16px;
    padding: 25px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
}

/* Section headers */
.glow-text {
    color: #00c853;
    text-shadow: 0 0 10px rgba(0, 200, 83, 0.3);
    font-weight: 800;
    letter-spacing: 0.5px;
}

.gold-text {
    color: #ffd700;
    text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    font-weight: 800;
    letter-spacing: 0.5px;
}

/* Custom badges */
.custom-badge {
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    display: inline-block;
    margin-right: 8px;
}
.badge-gold {
    background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%);
    color: #000;
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}
.badge-green {
    background: linear-gradient(135deg, #00c853 0%, #007e33 100%);
    color: #fff;
    box-shadow: 0 2px 8px rgba(0, 200, 83, 0.3);
}
.badge-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #eee;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

/* Pitch Visualizer Styles */
.pitch-container {
    background: #0d2315;
    background-image: linear-gradient(135deg, #12301c 0%, #08120a 100%);
    border: 3px solid #2e7d32;
    border-radius: 20px;
    padding: 35px 15px;
    position: relative;
    box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    margin: 20px auto;
    max-width: 850px;
}
.pitch-bg-lines {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    border: 2px solid rgba(255,255,255,0.15);
    margin: 15px;
    border-radius: 16px;
}
.pitch-half-line {
    position: absolute;
    top: 50%; left: 15px; right: 15px;
    height: 2px;
    background: rgba(255,255,255,0.15);
}
.pitch-center-circle {
    position: absolute;
    top: 50%; left: 50%;
    width: 140px; height: 140px;
    border: 2px solid rgba(255,255,255,0.15);
    border-radius: 50%;
    transform: translate(-50%, -50%);
}
.pitch-penalty-area-top {
    position: absolute;
    top: 15px; left: 50%;
    width: 320px; height: 100px;
    border: 2px solid rgba(255,255,255,0.15);
    border-top: none;
    transform: translateX(-50%);
}
.pitch-penalty-area-bottom {
    position: absolute;
    bottom: 15px; left: 50%;
    width: 320px; height: 100px;
    border: 2px solid rgba(255,255,255,0.15);
    border-bottom: none;
    transform: translateX(-50%);
}
.pitch-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 30px 0;
    position: relative;
    z-index: 10;
}

/* Card Styling - Inspired by EA Sports Ultimate Team */
.player-card {
    background: rgba(25, 35, 28, 0.9);
    border: 2px solid #cd7f32;
    border-radius: 12px;
    width: 100px;
    height: 150px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    position: relative;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    user-select: none;
}
.player-card:hover {
    transform: translateY(-8px) scale(1.06);
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    z-index: 50;
}
.card-rating-pos {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 11px;
    font-weight: bold;
    color: #fff;
}
.card-rating {
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 800;
}
.card-pos {
    font-weight: bold;
}
.card-face {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
}
.card-name {
    font-size: 10px;
    font-weight: 800;
    color: #fff;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    letter-spacing: -0.2px;
}
.card-club {
    font-size: 8px;
    color: #bbb;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
}
.empty-card {
    background: rgba(255, 255, 255, 0.03);
    border: 2px dashed rgba(255, 255, 255, 0.15);
    box-shadow: none;
}
.empty-card:hover {
    transform: none;
    box-shadow: none;
}
.empty-pos {
    font-size: 13px;
    font-weight: 800;
    color: rgba(255,255,255,0.3);
    margin-top: 40px;
}
.empty-plus {
    font-size: 18px;
    color: rgba(255,255,255,0.15);
    margin-bottom: 25px;
}

/* Card Themes */
.card-gold {
    border-color: #ffe082;
    background-image: linear-gradient(180deg, rgba(38, 30, 10, 0.95) 0%, rgba(18, 14, 5, 0.95) 100%);
    box-shadow: 0 4px 15px rgba(255, 224, 130, 0.15);
}
.card-gold .card-rating {
    background: #ffe082;
    color: #000;
}
.card-gold .card-pos {
    color: #ffe082;
}

.card-silver {
    border-color: #cfd8dc;
    background-image: linear-gradient(180deg, rgba(25, 27, 28, 0.95) 0%, rgba(12, 13, 14, 0.95) 100%);
    box-shadow: 0 4px 15px rgba(207, 216, 220, 0.1);
}
.card-silver .card-rating {
    background: #cfd8dc;
    color: #000;
}
.card-silver .card-pos {
    color: #cfd8dc;
}

.card-bronze {
    border-color: #b0bec5;
    background-image: linear-gradient(180deg, rgba(28, 23, 20, 0.95) 0%, rgba(14, 11, 10, 0.95) 100%);
}
.card-bronze .card-rating {
    background: #b0bec5;
    color: #000;
}
.card-bronze .card-pos {
    color: #b0bec5;
}

/* Card details on hover/stat sheets */
.stat-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 8px;
    text-align: center;
}
.stat-val {
    font-size: 18px;
    font-weight: 800;
    color: #ffd700;
}
.stat-lbl {
    font-size: 10px;
    color: #aaa;
    text-transform: uppercase;
}


</style>
""", unsafe_allow_html=True)

# ----------------- Configuration Constants -----------------
FORMATIONS = {
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "CDM", "CDM", "CAM", "LM", "RM", "ST", "ST"],
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LM", "RM", "ST"],
    "5-3-2": ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "CM", "ST", "ST"],
    "4-5-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CAM", "CAM", "LM", "RM", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"],
    "4-1-2-1-2": ["GK", "LB", "CB", "CB", "RB", "CDM", "LM", "RM", "CAM", "ST", "ST"],
    "4-3-2-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LF", "ST", "RF"],
}

# Mapping of positions for flexible filters
FLEXIBLE_POSITIONS = {
    "GK": ["GK"],
    "LB": ["LB", "LWB", "CB"],
    "LWB": ["LWB", "LB", "LM"],
    "CB": ["CB", "LB", "RB", "CDM"],
    "RB": ["RB", "RWB", "CB"],
    "RWB": ["RWB", "RB", "RM"],
    "CDM": ["CDM", "CM", "CB"],
    "CM": ["CM", "CDM", "CAM"],
    "CAM": ["CAM", "CM", "CF", "LM", "RM"],
    "LM": ["LM", "LW", "LWB", "CM"],
    "RM": ["RM", "RW", "RWB", "CM"],
    "LW": ["LW", "LM", "LF", "RW"],
    "RW": ["RW", "RM", "RF", "LW"],
    "ST": ["ST", "CF"],
    "CF": ["CF", "ST", "CAM", "LF", "RF"],
    "LF": ["LF", "LW", "CF", "ST"],
    "RF": ["RF", "RW", "CF", "ST"],
    "SUB": []
}

# ----------------- Data Loading (Cached) -----------------
@st.cache_data
def load_data(filepath="FC26_20250921.csv"):
    try:
        df = pd.read_csv(filepath, low_memory=False)
        # Standard cleaning
        df['player_id'] = df['player_id'].astype(str)
        df['short_name'] = df['short_name'].fillna("Unknown Player").astype(str)
        df['long_name'] = df['long_name'].fillna("Unknown Player").astype(str)
        df['player_positions'] = df['player_positions'].fillna("SUB").astype(str)
        df['overall'] = pd.to_numeric(df['overall'], errors='coerce').fillna(50).astype(int)
        df['club_name'] = df['club_name'].fillna("Free Agent").astype(str)
        df['nationality_name'] = df['nationality_name'].fillna("Unknown").astype(str)
        df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(25).astype(int)
        df['player_face_url'] = df['player_face_url'].fillna("https://cdn.sofifa.net/players/notfound_0_120.png").astype(str)
        
        # Parse stats
        for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic']:
            df[stat] = pd.to_numeric(df[stat], errors='coerce').fillna(50).astype(int)
            
        for gk_stat in ['goalkeeping_diving', 'goalkeeping_handling', 'goalkeeping_kicking', 
                        'goalkeeping_positioning', 'goalkeeping_reflexes', 'goalkeeping_speed']:
            df[gk_stat] = pd.to_numeric(df[gk_stat], errors='coerce').fillna(50).astype(int)
            
        # Parse position list
        df['pos_list'] = df['player_positions'].apply(lambda x: [p.strip().upper() for p in x.split(',') if p.strip()])
        return df
    except Exception as e:
        st.error(f"Error loading CSV data file: {str(e)}")
        # Return fallback empty dataframe with correct columns
        return pd.DataFrame(columns=[
            'player_id', 'short_name', 'long_name', 'player_positions', 'overall', 
            'club_name', 'nationality_name', 'age', 'player_face_url', 'pos_list',
            'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic'
        ])

# ----------------- Session Persistence Helper Functions -----------------
STATE_FILE = "draft_state.json"

def save_session_state():
    """Serialize and save the current draft state to disk."""
    state_to_save = {
        "phase": st.session_state.get("phase", "setup"),
        "participants": st.session_state.get("participants", []),
        "team_names": st.session_state.get("team_names", {}),
        "formations": st.session_state.get("formations", {}),
        "bench_slots": st.session_state.get("bench_slots", 5),
        "bans": st.session_state.get("bans", {}),
        "ban_submissions": st.session_state.get("ban_submissions", {}),
        "banned_player_ids": list(st.session_state.get("banned_player_ids", set())),
        "drafted_players": st.session_state.get("drafted_players", {}),
        "draft_sequence": st.session_state.get("draft_sequence", []),
        "current_pick_index": st.session_state.get("current_pick_index", 0),
        "draft_history": st.session_state.get("draft_history", [])
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state_to_save, f, indent=4)
    except Exception as e:
        pass

def load_session_state():
    """Deserialize and load saved draft state from disk if it exists."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                
            # Populate st.session_state from the loaded state
            st.session_state.phase = state.get("phase", "setup")
            st.session_state.participants = state.get("participants", [])
            st.session_state.team_names = state.get("team_names", {})
            st.session_state.formations = state.get("formations", {})
            st.session_state.bench_slots = state.get("bench_slots", 5)
            st.session_state.bans = state.get("bans", {})
            st.session_state.ban_submissions = state.get("ban_submissions", {})
            st.session_state.banned_player_ids = set(state.get("banned_player_ids", []))
            st.session_state.drafted_players = state.get("drafted_players", {})
            st.session_state.draft_sequence = state.get("draft_sequence", [])
            st.session_state.current_pick_index = state.get("current_pick_index", 0)
            st.session_state.draft_history = state.get("draft_history", [])
            return True
        except Exception as e:
            pass
    return False

# ----------------- Player Image Caching Helper Functions -----------------
IMAGE_CACHE_DIR = "image_cache"

def get_cached_player_image_base64(player_id, url):
    """Retrieve player image locally or download it, then return its base64 Data URI."""
    if not os.path.exists(IMAGE_CACHE_DIR):
        os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
        
    local_path = os.path.join(IMAGE_CACHE_DIR, f"{player_id}.png")
    
    # Download image if not cached locally
    if not os.path.exists(local_path):
        try:
            # Use request with a User-Agent to bypass potential CDN hotlink blocks
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                with open(local_path, "wb") as f:
                    f.write(response.read())
        except Exception as e:
            # If download fails, return a default transparent placeholder or direct URL as fallback
            fallback_local = os.path.join(IMAGE_CACHE_DIR, "notfound.png")
            if not os.path.exists(fallback_local):
                try:
                    fallback_req = urllib.request.Request(
                        "https://cdn.sofifa.net/players/notfound_0_120.png",
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(fallback_req, timeout=5) as fallback_response:
                        with open(fallback_local, "wb") as f:
                            f.write(fallback_response.read())
                except Exception:
                    # In case of complete network failure, return empty transparent pixel Data URI
                    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            local_path = fallback_local

    # Read the local file and convert it to Base64 data URI
    try:
        with open(local_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        # Fallback to direct URL if file read fails
        return url

@st.cache_data(show_spinner=False)
def get_player_image_base64_cached(player_id, url):
    """Cached wrapper around the image resolver to keep Base64 URIs in memory."""
    return get_cached_player_image_base64(player_id, url)

# Initialize Data
df_players = load_data()

# ----------------- Helper Functions -----------------
def get_formation_slots(formation):
    raw_slots = FORMATIONS.get(formation, ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"])
    slots = []
    counts = {}
    for pos in raw_slots:
        counts[pos] = counts.get(pos, 0) + 1
    
    current_counts = {}
    for pos in raw_slots:
        if counts[pos] > 1:
            current_counts[pos] = current_counts.get(pos, 0) + 1
            slots.append(f"{pos} {current_counts[pos]}")
        else:
            slots.append(pos)
    return slots

def get_base_position(slot_name):
    return slot_name.split()[0].upper()

def search_players(query="", position_filter=None, filter_mode="Strict"):
    filtered_df = df_players.copy()
    
    # Get all drafted player IDs
    drafted_ids = []
    for participant_squad in st.session_state.drafted_players.values():
        for player in participant_squad.values():
            drafted_ids.append(player['player_id'])
            
    # Combine banned and drafted IDs to exclude
    all_excluded = set(drafted_ids + list(st.session_state.banned_player_ids))
    if all_excluded:
        filtered_df = filtered_df[~filtered_df['player_id'].isin(all_excluded)]
        
    # Position filter
    if position_filter and position_filter != "SUB":
        if filter_mode == "Strict":
            filtered_df = filtered_df[filtered_df['pos_list'].apply(lambda pos: position_filter in pos)]
        else:
            # Flexible filtering
            allowed = FLEXIBLE_POSITIONS.get(position_filter, [position_filter])
            filtered_df = filtered_df[filtered_df['pos_list'].apply(lambda pos: any(p in pos for p in allowed))]
            
    # Text Query filter
    if query:
        query = query.lower()
        filtered_df = filtered_df[
            filtered_df['short_name'].str.lower().str.contains(query) | 
            filtered_df['long_name'].str.lower().str.contains(query) | 
            filtered_df['club_name'].str.lower().str.contains(query) | 
            filtered_df['nationality_name'].str.lower().str.contains(query)
        ]
    else:
        # Default fallback: Only show Overall >= 75 players to keep selectboxes snappy
        filtered_df = filtered_df[filtered_df['overall'] >= 75]
        
    return filtered_df.sort_values(by='overall', ascending=False)

def auto_draft_remaining(filter_mode="Flexible"):
    curr_idx = st.session_state.current_pick_index
    seq = st.session_state.draft_sequence
    
    # Construct current list of already drafted player IDs to prevent duplicates
    drafted_ids = set()
    for participant_squad in st.session_state.drafted_players.values():
        for player in participant_squad.values():
            drafted_ids.add(player['player_id'])
            
    all_excluded = drafted_ids.union(st.session_state.banned_player_ids)
    
    for idx in range(curr_idx, len(seq)):
        pick = seq[idx]
        picker = pick['participant']
        
        # Determine the user's empty slots
        form = st.session_state.formations[picker]
        starting_slots = get_formation_slots(form)
        bench_slots_list = [f"SUB {x}" for x in range(1, st.session_state.bench_slots + 1)]
        all_slots = starting_slots + bench_slots_list
        squad = st.session_state.drafted_players.setdefault(picker, {})
        empty_slots = [slot for slot in all_slots if slot not in squad]
        
        if not empty_slots:
            continue
            
        selected_slot = empty_slots[0]
        base_pos = get_base_position(selected_slot)
        
        # Filter available players from database
        filtered_df = df_players.copy()
        if all_excluded:
            filtered_df = filtered_df[~filtered_df['player_id'].isin(all_excluded)]
            
        # Apply positional filter
        if base_pos and base_pos != "SUB":
            allowed = FLEXIBLE_POSITIONS.get(base_pos, [base_pos]) if filter_mode == "Flexible" else [base_pos]
            filtered_df = filtered_df[filtered_df['pos_list'].apply(lambda pos: any(p in pos for p in allowed))]
            
        # Fallback to no positional filter if no matching player remains in database (very rare)
        if filtered_df.empty:
            filtered_df = df_players.copy()
            if all_excluded:
                filtered_df = filtered_df[~filtered_df['player_id'].isin(all_excluded)]
                
        if not filtered_df.empty:
            best_player = filtered_df.sort_values(by='overall', ascending=False).iloc[0].to_dict()
            st.session_state.drafted_players[picker][selected_slot] = best_player
            all_excluded.add(best_player['player_id'])
            
            # Record choice in history
            st.session_state.draft_history.append({
                "pick_overall": idx + 1,
                "round": pick['round'],
                "picker": picker,
                "slot": selected_slot,
                "player_name": best_player['short_name'],
                "overall": best_player['overall'],
                "position": best_player['player_positions']
            })
            
    # Set draft sequence index to end
    st.session_state.current_pick_index = len(seq)

@st.dialog("🎯 Draft Player Slot")
def draft_player_dialog(slot, picker):
    st.markdown(f"### Draft Player for: **{slot}**")
    
    # 1. Positional filtering
    base_pos = get_base_position(slot)
    filter_mode = st.session_state.get("filter_mode", "Flexible")
    st.write(f"Position Filter: **{base_pos}** ({filter_mode} Mode)")
    
    # 2. Search query and results
    search_query = st.text_input("🔍 Search by Name / Club / Nation", value="", key="dialog_search_input")
    df_pool = search_players(query=search_query, position_filter=base_pos, filter_mode=filter_mode)
    options = [f"{row['short_name']} ({row['overall']} OVR | {row['player_positions']} | {row['club_name']})" for _, row in df_pool.iterrows()]
    
    p_dict = None
    if not options:
        st.warning("No players found. Try adjusting search.")
    else:
        selected_player_str = st.selectbox("Choose Player to Draft", options, key="dialog_choose_player")
        if selected_player_str:
            idx = options.index(selected_player_str)
            p_dict = df_pool.iloc[idx].to_dict()
            
    # 3. Preview card
    if p_dict:
        st.write(" ")
        ovr = p_dict.get("overall", 50)
        card_class = "card-gold" if ovr >= 85 else ("card-silver" if ovr >= 75 else "card-bronze")
        face_url = p_dict.get("player_face_url", "")
        player_id = p_dict.get("player_id", "notfound")
        face_data_uri = get_player_image_base64_cached(player_id, face_url)
        
        st.html(f"""
        <div style="display: flex; justify-content: center; margin-bottom: 10px;">
            <div class="player-card {card_class}" style="width: 120px; height: 180px; padding: 10px; border-radius: 8px;">
                <div class="card-rating-pos" style="font-size: 13px;">
                    <span class="card-rating" style="font-size: 11px; padding: 1px 4px;">{ovr}</span>
                    <span class="card-pos" style="font-size: 12px;">{base_pos}</span>
                </div>
                <img class="card-face" src="{face_data_uri}" style="width: 70px; height: 70px;" referrerpolicy="no-referrer">
                <div class="card-name" style="font-size: 12px; margin-top: 4px;">{p_dict['short_name']}</div>
                <div class="card-club" style="font-size: 9px;">{p_dict['club_name']}</div>
            </div>
        </div>
        """)
        
        # 4. Confirm Draft button
        if st.button(f"✅ Confirm Draft", type="primary", use_container_width=True):
            st.session_state.drafted_players[picker][slot] = p_dict
            
            # Record choice in history
            curr_idx = st.session_state.current_pick_index
            seq = st.session_state.draft_sequence
            current_pick = seq[curr_idx]
            st.session_state.draft_history.append({
                "pick_overall": curr_idx + 1,
                "round": current_pick['round'],
                "picker": picker,
                "slot": slot,
                "player_name": p_dict['short_name'],
                "overall": p_dict['overall'],
                "position": p_dict['player_positions']
            })
            
            # Advance pick index and save state
            st.session_state.current_pick_index += 1
            save_session_state()
            
            # Clear query parameter and reload
            st.query_params.pop("draft_slot", None)
            st.rerun()

    st.write(" ")
    if st.button("❌ Cancel & Close", use_container_width=True, type="secondary"):
        st.query_params.pop("draft_slot", None)
        st.rerun()

def get_pitch_layout(formation, drafted_players):
    slots = get_formation_slots(formation)
    
    rows = {
        "attack": [],
        "midfield": [],
        "defense": [],
        "gk": []
    }
    
    # Sorting weights to line up positions properly (Left to Right)
    def get_horizontal_weight(slot):
        slot_upper = slot.upper()
        if slot_upper.startswith("LB"): return 1
        if slot_upper.startswith("LWB"): return 2
        if slot_upper.startswith("CB"): return 3
        if slot_upper.startswith("RWB"): return 4
        if slot_upper.startswith("RB"): return 5
        
        if slot_upper.startswith("LM"): return 1
        if slot_upper.startswith("CDM"): return 2
        if slot_upper.startswith("CM"): return 3
        if slot_upper.startswith("CAM"): return 4
        if slot_upper.startswith("RM"): return 5
        
        if slot_upper.startswith("LW"): return 1
        if slot_upper.startswith("LF"): return 2
        if slot_upper.startswith("CF"): return 3
        if slot_upper.startswith("ST"): return 4
        if slot_upper.startswith("RF"): return 5
        if slot_upper.startswith("RW"): return 6
        return 3 # Center default
        
    for slot in slots:
        slot_upper = slot.upper()
        player = drafted_players.get(slot, None)
        item = {"slot": slot, "player": player}
        
        if slot_upper.startswith("GK"):
            rows["gk"].append(item)
        elif any(slot_upper.startswith(pos) for pos in ["CB", "LB", "RB", "LWB", "RWB"]):
            rows["defense"].append(item)
        elif any(slot_upper.startswith(pos) for pos in ["CM", "CDM", "CAM", "LM", "RM"]):
            rows["midfield"].append(item)
        elif any(slot_upper.startswith(pos) for pos in ["ST", "LW", "RW", "CF", "LF", "RF"]):
            rows["attack"].append(item)
        else:
            rows["midfield"].append(item)
            
    # Sort horizontally
    for key in rows:
        rows[key] = sorted(rows[key], key=lambda x: get_horizontal_weight(x["slot"]))
        
    return rows

def render_pitch_html(formation, drafted_players, interactive=False):
    rows = get_pitch_layout(formation, drafted_players)
    
    html = """
    <div class="pitch-container">
        <div class="pitch-bg-lines"></div>
        <div class="pitch-half-line"></div>
        <div class="pitch-center-circle"></div>
        <div class="pitch-penalty-area-top"></div>
        <div class="pitch-penalty-area-bottom"></div>
    """
    
    for row_name in ["attack", "midfield", "defense", "gk"]:
        html += f'<div class="pitch-row row-{row_name}">'
        for item in rows[row_name]:
            slot = item["slot"]
            player = item["player"]
            
            if player:
                ovr = player.get("overall", 50)
                card_theme = "card-gold" if ovr >= 85 else ("card-silver" if ovr >= 75 else "card-bronze")
                face_url = player.get("player_face_url", "")
                if not isinstance(face_url, str) or not face_url.startswith("http"):
                    face_url = "https://cdn.sofifa.net/players/notfound_0_120.png"
                player_id = player.get("player_id", "notfound")
                face_data_uri = get_player_image_base64_cached(player_id, face_url)
                name = html_lib.escape(str(player.get("short_name", "Unknown")))
                long_name = html_lib.escape(str(player.get("long_name", name)))
                club = html_lib.escape(str(player.get("club_name", "Free Agent")))
                
                html += f"""
                <div class="player-card {card_theme}">
                    <div class="card-rating-pos">
                        <span class="card-rating">{ovr}</span>
                        <span class="card-pos">{slot.split()[0]}</span>
                    </div>
                    <img class="card-face" src="{face_data_uri}" referrerpolicy="no-referrer">
                    <div class="card-name" title="{long_name}">{name}</div>
                    <div class="card-club" title="{club}">{club}</div>
                </div>
                """
            else:
                card_html = f"""
                <div class="player-card empty-card">
                    <div class="empty-pos">{slot}</div>
                    <div class="empty-plus">+</div>
                </div>
                """
                if interactive:
                    html += f'<a href="?draft_slot={slot}" target="_self" style="text-decoration: none; color: inherit;">{card_html}</a>'
                else:
                    html += card_html
        html += '</div>'
        
    html += "</div>"
    return " ".join([line.strip() for line in html.splitlines()])

def display_pitch_component(formation, drafted_players, bench_slots_count, interactive=False):
    """Render pitch + bench using st.html with escaped HTML."""
    pitch_body = render_pitch_html(formation, drafted_players, interactive)
    bench_body = render_bench_html(bench_slots_count, drafted_players, interactive)
    st.html(pitch_body)
    if bench_body:
        st.html(bench_body)

def render_bench_html(bench_slots, drafted_players, interactive=False):
    if bench_slots == 0:
        return ""
        
    html = """
    <div style="text-align: center; margin-top: 30px;">
        <h4 class="gold-text" style="margin-bottom: 15px;">SUBSTITUTES / BENCH</h4>
        <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
    """
    
    for i in range(1, bench_slots + 1):
        slot = f"SUB {i}"
        player = drafted_players.get(slot, None)
        
        if player:
            ovr = player.get("overall", 50)
            card_theme = "card-gold" if ovr >= 85 else ("card-silver" if ovr >= 75 else "card-bronze")
            face_url = player.get("player_face_url", "")
            if not isinstance(face_url, str) or not face_url.startswith("http"):
                face_url = "https://cdn.sofifa.net/players/notfound_0_120.png"
            player_id = player.get("player_id", "notfound")
            face_data_uri = get_player_image_base64_cached(player_id, face_url)
            name = html_lib.escape(str(player.get("short_name", "Unknown")))
            long_name = html_lib.escape(str(player.get("long_name", name)))
            club = html_lib.escape(str(player.get("club_name", "Free Agent")))
            
            html += f"""
            <div class="player-card {card_theme}">
                <div class="card-rating-pos">
                    <span class="card-rating">{ovr}</span>
                    <span class="card-pos">SUB</span>
                </div>
                <img class="card-face" src="{face_data_uri}" referrerpolicy="no-referrer">
                <div class="card-name" title="{long_name}">{name}</div>
                <div class="card-club" title="{club}">{club}</div>
            </div>
            """
        else:
            card_html = f"""
            <div class="player-card empty-card">
                <div class="empty-pos">{slot}</div>
                <div class="empty-plus">+</div>
            </div>
            """
            if interactive:
                html += f'<a href="?draft_slot={slot}" target="_self" style="text-decoration: none; color: inherit;">{card_html}</a>'
            else:
                html += card_html
            
    html += """
        </div>
    </div>
    """
    return " ".join([line.strip() for line in html.splitlines()])

# ----------------- Session State Setup -----------------
if "initialized" not in st.session_state:
    load_session_state()
    st.session_state.initialized = True

if "phase" not in st.session_state:
    st.session_state.phase = "setup"
if "participants" not in st.session_state:
    st.session_state.participants = []
if "team_names" not in st.session_state:
    st.session_state.team_names = {}
if "formations" not in st.session_state:
    st.session_state.formations = {}
if "bench_slots" not in st.session_state:
    st.session_state.bench_slots = 5
if "bans" not in st.session_state:
    st.session_state.bans = {}
if "ban_submissions" not in st.session_state:
    st.session_state.ban_submissions = {}
if "banned_player_ids" not in st.session_state:
    st.session_state.banned_player_ids = set()
if "drafted_players" not in st.session_state:
    st.session_state.drafted_players = {}
if "draft_sequence" not in st.session_state:
    st.session_state.draft_sequence = []
if "current_pick_index" not in st.session_state:
    st.session_state.current_pick_index = 0
if "draft_history" not in st.session_state:
    st.session_state.draft_history = []

# ----------------- Query Parameter Listener -----------------
if st.session_state.phase == "draft" and "draft_slot" in st.query_params:
    slot = st.query_params["draft_slot"]
    seq = st.session_state.draft_sequence
    curr_idx = st.session_state.current_pick_index
    if curr_idx < len(seq):
        picker = seq[curr_idx]['participant']
        form = st.session_state.formations[picker]
        starting_slots = get_formation_slots(form)
        bench_slots_list = [f"SUB {x}" for x in range(1, st.session_state.bench_slots + 1)]
        all_slots = starting_slots + bench_slots_list
        squad = st.session_state.drafted_players.setdefault(picker, {})
        
        if slot in all_slots and slot not in squad:
            draft_player_dialog(slot, picker)
        else:
            st.query_params.pop("draft_slot", None)

# ----------------- Phase 1: Setup Phase -----------------
if st.session_state.phase == "setup":
    st.title("⚽ EA FC 26 Player Draft")
    st.write("Welcome to the Draft Manager! Get started by setting up participants, bench slots, and formations.")
    
    # --- Import Previous Draft Section ---
    with st.container(border=True):
        st.subheader("📂 Import a Previous Draft", anchor=False)
        st.write("Upload a previously exported roster CSV to view squads instantly.")
        uploaded_file = st.file_uploader("Upload Roster CSV", type=["csv"], key="csv_import")
        
        if uploaded_file is not None:
            btn_import = st.button("📥 Import & View Squads", type="primary", use_container_width=True)
            if btn_import:
                try:
                    imported_df = pd.read_csv(uploaded_file)
                    required_cols = {"Participant", "Formation", "Slot", "Player Name"}
                    if not required_cols.issubset(set(imported_df.columns)):
                        st.error(f"CSV must contain columns: {', '.join(required_cols)}. Found: {', '.join(imported_df.columns)}")
                    else:
                        # Reconstruct state from CSV
                        participants = list(imported_df['Participant'].unique())
                        formations = {}
                        team_names = {}
                        drafted_players = {p: {} for p in participants}
                        
                        # Detect bench slots count from SUB slots in the CSV
                        all_slots_in_csv = imported_df['Slot'].unique()
                        sub_slots = [s for s in all_slots_in_csv if str(s).startswith('SUB')]
                        bench_count = len(sub_slots) // len(participants) if participants else 5
                        
                        for _, row in imported_df.iterrows():
                            participant = row['Participant']
                            formation = row['Formation']
                            slot = row['Slot']
                            player_name = row['Player Name']
                            
                            formations[participant] = formation
                            team_names[participant] = row.get('Team Name', f"{participant} FC")
                            
                            if player_name and str(player_name) != 'N/A' and str(player_name) != 'nan':
                                # Match player back to the master database
                                match = df_players[df_players['short_name'] == player_name]
                                if match.empty:
                                    # Try long_name
                                    match = df_players[df_players['long_name'] == player_name]
                                
                                if not match.empty:
                                    drafted_players[participant][slot] = match.iloc[0].to_dict()
                                else:
                                    # Create a minimal player dict from CSV data
                                    drafted_players[participant][slot] = {
                                        'player_id': f'imported_{participant}_{slot}',
                                        'short_name': str(player_name),
                                        'long_name': str(player_name),
                                        'overall': int(row.get('Overall', 50)) if pd.notna(row.get('Overall')) else 50,
                                        'club_name': str(row.get('Club', 'Unknown')),
                                        'nationality_name': str(row.get('Nationality', 'Unknown')),
                                        'player_positions': str(row.get('Listed Positions', 'SUB')),
                                        'pos_list': [p.strip() for p in str(row.get('Listed Positions', 'SUB')).split(',')],
                                        'age': 25,
                                        'player_face_url': 'https://cdn.sofifa.net/players/notfound_0_120.png',
                                        'pace': 50, 'shooting': 50, 'passing': 50,
                                        'dribbling': 50, 'defending': 50, 'physic': 50,
                                        'goalkeeping_diving': 50, 'goalkeeping_handling': 50,
                                        'goalkeeping_kicking': 50, 'goalkeeping_positioning': 50,
                                        'goalkeeping_reflexes': 50, 'goalkeeping_speed': 50,
                                    }
                        
                        # Set session state
                        st.session_state.participants = participants
                        st.session_state.team_names = team_names
                        st.session_state.formations = formations
                        st.session_state.drafted_players = drafted_players
                        st.session_state.bench_slots = bench_count
                        st.session_state.bans = {p: [] for p in participants}
                        st.session_state.ban_submissions = {p: True for p in participants}
                        st.session_state.banned_player_ids = set()
                        st.session_state.draft_sequence = []
                        st.session_state.current_pick_index = 0
                        st.session_state.draft_history = []
                        st.session_state.phase = "completed"
                        save_session_state()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error importing CSV: {str(e)}")
    
    st.write(" ")
    
    # --- Manual Setup Section ---
    with st.container(border=True):
        st.subheader("🛠️ New Draft Setup", anchor=False)
        col1, col2 = st.columns(2)
        with col1:
            num_participants = st.slider("Number of Participants", min_value=2, max_value=20, value=4)
        with col2:
            bench_slots = st.slider("Number of Bench Slots (SUB)", min_value=0, max_value=10, value=5)
            
        st.write("---")
        st.subheader("Participant Setups", anchor=False)
        
        participant_names = []
        participant_team_names = []
        participant_formations = []
        
        for i in range(num_participants):
            col_name, col_team, col_form = st.columns([2, 2, 1])
            with col_name:
                name = st.text_input(f"Participant {i+1} Name", value=f"Participant {i+1}", key=f"p_name_{i}").strip()
                participant_names.append(name)
            with col_team:
                team = st.text_input(f"Team Name", value=f"{name} FC" if name else f"Team {i+1}", key=f"p_team_{i}").strip()
                participant_team_names.append(team)
            with col_form:
                form = st.selectbox(f"Formation for Participant {i+1}", list(FORMATIONS.keys()), index=0, key=f"p_form_{i}")
                participant_formations.append(form)
                
        st.write(" ")
        btn_start = st.button("🚀 Start Setup & Proceed to Bans", use_container_width=True, type="primary")
        
        if btn_start:
            unique_names = set([n for n in participant_names if n])
            if len(unique_names) != num_participants:
                st.error("Error: All participant names must be filled out and unique.")
            else:
                st.session_state.participants = participant_names.copy()
                st.session_state.team_names = {participant_names[j]: participant_team_names[j] for j in range(num_participants)}
                st.session_state.bench_slots = bench_slots
                st.session_state.formations = {participant_names[j]: participant_formations[j] for j in range(num_participants)}
                
                st.session_state.bans = {name: [] for name in participant_names}
                st.session_state.ban_submissions = {name: False for name in participant_names}
                st.session_state.drafted_players = {name: {} for name in participant_names}
                
                total_rounds = 11 + bench_slots
                draft_sequence = []
                
                randomized_participants = participant_names.copy()
                random.shuffle(randomized_participants)
                
                overall_pick = 1
                for r in range(1, total_rounds + 1):
                    round_order = randomized_participants.copy()
                    if r % 2 == 0:
                        round_order.reverse()
                    for pick_in_round, picker in enumerate(round_order):
                        draft_sequence.append({
                            "round": r,
                            "pick_in_round": pick_in_round + 1,
                            "overall_pick": overall_pick,
                            "participant": picker
                        })
                        overall_pick += 1
                        
                st.session_state.draft_sequence = draft_sequence
                st.session_state.current_pick_index = 0
                st.session_state.banned_player_ids = set()
                st.session_state.phase = "ban"
                save_session_state()
                st.rerun()

# ----------------- Phase 2: Blind Ban Phase -----------------
elif st.session_state.phase == "ban":
    st.title("🚫 Phase 2: Blind Player Bans")
    st.write("Each participant must select exactly **3 players** to ban from the pool. Selections are blind and hidden until all submit.")
    
    remaining_participants = [p for p in st.session_state.participants if not st.session_state.ban_submissions[p]]
    
    if remaining_participants:
        st.subheader("Select Participant to Submit Bans", anchor=False)
        selected_picker = st.selectbox("Who is banning right now?", remaining_participants)
        
        st.markdown(f"### 🛡️ Ban Selection for **{selected_picker}**")
        st.info("Pass the screen to this participant. Once they lock in their bans, the choices will be hidden.")
        
        col_ban1, col_ban2, col_ban3 = st.columns(3)
        
        with col_ban1:
            st.markdown("**Ban Choice 1**")
            q1 = st.text_input("Search Name/Club/Nation (1)", key=f"q_ban1_{selected_picker}")
            df_search1 = search_players(query=q1)
            options1 = [f"{row['short_name']} ({row['overall']} OVR | {row['player_positions']} | {row['club_name']})" for _, row in df_search1.iterrows()]
            selected_ban1_str = st.selectbox("Select Soccer Player 1", options1, key=f"sel_ban1_{selected_picker}")
            
            p1_dict = None
            if selected_ban1_str:
                idx1 = options1.index(selected_ban1_str)
                p1_dict = df_search1.iloc[idx1].to_dict()
                st.markdown(f"Selected: **{p1_dict['short_name']}** ({p1_dict['overall']} OVR)")
                
        with col_ban2:
            st.markdown("**Ban Choice 2**")
            q2 = st.text_input("Search Name/Club/Nation (2)", key=f"q_ban2_{selected_picker}")
            df_search2 = search_players(query=q2)
            if p1_dict:
                df_search2 = df_search2[df_search2['player_id'] != p1_dict['player_id']]
            options2 = [f"{row['short_name']} ({row['overall']} OVR | {row['player_positions']} | {row['club_name']})" for _, row in df_search2.iterrows()]
            selected_ban2_str = st.selectbox("Select Soccer Player 2", options2, key=f"sel_ban2_{selected_picker}")
            
            p2_dict = None
            if selected_ban2_str:
                idx2 = options2.index(selected_ban2_str)
                p2_dict = df_search2.iloc[idx2].to_dict()
                st.markdown(f"Selected: **{p2_dict['short_name']}** ({p2_dict['overall']} OVR)")
                
        with col_ban3:
            st.markdown("**Ban Choice 3**")
            q3 = st.text_input("Search Name/Club/Nation (3)", key=f"q_ban3_{selected_picker}")
            df_search3 = search_players(query=q3)
            exclude_ids = []
            if p1_dict: exclude_ids.append(p1_dict['player_id'])
            if p2_dict: exclude_ids.append(p2_dict['player_id'])
            if exclude_ids:
                df_search3 = df_search3[~df_search3['player_id'].isin(exclude_ids)]
            options3 = [f"{row['short_name']} ({row['overall']} OVR | {row['player_positions']} | {row['club_name']})" for _, row in df_search3.iterrows()]
            selected_ban3_str = st.selectbox("Select Soccer Player 3", options3, key=f"sel_ban3_{selected_picker}")
            
            p3_dict = None
            if selected_ban3_str:
                idx3 = options3.index(selected_ban3_str)
                p3_dict = df_search3.iloc[idx3].to_dict()
                st.markdown(f"Selected: **{p3_dict['short_name']}** ({p3_dict['overall']} OVR)")
                
        st.write(" ")
        btn_lock = st.button(f"🔒 Lock in Bans for {selected_picker}", use_container_width=True, type="primary")
        
        if btn_lock:
            if not p1_dict or not p2_dict or not p3_dict:
                st.error("Please ensure you have selected three distinct players to ban.")
            else:
                st.session_state.bans[selected_picker] = [p1_dict, p2_dict, p3_dict]
                st.session_state.ban_submissions[selected_picker] = True
                st.success(f"Bans locked for {selected_picker}! Moving on.")
                save_session_state()
                st.rerun()
    else:
        st.success("✅ All participants have submitted their bans!")
        st.subheader("Global Bans Reveal Room")
        st.write("Ready to see who was banned? This will reveal the final global ban list and start the Snake Draft.")
        
        # Calculate ranked bans
        all_bans = []
        for participant, player_list in st.session_state.bans.items():
            for p in player_list:
                p_copy = p.copy()
                p_copy['banned_by'] = participant
                all_bans.append(p_copy)
                
        # Sort by overall descending
        all_bans = sorted(all_bans, key=lambda x: x.get('overall', 50), reverse=True)
        
        # Display ranked list
        with st.container(border=True):
            st.markdown("### 🏆 Banned Players Ranking (Highest OVR first)")
            for rk, b in enumerate(all_bans, 1):
                st.markdown(f"{rk}. **{b['short_name']}** ({b['overall']} OVR) — Banned by *{b['banned_by']}*")
                
        st.write(" ")
        if st.button("🔥 Reveal Bans & Start Snake Draft", use_container_width=True, type="primary"):
            banned_player_ids = set()
            for participant, player_list in st.session_state.bans.items():
                for p in player_list:
                    banned_player_ids.add(p['player_id'])
                    
            st.session_state.banned_player_ids = banned_player_ids
            st.session_state.phase = "draft"
            save_session_state()
            st.rerun()

    st.write(" ")
    st.write("---")
    st.subheader("Ban Submission Status", anchor=False)
    cols_status = st.columns(len(st.session_state.participants))
    for idx, p_name in enumerate(st.session_state.participants):
        with cols_status[idx]:
            submitted = st.session_state.ban_submissions[p_name]
            status_text = "🔒 LOCKED & HIDDEN" if submitted else "⏳ AWAITING"
            status_class = "badge-green" if submitted else "badge-secondary"
            team_name = st.session_state.team_names.get(p_name, f"{p_name} FC")
            st.markdown(f"""
            <div style="text-align: center;" class="glass-panel">
                <h4>{p_name}</h4>
                <div style="font-size: 12px; color: #aaa; margin-bottom: 8px;">{team_name}</div>
                <span class="custom-badge {status_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)

# ----------------- Phase 3: Snake Draft Phase -----------------
elif st.session_state.phase == "draft":
    with st.sidebar:
        st.markdown("<h2 class='glow-text'>🏆 Draft Status</h2>", unsafe_allow_html=True)
        
        curr_idx = st.session_state.current_pick_index
        seq = st.session_state.draft_sequence
        
        if curr_idx < len(seq):
            current_pick = seq[curr_idx]
            picker_name = current_pick['participant']
            picker_team = st.session_state.team_names.get(picker_name, f"{picker_name} FC")
            st.markdown(f"""
            <div class="glass-panel" style="padding: 15px; border-color: #ffd700;">
                <h4 style="margin: 0; color: #ffd700;">🎯 Current Pick</h4>
                <div style="font-size: 22px; font-weight: 800; margin: 10px 0; line-height: 1.2;">{picker_name}<br/><span style="font-size: 13px; color: #ffd700; font-weight: 400;">{picker_team}</span></div>
                <div style="font-size: 14px; color: #aaa;">Round: <b>{current_pick['round']}</b></div>
                <div style="font-size: 14px; color: #aaa;">Pick overall: <b>{current_pick['overall_pick']} of {len(seq)}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("📅 **Up Next:**")
            for offset in range(1, 5):
                next_idx = curr_idx + offset
                if next_idx < len(seq):
                    np = seq[next_idx]
                    np_name = np['participant']
                    np_team = st.session_state.team_names.get(np_name, f"{np_name} FC")
                    st.write(f"{next_idx+1}. **{np_name}** ({np_team})")
        else:
            st.markdown("""
            <div class="glass-panel" style="padding: 15px; border-color: #00c853;">
                <h4 style="margin: 0; color: #00c853;">🎉 Draft Finished!</h4>
                <div style="font-size: 16px; margin-top: 10px;">All picks are complete. Check the Summary tab.</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("---")
        st.subheader("⚙️ Draft Settings")
        filter_mode = st.selectbox("Position Match Mode", ["Strict", "Flexible"], index=1, 
                                     help="Strict: Player must have exact position. Flexible: Allows adjacent positions (e.g. LWB in LB slot).")
        
        if curr_idx > 0:
            st.write(" ")
            if st.button("↩️ Undo Last Pick", use_container_width=True, type="secondary"):
                prev_idx = curr_idx - 1
                prev_pick = seq[prev_idx]
                prev_picker = prev_pick['participant']
                
                if st.session_state.draft_history:
                    last_log = st.session_state.draft_history.pop()
                    slot_to_remove = last_log['slot']
                    if slot_to_remove in st.session_state.drafted_players[prev_picker]:
                        del st.session_state.drafted_players[prev_picker][slot_to_remove]
                
                st.session_state.current_pick_index = prev_idx
                st.success("Successfully undid the last draft pick!")
                save_session_state()
                st.rerun()
                
        if curr_idx < len(seq):
            st.write(" ")
            with st.expander("🤖 Admin Auto-Draft Tool"):
                st.warning("This will automatically complete the entire remaining draft using the highest-rated available players.")
                auto_run_confirm = st.text_input("Type 'auto run' to confirm:", value="", key="auto_run_confirm_input").strip().lower()
                if auto_run_confirm == "auto run":
                    if st.button("🚀 Execute Auto-Draft", type="primary", use_container_width=True):
                        auto_draft_remaining(filter_mode)
                        st.success("Auto-draft complete!")
                        save_session_state()
                        st.rerun()
                
        with st.expander("🚫 Banned Players List (Ranked by OVR)"):
            all_bans = []
            for participant, player_list in st.session_state.bans.items():
                for p in player_list:
                    p_copy = p.copy()
                    p_copy['banned_by'] = participant
                    all_bans.append(p_copy)
                    
            # Sort by overall descending
            all_bans = sorted(all_bans, key=lambda x: x.get('overall', 50), reverse=True)
            
            if all_bans:
                for rk, b in enumerate(all_bans, 1):
                    st.write(f"{rk}. **{b['short_name']}** ({b['overall']} OVR) — Banned by *{b['banned_by']}*")
            else:
                st.write("No bans submitted.")

    st.title("🏟️ Snake Draft Board")
    
    if curr_idx < len(seq):
        current_pick = seq[curr_idx]
        picker = current_pick['participant']
        
        tab_draft, tab_board, tab_pitch = st.tabs(["🎯 Draft Room", "📊 Draft Board", "⚽ Squad Pitch Visualizer"])
        
        with tab_draft:
            col_select, col_preview = st.columns([5, 3])
            
            with col_select:
                st.markdown(f"### It is **{picker}**'s turn to draft!")
                st.write("1. Select an empty slot in your formation.")
                
                empty_slots = []
                form = st.session_state.formations[picker]
                starting_slots = get_formation_slots(form)
                bench_slots_list = [f"SUB {x}" for x in range(1, st.session_state.bench_slots + 1)]
                all_slots = starting_slots + bench_slots_list
                squad = st.session_state.drafted_players.get(picker, {})
                empty_slots = [slot for slot in all_slots if slot not in squad]
                
                if not empty_slots:
                    st.warning("All slots are filled for this squad.")
                    st.session_state.current_pick_index += 1
                    st.rerun()
                    
                selected_slot = st.selectbox("Select Empty Slot", empty_slots, key=f"sel_slot_{curr_idx}")
                base_pos = get_base_position(selected_slot)
                
                st.write(f"2. Search and select a player. Pool automatically filtered to position: **{base_pos}** ({filter_mode} Mode)")
                search_query = st.text_input("🔍 Search by Player Name / Club / Nation", value="", placeholder="Type here...", key=f"query_{curr_idx}")
                df_pool = search_players(query=search_query, position_filter=base_pos, filter_mode=filter_mode)
                options = [f"{row['short_name']} ({row['overall']} OVR | {row['player_positions']} | {row['club_name']})" for _, row in df_pool.iterrows()]
                
                if not options:
                    st.warning("No players found matching your criteria. Try adjusting your search query.")
                    p_dict = None
                else:
                    selected_player_str = st.selectbox("Choose Player to Draft", options, key=f"choose_player_{curr_idx}")
                    p_dict = None
                    if selected_player_str:
                        idx = options.index(selected_player_str)
                        p_dict = df_pool.iloc[idx].to_dict()
                
                st.write(" ")
                if p_dict:
                    btn_draft = st.button(f"✅ Draft {p_dict['short_name']} for {selected_slot}", type="primary", use_container_width=True)
                    if btn_draft:
                        st.session_state.drafted_players[picker][selected_slot] = p_dict
                        st.session_state.draft_history.append({
                            "pick_overall": curr_idx + 1,
                            "round": current_pick['round'],
                            "picker": picker,
                            "slot": selected_slot,
                            "player_name": p_dict['short_name'],
                            "overall": p_dict['overall'],
                            "position": p_dict['player_positions']
                        })
                        st.session_state.current_pick_index += 1
                        st.success(f"Successfully drafted {p_dict['short_name']}!")
                        save_session_state()
                        st.rerun()
                        
            with col_preview:
                if p_dict:
                    st.markdown("### 📋 Player Profile")
                    ovr = p_dict.get("overall", 50)
                    card_class = "card-gold" if ovr >= 85 else ("card-silver" if ovr >= 75 else "card-bronze")
                    face_url = p_dict.get("player_face_url", "https://cdn.sofifa.net/players/notfound_0_120.png")
                    player_id = p_dict.get("player_id", "notfound")
                    face_data_uri = get_player_image_base64_cached(player_id, face_url)
                    
                    st.markdown(f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                        <div class="player-card {card_class}" style="width: 140px; height: 210px; padding: 12px;">
                            <div class="card-rating-pos" style="font-size: 15px;">
                                <span class="card-rating" style="font-size: 13px; padding: 2px 6px;">{ovr}</span>
                                <span class="card-pos" style="font-size: 14px;">{base_pos}</span>
                            </div>
                            <img class="card-face" src="{face_data_uri}" style="width: 90px; height: 90px;" referrerpolicy="no-referrer">
                            <div class="card-name" style="font-size: 14px; margin-top: 5px;">{p_dict['short_name']}</div>
                            <div class="card-club" style="font-size: 10px;">{p_dict['club_name']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    is_gk = "GK" in p_dict['pos_list']
                    with st.container(border=True):
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        if is_gk:
                            with col_stat1:
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('goalkeeping_diving', 50)}</div><div class='stat-lbl'>DIV</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('goalkeeping_positioning', 50)}</div><div class='stat-lbl'>POS</div></div>", unsafe_allow_html=True)
                            with col_stat2:
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('goalkeeping_handling', 50)}</div><div class='stat-lbl'>HAN</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('goalkeeping_reflexes', 50)}</div><div class='stat-lbl'>REF</div></div>", unsafe_allow_html=True)
                            with col_stat3:
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('goalkeeping_kicking', 50)}</div><div class='stat-lbl'>KIC</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('goalkeeping_speed', 50)}</div><div class='stat-lbl'>SPD</div></div>", unsafe_allow_html=True)
                        else:
                            with col_stat1:
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('pace', 50)}</div><div class='stat-lbl'>PAC</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('dribbling', 50)}</div><div class='stat-lbl'>DRI</div></div>", unsafe_allow_html=True)
                            with col_stat2:
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('shooting', 50)}</div><div class='stat-lbl'>SHO</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('defending', 50)}</div><div class='stat-lbl'>DEF</div></div>", unsafe_allow_html=True)
                            with col_stat3:
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('passing', 50)}</div><div class='stat-lbl'>PAS</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='stat-box'><div class='stat-val'>{p_dict.get('physic', 50)}</div><div class='stat-lbl'>PHY</div></div>", unsafe_allow_html=True)
                                
                        st.markdown(f"""
                        <div style="font-size: 13px; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                            👤 <b>Full Name:</b> {p_dict['long_name']}<br/>
                            🌍 <b>Nationality:</b> {p_dict['nationality_name']}<br/>
                            🎂 <b>Age:</b> {p_dict['age']} years old<br/>
                            🏃 <b>Positions:</b> {p_dict['player_positions']}<br/>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Select a player from the dropdown to see their detailed profile here.")
                    
        with tab_board:
            st.subheader("All Squads Overview")
            cols_squads = st.columns(len(st.session_state.participants))
            for idx, p_name in enumerate(st.session_state.participants):
                with cols_squads[idx]:
                    team_name = st.session_state.team_names.get(p_name, f"{p_name} FC")
                    st.markdown(f"#### {p_name}")
                    st.markdown(f"*{team_name}*")
                    st.write(f"Formation: `{st.session_state.formations[p_name]}`")
                    form_slots = get_formation_slots(st.session_state.formations[p_name])
                    bench_slots_list = [f"SUB {x}" for x in range(1, st.session_state.bench_slots + 1)]
                    all_slots = form_slots + bench_slots_list
                    squad = st.session_state.drafted_players.get(p_name, {})
                    
                    for slot in all_slots:
                        if slot in squad:
                            player = squad[slot]
                            st.write(f"- **{slot}:** {player['short_name']} ({player['overall']} OVR)")
                        else:
                            st.write(f"- *{slot}:* (Empty)")
                            
        with tab_pitch:
            st.subheader("Field View")
            viewer_picker = st.selectbox(
                "Show pitch for participant:", 
                st.session_state.participants, 
                format_func=lambda x: f"{st.session_state.team_names.get(x, f'{x} FC')} ({x})",
                key="field_view_picker"
            )
            is_active_picker = (viewer_picker == picker)
            display_pitch_component(
                st.session_state.formations[viewer_picker],
                st.session_state.drafted_players[viewer_picker],
                st.session_state.bench_slots,
                interactive=is_active_picker
            )

    else:
        st.session_state.phase = "completed"
        st.rerun()

# ----------------- Phase 4: Output / Final Summary -----------------
elif st.session_state.phase == "completed":
    st.title("🏆 Draft Complete! Final Squads")
    st.write("Congratulations! All participants have built their squads. View squads, analyze stats, or export rosters below.")
    
    roster_rows = []
    text_summary = "EA FC 26 PLAYER DRAFT - FINAL ROSTERS\n"
    text_summary += "========================================\n\n"
    
    for participant in st.session_state.participants:
        team_name = st.session_state.team_names.get(participant, f"{participant} FC")
        text_summary += f"Participant: {participant} (Team: {team_name} | Formation: {st.session_state.formations[participant]})\n"
        text_summary += "----------------------------------------\n"
        
        form_slots = get_formation_slots(st.session_state.formations[participant])
        bench_slots_list = [f"SUB {x}" for x in range(1, st.session_state.bench_slots + 1)]
        all_slots = form_slots + bench_slots_list
        
        squad = st.session_state.drafted_players.get(participant, {})
        for slot in all_slots:
            player = squad.get(slot, {})
            p_name = player.get("short_name", "N/A")
            p_ovr = player.get("overall", "N/A")
            p_club = player.get("club_name", "N/A")
            p_nat = player.get("nationality_name", "N/A")
            p_pos = player.get("player_positions", "N/A")
            
            roster_rows.append({
                "Participant": participant,
                "Team Name": team_name,
                "Formation": st.session_state.formations[participant],
                "Slot": slot,
                "Player Name": p_name,
                "Overall": p_ovr,
                "Club": p_club,
                "Nationality": p_nat,
                "Listed Positions": p_pos
            })
            text_summary += f"[{slot}] {p_name} - {p_ovr} OVR | {p_pos} | {p_club} ({p_nat})\n"
        text_summary += "\n"
        
    df_rosters = pd.DataFrame(roster_rows)
    
    with st.container(border=True):
        st.subheader("💾 Export Roster Options", anchor=False)
        col_csv, col_txt, col_reset = st.columns(3)
        
        with col_csv:
            csv_buffer = io.BytesIO()
            df_rosters.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export Rosters (CSV)",
                data=csv_buffer.getvalue(),
                file_name="fc26_draft_rosters.csv",
                mime="text/csv",
                width='stretch'
            )
            
        with col_txt:
            st.download_button(
                label="📥 Export Rosters (TXT Summary)",
                data=text_summary,
                file_name="fc26_draft_summary.txt",
                mime="text/plain",
                width='stretch'
            )
            
        with col_reset:
            if st.button("🔄 Reset and Start New Draft", use_container_width=True, type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                if os.path.exists(STATE_FILE):
                    try:
                        os.remove(STATE_FILE)
                    except Exception:
                        pass
                st.rerun()

    tab_view, tab_data = st.tabs(["⚽ Visual Roster Sheets", "📊 Raw Rosters Table"])
    
    with tab_view:
        for participant in st.session_state.participants:
            part_df = df_rosters[df_rosters['Participant'] == participant]
            valid_ovrs = pd.to_numeric(part_df['Overall'], errors='coerce').dropna()
            avg_ovr = valid_ovrs.mean() if not valid_ovrs.empty else 0.0
            team_name = st.session_state.team_names.get(participant, f"{participant} FC")
            
            with st.expander(f"🏅 {team_name} ({participant}'s Squad) (Rating Avg: {avg_ovr:.1f})", expanded=True):
                display_pitch_component(
                    st.session_state.formations[participant],
                    st.session_state.drafted_players[participant],
                    st.session_state.bench_slots
                )
                
    with tab_data:
        st.subheader("Raw Rosters Dataframe")
        st.dataframe(df_rosters, width='stretch')
