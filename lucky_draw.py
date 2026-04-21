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
        background: rgba(10, 10, 20, 0.70);
        z-index: 0;
    }}
    [data-testid="stAppViewContainer"] > * {{ position: relative; z-index: 1; }}
    </style>
    """, unsafe_allow_html=True)

# ── File names — edit to match your files ─────────────────────────────────────
BG_FILE   = "background.jpg"   # e.g. "background.png"
LOGO_FILE = "logo.png"         # e.g. "logo.jpg"

if Path(BG_FILE).exists():
    apply_background(BG_FILE)
else:
    st.markdown("<style>.stApp { background: #0d0d14; }</style>", unsafe_allow_html=True)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap');

  /* ── Global white font override ── */
  html, body, [class*="css"],
  p, span, div, label, li, a,
  h1, h2, h3, h4, h5, h6,
  .stMarkdown, .stText,
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] span,
  [data-testid="stMarkdownContainer"] li,
  [data-testid="stText"],
  [data-testid="stWidgetLabel"] p,
  [data-testid="stWidgetLabel"] span,
  [data-testid="stFileUploaderLabel"] p,
  [data-testid="stFileUploaderLabel"] span,
  [data-testid="stFileUploadDropzone"] p,
  [data-testid="stFileUploadDropzone"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] p,
  [data-testid="stFileUploaderDropzoneInstructions"] div,
  .stFileUploader label,
  .stFileUploader p,
  .stSelectbox label,
  .stCheckbox label,
  .stAlert p,
  [data-testid="stAlert"] p,
  [data-testid="stAlert"] span {
    font-family: 'DM Sans', sans-serif !important;
    color: #ffffff !important;
  }

  h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #ffffff !important; }

  /* Success / error box text */
  [data-testid="stAlert"] { background: rgba(22,22,42,0.85) !important; border-radius: 10px !important; }

  /* Dataframe text */
  [data-testid="stDataFrame"] * { color: #ffffff !important; }

  /* Top-right logo */
  .logo-topright {
    position: fixed;
    top: 16px;
    right: 24px;
    z-index: 999;
  }
  .logo-topright img { width: 120px; object-fit: contain; }

  /* File uploader box */
  [data-testid="stFileUploadDropzone"] {
    border: 1.5px dashed #888888 !important;
    border-radius: 12px !important;
    background: rgba(22,22,42,0.75) !important;
  }

  /* Prize tier cards */
  .tier-card {
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
  }
  .tier-gold   { background: rgba(59,45,14,0.88);  border: 1px solid #c9a227; }
  .tier-silver { background: rgba(30,30,40,0.88);  border: 1px solid #8e9db5; }
  .tier-bronze { background: rgba(42,22,16,0.88);  border: 1px solid #a0522d; }

  .tier-label {
    font-size: 11px; font-weight: 500; letter-spacing: .12em;
    text-transform: uppercase; opacity: .75; margin-bottom: 4px;
    color: #ffffff !important;
  }
  .tier-winner {
    font-family: 'Playfair Display', serif !important;
    font-size: 26px; font-weight: 700;
  }
  .tier-gold   .tier-winner { color: #f5c842 !important; }
  .tier-silver .tier-winner { color: #c0cfe0 !important; }
  .tier-bronze .tier-winner { color: #d4825a !important; }

  .tier-badge {
    font-size: 36px;
    position: absolute; right: 1.25rem; top: 50%; transform: translateY(-50%);
    opacity: .18;
  }

  /* Rolling animation text */
  .rolling-text {
    font-family: 'Playfair Display', serif !important;
    font-size: 22px; font-weight: 700;
    color: #ffffff !important;
    animation: pulse 0.4s infinite alternate;
  }
  @keyframes pulse { from { opacity:.4; } to { opacity:1; } }

  hr { border-color: #444466 !important; }

  /* Buttons */
  div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid #666688 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all .18s !important;
  }
  div[data-testid="stButton"] > button:hover {
    border-color: #aaaacc !important;
    color: #ffffff !important;
    background: rgba(28,28,48,0.8) !important;
  }
  div[data-testid="stButton"] > button[kind="primary"] {
    background: #4a3fa5 !important;
    border-color: #6a5fcc !important;
    color: #ffffff !important;
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #5a50be !important;
  }

  /* "Browse files" button inside uploader */
  [data-testid="stFileUploadDropzone"] button {
    color: #ffffff !important;
    border-color: #888888 !important;
  }

  /* Remaining count and muted text */
  .muted { color: #cccccc !important; }
</style>
""", unsafe_allow_html=True)

# ── Logo — top right ───────────────────────────────────────────────────────────
if Path(LOGO_FILE).exists():
    logo_b64 = get_base64(LOGO_FILE)
    ext = Path(LOGO_FILE).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    st.markdown(f"""
    <div class="logo-topright">
      <img src="data:image/{mime};base64,{logo_b64}" alt="Logo">
    </div>
    """, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center; color:#ffffff; margin-bottom:0; padding-top:1rem;'>Belanja & Menang Winner Selection</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#cccccc; margin-top:4px; margin-bottom:2rem;'>Three prizes. One name each. Let fate decide.</p>", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "names": [],
        "pool": [],
        "winners": {"3rd": None, "2nd": None, "1st": None},
        "stage": "upload",
        "draw_order": ["3rd", "2nd", "1st"],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()
s = st.session_state

TIER_META = {
    "3rd": {"label": "3rd Prize", "badge": "🥉", "cls": "tier-bronze"},
    "2nd": {"label": "2nd Prize", "badge": "🥈", "cls": "tier-silver"},
    "1st": {"label": "1st Prize", "badge": "🥇", "cls": "tier-gold"},
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def reset():
    for k in ["names", "pool", "winners", "stage"]:
        del st.session_state[k]
    _init()

def render_winner_card(tier_key, name):
    m = TIER_META[tier_key]
    st.markdown(f"""
    <div class="tier-card {m['cls']}">
      <div class="tier-label">{m['label']}</div>
      <div class="tier-winner">{name}</div>
      <div class="tier-badge">{m['badge']}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Upload stage ───────────────────────────────────────────────────────────────
if s["stage"] == "upload":
    uploaded = st.file_uploader("Drop the name list here", type=["csv"])

    if uploaded:
        try:
            df = pd.read_csv(uploaded, header=0)
            col = df.columns[0]
            names = df[col].dropna().astype(str).str.strip().tolist()
            names = [n for n in names if n]

            if len(names) < 3:
                st.error(f"Need at least 3 participants — only found {len(names)}.")
            else:
                s["names"] = names
                s["pool"] = names.copy()
                st.success(f"✓ Loaded **{len(names)} participants** from column *{col}*")
                st.dataframe(pd.DataFrame(names, columns=["Participant"]), use_container_width=True, height=200)

                if st.button("Start Lucky Draw →", type="primary", use_container_width=True):
                    s["stage"] = "ready"
                    st.rerun()
        except Exception as e:
            st.error(f"Could not read file: {e}")

# ── Ready / Drawing / Done stage ──────────────────────────────────────────────
elif s["stage"] in ("ready", "drawing", "done"):

    drawn_tiers   = [t for t in s["draw_order"] if s["winners"][t] is not None]
    pending_tiers = [t for t in s["draw_order"] if s["winners"][t] is None]

    for t in drawn_tiers:
        render_winner_card(t, s["winners"][t])

    if s["stage"] != "done":
        next_tier = pending_tiers[0]
        meta = TIER_META[next_tier]
        st.markdown("---")
        st.markdown(f"<p style='color:#cccccc; font-size:13px; margin-bottom:.5rem;'>Up next</p>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:#ffffff; margin-top:0;'>{meta['badge']} {meta['label']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#cccccc; font-size:13px;'>{len(s['pool'])} names remaining in pool</p>", unsafe_allow_html=True)

        if s["stage"] == "drawing":
            roll_placeholder = st.empty()
            for _ in range(18):
                roll_placeholder.markdown(
                    f"<div class='rolling-text' style='text-align:center; padding:1rem 0;'>"
                    f"{random.choice(s['pool'])}</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.07)

            winner = random.choice(s["pool"])
            s["pool"].remove(winner)
            s["winners"][next_tier] = winner
            roll_placeholder.empty()

            s["stage"] = "done" if not pending_tiers[1:] else "ready"
            st.rerun()

        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"Draw {meta['label']} {meta['badge']}", type="primary", use_container_width=True):
                    s["stage"] = "drawing"
                    st.rerun()
            with col2:
                if st.button("Reset", use_container_width=True):
                    reset()
                    st.rerun()

    else:
        st.markdown("---")
        st.markdown("<p style='text-align:center; color:#cccccc; font-size:13px;'>All prizes have been drawn. Congratulations to our winners! 🎉</p>", unsafe_allow_html=True)
        if st.button("🔄 Start a new draw", use_container_width=True):
            reset()
            st.rerun()
