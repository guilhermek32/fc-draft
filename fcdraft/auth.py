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


def issue_auth_token(participant=None, is_admin=False):
    """Create a URL login token for an identity, replacing any previous token for it.

    Tokens let a login survive the full-page navigation caused by pitch-slot
    clicks (?draft_slot= anchors). One token per identity: re-logging in
    invalidates older tokens (stale bookmarked URLs stop working).
    """
    tokens = st.session_state.auth_tokens
    identity = (participant, bool(is_admin))
    for token in [t for t, e in tokens.items()
                  if (e.get("participant"), bool(e.get("is_admin"))) == identity]:
        del tokens[token]
    token = secrets.token_urlsafe(16)
    tokens[token] = {"participant": participant, "is_admin": bool(is_admin)}
    return token


def revoke_auth_token(token):
    """Remove a token from the map (no-op for unknown/None)."""
    if token is not None:
        st.session_state.auth_tokens.pop(token, None)


def resolve_auth_token(token):
    """The identity dict for a token, or None if unknown/invalid."""
    entry = st.session_state.auth_tokens.get(token)
    if not isinstance(entry, dict):
        return None
    if entry.get("is_admin"):
        return entry
    if entry.get("participant") in st.session_state.participants:
        return entry
    return None
