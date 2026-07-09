import pytest
import os
import json
import streamlit as st
import app


def test_save_and_load_session_state(tmp_path, monkeypatch, mock_streamlit_state):
    """Test that save_session_state saves data to disk, and load_session_state restores it."""
    test_state_file = tmp_path / "test_draft_state.json"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    # 1. Setup mock session state data
    # Note: st.session_state is mocked by conftest.py. Let's populate the mock store.
    mock_streamlit_state["participants"] = ["Alice", "Bob"]
    mock_streamlit_state["bench_slots"] = 3
    mock_streamlit_state["team_names"] = {"Alice": "Alice FC", "Bob": "Bob FC"}
    mock_streamlit_state["formations"] = {"Alice": "4-3-3", "Bob": "3-5-2"}
    mock_streamlit_state["bans"] = {"Alice": [{"player_id": 1, "short_name": "P1", "overall": 80}]}
    mock_streamlit_state["ban_submissions"] = {"Alice": True, "Bob": False}
    mock_streamlit_state["banned_player_ids"] = [1]
    mock_streamlit_state["drafted_players"] = {"Alice": {}, "Bob": {}}
    mock_streamlit_state["draft_sequence"] = [{"round": 1, "pick": 1, "participant": "Alice"}]
    mock_streamlit_state["current_pick_index"] = 0
    mock_streamlit_state["draft_history"] = []

    # Save state
    app.save_session_state()

    # Check that file was created
    assert test_state_file.exists()
    # Atomic write must not leave a temp file behind
    assert not (tmp_path / "test_draft_state.json.tmp").exists()

    # Check saved content
    with open(test_state_file, "r") as f:
        data = json.load(f)
        assert data["participants"] == ["Alice", "Bob"]
        assert data["bench_slots"] == 3
        assert data["formations"] == {"Alice": "4-3-3", "Bob": "3-5-2"}
        assert data["ban_submissions"] == {"Alice": True, "Bob": False}

    # 2. Clear state store and verify load restores it
    mock_streamlit_state.clear()
    assert "participants" not in mock_streamlit_state

    success = app.load_session_state()
    assert success

    # Verify loaded values
    assert mock_streamlit_state["participants"] == ["Alice", "Bob"]
    assert mock_streamlit_state["bench_slots"] == 3
    assert mock_streamlit_state["team_names"] == {"Alice": "Alice FC", "Bob": "Bob FC"}
    assert mock_streamlit_state["formations"] == {"Alice": "4-3-3", "Bob": "3-5-2"}
    assert mock_streamlit_state["ban_submissions"] == {"Alice": True, "Bob": False}


def test_load_non_existent_state(tmp_path, monkeypatch, mock_streamlit_state):
    """Verify that load_session_state returns False if state file does not exist."""
    test_state_file = tmp_path / "non_existent_file.json"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state.clear()
    success = app.load_session_state()
    assert not success


def test_load_corrupt_state(tmp_path, monkeypatch, mock_streamlit_state):
    """A corrupt state file is set aside as .corrupt and load returns False."""
    test_state_file = tmp_path / "draft_state.json"
    test_state_file.write_text("{not valid json !!!")
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    success = app.load_session_state()
    assert not success
    assert not test_state_file.exists()
    assert (tmp_path / "draft_state.json.corrupt").exists()


def test_drafted_players_saved_as_id_refs(tmp_path, monkeypatch, mock_streamlit_state):
    """Drafted players from the database are stored as id refs and rehydrated on load."""
    df = app.load_data()
    real_player = df.iloc[0].to_dict()
    fake_player = {"player_id": "imported_Alice_ST", "short_name": "Ghost", "overall": 70}

    test_state_file = tmp_path / "draft_state.json"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["drafted_players"] = {
        "Alice": {"ST": real_player, "SUB 1": fake_player}
    }
    app.save_session_state()

    with open(test_state_file) as f:
        data = json.load(f)
    # Known player collapses to its id; unknown player keeps the full dict
    assert data["drafted_players"]["Alice"]["ST"] == str(real_player["player_id"])
    assert data["drafted_players"]["Alice"]["SUB 1"]["short_name"] == "Ghost"

    mock_streamlit_state.clear()
    assert app.load_session_state()
    squad = mock_streamlit_state["drafted_players"]["Alice"]
    assert squad["ST"]["short_name"] == real_player["short_name"]
    assert squad["ST"]["overall"] == real_player["overall"]
    assert squad["SUB 1"]["short_name"] == "Ghost"


def test_save_with_full_player_dicts_is_json_safe(tmp_path, monkeypatch, mock_streamlit_state):
    """Real df rows carry a frozenset pos_set column; saving must still produce valid JSON."""
    df = app.load_data()
    player = df.iloc[0].to_dict()
    assert isinstance(player.get("pos_set"), frozenset)  # precondition

    test_state_file = tmp_path / "draft_state.json"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["bans"] = {"Alice": [player]}
    mock_streamlit_state["drafted_players"] = {"Alice": {"ST": {**player, "player_id": "not_in_db"}}}
    app.save_session_state()

    assert test_state_file.exists(), "save silently failed"
    assert not (tmp_path / "draft_state.json.tmp").exists()
    data = json.load(open(test_state_file))
    assert data["bans"]["Alice"][0]["short_name"] == player["short_name"]
    assert "pos_set" not in data["bans"]["Alice"][0]
    assert "pos_set" not in data["drafted_players"]["Alice"]["ST"]


def test_banned_ids_round_trip_as_set(tmp_path, monkeypatch, mock_streamlit_state):
    """banned_player_ids is saved as a list but always loaded back as a set."""
    test_state_file = tmp_path / "draft_state.json"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["banned_player_ids"] = {"3", "1", "2"}
    app.save_session_state()
    mock_streamlit_state.clear()
    assert app.load_session_state()
    assert mock_streamlit_state["banned_player_ids"] == {"1", "2", "3"}
    assert isinstance(mock_streamlit_state["banned_player_ids"], set)
