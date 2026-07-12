"""Phase 4: final squads, exports, and reset."""

import io

import pandas as pd
import streamlit as st

from fcdraft.formations import build_slot_list
from fcdraft.pitch import display_pitch_component
from fcdraft.state import reset_session_state


@st.cache_data(show_spinner=False)
def _build_exports_cached(state_version):
    """Cached exports; any squad change bumps state_version and invalidates."""
    return _build_exports()


def _build_exports():
    """Roster rows (for CSV) and the plain-text summary for every participant."""
    roster_rows = []
    text_summary = "EA FC 26 PLAYER DRAFT - FINAL ROSTERS\n"
    text_summary += "========================================\n\n"

    for participant in st.session_state.participants:
        team_name = st.session_state.team_names.get(participant, f"{participant} FC")
        formation = st.session_state.formations[participant]
        text_summary += f"Participant: {participant} (Team: {team_name} | Formation: {formation})\n"
        text_summary += "----------------------------------------\n"

        squad = st.session_state.drafted_players.get(participant, {})
        for slot in build_slot_list(formation, st.session_state.bench_slots):
            player = squad.get(slot, {})
            p_name = player.get("short_name", "N/A")
            p_ovr = player.get("overall", "N/A")
            p_club = player.get("club_name", "N/A")
            p_nat = player.get("nationality_name", "N/A")
            p_pos = player.get("player_positions", "N/A")

            roster_rows.append({
                "Participant": participant,
                "Team Name": team_name,
                "Formation": formation,
                "Slot": slot,
                "Player Name": p_name,
                "Overall": p_ovr,
                "Club": p_club,
                "Nationality": p_nat,
                "Listed Positions": p_pos,
            })
            text_summary += f"[{slot}] {p_name} - {p_ovr} OVR | {p_pos} | {p_club} ({p_nat})\n"
        text_summary += "\n"

    return pd.DataFrame(roster_rows), text_summary


def render():
    st.title("🏆 Draft Complete! Final Squads")
    st.write("Congratulations! All participants have built their squads. View squads, analyze stats, or export rosters below.")

    df_rosters, text_summary = _build_exports_cached(st.session_state.get("state_version", 0))

    with st.container(border=True):
        st.subheader("💾 Export Roster Options", anchor=False)
        col_csv, col_txt, col_reset = st.columns(3)

        with col_csv:
            csv_buffer = io.BytesIO()
            df_rosters.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export Rosters (CSV)",
                data=csv_buffer.getvalue(),
                file_name="fc26_draft_rosters.csv",
                mime="text/csv",
                width='stretch',
            )

        with col_txt:
            st.download_button(
                label="📥 Export Rosters (TXT Summary)",
                data=text_summary,
                file_name="fc26_draft_summary.txt",
                mime="text/plain",
                width='stretch',
            )

        with col_reset:
            if st.button("🔄 Reset and Start New Draft", use_container_width=True, type="secondary"):
                reset_session_state()
                st.rerun()

    tab_view, tab_data = st.tabs(["⚽ Visual Roster Sheets", "📊 Raw Rosters Table"])

    with tab_view:
        for participant in st.session_state.participants:
            part_df = df_rosters[df_rosters["Participant"] == participant]
            valid_ovrs = pd.to_numeric(part_df["Overall"], errors="coerce").dropna()
            avg_ovr = valid_ovrs.mean() if not valid_ovrs.empty else 0.0
            team_name = st.session_state.team_names.get(participant, f"{participant} FC")

            with st.expander(f"🏅 {team_name} ({participant}'s Squad) (Rating Avg: {avg_ovr:.1f})", expanded=True):
                display_pitch_component(
                    st.session_state.formations[participant],
                    st.session_state.drafted_players[participant],
                    st.session_state.bench_slots,
                )

    with tab_data:
        st.subheader("Raw Rosters Dataframe")
        st.dataframe(df_rosters, width='stretch')
