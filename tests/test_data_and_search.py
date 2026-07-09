import pytest
import pandas as pd
import app

def test_load_data():
    """Verify that load_data loads a valid DataFrame with player rows and expected columns."""
    df = app.load_data()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    
    # Check essential columns
    required_cols = {"player_id", "short_name", "overall", "player_positions", "club_name"}
    assert required_cols.issubset(set(df.columns))
    
    # Check that it is sorted by Overall rating descending
    assert df["overall"].iloc[0] >= df["overall"].iloc[-1]
    
    # Check that pos_list was created
    assert "pos_list" in df.columns
    assert isinstance(df["pos_list"].iloc[0], list)

def test_search_players_by_name():
    """Verify that search_players filters rows based on query text matches."""
    # Search for a unique player name
    results = app.search_players(query="Messi")
    assert not results.empty
    assert results.iloc[0]["short_name"] == "L. Messi"

def test_search_players_strict_position():
    """Verify strict position filtering (e.g. only matching exact position list entries)."""
    # Filter by LB position in strict mode
    results = app.search_players(position_filter="LB", filter_mode="Strict")
    for _, row in results.iterrows():
        assert "LB" in row["pos_list"]
        # Ensure we don't accidentally match LWB unless they also list LB
        if "LWB" in row["pos_list"]:
            assert "LB" in row["pos_list"]

def test_search_players_flexible_position():
    """Verify flexible position filtering (matching adjacent slots like LB for LWB)."""
    # LB is adjacent to LWB. In flexible mode, searching LWB should return LB even if they do not have LWB.
    results = app.search_players(position_filter="LWB", filter_mode="Flexible")
    
    # Check that we have at least one player matching who has LB but not LWB
    lb_found = False
    for _, row in results.iterrows():
        if "LB" in row["pos_list"] and "LWB" not in row["pos_list"]:
            lb_found = True
            break
    assert lb_found, "Flexible mode should return LB players for LWB filter"
