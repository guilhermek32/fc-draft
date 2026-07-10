"""Smoke tests: every phase page renders without raising under the mocks."""

import pytest
import streamlit as st

import app
from fcdraft.phases import ban, completed, draft, setup


@pytest.fixture(autouse=True)
def _ui_mocks(monkeypatch, mock_streamlit_state, tmp_path):
    # Buttons never fire, text inputs are empty, selectboxes pick the first option
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: False, raising=False)
    monkeypatch.setattr(st, "text_input", lambda *a, **k: "")
    monkeypatch.setattr(
        st, "selectbox",
        lambda label, options=(), *a, **k: options[0] if len(options) else None,
    )
    # No network / disk writes from smoke tests
    monkeypatch.setattr("fcdraft.cards.get_player_image_base64_cached", lambda pid, url: "data:image/png;base64,x")
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(tmp_path / "draft_state.json"))


def _seed_draft_state(store):
    store["participants"] = ["Alice", "Bob"]
    store["team_names"] = {"Alice": "Alice FC", "Bob": "Bob FC"}
    store["formations"] = {"Alice": "4-3-3", "Bob": "3-5-2"}
    store["bench_slots"] = 2
    store["bans"] = {"Alice": [], "Bob": []}
    store["ban_submissions"] = {"Alice": False, "Bob": False}
    store["drafted_players"] = {"Alice": {}, "Bob": {}}
    store["draft_sequence"] = [
        {"round": 1, "pick_in_round": 1, "overall_pick": 1, "participant": "Alice"},
        {"round": 1, "pick_in_round": 2, "overall_pick": 2, "participant": "Bob"},
    ]
    store["current_pick_index"] = 0
    store["draft_history"] = []


def test_setup_phase_renders(mock_streamlit_state):
    setup.render()


def test_ban_phase_renders_login_gateway(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = None
    ban.render()


def test_ban_phase_renders_generated_passwords_panel(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = None
    mock_streamlit_state["generated_passwords"] = {"Alice": "abc23456", "Bob": "def23456"}
    ban.render()


def test_ban_phase_renders_picker_when_authed(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = "Alice"
    ban.render()


def test_ban_phase_renders_locked_view(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = "Alice"
    mock_streamlit_state["ban_submissions"] = {"Alice": True, "Bob": False}
    mock_streamlit_state["bans"] = {
        "Alice": [{"player_id": "1", "short_name": "P1", "overall": 88}],
        "Bob": [],
    }
    ban.render()


def test_ban_phase_renders_reveal_room(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["ban_submissions"] = {"Alice": True, "Bob": True}
    mock_streamlit_state["bans"] = {
        "Alice": [{"player_id": "1", "short_name": "P1", "overall": 88}],
        "Bob": [{"player_id": "2", "short_name": "P2", "overall": 85}],
    }
    ban.render()


def test_draft_phase_renders_spectator(mock_streamlit_state):
    """No login: waiting room + login gateway, no pick UI."""
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = None
    draft.render()


def test_draft_phase_renders_on_clock_picker(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = "Alice"  # Alice is pick 1
    draft.render()


def test_draft_phase_renders_waiting_participant(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = "Bob"  # not on the clock
    draft.render()


def test_draft_phase_renders_admin_session(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    mock_streamlit_state["authed_participant"] = None
    mock_streamlit_state["is_admin"] = True
    mock_streamlit_state["current_pick_index"] = 1  # undo becomes available
    mock_streamlit_state["draft_history"] = [{"picker": "Alice", "slot": "ST", "player_name": "P", "overall": 90, "position": "ST", "round": 1, "pick_overall": 1}]
    draft.render()


def test_completed_phase_renders(mock_streamlit_state):
    _seed_draft_state(mock_streamlit_state)
    completed.render()


def test_get_pitch_layout_rows():
    layout = app.get_pitch_layout("4-3-3", {})
    assert [item["slot"] for item in layout["gk"]] == ["GK"]
    assert len(layout["defense"]) == 4
    assert len(layout["midfield"]) == 3
    assert len(layout["attack"]) == 3
    # Left-to-right ordering: LB before CBs before RB
    assert layout["defense"][0]["slot"] == "LB"
    assert layout["defense"][-1]["slot"] == "RB"
