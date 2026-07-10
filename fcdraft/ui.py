"""Shared UI components: phase rail, headers, chips, panels."""

import streamlit as st

_PHASES = [
    ("setup", "Setup"),
    ("ban", "Bans"),
    ("draft", "Draft"),
    ("completed", "Final"),
]


def phase_rail(current_phase: str):
    """Horizontal phase step indicator injected at the top of every page."""
    phase_keys = [p[0] for p in _PHASES]
    current_idx = phase_keys.index(current_phase) if current_phase in phase_keys else 0

    parts = ['<div class="phase-rail">']
    for i, (key, label) in enumerate(_PHASES):
        if i < current_idx:
            cls = "completed"
        elif i == current_idx:
            cls = "active"
        else:
            cls = ""

        parts.append(
            f'<div class="phase-step {cls}">'
            f'<span class="phase-dot {cls}"></span>'
            f'{label}'
            f'</div>'
        )
        if i < len(_PHASES) - 1:
            conn_cls = "completed" if i < current_idx else ("active" if i == current_idx else "")
            parts.append(f'<div class="phase-connector {conn_cls}"></div>')

    parts.append('</div>')
    st.html("".join(parts))


def page_header(title: str, subtitle: str = ""):
    """Phase title + optional subtitle in the new design language."""
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.html(f'<div class="page-header"><h1>{title}</h1>{sub}</div>')


def on_clock_strip(picker_name: str, team_name: str, pick_num: int,
                   total_picks: int, round_num: int):
    """Full-width floodlight amber strip showing whose turn it is."""
    pct = int((pick_num / total_picks) * 100) if total_picks else 0
    st.html(f"""
    <div class="on-clock-strip">
        <div>
            <div class="on-clock-label">On the clock</div>
            <div class="on-clock-name">{picker_name}</div>
            <div class="on-clock-team">{team_name}</div>
        </div>
        <div class="on-clock-meta">
            <div>Pick <strong>{pick_num}</strong> of {total_picks}</div>
            <div>Round <strong>{round_num}</strong></div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {pct}%"></div>
            </div>
        </div>
    </div>
    """)


def status_chip(text: str, variant: str = "waiting"):
    """Return HTML for an inline status chip. variant: 'locked', 'waiting', 'done'."""
    cls = f"status-chip chip-{variant}"
    return f'<span class="{cls}">{text}</span>'


def section_panel(content_html: str, flush: bool = False):
    """Wrap HTML in a desk panel."""
    cls = "desk-panel-flush" if flush else "desk-panel"
    return f'<div class="{cls}">{content_html}</div>'


def broadcast_row(rank: int, name: str, ovr: int, banned_by: str, count: int = 1):
    """One row of the ban-reveal broadcast board."""
    count_badge = f' <span style="color: var(--floodlight); font-family: var(--font-data); font-size: 11px;">\u00d7{count}</span>' if count > 1 else ""
    return f"""
    <div class="broadcast-row">
        <span class="broadcast-rank">{rank:02d}</span>
        <span class="broadcast-name">{name}{count_badge}</span>
        <span class="broadcast-ovr">{ovr} OVR</span>
        <span class="broadcast-banned-by">{banned_by}</span>
    </div>
    """


def ovr_chip(ovr):
    """Inline OVR badge."""
    return f'<span class="ovr-chip">{ovr}</span>'
