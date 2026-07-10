"""Shared login gateway and cross-device live-sync poller.

Used by the ban and draft phases: participants authenticate with the password
set during setup, the admin superuser with the admin password. Live sync works
by polling the persisted state_version counter and forcing a full-app rerun
only when another session has saved.
"""

import streamlit as st

from fcdraft.auth import check_credential, set_credential
from fcdraft.config import ADMIN_LABEL, ADMIN_NAME, LIVE_SYNC_INTERVAL
from fcdraft.state import peek_state_version, save_session_state


@st.fragment(run_every=LIVE_SYNC_INTERVAL)
def live_sync_poller():
    """Rerun the whole app when another session has written new state."""
    if peek_state_version() != st.session_state.get("state_version", 0):
        st.rerun(scope="app")


def get_authed_participant():
    """The logged-in participant for this browser session, or None."""
    authed = st.session_state.get("authed_participant")
    if authed not in st.session_state.participants:
        return None
    return authed


def render_login_gateway():
    """Name + secret password form; sets authed_participant (or is_admin) on success."""
    st.subheader("🔐 Participant Login", anchor=False)
    st.write("Select your name and enter your secret password.")

    options = list(st.session_state.participants) + [ADMIN_LABEL]
    name = st.selectbox("Participant", options, key="login_name")
    password = st.text_input("Secret Password", type="password", key="login_password")

    if st.button("Login", use_container_width=True, type="primary"):
        if not name or not password:
            st.error("Select your name and enter your password.")
        elif name == ADMIN_LABEL:
            if check_credential(ADMIN_NAME, password):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        elif name not in st.session_state.auth_credentials:
            # Legacy state file created before passwords existed: claim the name.
            set_credential(name, password)
            st.session_state.authed_participant = name
            save_session_state()
            st.rerun()
        elif check_credential(name, password):
            st.session_state.authed_participant = name
            st.rerun()
        else:
            st.error("Incorrect password.")


def render_logout_button(name):
    if st.button(f"🚪 Log out ({name})", use_container_width=True):
        st.session_state.authed_participant = None
        st.session_state.is_admin = False
        st.rerun()
