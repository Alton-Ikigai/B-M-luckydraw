import streamlit as st
import pandas as pd
import random
import time
import base64
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Belanja & Menang Winner Selection",
    layout="centered",
)
st.markdown("""
<head>
  <meta property="og:title" content="Belanja & Menang Winner Selection" />
  <meta property="og:description" content="Lucky draw winner selection system" />
  <meta property="og:image" content="https://raw.githubusercontent.com/Alton-Ikigai/B-M-luckydraw/main/preview.png" />
  <meta property="og:url" content="https://b-m-luckydraw-fd9sxyrpghmwyj5rw7tyzp.streamlit.app/" />
</head>
""", unsafe_allow_html=True)
# ── Image helpers ──────────────────────────────────────────────────────────────
def get_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def apply_background(image_path: str):
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    b64 = get_base64(image_path)
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/{mime};base64,{b64}");
        background-size: cover;
        background-position: center top;
        background-attachment: scroll;
        background-repeat: no-repeat;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(10, 10, 20, 0.40);
        z-index: 0;
    }}
    [data-testid="stAppViewContainer"] > * {{ position: relative; z-index: 1; }}
    </style>
    """, unsafe_allow_html=True)

# ── File names ─────────────────────────────────────────────────────────────────
BG_FILE   = "background.jpg"
LOGO_FILE = "logo.png"

if Path(BG_FILE).exists():
    apply_background(BG_FILE)
else:
    st.markdown("<style>.stApp { background: #0d0d14; }</style>", unsafe_allow_html=True)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap');

  #MainMenu { visibility: hidden; }
  header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
  footer { visibility: hidden; }
  [data-testid="stToolbar"] { display: none !important; }

  html, body, [class*="css"],
  p, span, div, label, li, a,
  h1, h2, h3, h4, h5, h6,
  .stMarkdown, .stText,
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] span,
  [data-testid="stMarkdownContainer"] li,
  [data-testid="stWidgetLabel"] p,
  [data-testid="stWidgetLabel"] span,
  [data-testid="stFileUploaderLabel"] p,
  [data-testid="stFileUploaderLabel"] span,
  .stFileUploader label, .stFileUploader p,
  .stAlert p, [data-testid="stAlert"] p, [data-testid="stAlert"] span {
    font-family: 'DM Sans', sans-serif !important;
    color: #ffffff !important;
  }
  h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #ffffff !important; }

  [data-testid="stAlert"] { background: rgba(22,22,42,0.85) !important; border-radius: 10px !important; }

  [data-testid="stAppViewContainer"] { padding-top: 0 !important; }
  [data-testid="block-container"] {
    padding-top: 0 !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 680px !important;
  }

  .logo-topright { position: fixed; top: 16px; right: 24px; z-index: 999; }
  .logo-topright img { width: 120px; object-fit: contain; }

  .title-block {
    position: fixed; top: 150px; right: 40px; z-index: 998;
    text-align: right; max-width: 320px;
  }
  .title-block h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 32px !important; font-weight: 700 !important;
    color: #ffffff !important; line-height: 1.3 !important;
    margin: 0 0 8px !important; text-shadow: 2px 2px 10px rgba(0,0,0,0.95);
  }
  .title-block p {
    font-size: 14px !important; color: #eeeeee !important;
    margin: 0 !important; text-shadow: 1px 1px 6px rgba(0,0,0,0.95);
  }

  [data-testid="stFileUploadDropzone"] {
    border: 1.5px solid #cccccc !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.88) !important;
  }
  [data-testid="stFileUploadDropzone"] p,
  [data-testid="stFileUploadDropzone"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] p,
  [data-testid="stFileUploaderDropzoneInstructions"] div { color: #222222 !important; }
  [data-testid="stFileUploadDropzone"] svg { fill: #333333 !important; }
  [data-testid="stFileUploadDropzone"] button {
    color: #222222 !important; border-color: #555555 !important; background: transparent !important;
  }

  .tier-card {
    border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 0.75rem;
    position: relative; overflow: hidden;
    display: flex; align-items: center; gap: 16px;
  }
  .tier-gold   { background: rgba(59,45,14,0.92);  border: 1px solid #c9a227; }
  .tier-silver { background: rgba(30,30,40,0.92);  border: 1px solid #8e9db5; }
  .tier-bronze { background: rgba(42,22,16,0.92);  border: 1px solid #a0522d; }
  .tier-backup { background: rgba(20,20,30,0.88);  border: 1px solid #555577; }

  .tier-icon { font-size: 40px; line-height: 1; flex-shrink: 0; }
  .tier-text { flex: 1; }
  .tier-label {
    font-size: 11px; font-weight: 500; letter-spacing: .12em;
    text-transform: uppercase; opacity: .75; margin-bottom: 3px; color: #ffffff !important;
  }
  .tier-winner { font-family: 'Playfair Display', serif !important; font-size: 24px; font-weight: 700; }

  .round-banner {
    background: rgba(74,63,165,0.85); border: 1px solid #6a5fcc;
    border-radius: 10px; padding: 0.6rem 1.2rem;
    font-size: 13px; font-weight: 500; color: #ffffff !important;
    display: inline-block; margin-bottom: 1rem;
  }

  /* Next prize banner */
  .next-prize-box {
    background: rgba(10,10,25,0.80);
    border: 1px solid #444466;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    display: flex; align-items: center; gap: 14px;
  }
  .next-prize-box .np-icon { font-size: 48px; line-height: 1; flex-shrink: 0; }
  .next-prize-box .np-info { flex: 1; }
  .next-prize-box .np-label { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #aaaacc !important; margin-bottom: 4px; }
  .next-prize-box .np-title { font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: #ffffff !important; }
  .next-prize-box .np-pool  { font-size: 12px; color: #aaaacc !important; margin-top: 4px; }

  .summary-card {
    background: rgba(10,10,25,0.88); border: 1px solid #333355;
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
  }
  .summary-title {
    font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700;
    color: #ffffff; margin: 0 0 1rem;
    border-bottom: 1px solid #333355; padding-bottom: 0.75rem;
  }
  .summary-row {
    display: flex; align-items: center; gap: 14px; padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .summary-row:last-child { border-bottom: none; }
  .summary-icon { font-size: 28px; flex-shrink: 0; width: 34px; text-align: center; }
  .summary-info { flex: 1; }
  .summary-prize { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #aaaacc !important; margin-bottom: 2px; }
  .summary-name  { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; }
  .summary-backup-name { font-size: 15px; color: #aaaacc !important; margin-top: 2px; }
  .gold-name   { color: #f5c842 !important; }
  .silver-name { color: #c0cfe0 !important; }
  .bronze-name { color: #d4825a !important; }

  .rolling-text {
    font-family: 'Playfair Display', serif !important;
    font-size: 26px; font-weight: 700; color: #ffffff !important;
    animation: pulse 0.35s infinite alternate; text-align: center; padding: 1rem 0;
  }
  @keyframes pulse { from { opacity:.3; } to { opacity:1; } }

  hr { border-color: #444466 !important; }

  div[data-testid="stButton"] > button {
    background: rgba(10,10,20,0.6) !important; border: 1px solid #666688 !important;
    border-radius: 8px !important; color: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important; transition: all .18s !important;
  }
  div[data-testid="stButton"] > button:hover {
    border-color: #aaaacc !important; background: rgba(28,28,48,0.9) !important;
  }
  div[data-testid="stButton"] > button[kind="primary"] {
    background: #4a3fa5 !important; border-color: #6a5fcc !important;
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover { background: #5a50be !important; }
</style>
""", unsafe_allow_html=True)

# ── Logo & Title ───────────────────────────────────────────────────────────────
if Path(LOGO_FILE).exists():
    logo_b64 = get_base64(LOGO_FILE)
    ext = Path(LOGO_FILE).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    st.markdown(f'<div class="logo-topright"><img src="data:image/{mime};base64,{logo_b64}" alt="Logo"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
  <h1>Belanja & Menang<br>Winner Selection</h1>
  <p>Three prizes. One name each.<br>Let fate decide.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 240px;'></div>", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "names":           [],
        "pool":            [],
        "winners":         {"3rd": None, "2nd": None, "1st": None},
        "backups":         {"3rd": None, "2nd": None, "1st": None},
        # stages: upload | w_ready | w_drawing | w_done | b_ready | b_drawing | summary
        "stage":           "upload",
        "current_tier":    "3rd",   # which tier is being drawn right now
        "draw_order":      ["3rd", "2nd", "1st"],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()
s = st.session_state

TIER_META = {
    "3rd": {"label": "3rd Prize", "badge": "🥉", "cls": "tier-bronze", "name_color": "#d4825a"},
    "2nd": {"label": "2nd Prize", "badge": "🥈", "cls": "tier-silver", "name_color": "#c0cfe0"},
    "1st": {"label": "1st Prize", "badge": "🥇", "cls": "tier-gold",   "name_color": "#f5c842"},
}
NAME_CLS = {"3rd": "bronze-name", "2nd": "silver-name", "1st": "gold-name"}

def reset():
    for k in ["names","pool","winners","backups","stage","current_tier"]:
        del st.session_state[k]
    _init()

def next_tier_after(tier):
    idx = s["draw_order"].index(tier)
    return s["draw_order"][idx + 1] if idx + 1 < len(s["draw_order"]) else None

def render_winner_card(tier_key, name, is_backup=False):
    m = TIER_META[tier_key]
    cls   = "tier-backup" if is_backup else m["cls"]
    label = f"Backup — {m['label']}" if is_backup else m["label"]
    icon  = "🔄" if is_backup else m["badge"]
    color = "#aaaacc" if is_backup else m["name_color"]
    st.markdown(f"""
    <div class="tier-card {cls}">
      <div class="tier-icon">{icon}</div>
      <div class="tier-text">
        <div class="tier-label">{label}</div>
        <div class="tier-winner" style="color:{color} !important;">{name}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
if s["stage"] == "upload":
    uploaded = st.file_uploader("Drop the name list here", type=["csv"])
    if uploaded:
        try:
            df    = pd.read_csv(uploaded, header=0)
            col   = df.columns[0]
            names = df[col].dropna().astype(str).str.strip().tolist()
            names = [n for n in names if n]
            if len(names) < 6:
                st.error(f"Need at least 6 participants — only found {len(names)}.")
            else:
                s["names"] = names
                s["pool"]  = names.copy()
                st.success(f"✓ Loaded **{len(names)} participants** successfully!")
                if st.button("Start Lucky Draw →", type="primary", use_container_width=True):
                    s["stage"]        = "w_ready"
                    s["current_tier"] = "3rd"
                    st.rerun()
        except Exception as e:
            st.error(f"Could not read file: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# WINNER ROUND — ready (show button, wait for click)
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "w_ready":
    st.markdown('<div class="round-banner">🏆 Round 1 — Main Winners</div>', unsafe_allow_html=True)

    # Show already-drawn winners
    for t in s["draw_order"]:
        if s["winners"][t]:
            render_winner_card(t, s["winners"][t])

    # Show next prize box
    tier = s["current_tier"]
    meta = TIER_META[tier]
    st.markdown(f"""
    <div class="next-prize-box">
      <div class="np-icon">{meta['badge']}</div>
      <div class="np-info">
        <div class="np-label">Up next</div>
        <div class="np-title">{meta['label']}</div>
        <div class="np-pool">{len(s['pool'])} names remaining in pool</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"Draw {meta['label']} {meta['badge']}", type="primary", use_container_width=True):
            s["stage"] = "w_drawing"
            st.rerun()
    with col2:
        if st.button("Reset", use_container_width=True):
            reset(); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# WINNER ROUND — drawing (animate then reveal)
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "w_drawing":
    st.markdown('<div class="round-banner">🏆 Round 1 — Main Winners</div>', unsafe_allow_html=True)

    for t in s["draw_order"]:
        if s["winners"][t]:
            render_winner_card(t, s["winners"][t])

    tier = s["current_tier"]
    meta = TIER_META[tier]

    roll = st.empty()
    for _ in range(20):
        roll.markdown(f"<div class='rolling-text'>{random.choice(s['pool'])}</div>", unsafe_allow_html=True)
        time.sleep(0.07)

    winner = random.choice(s["pool"])
    s["pool"].remove(winner)
    s["winners"][tier] = winner
    roll.empty()

    nxt = next_tier_after(tier)
    if nxt:
        s["current_tier"] = nxt
        s["stage"]        = "w_ready"
    else:
        s["stage"] = "w_done"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# WINNER ROUND — all done, prompt to start backup round
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "w_done":
    st.markdown('<div class="round-banner">🏆 Round 1 — Main Winners</div>', unsafe_allow_html=True)

    for t in s["draw_order"]:
        render_winner_card(t, s["winners"][t])

    st.markdown("---")
    st.markdown("<p style='color:#cccccc; font-size:13px; text-align:center;'>All main winners drawn! Proceed to backup draw.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Start Backup Draw →", type="primary", use_container_width=True):
            s["stage"]        = "b_ready"
            s["current_tier"] = "3rd"
            st.rerun()
    with col2:
        if st.button("Reset", use_container_width=True):
            reset(); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# BACKUP ROUND — ready
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "b_ready":
    st.markdown('<div class="round-banner">🔄 Round 2 — Backup Winners</div>', unsafe_allow_html=True)

    # Show main winners
    for t in s["draw_order"]:
        render_winner_card(t, s["winners"][t])

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Show already-drawn backups
    for t in s["draw_order"]:
        if s["backups"][t]:
            render_winner_card(t, s["backups"][t], is_backup=True)

    # Show next backup prize box
    tier = s["current_tier"]
    meta = TIER_META[tier]
    st.markdown(f"""
    <div class="next-prize-box">
      <div class="np-icon">🔄</div>
      <div class="np-info">
        <div class="np-label">Backup — up next</div>
        <div class="np-title">{meta['label']}</div>
        <div class="np-pool">{len(s['pool'])} names remaining in pool</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"Draw Backup {meta['label']} {meta['badge']}", type="primary", use_container_width=True):
            s["stage"] = "b_drawing"
            st.rerun()
    with col2:
        if st.button("Reset", use_container_width=True):
            reset(); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# BACKUP ROUND — drawing
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "b_drawing":
    st.markdown('<div class="round-banner">🔄 Round 2 — Backup Winners</div>', unsafe_allow_html=True)

    for t in s["draw_order"]:
        render_winner_card(t, s["winners"][t])

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    for t in s["draw_order"]:
        if s["backups"][t]:
            render_winner_card(t, s["backups"][t], is_backup=True)

    tier = s["current_tier"]

    roll = st.empty()
    for _ in range(20):
        roll.markdown(f"<div class='rolling-text'>{random.choice(s['pool'])}</div>", unsafe_allow_html=True)
        time.sleep(0.07)

    winner = random.choice(s["pool"])
    s["pool"].remove(winner)
    s["backups"][tier] = winner
    roll.empty()

    nxt = next_tier_after(tier)
    if nxt:
        s["current_tier"] = nxt
        s["stage"]        = "b_ready"
    else:
        s["stage"] = "summary"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "summary":
    st.markdown("<h3 style='text-align:center; color:#ffffff; margin-bottom:1.5rem;'>🎉 Final Results</h3>", unsafe_allow_html=True)

    for t in reversed(s["draw_order"]):  # 1st → 2nd → 3rd
        m      = TIER_META[t]
        winner = s["winners"][t]
        backup = s["backups"][t]
        nc     = NAME_CLS[t]
        st.markdown(f"""
        <div class="summary-card">
          <div class="summary-title">{m['badge']} {m['label']}</div>
          <div class="summary-row">
            <div class="summary-icon">🏆</div>
            <div class="summary-info">
              <div class="summary-prize">Winner</div>
              <div class="summary-name {nc}">{winner}</div>
            </div>
          </div>
          <div class="summary-row">
            <div class="summary-icon">🔄</div>
            <div class="summary-info">
              <div class="summary-prize">Backup</div>
              <div class="summary-backup-name">{backup}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Start a new draw", use_container_width=True):
        reset(); st.rerun()
