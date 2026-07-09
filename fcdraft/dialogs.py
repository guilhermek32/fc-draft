"""Draft pick dialog (opened via ?draft_slot= pitch clicks)."""

import streamlit as st

from fcdraft.cards import render_preview_card
from fcdraft.draft import record_pick
from fcdraft.formations import get_base_position
from fcdraft.search import format_player_options, search_players
from fcdraft.state import save_session_state


@st.dialog("🎯 Draft Player Slot")
def draft_player_dialog(slot, picker):
    st.markdown(f"### Draft Player for: **{slot}**")

    base_pos = get_base_position(slot)
    filter_mode = st.session_state.get("filter_mode", "Flexible")
    st.write(f"Position Filter: **{base_pos}** ({filter_mode} Mode)")

    search_query = st.text_input("🔍 Search by Name / Club / Nation", value="", key="dialog_search_input")
    df_pool = search_players(query=search_query, position_filter=base_pos, filter_mode=filter_mode)
    options = format_player_options(df_pool)

    p_dict = None
    if not options:
        st.warning("No players found. Try adjusting search.")
    else:
        selected_player_str = st.selectbox("Choose Player to Draft", options, key="dialog_choose_player")
        if selected_player_str:
            idx = options.index(selected_player_str)
            p_dict = df_pool.iloc[idx].to_dict()

    if p_dict:
        st.write(" ")
        st.html(render_preview_card(
            p_dict, base_pos, width=120, height=180, padding=10,
            rating_size=11, pos_size=12, face_size=70, name_size=12, club_size=9,
            border_radius="8px",
        ))

        if st.button("✅ Confirm Draft", type="primary", use_container_width=True):
            curr_idx = st.session_state.current_pick_index
            current_pick = st.session_state.draft_sequence[curr_idx]
            record_pick(picker, slot, p_dict, curr_idx + 1, current_pick["round"])
            st.session_state.current_pick_index += 1
            save_session_state()

            st.query_params.pop("draft_slot", None)
            st.rerun()

    st.write(" ")
    if st.button("❌ Cancel & Close", use_container_width=True, type="secondary"):
        st.query_params.pop("draft_slot", None)
        st.rerun()
