"""App entrypoint: page config, session bootstrap, and phase dispatch."""

import streamlit as st

from fcdraft.auth import resolve_auth_token
from fcdraft.dialogs import draft_player_dialog
from fcdraft.formations import build_slot_list
from fcdraft.phases import ban, completed, draft, setup
from fcdraft.state import init_session_state, refresh_shared_state
from fcdraft.styles import inject_css

_PHASES = {
    "setup": setup.render,
    "ban": ban.render,
    "draft": draft.render,
    "completed": completed.render,
}


def _restore_login_from_url():
    """A pitch-slot click is a full navigation that starts a NEW Streamlit
    session; the ?auth= token restores this browser's login into it."""
    if "auth" not in st.query_params:
        return
    if st.session_state.get("authed_participant") or st.session_state.get("is_admin"):
        return
    identity = resolve_auth_token(st.query_params["auth"])
    if identity is None:
        st.query_params.pop("auth", None)
        return
    st.session_state.auth_token = st.query_params["auth"]
    st.session_state.authed_participant = identity.get("participant")
    st.session_state.is_admin = bool(identity.get("is_admin"))


def _handle_draft_slot_query_param():
    """Open the draft dialog when a pitch card was clicked (?draft_slot=...)."""
    if st.session_state.phase != "draft" or "draft_slot" not in st.query_params:
        return
    slot = st.query_params["draft_slot"]
    seq = st.session_state.draft_sequence
    curr_idx = st.session_state.current_pick_index
    if curr_idx < len(seq):
        picker = seq[curr_idx]["participant"]
        if st.session_state.get("authed_participant") != picker:
            # Only the on-clock participant's own session may open the pick dialog.
            st.query_params.pop("draft_slot", None)
            return
        all_slots = build_slot_list(
            st.session_state.formations[picker], st.session_state.bench_slots
        )
        squad = st.session_state.drafted_players.setdefault(picker, {})

        if slot in all_slots and slot not in squad:
            draft_player_dialog(slot, picker)
        else:
            st.query_params.pop("draft_slot", None)


def run():
    st.set_page_config(
        page_title="EA FC 26 Draft Board",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    init_session_state()
    # Converge with writes from other devices before anything reads shared state
    # (the pick dialog below must see a fresh current_pick_index).
    if st.session_state.phase in ("ban", "draft"):
        refresh_shared_state()
    _restore_login_from_url()
    _handle_draft_slot_query_param()

    render_phase = _PHASES.get(st.session_state.phase, setup.render)
    render_phase()
