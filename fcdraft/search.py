"""Player pool searching and filtering."""

import streamlit as st

from fcdraft.config import DEFAULT_MIN_OVR, FLEXIBLE_POSITIONS
from fcdraft.data import load_data


def get_drafted_ids():
    """Ids of every already-drafted player."""
    drafted = set()
    for participant_squad in st.session_state.drafted_players.values():
        for player in participant_squad.values():
            drafted.add(player["player_id"])
    return drafted


def get_excluded_ids():
    """Ids of every already-drafted or banned player (undraftable pool)."""
    return get_drafted_ids() | set(st.session_state.banned_player_ids)


def get_picked_by():
    """Who drafted each player: {player_id: participant}."""
    picked = {}
    for participant, squad in st.session_state.drafted_players.items():
        for player in squad.values():
            picked[str(player["player_id"])] = participant
    return picked


def get_ban_counts():
    """How many participants banned each player: {player_id: count}."""
    counts = {}
    for player_list in st.session_state.get("bans", {}).values():
        for p in player_list:
            pid = str(p["player_id"])
            counts[pid] = counts.get(pid, 0) + 1
    return counts


def allowed_positions(position_filter, filter_mode):
    if filter_mode == "Strict":
        return [position_filter]
    return FLEXIBLE_POSITIONS.get(position_filter, [position_filter])


def search_players(query="", position_filter=None, filter_mode="Strict"):
    """Players matching the position and text filters.

    Banned and already-drafted players are kept but flagged (``is_banned`` /
    ``picked_by`` columns) so the UI can gray them out and label them; both
    remain undraftable. Results are sorted by overall rating descending (the
    database is pre-sorted).
    """
    df = load_data()
    if df.empty:
        return df.assign(is_banned=False, picked_by="")
    mask = None

    if position_filter and position_filter != "SUB":
        allowed = frozenset(allowed_positions(position_filter, filter_mode))
        pos_mask = df["pos_set"].map(lambda positions: not allowed.isdisjoint(positions))
        mask = pos_mask if mask is None else mask & pos_mask

    if query:
        text_mask = df["search_blob"].str.contains(query.lower(), regex=False)
        mask = text_mask if mask is None else mask & text_mask
    else:
        # Default fallback: only show high-rated players to keep selectboxes snappy
        ovr_mask = df["overall"] >= DEFAULT_MIN_OVR
        mask = ovr_mask if mask is None else mask & ovr_mask

    results = df[mask] if mask is not None else df
    banned = set(st.session_state.banned_player_ids)
    picked_by = get_picked_by()
    return results.assign(
        is_banned=results["player_id"].isin(banned) if banned else False,
        picked_by=results["player_id"].map(picked_by).fillna("") if picked_by else "",
    )


def format_player_options(df):
    """Selectbox labels for a search-result frame, preserving row order."""
    has_banned = "is_banned" in df.columns
    has_picked = "picked_by" in df.columns
    cols = ["short_name", "overall", "player_positions", "club_name"]
    if has_banned:
        cols += ["is_banned", "player_id"]
        ban_counts = get_ban_counts() if df["is_banned"].any() else {}
    if has_picked:
        cols += ["picked_by"]

    def _suffix(r):
        if has_picked and r["picked_by"]:
            return f" 🔒 PICKED by {r['picked_by']}"
        if not (has_banned and r["is_banned"]):
            return ""
        count = ban_counts.get(str(r["player_id"]), 1)
        return f" 🚫 BANNED ×{count}" if count > 1 else " 🚫 BANNED"

    return [
        f"{r['short_name']} ({r['overall']} OVR | {r['player_positions']} | {r['club_name']})" + _suffix(r)
        for r in df[cols].to_dict("records")
    ]
