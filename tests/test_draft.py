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
