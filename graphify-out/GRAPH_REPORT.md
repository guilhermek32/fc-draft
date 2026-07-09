# Graph Report - .  (2026-07-09)

## Corpus Check
- Corpus is ~7,304 words - fits in a single context window. You may not need a graph.

## Summary
- 91 nodes · 110 edges · 9 communities
- Extraction: 93% EXTRACTED · 6% INFERRED · 1% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.76)
- Token cost: 25,774 input · 0 output

## Community Hubs (Navigation)
- Draft App Core Logic
- Mock Session State Fixture
- Draft Features & Docs
- CI & Dependencies
- Data & Search Tests
- Rendering Tests
- Draft Logic Tests
- Card & Pitch Visuals
- Persistence Tests

## God Nodes (most connected - your core abstractions)
1. `MockSessionState` - 13 edges
2. `EA FC 26 Player Draft Board` - 8 edges
3. `get_player_image_base64_cached()` - 6 edges
4. `Snake Draft Board & Click-to-Draft` - 6 edges
5. `draft_player_dialog()` - 5 edges
6. `build-and-test Job` - 5 edges
7. `render_pitch_html()` - 4 edges
8. `display_pitch_component()` - 4 edges
9. `Session State Persistence (draft_state.json)` - 4 edges
10. `requirements.txt Dependency Manifest` - 4 edges

## Surprising Connections (you probably didn't know these)
- `EA FC 26 Player Draft Board` --references--> `CI Pipeline`  [EXTRACTED]
  README.md → .github/workflows/ci.yml
- `EA FC 26 Player Draft Board` --references--> `Streamlit 1.59.1`  [EXTRACTED]
  README.md → requirements.txt
- `FUT Card Rendering` --conceptually_related_to--> `Pillow 12.3.0`  [AMBIGUOUS]
  README.md → requirements.txt
- `build-and-test Job` --references--> `pytest 9.1.1`  [EXTRACTED]
  .github/workflows/ci.yml → requirements.txt
- `uv Package Manager` --conceptually_related_to--> `uv Dependency Caching`  [INFERRED]
  README.md → .github/workflows/ci.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Draft Application Flow Phases** — readme_setup_and_reimport_phase, readme_blind_ban_room, readme_snake_draft_board, readme_roster_exports [EXTRACTED 1.00]
- **CI Build and Verification Flow** — _github_workflows_ci_build_and_test_job, _github_workflows_ci_uv_caching, _github_workflows_ci_compilation_check, requirements_dependency_manifest [EXTRACTED 1.00]
- **Pitch and Card Rendering System** — readme_squad_pitch_visualizer, readme_fut_card_rendering, readme_cached_card_faces [INFERRED 0.85]

## Communities (9 total, 0 thin omitted)

### Community 0 - "Draft App Core Logic"
Cohesion: 0.17
Nodes (18): auto_draft_remaining(), display_pitch_component(), draft_player_dialog(), get_base_position(), get_cached_player_image_base64(), get_formation_slots(), get_pitch_layout(), get_player_image_base64_cached() (+10 more)

### Community 1 - "Mock Session State Fixture"
Cohesion: 0.13
Nodes (3): mock_streamlit_state(), MockSessionState, Fixture that resets the mock session store before each test and returns it.

### Community 2 - "Draft Features & Docs"
Cohesion: 0.29
Nodes (10): Admin Auto-Draft, Blind Ban Room, EA FC 26 Player Draft Board, Position-Matched Filtering (Strict/Flexible), Roster Exports (CSV & Text Log), Session State Persistence (draft_state.json), Setup & Re-Import Phase, Snake Draft Board & Click-to-Draft (+2 more)

### Community 3 - "CI & Dependencies"
Cohesion: 0.28
Nodes (9): build-and-test Job, CI Pipeline, Python Compilation Check, uv Dependency Caching, Streamlit Cloud Deployment, uv Package Manager, requirements.txt Dependency Manifest, pytest 9.1.1 (+1 more)

### Community 4 - "Data & Search Tests"
Cohesion: 0.22
Nodes (8): Verify that search_players filters rows based on query text matches., Verify strict position filtering (e.g. only matching exact position list entries, Verify flexible position filtering (matching adjacent slots like LB for LWB)., Verify that load_data loads a valid DataFrame with player rows and expected colu, test_load_data(), test_search_players_by_name(), test_search_players_flexible_position(), test_search_players_strict_position()

### Community 5 - "Rendering Tests"
Cohesion: 0.22
Nodes (8): Verify that empty slots are wrapped in anchor tags when interactive=True., Verify bench layout rendering., Verify that cached base64 image resolver gracefully returns fallback placeholder, Verify that render_pitch_html outputs card markup without click links when inter, test_get_player_image_base64_cached_fallback(), test_render_bench_html(), test_render_pitch_html_interactive(), test_render_pitch_html_non_interactive()

### Community 6 - "Draft Logic Tests"
Cohesion: 0.29
Nodes (6): Verify compound slot names map to standard base FIFA positions., Verify that auto_draft_remaining automatically drafts matching players for all e, Verify slots match the specified tactical formation., test_auto_draft_remaining(), test_get_base_position(), test_get_formation_slots()

### Community 7 - "Card & Pitch Visuals"
Cohesion: 0.40
Nodes (5): Cached Card Faces (image_cache Base64), FUT Card Rendering, Squad Pitch Visualizer, Pillow 12.3.0, requests 2.34.2

### Community 8 - "Persistence Tests"
Cohesion: 0.40
Nodes (4): Verify that load_session_state returns False if state file does not exist., Test that save_session_state saves data to disk, and load_session_state restores, test_load_non_existent_state(), test_save_and_load_session_state()

## Ambiguous Edges - Review These
- `FUT Card Rendering` → `Pillow 12.3.0`  [AMBIGUOUS]
  README.md · relation: conceptually_related_to

## Knowledge Gaps
- **7 isolated node(s):** `Admin Auto-Draft`, `Undo Last Pick`, `Position-Matched Filtering (Strict/Flexible)`, `Pandas 3.0.3`, `pytest 9.1.1` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `FUT Card Rendering` and `Pillow 12.3.0`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `EA FC 26 Player Draft Board` connect `Draft Features & Docs` to `CI & Dependencies`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Snake Draft Board & Click-to-Draft` connect `Draft Features & Docs` to `Card & Pitch Visuals`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `Serialize and save the current draft state to disk.`, `Deserialize and load saved draft state from disk if it exists.`, `Retrieve player image locally or download it, then return its base64 Data URI.` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Mock Session State Fixture` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._