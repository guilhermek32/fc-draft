import pytest
import streamlit as st
import app

def test_get_formation_slots():
    """Verify slots match the specified tactical formation."""
    # Test 4-3-3
    slots = app.get_formation_slots("4-3-3")
    assert len(slots) == 11
    assert "ST" in slots
    assert "LW" in slots
    assert "RW" in slots
    assert "CB 1" in slots
    assert "CB 2" in slots
    
    # Test 3-5-2
    slots_352 = app.get_formation_slots("3-5-2")
    assert len(slots_352) == 11
    assert "ST 1" in slots_352
    assert "ST 2" in slots_352
    assert "CB 1" in slots_352
    assert "CB 3" in slots_352

def test_get_base_position():
    """Verify compound slot names map to standard base FIFA positions."""
    assert app.get_base_position("CB 1") == "CB"
    assert app.get_base_position("ST 2") == "ST"
    assert app.get_base_position("SUB 4") == "SUB"
    assert app.get_base_position("GK") == "GK"

def _seed_commit_state(store, tmp_path, monkeypatch):
    """Draft-phase state on disk + in memory where Alice is on the clock."""
    import json

    state_file = tmp_path / "draft_state.json"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(state_file))

    store.update({
        "phase": "draft",
        "participants": ["Alice", "Bob"],
        "formations": {"Alice": "4-3-3", "Bob": "4-3-3"},
        "bench_slots": 0,
        "bans": {}, "ban_submissions": {},
        "drafted_players": {"Alice": {}, "Bob": {}},
        "draft_sequence": [
            {"round": 1, "pick_in_round": 1, "overall_pick": 1, "participant": "Alice"},
            {"round": 1, "pick_in_round": 2, "overall_pick": 2, "participant": "Bob"},
        ],
        "current_pick_index": 0,
        "draft_history": [],
        "banned_player_ids": set(),
        "authed_participant": "Alice",
    })
    app.save_session_state()
    return state_file


def _player():
    return {"player_id": "p1", "short_name": "P1", "overall": 90, "player_positions": "ST"}


def test_commit_pick_happy_path(tmp_path, monkeypatch, mock_streamlit_state):
    from fcdraft.draft import commit_pick

    _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    assert commit_pick("Alice", "ST", _player()) is True
    assert mock_streamlit_state["current_pick_index"] == 1
    assert mock_streamlit_state["drafted_players"]["Alice"]["ST"]["short_name"] == "P1"
    assert len(mock_streamlit_state["draft_history"]) == 1


def test_commit_pick_aborts_when_turn_moved_on(tmp_path, monkeypatch, mock_streamlit_state):
    """Another device already advanced the draft on disk: the stale click must not land."""
    import json
    from fcdraft.draft import commit_pick

    state_file = _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    on_disk = json.loads(state_file.read_text())
    on_disk["current_pick_index"] = 1  # Bob is now on the clock
    state_file.write_text(json.dumps(on_disk))

    assert commit_pick("Alice", "ST", _player()) is False
    assert mock_streamlit_state["current_pick_index"] == 1  # refreshed, not advanced
    assert mock_streamlit_state["draft_history"] == []


def test_commit_pick_aborts_for_wrong_session(tmp_path, monkeypatch, mock_streamlit_state):
    from fcdraft.draft import commit_pick

    _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    mock_streamlit_state["authed_participant"] = "Bob"  # not the on-clock participant

    assert commit_pick("Alice", "ST", _player()) is False
    assert mock_streamlit_state["current_pick_index"] == 0


def test_commit_pick_aborts_on_filled_slot_and_banned_player(tmp_path, monkeypatch, mock_streamlit_state):
    import json
    from fcdraft.draft import commit_pick

    state_file = _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    on_disk = json.loads(state_file.read_text())
    on_disk["drafted_players"] = {"Alice": {"ST": {"player_id": "zzz", "short_name": "Taken", "overall": 80}}}
    state_file.write_text(json.dumps(on_disk))
    assert commit_pick("Alice", "ST", _player()) is False

    on_disk["drafted_players"] = {"Alice": {}}
    on_disk["banned_player_ids"] = ["p1"]
    state_file.write_text(json.dumps(on_disk))
    assert commit_pick("Alice", "LW", _player()) is False
    assert mock_streamlit_state["draft_history"] == []


def test_auto_draft_remaining(mock_streamlit_state):
    """Verify that auto_draft_remaining automatically drafts matching players for all empty slots."""
    # Setup mock draft sequence and participants
    mock_streamlit_state["participants"] = ["Alice"]
    mock_streamlit_state["bench_slots"] = 2
    mock_streamlit_state["formations"] = {"Alice": "4-3-3"}
    mock_streamlit_state["drafted_players"] = {"Alice": {}}
    mock_streamlit_state["banned_player_ids"] = set()
    
    # We will set a custom draft sequence of 2 picks for Alice
    mock_streamlit_state["draft_sequence"] = [
        {"round": 1, "pick": 1, "participant": "Alice"},
        {"round": 2, "pick": 2, "participant": "Alice"}
    ]
    mock_streamlit_state["current_pick_index"] = 0
    mock_streamlit_state["draft_history"] = []
    
    # Run auto-draft
    app.auto_draft_remaining(filter_mode="Flexible")
    
    # Verify that Alice now has 2 drafted players (since there are 2 rounds in the sequence)
    drafted = mock_streamlit_state["drafted_players"]["Alice"]
    assert len(drafted) == 2
    
    # Verify that the draft history has logged the choices
    assert len(mock_streamlit_state["draft_history"]) == 2
    
    # Verify current pick index has advanced to the end
    assert mock_streamlit_state["current_pick_index"] == 2
