"""Draft progression helpers."""

import streamlit as st

from fcdraft.data import load_data
from fcdraft.formations import build_slot_list, get_base_position
from fcdraft.search import allowed_positions, get_excluded_ids
from fcdraft.state import refresh_shared_state, save_session_state


def commit_pick(picker, slot, player):
    """Validate against the freshest shared state, then record and save a pick.

    Guards the race where another device advanced the draft (or an admin undid
    a pick) between this session's render and the button click. Returns True
    when the pick landed, False (with a warning shown) otherwise.
    """
    refresh_shared_state()
    curr_idx = st.session_state.current_pick_index
    seq = st.session_state.draft_sequence

    if curr_idx >= len(seq) or seq[curr_idx]["participant"] != picker:
        st.warning("The draft has moved on — it is no longer your turn. The board has been refreshed.")
        return False
    if st.session_state.get("authed_participant") != picker:
        st.warning("You must be logged in as the on-clock participant to draft.")
        return False
    if slot in st.session_state.drafted_players.get(picker, {}):
        st.warning(f"Slot {slot} was already filled. Pick another slot.")
        return False
    if str(player["player_id"]) in {str(pid) for pid in st.session_state.banned_player_ids}:
        st.warning(f"{player['short_name']} is banned and cannot be drafted.")
        return False

    record_pick(picker, slot, player, curr_idx + 1, seq[curr_idx]["round"])
    st.session_state.current_pick_index = curr_idx + 1
    save_session_state()
    return True


def record_pick(picker, slot, player, pick_overall, round_number):
    """Assign a player to a slot and log the pick in the draft history."""
    st.session_state.drafted_players.setdefault(picker, {})[slot] = player
    st.session_state.draft_history.append({
        "pick_overall": pick_overall,
        "round": round_number,
        "picker": picker,
        "slot": slot,
        "player_name": player["short_name"],
        "overall": player["overall"],
        "position": player["player_positions"],
    })


def auto_draft_remaining(filter_mode="Flexible"):
    """Fill every remaining pick with the best available (position-matching) player."""
    curr_idx = st.session_state.current_pick_index
    seq = st.session_state.draft_sequence

    df = load_data()  # pre-sorted by overall descending
    all_excluded = get_excluded_ids()

    for idx in range(curr_idx, len(seq)):
        pick = seq[idx]
        picker = pick["participant"]

        all_slots = build_slot_list(
            st.session_state.formations[picker], st.session_state.bench_slots
        )
        squad = st.session_state.drafted_players.setdefault(picker, {})
        empty_slots = [slot for slot in all_slots if slot not in squad]
        if not empty_slots:
            continue

        selected_slot = empty_slots[0]
        base_pos = get_base_position(selected_slot)

        candidates = df
        if all_excluded:
            candidates = candidates[~candidates["player_id"].isin(all_excluded)]

        if base_pos and base_pos != "SUB":
            allowed = frozenset(allowed_positions(base_pos, filter_mode))
            positional = candidates[
                candidates["pos_set"].map(lambda positions: not allowed.isdisjoint(positions))
            ]
            # Fallback to no positional filter if no matching player remains (very rare)
            if not positional.empty:
                candidates = positional

        if not candidates.empty:
            best_player = candidates.iloc[0].to_dict()
            record_pick(picker, selected_slot, best_player, idx + 1, pick["round"])
            all_excluded.add(best_player["player_id"])

    st.session_state.current_pick_index = len(seq)
