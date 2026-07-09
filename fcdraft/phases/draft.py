"""Phase 3: snake draft board."""

import streamlit as st

from fcdraft.draft import auto_draft_remaining, record_pick
from fcdraft.formations import build_slot_list, get_base_position
from fcdraft.phases.ban import _ranked_bans
from fcdraft.pitch import display_pitch_component
from fcdraft.search import format_player_options, search_players
from fcdraft.cards import render_preview_card
from fcdraft.state import save_session_state


def _render_sidebar(curr_idx, seq):
    """Draft status, settings, undo, and admin tools. Returns the filter mode."""
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
    st.subheader("⚙️ Draft Settings")
    filter_mode = st.selectbox("Position Match Mode", ["Strict", "Flexible"], index=1,
                               help="Strict: Player must have exact position. Flexible: Allows adjacent positions (e.g. LWB in LB slot).")

    if curr_idx > 0:
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
            save_session_state()
            st.rerun()

    if curr_idx < len(seq):
        st.write(" ")
        with st.expander("🤖 Admin Auto-Draft Tool"):
            st.warning("This will automatically complete the entire remaining draft using the highest-rated available players.")
            auto_run_confirm = st.text_input("Type 'auto run' to confirm:", value="", key="auto_run_confirm_input").strip().lower()
            if auto_run_confirm == "auto run":
                if st.button("🚀 Execute Auto-Draft", type="primary", use_container_width=True):
                    auto_draft_remaining(filter_mode)
                    st.success("Auto-draft complete!")
                    save_session_state()
                    st.rerun()

    with st.expander("🚫 Banned Players List (Ranked by OVR)"):
        all_bans = _ranked_bans()
        if all_bans:
            for rk, b in enumerate(all_bans, 1):
                st.write(f"{rk}. **{b['short_name']}** ({b['overall']} OVR) — Banned by *{b['banned_by']}*")
        else:
            st.write("No bans submitted.")

    return filter_mode


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


def _render_draft_room(curr_idx, seq, picker, filter_mode):
    current_pick = seq[curr_idx]
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
            save_session_state()
            st.rerun()

        selected_slot = st.selectbox("Select Empty Slot", empty_slots, key=f"sel_slot_{curr_idx}")
        base_pos = get_base_position(selected_slot)

        st.write(f"2. Search and select a player. Pool automatically filtered to position: **{base_pos}** ({filter_mode} Mode)")
        search_query = st.text_input("🔍 Search by Player Name / Club / Nation", value="", placeholder="Type here...", key=f"query_{curr_idx}")
        df_pool = search_players(query=search_query, position_filter=base_pos, filter_mode=filter_mode)
        options = format_player_options(df_pool)

        p_dict = None
        if not options:
            st.warning("No players found matching your criteria. Try adjusting your search query.")
        else:
            selected_player_str = st.selectbox("Choose Player to Draft", options, key=f"choose_player_{curr_idx}")
            if selected_player_str:
                idx = options.index(selected_player_str)
                p_dict = df_pool.iloc[idx].to_dict()

        st.write(" ")
        if p_dict and p_dict.get("is_banned"):
            st.error(f"🚫 {p_dict['short_name']} was banned from this draft and cannot be drafted.")
        elif p_dict:
            if st.button(f"✅ Draft {p_dict['short_name']} for {selected_slot}", type="primary", use_container_width=True):
                record_pick(picker, selected_slot, p_dict, curr_idx + 1, current_pick["round"])
                st.session_state.current_pick_index += 1
                st.success(f"Successfully drafted {p_dict['short_name']}!")
                save_session_state()
                st.rerun()

    with col_preview:
        if p_dict:
            st.markdown("### 📋 Player Profile")
            st.markdown(render_preview_card(
                p_dict, base_pos, width=140, height=210, padding=12,
                rating_size=13, pos_size=14, face_size=90, name_size=14, club_size=10,
                rating_padding="2px 6px", margin_bottom="15px",
                banned=bool(p_dict.get("is_banned")),
            ), unsafe_allow_html=True)
            if p_dict.get("is_banned"):
                st.warning("🚫 This player was **banned** during the blind ban phase.")
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
                    st.write(f"- **{slot}:** {player['short_name']} ({player['overall']} OVR)")
                else:
                    st.write(f"- *{slot}:* (Empty)")


def _render_pitch_tab(picker):
    st.subheader("Field View")
    viewer_picker = st.selectbox(
        "Show pitch for participant:",
        st.session_state.participants,
        format_func=lambda x: f"{st.session_state.team_names.get(x, f'{x} FC')} ({x})",
        key="field_view_picker",
    )
    display_pitch_component(
        st.session_state.formations[viewer_picker],
        st.session_state.drafted_players[viewer_picker],
        st.session_state.bench_slots,
        interactive=(viewer_picker == picker),
    )


def render():
    curr_idx = st.session_state.current_pick_index
    seq = st.session_state.draft_sequence

    with st.sidebar:
        filter_mode = _render_sidebar(curr_idx, seq)

    st.title("🏟️ Snake Draft Board")

    if curr_idx < len(seq):
        picker = seq[curr_idx]["participant"]
        tab_draft, tab_board, tab_pitch = st.tabs(["🎯 Draft Room", "📊 Draft Board", "⚽ Squad Pitch Visualizer"])
        with tab_draft:
            _render_draft_room(curr_idx, seq, picker, filter_mode)
        with tab_board:
            _render_board()
        with tab_pitch:
            _render_pitch_tab(picker)
    else:
        st.session_state.phase = "completed"
        save_session_state()
        st.rerun()
