"""FUT-style player card HTML, shared by pitch, bench, and preview panes."""

import html as html_lib

import streamlit as st

from fcdraft.config import NOTFOUND_IMG_URL, OVR_TIER_GOLD, OVR_TIER_SILVER
from fcdraft.images import get_player_image_base64_cached


def ovr_tier_class(ovr):
    if ovr >= OVR_TIER_GOLD:
        return "card-gold"
    if ovr >= OVR_TIER_SILVER:
        return "card-silver"
    return "card-bronze"


def player_face_data_uri(player):
    face_url = player.get("player_face_url", "")
    if not isinstance(face_url, str) or not face_url.startswith("http"):
        face_url = NOTFOUND_IMG_URL
    return get_player_image_base64_cached(player.get("player_id", "notfound"), face_url)


def render_player_card(player, pos_label):
    """Standard-size card used on the pitch and bench."""
    ovr = player.get("overall", 50)
    name = html_lib.escape(str(player.get("short_name", "Unknown")))
    long_name = html_lib.escape(str(player.get("long_name", name)))
    club = html_lib.escape(str(player.get("club_name", "Free Agent")))
    return f"""
    <div class="player-card {ovr_tier_class(ovr)}">
        <div class="card-rating-pos">
            <span class="card-rating">{ovr}</span>
            <span class="card-pos">{pos_label}</span>
        </div>
        <img class="card-face" src="{player_face_data_uri(player)}" referrerpolicy="no-referrer">
        <div class="card-name" title="{long_name}">{name}</div>
        <div class="card-club" title="{club}">{club}</div>
    </div>
    """


def render_empty_card(slot, interactive=False):
    card_html = f"""
    <div class="player-card empty-card">
        <div class="empty-pos">{slot}</div>
        <div class="empty-plus">+</div>
    </div>
    """
    if interactive:
        # The anchor triggers a full page navigation (new Streamlit session);
        # carrying the login token lets the new session restore the login.
        token = st.session_state.get("auth_token")
        auth_part = f"&auth={token}" if token else ""
        return f'<a href="?draft_slot={slot}{auth_part}" target="_self" style="text-decoration: none; color: inherit;">{card_html}</a>'
    return card_html


def render_preview_card(player, pos_label, width, height, padding,
                        rating_size, pos_size, face_size, name_size, club_size,
                        rating_padding="1px 4px", border_radius="", margin_bottom="10px",
                        banned=False):
    """Enlarged, centered preview card (draft dialog and draft-room profile pane)."""
    ovr = player.get("overall", 50)
    radius_style = f" border-radius: {border_radius};" if border_radius else ""
    face_style = " filter: grayscale(1) brightness(0.55);" if banned else ""
    card_style = " opacity: 0.75; border-color: #b71c1c;" if banned else ""
    return f"""
    <div style="display: flex; justify-content: center; margin-bottom: {margin_bottom};">
        <div class="player-card {ovr_tier_class(ovr)}" style="width: {width}px; height: {height}px; padding: {padding}px;{radius_style}{card_style}">
            <div class="card-rating-pos" style="font-size: {rating_size + 2}px;">
                <span class="card-rating" style="font-size: {rating_size}px; padding: {rating_padding};">{ovr}</span>
                <span class="card-pos" style="font-size: {pos_size}px;">{pos_label}</span>
            </div>
            <img class="card-face" src="{player_face_data_uri(player)}" style="width: {face_size}px; height: {face_size}px;{face_style}" referrerpolicy="no-referrer">
            <div class="card-name" style="font-size: {name_size}px; margin-top: 4px;">{player['short_name']}</div>
            <div class="card-club" style="font-size: {club_size}px;">{player['club_name']}</div>
        </div>
    </div>
    """
