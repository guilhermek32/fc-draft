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


def allowed_positions(position_filter, filter_mode):
    if filter_mode == "Strict":
        return [position_filter]
    return FLEXIBLE_POSITIONS.get(position_filter, [position_filter])


def search_players(query="", position_filter=None, filter_mode="Strict"):
    """Available players matching the position and text filters.

    Drafted players are excluded; banned players are kept but flagged in an
    ``is_banned`` column so the UI can gray them out (they remain undraftable).
    Results are sorted by overall rating descending (the database is pre-sorted).
    """
    df = load_data()
    if df.empty:
        return df.assign(is_banned=False) if "is_banned" not in df.columns else df
    mask = None

    drafted = get_drafted_ids()
    if drafted:
        mask = ~df["player_id"].isin(drafted)

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
    return results.assign(is_banned=results["player_id"].isin(banned) if banned else False)


def format_player_options(df):
    """Selectbox labels for a search-result frame, preserving row order."""
    has_banned = "is_banned" in df.columns
    cols = ["short_name", "overall", "player_positions", "club_name"] + (["is_banned"] if has_banned else [])
    return [
        f"{r['short_name']} ({r['overall']} OVR | {r['player_positions']} | {r['club_name']})"
        + (" 🚫 BANNED" if has_banned and r["is_banned"] else "")
        for r in df[cols].to_dict("records")
    ]
