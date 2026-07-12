"""Player face image download, validation, and caching (static URLs + base64)."""

import base64
import io
import os
import shutil
import urllib.request
from functools import lru_cache

import streamlit as st
from PIL import Image

from fcdraft.config import (
    DOWNLOAD_TIMEOUT,
    IMAGE_CACHE_DIR,
    LEGACY_IMAGE_CACHE_DIR,
    NOTFOUND_IMG_URL,
    TRANSPARENT_PIXEL_URI,
)

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Player faces are small PNGs; anything bigger is not a face image.
MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _download_image(url, dest_path):
    """Download url to dest_path; only keep payloads that are actual images."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
        data = response.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"image exceeds {MAX_IMAGE_BYTES} bytes: {url}")
    Image.open(io.BytesIO(data)).verify()  # raises if not a valid image
    with open(dest_path, "wb") as f:
        f.write(data)


@lru_cache(maxsize=1)
def _ensure_cache_dir():
    """Create the static cache dir, migrating PNGs from the legacy location once."""
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    try:
        if not os.listdir(IMAGE_CACHE_DIR) and os.path.isdir(LEGACY_IMAGE_CACHE_DIR):
            for name in os.listdir(LEGACY_IMAGE_CACHE_DIR):
                if name.endswith(".png"):
                    shutil.copy2(
                        os.path.join(LEGACY_IMAGE_CACHE_DIR, name),
                        os.path.join(IMAGE_CACHE_DIR, name),
                    )
    except OSError:
        pass


def _cached_image_filename(player_id, url):
    """Filename inside IMAGE_CACHE_DIR for a player's face, downloading on miss.

    Returns None on complete network failure (caller falls back to a data URI).
    """
    _ensure_cache_dir()
    local_path = os.path.join(IMAGE_CACHE_DIR, f"{player_id}.png")
    if os.path.exists(local_path):
        return f"{player_id}.png"
    try:
        _download_image(url, local_path)
        return f"{player_id}.png"
    except Exception:
        # Fall back to the shared "not found" placeholder image
        fallback_local = os.path.join(IMAGE_CACHE_DIR, "notfound.png")
        if not os.path.exists(fallback_local):
            try:
                _download_image(NOTFOUND_IMG_URL, fallback_local)
            except Exception:
                return None
        return "notfound.png"


@st.cache_data(show_spinner=False)
def get_player_image_src(player_id, url):
    """Browser-cacheable static URL for a player's face (served by Streamlit).

    Falls back to a transparent-pixel data URI on complete network failure.
    """
    filename = _cached_image_filename(player_id, url)
    if filename is None:
        return TRANSPARENT_PIXEL_URI
    return f"./app/static/image_cache/{filename}"


def get_cached_player_image_base64(player_id, url):
    """Retrieve player image locally or download it, then return its base64 Data URI."""
    filename = _cached_image_filename(player_id, url)
    if filename is None:
        return TRANSPARENT_PIXEL_URI
    local_path = os.path.join(IMAGE_CACHE_DIR, filename)

    try:
        with open(local_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return url


@st.cache_data(show_spinner=False)
def get_player_image_base64_cached(player_id, url):
    """Cached wrapper around the image resolver to keep Base64 URIs in memory."""
    return get_cached_player_image_base64(player_id, url)
