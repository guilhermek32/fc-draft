"""Player pool searching and filtering."""

import streamlit as st

from fcdraft.config import DEFAULT_MIN_OVR, FLEXIBLE_POSITIONS
from fcdraft.data import load_data


def get_excluded_ids():
    """Ids of every already-drafted or banned player."""
    excluded = set()
    for participant_squad in st.session_state.drafted_players.values():
        for player in participant_squad.values():
            excluded.add(player["player_id"])
    excluded.update(st.session_state.banned_player_ids)
    return excluded


def allowed_positions(position_filter, filter_mode):
    if filter_mode == "Strict":
        return [position_filter]
    return FLEXIBLE_POSITIONS.get(position_filter, [position_filter])


def search_players(query="", position_filter=None, filter_mode="Strict"):
    """Available (not drafted/banned) players matching the position and text filters.

    Results are sorted by overall rating descending (the database is pre-sorted).
    """
    df = load_data()
    if df.empty:
        return df
    mask = None

    excluded = get_excluded_ids()
    if excluded:
        mask = ~df["player_id"].isin(excluded)

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

    return df[mask] if mask is not None else df


def format_player_options(df):
    """Selectbox labels for a search-result frame, preserving row order."""
    return [
        f"{r['short_name']} ({r['overall']} OVR | {r['player_positions']} | {r['club_name']})"
        for r in df[["short_name", "overall", "player_positions", "club_name"]].to_dict("records")
    ]
