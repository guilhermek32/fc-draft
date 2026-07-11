---
name: verify
description: Build/launch/drive recipe for verifying changes to the FC draft Streamlit app at its browser surface.
---

# Verifying the FC draft app

Streamlit app; entry point `app.py`, code in `fcdraft/`. Python env: repo `.venv` (has streamlit, pandas, pytest — no playwright).

## Launch (isolated — never clobber the repo's live `draft_state.json`)

`STATE_FILE` and `CSV_FILE` in `fcdraft/config.py` are **CWD-relative**. Run from a scratch dir with symlinks so state writes land there:

```bash
mkdir -p /tmp/fc-verify/.streamlit && cd /tmp/fc-verify
ln -sf <repo>/FC26_20250921.csv . && ln -sf <repo>/image_cache .
cp <repo>/app.py . && cp <repo>/.streamlit/config.toml .streamlit/
PYTHONPATH=<repo> <repo>/.venv/bin/streamlit run app.py \
  --server.port 8631 --server.headless true
```

Run the **local copy of app.py**, not the repo path: static file serving
(`enableStaticServing`, player faces at `./app/static/image_cache/...`) roots
at the *main script's* directory. Faces auto-migrate from the `image_cache`
symlink into `./static/image_cache/` on first render. The config.toml copy
matters too (static serving + `runner.postScriptGC=false`).

Fresh scenario = delete the scratch `draft_state.json` and restart (sessions cache state in memory).

## Drive (Playwright, separate venv)

Install playwright in its own venv (`python3 -m venv pwvenv && pip install playwright && python -m playwright install chromium` — `--with-deps` needs sudo, skip it; plain install works).

- Each `browser.new_context()` = a separate Streamlit session (multi-device sim). Cross-device sync polls every 2s.
- Widgets: text inputs → `get_by_role("textbox", name=<label>)`; selectbox → `get_by_role("combobox", name=<label>).click()` then `get_by_role("option", name=...)`; checkbox → click its label text; buttons → `get_by_role("button", name=...)` (emoji in labels is fine, name matching is partial).
- After any button that triggers `st.rerun()`, `wait_for_load_state("networkidle")` + ~1.5s sleep; expanders collapse on rerun and label clicks *toggle* them — check inner content visibility before clicking again.
- Setup page: default 4 participants; fill "Admin Password" + the 4 "Secret Password" fields (`.nth(i)`), click "Start Setup & Proceed to Bans".
- Ban phase: the three ban selectboxes default to valid distinct players, so locking bans is just: click the confirm-checkbox label, click "Lock in My Bans".
- Assert persisted outcomes by reading the scratch `draft_state.json` (players stored as id strings; `state_version` bumps every save).

## Gotchas

- `pkill -f "streamlit"` from the agent shell kills the agent's own shell (pattern matches the wrapper command) — use a background task handle or `kill $(pgrep -f 'bin/streamlit')`.
- The admin session in the ban phase still sees the participant login form in the page body (admin isn't a participant) — expected, use the sidebar for admin tools.
