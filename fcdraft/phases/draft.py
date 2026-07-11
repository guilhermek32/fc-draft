"""Phase 3: snake draft board."""

import time

import streamlit as st

from fcdraft.config import ADMIN_LABEL, PICK_TIMER_SECONDS
from fcdraft.draft import apply_pick_autopick, auto_draft_remaining, commit_pick, reset_pick_deadline
from fcdraft.formations import build_slot_list, get_base_position, position_label_pt, slot_label_pt
from fcdraft.gateway import (
    get_authed_participant,
    live_sync_poller,
    render_account_box,
    render_login_gateway,
    render_logout_button,
)
from fcdraft.phases.ban import _ranked_bans
from fcdraft.pitch import display_pitch_component
from fcdraft.search import (
    allowed_positions,
    first_draftable_index,
    format_player_options,
    get_ban_counts,
    search_players,
)
from fcdraft.cards import render_preview_card
from fcdraft.state import save_session_state


@st.fragment(run_every="1s")
def _pick_timer_fragment():
    """Countdown for the current pick; auto-picks for the on-clock picker on expiry.

    Any open session may trigger the timeout — apply_pick_autopick() re-checks
    the freshest shared state so concurrent enforcement lands only once.
    """
    deadline = st.session_state.get("pick_deadline")
    if deadline is None or st.session_state.current_pick_index >= len(st.session_state.draft_sequence):
        return

    remaining = deadline - time.time()
    if remaining <= 0:
        apply_pick_autopick(deadline)
        st.rerun(scope="app")

    color = "#ff4b4b" if remaining < 15 else "#ffd700"
    minutes, seconds = divmod(int(remaining), 60)
    st.markdown(f"""
    <div class="glass-panel" style="padding: 8px 15px; text-align: center; border-color: {color};">
        ⏱️ Time left for this pick:
        <span style="font-size: 22px; font-weight: 800; color: {color};">{minutes}:{seconds:02d}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_timeout_notice():
    last = st.session_state.get("last_timeout")
    if not last:
        return
    if last.get("player_name"):
        st.warning(
            f"⏱️ **{last['participant']}** ran out of time on pick {last['at_pick']} — "
            f"**{last['player_name']}** was auto-picked for **{slot_label_pt(last['slot'])}**."
        )
    else:
        # Legacy relegation notice persisted by an older version.
        st.warning(
            f"⏱️ **{last['participant']}** ran out of time on pick {last['at_pick']} — "
            "all of their remaining picks were moved to the end of the draft."
        )


def _render_sidebar(curr_idx, seq):
    """Account box, draft status, undo, and admin tools."""
    render_account_box()
    st.write("---")

    st.markdown("<h2 class='glow-text'>🏆 Draft Status</h2>", unsafe_allow_html=True)

    if curr_idx < len(seq):
        current_pick = seq[curr_idx]
        picker_name = current_pick["participant"]
        picker_team = st.session_state.team_names.get(picker_name, f"{picker_name} FC")
        st.markdown(f"""
        <div class="glass-panel" style="padding: 15px; border-color: #ffd700;">
            <h4 style="margin: 0; color: #ffd700;">🎯 Current Pick</h4>
            <div style="font-size: 22px; font-weight: 800; margin: 10px 0; line-height: 1.2;">{picker_name}<br/><span style="font-size: 13px; color: #ffd700; font-weight: 400;">{picker_team}</span></div>
            <div style="font-size: 14px; color: #aaa;">Round: <b>{current_pick['round']}</b></div>
            <div style="font-size: 14px; color: #aaa;">Pick overall: <b>{current_pick['overall_pick']} of {len(seq)}</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.write("📅 **Up Next:**")
        for offset in range(1, 5):
            next_idx = curr_idx + offset
            if next_idx < len(seq):
                np = seq[next_idx]
                np_name = np["participant"]
                np_team = st.session_state.team_names.get(np_name, f"{np_name} FC")
                st.write(f"{next_idx+1}. **{np_name}** ({np_team})")
    else:
        st.markdown("""
        <div class="glass-panel" style="padding: 15px; border-color: #00c853;">
            <h4 style="margin: 0; color: #00c853;">🎉 Draft Finished!</h4>
            <div style="font-size: 16px; margin-top: 10px;">All picks are complete. Check the Summary tab.</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    is_admin = st.session_state.get("is_admin", False)
    if is_admin and curr_idx > 0:
        st.write(" ")
        if st.button("↩️ Undo Last Pick", use_container_width=True, type="secondary"):
            prev_idx = curr_idx - 1
            prev_picker = seq[prev_idx]["participant"]

            if st.session_state.draft_history:
                last_log = st.session_state.draft_history.pop()
                slot_to_remove = last_log["slot"]
                if slot_to_remove in st.session_state.drafted_players[prev_picker]:
                    del st.session_state.drafted_players[prev_picker][slot_to_remove]

            st.session_state.current_pick_index = prev_idx
            st.success("Successfully undid the last draft pick!")
            reset_pick_deadline()
            save_session_state()
            st.rerun()

    if is_admin and curr_idx < len(seq):
        st.write(" ")
        with st.expander("🤖 Admin Auto-Draft Tool"):
            st.warning("This will automatically complete the entire remaining draft using the highest-rated available players.")
            auto_run_confirm = st.text_input("Type 'auto run' to confirm:", value="", key="auto_run_confirm_input").strip().lower()
            if auto_run_confirm == "auto run":
                if st.button("🚀 Execute Auto-Draft", type="primary", use_container_width=True):
                    auto_draft_remaining()
                    st.success("Auto-draft complete!")
                    save_session_state()
                    st.rerun()

    with st.expander("🚫 Banned Players List (Ranked by OVR)"):
        all_bans = _ranked_bans()
        if all_bans:
            for rk, b in enumerate(all_bans, 1):
                count = f" ×{b['ban_count']}" if b["ban_count"] > 1 else ""
                st.write(f"{rk}. **{b['short_name']}** ({b['overall']} OVR){count} — Banned by *{b['banned_by']}*")
        else:
            st.write("No bans submitted.")


def _render_stat_grid(p_dict):
    is_gk = "GK" in p_dict["pos_list"]
    stat_pairs = (
        [("goalkeeping_diving", "DIV"), ("goalkeeping_positioning", "POS"),
         ("goalkeeping_handling", "HAN"), ("goalkeeping_reflexes", "REF"),
         ("goalkeeping_kicking", "KIC"), ("goalkeeping_speed", "SPD")]
        if is_gk else
        [("pace", "PAC"), ("dribbling", "DRI"),
         ("shooting", "SHO"), ("defending", "DEF"),
         ("passing", "PAS"), ("physic", "PHY")]
    )
    with st.container(border=True):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            with col:
                for stat_key, stat_lbl in stat_pairs[col_idx * 2:col_idx * 2 + 2]:
                    st.markdown(
                        f"<div class='stat-box'><div class='stat-val'>{p_dict.get(stat_key, 50)}</div><div class='stat-lbl'>{stat_lbl}</div></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown(f"""
        <div style="font-size: 13px; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
            👤 <b>Full Name:</b> {p_dict['long_name']}<br/>
            🌍 <b>Nationality:</b> {p_dict['nationality_name']}<br/>
            🎂 <b>Age:</b> {p_dict['age']} years old<br/>
            🏃 <b>Positions:</b> {p_dict['player_positions']}<br/>
        </div>
        """, unsafe_allow_html=True)


# Sentinel option in the slot selectbox: browse the whole pool ("Todos").
_ALL_SLOTS = "__ALL__"
_ALL_PAGE_SIZE = 100


def _compatible_empty_slot(player, empty_slots):
    """First empty slot the player can fill (field slots first; SUB takes anyone)."""
    pos_set = set(player.get("pos_list") or [])
    fallback_sub = None
    for slot in empty_slots:
        base = get_base_position(slot)
        if base == "SUB":
            fallback_sub = fallback_sub or slot
            continue
        if pos_set & set(allowed_positions(base, "Flexible")):
            return slot
    return fallback_sub


def _render_draft_room(curr_idx, seq, picker):
    col_select, col_preview = st.columns([5, 3])

    with col_select:
        st.markdown(f"### It is **{picker}**'s turn to draft!")
        st.write("1. Select an empty slot in your formation.")

        all_slots = build_slot_list(st.session_state.formations[picker], st.session_state.bench_slots)
        squad = st.session_state.drafted_players.get(picker, {})
        empty_slots = [slot for slot in all_slots if slot not in squad]

        if not empty_slots:
            st.warning("All slots are filled for this squad.")
            st.session_state.current_pick_index += 1
            reset_pick_deadline()
            save_session_state()
            st.rerun()

        selected_slot = st.selectbox(
            "Escolha a Posição Livre",
            [_ALL_SLOTS] + empty_slots,
            index=1,
            format_func=lambda s: "Todos" if s == _ALL_SLOTS else slot_label_pt(s),
            key=f"sel_slot_{curr_idx}",
        )
        browse_all = selected_slot == _ALL_SLOTS
        base_pos = None if browse_all else get_base_position(selected_slot)

        if browse_all:
            st.write("2. Search and select a player from the **whole pool** (best overall first).")
        else:
            st.write(f"2. Search and select a player. Pool automatically filtered to position: **{position_label_pt(base_pos)}**")
        search_query = st.text_input("🔍 Search by Player Name / Club / Nation", value="", placeholder="Type here...", key=f"query_{curr_idx}")
        df_pool = search_players(query=search_query, position_filter=base_pos, filter_mode="Flexible")

        load_more_option = None
        if browse_all:
            limit_key = f"all_limit_{curr_idx}"
            limit = st.session_state.get(limit_key, _ALL_PAGE_SIZE)
            if len(df_pool) > limit:
                load_more_option = f"⬇️ Carregar mais… (mostrando {limit} de {len(df_pool)})"
            df_pool = df_pool.head(limit)
        options = format_player_options(df_pool)
        if load_more_option:
            options = options + [load_more_option]

        p_dict = None
        if not options:
            st.warning("No players found matching your criteria. Try adjusting your search query.")
        else:
            selected_player_str = st.selectbox(
                "Choose Player to Draft", options,
                index=first_draftable_index(df_pool),
                key=f"choose_player_{curr_idx}",
            )
            if load_more_option and selected_player_str == load_more_option:
                st.session_state[limit_key] = limit + _ALL_PAGE_SIZE
                st.rerun()
            elif selected_player_str:
                idx = options.index(selected_player_str)
                p_dict = df_pool.iloc[idx].to_dict()

        st.write(" ")
        if p_dict and p_dict.get("is_banned"):
            count = get_ban_counts().get(str(p_dict["player_id"]), 1)
            times = f"{count} times" if count > 1 else "once"
            st.error(f"🚫 {p_dict['short_name']} was banned {times} in this draft and cannot be drafted.")
        elif p_dict and p_dict.get("picked_by"):
            st.error(f"🔒 {p_dict['short_name']} was already drafted by **{p_dict['picked_by']}**.")
        elif p_dict:
            target_slot = _compatible_empty_slot(p_dict, empty_slots) if browse_all else selected_slot
            if target_slot is None:
                st.error(f"🚫 Nenhuma posição livre compatível com {p_dict['short_name']}.")
            elif st.button(f"✅ Draft {p_dict['short_name']} for {slot_label_pt(target_slot)}", type="primary", use_container_width=True):
                if commit_pick(picker, target_slot, p_dict):
                    st.rerun()

    with col_preview:
        if p_dict:
            preview_pos = (p_dict.get("pos_list") or ["SUB"])[0] if browse_all else base_pos
            st.markdown("### 📋 Player Profile")
            st.markdown(render_preview_card(
                p_dict, position_label_pt(preview_pos), width=140, height=210, padding=12,
                rating_size=13, pos_size=14, face_size=90, name_size=14, club_size=10,
                rating_padding="2px 6px", margin_bottom="15px",
                banned=bool(p_dict.get("is_banned") or p_dict.get("picked_by")),
            ), unsafe_allow_html=True)
            if p_dict.get("is_banned"):
                count = get_ban_counts().get(str(p_dict["player_id"]), 1)
                by = f"by **{count} participants**" if count > 1 else "by **1 participant**"
                st.warning(f"🚫 This player was **banned** {by} during the blind ban phase.")
            elif p_dict.get("picked_by"):
                st.warning(f"🔒 This player was already drafted by **{p_dict['picked_by']}**.")
            _render_stat_grid(p_dict)
        else:
            st.info("Select a player from the dropdown to see their detailed profile here.")


def _render_board():
    st.subheader("All Squads Overview")
    cols_squads = st.columns(len(st.session_state.participants))
    for idx, p_name in enumerate(st.session_state.participants):
        with cols_squads[idx]:
            team_name = st.session_state.team_names.get(p_name, f"{p_name} FC")
            st.markdown(f"#### {p_name}")
            st.markdown(f"*{team_name}*")
            st.write(f"Formation: `{st.session_state.formations[p_name]}`")
            all_slots = build_slot_list(st.session_state.formations[p_name], st.session_state.bench_slots)
            squad = st.session_state.drafted_players.get(p_name, {})

            for slot in all_slots:
                if slot in squad:
                    player = squad[slot]
                    st.write(f"- **{slot_label_pt(slot)}:** {player['short_name']} ({player['overall']} OVR)")
                else:
                    st.write(f"- *{slot_label_pt(slot)}:* (Empty)")


def _render_pitch_tab(picker):
    """Pitch visualizer; slots are clickable only for the on-clock viewer (picker)."""
    st.subheader("Field View")
    labels = {
        f"{st.session_state.team_names.get(p, f'{p} FC')} ({p})": p
        for p in st.session_state.participants
    }
    choice = st.selectbox("Show pitch for participant:", list(labels), key="field_view_picker")
    viewer_picker = labels[choice]
    display_pitch_component(
        st.session_state.formations[viewer_picker],
        st.session_state.drafted_players[viewer_picker],
        st.session_state.bench_slots,
        interactive=(viewer_picker == picker),
    )


def _render_waiting_room(viewer, curr_idx, seq, on_clock):
    """Draft Room tab for everyone who is not on the clock."""
    on_clock_team = st.session_state.team_names.get(on_clock, f"{on_clock} FC")
    st.markdown(f"""
    <div class="glass-panel" style="padding: 20px; text-align: center; border-color: #ffd700;">
        <h3 style="margin: 0;">🎯 <b>{on_clock}</b> is on the clock</h3>
        <div style="font-size: 14px; color: #aaa; margin-top: 6px;">{on_clock_team} — the screen updates automatically when they pick.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write(" ")

    if viewer is None and not st.session_state.get("is_admin"):
        render_login_gateway()
        return

    if viewer is not None:
        turns_away = next(
            (offset for offset, pick in enumerate(seq[curr_idx:]) if pick["participant"] == viewer),
            None,
        )
        if turns_away is not None:
            st.info(f"⏳ You pick in **{turns_away}** turn{'s' if turns_away != 1 else ''}.")
        else:
            st.info("✅ Your squad is complete — no picks remaining for you.")
    render_logout_button(viewer if viewer is not None else ADMIN_LABEL)


def render():
    # Rerun automatically when another device drafts a player.
    live_sync_poller()

    curr_idx = st.session_state.current_pick_index
    seq = st.session_state.draft_sequence

    with st.sidebar:
        _render_sidebar(curr_idx, seq)

    st.title("🏟️ Snake Draft Board")

    if curr_idx < len(seq):
        # Old state file (or fresh draft) without a running clock: start one now.
        if st.session_state.get("pick_deadline") is None:
            reset_pick_deadline()
            save_session_state()
        _render_timeout_notice()
        _pick_timer_fragment()

        on_clock = seq[curr_idx]["participant"]
        viewer = get_authed_participant()
        is_my_turn = viewer is not None and viewer == on_clock

        tab_draft, tab_board, tab_pitch = st.tabs(["🎯 Draft Room", "📊 Draft Board", "⚽ Squad Pitch Visualizer"])
        with tab_draft:
            if is_my_turn:
                _render_draft_room(curr_idx, seq, on_clock)
                render_logout_button(viewer)
            else:
                _render_waiting_room(viewer, curr_idx, seq, on_clock)
        with tab_board:
            _render_board()
        with tab_pitch:
            _render_pitch_tab(on_clock if is_my_turn else None)
    else:
        st.session_state.phase = "completed"
        save_session_state()
        st.rerun()
