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

def test_search_keeps_banned_players_flagged(mock_streamlit_state):
    """Banned players stay in search results, flagged and labeled."""
    df = app.load_data()
    banned_id = str(df.iloc[0]["player_id"])
    mock_streamlit_state["banned_player_ids"] = {banned_id}

    results = app.search_players(query=df.iloc[0]["short_name"])
    assert banned_id in set(results["player_id"]), "banned player must remain searchable"
    row = results[results["player_id"] == banned_id].iloc[0]
    assert bool(row["is_banned"])

    from fcdraft.search import format_player_options
    labels = format_player_options(results)
    assert any("🚫 BANNED" in l for l in labels)


def test_search_keeps_drafted_players_flagged_with_picker(mock_streamlit_state):
    """Drafted players stay in search results, labeled with who picked them."""
    df = app.load_data()
    drafted = df.iloc[1].to_dict()
    mock_streamlit_state["drafted_players"] = {"Alice": {"ST": drafted}}

    results = app.search_players(query=drafted["short_name"])
    assert drafted["player_id"] in set(results["player_id"]), "drafted player must remain searchable"
    row = results[results["player_id"] == drafted["player_id"]].iloc[0]
    assert row["picked_by"] == "Alice"

    from fcdraft.search import format_player_options
    labels = format_player_options(results)
    assert any("🔒 PICKED by Alice" in l for l in labels), labels

def test_ban_count_in_options(mock_streamlit_state):
    """A player banned by multiple participants shows a xN count in the dropdown label."""
    df = app.load_data()
    player = df.iloc[0].to_dict()
    pid = str(player["player_id"])
    mock_streamlit_state["banned_player_ids"] = {pid}
    mock_streamlit_state["bans"] = {"Alice": [player], "Bob": [player]}

    from fcdraft.search import format_player_options, get_ban_counts
    assert get_ban_counts()[pid] == 2

    results = app.search_players(query=player["short_name"])
    labels = format_player_options(results)
    assert any("🚫 BANNED ×2" in l for l in labels), labels
