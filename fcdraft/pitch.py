"""Pitch and bench visualization."""

import streamlit as st

from fcdraft.cards import render_empty_card, render_player_card
from fcdraft.formations import get_formation_slots, position_label_pt

_ROW_POSITIONS = {
    "defense": ("CB", "LB", "RB", "LWB", "RWB"),
    "midfield": ("CM", "CDM", "CAM", "LM", "RM"),
    "attack": ("ST", "LW", "RW", "CF", "LF", "RF"),
}

# Sorting weights to line up positions properly (left to right)
_HORIZONTAL_WEIGHTS = (
    ("LWB", 2), ("LB", 1), ("CB", 3), ("RWB", 4), ("RB", 5),
    ("LM", 1), ("CDM", 2), ("CM", 3), ("CAM", 4), ("RM", 5),
    ("LW", 1), ("LF", 2), ("CF", 3), ("ST", 4), ("RF", 5), ("RW", 6),
)


def _get_horizontal_weight(slot):
    slot_upper = slot.upper()
    # LWB/RWB before LB/RB so the longer prefix wins
    for prefix, weight in _HORIZONTAL_WEIGHTS:
        if slot_upper.startswith(prefix):
            return weight
    return 3  # center default


def get_pitch_layout(formation, drafted_players):
    rows = {"attack": [], "midfield": [], "defense": [], "gk": []}

    for slot in get_formation_slots(formation):
        slot_upper = slot.upper()
        item = {"slot": slot, "player": drafted_players.get(slot, None)}

        if slot_upper.startswith("GK"):
            rows["gk"].append(item)
        elif any(slot_upper.startswith(pos) for pos in _ROW_POSITIONS["defense"]):
            rows["defense"].append(item)
        elif any(slot_upper.startswith(pos) for pos in _ROW_POSITIONS["midfield"]):
            rows["midfield"].append(item)
        elif any(slot_upper.startswith(pos) for pos in _ROW_POSITIONS["attack"]):
            rows["attack"].append(item)
        else:
            rows["midfield"].append(item)

    for key in rows:
        rows[key] = sorted(rows[key], key=lambda x: _get_horizontal_weight(x["slot"]))
    return rows


def _flatten(html):
    return " ".join(line.strip() for line in html.splitlines())


def render_pitch_html(formation, drafted_players, interactive=False):
    rows = get_pitch_layout(formation, drafted_players)

    parts = ["""
    <div class="pitch-container">
        <div class="pitch-bg-lines"></div>
        <div class="pitch-half-line"></div>
        <div class="pitch-center-circle"></div>
        <div class="pitch-penalty-area-top"></div>
        <div class="pitch-penalty-area-bottom"></div>
    """]

    for row_name in ["attack", "midfield", "defense", "gk"]:
        parts.append(f'<div class="pitch-row row-{row_name}">')
        for item in rows[row_name]:
            slot, player = item["slot"], item["player"]
            if player:
                parts.append(render_player_card(player, position_label_pt(slot.split()[0])))
            else:
                parts.append(render_empty_card(slot, interactive))
        parts.append("</div>")

    parts.append("</div>")
    return _flatten("".join(parts))


def render_bench_html(bench_slots, drafted_players, interactive=False):
    if bench_slots == 0:
        return ""

    parts = ["""
    <div style="text-align: center; margin-top: 30px;">
        <h4 class="gold-text" style="margin-bottom: 15px;">RESERVAS / BANCO</h4>
        <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
    """]

    for i in range(1, bench_slots + 1):
        slot = f"SUB {i}"
        player = drafted_players.get(slot, None)
        if player:
            parts.append(render_player_card(player, "RES"))
        else:
            parts.append(render_empty_card(slot, interactive))

    parts.append("""
        </div>
    </div>
    """)
    return _flatten("".join(parts))


def display_pitch_component(formation, drafted_players, bench_slots_count, interactive=False):
    """Render pitch + bench using st.html."""
    st.html(render_pitch_html(formation, drafted_players, interactive))
    bench_body = render_bench_html(bench_slots_count, drafted_players, interactive)
    if bench_body:
        st.html(bench_body)
