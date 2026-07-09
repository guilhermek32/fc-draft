import io

import pytest
from PIL import Image

import fcdraft.images as images


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def image_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "image_cache"
    monkeypatch.setattr(images, "IMAGE_CACHE_DIR", str(cache_dir))
    return cache_dir


def test_valid_image_is_downloaded_and_cached(image_cache_dir, monkeypatch):
    monkeypatch.setattr(
        images.urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse(_png_bytes())
    )
    uri = images.get_cached_player_image_base64("123", "http://example.com/p.png")
    assert uri.startswith("data:image/png;base64,")
    assert (image_cache_dir / "123.png").exists()


def test_error_payload_is_never_cached(image_cache_dir, monkeypatch):
    """An HTML error page must not be cached as a player image."""
    monkeypatch.setattr(
        images.urllib.request,
        "urlopen",
        lambda req, timeout=None: _FakeResponse(b"<html>404 Not Found</html>"),
    )
    uri = images.get_cached_player_image_base64("456", "http://example.com/p.png")
    # Both the player image and the notfound fallback fail validation:
    # fall back to the transparent pixel and cache nothing.
    assert uri == images.TRANSPARENT_PIXEL_URI
    assert not (image_cache_dir / "456.png").exists()
    assert not (image_cache_dir / "notfound.png").exists()


def test_cached_file_skips_network(image_cache_dir, monkeypatch):
    image_cache_dir.mkdir()
    (image_cache_dir / "789.png").write_bytes(_png_bytes())

    def _boom(req, timeout=None):
        raise AssertionError("network must not be hit for cached images")

    monkeypatch.setattr(images.urllib.request, "urlopen", _boom)
    uri = images.get_cached_player_image_base64("789", "http://example.com/p.png")
    assert uri.startswith("data:image/png;base64,")
