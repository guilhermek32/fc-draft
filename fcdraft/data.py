"""Player database loading and cleaning."""

from functools import lru_cache

import pandas as pd
import streamlit as st

from fcdraft.config import CSV_FILE, GK_STATS, NOTFOUND_IMG_URL, OUTFIELD_STATS

_FALLBACK_COLUMNS = [
    "player_id", "short_name", "long_name", "player_positions", "overall",
    "club_name", "nationality_name", "age", "player_face_url", "pos_list",
    "pos_set", "search_blob",
    "pace", "shooting", "passing", "dribbling", "defending", "physic",
]


@lru_cache(maxsize=2)
def _load_data_uncached(filepath):
    df = pd.read_csv(filepath, low_memory=False)
    # Standard cleaning
    df["player_id"] = df["player_id"].astype(str)
    df["short_name"] = df["short_name"].fillna("Unknown Player").astype(str)
    df["long_name"] = df["long_name"].fillna("Unknown Player").astype(str)
    df["player_positions"] = df["player_positions"].fillna("SUB").astype(str)
    df["overall"] = pd.to_numeric(df["overall"], errors="coerce").fillna(50).astype(int)
    df["club_name"] = df["club_name"].fillna("Free Agent").astype(str)
    df["nationality_name"] = df["nationality_name"].fillna("Unknown").astype(str)
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(25).astype(int)
    df["player_face_url"] = df["player_face_url"].fillna(NOTFOUND_IMG_URL).astype(str)

    for stat in OUTFIELD_STATS + GK_STATS:
        df[stat] = pd.to_numeric(df[stat], errors="coerce").fillna(50).astype(int)

    df["pos_list"] = df["player_positions"].apply(
        lambda x: [p.strip().upper() for p in x.split(",") if p.strip()]
    )
    # Precomputed columns so search never has to copy the frame or lowercase per call
    df["pos_set"] = df["pos_list"].apply(frozenset)
    df["search_blob"] = (
        df["short_name"] + "\n" + df["long_name"] + "\n"
        + df["club_name"] + "\n" + df["nationality_name"]
    ).str.lower()

    # Pre-sorted by rating so search results never need a per-call sort
    return df.sort_values(by="overall", ascending=False, kind="stable").reset_index(drop=True)


@st.cache_data
def load_data(filepath=CSV_FILE):
    try:
        return _load_data_uncached(filepath)
    except Exception as e:
        st.error(f"Error loading CSV data file: {str(e)}")
        return pd.DataFrame(columns=_FALLBACK_COLUMNS)


@lru_cache(maxsize=2)
def _players_by_id_uncached(filepath):
    df = _load_data_uncached(filepath)
    return df.set_index("player_id", drop=False)


def get_player_by_id(player_id, filepath=CSV_FILE):
    """Return a single player's row as a dict, or None if the id is unknown."""
    try:
        indexed = _players_by_id_uncached(filepath)
        if player_id in indexed.index:
            return indexed.loc[player_id].to_dict()
    except Exception:
        pass
    return None
