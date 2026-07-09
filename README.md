# ⚽ EA FC 26 Player Draft Board

[![Streamlit App](https://static.streamlit.io/badge_github_white.svg)](https://share.streamlit.io)
[![CI Status](https://github.com/guilhermek32/fc-draft/actions/workflows/ci.yml/badge.svg)](https://github.com/guilhermek32/fc-draft/actions)
[![Python 3.11+](https://img.shields.www.com/badge/python-3.11+-blue.svg)](https://www.python.org/)

A premium, interactive web application built with **Streamlit** and **Pandas** to run an EA FC 26 player draft among a group of friends. The app uses real EA FC 26 database stats, offers blind banning, manages randomized snake drafting order, displays a clickable tactical football pitch view, and persists state across page reloads.

---

## 🚀 Key Features

### 1. 📋 Setup & Re-Import Phase
* **Participant Customization**: Supports up to 20 participants with custom user names, team names (defaulting to `<Name> FC`), and individual tactical formations (e.g., 4-3-3, 3-5-2, 4-4-2, etc.).
* **Custom Bench Count**: Configure your own count of substitute players.
* **CSV Re-Import**: Upload a previously exported roster CSV file to instantly reconstruct the draft board, restore formations, and load squads, without repeating the draft.

### 2. 🚫 Blind Ban Room
* **Hidden Bans**: Each participant selects 3 soccer players to ban. Selections are kept entirely hidden until all players have locked their bans.
* **OVR Ban Ranking**: Once bans are locked and revealed, banned players are listed as a numbered ranking sorted by Overall rating (highest first) to highlight who removed the top talent from the pool.

### 3. 🏟️ Snake Draft Board & Click-to-Draft
* **Snake Order Sequence**: Generates a randomized fair snake draft order.
* **Position-Matched Filtering**: Automatically filters available database pools based on the chosen slot (e.g., selecting `LM` only displays Left Midfielders). Includes a toggle between **Strict** and **Flexible** (allowing adjacent slots like LWB for LB) matching rules.
* **Click-to-Draft**: Click directly on empty position cards on the **Squad Pitch Visualizer** to launch a Streamlit dialog (`@st.dialog`) popup, search for players, preview their stats, and confirm selections.
* **Admin Auto-Draft**: Protects your draft progress via safety locks. Typing the string `auto run` in the sidebar unlocks the **Execute Auto-Draft** button to automatically fast-forward remaining slots using highest OVR available matching players.
* **Undo Support**: Instantly revert accidental clicks with the `↩️ Undo Last Pick` sidebar hook.

### 4. 🎨 Rich Aesthetic Pitch & Substitutes Board
* **FUT Card Rendering**: Renders player cards styled after Ultimate Team cards (Gold for 85+ OVR, Silver for 75-84, Bronze for <75) on a green pitch with penalty boxes and tactical lines.
* **Cached Card Faces**: Automatically downloads player face images to local cache (`image_cache/`) and reads them as Base64 Data URIs to bypass CDN rate-limits and load pages instantly.

### 5. 💾 Session State Persistence
* Saves all draft configurations, draft history logs, and squad selections on disk in `draft_state.json` during state-mutating actions (picking, resetting, and banning).
* Automatically reloads active states at startup, protecting your progress from browser refreshes or server restarts.

### 📥 6. Roster Exports
* Export rosters directly as a standardized CSV table.
* Generate and download a complete human-readable text draft log and final summary report.

---

## 🛠️ Installation & Local Execution

We recommend using **`uv`** (by Astral) for rapid package management.

### 1. Create a Virtual Environment
Initialize a Python virtual environment in the project root:
```bash
uv venv
```

### 2. Install Dependencies
Install Streamlit, Pandas, and Python libraries inside the virtual environment:
```bash
uv pip install -r requirements.txt
```

### 3. Run the App
Launch the Streamlit server:
```bash
.venv/bin/streamlit run app.py
```
Open **http://localhost:8501** in your browser!

---

## 🧪 Continuous Integration (CI)
This repository includes a GitHub Actions CI pipeline (`.github/workflows/ci.yml`) that:
* Triggers on every push or pull request to the `main` branch.
* Spins up an Ubuntu runner, configures Python, and setups `uv` caching.
* Runs a compilation check (`python -m py_compile app.py`) to verify there are no syntax errors before deployment.

---

## 🚀 Deployment to Streamlit Cloud
You can deploy this application for free on **[Streamlit Community Cloud](https://share.streamlit.io/)**:
1. Log in with your GitHub account.
2. Click **New app** and specify your repository: `guilhermek32/fc-draft`.
3. Set the Branch: `main`, and Main file path: `app.py`.
4. Click **Deploy!**
Streamlit Cloud will read `requirements.txt` and host the draft board publicly.