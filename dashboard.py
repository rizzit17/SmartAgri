"""SmartAgri's local dashboard. Run: streamlit run dashboard.py."""
import hashlib
import hmac
import io
import json
import math
import os
import pickle
import re
import secrets
from datetime import datetime
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = Path(os.environ.get("SMARTAGRI_DATA_DIR", Path(__file__).resolve().parent))
LATEST_JSON = BASE_DIR / "latest.json"
CSV_FILE = BASE_DIR / "sensor_log.csv"
MODEL_FILE = BASE_DIR / "crop_model.pkl"
USERS_FILE = BASE_DIR / "users.json"
PAGES = ["Overview", "History", "Crops", "Field notes", "Reports", "Account"]
st.set_page_config(page_title="SmartAgri", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

CSS = """<style>
:root { --ink:#293a30; --muted:#647368; --leaf:#3e654e; --paper:#f7f7f0; --line:#dce3d9; --sage:#e9eee3; }
[data-testid="stAppViewContainer"],.stApp { background:var(--paper); color:var(--ink); }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stMainBlockContainer"],.main .block-container { max-width:1160px; padding:2rem 2.5rem 3rem; }
h1,h2,h3 { color:var(--ink); letter-spacing:-.035em; }
h1,h1 span { font-family:Georgia,serif!important; font-weight:400!important; }
h1 { font-size:2.8rem!important; line-height:1.12!important; }
h2 { font-size:1.45rem!important; font-weight:600!important; }
h3 { font-size:1.05rem!important; font-weight:600!important; letter-spacing:-.015em; }
p,label,input,button { font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p { color:var(--muted)!important; }
a { color:var(--leaf); }
[data-testid="stVerticalBlockBorderWrapper"]>div { border-color:var(--line)!important; border-radius:18px!important; background:#fffefa; }
[data-testid="stForm"] { border:0; padding:0; }
[data-testid="stTextInput"] input { color:var(--ink); }
[data-baseweb="input"],[data-baseweb="select"]>div { background:#fffefa; border-color:var(--line); border-radius:10px; }
[data-testid="stTextInput"] label,[data-testid="stSelectbox"] label { font-size:.87rem; }
button[kind="primary"] { background:var(--leaf); color:white; border-color:var(--leaf); border-radius:10px; box-shadow:none; }
button[kind="secondary"],[data-testid="stDownloadButton"] button { background:#fffefa; color:var(--ink); border-color:var(--line); border-radius:10px; }
button:hover { border-color:var(--leaf)!important; }
button:focus-visible,input:focus-visible { outline:3px solid #93b29a!important; outline-offset:3px; }
[data-testid="stMetric"] { padding:1.2rem; border:1px solid var(--line); border-radius:16px; background:#fffefa; }
[data-testid="stMetricLabel"] { color:var(--muted); font-size:.8rem; }
[data-testid="stMetricValue"] { font-family:Georgia,serif; font-size:2rem; font-weight:400; color:var(--ink); }
[data-testid="stRadio"] [role="radiogroup"] { gap:.2rem; flex-wrap:wrap; }
[data-testid="stRadio"] [role="radiogroup"] label { background:transparent; border:1px solid transparent; border-radius:9px; padding:.45rem .85rem; margin:0; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) { background:var(--sage); border-color:#d7dfcf; }
[data-testid="stRadio"] [role="radiogroup"] label>div:first-child { display:none; }
[data-testid="stRadio"] [role="radiogroup"] label:focus-within { outline:2px solid #93b29a; }
[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stChatMessage"] { border-radius:14px; background:#edf1e7; }
[data-testid="stChatInput"] { border-color:var(--line); background:#fffefa; }
[data-baseweb="tab-highlight"] { background:var(--leaf); }
[data-testid="stExpander"] { border-color:var(--line); border-radius:12px; background:#fffefa; }
.brand { display:flex; align-items:center; gap:10px; color:var(--ink); font-weight:650; font-size:1.05rem; }
.brand svg { width:34px; height:34px; }
.eyebrow { color:var(--muted); font-size:.72rem; font-weight:650; letter-spacing:.12em; text-transform:uppercase; margin:0 0 12px; }
.quiet { color:var(--muted); font-size:.94rem; line-height:1.6; }
.hero { background:var(--sage); border:1px solid #dce4d5; border-radius:20px; padding:24px 28px; margin:0 0 16px; }
.hero h1 { margin:8px 0 12px; max-width:600px; font-size:2.3rem!important; }
.hero .quiet { margin-bottom:0; }
.garden { display:block; width:100%; max-width:420px; margin:28px auto 0; }
.auth-intro { padding:38px 28px 0 0; }
.auth-intro h1 { font-size:3.3rem!important; margin:24px 0 18px; max-width:410px; }
.auth-note { border-top:1px solid var(--line); padding-top:18px; color:var(--muted); font-size:.8rem; margin-top:22px; }
.section-intro { color:var(--muted); margin-top:-8px; margin-bottom:24px; font-size:.94rem; }
.crop-card { padding:24px; border:1px solid var(--line); border-radius:16px; background:#fffefa; min-height:156px; }
.crop-number { color:var(--muted); font-size:.76rem; letter-spacing:.07em; }
.crop-name { font-family:Georgia,serif; font-size:1.9rem; margin:12px 0 6px; color:var(--ink); text-transform:capitalize; }
.crop-score { color:var(--leaf); font-size:.9rem; }
.empty { text-align:center; padding:44px 24px; border:1px dashed #cdd8c8; border-radius:18px; background:#f0f3e9; margin:20px 0; }
.empty h3 { font-family:Georgia,serif; font-size:1.7rem!important; font-weight:400!important; }
.pill { display:inline-block; padding:6px 11px; border-radius:20px; background:#e9eee3; color:#3c5946; font-size:.8rem; }
.pill.warn { background:#f4e6da; color:#825238; }
.footer { border-top:1px solid var(--line); margin-top:40px; padding-top:18px; color:var(--muted); font-size:.75rem; display:flex; justify-content:space-between; gap:16px; }
@media(max-width:700px) {
 [data-testid="stMainBlockContainer"],.main .block-container { padding:1.2rem 1rem 2rem; }
 h1 { font-size:2.1rem!important; } .auth-intro { padding:0; } .auth-intro h1 { font-size:2.4rem!important; }
 .garden { max-height:180px; } .hero { padding:24px; } .footer { flex-direction:column; }
 [data-testid="stRadio"] [role="radiogroup"] label { padding:.4rem .6rem; }
}
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none!important; transition:none!important; } }
</style>"""
LOGO = '<svg viewBox="0 0 36 36" fill="none" aria-hidden="true"><rect width="36" height="36" rx="12" fill="#e2e9d9"/><path d="M18 27V15M18 21C10 21 9 16 9 12c7 0 9 3 9 9ZM18 17c0-7 4-9 10-9 0 7-3 10-10 10" stroke="#43674d" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
GARDEN = """<svg class="garden" viewBox="0 0 430 230" fill="none" role="img" aria-label="Three small plants growing in terracotta pots">
<ellipse cx="217" cy="204" rx="167" ry="12" fill="#e6eadf"/><circle cx="344" cy="44" r="23" fill="#ecd8a9"/><path d="M65 203h310" stroke="#c3ceb9" stroke-width="2"/>
<path d="M85 151h64l-8 47H93z" fill="#c7896c"/><path d="M82 148h70v11H82z" fill="#d29c7d"/>
<path d="M118 148v-49m0 23c-23-2-34-13-34-31 24 0 34 11 34 31Zm0-15c0-23 12-36 35-36-1 23-13 36-35 36Z" stroke="#547554" stroke-width="3" fill="#bbccb0" stroke-linejoin="round"/>
<path d="M187 132h76l-10 66h-56z" fill="#aeba9d"/><path d="M182 127h86v13h-86z" fill="#c2cdb3"/>
<path d="M225 127V57m0 39c-26 0-40-15-40-39 26 0 40 15 40 39Zm0-18c0-29 13-43 38-43 0 26-14 43-38 43Z" stroke="#43674d" stroke-width="3" fill="#8fa783" stroke-linejoin="round"/>
<path d="M306 165h54l-7 33h-40z" fill="#d8b18a"/><path d="M303 160h60v11h-60z" fill="#e2c4a2"/>
<path d="M333 160v-36m0 20c-20 0-28-11-28-25 18 0 28 10 28 25Zm0-14c0-17 8-27 26-27 0 17-10 27-26 27Z" stroke="#718662" stroke-width="3" fill="#cad5bb" stroke-linejoin="round"/></svg>"""


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def load_users():
    if not USERS_FILE.exists():
        return {}
    users = read_json(USERS_FILE)
    if users is None:
        raise ValueError("The account file could not be read. Restore users.json before continuing.")
    return users


def save_user(name, record, create=False):
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = USERS_FILE.with_suffix(".lock")
    with lock_path.open("x") as lock:
        try:
            users = load_users()
            if create and any(key.casefold() == name.casefold() for key in users):
                raise ValueError("That username is taken. Try another one.")
            users[name] = record
            temp = USERS_FILE.with_name(f"users.{secrets.token_hex(6)}.tmp")
            try:
                temp.write_text(json.dumps(users, indent=2), encoding="utf-8")
                os.replace(temp, USERS_FILE)
            finally:
                temp.unlink(missing_ok=True)
        finally:
            lock.close()
            lock_path.unlink(missing_ok=True)


def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def password_matches(password, stored):
    if isinstance(stored, str):
        return hmac.compare_digest(password.encode(), stored.encode())
    if not isinstance(stored, dict):
        return False
    try:
        method, rounds, salt, expected = stored["password_hash"].split("$")
        if method != "pbkdf2_sha256" or not 100000 <= int(rounds) <= 1000000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except (KeyError, ValueError, TypeError):
        return False


def brand():
    st.markdown(f'<div class="brand">{LOGO}<span>SmartAgri</span></div>', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="footer"><span>SmartAgri · A little closer to your field.</span><span>Rishit & Siddharth</span></div>', unsafe_allow_html=True)


def login_ui():
    brand()
    left, right = st.columns([1.12, 1], gap="large")
    with left:
        st.markdown('<div class="auth-intro"><div class="eyebrow">Your field, in view</div><h1>A quiet place<br>to check on<br>what’s growing.</h1><p class="quiet">Keep an eye on your sensors, look back at recent readings, and take a few field notes.</p>' + GARDEN + '</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div style="height:30px"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Make yourself at home")
            st.caption("Sign in, or create an account for this installation.")
            mode = st.radio("Account access", ["Sign in", "Create account"], horizontal=True, label_visibility="collapsed")
            try:
                users = load_users()
            except ValueError as exc:
                st.error(str(exc))
                return
            if mode == "Sign in":
                with st.form("sign_in"):
                    username = st.text_input("Username", placeholder="Your username", max_chars=30)
                    password = st.text_input("Password", type="password", placeholder="Your password", max_chars=256)
                    submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                if submitted:
                    name = username.strip()
                    if not name or not password:
                        st.error("Enter your username and password.")
                    elif password_matches(password, users.get(name)):
                        try:
                            if isinstance(users[name], str):
                                save_user(name, {"password_hash": password_hash(password)})
                            st.session_state.update(logged_in=True, user=name, chat=[], page="Overview")
                            st.rerun()
                        except (OSError, ValueError):
                            st.error("Your account could not be updated. Check the account file permissions and try again.")
                    else:
                        st.error("That username and password don’t match. Please try again.")
                with st.expander("Forgot your password?"):
                    st.write("Ask the person who manages this installation to reset your local account. Email recovery isn’t connected.")
            else:
                with st.form("sign_up"):
                    username = st.text_input("Username", placeholder="e.g. rishit", max_chars=30)
                    st.caption("3–30 letters, numbers, underscores or hyphens.")
                    password = st.text_input("Password", type="password", placeholder="At least 8 characters", max_chars=256)
                    confirmation = st.text_input("Confirm password", type="password", max_chars=256)
                    submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
                if submitted:
                    name = username.strip()
                    if not re.fullmatch(r"[A-Za-z0-9_-]{3,30}", name):
                        st.error("Choose a username with 3–30 letters, numbers, underscores or hyphens.")
                    elif any(key.casefold() == name.casefold() for key in users):
                        st.error("That username is taken. Try another one.")
                    elif len(password) < 8:
                        st.error("Use at least 8 characters for your password.")
                    elif password != confirmation:
                        st.error("The passwords don’t match yet.")
                    else:
                        try:
                            save_user(name, {"password_hash": password_hash(password)}, create=True)
                            st.session_state.update(logged_in=True, user=name, chat=[], page="Overview")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                        except OSError:
                            st.error("We couldn’t save that account. Please try again in a moment.")
            st.markdown('<div class="auth-note">Accounts belong to this SmartAgri installation. All signed-in accounts see the same connected field.</div>', unsafe_allow_html=True)
    footer()


def safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def value_text(value, unit=""):
    number = safe_float(value)
    return "—" if number is None else f"{number:.1f}{unit}"


def read_latest():
    data = read_json(LATEST_JSON)
    if not data:
        return {}
    return {**data, "temperature": safe_float(data.get("temperature")), "humidity": safe_float(data.get("humidity")), "soil_moisture": safe_float(data.get("soil_moisture", data.get("moisture")))}


@st.cache_data(ttl=5)
def read_csv():
    try:
        frame = pd.read_csv(CSV_FILE)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", format="mixed")
        for col in frame.columns:
            if col not in ("timestamp", "status", "action", "city"):
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
        return frame.dropna(subset=["timestamp"]).sort_values("timestamp")
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        return pd.DataFrame()


@st.cache_resource
def load_model(modified_ns):
    try:
        with MODEL_FILE.open("rb") as model_file:
            return pickle.load(model_file)
    except (OSError, ValueError, pickle.UnpicklingError, EOFError, ImportError, AttributeError):
        return None


def recommendations(data):
    if not MODEL_FILE.exists():
        return [], "No crop model is available yet."
    model = load_model(MODEL_FILE.stat().st_mtime_ns)
    if model is None:
        return [], "The saved crop model could not be opened."
    values = [data.get("temperature"), data.get("humidity"), data.get("soil_moisture")]
    if any(safe_float(value) is None for value in values):
        return [], "Three complete sensor readings are needed for crop suggestions."
    if not 0 <= values[2] <= 100:
        return [], "Moisture needs to be a calibrated percentage before crop suggestions can be shown."
    try:
        if getattr(model, "n_features_in_", 3) != 3:
            return [], "The saved model expects a different set of inputs."
        inputs = pd.DataFrame([values], columns=list(model.feature_names_in_)) if hasattr(model, "feature_names_in_") else [values]
        scores = model.predict_proba(inputs)[0]
        return [(str(model.classes_[i]), float(scores[i]) * 100) for i in np.argsort(scores)[::-1][:3]], None
    except (ValueError, TypeError, AttributeError):
        return [], "The saved model is incompatible with the current readings."


def alerts_for(data):
    alerts = []
    moisture = safe_float(data.get("soil_moisture"))
    wind = safe_float(data.get("wind_speed"))
    if moisture is not None and not 0 <= moisture <= 100:
        alerts.append(("warning", "Moisture is outside 0–100%. Check the sensor’s units or calibration."))
    elif moisture is not None and moisture < 25:
        alerts.append(("error", "Moisture is below the 25% alert threshold. Check the field and irrigation."))
    elif moisture is not None and moisture < 40:
        alerts.append(("warning", "Moisture is below the 40% notice threshold. Keep an eye on the next readings."))
    if wind is not None and wind > 12:
        alerts.append(("warning", "Wind is above 12 km/h. Check conditions before sprinkler irrigation."))
    return alerts


def empty_state(title, description):
    st.markdown(f'<div class="empty"><h3>{escape(title)}</h3><p class="quiet">{escape(description)}</p></div>', unsafe_allow_html=True)


def page_heading(title, description):
    st.title(title)
    st.markdown(f'<p class="section-intro">{escape(description)}</p>', unsafe_allow_html=True)


def show_history(frame, compact=False):
    if frame.empty:
        empty_state("A little time, a little history", "Your readings will appear here as the collector records them.")
        return
    fields = {"Moisture": "soil_moisture", "Air temperature": "soil_temp", "Air humidity": "soil_humidity", "Outside temperature": "outside_temp", "Wind speed": "wind_speed"}
    choice = st.selectbox("Reading", list(fields), key="overview_metric" if compact else "history_metric")
    column = fields[choice]
    if column not in frame or frame[column].dropna().empty:
        st.info("There are no saved values for this reading yet.")
        return
    subset = frame.tail(60) if compact else frame
    st.line_chart(subset.set_index("timestamp")[[column]].rename(columns={column: choice}), color="#668465", height=220 if compact else 320)


@st.fragment(run_every="5s")
def overview():
    data = read_latest()
    username = escape(st.session_state["user"])
    st.markdown(f'<div class="hero"><div class="eyebrow">Field overview</div><h1>Good to see you, {username}.</h1><p class="quiet">A small check-in with your field.</p></div>', unsafe_allow_html=True)
    if not data:
        empty_state("Waiting for the first reading", "Your dashboard is ready. Once the collector receives a message, your sensors will appear here.")
        with st.expander("Connect your sensors"):
            st.write("Start collector.py with your MQTT settings, then start the sensor publisher. This page checks for new readings every five seconds.")
        return
    try:
        changed = datetime.fromtimestamp(LATEST_JSON.stat().st_mtime)
        age = (datetime.now() - changed).total_seconds()
        label = "Recent file update" if age < 30 else "No recent file update"
        css = "pill" if age < 30 else "pill warn"
        st.markdown(f'<span class="{css}">{label}</span>', unsafe_allow_html=True)
        st.caption(f"File updated {changed:%d %b, %H:%M:%S} · File time does not confirm when the sensor measured the reading.")
    except OSError:
        st.caption("Waiting for the next collector update.")
    for col, label, value, unit in zip(st.columns(3), ["Air temperature", "Air humidity", "Soil moisture"], [data.get("temperature"), data.get("humidity"), data.get("soil_moisture")], [" °C", " %", " %"]):
        col.metric(label, value_text(value, unit))
    st.write("")
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Worth a look")
            alerts = alerts_for(data)
            if alerts:
                for level, text in alerts:
                    getattr(st, level)(text)
            elif any(data.get(k) is None for k in ["temperature", "humidity", "soil_moisture"]):
                st.info("Some sensor readings are missing. Check the next collector update.")
            else:
                st.write("No moisture or wind alerts right now.")
                st.caption("These are prototype thresholds, not an assessment of crop health.")
            status = str(data.get("status", "Not reported")).replace("_", " ").capitalize()
            st.caption(f"Device status: {status} · Device action: {str(data.get('action') or 'Not reported')}")
    with right:
        with st.container(border=True):
            st.subheader("Outside today")
            st.write(str(data.get("city") or "Location not set"))
            st.write(f"Temperature · {value_text(data.get('outside_temp'), ' °C')}")
            st.write(f"Wind · {value_text(data.get('wind_speed'), ' km/h')}")
            st.caption("Latest weather supplied by the collector.")
    st.subheader("Recently in your field")
    show_history(read_csv(), compact=True)


def history_page():
    page_heading("A look back", "Browse the readings your collector has saved.")
    frame = read_csv()
    if frame.empty:
        empty_state("Nothing recorded just yet", "Leave the collector running to start a history of your field.")
        return
    start, end = frame.timestamp.min().date(), frame.timestamp.max().date()
    dates = st.date_input("Date range", value=(start, end), min_value=start, max_value=end)
    if len(dates) != 2:
        st.info("Choose an end date to complete your range.")
        return
    filtered = frame[(frame.timestamp.dt.date >= dates[0]) & (frame.timestamp.dt.date <= dates[1])]
    if filtered.empty:
        empty_state("No readings in this range", "Try a wider date range.")
        return
    st.caption(f"{len(filtered):,} records · {dates[0]:%d %b %Y} to {dates[1]:%d %b %Y}")
    with st.container(border=True):
        show_history(filtered)
    with st.expander("View recorded values"):
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("Download these readings", filtered.to_csv(index=False).encode(), "field_readings.csv", "text/csv")


def crops_page():
    page_heading("What might grow here?", "A short list from your saved crop model, using the current readings.")
    data = read_latest()
    recs, error = recommendations(data)
    if error:
        empty_state("Suggestions aren’t ready yet", error)
        with st.expander("Set up crop suggestions"):
            st.write("Train the three-feature sensor-aligned model. The node needs temperature, humidity and calibrated percentage moisture readings.")
        return
    for col, (name, score), rank in zip(st.columns(len(recs)), recs, range(1, len(recs) + 1)):
        with col:
            st.markdown(f'<div class="crop-card"><div class="crop-number">SUGGESTION {rank:02}</div><div class="crop-name">{escape(name)}</div><div class="crop-score">{score:.1f}% model score</div></div>', unsafe_allow_html=True)
    st.write("")
    st.caption("Model scores are not calibrated confidence or a guarantee that a crop suits your field.")
    with st.container(border=True):
        st.subheader("The readings behind this list")
        st.write(f"Air temperature {value_text(data.get('temperature'), ' °C')} · Humidity {value_text(data.get('humidity'), '%')} · Moisture {value_text(data.get('soil_moisture'), '%')}")
        st.write("The current model uses a training-data moisture proxy. Check soil nutrients, pH, season and local advice before choosing a crop.")


def bot(question, data, recs):
    q = question.casefold()
    if re.search(r"\b(hi|hello|hey)\b", q):
        return "Hello. I can help you read your moisture, weather and crop suggestions. What would you like to check?"
    if any(word in q for word in ("summary", "snapshot", "overview")) and "weather" not in q:
        return f"Air temperature: **{value_text(data.get('temperature'), ' °C')}**. Humidity: **{value_text(data.get('humidity'), '%')}**. Moisture: **{value_text(data.get('soil_moisture'), '%')}**.\n\n" + ("\n\n".join(text for _, text in alerts_for(data)) or "No moisture or wind alerts in the available readings.")
    if any(word in q for word in ("water", "irrigat", "moisture", "pump", "soil")):
        m = data.get("soil_moisture")
        if m is None:
            return "There isn’t a moisture reading yet. Check the sensor publisher and collector, then try again."
        return f"The latest moisture reading is **{value_text(m, '%')}**.\n\n" + ("\n\n".join(text for _, text in alerts_for(data) if "oisture" in text) or "No moisture threshold alert is active. Check the field before changing irrigation; this reading alone cannot determine how much water a crop needs.")
    if any(word in q for word in ("weather", "wind", "outside", "rain", "forecast")):
        return f"The collector reports outside temperature **{value_text(data.get('outside_temp'), ' °C')}** and wind **{value_text(data.get('wind_speed'), ' km/h')}** for **{str(data.get('city') or 'an unset location')}**. These are the latest saved conditions, not a rain forecast."
    if any(word in q for word in ("crop", "grow", "plant", "seed")):
        return f"The highest model score is for **{recs[0][0]}**, at **{recs[0][1]:.1f}%**. This is a dataset-based suggestion; check soil tests, season and local agronomic advice before planting." if recs else "There isn’t a crop suggestion available yet. The Crops page explains which readings or model file are missing."
    if any(word in q for word in ("temperature", "hot", "cold", "heat")):
        return f"The latest air temperature is **{value_text(data.get('temperature'), ' °C')}**. This sensor measures air, not soil temperature. Crop-specific limits depend on the variety and growth stage."
    if "humid" in q:
        return f"The latest relative humidity is **{value_text(data.get('humidity'), '%')}**. A humidity reading alone cannot diagnose disease or determine an irrigation duration."
    if any(word in q for word in ("alert", "warning", "status")):
        return "\n\n".join(text for _, text in alerts_for(data)) or "There are no moisture or wind threshold alerts in the available readings. Missing values are not evaluated."
    if any(word in q for word in ("fertiliz", "pest", "disease", "harvest", "nutrient", "yield")):
        return "These sensors cannot establish nutrient needs, diagnose pests, or determine harvest readiness. Record what you see in the field and check with a local adviser or a soil test."
    return "Try asking about moisture, temperature, humidity, weather, crop suggestions, or a field summary. I use simple rules and the saved readings; I don’t search the web."


def notes_page():
    page_heading("A few field notes", "Ask a quick question about the readings in front of you.")
    st.caption("A rules-based helper, using saved sensor data.")
    data = read_latest()
    recs, _ = recommendations(data)
    if not st.session_state.get("chat"):
        with st.container(border=True):
            st.subheader("Where would you like to start?")
            for col, question in zip(st.columns(3), ["Check moisture", "Weather summary", "Crop suggestions"]):
                if col.button(question, use_container_width=True):
                    st.session_state.setdefault("chat", []).extend([("user", question), ("assistant", bot(question, data, recs))])
                    st.rerun()
    for role, message in st.session_state.get("chat", []):
        with st.chat_message(role, avatar="user" if role == "user" else "🌱"):
            st.write(message)
    question = st.chat_input("What would you like to check?", max_chars=1000)
    if question:
        st.session_state.setdefault("chat", []).extend([("user", question), ("assistant", bot(question, data, recs))])
        st.rerun()
    if st.session_state.get("chat") and st.button("Clear this conversation"):
        st.session_state.chat = []
        st.rerun()


def generate_pdf(data, recs):
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="FarmTitle", fontName="Times-Roman", fontSize=30, leading=34, textColor=colors.HexColor("#293a30"), spaceAfter=12))
    body = [Paragraph("SmartAgri", styles["FarmTitle"]), Paragraph("Field snapshot", styles["Heading2"]), Paragraph(datetime.now().strftime("Prepared %d %B %Y at %H:%M"), styles["Normal"]), Spacer(1, .6 * cm)]
    rows = [["Reading", "Recorded value"]]
    for label, key, unit in [("Air temperature", "temperature", " C"), ("Air humidity", "humidity", "%"), ("Soil moisture", "soil_moisture", "%"), ("Outside temperature", "outside_temp", " C"), ("Wind", "wind_speed", " km/h")]:
        number = safe_float(data.get(key))
        rows.append([label, "Not available" if number is None else f"{number:.1f}{unit}"])
    for label, key in [("Location", "city"), ("Device status", "status"), ("Device action", "action")]:
        rows.append([label, Paragraph(escape(str(data.get(key) or "Not reported")), styles["Normal"])])
    table = Table(rows, colWidths=[6 * cm, 11 * cm], hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eee3")), ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#293a30")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10), ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#dce3d9")), ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    body += [table, Spacer(1, .7 * cm), Paragraph("Crop suggestions", styles["Heading2"])]
    for name, score in recs:
        body.append(Paragraph(f"{escape(name.title())} - {score:.1f}% model score", styles["Normal"]))
    if not recs:
        body.append(Paragraph("No crop suggestions available for this snapshot.", styles["Normal"]))
    body += [Spacer(1, .5 * cm), Paragraph("Model scores are not calibrated confidence. Prototype thresholds and saved readings do not establish crop health or determine irrigation requirements.", styles["Normal"])]
    document.build(body)
    return buffer.getvalue()


def reports_page():
    page_heading("Keep a copy", "A simple snapshot to take with you or share with your adviser.")
    data = read_latest()
    frame = read_csv()
    with st.container(border=True):
        st.subheader("Field snapshot")
        st.write("Current sensor values, weather and available crop suggestions in one PDF.")
        if not data:
            st.info("A sensor reading is needed before a snapshot can be prepared.")
        elif st.button("Prepare snapshot", type="primary"):
            recs, _ = recommendations(data)
            st.session_state["report_pdf"] = generate_pdf(data, recs)
            st.session_state["report_time"] = datetime.now().strftime("%d %b, %H:%M")
        if st.session_state.get("report_pdf"):
            st.caption(f"Prepared {st.session_state['report_time']}. Prepare again to include newer readings.")
            st.download_button("Download PDF", st.session_state["report_pdf"], "farm_report.pdf", "application/pdf")
    with st.container(border=True):
        st.subheader("Recorded readings")
        st.write("The collector’s history as a CSV, ready to open in a spreadsheet.")
        st.download_button("Download CSV", frame.to_csv(index=False).encode(), "field_readings.csv", "text/csv", disabled=frame.empty)


def sign_out():
    # A callback clears application data before the login screen renders.
    for key in ("logged_in", "user", "chat", "report_pdf", "report_time", "page"):
        st.session_state.pop(key, None)


def account_page():
    page_heading("Your little corner", "Account details for this SmartAgri installation.")
    with st.container(border=True):
        st.subheader(st.session_state["user"])
        st.caption("Local account · Shared field dashboard")
        with st.expander("Change password"):
            with st.form("change_password"):
                current = st.text_input("Current password", type="password", max_chars=256)
                new = st.text_input("New password", type="password", max_chars=256)
                confirmation = st.text_input("Confirm new password", type="password", max_chars=256)
                submitted = st.form_submit_button("Update password")
            if submitted:
                try:
                    users = load_users()
                    if not password_matches(current, users.get(st.session_state["user"])):
                        st.error("Your current password doesn’t match.")
                    elif len(new) < 8:
                        st.error("Use at least 8 characters for your new password.")
                    elif new != confirmation:
                        st.error("The new passwords don’t match.")
                    else:
                        save_user(st.session_state["user"], {"password_hash": password_hash(new)})
                        st.success("Your password has been updated.")
                except (OSError, ValueError):
                    st.error("The password couldn’t be saved. Please try again.")
        st.write("")
        st.button("Sign out", on_click=sign_out)


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    if not st.session_state.get("logged_in"):
        login_ui()
        return
    left, right = st.columns([4, 1])
    with left:
        brand()
    with right:
        st.caption(f"Signed in as {st.session_state['user']}")
    page = st.radio("Navigation", PAGES, horizontal=True, label_visibility="collapsed", key="page")
    st.write("")
    {"Overview": overview, "History": history_page, "Crops": crops_page, "Field notes": notes_page, "Reports": reports_page, "Account": account_page}[page]()
    footer()


if __name__ == "__main__":
    main()
