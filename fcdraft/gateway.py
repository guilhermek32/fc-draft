"""Shared login gateway and cross-device live-sync poller.

Used by the ban and draft phases: participants authenticate with the password
set during setup, the admin superuser with the admin password. Live sync works
by polling the persisted state_version counter and forcing a full-app rerun
only when another session has saved.
"""

import streamlit as st

from fcdraft.auth import check_credential, issue_auth_token, revoke_auth_token, set_credential
from fcdraft.config import ADMIN_LABEL, ADMIN_NAME, LIVE_SYNC_INTERVAL
from fcdraft.state import (
    refresh_shared_state,
    save_session_state,
    shared_state_lock,
    state_file_signature,
)


@st.fragment(run_every=LIVE_SYNC_INTERVAL)
def live_sync_poller():
    """Rerun the whole app when another session has written new state.

    One os.stat per poll; a missing/unreadable file (signature None) never
    triggers a rerun, so transient failures cause no rerun storms.
    """
    signature = state_file_signature()
    if signature is not None and signature != st.session_state.get("state_signature"):
        st.rerun(scope="app")


def get_authed_participant():
    """The logged-in participant for this browser session, or None."""
    authed = st.session_state.get("authed_participant")
    if authed not in st.session_state.participants:
        return None
    return authed


def _finish_login(participant=None, is_admin=False, claim_password=None):
    """Issue a URL token so the login survives pitch-click page navigations.

    Refreshes shared state under the lock before saving, so a login never
    overwrites a pick another session made in the meantime. claim_password
    handles legacy state files: the credential is (re-)claimed only after the
    refresh, against the freshest credentials on disk.
    """
    with shared_state_lock():
        refresh_shared_state()
        if participant is not None and participant not in st.session_state.participants:
            st.session_state.authed_participant = None
            st.error("This participant is no longer part of the draft.")
            return
        if claim_password is not None:
            name = ADMIN_NAME if is_admin else participant
            if name in st.session_state.auth_credentials:
                # Someone claimed this name between render and click.
                if not check_credential(name, claim_password):
                    st.session_state.authed_participant = None
                    st.session_state.is_admin = False
                    st.error("Incorrect password.")
                    return
            else:
                set_credential(name, claim_password)
        token = issue_auth_token(participant, is_admin)
        st.session_state.auth_token = token
        save_session_state()
    st.query_params["auth"] = token
    st.rerun()


def render_login_gateway(key_prefix=""):
    """Name + secret password form; sets authed_participant (or is_admin) on success.

    key_prefix allows a second instance of the form on the same page (e.g. the
    sidebar account box) without widget-key collisions.
    """
    st.subheader("🔐 Participant Login", anchor=False)
    st.write("Select your name and enter your secret password.")

    options = list(st.session_state.participants) + [ADMIN_LABEL]
    name = st.selectbox("Participant", options, key=f"{key_prefix}login_name")
    password = st.text_input("Secret Password", type="password", key=f"{key_prefix}login_password")

    if st.button("Login", use_container_width=True, type="primary", key=f"{key_prefix}login_btn"):
        if not name or not password:
            st.error("Select your name and enter your password.")
        elif name == ADMIN_LABEL:
            if check_credential(ADMIN_NAME, password):
                st.session_state.is_admin = True
                _finish_login(is_admin=True)
            elif ADMIN_NAME not in st.session_state.auth_credentials:
                # Legacy state file created before the admin superuser existed:
                # the first admin login claims the password.
                st.session_state.is_admin = True
                _finish_login(is_admin=True, claim_password=password)
            else:
                st.error("Incorrect password.")
        elif name not in st.session_state.auth_credentials:
            # Legacy state file created before passwords existed: claim the name.
            st.session_state.authed_participant = name
            _finish_login(name, claim_password=password)
        elif check_credential(name, password):
            st.session_state.authed_participant = name
            _finish_login(name)
        else:
            st.error("Incorrect password.")


def logout():
    with shared_state_lock():
        refresh_shared_state()
        revoke_auth_token(st.session_state.get("auth_token"))
        save_session_state()
    st.session_state.auth_token = None
    st.session_state.authed_participant = None
    st.session_state.is_admin = False
    st.query_params.pop("auth", None)
    st.rerun()


def render_logout_button(name, key=None):
    if st.button(f"🚪 Log out ({name})", use_container_width=True, key=key):
        logout()


def render_account_box():
    """Always-visible login/logout control, usable in a sidebar or page body."""
    viewer = get_authed_participant()
    if viewer is not None:
        st.markdown(f"👤 Logged in as **{viewer}**")
        render_logout_button(viewer, key="account_logout")
    elif st.session_state.get("is_admin"):
        st.markdown(f"👤 Logged in as **{ADMIN_LABEL}**")
        render_logout_button(ADMIN_LABEL, key="account_logout")
    else:
        with st.expander("🔐 Log in"):
            render_login_gateway(key_prefix="account_")
