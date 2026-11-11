import streamlit as st
import pandas as pd
import random
import time
import base64
import io
import hmac
import copy
from html import escape
import requests
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Belanja & Menang Winner Selection",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Two-role access control ───────────────────────────────────────────────────
# Access is per browser session. Neither password is stored in GitHub or Supabase.
# This gate runs before displaying the draw or loading participant data.
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
CLIENT_PASSWORD = st.secrets["CLIENT_PASSWORD"]

if not (st.session_state.get("admin_ok", False) or st.session_state.get("client_ok", False)):
    st.markdown("""<style>
        .stApp {background: linear-gradient(135deg,#15265b,#076c98) !important;}
        [data-testid="stHeader"] {background:transparent !important;}
        [data-testid="stSidebar"] {display:none !important;}
        .stApp h1,.stApp h2,.stApp p,.stApp label {color:white !important;}
    </style>""", unsafe_allow_html=True)
    st.title("Belanja & Menang — Secure Access")
    st.write("Sign in to access the Lucky Draw system.")
    role = st.radio("Access type", ["Client — Lucky Draw", "Admin — Manage Event"], horizontal=True)
    with st.form("secure_access_login"):
        supplied = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        expected = CLIENT_PASSWORD if role.startswith("Client") else ADMIN_PASSWORD
        if hmac.compare_digest(supplied, str(expected)):
            if role.startswith("Client"):
                st.session_state.client_ok = True
            else:
                st.session_state.admin_ok = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

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
        pointer-events: none;
    }}
    /* Do not elevate all children above the Streamlit header. */
    </style>
    """, unsafe_allow_html=True)

# ── File names ─────────────────────────────────────────────────────────────────
BG_FILE      = "background.jpg"
LOGO_FILE    = "logo.png"
BACKUP_COUNT = 10   # number of backups drawn per prize in one press

# Premium theme uses CSS gradient; original background.jpg remains untouched.

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap');

  #MainMenu { visibility: hidden; }
  /* Keep Streamlit 1.66.1 native header and sidebar toggle intact.
     Do not hide stToolbar or override stHeader positioning/height. */
  [data-testid="stHeader"] {
    background: transparent !important;
  }
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="stExpandSidebarButton"] {
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
  }
  [data-testid="stSidebarCollapsedControl"] button,
  [data-testid="stExpandSidebarButton"] button {
    color: white !important;
  }
  footer { visibility: hidden; }

  html, body,
  p, label, li, a,
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
  /* Streamlit icons are font ligatures, not normal text. */
  .material-symbols-rounded,
  .material-symbols-outlined,
  .material-icons,
  [data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 24px !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    font-feature-settings: 'liga' !important;
    -webkit-font-feature-settings: 'liga' !important;
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
    border: 1.5px solid #cccccc !important; border-radius: 12px !important;
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

  /* Winner card */
  .tier-card {
    border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 0.75rem;
    display: flex; align-items: center; gap: 16px;
  }
  .tier-gold   { background: rgba(59,45,14,0.92);  border: 1px solid #c9a227; }
  .tier-silver { background: rgba(30,30,40,0.92);  border: 1px solid #8e9db5; }
  .tier-bronze { background: rgba(42,22,16,0.92);  border: 1px solid #a0522d; }
  .tier-icon { font-size: 40px; line-height: 1; flex-shrink: 0; }
  .tier-text { flex: 1; }
  .tier-label {
    font-size: 11px; font-weight: 500; letter-spacing: .12em;
    text-transform: uppercase; opacity: .75; margin-bottom: 3px; color: #ffffff !important;
  }
  .tier-winner { font-family: 'Playfair Display', serif !important; font-size: 24px; font-weight: 700; }

  /* Backup card — shows list of 10 */
  .backup-card {
    background: rgba(10,10,25,0.88); border: 1px solid #333355;
    border-radius: 14px; padding: 1rem 1.5rem; margin-bottom: 0.75rem;
  }
  .backup-card-title {
    font-size: 12px; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; color: #aaaacc !important;
    margin-bottom: 0.75rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid #333355;
  }
  .backup-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 4px 16px;
  }
  .backup-item {
    display: flex; align-items: center; gap: 8px;
    padding: 4px 0; font-size: 14px; color: #ffffff !important;
  }
  .backup-num {
    font-size: 11px; color: #666688 !important;
    min-width: 18px; text-align: right; flex-shrink: 0;
  }

  /* Next prize box */
  .next-prize-box {
    background: rgba(10,10,25,0.80); border: 1px solid #444466;
    border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 14px;
  }
  .next-prize-box .np-icon { font-size: 48px; line-height: 1; flex-shrink: 0; }
  .next-prize-box .np-info { flex: 1; }
  .next-prize-box .np-label { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #aaaacc !important; margin-bottom: 4px; }
  .next-prize-box .np-title { font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: #ffffff !important; }
  .next-prize-box .np-pool  { font-size: 12px; color: #aaaacc !important; margin-top: 4px; }

  .round-banner {
    background: rgba(74,63,165,0.85); border: 1px solid #6a5fcc;
    border-radius: 10px; padding: 0.6rem 1.2rem;
    font-size: 13px; font-weight: 500; color: #ffffff !important;
    display: inline-block; margin-bottom: 1rem;
  }

  /* Rolling animation */
  .rolling-text {
    font-family: 'Playfair Display', serif !important;
    font-size: 26px; font-weight: 700; color: #ffffff !important;
    animation: pulse 0.35s infinite alternate; text-align: center; padding: 1rem 0;
  }
  @keyframes pulse { from { opacity:.3; } to { opacity:1; } }

  /* Summary */
  .summary-card {
    background: rgba(10,10,25,0.88); border: 1px solid #333355;
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
  }
  .summary-title {
    font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700;
    color: #ffffff; margin: 0 0 1rem;
    border-bottom: 1px solid #333355; padding-bottom: 0.75rem;
  }
  .summary-winner-row {
    display: flex; align-items: center; gap: 14px;
    padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.75rem;
  }
  .summary-icon { font-size: 26px; flex-shrink: 0; width: 32px; text-align: center; }
  .summary-prize { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #aaaacc !important; margin-bottom: 2px; }
  .summary-name  { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; }
  .gold-name   { color: #f5c842 !important; }
  .silver-name { color: #c0cfe0 !important; }
  .bronze-name { color: #d4825a !important; }
  .summary-backup-label { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #aaaacc !important; margin-bottom: 0.5rem; }
  .summary-backup-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 16px; }
  .summary-backup-item {
    font-size: 14px; color: #ccccdd !important;
    padding: 3px 0; display: flex; gap: 8px; align-items: center;
  }
  .summary-backup-num { color: #666688 !important; min-width: 18px; font-size: 11px; }

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

  /* Sidebar-only light theme: override global white text without affecting draw. */
  [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3,
  [data-testid="stSidebar"] h4,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] span:not(.material-symbols-rounded):not(.material-symbols-outlined):not(.material-icons),
  [data-testid="stSidebar"] li,
  [data-testid="stSidebar"] .stMarkdown,
  [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #1F2937 !important;
  }
  [data-testid="stSidebar"] input { color: #1F2937 !important; background: #FFFFFF !important; }
  [data-testid="stSidebar"] div[data-testid="stButton"] > button {
    color: #1F2937 !important;
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
  }
  [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    color: #111827 !important;
    background: #E2E8F0 !important;
  }
  [data-testid="stSidebar"] [data-testid="stFileUploader"] {
    color: #1F2937 !important;
  }
  /* Streamlit help tooltips are portalled outside the sidebar. */
  [data-baseweb="tooltip"],
  [role="tooltip"],
  [data-testid="stTooltipContent"] {
    background-color: #F8FAFC !important;
    color: #1F2937 !important;
  }
  [data-baseweb="tooltip"] *,
  [role="tooltip"] *,
  [data-testid="stTooltipContent"] * {
    color: #1F2937 !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Premium royal blue / gold design overrides ─────────────────────────────
st.markdown("""
<style>
.stApp {
 background: radial-gradient(ellipse at 50% 10%, rgba(250,135,25,.25),transparent 39%),
 linear-gradient(145deg,#061b43 0%,#07376b 52%,#05142f 100%) !important;
}
[data-testid="block-container"] {
 max-width: 1320px !important; padding: 1.5rem 2.4rem 5rem !important;
}
/* The campaign hero is a normal image; avoid old fixed-position overlay elements. */
[data-testid="stImage"] img { border-radius: 18px; box-shadow: 0 14px 42px rgba(0,0,0,.24); }
.premium-caption {
 text-align:center; letter-spacing:.24em; color:#ffd67a !important;
 font-size:12px; font-weight:700; margin: 0.4rem 0 1.4rem;
}
.round-banner {
 background: linear-gradient(100deg,#074d9a,#1b286d) !important;
 border: 1px solid #dba952 !important; color:#fff3d3 !important;
 border-radius: 24px !important; padding:.7rem 1.3rem !important;
 box-shadow:0 6px 20px rgba(0,0,0,.2);
}
.next-prize-box {
 background:linear-gradient(110deg,rgba(4,30,75,.97),rgba(9,65,122,.96)) !important;
 border:2px solid #e9b75c !important; border-radius:22px !important;
 box-shadow:0 12px 34px rgba(0,0,0,.3),inset 0 1px rgba(255,255,255,.12);
 padding:1.65rem 2rem !important;
}
.next-prize-box .np-label {color:#f7c979 !important;font-size:13px !important;}
.next-prize-box .np-title {color:#ffdf91 !important;font-family:'DM Sans',sans-serif !important;font-size:clamp(30px,4vw,58px) !important;}
.next-prize-box .np-pool {color:#e0ecff !important;font-size:15px !important;}
.tier-card,.summary-card,.backup-card {
 background:linear-gradient(125deg,rgba(4,24,62,.96),rgba(12,51,101,.93)) !important;
 border:1px solid #cfa456 !important; border-radius:18px !important;
 box-shadow:0 12px 30px rgba(0,0,0,.23);
}
.tier-gold {border-color:#ffd36e !important;}
.tier-silver {border-color:#b6c8e5 !important;}
.tier-bronze {border-color:#e9a66e !important;}
.tier-winner {font-family:'DM Sans',sans-serif !important;font-size:clamp(24px,3vw,38px) !important;}
.backup-card-title,.summary-backup-label {color:#f5d18d !important;}
.backup-num,.summary-backup-num {color:#d5b56e !important;}
/* Main-page primary action only; sidebar controls retain their own light theme. */
[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"] {
 background:linear-gradient(180deg,#ffe49a 0%,#f8b93f 100%) !important;
 color:#072f64 !important;border:2px solid #fff0c2 !important;
 border-radius:16px !important;min-height:64px !important;
 font-size:20px !important;font-weight:800 !important;
 box-shadow:0 8px 26px rgba(255,175,48,.24);
}
[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"] span {color:#072f64 !important;}
[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:hover {
 background:linear-gradient(180deg,#fff2be,#ffd166) !important;
}
[data-testid="stSidebar"] {background:#edf1f7 !important;}
[data-testid="stSidebar"] .stSuccess {background:#dcefe9 !important;}
[data-testid="stSidebar"] [data-testid="stAlert"] p,
[data-testid="stSidebar"] [data-testid="stAlert"] span {color:#163a4a !important;}
/* Preserve Streamlit's native sidebar arrows and icon fonts. */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {visibility:visible !important;opacity:1 !important;}
@media(max-width:850px){[data-testid="block-container"]{padding:1rem 1rem 3rem !important;}.next-prize-box{padding:1rem !important;}}
</style>
""",unsafe_allow_html=True)

# ── Full-screen KV background (no poster widget or extra caption) ───────────
# This background is decorative. Draw controls remain separate interactive widgets.
if Path("lucky_draw_fullscreen_kv.jpg").exists():
    kv_b64 = get_base64("lucky_draw_fullscreen_kv.jpg")
    st.markdown(f"""<style>
    .stApp {{
        background-image: linear-gradient(180deg,rgba(3,18,48,.03) 0%,rgba(3,18,48,.05) 50%,rgba(3,18,48,.70) 90%),url('data:image/jpeg;base64,{kv_b64}') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    [data-testid="stMainBlockContainer"] {{padding-top: min(62vh, 670px) !important;}}
    @media(max-width:850px) {{
       .stApp {{background-position: center center !important;}}
       [data-testid="stMainBlockContainer"] {{padding-top: 54vh !important;}}
    }}
    </style>""",unsafe_allow_html=True)

# ── Main-page notification contrast fix ───────────────────────────────────
st.markdown("""
<style>
[data-testid="stMain"] [data-testid="stAlert"] {
    background-color: #EAF2FF !important;
    border: 1px solid #B8D4F5 !important;
    border-radius: 10px !important;
}
[data-testid="stMain"] [data-testid="stAlert"] p,
[data-testid="stMain"] [data-testid="stAlert"] span,
[data-testid="stMain"] [data-testid="stAlert"] li,
[data-testid="stMain"] [data-testid="stAlert"] [data-testid="stMarkdownContainer"] * {
    color: #17365D !important;
}
[data-testid="stMain"] [data-testid="stAlert"] svg {
    color: #164A86 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Shared event storage (Supabase) ───────────────────────────────────────────
# Secrets are configured in Streamlit Cloud, never committed to GitHub.
SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
API = f"{SUPABASE_URL}/rest/v1/lucky_draw_state"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
           "Content-Type": "application/json"}

def blank_state():
    return {"names": [], "pool": [],
            "winners": {"3rd": None, "2nd": None, "1st": None},
            "backups": {"3rd": [], "2nd": [], "1st": []},
            "stage": "upload", "current_tier": "3rd",
            "draw_order": ["3rd", "2nd", "1st"]}

def load_state():
    response = requests.get(API, headers=HEADERS,
                            params={"id": "eq.1", "select": "version,data"}, timeout=15)
    response.raise_for_status()
    rows = response.json()
    if not rows:
        raise RuntimeError("Missing database row. Run the setup SQL first.")
    return rows[0]["data"], rows[0]["version"]

def save_state(new_data, expected_version):
    st.session_state["draw_animation_active"] = False
    # Optimistic concurrency: only one laptop can update a given version.
    response = requests.patch(API, headers={**HEADERS, "Prefer": "return=representation"},
        params={"id": "eq.1", "version": f"eq.{expected_version}"},
        json={"data": new_data, "version": expected_version + 1}, timeout=20)
    response.raise_for_status()
    if not response.json():
        st.warning("Another user updated the draw. The latest state will now load.")
        st.rerun()
    return True

def commit_and_rerun():
    st.session_state["draw_animation_active"] = False
    save_state(s, version)
    st.rerun()

def reset():
    save_state(blank_state(), version)
    st.rerun()

try:
    s, version = load_state()
except Exception as exc:
    st.error(f"Unable to connect to shared lucky draw storage: {exc}")
    st.stop()

# Separate monthly records live inside the SAME Supabase JSON row as the final draw.
# This preserves the existing database schema and existing grand-final results.
MONTHS = ["September 2026", "October 2026", "November 2026", "December 2026"]

def empty_month():
    return {"entries": [], "pool": [], "winner": None, "backups": [], "stage": "upload"}

s.setdefault("monthly_draws", {})
s.setdefault("active_mode", "Grand Final Draw")
s.setdefault("active_month", MONTHS[0])

# Admin controls remain in the original collapsible sidebar.
admin = st.session_state.get("admin_ok", False)
with st.sidebar:
    if admin:
        st.subheader("Admin Access")
        st.success("Admin logged in")
        if st.button("Logout", key="admin_logout"):
            st.session_state.admin_ok = False
            st.rerun()
    else:
        st.caption("Client access — draw controls only")
        if st.button("Logout", key="client_logout"):
            st.session_state.client_ok = False
            st.rerun()

# Draw mode is shared between laptops, rather than stored in one browser session.
if admin:
    with st.sidebar:
        st.divider()
        st.subheader("Draw Configuration")
        mode_choice = st.selectbox("Draw type", ["Monthly Lucky Draw", "Grand Final Draw"],
            index=0 if s["active_mode"] == "Monthly Lucky Draw" else 1)
        # Campaign month applies only to Monthly Lucky Draw.
        # Keep the previously saved month when Grand Final is selected.
        month_choice = s["active_month"]
        if mode_choice == "Monthly Lucky Draw":
            month_choice = st.selectbox("Campaign month", MONTHS,
                index=MONTHS.index(s["active_month"]) if s["active_month"] in MONTHS else 0)
        if mode_choice != s["active_mode"] or (mode_choice == "Monthly Lucky Draw" and month_choice != s["active_month"]):
            if st.button("Apply Draw Selection", type="primary"):
                s["active_mode"] = mode_choice
                if mode_choice == "Monthly Lucky Draw":
                    s["active_month"] = month_choice
                commit_and_rerun()
        st.caption(f"Active on both laptops: {s['active_mode']}" +
                   (f" — {s['active_month']}" if s['active_mode'] == 'Monthly Lucky Draw' else ''))

monthly_mode = s["active_mode"] == "Monthly Lucky Draw"
active_month = s["active_month"]
month_state = s["monthly_draws"].get(active_month, empty_month())

# Lightweight synchronization: rerun the whole app ONLY when Supabase changes.
# Unlike st_autorefresh, the 2-second timer does not restart the entire page
# while the operator is watching the rolling-name animation.
def begin_draw_animation():
    st.session_state["draw_animation_active"] = True

@st.fragment(run_every="2s")
def watch_shared_draw_state():
    # A fragment refresh is isolated from the main page. Never interrupt a draw.
    if st.session_state.get("draw_animation_active", False):
        return
    try:
        latest_data, latest_version = load_state()
    except requests.RequestException:
        # A temporary network issue should not erase the current draw screen.
        return
    if latest_version != version:
        # Admin uploaded, changed mode, drew, or reset on another laptop.
        st.rerun(scope="app")

watch_shared_draw_state()

# Staff upload is available only in the protected sidebar.
if admin:
    with st.sidebar:
        st.divider()
        st.subheader("Participant Upload")
        if monthly_mode:
            st.caption(f"Upload entries for {active_month}. Other months and the Grand Final will not be affected.")
        else:
            st.caption("Upload a new CSV for the Grand Final. Monthly records will not be affected.")
        uploaded = st.file_uploader("Filtered participant CSV", type=["csv"],
                                    key=f"admin_csv_{s['active_mode']}_{active_month}")
        if uploaded is not None:
            try:
                raw = uploaded.getvalue()
                df = None
                for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                    try:
                        df = pd.read_csv(io.BytesIO(raw), encoding=enc)
                        break
                    except UnicodeError:
                        continue
                if df is None or df.empty:
                    st.error("CSV is empty or unreadable")
                else:
                    col = df.columns[0]
                    names = df[col].dropna().astype(str).str.strip().tolist()
                    names = [name for name in names if name]
                    unique_names = list(dict.fromkeys(names))
                    minimum = (1 + BACKUP_COUNT) if monthly_mode else (3 + 3 * BACKUP_COUNT)
                    if len(unique_names) < minimum:
                        st.error(f"Need at least {minimum} distinct names; found {len(unique_names)}.")
                    else:
                        st.info(f"{len(names):,} valid entries")
                        if st.button("Confirm & Publish Candidate List", type="primary"):
                            if monthly_mode:
                                s["monthly_draws"][active_month] = {
                                    "entries": names.copy(), "pool": names.copy(),
                                    "winner": None, "backups": [], "stage": "ready"
                                }
                            else:
                                # Replace ONLY grand-final data; preserve monthly results and active mode.
                                fresh = blank_state()
                                fresh["names"] = names.copy()
                                fresh["pool"] = names.copy()
                                for key in fresh:
                                    s[key] = fresh[key]
                            commit_and_rerun()
            except Exception as exc:
                st.error(f"CSV upload failed: {exc}")
        if st.button("Reset Current Draw"):
            st.session_state["confirm_reset"] = True
        if st.session_state.get("confirm_reset"):
            target = active_month if monthly_mode else "Grand Final"
            st.warning(f"This will permanently clear the {target} draw only.")
            if st.button("Yes, reset current draw"):
                st.session_state.confirm_reset = False
                if monthly_mode:
                    s["monthly_draws"][active_month] = empty_month()
                else:
                    for key, val in blank_state().items():
                        s[key] = val
                commit_and_rerun()
            if st.button("Cancel reset"):
                st.session_state.confirm_reset = False
                st.rerun()

TIER_META = {
    "3rd": {"label": "3rd Prize", "badge": "🥉", "cls": "tier-bronze", "name_color": "#d4825a"},
    "2nd": {"label": "2nd Prize", "badge": "🥈", "cls": "tier-silver", "name_color": "#c0cfe0"},
    "1st": {"label": "1st Prize", "badge": "🥇", "cls": "tier-gold",   "name_color": "#f5c842"},
}
NAME_CLS = {"3rd": "bronze-name", "2nd": "silver-name", "1st": "gold-name"}


def next_tier_after(tier):
    idx = s["draw_order"].index(tier)
    return s["draw_order"][idx + 1] if idx + 1 < len(s["draw_order"]) else None

def render_winner_card(tier_key, name):
    m = TIER_META[tier_key]
    st.markdown(f"""
    <div class="tier-card {m['cls']}">
      <div class="tier-icon">{m['badge']}</div>
      <div class="tier-text">
        <div class="tier-label">{m['label']}</div>
        <div class="tier-winner" style="color:{m['name_color']} !important;">{escape(str(name))}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_backup_card(tier_key):
    m    = TIER_META[tier_key]
    bkps = s["backups"][tier_key]
    if not bkps:
        return
    items_html = "".join([
        f'<div class="backup-item"><span class="backup-num">{i+1}.</span>{escape(str(name))}</div>'
        for i, name in enumerate(bkps)
    ])
    st.markdown(f"""
    <div class="backup-card">
      <div class="backup-card-title">🔄 Backup List — {m['label']} ({len(bkps)} names)</div>
      <div class="backup-grid">{items_html}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<style>" + '\n/* High-visibility, cinematic lucky-draw rolling display */\n.draw-animation-panel {\n  text-align:center; padding:1.5rem 1rem; margin:1rem 0;\n  background:linear-gradient(120deg,rgba(3,25,66,.97),rgba(9,63,120,.96));\n  border:2px solid #f6c969; border-radius:20px;\n  box-shadow:0 10px 40px rgba(0,0,0,.4);\n}\n.draw-animation-label {font-size:14px;letter-spacing:.18em;color:#ffe39b!important;font-weight:800;}\n.draw-animation-name {font-size:clamp(28px,4vw,56px);font-weight:800;color:white!important;\n  margin:1rem auto;line-height:1.2;overflow-wrap:anywhere;}\n.draw-animation-hint {font-size:14px;color:#d8e9ff!important;}\n.draw-animation-reveal {border-color:#ffe9a5;box-shadow:0 0 35px rgba(255,207,85,.35);}\n.draw-animation-reveal .draw-animation-name {color:#ffe39b!important;}\n.draw-backup-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem 1rem;margin-top:1rem;}\n.draw-backup-name {font-size:clamp(14px,1.5vw,20px);font-weight:600;color:white!important;\n  text-align:left;overflow-wrap:anywhere;}\n@media(max-width:600px){.draw-backup-grid{grid-template-columns:1fr;}}\n' + "</style>", unsafe_allow_html=True)

# Visible rolling animation runs before the shared state is committed.
# The selected winner is determined independently by the existing weighted draw.
def animate_lucky_draw(pool, selected, label="LUCKY DRAW", steps=36):
    if not pool:
        return
    placeholder = st.empty()
    for i in range(steps):
        name = random.choice(pool)
        placeholder.markdown(
            f'<div class="draw-animation-panel">'
            f'<div class="draw-animation-label">{escape(label)}</div>'
            f'<div class="draw-animation-name">{escape(str(name))}</div>'
            f'<div class="draw-animation-hint">Selecting a winner...</div>'
            f'</div>', unsafe_allow_html=True)
        time.sleep(0.045 + (i / max(steps - 1, 1)) ** 2 * 0.12)
    placeholder.markdown(
        f'<div class="draw-animation-panel draw-animation-reveal">'
        f'<div class="draw-animation-label">🏆 SELECTED</div>'
        f'<div class="draw-animation-name">{escape(str(selected))}</div>'
        f'</div>', unsafe_allow_html=True)
    time.sleep(2.0)


def animate_backup_draw(pool, chosen, label="BACKUP WINNERS"):
    # Short rolling preview followed by all ten actual selected names.
    if not pool:
        return
    placeholder = st.empty()
    for i in range(32):
        placeholder.markdown(
            f'<div class="draw-animation-panel">'
            f'<div class="draw-animation-label">{escape(label)}</div>'
            f'<div class="draw-animation-name">{escape(str(random.choice(pool)))}</div>'
            f'<div class="draw-animation-hint">Drawing backup winners...</div>'
            f'</div>', unsafe_allow_html=True)
        time.sleep(0.045 + (i / 31) ** 2 * 0.10)
    names = ''.join(f'<div class="draw-backup-name">{i}. {escape(str(name))}</div>'
                    for i, name in enumerate(chosen, 1))
    placeholder.markdown(
        f'<div class="draw-animation-panel draw-animation-reveal">'
        f'<div class="draw-animation-label">🏆 {escape(label)} SELECTED</div>'
        f'<div class="draw-backup-grid">{names}</div></div>', unsafe_allow_html=True)
    time.sleep(2.5)


# MONTHLY LUCKY DRAW — one winner followed by 10 weighted backup winners.
# Every CSV row is a chance. Once a name is selected, all of its entries are
# removed from this month's remaining pool (not from other months/final draw).
if monthly_mode:
    m = month_state
    st.markdown(f'<div class="round-banner">🏆 Monthly Lucky Draw — {escape(active_month)}</div>',
                unsafe_allow_html=True)
    st.markdown(f"<div class='next-prize-box'><div class='np-icon'>👥</div>"
                f"<div class='np-info'><div class='np-label'>Total Valid Entries</div>"
                f"<div class='np-title'>{len(m['entries']):,}</div>"
                f"</div></div>", unsafe_allow_html=True)

    if m["stage"] == "upload":
        st.info(f"Waiting for Admin to upload the {active_month} participant CSV.")
        st.button("Draw Monthly Winner", type="primary", disabled=True, use_container_width=True)
    else:
        if m["winner"] is not None:
            st.markdown(f'<div class="tier-card tier-gold"><div class="tier-icon">🏆</div>'
                        f'<div class="tier-text"><div class="tier-label">Monthly Main Winner</div>'
                        f'<div class="tier-winner">{escape(str(m["winner"]))}</div></div></div>',
                        unsafe_allow_html=True)
        if m["stage"] == "ready":
            if st.button("Draw Monthly Winner 🏆", type="primary", use_container_width=True, on_click=begin_draw_animation):
                picked = random.choice(m["pool"])
                animate_lucky_draw(m["pool"], picked, f"{active_month} — MONTHLY WINNER")
                m["winner"] = picked
                m["pool"] = [name for name in m["pool"] if name != picked]
                m["stage"] = "backup_ready"
                s["monthly_draws"][active_month] = m
                commit_and_rerun()
        elif m["stage"] == "backup_ready":
            st.markdown(f'<div class="round-banner">🔄 Draw {BACKUP_COUNT} Backup Winners</div>',
                        unsafe_allow_html=True)
            if st.button(f"Draw {BACKUP_COUNT} Backups", type="primary", use_container_width=True, on_click=begin_draw_animation):
                weighted_pool = m["pool"].copy()
                if len(set(weighted_pool)) < BACKUP_COUNT:
                    st.error("Not enough distinct remaining names for the backup draw.")
                else:
                    chosen = []
                    for _ in range(BACKUP_COUNT):
                        picked = random.choice(weighted_pool)
                        chosen.append(picked)
                        weighted_pool = [name for name in weighted_pool if name != picked]
                    animate_backup_draw(m["pool"], chosen, f"{active_month} — BACKUP WINNERS")
                    m["backups"] = chosen
                    m["pool"] = weighted_pool
                    m["stage"] = "complete"
                    s["monthly_draws"][active_month] = m
                    commit_and_rerun()
        elif m["stage"] == "complete":
            st.success(f"{active_month} draw completed. Results saved to Supabase.")
            items = "".join(f'<div class="backup-item"><span class="backup-num">{i}.</span>'
                            f'{escape(str(name))}</div>' for i, name in enumerate(m["backups"], 1))
            st.markdown(f'<div class="backup-card"><div class="backup-card-title">🔄 Backup Winners ({BACKUP_COUNT})</div>'
                        f'<div class="backup-grid">{items}</div></div>', unsafe_allow_html=True)

            # Export uses the same openpyxl dependency as the existing Grand Final export.
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            wb = Workbook()
            ws = wb.active
            ws.title = "Monthly Results"
            ws.append(["Month", "Category", "Position", "Name"])
            ws.append([active_month, "Main Winner", 1, m["winner"]])
            for i, name in enumerate(m["backups"], 1):
                ws.append([active_month, "Backup", i, name])
            for cell in ws[1]:
                cell.fill = PatternFill("solid", fgColor="07376B")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")
            for col, width in {"A": 23, "B": 19, "C": 14, "D": 45}.items():
                ws.column_dimensions[col].width = width
            out = io.BytesIO()
            wb.save(out)
            st.download_button("📥 Export Monthly Results to Excel", out.getvalue(),
                               file_name=f"Belanja_Menang_{active_month.replace(' ', '_')}_Results.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               type="primary", use_container_width=True)

# CLIENT START SCREEN — candidate count updates after staff uploads CSV
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "upload":
    st.markdown('<div class="round-banner">🏆 Belanja & Menang Lucky Draw</div>', unsafe_allow_html=True)
    count = len(s["names"])
    st.markdown(f"<div class='next-prize-box'><div class='np-icon'>👥</div>"
                f"<div class='np-info'><div class='np-label'>Total Eligible Candidates</div>"
                f"<div class='np-title'>{count:,}</div>"
                f"<div class='np-pool'>{'Ready for lucky draw' if count else 'Waiting for participant list...'}</div>"
                f"</div></div>", unsafe_allow_html=True)
    if st.button("Start Lucky Draw →", type="primary", use_container_width=True,
                 disabled=(count == 0)):
        s["stage"] = "w_ready"
        s["current_tier"] = "3rd"
        commit_and_rerun()

# ─────────────────────────────────────────────────────────────────────────────
# WINNER ROUND — ready (wait for button click)
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "w_ready":
    st.markdown('<div class="round-banner">🏆 Round 1 — Main Winners</div>', unsafe_allow_html=True)
    for t in s["draw_order"]:
        if s["winners"][t]:
            render_winner_card(t, s["winners"][t])

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
        if st.button(f"Draw {meta['label']} {meta['badge']}", type="primary", use_container_width=True, on_click=begin_draw_animation):
            
            tier_key = s["current_tier"]
            chosen = random.choice(s["pool"])
            animate_lucky_draw(s["pool"], chosen, f"GRAND FINAL — {meta['label'].upper()}")
            s["pool"] = [n for n in s["pool"] if n != chosen]
            s["winners"][tier_key] = chosen
            nxt = next_tier_after(tier_key)
            s["current_tier"] = nxt if nxt else tier_key
            s["stage"] = "w_ready" if nxt else "w_done"
            commit_and_rerun()
    with col2:
        st.caption(" ")

# ─────────────────────────────────────────────────────────────────────────────
# WINNER ROUND — all 3 winners drawn
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "w_done":
    st.markdown('<div class="round-banner">🏆 Round 1 — Main Winners</div>', unsafe_allow_html=True)
    for t in s["draw_order"]:
        render_winner_card(t, s["winners"][t])

    st.markdown("---")
    st.markdown(f"<p style='color:#cccccc; font-size:13px; text-align:center;'>All main winners drawn! Now draw {BACKUP_COUNT} backups per prize — 1 press per prize.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Start Backup Draw →", type="primary", use_container_width=True):
            s["stage"] = "b_ready"; s["current_tier"] = "3rd"; commit_and_rerun()
    with col2:
        st.caption(" ")

# ─────────────────────────────────────────────────────────────────────────────
# BACKUP ROUND — ready (1 press = 10 backups)
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "b_ready":
    tier = s["current_tier"]
    meta = TIER_META[tier]

    st.markdown('<div class="round-banner">🔄 Round 2 — Backup Winners</div>', unsafe_allow_html=True)

    # Show main winners
    for t in s["draw_order"]:
        render_winner_card(t, s["winners"][t])

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Show already completed backup lists
    for t in s["draw_order"]:
        if t == tier:
            break
        render_backup_card(t)

    # Next backup draw box
    st.markdown(f"""
    <div class="next-prize-box">
      <div class="np-icon">🔄</div>
      <div class="np-info">
        <div class="np-label">Backup — up next</div>
        <div class="np-title">{meta['label']} — {BACKUP_COUNT} names</div>
        <div class="np-pool">{len(s['pool'])} names remaining in pool</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"Draw {BACKUP_COUNT} Backups — {meta['label']} {meta['badge']}", type="primary", use_container_width=True, on_click=begin_draw_animation):
            
            tier_key = s["current_tier"]
            # Weighted selection: each CSV entry is a chance, including repeats.
            # Once a person is selected, remove all their entries so that
            # the same name cannot occupy multiple backup/winner positions.
            weighted_pool = s["pool"].copy()
            chosen = []
            for _ in range(BACKUP_COUNT):
                picked = random.choice(weighted_pool)
                chosen.append(picked)
                weighted_pool = [n for n in weighted_pool if n != picked]
            animate_backup_draw(s["pool"], chosen, f"GRAND FINAL — {meta['label'].upper()} BACKUPS")
            selected = set(chosen)
            s["pool"] = [n for n in s["pool"] if n not in selected]
            s["backups"][tier_key] = chosen
            nxt = next_tier_after(tier_key)
            s["current_tier"] = nxt if nxt else tier_key
            s["stage"] = "b_ready" if nxt else "summary"
            commit_and_rerun()
    with col2:
        st.caption(" ")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY — winners + 10 backups each
# ─────────────────────────────────────────────────────────────────────────────
elif s["stage"] == "summary":
    st.markdown("<h3 style='text-align:center; color:#ffffff; margin-bottom:1.5rem;'>🎉 Final Results</h3>", unsafe_allow_html=True)

    for t in reversed(s["draw_order"]):   # 1st → 2nd → 3rd
        m      = TIER_META[t]
        winner = s["winners"][t]
        bkps   = s["backups"][t]
        nc     = NAME_CLS[t]

        backup_items_html = "".join([
            f'<div class="summary-backup-item"><span class="summary-backup-num">{i+1}.</span>{escape(str(name))}</div>'
            for i, name in enumerate(bkps)
        ])

        st.markdown(f"""
        <div class="summary-card">
          <div class="summary-title">{m['badge']} {m['label']}</div>
          <div class="summary-winner-row">
            <div class="summary-icon">🏆</div>
            <div>
              <div class="summary-prize">Winner</div>
              <div class="summary-name {nc}">{escape(str(winner))}</div>
            </div>
          </div>
          <div class="summary-backup-label">🔄 Backup List ({BACKUP_COUNT} names)</div>
          <div class="summary-backup-grid">{backup_items_html}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Export to Excel ──
    import io as _io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    def build_excel():
        wb = Workbook()
        wb.remove(wb.active)  # remove default sheet

        tier_styles = {
            "1st": {"title": "1st Prize 🥇", "header_fill": "B8860B", "winner_fill": "FFF3CD", "backup_fill": "FFFDE7"},
            "2nd": {"title": "2nd Prize 🥈", "header_fill": "4A6B8A", "winner_fill": "E8F0F7", "backup_fill": "F0F6FF"},
            "3rd": {"title": "3rd Prize 🥉", "header_fill": "7B4A2D", "winner_fill": "F7EDE8", "backup_fill": "FFF5F0"},
        }

        thin = Side(style="thin", color="CCCCCC")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for t in reversed(s["draw_order"]):  # 1st → 2nd → 3rd
            m      = TIER_META[t]
            style  = tier_styles[t]
            winner = s["winners"][t]
            bkps   = s["backups"][t]

            ws = wb.create_sheet(title=style["title"])
            ws.column_dimensions["A"].width = 8
            ws.column_dimensions["B"].width = 45

            # ── Title row ──
            ws.merge_cells("A1:B1")
            title_cell = ws["A1"]
            title_cell.value = style["title"]
            title_cell.font      = Font(bold=True, size=14, color="FFFFFF")
            title_cell.fill      = PatternFill("solid", fgColor=style["header_fill"])
            title_cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[1].height = 30

            # ── Winner section header ──
            ws.merge_cells("A2:B2")
            wh = ws["A2"]
            wh.value     = "🏆  WINNER"
            wh.font      = Font(bold=True, size=11, color="FFFFFF")
            wh.fill      = PatternFill("solid", fgColor="333355")
            wh.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            ws.row_dimensions[2].height = 22

            # Winner name row
            ws["A3"].value = "1"
            ws["A3"].font      = Font(color="888888", size=10)
            ws["A3"].alignment = Alignment(horizontal="center", vertical="center")
            ws["A3"].fill      = PatternFill("solid", fgColor=style["winner_fill"])
            ws["A3"].border    = border

            ws["B3"].value     = winner
            ws["B3"].font      = Font(bold=True, size=12)
            ws["B3"].alignment = Alignment(vertical="center", indent=1)
            ws["B3"].fill      = PatternFill("solid", fgColor=style["winner_fill"])
            ws["B3"].border    = border
            ws.row_dimensions[3].height = 22

            # ── Blank spacer ──
            ws.row_dimensions[4].height = 8

            # ── Backup section header ──
            ws.merge_cells("A5:B5")
            bh = ws["A5"]
            bh.value     = f"🔄  BACKUP LIST  ({len(bkps)} names)"
            bh.font      = Font(bold=True, size=11, color="FFFFFF")
            bh.fill      = PatternFill("solid", fgColor="333355")
            bh.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            ws.row_dimensions[5].height = 22

            # Backup name rows
            for i, name in enumerate(bkps):
                row = 6 + i
                ws[f"A{row}"].value     = str(i + 1)
                ws[f"A{row}"].font      = Font(color="888888", size=10)
                ws[f"A{row}"].alignment = Alignment(horizontal="center", vertical="center")
                ws[f"A{row}"].fill      = PatternFill("solid", fgColor=style["backup_fill"])
                ws[f"A{row}"].border    = border

                ws[f"B{row}"].value     = name
                ws[f"B{row}"].font      = Font(size=11)
                ws[f"B{row}"].alignment = Alignment(vertical="center", indent=1)
                ws[f"B{row}"].fill      = PatternFill("solid", fgColor=style["backup_fill"])
                ws[f"B{row}"].border    = border
                ws.row_dimensions[row].height = 20

        # ── Summary sheet ──
        ws_sum = wb.create_sheet(title="Summary", index=0)
        ws_sum.column_dimensions["A"].width = 12
        ws_sum.column_dimensions["B"].width = 40
        ws_sum.column_dimensions["C"].width = 10
        ws_sum.column_dimensions["D"].width = 40

        ws_sum.merge_cells("A1:D1")
        hdr = ws_sum["A1"]
        hdr.value     = "Belanja & Menang — Winner Selection Results"
        hdr.font      = Font(bold=True, size=14, color="FFFFFF")
        hdr.fill      = PatternFill("solid", fgColor="4a3fa5")
        hdr.alignment = Alignment(horizontal="center", vertical="center")
        ws_sum.row_dimensions[1].height = 32

        headers = ["Prize", "Winner", "Backup #", "Backup Name"]
        fills   = ["D9D9D9"] * 4
        for col_idx, (h, f) in enumerate(zip(headers, fills), 1):
            c = ws_sum.cell(row=2, column=col_idx)
            c.value     = h
            c.font      = Font(bold=True, size=10)
            c.fill      = PatternFill("solid", fgColor="333355")
            c.font      = Font(bold=True, color="FFFFFF")
            c.alignment = Alignment(horizontal="center", vertical="center", indent=1)
            c.border    = border
        ws_sum.row_dimensions[2].height = 20

        current_row = 3
        for t in reversed(s["draw_order"]):
            m      = TIER_META[t]
            winner = s["winners"][t]
            bkps   = s["backups"][t]
            style  = tier_styles[t]
            start  = current_row

            # Winner row
            ws_sum.cell(row=current_row, column=1).value     = m["label"]
            ws_sum.cell(row=current_row, column=1).font      = Font(bold=True)
            ws_sum.cell(row=current_row, column=1).fill      = PatternFill("solid", fgColor=style["winner_fill"])
            ws_sum.cell(row=current_row, column=1).border    = border
            ws_sum.cell(row=current_row, column=1).alignment = Alignment(horizontal="center", vertical="center")

            ws_sum.cell(row=current_row, column=2).value     = winner
            ws_sum.cell(row=current_row, column=2).font      = Font(bold=True)
            ws_sum.cell(row=current_row, column=2).fill      = PatternFill("solid", fgColor=style["winner_fill"])
            ws_sum.cell(row=current_row, column=2).border    = border
            ws_sum.cell(row=current_row, column=2).alignment = Alignment(vertical="center", indent=1)

            ws_sum.cell(row=current_row, column=3).fill   = PatternFill("solid", fgColor=style["winner_fill"])
            ws_sum.cell(row=current_row, column=3).border = border
            ws_sum.cell(row=current_row, column=4).fill   = PatternFill("solid", fgColor=style["winner_fill"])
            ws_sum.cell(row=current_row, column=4).border = border
            ws_sum.row_dimensions[current_row].height = 20
            current_row += 1

            # Backup rows
            for i, name in enumerate(bkps):
                ws_sum.cell(row=current_row, column=1).fill   = PatternFill("solid", fgColor=style["backup_fill"])
                ws_sum.cell(row=current_row, column=1).border = border
                ws_sum.cell(row=current_row, column=2).fill   = PatternFill("solid", fgColor=style["backup_fill"])
                ws_sum.cell(row=current_row, column=2).border = border

                ws_sum.cell(row=current_row, column=3).value     = str(i + 1)
                ws_sum.cell(row=current_row, column=3).font      = Font(color="888888", size=10)
                ws_sum.cell(row=current_row, column=3).fill      = PatternFill("solid", fgColor=style["backup_fill"])
                ws_sum.cell(row=current_row, column=3).border    = border
                ws_sum.cell(row=current_row, column=3).alignment = Alignment(horizontal="center")

                ws_sum.cell(row=current_row, column=4).value     = name
                ws_sum.cell(row=current_row, column=4).font      = Font(size=10)
                ws_sum.cell(row=current_row, column=4).fill      = PatternFill("solid", fgColor=style["backup_fill"])
                ws_sum.cell(row=current_row, column=4).border    = border
                ws_sum.cell(row=current_row, column=4).alignment = Alignment(vertical="center", indent=1)
                ws_sum.row_dimensions[current_row].height = 18
                current_row += 1

            # Merge prize label across its rows
            if current_row - start > 1:
                ws_sum.merge_cells(f"A{start}:A{current_row-1}")
                ws_sum[f"A{start}"].alignment = Alignment(horizontal="center", vertical="center")

            current_row += 1  # spacer row

        buf = _io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue()

    excel_data = build_excel()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Export Results to Excel",
            data=excel_data,
            file_name="Belanja_Menang_Results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )
    with col2:
        st.caption("Admin can reset the event from the sidebar.")
