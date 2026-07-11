"""Draft pick dialog (opened via ?draft_slot= pitch clicks)."""

import streamlit as st

from fcdraft.cards import render_preview_card
from fcdraft.draft import commit_pick
from fcdraft.formations import get_base_position, position_label_pt, slot_label_pt
from fcdraft.search import format_player_options, get_ban_counts, search_players


@st.dialog("🎯 Draft Player Slot")
def draft_player_dialog(slot, picker):
    if st.session_state.get("authed_participant") != picker:
        st.warning(f"Only **{picker}** can make this pick.")
        if st.button("Close", use_container_width=True):
            st.query_params.pop("draft_slot", None)
            st.rerun()
        return

    st.markdown(f"### Draft Player for: **{slot_label_pt(slot)}**")

    base_pos = get_base_position(slot)
    st.write(f"Position Filter: **{position_label_pt(base_pos)}**")

    search_query = st.text_input("🔍 Search by Name / Club / Nation", value="", key="dialog_search_input")
    df_pool = search_players(query=search_query, position_filter=base_pos, filter_mode="Flexible")
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
            p_dict, position_label_pt(base_pos), width=120, height=180, padding=10,
            rating_size=11, pos_size=12, face_size=70, name_size=12, club_size=9,
            border_radius="8px", banned=bool(p_dict.get("is_banned") or p_dict.get("picked_by")),
        ))

        if p_dict.get("is_banned"):
            count = get_ban_counts().get(str(p_dict["player_id"]), 1)
            times = f"{count} times" if count > 1 else "once"
            st.error(f"🚫 {p_dict['short_name']} was banned {times} in this draft and cannot be drafted.")
        elif p_dict.get("picked_by"):
            st.error(f"🔒 {p_dict['short_name']} was already drafted by **{p_dict['picked_by']}**.")
        elif st.button("✅ Confirm Draft", type="primary", use_container_width=True):
            if commit_pick(picker, slot, p_dict):
                st.query_params.pop("draft_slot", None)
                st.rerun()

    st.write(" ")
    if st.button("❌ Cancel & Close", use_container_width=True, type="secondary"):
        st.query_params.pop("draft_slot", None)
        st.rerun()
