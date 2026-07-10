"""Participant password hashing and credential checks.

Only salted PBKDF2 hashes are ever kept in session state or on disk; the
plaintext password exists only inside the login/setup widgets.
"""

import hashlib
import hmac
import secrets

import streamlit as st

from fcdraft.config import GENERATED_PASSWORD_LENGTH, PBKDF2_ITERATIONS, SALT_BYTES

# Unambiguous characters only (no 0/O, 1/l/i) so passwords are easy to share verbally.
_PASSWORD_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def generate_password(length=GENERATED_PASSWORD_LENGTH):
    """Random, easy-to-share secret password."""
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))


def hash_password(password, salt_hex=None):
    """Hash a password, generating a fresh salt when none is given.

    Returns (salt_hex, hash_hex).
    """
    if salt_hex is None:
        salt_hex = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
    )
    return salt_hex, digest.hex()


def verify_password(password, salt_hex, hash_hex):
    """Constant-time check of a password against a stored salt/hash pair."""
    try:
        _, candidate_hex = hash_password(password, salt_hex)
    except ValueError:  # malformed salt hex
        return False
    return hmac.compare_digest(candidate_hex, hash_hex)


def set_credential(name, password):
    """Store the salted hash for a participant in session state."""
    salt_hex, hash_hex = hash_password(password)
    st.session_state.auth_credentials[name] = {"salt": salt_hex, "hash": hash_hex}


def check_credential(name, password):
    """True if the password matches the participant's stored credential."""
    credential = st.session_state.auth_credentials.get(name)
    if not isinstance(credential, dict):
        return False
    return verify_password(password, credential.get("salt", ""), credential.get("hash", ""))
