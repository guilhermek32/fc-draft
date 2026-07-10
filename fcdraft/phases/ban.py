"""Phase 2: blind player bans behind a per-participant login gateway."""

import streamlit as st

from fcdraft.draft import reset_pick_deadline
from fcdraft.gateway import (
    get_authed_participant,
    live_sync_poller,
    render_account_box,
    render_login_gateway,
    render_logout_button,
)
from fcdraft.search import format_player_options, search_players
from fcdraft.state import save_session_state


def _ranked_bans():
    """Submitted bans aggregated per player (who banned them and how often), highest OVR first."""
    by_player = {}
    for participant, player_list in st.session_state.bans.items():
        for p in player_list:
            pid = str(p["player_id"])
            entry = by_player.setdefault(pid, {**p, "banned_by_list": []})
            entry["banned_by_list"].append(participant)
    all_bans = []
    for entry in by_player.values():
        entry["ban_count"] = len(entry["banned_by_list"])
        entry["banned_by"] = ", ".join(entry["banned_by_list"])
        all_bans.append(entry)
    return sorted(all_bans, key=lambda x: (x.get("overall", 50), x["ban_count"]), reverse=True)


def _ban_choice_column(label_num, picker, exclude_ids):
    """One ban-selection column; returns the chosen player dict or None."""
    st.markdown(f"**Ban Choice {label_num}**")
    query = st.text_input(f"Search Name/Club/Nation ({label_num})", key=f"q_ban{label_num}_{picker}")
    df_search = search_players(query=query)
    if exclude_ids:
        df_search = df_search[~df_search["player_id"].isin(exclude_ids)]
    options = format_player_options(df_search)
    selected_str = st.selectbox(f"Select Soccer Player {label_num}", options, key=f"sel_ban{label_num}_{picker}")

    if selected_str:
        idx = options.index(selected_str)
        p_dict = df_search.iloc[idx].to_dict()
        st.markdown(f"Selected: **{p_dict['short_name']}** ({p_dict['overall']} OVR)")
        return p_dict
    return None


def _render_generated_passwords_panel():
    """One-time display of auto-generated passwords for the admin to distribute.

    Lives only in the setup admin's browser session (never persisted); the
    dismiss button destroys the plaintext for good.
    """
    generated = st.session_state.get("generated_passwords")
    if not generated:
        return
    with st.container(border=True):
        st.markdown("### 🎲 Auto-Generated Secret Passwords")
        st.warning("Share each password with its participant now — they are shown only once, on this screen.")
        for name, password in generated.items():
            st.markdown(f"- **{name}**: `{password}`")
        if st.button("✅ I've shared the passwords — hide them forever", use_container_width=True):
            del st.session_state["generated_passwords"]
            st.rerun()


def _render_ban_picker(picker):
    """Authenticated, not-yet-submitted view: pick and lock in exactly 3 bans."""
    st.markdown(f"### 🛡️ Ban Selection for **{picker}**")
    st.info("Your choices are private. Once you lock them in, they cannot be changed.")

    col_ban1, col_ban2, col_ban3 = st.columns(3)
    with col_ban1:
        p1_dict = _ban_choice_column(1, picker, [])
    with col_ban2:
        p2_dict = _ban_choice_column(2, picker, [p1_dict["player_id"]] if p1_dict else [])
    with col_ban3:
        exclude_ids = [p["player_id"] for p in (p1_dict, p2_dict) if p]
        p3_dict = _ban_choice_column(3, picker, exclude_ids)

    st.write(" ")
    confirmed = st.checkbox("I understand my bans are final once locked in.", key=f"confirm_bans_{picker}")
    if st.button("🔒 Lock in My Bans", use_container_width=True, type="primary", disabled=not confirmed):
        if not p1_dict or not p2_dict or not p3_dict:
            st.error("Please ensure you have selected three distinct players to ban.")
        else:
            st.session_state.bans[picker] = [p1_dict, p2_dict, p3_dict]
            st.session_state.ban_submissions[picker] = True
            save_session_state()
            st.rerun()

    st.write(" ")
    render_logout_button(picker)


def _render_locked_view(picker):
    """Authenticated, already-submitted view: read-only look at your own bans."""
    st.success("✅ Your bans are locked in and hidden from everyone else.")
    with st.container(border=True):
        st.markdown("### 🔒 Your Locked Bans")
        for i, p in enumerate(st.session_state.bans.get(picker, []), 1):
            st.markdown(f"{i}. **{p['short_name']}** ({p.get('overall', '?')} OVR)")
    st.write("Waiting for the remaining participants to submit their bans.")
    render_logout_button(picker)


def _render_reveal_room():
    st.success("✅ All participants have submitted their bans!")
    st.subheader("Global Bans Reveal Room")
    st.write("Ready to see who was banned? This will reveal the final global ban list and start the Snake Draft.")

    with st.container(border=True):
        st.markdown("### 🏆 Banned Players Ranking (Highest OVR first)")
        for rk, b in enumerate(_ranked_bans(), 1):
            count = f" ×{b['ban_count']}" if b["ban_count"] > 1 else ""
            st.markdown(f"{rk}. **{b['short_name']}** ({b['overall']} OVR){count} — Banned by *{b['banned_by']}*")

    st.write(" ")
    if st.button("🔥 Reveal Bans & Start Snake Draft", use_container_width=True, type="primary"):
        banned_player_ids = set()
        for player_list in st.session_state.bans.values():
            for p in player_list:
                banned_player_ids.add(p["player_id"])

        st.session_state.banned_player_ids = banned_player_ids
        st.session_state.phase = "draft"
        reset_pick_deadline()
        save_session_state()
        st.rerun()


def render():
    # Flip waiting screens automatically when another device submits.
    live_sync_poller()

    st.title("🚫 Phase 2: Blind Player Bans")
    st.write("Each participant must select exactly **3 players** to ban from the pool. Selections are blind and hidden until all submit.")

    with st.sidebar:
        render_account_box()

    _render_generated_passwords_panel()

    all_submitted = all(st.session_state.ban_submissions.values()) if st.session_state.ban_submissions else False
    authed = get_authed_participant()

    if all_submitted:
        _render_reveal_room()
    elif authed is None:
        render_login_gateway()
    elif st.session_state.ban_submissions.get(authed):
        _render_locked_view(authed)
    else:
        _render_ban_picker(authed)

    st.write(" ")
    st.write("---")
    st.subheader("Ban Submission Status", anchor=False)
    cols_status = st.columns(len(st.session_state.participants))
    for idx, p_name in enumerate(st.session_state.participants):
        with cols_status[idx]:
            submitted = st.session_state.ban_submissions.get(p_name, False)
            status_text = "🔒 LOCKED & HIDDEN" if submitted else "⏳ AWAITING"
            status_class = "badge-green" if submitted else "badge-secondary"
            team_name = st.session_state.team_names.get(p_name, f"{p_name} FC")
            st.markdown(f"""
            <div style="text-align: center;" class="glass-panel">
                <h4>{p_name}</h4>
                <div style="font-size: 12px; color: #aaa; margin-bottom: 8px;">{team_name}</div>
                <span class="custom-badge {status_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)
