"""Phase 1: participants, formations, and previous-draft import."""

import random

import pandas as pd
import streamlit as st

from fcdraft.config import FORMATIONS, NOTFOUND_IMG_URL
from fcdraft.data import load_data
from fcdraft.state import save_session_state

_REQUIRED_IMPORT_COLS = {"Participant", "Formation", "Slot", "Player Name"}


def _minimal_player_from_row(participant, slot, player_name, row):
    """Fallback player dict for imported names not found in the master database."""
    positions = str(row.get("Listed Positions", "SUB"))
    player = {
        "player_id": f"imported_{participant}_{slot}",
        "short_name": str(player_name),
        "long_name": str(player_name),
        "overall": int(row.get("Overall", 50)) if pd.notna(row.get("Overall")) else 50,
        "club_name": str(row.get("Club", "Unknown")),
        "nationality_name": str(row.get("Nationality", "Unknown")),
        "player_positions": positions,
        "pos_list": [p.strip() for p in positions.split(",")],
        "age": 25,
        "player_face_url": NOTFOUND_IMG_URL,
    }
    for stat in ("pace", "shooting", "passing", "dribbling", "defending", "physic",
                 "goalkeeping_diving", "goalkeeping_handling", "goalkeeping_kicking",
                 "goalkeeping_positioning", "goalkeeping_reflexes", "goalkeeping_speed"):
        player[stat] = 50
    return player


def _import_previous_draft(imported_df):
    """Reconstruct completed-draft state from an exported roster CSV."""
    df_players = load_data()
    participants = list(imported_df["Participant"].unique())
    formations = {}
    team_names = {}
    drafted_players = {p: {} for p in participants}

    # Detect bench slots count from SUB slots in the CSV
    all_slots_in_csv = imported_df["Slot"].unique()
    sub_slots = [s for s in all_slots_in_csv if str(s).startswith("SUB")]
    bench_count = len(sub_slots) // len(participants) if participants else 5

    for _, row in imported_df.iterrows():
        participant = row["Participant"]
        slot = row["Slot"]
        player_name = row["Player Name"]

        formations[participant] = row["Formation"]
        team_names[participant] = row.get("Team Name", f"{participant} FC")

        if player_name and str(player_name) not in ("N/A", "nan"):
            # Match player back to the master database
            match = df_players[df_players["short_name"] == player_name]
            if match.empty:
                match = df_players[df_players["long_name"] == player_name]

            if not match.empty:
                drafted_players[participant][slot] = match.iloc[0].to_dict()
            else:
                drafted_players[participant][slot] = _minimal_player_from_row(
                    participant, slot, player_name, row
                )

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


def _build_draft_sequence(participant_names, bench_slots):
    """Snake-order pick sequence over 11 + bench rounds."""
    total_rounds = 11 + bench_slots
    randomized_participants = participant_names.copy()
    random.shuffle(randomized_participants)

    draft_sequence = []
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
                "participant": picker,
            })
            overall_pick += 1
    return draft_sequence


def render():
    st.title("⚽ EA FC 26 Player Draft")
    st.write("Welcome to the Draft Manager! Get started by setting up participants, bench slots, and formations.")

    # --- Import Previous Draft Section ---
    with st.container(border=True):
        st.subheader("📂 Import a Previous Draft", anchor=False)
        st.write("Upload a previously exported roster CSV to view squads instantly.")
        uploaded_file = st.file_uploader("Upload Roster CSV", type=["csv"], key="csv_import")

        if uploaded_file is not None:
            if st.button("📥 Import & View Squads", type="primary", use_container_width=True):
                try:
                    imported_df = pd.read_csv(uploaded_file)
                    if not _REQUIRED_IMPORT_COLS.issubset(set(imported_df.columns)):
                        st.error(
                            f"CSV must contain columns: {', '.join(_REQUIRED_IMPORT_COLS)}. "
                            f"Found: {', '.join(imported_df.columns)}"
                        )
                    else:
                        _import_previous_draft(imported_df)
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
                team = st.text_input("Team Name", value=f"{name} FC" if name else f"Team {i+1}", key=f"p_team_{i}").strip()
                participant_team_names.append(team)
            with col_form:
                form = st.selectbox(f"Formation for Participant {i+1}", list(FORMATIONS.keys()), index=0, key=f"p_form_{i}")
                participant_formations.append(form)

        st.write(" ")
        if st.button("🚀 Start Setup & Proceed to Bans", use_container_width=True, type="primary"):
            unique_names = set([n for n in participant_names if n])
            if len(unique_names) != num_participants:
                st.error("Error: All participant names must be filled out and unique.")
            else:
                st.session_state.participants = participant_names.copy()
                st.session_state.team_names = {
                    participant_names[j]: participant_team_names[j] for j in range(num_participants)
                }
                st.session_state.bench_slots = bench_slots
                st.session_state.formations = {
                    participant_names[j]: participant_formations[j] for j in range(num_participants)
                }
                st.session_state.bans = {name: [] for name in participant_names}
                st.session_state.ban_submissions = {name: False for name in participant_names}
                st.session_state.drafted_players = {name: {} for name in participant_names}
                st.session_state.draft_sequence = _build_draft_sequence(participant_names, bench_slots)
                st.session_state.current_pick_index = 0
                st.session_state.banned_player_ids = set()
                st.session_state.phase = "ban"
                save_session_state()
                st.rerun()
