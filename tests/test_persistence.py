import pytest
import os
import json
import streamlit as st
import app

def test_save_and_load_session_state(tmp_path, monkeypatch, mock_streamlit_state):
    """Test that save_session_state saves data to disk, and load_session_state restores it."""
    test_state_file = tmp_path / "test_draft_state.json"
    monkeypatch.setattr(app, "STATE_FILE", str(test_state_file))
    
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
    
    # Load state (mock_streamlit_state is populated internally)
    # Wait, we need to temporarily un-monkeypatch load_session_state in conftest.py
    # or just call app.load_session_state() directly.
    # In conftest.py we did: monkeypatch.setattr(app, "load_session_state", lambda: True)
    # But wait, in the updated conftest.py, we DID NOT monkeypatch load_session_state!
    # Let's check: yes, in the final conftest.py, we only mocked MockSessionState and UI methods,
    # we removed the monkeypatch on load_session_state! That is perfect!
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
    monkeypatch.setattr(app, "STATE_FILE", str(test_state_file))
    
    mock_streamlit_state.clear()
    success = app.load_session_state()
    assert not success
