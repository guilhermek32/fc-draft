# Graph Report - fc-draft  (2026-07-10)

## Corpus Check
- 35 files · ~18,603 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 403 nodes · 764 edges · 38 communities (20 shown, 18 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa7231c6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- test_auth_tokens.py
- test_phases.py
- cards.py
- ui.py
- test_auth.py
- test_images.py
- setup.py
- set_credential
- Frontend Design
- Repository Guide
- test_load_corrupt_state
- Admin Auto-Draft
- Blind Ban Room
- FUT Card Rendering
- Position-Matched Filtering (Strict/Flexible)
- Roster Exports (CSV & Text Log)
- Session State Persistence (draft_state.json)
- Setup & Re-Import Phase
- Snake Draft Board & Click-to-Draft
- Squad Pitch Visualizer
- Streamlit Cloud Deployment
- Undo Last Pick
- uv Package Manager
- Pandas 3.0.3
- Pillow 12.3.0
- requests 2.34.2
- Streamlit 1.59.1

## God Nodes (most connected - your core abstractions)
1. `save_session_state()` - 22 edges
2. `commit_pick()` - 18 edges
3. `issue_auth_token()` - 13 edges
4. `build_slot_list()` - 13 edges
5. `render()` - 13 edges
6. `format_player_options()` - 13 edges
7. `refresh_shared_state()` - 13 edges
8. `MockSessionState` - 13 edges
9. `set_credential()` - 12 edges
10. `apply_pick_timeout()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_generate_password_shape_and_uniqueness()` --calls--> `generate_password()`  [EXTRACTED]
  tests/test_auth.py → fcdraft/auth.py
- `test_generated_password_verifies()` --calls--> `generate_password()`  [EXTRACTED]
  tests/test_auth.py → fcdraft/auth.py
- `test_explicit_salt_is_deterministic()` --calls--> `hash_password()`  [EXTRACTED]
  tests/test_auth.py → fcdraft/auth.py
- `test_same_password_gets_different_salts_and_hashes()` --calls--> `hash_password()`  [EXTRACTED]
  tests/test_auth.py → fcdraft/auth.py
- `test_malformed_salt_hex_returns_false()` --calls--> `verify_password()`  [EXTRACTED]
  tests/test_auth.py → fcdraft/auth.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CI Build and Verification Flow** — _github_workflows_ci_build_and_test_job, _github_workflows_ci_uv_caching, _github_workflows_ci_compilation_check, requirements_dependency_manifest [EXTRACTED 1.00]

## Communities (38 total, 18 thin omitted)

### Community 0 - "Draft App Core Logic"
Cohesion: 0.06
Nodes (70): EA FC 26 Draft Board — Streamlit entrypoint.  The application lives in the ``f, render_empty_card(), Configuration constants for the EA FC 26 draft app., get_player_by_id(), load_data(), _load_data_uncached(), _players_by_id_uncached(), Player database loading and cleaning. (+62 more)

### Community 1 - "Mock Session State Fixture"
Cohesion: 0.13
Nodes (3): mock_streamlit_state(), MockSessionState, Fixture that resets the mock session store before each test and returns it.

### Community 2 - "Draft Features & Docs"
Cohesion: 0.13
Nodes (14): 1. Create a Virtual Environment, 1. 📋 Setup & Re-Import Phase, 2. 🚫 Blind Ban Room, 2. Install Dependencies, 3. Run the App, 3. 🏟️ Snake Draft Board & Click-to-Draft, 4. 🎨 Rich Aesthetic Pitch & Substitutes Board, 5. 💾 Session State Persistence (+6 more)

### Community 3 - "CI & Dependencies"
Cohesion: 0.40
Nodes (6): build-and-test Job, CI Pipeline, Python Compilation Check, uv Dependency Caching, requirements.txt Dependency Manifest, pytest 9.1.1

### Community 4 - "Data & Search Tests"
Cohesion: 0.06
Nodes (66): Remove a token from the map (no-op for unknown/None)., revoke_auth_token(), commit_pick(), Restart the pick clock for the current pick (None when the draft is over)., Validate against the freshest shared state, then record and save a pick., reset_pick_deadline(), _finish_login(), get_authed_participant() (+58 more)

### Community 5 - "Rendering Tests"
Cohesion: 0.18
Nodes (10): Verify that empty slots are wrapped in anchor tags when interactive=True., Verify bench layout rendering., When the session holds a login token, pitch-click anchors include it so     the, Verify that render_pitch_html outputs card markup without click links when inter, Verify that cached base64 image resolver gracefully returns fallback placeholder, test_get_player_image_base64_cached_fallback(), test_interactive_links_carry_auth_token(), test_render_bench_html() (+2 more)

### Community 6 - "Draft Logic Tests"
Cohesion: 0.13
Nodes (28): apply_pick_timeout(), Relegate the on-clock participant after their pick clock ran out.      All of, _pick(), _player(), Draft-phase state on disk + in memory with an already-expired pick clock., Two players timing out end up drafting in the same order at the back., A player another participant already drafted (now visible in search) cannot be p, Verify compound slot names map to standard base FIFA positions. (+20 more)

### Community 8 - "Persistence Tests"
Cohesion: 0.07
Nodes (28): peek_state_version(), The state_version currently on disk, without touching session state.      On a, Real df rows carry a frozenset pos_set column; saving must still produce valid J, Pre-reveal bans persist as bare player ids (no names on disk) and rehydrate on l, State files written before passwords existed load with empty credentials., refresh_shared_state re-reads shared keys from disk without touching login state, Saves base the version on the disk value so alternating writers never repeat., Missing file or legacy file without the key never looks like a remote change. (+20 more)

### Community 9 - "test_auth_tokens.py"
Cohesion: 0.25
Nodes (16): issue_auth_token(), Create a URL login token for an identity, replacing any previous token for it., The identity dict for a token, or None if unknown/invalid., resolve_auth_token(), A pitch-slot click is a full navigation that starts a NEW Streamlit     session, _restore_login_from_url(), Unit tests for URL login tokens (pitch-click session restore)., test_admin_token_resolves_without_participants() (+8 more)

### Community 10 - "test_phases.py"
Cohesion: 0.19
Nodes (13): Smoke tests: every phase page renders without raising under the mocks., No login: waiting room + login gateway, no pick UI., _seed_draft_state(), test_ban_phase_renders_generated_passwords_panel(), test_ban_phase_renders_locked_view(), test_ban_phase_renders_login_gateway(), test_ban_phase_renders_picker_when_authed(), test_ban_phase_renders_reveal_room() (+5 more)

### Community 11 - "cards.py"
Cohesion: 0.19
Nodes (14): ovr_tier_class(), player_face_data_uri(), FUT-style player card HTML, shared by pitch, bench, and preview panes., Standard-size card used on the pitch and bench., Enlarged, centered preview card (draft dialog and draft-room profile pane)., render_player_card(), render_preview_card(), _download_image() (+6 more)

### Community 12 - "ui.py"
Cohesion: 0.13
Nodes (13): broadcast_row(), on_clock_strip(), page_header(), phase_rail(), Shared UI components: phase rail, headers, chips, panels., Horizontal phase step indicator injected at the top of every page., Phase title + optional subtitle in the new design language., Full-width floodlight amber strip showing whose turn it is. (+5 more)

### Community 13 - "test_auth.py"
Cohesion: 0.25
Nodes (12): hash_password(), Participant password hashing and credential checks.  Only salted PBKDF2 hashes, Hash a password, generating a fresh salt when none is given.      Returns (sal, Constant-time check of a password against a stored salt/hash pair., verify_password(), Unit tests for participant password hashing and credential checks., test_explicit_salt_is_deterministic(), test_generate_password_shape_and_uniqueness() (+4 more)

### Community 14 - "test_images.py"
Cohesion: 0.23
Nodes (6): _FakeResponse, _png_bytes(), An HTML error page must not be cached as a player image., test_cached_file_skips_network(), test_error_payload_is_never_cached(), test_valid_image_is_downloaded_and_cached()

### Community 15 - "setup.py"
Cohesion: 0.25
Nodes (10): generate_password(), Random, easy-to-share secret password., _build_draft_sequence(), _import_previous_draft(), _minimal_player_from_row(), Phase 1: participants, formations, and previous-draft import., Fallback player dict for imported names not found in the master database., Reconstruct completed-draft state from an exported roster CSV. (+2 more)

### Community 16 - "set_credential"
Cohesion: 0.32
Nodes (8): check_credential(), Store the salted hash for a participant in session state., True if the password matches the participant's stored credential., set_credential(), test_credentials_store_only_salted_hashes(), test_generated_password_verifies(), Credentials persist as salted hashes; plaintext passwords never reach disk., test_auth_credentials_round_trip_without_plaintext()

### Community 17 - "Frontend Design"
Cohesion: 0.29
Nodes (6): Design principles, Frontend Design, Ground it in the subject, More on writing in design, Process: brainstorm, explore, plan, critique, build, critique again, Restraint and self-critique

### Community 18 - "Repository Guide"
Cohesion: 0.33
Nodes (5): Architecture, Commands, Repository Guide, State And Auth, Tests

## Knowledge Gaps
- **37 isolated node(s):** `Ground it in the subject`, `Design principles`, `Process: brainstorm, explore, plan, critique, build, critique again`, `Restraint and self-critique`, `More on writing in design` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `save_session_state()` connect `Data & Search Tests` to `Draft App Core Logic`, `Persistence Tests`, `Draft Logic Tests`, `setup.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `commit_pick()` connect `Data & Search Tests` to `Draft App Core Logic`, `Draft Logic Tests`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `refresh_shared_state()` connect `Draft App Core Logic` to `Persistence Tests`, `Data & Search Tests`, `Draft Logic Tests`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `EA FC 26 Draft Board — Streamlit entrypoint.  The application lives in the ``f`, `Participant password hashing and credential checks.  Only salted PBKDF2 hashes`, `Random, easy-to-share secret password.` to the rest of the system?**
  _166 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Draft App Core Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.05510388437217705 - nodes in this community are weakly interconnected._
- **Should `Mock Session State Fixture` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `Draft Features & Docs` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._