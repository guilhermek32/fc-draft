"""EA FC 26 Draft Board — Streamlit entrypoint.

The application lives in the ``fcdraft`` package; this file stays the
Streamlit Cloud entrypoint and re-exports the public API for the tests.
"""

from fcdraft.config import FLEXIBLE_POSITIONS, FORMATIONS, IMAGE_CACHE_DIR, STATE_FILE  # noqa: F401
from fcdraft.data import load_data  # noqa: F401
from fcdraft.draft import auto_draft_remaining  # noqa: F401
from fcdraft.dialogs import draft_player_dialog  # noqa: F401
from fcdraft.formations import build_slot_list, get_base_position, get_formation_slots  # noqa: F401
from fcdraft.images import get_cached_player_image_base64, get_player_image_base64_cached  # noqa: F401
from fcdraft.main import run
from fcdraft.pitch import (  # noqa: F401
    display_pitch_component,
    get_pitch_layout,
    render_bench_html,
    render_pitch_html,
)
from fcdraft.search import search_players  # noqa: F401
from fcdraft.state import load_session_state, save_session_state  # noqa: F401

if __name__ == "__main__":
    run()
