# Repository Guide

## Commands

- Run commands from repository root. Player data, state, and image-cache paths are relative to current working directory.
- CI uses Python 3.12 and fully pinned `requirements.txt`: `uv venv --python 3.12`, then `uv pip install -r requirements.txt`.
- Start app: `python -m streamlit run app.py` from activated environment. `app.py` must remain Streamlit Cloud entrypoint.
- Match CI order: `python -m py_compile app.py`, then `python -m pytest -v`.
- Focus one test: `python -m pytest tests/test_draft.py::test_commit_pick_happy_path -q`.
- No formatter, linter, typechecker, or codegen task is configured.

## Architecture

- Keep `app.py` thin. It calls `fcdraft.main.run()` and re-exports package APIs used by tests; move implementation into `fcdraft/` without breaking those exports.
- `fcdraft/main.py` bootstraps state/auth, refreshes shared state, then dispatches `setup -> ban -> draft -> completed` to `fcdraft/phases/`.
- `fcdraft/data.py` owns tracked `FC26_20250921.csv`; `state.py` owns disk persistence; `gateway.py` owns login/live sync; `draft.py` owns concurrency-sensitive pick and timeout mutations; `cards.py`/`pitch.py` produce HTML; `styles.py` contains global CSS.
- `graphify-out/` is generated navigation data, not executable source of truth; trust code/config when it disagrees.

## State And Auth

- Multi-browser sync is file-backed through ignored `draft_state.json`, atomic `.tmp` replacement, monotonic `state_version`, and Streamlit polling. State mutations must persist through `save_session_state()`; concurrency-sensitive picks/timeouts must refresh and revalidate disk state before committing.
- Preserve persistence shape: known players and pre-reveal bans save as player-ID references and rehydrate from master CSV; imported unknown players save as sanitized full dicts.
- `authed_participant`, `is_admin`, current browser `auth_token`, and one-time `generated_passwords` are session-local and must never persist. Shared URL-token map `auth_tokens` intentionally persists so `?draft_slot=` full navigation can restore login.
- Never commit `draft_state.json` or `image_cache/`; tests assert state file remains gitignored.

## Tests

- `tests/conftest.py` patches Streamlit globally before importing app code and resets shared mock session state for every test. New Streamlit APIs usually require matching mocks there.
- Patch constants where imported, e.g. `fcdraft.state.STATE_FILE` or `fcdraft.images.IMAGE_CACHE_DIR`; patching only `fcdraft.config` will not redirect existing module bindings.
- Tests use real root CSV but isolate state/cache writes with `tmp_path`; image tests mock network. Add phase smoke coverage when changing phase rendering or Streamlit widget calls.
