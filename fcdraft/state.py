"""Draft session persistence and session-state initialization.

On disk, drafted players are stored as player_id references and rehydrated from
the player database on load; players that don't exist in the database (e.g.
reconstructed from an imported roster CSV) are stored as full dicts. In
st.session_state the squads always hold full player dicts.

Concurrency model: all browser sessions are threads of one Streamlit process,
so _STATE_LOCK serializes every refresh → mutate → save in-process; the DB's
compare-and-swap on the version column is the backstop against writers this
lock can't see (a second process pointed at the same DB). Mutating writes pass
expected_version so a stale save fails instead of clobbering; only the setup
phase writes unconditionally (it wholesale-replaces the state by design).
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from fcdraft.config import DEFAULT_BENCH_SLOTS, STATE_FILE
from fcdraft.data import get_player_by_id
from fcdraft.formations import build_snake_sequence

# Serializes every read-modify-write of the shared state DB. All browser
# sessions are threads of the single Streamlit process, so one module-level
# lock covers them all. Reentrant because enforcement paths nest (e.g.
# apply_pick_autopick falls back into apply_pick_timeout).
_STATE_LOCK = threading.RLock()


@contextmanager
def shared_state_lock():
    """Hold this around refresh → validate → mutate → save so no other session
    can write the state DB between the read and the write."""
    with _STATE_LOCK:
        yield


_SESSION_DEFAULTS = {
    "phase": "setup",
    "participants": [],
    "team_names": {},
    "formations": {},
    "bench_slots": DEFAULT_BENCH_SLOTS,
    "bans": {},
    "ban_submissions": {},
    "auth_credentials": {},
    # URL login tokens ({token: {"participant", "is_admin"}}); persisted so a
    # pitch-click navigation (new session) can restore the login.
    "auth_tokens": {},
    # This browser session's own URL token; never persisted.
    "auth_token": None,
    # Which participant is logged in for this browser session; never persisted.
    "authed_participant": None,
    # Whether this browser session is the admin superuser; never persisted.
    "is_admin": False,
    # Monotonic save counter used to order concurrent saves.
    "state_version": 0,
    # DB version as last loaded by THIS session; the poller and per-render
    # refresh skip all work while it is unchanged.
    "state_signature": None,
    "banned_player_ids": set(),
    "drafted_players": {},
    "draft_sequence": [],
    "current_pick_index": 0,
    "draft_history": [],
    # Participants removed during the ban phase ({name: stashed data}), kept so
    # an admin can restore them.
    "removed_participants": {},
    # Absolute unix-epoch deadline for the current pick (None = no timer running).
    "pick_deadline": None,
    # Last pick-timer expiry ({"participant", "at_pick"}); shown as a notice on all devices.
    "last_timeout": None,
}


def normalize_banned_ids(value):
    """Session state always holds a set of banned player ids."""
    return set(value) if value else set()


def _json_safe_player(player):
    """Strip derived, non-JSON-serializable columns (e.g. the pos_set frozenset)."""
    if not isinstance(player, dict):
        return player
    return {
        k: (sorted(v) if isinstance(v, (set, frozenset)) else v)
        for k, v in player.items()
        if k not in ("pos_set", "search_blob", "is_banned", "picked_by")
    }


def _slim_squads(drafted_players):
    """Replace player dicts with id references where the id exists in the database."""
    slim = {}
    for participant, squad in drafted_players.items():
        slim[participant] = {}
        for slot, player in squad.items():
            player_id = player.get("player_id") if isinstance(player, dict) else None
            if player_id is not None and get_player_by_id(str(player_id)) is not None:
                slim[participant][slot] = str(player_id)
            else:
                slim[participant][slot] = _json_safe_player(player)
    return slim


def _rehydrate_squads(drafted_players):
    """Resolve id references back into full player dicts."""
    full = {}
    for participant, squad in drafted_players.items():
        full[participant] = {}
        for slot, value in squad.items():
            if isinstance(value, str):
                player = get_player_by_id(value)
                if player is None:
                    continue  # player id no longer resolvable; drop the slot
                full[participant][slot] = player
            else:
                full[participant][slot] = value
    return full


def _slim_bans(bans):
    """Replace ban player dicts with id references where the id exists in the database."""
    slim = {}
    for participant, player_list in bans.items():
        slim[participant] = []
        for player in player_list:
            player_id = player.get("player_id") if isinstance(player, dict) else None
            if player_id is not None and get_player_by_id(str(player_id)) is not None:
                slim[participant].append(str(player_id))
            else:
                slim[participant].append(_json_safe_player(player))
    return slim


def _rehydrate_bans(bans):
    """Resolve ban id references back into full player dicts (legacy full dicts pass through)."""
    full = {}
    for participant, player_list in bans.items():
        full[participant] = []
        for value in player_list:
            if isinstance(value, str):
                player = get_player_by_id(value)
                if player is None:
                    continue  # player id no longer resolvable; drop the ban
                full[participant].append(player)
            else:
                full[participant].append(value)
    return full


# The state stays one JSON document, stored in a single SQLite row; the
# version lives in its own column so CAS is enforced by the database itself.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS draft_state (
    id      INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL,
    payload TEXT NOT NULL
)
"""


def _connect(path):
    conn = sqlite3.connect(path, timeout=5)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
    except sqlite3.Error:
        conn.close()
        raise
    return conn


def _connect_ro(path):
    """Read-only connection for the poller/refresh hot path.

    Skips the WAL/synchronous PRAGMAs — journal mode is a persistent property
    of the DB set by the write path, and re-issuing it on every 2s poll from
    every session is pure connection churn.
    """
    return sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True, timeout=5)


def _read_version(path):
    """The stored version, or None (missing DB / no row / unreadable DB)."""
    if not os.path.exists(path):
        return None
    try:
        conn = _connect_ro(path)
        try:
            row = conn.execute("SELECT version FROM draft_state WHERE id = 1").fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    return row[0] if row else None


def _read_doc(path):
    """(version, state dict) from the DB, or None if there is nothing to read.

    Raises sqlite3.DatabaseError / json.JSONDecodeError on a corrupt DB so
    load_session_state can set the file aside.
    """
    if not os.path.exists(path):
        return None
    conn = _connect_ro(path)
    try:
        try:
            row = conn.execute("SELECT version, payload FROM draft_state WHERE id = 1").fetchone()
        except sqlite3.OperationalError:
            return None  # no table yet
    finally:
        conn.close()
    if row is None:
        return None
    state = json.loads(row[1])
    if not isinstance(state, dict):
        return None
    return row[0], state


def _write_doc(path, doc, expected_version):
    """Compare-and-swap write in one transaction.

    Returns the new version, or None when the row exists but its version no
    longer matches expected_version (another process saved in between).
    """
    payload = json.dumps(doc)
    new_version = expected_version + 1
    conn = _connect(path)
    try:
        with conn:
            conn.execute(_SCHEMA)
            cur = conn.execute(
                "UPDATE draft_state SET version = ?, payload = ? WHERE id = 1 AND version = ?",
                (new_version, payload, expected_version),
            )
            if cur.rowcount == 1:
                return new_version
            cur = conn.execute(
                "INSERT OR IGNORE INTO draft_state (id, version, payload) VALUES (1, ?, ?)",
                (new_version, payload),
            )
            return new_version if cur.rowcount == 1 else None
    finally:
        conn.close()


def read_state_doc(path=None):
    """The current state document, or None. Used by tests to inspect the DB."""
    doc = _read_doc(path or STATE_FILE)
    return doc[1] if doc else None


def write_state_doc(path, doc, version=None):
    """Store doc as the single state row, overwriting whatever is there.

    Used by tests to simulate another device writing. version defaults to the
    doc's state_version key, else current+1 so a plain write always looks
    like a remote change. Returns the version.
    """
    doc = dict(doc)
    doc_version = doc.pop("state_version", None)
    if version is None:
        version = doc_version
    if version is None:
        current = _read_version(path)
        version = (current or 0) + 1
    conn = _connect(path)
    try:
        with conn:
            conn.execute(_SCHEMA)
            conn.execute(
                "INSERT INTO draft_state (id, version, payload) VALUES (1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET version = excluded.version, payload = excluded.payload",
                (version, json.dumps(doc)),
            )
    finally:
        conn.close()
    return version


def state_signature(path=None):
    """Cheap change marker for the shared state: the DB version, or None.

    One indexed single-row SELECT — used by the live-sync poller and the
    per-render refresh so unchanged state never costs a payload parse.
    """
    return _read_version(path or STATE_FILE)


def peek_state_version(path=None):
    """The version currently in the DB, without touching session state.

    Used by tests to observe version bumps without a full load.

    On a missing DB or read error, returns the in-memory version so a
    transient failure never looks like a remote change (no rerun storms).
    """
    version = _read_version(path or STATE_FILE)
    if version is None:
        return st.session_state.get("state_version", 0)
    return version


def save_session_state(path=None, expected_version=None):
    """Serialize and save the current draft state to the DB (one transaction).

    When expected_version is given, the write only happens if the stored
    version still matches it (compare-and-swap, enforced by the database); a
    mismatch means another session saved in between and the caller must
    refresh and re-validate. Returns True when the state was written.
    """
    path = path or STATE_FILE
    with _STATE_LOCK:
        disk_version = _read_version(path)
        if disk_version is None:
            # Missing DB/row: base the first version on memory so versions
            # stay monotonic across a reset.
            disk_version = st.session_state.get("state_version", 0)
        if expected_version is not None and disk_version != expected_version:
            return False
        try:
            new_version = _write_doc(path, _build_state_doc(), disk_version)
        except (sqlite3.Error, TypeError, ValueError) as e:
            st.warning(f"Could not save draft state: {e}")
            return False
        if new_version is None:
            return False
        st.session_state.state_version = new_version
        st.session_state.state_signature = new_version
        return True


# Single source of truth for every key shared across sessions through the DB:
# (key, default, to_doc, from_doc). to_doc/from_doc of None mean the value is
# stored as-is. _build_state_doc, load_session_state, and refresh_shared_state
# are all driven from this table — add new shared keys here, nowhere else.
_SHARED_KEYS = (
    ("phase", "setup", None, None),
    ("participants", [], None, None),
    ("team_names", {}, None, None),
    ("formations", {}, None, None),
    ("bench_slots", DEFAULT_BENCH_SLOTS, None, None),
    ("bans", {}, _slim_bans, _rehydrate_bans),
    ("ban_submissions", {}, None, None),
    ("auth_credentials", {}, None, None),
    ("auth_tokens", {}, None, None),
    ("banned_player_ids", [], lambda v: sorted(v or (), key=str), normalize_banned_ids),
    ("drafted_players", {}, _slim_squads, _rehydrate_squads),
    ("draft_sequence", [], None, None),
    ("current_pick_index", 0, None, None),
    ("draft_history", [], None, None),
    ("removed_participants", {}, None, None),
    ("pick_deadline", None, None, None),
    ("last_timeout", None, None, None),
)


def _build_state_doc():
    doc = {}
    for key, default, to_doc, _ in _SHARED_KEYS:
        value = st.session_state.get(key, default)
        doc[key] = to_doc(value) if to_doc else value
    return doc


def _apply_state_doc(state, signature, phase_fallback):
    """Write a state doc into session state (shared keys + version markers)."""
    for key, default, _, from_doc in _SHARED_KEYS:
        if key == "phase":
            st.session_state.phase = state.get("phase", phase_fallback)
            continue
        if key in state:
            raw = state[key]
        else:
            raw = default.copy() if isinstance(default, (dict, list)) else default
        st.session_state[key] = from_doc(raw) if from_doc else raw
    st.session_state.state_version = signature
    st.session_state.state_signature = signature


def load_session_state(path=None):
    """Load saved draft state from the DB if it exists. Returns True on success."""
    path = path or STATE_FILE
    with _STATE_LOCK:
        try:
            doc = _read_doc(path)
        except (sqlite3.DatabaseError, json.JSONDecodeError) as e:
            try:
                os.replace(path, f"{path}.corrupt")
            except OSError:
                pass
            st.warning(f"Saved draft state could not be read and was set aside: {e}")
            return False
        if doc is None:
            return False
    signature, state = doc

    try:
        _apply_state_doc(state, signature, phase_fallback="setup")
        return True
    except (AttributeError, TypeError) as e:
        st.warning(f"Saved draft state has an unexpected shape and was ignored: {e}")
        return False


def refresh_shared_state(path=None):
    """Re-read the multi-user keys from the DB so concurrent sessions converge.

    init_session_state() loads the state only once per browser session, so
    without this a participant's tab would never see submissions made from
    another device. Per-session keys (e.g. authed_participant) are untouched.
    """
    path = path or STATE_FILE
    # Nothing changed since this session last loaded the state: skip the
    # payload parse and rehydration entirely (this runs on every rerun).
    version = _read_version(path)
    if version is None or version == st.session_state.get("state_signature"):
        return
    try:
        doc = _read_doc(path)
    except (sqlite3.DatabaseError, json.JSONDecodeError):
        return
    if doc is None:
        return
    signature, state = doc
    _apply_state_doc(
        state, signature, phase_fallback=st.session_state.get("phase", "setup")
    )


def remove_participant(name):
    """Scrub a participant from all shared state (e.g. a ban-phase no-show).

    The snake order among the remaining participants is preserved; picks are
    renumbered so overall_pick stays gapless. Safe only before the draft
    starts (current_pick_index is 0). The participant's data is stashed in
    removed_participants so restore_participant() can bring them back.
    """
    with _STATE_LOCK:
        refresh_shared_state()
        if name not in st.session_state.participants:
            return
        _remove_participant_locked(name)


def _remove_participant_locked(name):
    base_order = _base_pick_order()
    st.session_state.removed_participants[name] = {
        "team_name": st.session_state.team_names.get(name, f"{name} FC"),
        "formation": st.session_state.formations.get(name),
        "credential": st.session_state.auth_credentials.get(name),
        "base_index": base_order.index(name) if name in base_order else len(base_order),
    }
    if name in st.session_state.participants:
        st.session_state.participants.remove(name)
    for key in ("team_names", "formations", "bans", "ban_submissions",
                "drafted_players", "auth_credentials"):
        st.session_state[key].pop(name, None)
    st.session_state.auth_tokens = {
        token: identity
        for token, identity in st.session_state.auth_tokens.items()
        if identity.get("participant") != name
    }

    new_sequence = []
    overall_pick = 1
    picks_in_round = {}
    for pick in st.session_state.draft_sequence:
        if pick["participant"] == name:
            continue
        picks_in_round[pick["round"]] = picks_in_round.get(pick["round"], 0) + 1
        new_sequence.append({
            "round": pick["round"],
            "pick_in_round": picks_in_round[pick["round"]],
            "overall_pick": overall_pick,
            "participant": pick["participant"],
        })
        overall_pick += 1
    st.session_state.draft_sequence = new_sequence

    save_session_state(expected_version=st.session_state.get("state_version", 0))


def _base_pick_order():
    """Round-1 pick order of the current draft sequence (the snake base order)."""
    return [
        pick["participant"]
        for pick in st.session_state.draft_sequence
        if pick["round"] == 1
    ]


def restore_participant(name):
    """Bring back a participant removed during the ban phase.

    Reinstates their team, formation, and login, with bans unsubmitted so they
    go through the ban phase again. Their picks rejoin the snake sequence at
    the original position where possible. Safe only before the draft starts.
    """
    with _STATE_LOCK:
        refresh_shared_state()
        stash = st.session_state.removed_participants.pop(name, None)
        if stash is None:
            return
        _restore_participant_locked(name, stash)


def _restore_participant_locked(name, stash):

    st.session_state.participants.append(name)
    st.session_state.team_names[name] = stash["team_name"]
    if stash["formation"] is not None:
        st.session_state.formations[name] = stash["formation"]
    if stash["credential"] is not None:
        st.session_state.auth_credentials[name] = stash["credential"]
    st.session_state.bans[name] = []
    st.session_state.ban_submissions[name] = False
    st.session_state.drafted_players[name] = {}

    base_order = _base_pick_order() or [p for p in st.session_state.participants if p != name]
    base_order.insert(min(stash["base_index"], len(base_order)), name)
    st.session_state.draft_sequence = build_snake_sequence(
        base_order, st.session_state.bench_slots
    )

    save_session_state(expected_version=st.session_state.get("state_version", 0))


def init_session_state():
    """Restore a saved draft on first run, then fill in any missing defaults."""
    if "initialized" not in st.session_state:
        load_session_state()
        st.session_state.initialized = True

    for key, default in _SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default.copy() if isinstance(default, (dict, list, set)) else default


def reset_session_state(path=None):
    """Wipe the in-memory session and the on-disk state DB (with WAL sidecars)."""
    path = path or STATE_FILE
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    for target in (path, f"{path}-wal", f"{path}-shm"):
        try:
            os.remove(target)
        except OSError:
            pass
