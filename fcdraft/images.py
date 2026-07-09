"""Player face image download, validation, and base64 caching."""

import base64
import io
import os
import urllib.request

import streamlit as st
from PIL import Image

from fcdraft.config import DOWNLOAD_TIMEOUT, IMAGE_CACHE_DIR, NOTFOUND_IMG_URL, TRANSPARENT_PIXEL_URI

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _download_image(url, dest_path):
    """Download url to dest_path; only keep payloads that are actual images."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
        data = response.read()
    Image.open(io.BytesIO(data)).verify()  # raises if not a valid image
    with open(dest_path, "wb") as f:
        f.write(data)


def get_cached_player_image_base64(player_id, url):
    """Retrieve player image locally or download it, then return its base64 Data URI."""
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    local_path = os.path.join(IMAGE_CACHE_DIR, f"{player_id}.png")

    if not os.path.exists(local_path):
        try:
            _download_image(url, local_path)
        except Exception:
            # Fall back to the shared "not found" placeholder image
            fallback_local = os.path.join(IMAGE_CACHE_DIR, "notfound.png")
            if not os.path.exists(fallback_local):
                try:
                    _download_image(NOTFOUND_IMG_URL, fallback_local)
                except Exception:
                    # Complete network failure: transparent pixel
                    return TRANSPARENT_PIXEL_URI
            local_path = fallback_local

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
