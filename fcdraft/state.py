"""Draft session persistence and session-state initialization.

On disk, drafted players are stored as player_id references and rehydrated from
the player database on load; players that don't exist in the database (e.g.
reconstructed from an imported roster CSV) are stored as full dicts. In
st.session_state the squads always hold full player dicts.
"""

import json
import os

import streamlit as st

from fcdraft.config import DEFAULT_BENCH_SLOTS, STATE_FILE
from fcdraft.data import get_player_by_id
from fcdraft.formations import build_snake_sequence

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
    # Monotonic save counter used by the live-sync poller to detect remote writes.
    "state_version": 0,
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


def peek_state_version(path=None):
    """The state_version currently on disk, without touching session state.

    On a missing file or read error, returns the in-memory version so a
    transient failure never looks like a remote change (no rerun storms).
    """
    path = path or STATE_FILE
    fallback = st.session_state.get("state_version", 0)
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return fallback
    if not isinstance(state, dict):
        return fallback
    return state.get("state_version", 0)


def save_session_state(path=None):
    """Serialize and save the current draft state to disk (atomically)."""
    path = path or STATE_FILE
    # Base the new version on the disk value, not memory, so two sessions that
    # alternate saves always produce strictly increasing versions.
    new_version = peek_state_version(path) + 1
    state_to_save = {
        "state_version": new_version,
        "phase": st.session_state.get("phase", "setup"),
        "participants": st.session_state.get("participants", []),
        "team_names": st.session_state.get("team_names", {}),
        "formations": st.session_state.get("formations", {}),
        "bench_slots": st.session_state.get("bench_slots", DEFAULT_BENCH_SLOTS),
        "bans": _slim_bans(st.session_state.get("bans", {})),
        "ban_submissions": st.session_state.get("ban_submissions", {}),
        "auth_credentials": st.session_state.get("auth_credentials", {}),
        "auth_tokens": st.session_state.get("auth_tokens", {}),
        "banned_player_ids": sorted(st.session_state.get("banned_player_ids", set()), key=str),
        "drafted_players": _slim_squads(st.session_state.get("drafted_players", {})),
        "draft_sequence": st.session_state.get("draft_sequence", []),
        "current_pick_index": st.session_state.get("current_pick_index", 0),
        "draft_history": st.session_state.get("draft_history", []),
        "removed_participants": st.session_state.get("removed_participants", {}),
        "pick_deadline": st.session_state.get("pick_deadline"),
        "last_timeout": st.session_state.get("last_timeout"),
    }
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(state_to_save, f)
        os.replace(tmp_path, path)
        st.session_state.state_version = new_version
    except (OSError, TypeError, ValueError) as e:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        st.warning(f"Could not save draft state: {e}")


def load_session_state(path=None):
    """Load saved draft state from disk if it exists. Returns True on success."""
    path = path or STATE_FILE
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        try:
            os.replace(path, f"{path}.corrupt")
        except OSError:
            pass
        st.warning(f"Saved draft state could not be read and was set aside: {e}")
        return False

    try:
        st.session_state.phase = state.get("phase", "setup")
        st.session_state.participants = state.get("participants", [])
        st.session_state.team_names = state.get("team_names", {})
        st.session_state.formations = state.get("formations", {})
        st.session_state.bench_slots = state.get("bench_slots", DEFAULT_BENCH_SLOTS)
        st.session_state.bans = _rehydrate_bans(state.get("bans", {}))
        st.session_state.ban_submissions = state.get("ban_submissions", {})
        st.session_state.auth_credentials = state.get("auth_credentials", {})
        st.session_state.auth_tokens = state.get("auth_tokens", {})
        st.session_state.banned_player_ids = normalize_banned_ids(state.get("banned_player_ids", []))
        st.session_state.drafted_players = _rehydrate_squads(state.get("drafted_players", {}))
        st.session_state.draft_sequence = state.get("draft_sequence", [])
        st.session_state.current_pick_index = state.get("current_pick_index", 0)
        st.session_state.draft_history = state.get("draft_history", [])
        st.session_state.removed_participants = state.get("removed_participants", {})
        st.session_state.pick_deadline = state.get("pick_deadline")
        st.session_state.last_timeout = state.get("last_timeout")
        st.session_state.state_version = state.get("state_version", 0)
        return True
    except (AttributeError, TypeError) as e:
        st.warning(f"Saved draft state has an unexpected shape and was ignored: {e}")
        return False


def refresh_shared_state(path=None):
    """Re-read the multi-user keys from disk so concurrent browser sessions converge.

    init_session_state() loads the state file only once per browser session, so
    without this a participant's tab would never see submissions made from
    another device. Per-session keys (e.g. authed_participant) are untouched.
    """
    path = path or STATE_FILE
    if not os.path.exists(path):
        return
    try:
        with open(path, "r") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(state, dict):
        return
    st.session_state.phase = state.get("phase", st.session_state.get("phase", "setup"))
    st.session_state.participants = state.get("participants", [])
    st.session_state.team_names = state.get("team_names", {})
    st.session_state.formations = state.get("formations", {})
    st.session_state.bench_slots = state.get("bench_slots", DEFAULT_BENCH_SLOTS)
    st.session_state.bans = _rehydrate_bans(state.get("bans", {}))
    st.session_state.ban_submissions = state.get("ban_submissions", {})
    st.session_state.auth_credentials = state.get("auth_credentials", {})
    st.session_state.auth_tokens = state.get("auth_tokens", {})
    st.session_state.banned_player_ids = normalize_banned_ids(state.get("banned_player_ids", []))
    st.session_state.drafted_players = _rehydrate_squads(state.get("drafted_players", {}))
    st.session_state.draft_sequence = state.get("draft_sequence", [])
    st.session_state.current_pick_index = state.get("current_pick_index", 0)
    st.session_state.draft_history = state.get("draft_history", [])
    st.session_state.removed_participants = state.get("removed_participants", {})
    st.session_state.pick_deadline = state.get("pick_deadline")
    st.session_state.last_timeout = state.get("last_timeout")
    st.session_state.state_version = state.get("state_version", 0)


def remove_participant(name):
    """Scrub a participant from all shared state (e.g. a ban-phase no-show).

    The snake order among the remaining participants is preserved; picks are
    renumbered so overall_pick stays gapless. Safe only before the draft
    starts (current_pick_index is 0). The participant's data is stashed in
    removed_participants so restore_participant() can bring them back.
    """
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

    save_session_state()


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
    stash = st.session_state.removed_participants.pop(name, None)
    if stash is None:
        return

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

    save_session_state()


def init_session_state():
    """Restore a saved draft on first run, then fill in any missing defaults."""
    if "initialized" not in st.session_state:
        load_session_state()
        st.session_state.initialized = True

    for key, default in _SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default.copy() if isinstance(default, (dict, list, set)) else default


def reset_session_state(path=None):
    """Wipe the in-memory session and the on-disk state file."""
    path = path or STATE_FILE
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
