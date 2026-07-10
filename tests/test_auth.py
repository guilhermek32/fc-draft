"""Unit tests for participant password hashing and credential checks."""

from fcdraft.auth import (
    _PASSWORD_ALPHABET,
    check_credential,
    generate_password,
    hash_password,
    set_credential,
    verify_password,
)
from fcdraft.config import GENERATED_PASSWORD_LENGTH


def test_hash_and_verify_round_trip():
    salt, digest = hash_password("hunter2")
    assert verify_password("hunter2", salt, digest)


def test_wrong_password_rejected():
    salt, digest = hash_password("hunter2")
    assert not verify_password("hunter3", salt, digest)


def test_same_password_gets_different_salts_and_hashes():
    salt_a, hash_a = hash_password("hunter2")
    salt_b, hash_b = hash_password("hunter2")
    assert salt_a != salt_b
    assert hash_a != hash_b


def test_explicit_salt_is_deterministic():
    salt, hash_a = hash_password("hunter2")
    _, hash_b = hash_password("hunter2", salt)
    assert hash_a == hash_b


def test_malformed_salt_hex_returns_false():
    assert not verify_password("hunter2", "not-hex!!", "00ff")


def test_generate_password_shape_and_uniqueness():
    passwords = {generate_password() for _ in range(50)}
    assert len(passwords) == 50  # astronomically unlikely to collide
    for pw in passwords:
        assert len(pw) == GENERATED_PASSWORD_LENGTH
        assert all(c in _PASSWORD_ALPHABET for c in pw)


def test_generated_password_verifies(mock_streamlit_state):
    mock_streamlit_state["auth_credentials"] = {}
    pw = generate_password()
    set_credential("Alice", pw)
    assert check_credential("Alice", pw)


def test_credentials_store_only_salted_hashes(mock_streamlit_state):
    mock_streamlit_state["auth_credentials"] = {}
    set_credential("Alice", "hunter2")

    credential = mock_streamlit_state["auth_credentials"]["Alice"]
    assert set(credential) == {"salt", "hash"}
    assert "hunter2" not in credential.values()

    assert check_credential("Alice", "hunter2")
    assert not check_credential("Alice", "wrong")
    assert not check_credential("Nobody", "hunter2")
