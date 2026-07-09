"""Page-wide CSS, injected once per rerun."""

import streamlit as st

PAGE_CSS = """
<style>
/* App-wide background and font adjustments */
.stApp {
    background-color: #0b140f;
    color: #e0e0e0;
    font-family: 'Outfit', 'Inter', sans-serif;
}

/* Glassmorphism panel container */
.glass-panel {
    background: rgba(18, 30, 22, 0.65);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(46, 125, 50, 0.25);
    border-radius: 16px;
    padding: 25px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
}

/* Section headers */
.glow-text {
    color: #00c853;
    text-shadow: 0 0 10px rgba(0, 200, 83, 0.3);
    font-weight: 800;
    letter-spacing: 0.5px;
}

.gold-text {
    color: #ffd700;
    text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    font-weight: 800;
    letter-spacing: 0.5px;
}

/* Custom badges */
.custom-badge {
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    display: inline-block;
    margin-right: 8px;
}
.badge-gold {
    background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%);
    color: #000;
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}
.badge-green {
    background: linear-gradient(135deg, #00c853 0%, #007e33 100%);
    color: #fff;
    box-shadow: 0 2px 8px rgba(0, 200, 83, 0.3);
}
.badge-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #eee;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

/* Pitch Visualizer Styles */
.pitch-container {
    background: #0d2315;
    background-image: linear-gradient(135deg, #12301c 0%, #08120a 100%);
    border: 3px solid #2e7d32;
    border-radius: 20px;
    padding: 35px 15px;
    position: relative;
    box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    margin: 20px auto;
    max-width: 850px;
}
.pitch-bg-lines {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    border: 2px solid rgba(255,255,255,0.15);
    margin: 15px;
    border-radius: 16px;
}
.pitch-half-line {
    position: absolute;
    top: 50%; left: 15px; right: 15px;
    height: 2px;
    background: rgba(255,255,255,0.15);
}
.pitch-center-circle {
    position: absolute;
    top: 50%; left: 50%;
    width: 140px; height: 140px;
    border: 2px solid rgba(255,255,255,0.15);
    border-radius: 50%;
    transform: translate(-50%, -50%);
}
.pitch-penalty-area-top {
    position: absolute;
    top: 15px; left: 50%;
    width: 320px; height: 100px;
    border: 2px solid rgba(255,255,255,0.15);
    border-top: none;
    transform: translateX(-50%);
}
.pitch-penalty-area-bottom {
    position: absolute;
    bottom: 15px; left: 50%;
    width: 320px; height: 100px;
    border: 2px solid rgba(255,255,255,0.15);
    border-bottom: none;
    transform: translateX(-50%);
}
.pitch-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 30px 0;
    position: relative;
    z-index: 10;
}

/* Card Styling - Inspired by EA Sports Ultimate Team */
.player-card {
    background: rgba(25, 35, 28, 0.9);
    border: 2px solid #cd7f32;
    border-radius: 12px;
    width: 100px;
    height: 150px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    position: relative;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    user-select: none;
}
.player-card:hover {
    transform: translateY(-8px) scale(1.06);
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    z-index: 50;
}
.card-rating-pos {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 11px;
    font-weight: bold;
    color: #fff;
}
.card-rating {
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 800;
}
.card-pos {
    font-weight: bold;
}
.card-face {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
}
.card-name {
    font-size: 10px;
    font-weight: 800;
    color: #fff;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    letter-spacing: -0.2px;
}
.card-club {
    font-size: 8px;
    color: #bbb;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
}
.empty-card {
    background: rgba(255, 255, 255, 0.03);
    border: 2px dashed rgba(255, 255, 255, 0.15);
    box-shadow: none;
}
.empty-card:hover {
    transform: none;
    box-shadow: none;
}
.empty-pos {
    font-size: 13px;
    font-weight: 800;
    color: rgba(255,255,255,0.3);
    margin-top: 40px;
}
.empty-plus {
    font-size: 18px;
    color: rgba(255,255,255,0.15);
    margin-bottom: 25px;
}

/* Card Themes */
.card-gold {
    border-color: #ffe082;
    background-image: linear-gradient(180deg, rgba(38, 30, 10, 0.95) 0%, rgba(18, 14, 5, 0.95) 100%);
    box-shadow: 0 4px 15px rgba(255, 224, 130, 0.15);
}
.card-gold .card-rating {
    background: #ffe082;
    color: #000;
}
.card-gold .card-pos {
    color: #ffe082;
}

.card-silver {
    border-color: #cfd8dc;
    background-image: linear-gradient(180deg, rgba(25, 27, 28, 0.95) 0%, rgba(12, 13, 14, 0.95) 100%);
    box-shadow: 0 4px 15px rgba(207, 216, 220, 0.1);
}
.card-silver .card-rating {
    background: #cfd8dc;
    color: #000;
}
.card-silver .card-pos {
    color: #cfd8dc;
}

.card-bronze {
    border-color: #b0bec5;
    background-image: linear-gradient(180deg, rgba(28, 23, 20, 0.95) 0%, rgba(14, 11, 10, 0.95) 100%);
}
.card-bronze .card-rating {
    background: #b0bec5;
    color: #000;
}
.card-bronze .card-pos {
    color: #b0bec5;
}

/* Card details on hover/stat sheets */
.stat-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 8px;
    text-align: center;
}
.stat-val {
    font-size: 18px;
    font-weight: 800;
    color: #ffd700;
}
.stat-lbl {
    font-size: 10px;
    color: #aaa;
    text-transform: uppercase;
}


</style>
"""


def inject_css():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
