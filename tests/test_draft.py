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
    state_file = tmp_path / "draft_state.db"
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
    from fcdraft.draft import commit_pick
    from fcdraft.state import read_state_doc, write_state_doc

    state_file = _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    on_disk = read_state_doc(str(state_file))
    on_disk["current_pick_index"] = 1  # Bob is now on the clock
    write_state_doc(str(state_file), on_disk)

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
    from fcdraft.draft import commit_pick
    from fcdraft.state import read_state_doc, write_state_doc

    state_file = _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    on_disk = read_state_doc(str(state_file))
    on_disk["drafted_players"] = {"Alice": {"ST": {"player_id": "zzz", "short_name": "Taken", "overall": 80}}}
    write_state_doc(str(state_file), on_disk)
    assert commit_pick("Alice", "ST", _player()) is False

    on_disk["drafted_players"] = {"Alice": {}}
    on_disk["banned_player_ids"] = ["p1"]
    write_state_doc(str(state_file), on_disk)
    assert commit_pick("Alice", "LW", _player()) is False
    assert mock_streamlit_state["draft_history"] == []


# --- Pick timer / relegation ---

def _pick(overall_pick, participant, round_=1):
    return {"round": round_, "pick_in_round": 1, "overall_pick": overall_pick, "participant": participant}


def _seed_timer_state(store, tmp_path, monkeypatch, sequence, expired_deadline):
    """Draft-phase state on disk + in memory with an already-expired pick clock."""
    state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(state_file))
    store.update({
        "participants": sorted({p["participant"] for p in sequence}),
        "team_names": {}, "formations": {}, "bench_slots": 0,
        "bans": {}, "ban_submissions": {},
        "drafted_players": {}, "banned_player_ids": set(),
        "draft_sequence": sequence,
        "current_pick_index": 0,
        "draft_history": [],
        "pick_deadline": expired_deadline,
        "last_timeout": None,
    })
    app.save_session_state()
    return state_file


def test_timeout_relegates_all_picks_to_end(tmp_path, monkeypatch, mock_streamlit_state):
    import time
    from fcdraft.draft import apply_pick_timeout

    expired = time.time() - 5
    seq = [
        _pick(1, "Alice"), _pick(2, "Bob"), _pick(3, "Cara"),
        _pick(4, "Cara", 2), _pick(5, "Bob", 2), _pick(6, "Alice", 2),
    ]
    _seed_timer_state(mock_streamlit_state, tmp_path, monkeypatch, seq, expired)

    assert apply_pick_timeout(expired) is True
    order = [p["participant"] for p in mock_streamlit_state["draft_sequence"]]
    assert order == ["Bob", "Cara", "Cara", "Bob", "Alice", "Alice"]
    assert [p["overall_pick"] for p in mock_streamlit_state["draft_sequence"]] == [1, 2, 3, 4, 5, 6]
    assert mock_streamlit_state["last_timeout"] == {"participant": "Alice", "at_pick": 1}
    assert mock_streamlit_state["pick_deadline"] > time.time()  # clock renewed


def test_second_relegation_keeps_relative_order(tmp_path, monkeypatch, mock_streamlit_state):
    """Two players timing out end up drafting in the same order at the back."""
    import time
    from fcdraft.draft import apply_pick_timeout

    expired = time.time() - 5
    seq = [
        _pick(1, "Alice"), _pick(2, "Bob"), _pick(3, "Cara"),
        _pick(4, "Cara", 2), _pick(5, "Bob", 2), _pick(6, "Alice", 2),
    ]
    _seed_timer_state(mock_streamlit_state, tmp_path, monkeypatch, seq, expired)

    assert apply_pick_timeout(expired) is True  # relegates Alice; Bob now on the clock
    second_expired = mock_streamlit_state["pick_deadline"]
    monkeypatch.setattr("fcdraft.draft.time", type("T", (), {"time": staticmethod(lambda: second_expired + 1)}))
    assert apply_pick_timeout(second_expired) is True  # relegates Bob too

    order = [p["participant"] for p in mock_streamlit_state["draft_sequence"]]
    assert order == ["Cara", "Cara", "Alice", "Alice", "Bob", "Bob"]


def test_timeout_noop_when_another_session_handled_it(tmp_path, monkeypatch, mock_streamlit_state):
    import time
    from fcdraft.draft import apply_pick_timeout
    from fcdraft.state import read_state_doc, write_state_doc

    expired = time.time() - 5
    seq = [_pick(1, "Alice"), _pick(2, "Bob")]
    state_file = _seed_timer_state(mock_streamlit_state, tmp_path, monkeypatch, seq, expired)

    # Another device already renewed the clock on disk.
    on_disk = read_state_doc(str(state_file))
    on_disk["pick_deadline"] = time.time() + 60
    write_state_doc(str(state_file), on_disk)

    assert apply_pick_timeout(expired) is False
    order = [p["participant"] for p in mock_streamlit_state["draft_sequence"]]
    assert order == ["Alice", "Bob"]
    assert mock_streamlit_state["last_timeout"] is None


def test_timeout_loops_when_only_relegated_picks_remain(tmp_path, monkeypatch, mock_streamlit_state):
    import time
    from fcdraft.draft import apply_pick_timeout

    expired = time.time() - 5
    seq = [_pick(1, "Alice"), _pick(2, "Alice", 2)]
    _seed_timer_state(mock_streamlit_state, tmp_path, monkeypatch, seq, expired)

    assert apply_pick_timeout(expired) is True
    order = [p["participant"] for p in mock_streamlit_state["draft_sequence"]]
    assert order == ["Alice", "Alice"]  # nothing to push behind; clock just restarts
    assert mock_streamlit_state["pick_deadline"] > time.time()


def test_commit_pick_renews_deadline(tmp_path, monkeypatch, mock_streamlit_state):
    import time
    from fcdraft.draft import commit_pick

    _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    assert commit_pick("Alice", "ST", _player()) is True
    assert mock_streamlit_state["pick_deadline"] > time.time()

    # Last pick of the draft: the clock stops.
    mock_streamlit_state["authed_participant"] = "Bob"
    app.save_session_state()
    assert commit_pick("Bob", "ST", _player() | {"player_id": "p2"}) is True
    assert mock_streamlit_state["pick_deadline"] is None


def test_pick_deadline_persists_across_save_load(tmp_path, monkeypatch, mock_streamlit_state):
    import time

    expired = time.time() + 42.5
    seq = [_pick(1, "Alice")]
    _seed_timer_state(mock_streamlit_state, tmp_path, monkeypatch, seq, expired)

    mock_streamlit_state["pick_deadline"] = None  # wipe memory, reload from disk
    assert app.load_session_state() is True
    assert mock_streamlit_state["pick_deadline"] == expired


def test_commit_pick_aborts_on_already_drafted_player(tmp_path, monkeypatch, mock_streamlit_state):
    """A player another participant already drafted (now visible in search) cannot be picked."""
    from fcdraft.draft import commit_pick
    from fcdraft.state import read_state_doc, write_state_doc

    state_file = _seed_commit_state(mock_streamlit_state, tmp_path, monkeypatch)
    on_disk = read_state_doc(str(state_file))
    on_disk["drafted_players"] = {"Bob": {"ST": {"player_id": "p1", "short_name": "P1", "overall": 90}}}
    write_state_doc(str(state_file), on_disk)

    assert commit_pick("Alice", "ST", _player()) is False
    assert mock_streamlit_state["draft_history"] == []
    assert "ST" not in mock_streamlit_state["drafted_players"].get("Alice", {})


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


def test_autopick_lands_only_once_for_same_deadline(tmp_path, monkeypatch, mock_streamlit_state):
    """Two sessions enforcing the same expired deadline auto-pick exactly one player."""
    import time
    from fcdraft.draft import apply_pick_autopick

    expired = time.time() - 5
    seq = [_pick(1, "Alice"), _pick(2, "Bob")]
    _seed_timer_state(mock_streamlit_state, tmp_path, monkeypatch, seq, expired)
    mock_streamlit_state["formations"] = {"Alice": "4-3-3", "Bob": "4-3-3"}
    mock_streamlit_state["drafted_players"] = {"Alice": {}, "Bob": {}}
    app.save_session_state()

    assert apply_pick_autopick(expired) is True
    assert mock_streamlit_state["current_pick_index"] == 1
    assert len(mock_streamlit_state["draft_history"]) == 1
    assert mock_streamlit_state["pick_deadline"] > time.time()  # clock renewed

    # A second session observing the same (now stale) deadline must no-op.
    assert apply_pick_autopick(expired) is False
    assert mock_streamlit_state["current_pick_index"] == 1
    assert len(mock_streamlit_state["draft_history"]) == 1
