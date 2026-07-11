import pytest
import os
import json
import streamlit as st
import app

from fcdraft.state import read_state_doc, write_state_doc


def test_save_and_load_session_state(tmp_path, monkeypatch, mock_streamlit_state):
    """Test that save_session_state saves data to disk, and load_session_state restores it."""
    test_state_file = tmp_path / "test_draft_state.db"
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

    # Check that the DB was created
    assert test_state_file.exists()

    # Check saved content
    data = read_state_doc(str(test_state_file))
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
    """Verify that load_session_state returns False if the state DB does not exist."""
    test_state_file = tmp_path / "non_existent_file.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state.clear()
    success = app.load_session_state()
    assert not success


def test_load_corrupt_state(tmp_path, monkeypatch, mock_streamlit_state):
    """A corrupt state DB is set aside as .corrupt and load returns False."""
    test_state_file = tmp_path / "draft_state.db"
    test_state_file.write_bytes(b"this is definitely not a sqlite database !!!")
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    success = app.load_session_state()
    assert not success
    assert not test_state_file.exists()
    assert (tmp_path / "draft_state.db.corrupt").exists()


def test_legacy_json_migrates_into_db(tmp_path, monkeypatch, mock_streamlit_state):
    """A pre-SQLite draft_state.json is imported into the DB once and renamed."""
    from fcdraft.state import peek_state_version

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    legacy_file = tmp_path / "draft_state.json"
    legacy_file.write_text(json.dumps({
        "state_version": 7, "phase": "ban", "participants": ["Alice"], "bans": {"Alice": []},
    }))

    assert app.load_session_state()
    assert mock_streamlit_state["participants"] == ["Alice"]
    assert mock_streamlit_state["state_version"] == 7
    assert peek_state_version() == 7
    # The JSON was renamed so the import never repeats
    assert not legacy_file.exists()
    assert (tmp_path / "draft_state.json.imported").exists()
    assert read_state_doc(str(test_state_file))["phase"] == "ban"


def test_drafted_players_saved_as_id_refs(tmp_path, monkeypatch, mock_streamlit_state):
    """Drafted players from the database are stored as id refs and rehydrated on load."""
    df = app.load_data()
    real_player = df.iloc[0].to_dict()
    fake_player = {"player_id": "imported_Alice_ST", "short_name": "Ghost", "overall": 70}

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["drafted_players"] = {
        "Alice": {"ST": real_player, "SUB 1": fake_player}
    }
    app.save_session_state()

    data = read_state_doc(str(test_state_file))
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

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["bans"] = {"Alice": [{**player, "player_id": "not_in_db"}]}
    mock_streamlit_state["drafted_players"] = {"Alice": {"ST": {**player, "player_id": "not_in_db"}}}
    app.save_session_state()

    data = read_state_doc(str(test_state_file))
    assert data is not None, "save silently failed"
    assert data["bans"]["Alice"][0]["short_name"] == player["short_name"]
    assert "pos_set" not in data["bans"]["Alice"][0]
    assert "pos_set" not in data["drafted_players"]["Alice"]["ST"]


def test_bans_saved_as_id_refs_without_player_names(tmp_path, monkeypatch, mock_streamlit_state):
    """Pre-reveal bans persist as bare player ids (no names on disk) and rehydrate on load."""
    df = app.load_data()
    real_player = df.iloc[0].to_dict()

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["bans"] = {"Alice": [real_player]}
    app.save_session_state()

    data = read_state_doc(str(test_state_file))
    assert data["bans"]["Alice"] == [str(real_player["player_id"])]
    assert real_player["short_name"] not in json.dumps(data["bans"])

    mock_streamlit_state.clear()
    assert app.load_session_state()
    loaded = mock_streamlit_state["bans"]["Alice"][0]
    assert loaded["short_name"] == real_player["short_name"]
    assert loaded["overall"] == real_player["overall"]


def test_auth_credentials_round_trip_without_plaintext(tmp_path, monkeypatch, mock_streamlit_state):
    """Credentials persist as salted hashes; plaintext passwords never reach disk."""
    from fcdraft.auth import check_credential, set_credential

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["auth_credentials"] = {}
    set_credential("Alice", "hunter2")
    app.save_session_state()

    assert "hunter2" not in json.dumps(read_state_doc(str(test_state_file)))

    mock_streamlit_state.clear()
    assert app.load_session_state()
    assert check_credential("Alice", "hunter2")
    assert not check_credential("Alice", "wrong")


def test_legacy_state_without_credentials_loads(tmp_path, monkeypatch, mock_streamlit_state):
    """State documents written before passwords existed load with empty credentials."""
    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    legacy = {"phase": "ban", "participants": ["Alice"], "bans": {"Alice": []}}
    write_state_doc(str(test_state_file), legacy)

    assert app.load_session_state()
    assert mock_streamlit_state["auth_credentials"] == {}


def test_refresh_shared_state_picks_up_other_sessions(tmp_path, monkeypatch, mock_streamlit_state):
    """refresh_shared_state re-reads shared keys from disk without touching login state."""
    from fcdraft.state import refresh_shared_state

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    on_disk = {
        "phase": "draft",
        "bans": {"Alice": [], "Bob": []},
        "ban_submissions": {"Alice": True, "Bob": False},
        "auth_credentials": {"Alice": {"salt": "00", "hash": "00"}},
        "banned_player_ids": ["9"],
        "drafted_players": {"Alice": {"ST": {"player_id": "x", "short_name": "Ghost"}}},
        "draft_sequence": [{"round": 1, "participant": "Alice"}],
        "current_pick_index": 1,
        "draft_history": [{"picker": "Alice", "slot": "ST"}],
        "state_version": 7,
    }
    write_state_doc(str(test_state_file), on_disk)

    mock_streamlit_state["ban_submissions"] = {"Alice": False, "Bob": False}
    mock_streamlit_state["current_pick_index"] = 0
    mock_streamlit_state["authed_participant"] = "Bob"
    mock_streamlit_state["is_admin"] = True
    refresh_shared_state()

    assert mock_streamlit_state["ban_submissions"] == {"Alice": True, "Bob": False}
    assert mock_streamlit_state["auth_credentials"] == {"Alice": {"salt": "00", "hash": "00"}}
    assert mock_streamlit_state["banned_player_ids"] == {"9"}
    assert mock_streamlit_state["drafted_players"]["Alice"]["ST"]["short_name"] == "Ghost"
    assert mock_streamlit_state["draft_sequence"] == [{"round": 1, "participant": "Alice"}]
    assert mock_streamlit_state["current_pick_index"] == 1
    assert mock_streamlit_state["draft_history"] == [{"picker": "Alice", "slot": "ST"}]
    assert mock_streamlit_state["state_version"] == 7
    # Per-session keys untouched
    assert mock_streamlit_state["authed_participant"] == "Bob"
    assert mock_streamlit_state["is_admin"] is True


def test_state_version_increments_from_disk(tmp_path, monkeypatch, mock_streamlit_state):
    """Saves base the version on the stored value so alternating writers never repeat."""
    from fcdraft.state import peek_state_version

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    write_state_doc(str(test_state_file), {}, version=5)
    mock_streamlit_state["state_version"] = 0  # stale in-memory value
    app.save_session_state()

    assert peek_state_version() == 6
    assert mock_streamlit_state["state_version"] == 6


def test_peek_state_version_fallbacks(tmp_path, monkeypatch, mock_streamlit_state):
    """A missing DB never looks like a remote change; a stored row wins over memory."""
    from fcdraft.state import peek_state_version

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["state_version"] = 3
    assert peek_state_version() == 3  # missing DB -> in-memory value

    write_state_doc(str(test_state_file), {"phase": "ban"}, version=12)
    assert peek_state_version() == 12


def test_authed_participant_never_persisted(tmp_path, monkeypatch, mock_streamlit_state):
    """The per-browser login key must not be written to disk."""
    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["authed_participant"] = "Alice"
    mock_streamlit_state["generated_passwords"] = {"Alice": "abc23456"}
    mock_streamlit_state["auth_token"] = "session-own-token"
    app.save_session_state()

    data = read_state_doc(str(test_state_file))
    assert "authed_participant" not in data
    assert "generated_passwords" not in data
    assert "abc23456" not in json.dumps(data)
    assert "auth_token" not in data


def test_auth_tokens_round_trip_and_refresh(tmp_path, monkeypatch, mock_streamlit_state):
    """The token map persists and is picked up by refresh_shared_state."""
    from fcdraft.state import refresh_shared_state

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["auth_tokens"] = {"tok1": {"participant": "Alice", "is_admin": False}}
    app.save_session_state()

    mock_streamlit_state.clear()
    assert app.load_session_state()
    assert mock_streamlit_state["auth_tokens"] == {"tok1": {"participant": "Alice", "is_admin": False}}

    # Simulate a session that has not seen the state yet (no version signature):
    # refresh must pick the tokens up from the DB. A session whose signature
    # matches the stored version skips the reload by design.
    mock_streamlit_state["auth_tokens"] = {}
    mock_streamlit_state.pop("state_signature", None)
    refresh_shared_state()
    assert mock_streamlit_state["auth_tokens"] == {"tok1": {"participant": "Alice", "is_admin": False}}


def test_refresh_skips_reload_when_file_unchanged(tmp_path, monkeypatch, mock_streamlit_state):
    """An unchanged state DB must not be re-read on every rerun."""
    from fcdraft.state import refresh_shared_state

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["auth_tokens"] = {"tok1": {"participant": "Alice", "is_admin": False}}
    app.save_session_state()

    # In-memory divergence without a disk change stays as-is (the fast path).
    mock_streamlit_state["auth_tokens"] = {}
    refresh_shared_state()
    assert mock_streamlit_state["auth_tokens"] == {}


def test_state_file_is_gitignored():
    """The plaintext-adjacent state DB (and its WAL sidecars) must never be committable."""
    import subprocess
    from fcdraft.config import STATE_FILE

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for target in (STATE_FILE, f"{STATE_FILE}-wal", f"{STATE_FILE}-shm"):
        result = subprocess.run(
            ["git", "check-ignore", target],
            cwd=repo_root,
            capture_output=True,
        )
        assert result.returncode == 0, f"{target} is not gitignored"


def test_banned_ids_round_trip_as_set(tmp_path, monkeypatch, mock_streamlit_state):
    """banned_player_ids is saved as a list but always loaded back as a set."""
    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    mock_streamlit_state["banned_player_ids"] = {"3", "1", "2"}
    app.save_session_state()
    mock_streamlit_state.clear()
    assert app.load_session_state()
    assert mock_streamlit_state["banned_player_ids"] == {"1", "2", "3"}
    assert isinstance(mock_streamlit_state["banned_player_ids"], set)


def test_save_cas_rejects_stale_expected_version(tmp_path, monkeypatch, mock_streamlit_state):
    """save_session_state(expected_version=...) only writes when the DB still matches."""
    from fcdraft.state import peek_state_version, save_session_state

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    write_state_doc(str(test_state_file), {"phase": "draft"}, version=5)
    before = read_state_doc(str(test_state_file))

    mock_streamlit_state["state_version"] = 3  # this session lost a race
    assert save_session_state(expected_version=3) is False
    assert read_state_doc(str(test_state_file)) == before  # nothing written
    assert peek_state_version() == 5

    assert save_session_state(expected_version=5) is True
    assert peek_state_version() == 6


def test_write_state_doc_bumps_version_by_default(tmp_path, monkeypatch, mock_streamlit_state):
    """A plain write_state_doc always looks like a remote change to other sessions."""
    from fcdraft.state import peek_state_version

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    write_state_doc(str(test_state_file), {"phase": "ban"})
    assert peek_state_version() == 1
    write_state_doc(str(test_state_file), {"phase": "draft"})
    assert peek_state_version() == 2
    # A doc-embedded state_version key lands in the version column, not the payload.
    write_state_doc(str(test_state_file), {"phase": "draft", "state_version": 12})
    assert peek_state_version() == 12
    assert "state_version" not in read_state_doc(str(test_state_file))


def test_save_without_expected_version_keeps_unconditional_behavior(tmp_path, monkeypatch, mock_streamlit_state):
    """Callers that pass no expected_version still always write (and report success)."""
    from fcdraft.state import peek_state_version

    test_state_file = tmp_path / "draft_state.db"
    monkeypatch.setattr("fcdraft.state.STATE_FILE", str(test_state_file))

    write_state_doc(str(test_state_file), {}, version=9)
    mock_streamlit_state["state_version"] = 2  # stale, but no CAS requested
    assert app.save_session_state() is True
    assert peek_state_version() == 10
