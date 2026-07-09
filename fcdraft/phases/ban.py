"""Phase 2: blind player bans."""

import streamlit as st

from fcdraft.search import format_player_options, search_players
from fcdraft.state import save_session_state


def _ranked_bans():
    """All submitted bans, tagged with who banned them, highest OVR first."""
    all_bans = []
    for participant, player_list in st.session_state.bans.items():
        for p in player_list:
            p_copy = p.copy()
            p_copy["banned_by"] = participant
            all_bans.append(p_copy)
    return sorted(all_bans, key=lambda x: x.get("overall", 50), reverse=True)


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


def render():
    st.title("🚫 Phase 2: Blind Player Bans")
    st.write("Each participant must select exactly **3 players** to ban from the pool. Selections are blind and hidden until all submit.")

    remaining_participants = [p for p in st.session_state.participants if not st.session_state.ban_submissions[p]]

    if remaining_participants:
        st.subheader("Select Participant to Submit Bans", anchor=False)
        selected_picker = st.selectbox("Who is banning right now?", remaining_participants)

        st.markdown(f"### 🛡️ Ban Selection for **{selected_picker}**")
        st.info("Pass the screen to this participant. Once they lock in their bans, the choices will be hidden.")

        col_ban1, col_ban2, col_ban3 = st.columns(3)
        with col_ban1:
            p1_dict = _ban_choice_column(1, selected_picker, [])
        with col_ban2:
            p2_dict = _ban_choice_column(2, selected_picker, [p1_dict["player_id"]] if p1_dict else [])
        with col_ban3:
            exclude_ids = [p["player_id"] for p in (p1_dict, p2_dict) if p]
            p3_dict = _ban_choice_column(3, selected_picker, exclude_ids)

        st.write(" ")
        if st.button(f"🔒 Lock in Bans for {selected_picker}", use_container_width=True, type="primary"):
            if not p1_dict or not p2_dict or not p3_dict:
                st.error("Please ensure you have selected three distinct players to ban.")
            else:
                st.session_state.bans[selected_picker] = [p1_dict, p2_dict, p3_dict]
                st.session_state.ban_submissions[selected_picker] = True
                st.success(f"Bans locked for {selected_picker}! Moving on.")
                save_session_state()
                st.rerun()
    else:
        st.success("✅ All participants have submitted their bans!")
        st.subheader("Global Bans Reveal Room")
        st.write("Ready to see who was banned? This will reveal the final global ban list and start the Snake Draft.")

        with st.container(border=True):
            st.markdown("### 🏆 Banned Players Ranking (Highest OVR first)")
            for rk, b in enumerate(_ranked_bans(), 1):
                st.markdown(f"{rk}. **{b['short_name']}** ({b['overall']} OVR) — Banned by *{b['banned_by']}*")

        st.write(" ")
        if st.button("🔥 Reveal Bans & Start Snake Draft", use_container_width=True, type="primary"):
            banned_player_ids = set()
            for player_list in st.session_state.bans.values():
                for p in player_list:
                    banned_player_ids.add(p["player_id"])

            st.session_state.banned_player_ids = banned_player_ids
            st.session_state.phase = "draft"
            save_session_state()
            st.rerun()

    st.write(" ")
    st.write("---")
    st.subheader("Ban Submission Status", anchor=False)
    cols_status = st.columns(len(st.session_state.participants))
    for idx, p_name in enumerate(st.session_state.participants):
        with cols_status[idx]:
            submitted = st.session_state.ban_submissions[p_name]
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
