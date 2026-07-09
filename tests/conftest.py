import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock
import streamlit as st

# 1. Global Session Store & Mock State
session_store = {
    "phase": "testing", 
    "initialized": True,
    "drafted_players": {},
    "banned_player_ids": set()
}

class MockSessionState:
    def __getitem__(self, key):
        if key == "phase":
            return "testing"
        return session_store.get(key)
    def __setitem__(self, key, value):
        if key == "phase":
            return
        session_store[key] = value
    def __delitem__(self, key):
        if key in session_store:
            del session_store[key]
    def __contains__(self, key):
        if key == "phase":
            return True
        return key in session_store
    def get(self, key, default=None):
        if key == "phase":
            return "testing"
        return session_store.get(key, default)
    def setdefault(self, key, default=None):
        if key == "phase":
            if "phase" not in session_store:
                session_store["phase"] = "testing"
            return "testing"
        return session_store.setdefault(key, default)
    def keys(self):
        return list(session_store.keys())
    def items(self):
        return session_store.items()
    def clear(self):
        session_store.clear()
        session_store["phase"] = "testing"
        session_store["initialized"] = True
        session_store["drafted_players"] = {}
        session_store["banned_player_ids"] = set()

    # Attribute access support (st.session_state.phase)
    def __getattr__(self, name):
        if name == "phase":
            return "testing"
        if name in session_store:
            return session_store[name]
        raise AttributeError(f"'MockSessionState' object has no attribute '{name}'")
        
    def __setattr__(self, name, value):
        if name == "phase":
            return
        session_store[name] = value

    def __delattr__(self, name):
        if name in session_store:
            del session_store[name]

# Helper to mock decorators with or without arguments
def mock_decorator_or_factory(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return lambda func: func

# 2. Apply Global Monkeypatches immediately on Streamlit module
st.session_state = MockSessionState()
st.rerun = MagicMock()
st.cache_data = mock_decorator_or_factory
st.dialog = mock_decorator_or_factory
st.html = MagicMock()
st.markdown = MagicMock()
st.write = MagicMock()
st.success = MagicMock()
st.warning = MagicMock()
st.error = MagicMock()
st.sidebar = MagicMock()
st.selectbox = MagicMock()
st.text_input = MagicMock()
st.button = MagicMock()
st.columns = lambda *args, **kwargs: [MagicMock() for _ in range(args[0] if args else 2)]
st.tabs = lambda *args, **kwargs: [MagicMock() for _ in range(len(args[0]) if args else 2)]

import pytest

@pytest.fixture(autouse=True)
def mock_streamlit_state():
    """Fixture that resets the mock session store before each test and returns it."""
    session_store.clear()
    session_store["phase"] = "testing"
    session_store["initialized"] = True
    session_store["drafted_players"] = {}
    session_store["banned_player_ids"] = set()
    return session_store
