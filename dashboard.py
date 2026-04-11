##py -m streamlit run dashboard.py
import streamlit as st
import json, os, time, pickle
import pandas as pd
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)

# ======================================================
# PATHS
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_JSON = os.path.join(BASE_DIR, "latest.json")
CSV_FILE = os.path.join(BASE_DIR, "sensor_log.csv")
MODEL_FILE = os.path.join(BASE_DIR, "crop_model.pkl")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Smart Agriculture Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ======================================================
# CUSTOM CSS — DARK AGRICULTURE THEME (HIGH CONTRAST)
# ======================================================
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary: #0f1a0f;
    --bg-secondary: #162016;
    --bg-card: #1a2b1a;
    --bg-card-hover: #223322;
    --bg-input: #1e2e1e;
    --green-bright: #4caf50;
    --green-vibrant: #66bb6a;
    --green-neon: #76ff03;
    --green-soft: #a5d6a7;
    --yellow-accent: #ffd54f;
    --orange-accent: #ffb74d;
    --red-accent: #ef5350;
    --text-primary: #e8f5e9;
    --text-secondary: #a5d6a7;
    --text-bright: #ffffff;
    --border-color: #2e7d32;
    --border-subtle: #2a3d2a;
    --shadow: rgba(0, 0, 0, 0.4);
    --radius: 16px;
}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"] {
    background: linear-gradient(170deg, #0a130a 0%, #0f1a0f 30%, #121f12 60%, #0d180d 100%) !important;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stHeader"] {background: transparent !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #0a130a 0%, #162016 100%) !important;
}

/* ── ALL Text elements — force light on dark ── */
h1, h2, h3, h4, h5, h6,
p, span, label, div,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stCaptionContainer"],
[data-testid="stText"] {
    color: var(--text-primary) !important;
}

/* ── Title ── */
h1 {
    font-weight: 900 !important;
    letter-spacing: -0.5px !important;
    font-size: 2.4rem !important;
}

/* ── Subheaders ── */
[data-testid="stSubheader"],
h2, h3 {
    color: var(--green-vibrant) !important;
    font-weight: 700 !important;
    font-size: 1.4rem !important;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border-color);
    margin-bottom: 16px !important;
}

h3 {
    font-size: 1.2rem !important;
    border-bottom: none;
}

h4 {
    color: var(--green-soft) !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    padding: 22px 24px !important;
    box-shadow: 0 4px 20px var(--shadow) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 30px rgba(76, 175, 80, 0.15) !important;
    border-color: var(--green-bright) !important;
}

[data-testid="stMetricLabel"] {
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    font-size: 1rem !important;
    letter-spacing: 0.3px !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-bright) !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
    color: white !important;
    border: 1px solid #4caf50 !important;
    border-radius: 12px !important;
    padding: 14px 32px !important;
    font-weight: 700 !important;
    font-size: 1.15rem !important;
    letter-spacing: 0.4px;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 16px rgba(46, 125, 50, 0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(76, 175, 80, 0.4) !important;
    border-color: var(--green-neon) !important;
    background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #e65100 0%, #bf360c 100%) !important;
    color: white !important;
    border: 1px solid #ff6d00 !important;
    border-radius: 12px !important;
    padding: 12px 32px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 16px rgba(230, 81, 0, 0.25) !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(255, 109, 0, 0.35) !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    border-width: 2px !important;
}

/* success alert */
[data-testid="stAlert"][data-baseweb*="notification"] {
    background: rgba(46, 125, 50, 0.15) !important;
}

/* ── Dividers ── */
hr {
    border-color: var(--border-subtle) !important;
    opacity: 0.5;
    margin: 28px 0 !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 2px 12px var(--shadow) !important;
    padding: 16px !important;
}
[data-testid="stChatMessage"] p {
    font-size: 1rem !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    border-color: var(--border-color) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] > div {
    background: var(--bg-input) !important;
    border-radius: 14px !important;
    border: 2px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
}
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--green-bright) !important;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2) !important;
}

/* ── Text inputs (login) ── */
[data-testid="stTextInput"] label {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 1.15rem !important;
}
/* Outer wrapper gets the visible border + clip */
[data-testid="stTextInput"] > div {
    background: var(--bg-input) !important;
    border-radius: 12px !important;
    border: 2px solid var(--border-color) !important;
    overflow: hidden !important;
    position: relative !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stTextInput"] > div:focus-within {
    border-color: var(--green-bright) !important;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2) !important;
}
/* Inner div — no border, just transparent */
[data-testid="stTextInput"] > div > div {
    background: transparent !important;
    border: none !important;
    flex: 1 !important;
}
[data-testid="stTextInput"] > div > div:focus-within {
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] input {
    color: var(--text-bright) !important;
    font-size: 1.1rem !important;
    background: transparent !important;
}
/* ── Eye icon — sibling of inner div, clipped by outer overflow:hidden ── */
[data-testid="stTextInput"] > div > button {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    color: var(--text-secondary) !important;
    padding: 0 12px !important;
    margin: 0 !important;
    min-height: unset !important;
    height: 100% !important;
    width: auto !important;
    min-width: unset !important;
    box-shadow: none !important;
    transform: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}
[data-testid="stTextInput"] > div > button:hover {
    color: var(--green-bright) !important;
    background: transparent !important;
    transform: none !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] > div > button svg {
    width: 18px !important;
    height: 18px !important;
    fill: currentColor !important;
}

/* ── Line chart ── */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
    box-shadow: 0 4px 20px var(--shadow) !important;
}

/* ── Welcome banner ── */
.welcome-banner {
    background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 40%, #33691e 100%);
    border-radius: 20px;
    padding: 36px 40px;
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    border: 1px solid rgba(76, 175, 80, 0.3);
    position: relative;
    overflow: hidden;
}
.welcome-banner::before {
    content: '';
    position: absolute;
    top: -30px;
    right: -30px;
    width: 160px;
    height: 160px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.welcome-banner::after {
    content: '';
    position: absolute;
    bottom: -40px;
    right: 80px;
    width: 100px;
    height: 100px;
    background: rgba(255,255,255,0.03);
    border-radius: 50%;
}
.welcome-banner h1 {
    color: white !important;
    font-size: 2rem !important;
    margin: 0 0 8px 0 !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    border-bottom: none !important;
}
.welcome-banner .greeting {
    font-size: 1.15rem;
    color: #c8e6c9;
    font-weight: 500;
}
.welcome-banner .date {
    font-size: 0.95rem;
    color: #a5d6a7;
    margin-top: 4px;
}

/* ── Recommendation cards ── */
.rec-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 16px 22px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 12px var(--shadow);
}
.rec-card:hover {
    border-color: var(--green-bright);
    background: var(--bg-card-hover);
    transform: translateX(4px);
}
.rec-rank {
    background: linear-gradient(135deg, #2e7d32, #4caf50);
    color: white;
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1rem;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}
.rec-name {
    font-weight: 700;
    color: var(--text-bright);
    font-size: 1.1rem;
    text-transform: capitalize;
}
.rec-pct {
    color: var(--yellow-accent);
    font-size: 1.05rem;
    margin-left: auto;
    font-weight: 700;
}

/* ── Status badges ── */
.status-badge {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 24px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
}
.status-green {
    background: rgba(46, 125, 50, 0.25);
    color: #69f0ae;
    border: 1px solid #4caf50;
}
.status-orange {
    background: rgba(230, 81, 0, 0.2);
    color: #ffb74d;
    border: 1px solid #e65100;
}
.status-red {
    background: rgba(198, 40, 40, 0.2);
    color: #ef5350;
    border: 1px solid #c62828;
}

/* ── Info row ── */
.info-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
}
.info-label {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: 1.05rem;
    min-width: 80px;
}

/* ── Login page ── */
.login-wrapper {
    max-width: 460px;
    margin: 40px auto;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    padding: 48px 40px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.login-icon {
    font-size: 4.5rem;
    text-align: center;
    margin-bottom: 20px;
}
.login-title {
    text-align: center;
    color: var(--green-vibrant) !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    margin-bottom: 8px;
}
.login-subtitle {
    text-align: center;
    color: var(--text-secondary) !important;
    font-size: 1.2rem;
    margin-bottom: 28px;
}

/* ── Footer ── */
.footer-text {
    text-align: center;
    color: var(--text-secondary) !important;
    font-size: 1rem;
    padding: 20px 0 8px 0;
    letter-spacing: 0.2px;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ── Selectbox / other inputs ── */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
}

/* ── Tabs if used ── */
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--green-bright) !important;
    border-bottom-color: var(--green-bright) !important;
}

/* ── Toast ── */
[data-testid="stToast"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--green-bright); }
</style>
""", unsafe_allow_html=True)

# ======================================================
# AUTH SYSTEM
# ======================================================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {"admin": "admin"}  # fallback user
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"admin": "admin"}

def login_ui():
    st.markdown('<div class="login-icon">🌾</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Smart Agriculture</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Sign in to access your farm dashboard</div>', unsafe_allow_html=True)

    users = load_users()

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Username", placeholder="Enter your username")
        p = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

        if st.button("🔓  Sign In", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["user"] = u
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

        st.markdown("""
        <div style="text-align:center; margin-top:32px; color:#a5d6a7; font-size:1rem;">
            Built by <strong>Rishit & Siddharth</strong> • Smart Agriculture IoT
        </div>
        """, unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    login_ui()
    st.stop()

# ======================================================
# LOAD MODEL SAFELY
# ======================================================
@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_FILE):
        return None
    try:
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)
    except:
        return None

model = load_model()

# ======================================================
# SAFE DATA LOADERS
# ======================================================
def read_latest():
    if not os.path.exists(LATEST_JSON):
        return None
    try:
        with open(LATEST_JSON, "r") as f:
            return json.load(f)
    except:
        return None

@st.cache_data(ttl=5)
def read_csv():
    if not os.path.exists(CSV_FILE):
        return None
    try:
        df = pd.read_csv(CSV_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df.dropna(subset=["timestamp"])
    except:
        return None

data = read_latest()

if not data:
    st.warning("⏳ Waiting for live sensor data...")
    st.stop()

# ======================================================
# VALUES
# ======================================================
temp = data.get("temperature")
humidity = data.get("humidity")
moisture = data.get("soil_moisture")
status = data.get("status", "Unknown")
action = data.get("action", "")

# Derive action from status if device didn't send one
if not action or action.strip().lower() in ("unknown", "none", "null", ""):
    _s = status.lower()
    if "water_needed" in _s or "dry" in _s or "low" in _s:
        action = "Irrigate Now"
    elif "too_wet" in _s or "waterlog" in _s or "flood" in _s or "high" in _s:
        action = "Stop Irrigation"
    elif _s in ("ok", "normal", "healthy", "good"):
        action = "No Action Needed"
    else:
        action = "Monitor Sensors"

outside_temp = data.get("outside_temp")
wind = data.get("wind_speed")
city = data.get("city", "Unknown")

def safe_float(x):
    try:
        return float(x)
    except:
        return None

t = safe_float(temp)
h = safe_float(humidity)
m = safe_float(moisture)

# ======================================================
# WELCOME BANNER
# ======================================================
now = datetime.now()
hour = now.hour
greet = "Good Morning ☀️" if hour < 12 else "Good Afternoon 🌤" if hour < 17 else "Good Evening 🌙"

st.markdown(f"""
<div class="welcome-banner">
    <h1>🌱 Smart Agriculture Dashboard</h1>
    <div class="greeting">{greet}, {st.session_state['user'].title()}</div>
    <div class="date">📅  {now.strftime("%d %b %Y")}  •  🕐  {now.strftime("%I:%M:%S %p")}</div>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SMART AI + LOGIC CROP RECOMMENDATION
# ======================================================
st.subheader("🤖 AI Crop Recommendation")

def safe_float(x):
    try:
        return float(x)
    except:
        return None

t = safe_float(temp)
h = safe_float(humidity)
m = safe_float(moisture)

pred = None   # IMPORTANT: define pred globally for rest of app

if model is None:
    st.error("⚠️ ML model not loaded")

elif None in [t, h, m]:
    st.warning("⏳ Waiting for valid sensor data...")

else:
    try:
        X = [[t, h, m]]

        probs = model.predict_proba(X)[0]
        classes = model.classes_

        top_idx = np.argsort(probs)[::-1][:3]

        pred = classes[top_idx[0]]   # ✅ now pred is defined

        st.success(f"🌾  **Best Crop Recommendation:  {pred.upper()}**")

        st.markdown("#### 🏆 Top 3 Recommendations")
        for rank, i in enumerate(top_idx, 1):
            pct = round(probs[i]*100, 1)
            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-rank">{rank}</div>
                <div class="rec-name">{classes[i]}</div>
                <div class="rec-pct">{pct}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Prediction error: {e}")

st.divider()

# ======================================================
# LIVE SENSOR DATA
# ======================================================
st.subheader("📡 Live Sensor Data")

c1, c2, c3 = st.columns(3)
c1.metric("🌡  Soil Temp (°C)", temp)
c2.metric("💧  Humidity (%)", humidity)
c3.metric("🌱  Moisture (%)", moisture)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

s1, s2 = st.columns(2)
with s1:
    badge_cls = "status-green" if status.lower() in ["ok", "normal", "healthy"] else "status-orange"
    st.markdown(f"""
    <div class="info-row">
        <span class="info-label">Status</span>
        <span class="status-badge {badge_cls}">{status}</span>
    </div>
    """, unsafe_allow_html=True)
with s2:
    action_cls = "status-green" if "no" in action.lower() or "none" in action.lower() else "status-orange"
    st.markdown(f"""
    <div class="info-row">
        <span class="info-label">Action</span>
        <span class="status-badge {action_cls}">{action}</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ======================================================
# WEATHER
# ======================================================
st.subheader("🌦  Environmental Context")

w1, w2, w3 = st.columns(3)
w1.metric("🌤  Outside Temp", outside_temp)
w2.metric("💨  Wind Speed", wind)
w3.metric("📍  City", city)
st.divider()

# ======================================================
# SMART ALERTS
# ======================================================
st.subheader("⚠️ Smart Alerts")

alerts = []

try:
    if float(m) < 25:
        alerts.append(("error", "🚨 Soil moisture critically low. Irrigate immediately."))
    elif float(m) < 40:
        alerts.append(("warning", "⚠️ Soil moisture low. Consider irrigation."))

    if safe_float(wind) and float(wind) > 12:
        alerts.append(("warning", "💨 High wind may reduce irrigation efficiency."))

    if not alerts:
        alerts.append(("success", "✅ All environmental conditions look healthy."))
except:
    alerts.append(("info", "⏳ Waiting for valid data..."))

for level, msg in alerts:
    getattr(st, level)(msg)

st.divider()

# ======================================================
# TRENDS
# ======================================================
st.subheader("📈 Historical Trends")

df = read_csv()
if df is not None and len(df) > 0:
    cols = [c for c in ["soil_temp", "soil_moisture", "outside_temp"] if c in df.columns]
    if cols:
        st.line_chart(df.set_index("timestamp")[cols])
    else:
        st.info("CSV found but missing expected columns.")
else:
    st.info("📭 No history yet.")

st.divider()

# ======================================================
# PDF REPORT (PROFESSIONAL)
# ======================================================
def generate_pdf(report_data, pred_crop, top_recs=None):
    path = os.path.join(BASE_DIR, "farm_report.pdf")
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
    )

    # Colors
    clr_green_dark = HexColor("#1b5e20")
    clr_green = HexColor("#2e7d32")
    clr_green_light = HexColor("#e8f5e9")
    clr_white = HexColor("#ffffff")
    clr_text = HexColor("#263238")
    clr_text_sec = HexColor("#546e7a")
    clr_orange = HexColor("#e65100")
    clr_orange_light = HexColor("#fff3e0")
    clr_border = HexColor("#c8e6c9")
    clr_yellow_light = HexColor("#fffde7")

    # ------- Styles -------
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=clr_white,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=HexColor("#c8e6c9"),
        alignment=TA_CENTER,
        spaceAfter=0,
    )
    section_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=clr_green_dark,
        spaceBefore=18,
        spaceAfter=8,
        leftIndent=0,
    )
    label_style = ParagraphStyle(
        "CellLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=clr_text,
    )
    value_style = ParagraphStyle(
        "CellValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=clr_text,
    )
    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=clr_text_sec,
        alignment=TA_CENTER,
    )
    best_crop_style = ParagraphStyle(
        "BestCrop",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=clr_green_dark,
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=6,
    )

    content = []

    # ------- Header Banner -------
    header_data = [[
        Paragraph("🌾  Smart Agriculture Report", title_style),
    ]]
    header_sub = [[
        Paragraph(f"Generated on {now.strftime('%d %B %Y at %I:%M %p')}  •  City: {city}", subtitle_style),
    ]]
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), clr_green_dark),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [8, 8, 0, 0]),
    ]))
    content.append(header_table)

    header_sub_tbl = Table(header_sub, colWidths=[doc.width])
    header_sub_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), clr_green),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [0, 0, 8, 8]),
    ]))
    content.append(header_sub_tbl)
    content.append(Spacer(1, 16))

    # ------- Sensor Data Section -------
    content.append(Paragraph("📡  Sensor Readings", section_style))
    content.append(HRFlowable(width="100%", thickness=1, color=clr_border, spaceAfter=8))

    sensor_data = [
        [Paragraph("<b>Parameter</b>", label_style),
         Paragraph("<b>Value</b>", label_style),
         Paragraph("<b>Unit</b>", label_style)],
        [Paragraph("Soil Temperature", value_style),
         Paragraph(str(temp), value_style),
         Paragraph("°C", value_style)],
        [Paragraph("Humidity", value_style),
         Paragraph(str(humidity), value_style),
         Paragraph("%", value_style)],
        [Paragraph("Soil Moisture", value_style),
         Paragraph(str(moisture), value_style),
         Paragraph("%", value_style)],
    ]
    sensor_tbl = Table(sensor_data, colWidths=[doc.width*0.45, doc.width*0.3, doc.width*0.25])
    sensor_tbl.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), clr_green_dark),
        ("TEXTCOLOR", (0, 0), (-1, 0), clr_white),
        # Alternating rows
        ("BACKGROUND", (0, 1), (-1, 1), clr_green_light),
        ("BACKGROUND", (0, 2), (-1, 2), clr_white),
        ("BACKGROUND", (0, 3), (-1, 3), clr_green_light),
        # Borders
        ("GRID", (0, 0), (-1, -1), 0.5, clr_border),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    content.append(sensor_tbl)
    content.append(Spacer(1, 14))

    # ------- Status & Action -------
    content.append(Paragraph("📋  System Status", section_style))
    content.append(HRFlowable(width="100%", thickness=1, color=clr_border, spaceAfter=8))

    status_data = [
        [Paragraph("<b>Field</b>", label_style),
         Paragraph("<b>Current Value</b>", label_style)],
        [Paragraph("Pump Status", value_style),
         Paragraph(str(status), value_style)],
        [Paragraph("Recommended Action", value_style),
         Paragraph(str(action), value_style)],
    ]
    status_tbl = Table(status_data, colWidths=[doc.width*0.45, doc.width*0.55])
    status_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), clr_green_dark),
        ("TEXTCOLOR", (0, 0), (-1, 0), clr_white),
        ("BACKGROUND", (0, 1), (-1, 1), clr_green_light),
        ("BACKGROUND", (0, 2), (-1, 2), clr_white),
        ("GRID", (0, 0), (-1, -1), 0.5, clr_border),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    content.append(status_tbl)
    content.append(Spacer(1, 14))

    # ------- Weather Section -------
    content.append(Paragraph("🌦  Weather Conditions", section_style))
    content.append(HRFlowable(width="100%", thickness=1, color=clr_border, spaceAfter=8))

    weather_data = [
        [Paragraph("<b>Parameter</b>", label_style),
         Paragraph("<b>Value</b>", label_style)],
        [Paragraph("Outside Temperature", value_style),
         Paragraph(f"{outside_temp} °C", value_style)],
        [Paragraph("Wind Speed", value_style),
         Paragraph(f"{wind} km/h", value_style)],
        [Paragraph("City", value_style),
         Paragraph(str(city), value_style)],
    ]
    weather_tbl = Table(weather_data, colWidths=[doc.width*0.45, doc.width*0.55])
    weather_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), clr_green_dark),
        ("TEXTCOLOR", (0, 0), (-1, 0), clr_white),
        ("BACKGROUND", (0, 1), (-1, 1), clr_green_light),
        ("BACKGROUND", (0, 2), (-1, 2), clr_white),
        ("BACKGROUND", (0, 3), (-1, 3), clr_green_light),
        ("GRID", (0, 0), (-1, -1), 0.5, clr_border),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    content.append(weather_tbl)
    content.append(Spacer(1, 14))

    # ------- Crop Recommendation Section -------
    content.append(Paragraph("🤖  AI Crop Recommendation", section_style))
    content.append(HRFlowable(width="100%", thickness=1, color=clr_border, spaceAfter=8))

    # Best crop highlight box
    best_crop_data = [[
        Paragraph(f"🌾  Best Recommended Crop:  <b>{pred_crop.upper() if pred_crop else 'N/A'}</b>", best_crop_style)
    ]]
    best_tbl = Table(best_crop_data, colWidths=[doc.width])
    best_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), clr_yellow_light),
        ("GRID", (0, 0), (-1, -1), 1, HexColor("#ffd54f")),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
    ]))
    content.append(best_tbl)
    content.append(Spacer(1, 10))

    # Top recommendations table (if available)
    if top_recs:
        rec_header = [
            Paragraph("<b>Rank</b>", label_style),
            Paragraph("<b>Crop</b>", label_style),
            Paragraph("<b>Confidence</b>", label_style),
        ]
        rec_rows = [rec_header]
        for rank, (crop, pct) in enumerate(top_recs, 1):
            rec_rows.append([
                Paragraph(f"#{rank}", value_style),
                Paragraph(str(crop).capitalize(), value_style),
                Paragraph(f"{pct}%", value_style),
            ])

        rec_tbl = Table(rec_rows, colWidths=[doc.width*0.15, doc.width*0.5, doc.width*0.35])
        rec_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), clr_green_dark),
            ("TEXTCOLOR", (0, 0), (-1, 0), clr_white),
            ("BACKGROUND", (0, 1), (-1, 1), clr_green_light),
            ("BACKGROUND", (0, 2), (-1, 2), clr_white),
            ("BACKGROUND", (0, 3), (-1, 3), clr_green_light),
            ("GRID", (0, 0), (-1, -1), 0.5, clr_border),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        content.append(rec_tbl)

    content.append(Spacer(1, 24))

    # ------- Footer -------
    content.append(HRFlowable(width="100%", thickness=1, color=clr_border, spaceAfter=8))
    content.append(Paragraph(
        f"Report generated by Smart Agriculture IoT System  •  Built by Rishit & Siddharth",
        footer_style
    ))
    content.append(Paragraph(
        f"Generated: {now.strftime('%d %B %Y, %I:%M %p')}  •  This is an auto-generated report.",
        footer_style
    ))

    doc.build(content)
    return path

st.subheader("📄 Farm Report")

report = {
    "Temperature": temp,
    "Humidity": humidity,
    "Moisture": moisture,
    "Status": status,
    "Action": action,
    "Outside Temp": outside_temp,
    "Wind": wind,
    "City": city,
    "Recommended Crop": pred if pred else "N/A"
}

# Build top recommendations list for PDF
top_recs_for_pdf = None
if model is not None and None not in [t, h, m]:
    try:
        probs_pdf = model.predict_proba([[t, h, m]])[0]
        classes_pdf = model.classes_
        top_idx_pdf = np.argsort(probs_pdf)[::-1][:3]
        top_recs_for_pdf = [(classes_pdf[i], round(probs_pdf[i]*100, 1)) for i in top_idx_pdf]
    except:
        top_recs_for_pdf = None

if st.button("📥  Generate PDF Report", use_container_width=False):
    path = generate_pdf(report, pred, top_recs_for_pdf)
    with open(path, "rb") as f:
        st.download_button("⬇️  Download Report", f, file_name="farm_report.pdf")

st.divider()

# ======================================================
# CHATBOT
# ======================================================
st.subheader("💬 Smart Farming Assistant")

if "chat" not in st.session_state:
    st.session_state.chat = []

def bot(q):
    q_raw = q.strip()
    q = q_raw.lower()

    m_val = safe_float(moisture)
    t_val = safe_float(temp)
    h_val = safe_float(humidity)
    ot_val = safe_float(outside_temp)
    w_val  = safe_float(wind)

    # ── Greeting ──
    if any(x in q for x in ["hello", "hi", "hey", "good morning", "good evening", "good afternoon"]):
        return (f"👋 Hello! I'm your Smart Farming Assistant for **{city}**.\n\n"
                f"Current snapshot → Moisture: **{moisture}%** | Temp: **{temp}°C** | Humidity: **{humidity}%**\n\n"
                "Ask me about irrigation, crops, weather, soil health, alerts, or farming tips!")

    # ── Help ──
    if any(x in q for x in ["help", "what can you", "commands", "topics", "options"]):
        return ("🌾 I can answer questions about:\n"
                "- **Irrigation** – when & how much to water\n"
                "- **Crop** – best crop recommendation with confidence\n"
                "- **Soil** – soil health, temperature & moisture levels\n"
                "- **Humidity** – air humidity impact on crops\n"
                "- **Weather** – outside temp, wind speed\n"
                "- **Alerts** – current warnings for your farm\n"
                "- **Status / Action** – pump status & recommended action\n"
                "- **Fertilizer** – when & what to apply\n"
                "- **Pest** – pest risk based on conditions\n"
                "- **Harvest** – readiness based on conditions\n"
                "- **Summary** – full farm snapshot\n"
                "- **Tips** – general smart farming advice")

    # ── Summary ──
    if any(x in q for x in ["summary", "overview", "snapshot", "report", "all data", "full"]):
        alerts_list = []
        if m_val is not None and m_val < 25:
            alerts_list.append("🚨 Critically low moisture — irrigate immediately")
        elif m_val is not None and m_val < 40:
            alerts_list.append("⚠️ Low moisture — consider watering soon")
        if h_val is not None and h_val > 85:
            alerts_list.append("⚠️ High humidity — fungal disease risk")
        if t_val is not None and t_val > 38:
            alerts_list.append("🌡️ Soil overheating — mulch recommended")
        if w_val is not None and w_val > 12:
            alerts_list.append("💨 High wind — irrigation efficiency reduced")
        alert_str = "\n".join(alerts_list) if alerts_list else "✅ No active alerts"
        return (f"📊 **Farm Snapshot — {city}**\n\n"
                f"🌱 Soil Moisture: **{moisture}%**\n"
                f"🌡️ Soil Temp: **{temp}°C**\n"
                f"💧 Humidity: **{humidity}%**\n"
                f"🌤️ Outside Temp: **{outside_temp}°C** | Wind: **{wind} km/h**\n"
                f"📋 Status: **{status}** | Action: **{action}**\n"
                f"🌾 Best Crop: **{pred.upper() if pred else 'N/A'}**\n\n"
                f"**Active Alerts:**\n{alert_str}")

    # ── Irrigation / Water ──
    if any(x in q for x in ["irrigat", "water", "pump", "sprinkler", "drip"]):
        if m_val is None:
            return "⏳ Moisture data not available yet. Please check your sensor connection."
        if m_val < 20:
            return (f"🚨 **CRITICAL — Irrigate Immediately!**\n\n"
                    f"Soil moisture is at **{moisture}%**, well below the critical threshold of 25%.\n"
                    f"Plants are under severe stress. Run irrigation for **30–45 minutes** now.\n"
                    f"Check pump status: **{status}**")
        elif m_val < 35:
            return (f"⚠️ **Irrigation Recommended**\n\n"
                    f"Soil moisture is **{moisture}%** (ideal: 40–70%).\n"
                    f"Schedule watering within the next few hours.\n"
                    f"💡 Tip: Water early morning (6–8 AM) to minimise evaporation.\n"
                    f"Current action: **{action}**")
        elif m_val < 55:
            return (f"✅ **Soil moisture is adequate at {moisture}%**\n\n"
                    f"No irrigation needed right now. Monitor every 2–3 hours.\n"
                    f"Ideal range is 40–70% for most crops.")
        elif m_val < 75:
            return (f"💧 **Moisture is good at {moisture}%** — no watering needed.\n\n"
                    f"If it rises above 75%, pause irrigation to avoid waterlogging.")
        else:
            return (f"🛑 **Stop Irrigation — Soil is Oversaturated!**\n\n"
                    f"Moisture is **{moisture}%**, above the safe upper limit of 75%.\n"
                    f"Waterlogged soil can cause root rot. Ensure drainage channels are open.")

    # ── Crop recommendation ──
    if any(x in q for x in ["crop", "plant", "grow", "cultivat", "sow", "seed", "recommend"]):
        if pred:
            return (f"🌾 **Best Crop: {pred.upper()}**\n\n"
                    f"Based on Soil Temp **{temp}°C**, Humidity **{humidity}%**, and Moisture **{moisture}%**, "
                    f"your field conditions best match **{pred}**.\n\n"
                    f"💡 Tips for growing {pred}:\n"
                    f"- Maintain moisture between 40–65%\n"
                    f"- Monitor for pests during high humidity (>80%)\n"
                    f"- Ensure proper drainage if moisture exceeds 70%")
        return "⏳ Crop recommendation not available — waiting for sensor data."

    # ── Soil health / moisture ──
    if any(x in q for x in ["soil", "moisture", "ground", "field", "earth"]):
        if m_val is None:
            return "⏳ Soil moisture data unavailable."
        health = ("🔴 Critical" if m_val < 20 else
                  "🟠 Low" if m_val < 35 else
                  "🟢 Healthy" if m_val < 70 else
                  "🔵 Oversaturated")
        return (f"🌱 **Soil Health Report**\n\n"
                f"Moisture: **{moisture}%** → {health}\n"
                f"Soil Temp: **{temp}°C**\n\n"
                f"{'🚨 Irrigate immediately!' if m_val < 20 else '⚠️ Water soon.' if m_val < 35 else '✅ Soil looks healthy. Keep monitoring.' if m_val < 70 else '🛑 Reduce watering — waterlogging risk.'}\n\n"
                f"💡 Ideal moisture for most crops: **40–65%**")

    # ── Temperature ──
    if any(x in q for x in ["temp", "hot", "cold", "heat", "cool", "degree"]):
        if t_val is None:
            return "⏳ Temperature data unavailable."
        if t_val < 10:
            advice = "🧊 Very cold — frost risk. Cover sensitive crops. Avoid watering at night."
        elif t_val < 18:
            advice = "🌤️ Cool conditions — suitable for wheat, barley, mustard."
        elif t_val < 28:
            advice = "✅ Optimal temperature range for most crops."
        elif t_val < 35:
            advice = "🌡️ Warm — monitor moisture closely. Water more frequently."
        else:
            advice = "🔥 Very hot — at risk of heat stress. Apply mulch & water in the early morning."
        return (f"🌡️ **Temperature Analysis**\n\n"
                f"Soil Temp: **{temp}°C**\n"
                f"Outside Temp: **{outside_temp}°C**\n\n"
                f"{advice}")

    # ── Humidity ──
    if any(x in q for x in ["humid", "moisture in air", "damp", "dry air"]):
        if h_val is None:
            return "⏳ Humidity data unavailable."
        if h_val < 30:
            advice = "⚠️ Very dry air — increase irrigation frequency, consider misting."
        elif h_val < 50:
            advice = "✅ Low to moderate humidity — good for most crops."
        elif h_val < 70:
            advice = "✅ Ideal humidity range — crops should thrive."
        elif h_val < 85:
            advice = "⚠️ High humidity — watch for early signs of fungal disease."
        else:
            advice = "🚨 Very high humidity — high risk of fungal infections (blight, mildew). Improve ventilation."
        return f"💧 **Air Humidity: {humidity}%**\n\n{advice}"

    # ── Weather ──
    if any(x in q for x in ["weather", "wind", "outside", "forecast", "rain", "climate"]):
        wind_advice = ""
        if w_val and w_val > 15:
            wind_advice = "\n⚠️ High wind speed — avoid sprinkler irrigation as water loss increases significantly."
        elif w_val and w_val > 8:
            wind_advice = "\n💡 Moderate wind — drip irrigation preferred over sprinklers."
        return (f"🌦️ **Weather Conditions — {city}**\n\n"
                f"Outside Temp: **{outside_temp}°C**\n"
                f"Wind Speed: **{wind} km/h**\n"
                f"{wind_advice}\n"
                f"💡 Factor weather into your irrigation schedule — hot windy days need more frequent watering.")

    # ── Alerts / Warnings ──
    if any(x in q for x in ["alert", "warning", "danger", "risk", "problem", "issue", "critical"]):
        alerts_list = []
        if m_val is not None and m_val < 25:
            alerts_list.append("🚨 **Critical**: Soil moisture at {moisture}% — irrigate immediately")
        elif m_val is not None and m_val < 40:
            alerts_list.append(f"⚠️ **Warning**: Soil moisture low at {moisture}%")
        if h_val is not None and h_val > 85:
            alerts_list.append(f"⚠️ **Warning**: Humidity at {humidity}% — fungal disease risk")
        if t_val is not None and t_val > 38:
            alerts_list.append(f"🌡️ **Warning**: Soil temp {temp}°C — apply mulch to cool soil")
        if w_val is not None and w_val > 12:
            alerts_list.append(f"💨 **Notice**: Wind at {wind} km/h — use drip irrigation")
        if not alerts_list:
            return "✅ **No active alerts!** All farm conditions are within healthy ranges."
        return "📋 **Current Farm Alerts:**\n\n" + "\n".join(alerts_list)

    # ── Status / Action ──
    if any(x in q for x in ["status", "action", "pump", "system"]):
        return (f"📋 **System Status**\n\n"
                f"Status: **{status}**\n"
                f"Recommended Action: **{action}**\n\n"
                f"Moisture: **{moisture}%** | Soil Temp: **{temp}°C**")

    # ── Fertilizer ──
    if any(x in q for x in ["fertiliz", "nutrient", "npk", "nitrogen", "compost", "manure"]):
        return (f"🧪 **Fertilizer Advice**\n\n"
                f"Current soil temp: **{temp}°C** | Moisture: **{moisture}%**\n\n"
                f"{'⚠️ Soil is too dry for fertilizer — irrigate first, then apply.' if (m_val and m_val < 30) else '✅ Moisture levels are suitable for fertilizer application.'}\n\n"
                f"General tips:\n"
                f"- Apply NPK fertilizer at the start of the growing season\n"
                f"- Use urea (nitrogen) for leafy growth, superphosphate for root development\n"
                f"- Avoid fertilizing during heavy rain or very high wind\n"
                f"- For {pred if pred else 'your crop'}, apply potassium-rich fertilizer during fruiting stage")

    # ── Pest ──
    if any(x in q for x in ["pest", "insect", "bug", "disease", "fungal", "blight", "infection"]):
        risk = "Low"
        tips = []
        if h_val and h_val > 80:
            risk = "High"
            tips.append("💧 High humidity greatly increases fungal disease risk (blight, mildew, rust)")
        if t_val and 20 < t_val < 32:
            tips.append("🌡️ Temperatures in the 20–32°C range are ideal for many pests")
        if m_val and m_val > 75:
            tips.append("🌱 Waterlogged soil increases root rot risk")
        if not tips:
            tips.append("✅ Current conditions are not particularly conducive to pests")
        return (f"🐛 **Pest & Disease Risk: {risk}**\n\n"
                + "\n".join(tips) +
                "\n\n💡 Preventive measures:\n"
                "- Inspect leaves weekly for early signs\n"
                "- Ensure good air circulation between plants\n"
                "- Avoid over-watering to prevent fungal issues")

    # ── Harvest ──
    if any(x in q for x in ["harvest", "ready", "mature", "pick", "yield"]):
        return (f"🌾 **Harvest Readiness Notes**\n\n"
                f"Recommended crop: **{pred.upper() if pred else 'N/A'}**\n\n"
                f"Current soil conditions:\n"
                f"- Moisture: **{moisture}%** {'(reduce before harvest for root crops)' if m_val and m_val > 60 else ''}\n"
                f"- Temp: **{temp}°C**\n\n"
                f"💡 General harvest tips:\n"
                f"- Harvest in the cool morning hours to preserve quality\n"
                f"- Avoid harvesting right after irrigation — let soil dry slightly\n"
                f"- Monitor crop maturity indicators (colour, size, firmness)")

    # ── Tips ──
    if any(x in q for x in ["tip", "advice", "best practice", "suggest", "recommend", "how to"]):
        return ("🌿 **Smart Farming Tips**\n\n"
                "1. 💧 **Water early morning** (6–8 AM) to reduce evaporation\n"
                "2. 🌱 **Maintain moisture 40–65%** for most crops year-round\n"
                "3. 🌡️ **Mulch your soil** during hot weather to retain moisture & cool roots\n"
                "4. 🐛 **Inspect crops weekly** for pest/disease signs — early detection saves yield\n"
                "5. 💨 **Avoid sprinkler irrigation on windy days** — use drip irrigation instead\n"
                "6. 🧪 **Test soil nutrients** every season and adjust fertilizer accordingly\n"
                "7. 📊 **Use your sensor data** — don't water by schedule, water by moisture level\n"
                "8. 🌾 **Rotate crops** each season to maintain soil health and break pest cycles")

    # ── Default ──
    return (f"🤔 I didn't quite catch that. Try asking about:\n\n"
            f"**irrigation** • **crop** • **soil** • **temperature** • **humidity** • "
            f"**weather** • **alerts** • **fertilizer** • **pest** • **harvest** • **tips** • **summary**")


user_msg = st.chat_input("Ask about your farm...")

if user_msg:
    st.session_state.chat.append(("user", user_msg))
    st.session_state.chat.append(("bot", bot(user_msg)))

for role, msg in st.session_state.chat:
    st.chat_message("user" if role == "user" else "assistant").write(msg)

# ======================================================
# FOOTER
# ======================================================
st.divider()
st.markdown("""
<div class="footer-text">
    Built with 💚 by <strong>Rishit, Pratishtha & Siddharth</strong>  •  Smart Agriculture IoT System
</div>
""", unsafe_allow_html=True)

# ======================================================
# AUTO REFRESH
# ======================================================
time.sleep(2)
st.rerun()


