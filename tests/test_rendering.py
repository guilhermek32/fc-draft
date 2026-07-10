import pytest
import app

def test_render_pitch_html_non_interactive():
    """Verify that render_pitch_html outputs card markup without click links when interactive=False."""
    drafted_players = {
        "GK": {"player_id": 1, "short_name": "Alisson", "overall": 89, "player_face_url": "", "club_name": "Liverpool"}
    }
    
    html = app.render_pitch_html(formation="4-3-3", drafted_players=drafted_players, interactive=False)
    
    # Verify card content is rendered
    assert "Alisson" in html
    assert "89" in html
    assert "GK" in html
    
    # Since it is non-interactive, there should be no anchor tags targeting draft_slot
    assert "?draft_slot=" not in html

def test_render_pitch_html_interactive():
    """Verify that empty slots are wrapped in anchor tags when interactive=True."""
    drafted_players = {}  # All slots are empty
    
    html = app.render_pitch_html(formation="4-3-3", drafted_players=drafted_players, interactive=True)
    
    # Since interactive is True, empty slots like ST and LW should have interactive links
    assert '<a href="?draft_slot=ST"' in html
    assert '<a href="?draft_slot=LW"' in html

def test_render_bench_html():
    """Verify bench layout rendering."""
    # Non-interactive filled and empty bench slots
    drafted_players = {
        "SUB 1": {"player_id": 2, "short_name": "Salah", "overall": 89, "player_face_url": "", "club_name": "Liverpool"}
    }
    
    html = app.render_bench_html(bench_slots=3, drafted_players=drafted_players, interactive=False)
    
    # Verify that filled and empty slot markings exist
    assert "Salah" in html
    assert "SUB 2" in html
    assert "?draft_slot=" not in html
    
    # Interactive bench slots
    html_interactive = app.render_bench_html(bench_slots=3, drafted_players=drafted_players, interactive=True)
    assert '<a href="?draft_slot=SUB 2"' in html_interactive

def test_interactive_links_carry_auth_token(mock_streamlit_state):
    """When the session holds a login token, pitch-click anchors include it so
    the resulting page navigation can restore the login."""
    mock_streamlit_state["auth_token"] = "tok123"

    html = app.render_pitch_html(formation="4-3-3", drafted_players={}, interactive=True)
    assert '<a href="?draft_slot=ST&auth=tok123"' in html

    bench = app.render_bench_html(bench_slots=2, drafted_players={}, interactive=True)
    assert '<a href="?draft_slot=SUB 1&auth=tok123"' in bench


def test_get_player_image_base64_cached_fallback():
    """Verify that cached base64 image resolver gracefully returns fallback placeholder on invalid URL or ID."""
    # When ID is empty or notfound, it should return the fallback notfound base64 string or url
    img = app.get_player_image_base64_cached(player_id="notfound", url="")
    assert img.startswith("data:image/png;base64,") or "notfound" in img
