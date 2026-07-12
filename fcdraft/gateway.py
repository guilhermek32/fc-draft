"""Shared login gateway and cross-device live-sync poller.

Used by the ban and draft phases: participants authenticate with the password
set during setup, the admin superuser with the admin password. Live sync works
by polling the persisted state_version counter and forcing a full-app rerun
only when another session has saved.
"""

import json
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from fcdraft.auth import check_credential, issue_auth_token, revoke_auth_token
from fcdraft.config import ADMIN_LABEL, ADMIN_NAME, LIVE_SYNC_INTERVAL
from fcdraft.state import (
    refresh_shared_state,
    save_session_state,
    shared_state_lock,
    state_signature,
)


# If the poller heartbeat stops for this long, the browser-side watchdog
# declares the screen frozen and tells the user to reload.
_FREEZE_AFTER_MS = 15_000


@st.fragment(run_every=LIVE_SYNC_INTERVAL)
def live_sync_poller():
    """Rerun the whole app when another session has written new state.

    One version SELECT per poll; a missing/unreadable DB (signature None)
    never triggers a rerun, so transient failures cause no rerun storms.

    Also shows when this session last synced, and plants a browser-side
    watchdog: the JS keeps running even when the fragment stops rerunning
    (dead websocket, hung server), so a frozen screen gets a visible banner
    instead of silently showing stale state.
    """
    _render_sync_status()
    signature = state_signature()
    if signature is not None and signature != st.session_state.get("state_signature"):
        st.rerun(scope="app")


# Runs in the top window (not the component iframe): the component iframe is
# replaced on every poll, which would kill any interval it owned.
_WATCHDOG_JS = """
window.__syncWatchdog = setInterval(function() {
    var stale = Date.now() - (window.__lastSyncBeat || Date.now()) > %(freeze_ms)d;
    var banner = document.getElementById('sync-freeze-banner');
    if (stale && !banner) {
        banner = document.createElement('div');
        banner.id = 'sync-freeze-banner';
        banner.style.cssText =
            'position:fixed;top:0;left:0;right:0;z-index:999999;' +
            'background:#b91c1c;color:#fff;text-align:center;' +
            'padding:10px;font-family:sans-serif;font-size:15px;';
        banner.textContent =
            '⚠️ The screen stopped updating — reload the page to see the latest picks.';
        document.body.appendChild(banner);
    } else if (!stale && banner) {
        banner.remove();
    }
}, 3000);
""" % {"freeze_ms": _FREEZE_AFTER_MS}


def _render_sync_status():
    now = datetime.now()
    st.caption(f"🔄 Live sync · last updated {now:%H:%M:%S}")
    # The beat timestamp is baked into the markup: identical HTML would be
    # memoized by Streamlit and the script would only ever run once, so the
    # heartbeat would go stale on a healthy page.
    components.html(
        f"""
        <script>
        // beat {now.timestamp()}
        (function() {{
            const w = window.parent;
            w.__lastSyncBeat = Date.now();
            if (!w.__syncWatchdog) {{
                const s = w.document.createElement('script');
                s.textContent = {json.dumps(_WATCHDOG_JS)};
                w.document.head.appendChild(s);
            }}
        }})();
        </script>
        """,
        height=0,
    )


def get_authed_participant():
    """The logged-in participant for this browser session, or None."""
    authed = st.session_state.get("authed_participant")
    if authed not in st.session_state.participants:
        return None
    return authed


def _finish_login(participant=None, is_admin=False):
    """Issue a URL token so the login survives pitch-click page navigations.

    Refreshes shared state under the lock before saving, so a login never
    overwrites a pick another session made in the meantime.
    """
    with shared_state_lock():
        refresh_shared_state()
        if participant is not None and participant not in st.session_state.participants:
            st.session_state.authed_participant = None
            st.error("This participant is no longer part of the draft.")
            return
        token = issue_auth_token(participant, is_admin)
        st.session_state.auth_token = token
        save_session_state(expected_version=st.session_state.get("state_version", 0))
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
            else:
                st.error("Incorrect password.")
        elif check_credential(name, password):
            st.session_state.authed_participant = name
            _finish_login(name)
        else:
            st.error("Incorrect password.")


def logout():
    with shared_state_lock():
        refresh_shared_state()
        revoke_auth_token(st.session_state.get("auth_token"))
        save_session_state(expected_version=st.session_state.get("state_version", 0))
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
