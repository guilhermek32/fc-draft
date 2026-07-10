"""Unit tests for URL login tokens (pitch-click session restore)."""

import streamlit as st

from fcdraft.auth import issue_auth_token, resolve_auth_token, revoke_auth_token
from fcdraft.main import _restore_login_from_url


def test_issue_and_resolve_participant_token(mock_streamlit_state):
    mock_streamlit_state["participants"] = ["Alice", "Bob"]
    token = issue_auth_token("Alice")
    assert resolve_auth_token(token) == {"participant": "Alice", "is_admin": False}


def test_reissue_replaces_previous_token(mock_streamlit_state):
    mock_streamlit_state["participants"] = ["Alice"]
    old = issue_auth_token("Alice")
    new = issue_auth_token("Alice")
    assert old != new
    assert resolve_auth_token(old) is None
    assert resolve_auth_token(new) is not None
    assert len(mock_streamlit_state["auth_tokens"]) == 1


def test_admin_token_resolves_without_participants(mock_streamlit_state):
    token = issue_auth_token(is_admin=True)
    assert resolve_auth_token(token) == {"participant": None, "is_admin": True}


def test_token_for_removed_participant_is_invalid(mock_streamlit_state):
    mock_streamlit_state["participants"] = ["Alice"]
    token = issue_auth_token("Alice")
    mock_streamlit_state["participants"] = ["Bob"]
    assert resolve_auth_token(token) is None


def test_unknown_and_revoked_tokens(mock_streamlit_state):
    mock_streamlit_state["participants"] = ["Alice"]
    assert resolve_auth_token("nope") is None
    token = issue_auth_token("Alice")
    revoke_auth_token(token)
    revoke_auth_token(None)  # no-op
    assert resolve_auth_token(token) is None


def test_restore_login_from_url_valid_token(mock_streamlit_state):
    mock_streamlit_state["participants"] = ["Alice"]
    token = issue_auth_token("Alice")
    st.query_params["auth"] = token

    _restore_login_from_url()
    assert mock_streamlit_state["authed_participant"] == "Alice"
    assert mock_streamlit_state["auth_token"] == token
    assert mock_streamlit_state["is_admin"] is False


def test_restore_login_from_url_admin_token(mock_streamlit_state):
    token = issue_auth_token(is_admin=True)
    st.query_params["auth"] = token

    _restore_login_from_url()
    assert mock_streamlit_state["is_admin"] is True


def test_restore_login_from_url_unknown_token_pops_param(mock_streamlit_state):
    st.query_params["auth"] = "bogus"
    _restore_login_from_url()
    assert "auth" not in st.query_params
    assert not mock_streamlit_state.get("authed_participant")


def test_restore_login_does_not_hijack_existing_session(mock_streamlit_state):
    mock_streamlit_state["participants"] = ["Alice", "Bob"]
    mock_streamlit_state["authed_participant"] = "Bob"
    token = issue_auth_token("Alice")
    st.query_params["auth"] = token

    _restore_login_from_url()
    assert mock_streamlit_state["authed_participant"] == "Bob"
