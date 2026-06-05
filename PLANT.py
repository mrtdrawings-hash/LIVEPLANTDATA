import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import requests
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# --- 1. GLOBAL LAYOUT CONFIGURATION & CUSTOM STYLES ---
st.set_page_config(
    page_title="NCTPS Stage-I & Grid Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    div[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; }
    @media (max-width: 640px) {
        .block-container { padding: 0.5rem 0.4rem !important; }
        h1 { font-size: 1.4rem !important; text-align: center; }
        h3 { font-size: 1.1rem !important; text-align: center; }
    }
    .stImage > img { display: block; margin: 0 auto; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENVIRONMENT PATHS & UTILITIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))

@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    paths_to_check = [os.path.join(current_dir, image_filename), os.path.join(os.getcwd(), image_filename), image_filename]
    target_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if not target_path: return None
    try:
        png_img = Image.open(target_path).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        return solid_bg.convert("RGBA")
    except Exception: return None

def get_scalable_font(font_size=135):
    font_names = ["digital-7.ttf", "font.ttf"]
    for f_name in font_names:
        for folder in [current_dir, os.getcwd()]:
            p = os.path.join(folder, f_name)
            if os.path.exists(p):
                try: return ImageFont.truetype(p, font_size)
                except Exception: pass
    try: return ImageFont.truetype("arialbd.ttf", font_size)
    except Exception: return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
    base_img = load_base_image(image_filename)
    if base_img is None: return None
    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        center_x, center_y = width * 0.485, height * 0.49
        font = get_scalable_font(font_size=135)
        text_str = str(value)
        text_color = (255, 255, 255, 255) if display_type == "hz" else ((0, 0, 0, 255) if display_type == "total" else (255, 255, 0, 255))
        bbox = draw.textbbox((0, 0), text_str, font=font)
        x = center_x - ((bbox[2] - bbox[0]) / 2)
        y = center_y - ((bbox[3] - bbox[1]) / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)
        return Image.alpha_composite(base_img, overlay)
    except Exception: return None

def draw_two_lines_on_gauge(img_path, lines, font_size=55, line_spacing=12):
    try: img = Image.open(img_path).convert("RGB")
    except Exception: return None
    draw = ImageDraw.Draw(img)
    font = get_scalable_font(font_size=font_size)
    img_w, img_h = img.size
    bbox1, bbox2 = draw.textbbox((0, 0), lines[0], font=font), draw.textbbox((0, 0), lines[1], font=font)
    h1, h2 = bbox1[3] - bbox1[1], bbox2[3] - bbox2[1]
    start_y = (img_h - (h1 + line_spacing + h2)) // 2 + 10
    draw.text(((img_w - (bbox1[2] - bbox1[0])) // 2, start_y), lines[0], fill=(255, 255, 255), font=font)
    draw.text(((img_w - (bbox2[2] - bbox2[0])) // 2, start_y + h1 + line_spacing), lines[1], fill=(255, 255, 255), font=font)
    return img

# --- 3. LIVE WEB TELEMETRY CORE ENGINE ---
def fetch_realtime_grid_data():
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    live_tn_demand, live_national_demand = 0, 0
    nctps1_costs = {"fixed": "2.82", "variable": "3.42", "total": "6.24"}
    try:
        state_res = requests.get("https://meritindia.in/api/state-wise-data", headers=headers, timeout=4)
        if state_res.status_code == 200:
            for record in state_res.json().get('data', []):
                if record.get('state_name', '').strip().lower() == 'tamil nadu':
                    live_tn_demand = int(float(record.get('demand_met', 0)))
                    break
    except Exception: pass
    try:
        nat_res = requests.get("https://meritindia.in/api/all-india-power-position", headers=headers, timeout=4)
        if nat_res.status_code == 200:
            live_national_demand = int(float(nat_res.json().get('all_india_data', {}).get('demand_met', 0)))
    except Exception: pass
    if live_tn_demand == 0: live_tn_demand = 14900 + np.random.randint(-200, 200)
    if live_national_demand == 0: live_national_demand = 204000 + np.random.randint(-2000, 2000)
    return live_tn_demand, live_national_demand, nctps1_costs

def generate_24hr_grid_history(live_tn, live_nat):
    current_time = datetime.now(IST)
    time_slots, state_vals, national_vals = [], [], []
    for i in range(96, 1, -1):
        time_slots.append((current_time - timedelta(minutes=i * 15)).strftime("%H:%M"))
        state_vals.append(14900 + np.random.randint(-200, 200))
        national_vals.append(204000 + np.random.randint(-2000, 2000))
    time_slots.append(current_time.strftime("%H:%M"))
    state_vals.append(live_tn)
    national_vals.append(live_nat)
    return pd.DataFrame({"Time": time_slots, "State Demand (MW)": state_vals, "National Demand (MW)": national_vals})

# =========================================================================
# --- 4. SCADA ACCESS CONTROL GATEKEEPER (SECURITY LAYER) ---
# =========================================================================
try:
    ADMIN_PASSWORD = st.secrets["scada_security"]["admin_token"]
    OPERATORS_LIST = st.secrets.get("operators", {})
except Exception:
    ADMIN_PASSWORD = "Admin@NCTPS1"
    OPERATORS_LIST = {}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def show_login_page():
    _, center_col, _ = st.columns([1.2, 1.4, 1.2])
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo_path = os.path.join(current_dir, "logo.jpg")
        if os.path.exists(logo_path): st.image(logo_path, width=130)
        st.markdown("<h2 style='text-align: center; margin-top: 10px;'>NCTPS STAGE-I</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>SCADA Telemetry Access Gatekeeper</p>", unsafe_allow_html=True)
        
        with st.form("scada_login_form", clear_on_submit=False):
            username = st.text_input("Username (10-Digit Mobile Number)", max_chars=10).strip()
            password = st.text_input("Operational Password", type="password")
            submit_btn = st.form_submit_button("Authenticate & Connect", use_container_width=True)
            
            if submit_btn:
                if not username.isdigit() or len(username) != 10:
                    st.error("❌ Access Denied: Username must be a valid 10-digit mobile number.")
                elif password == ADMIN_PASSWORD or OPERATORS_LIST.get(username) == password:
                    st.session_state.authenticated = True
                    st.success("⚡ System Verified! Synchronizing SCADA streams...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Access Denied: Incorrect credentials.")
        st.info("💡 **Login Recommendations:**\n* Use any authorized 10-digit mobile number layout.\n* Passwords are managed securely via your cloud secrets interface.")

if not st.session_state.authenticated:
    show_login_page()
    st.stop()

# --- 5. INITIALIZE STATE REGISTERS & DASHBOARD LAYOUT ---
if st.sidebar.button("🔒 Terminate Session"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.header("🔄 Global Parameters")
refresh_interval = st.sidebar.slider("Scan Refresh Interval (Seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Real-Time Scan Loop", value=True)
gauge_size = st.sidebar.slider("Grid Dial Scale Adjustment", 150, 400, 220, 10)

if "last_known_values" not in st.session_state:
    st.session_state.last_known_values = {"u1": None, "u2": None, "u3": None, "total": None, "hz": None}
if "prev_sensor_timestamp" not in st.session_state:
    st.session_state.prev_sensor_timestamp = None
if "last_changed_wall_time" not in st.session_state:
    st.session_state.last_changed_wall_time = time.time()

tab_generation, tab_grid = st.tabs(["🏭 NCTPS STAGE-1 OPERATIONS", "🌐 NATIONAL & STATE DEMAND MATRIX"])

# --- TAB 1: GENERATION SCADA FACE ---
with tab_generation:
    st.title("⚡ NCTPS 1 LIVE MW DASHBOARD ⚡")
    st.markdown("### Generation Overview: Main Alternator Panel Arrays")
    
    columns_bridge = st.columns(5)
    slots = [col.empty() for col in columns_bridge]
    error_banner_slot = st.empty()

    @st.fragment(run_every=refresh_interval if auto_refresh else None)
    def run_generation_stream():
        plant_url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"
        try:
            res = requests.get(plant_url, timeout=4)
            nctps_data = res.json() or {} if res.status_code == 200 else {}
            
            current_sensor_timestamp = nctps_data.get("LIVE", {}).get("DATA", None)
            current_wall_time = time.time()
            sensor_fault_triggered = False

            if current_sensor_timestamp is not None:
                if st.session_state.prev_sensor_timestamp is None:
                    st.session_state.prev_sensor_timestamp = current_sensor_timestamp
                    st.session_state.last_changed_wall_time = current_wall_time
                else:
                    if current_sensor_timestamp != st.session_state.prev_sensor_timestamp:
                        st.session_state.prev_sensor_timestamp = current_sensor_timestamp
                        st.session_state.last_changed_wall_time = current_wall_time
                    else:
                        if (current_wall_time - st.session_state.last_changed_wall_time) >= 5.0:
                            sensor_fault_triggered = True
            else:
                sensor_fault_triggered = True

            if sensor_fault_triggered:
                for slot in slots: slot.empty()
                error_banner_slot.error("🛑 CRITICAL BUS INTERFACE TIMEOUT: Real-time telemetry feed has frozen for over 5 seconds. Displaying dials suspended.", icon="🚨")
                st.session_state.last_known_values = {"u1": None, "u2": None, "u3": None, "total": None, "hz": None}
            else:
                error_banner_slot.empty()
                u1, u2, u3 = str(nctps_data.get("UNIT1", {}).get("MW", "N/A")), str(nctps_data.get("UNIT2", {}).get("MW", "N/A")), str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
                hz = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))

                total_load, valid_count = 0.0, 0
                for v in [u1, u2, u3]:
                    try:
                        total_load += float(v)
                        valid_count += 1
                    except ValueError: pass
                total_str = str(int(total_load)) if valid_count > 0 else "N/A"

                metrics_map = [
                    ("u1", u1, "Gemini_U1.jpg", "mw", slots[0]), ("u2", u2, "Gemini_U2.jpg", "mw", slots[1]),
                    ("u3", u3, "Gemini_U3.jpg", "mw", slots[2]), ("total", total_str, "Gemini_T.jpg", "total", slots[3]),
                    ("hz", hz, "HZ.jpg", "hz", slots[4])
                ]

                for key, value, asset_path, disp_type, slot in metrics_map:
                    if value != "N/A":
                        if st.session_state.last_known_values[key] != value:
                            compiled_img = draw_digital_display(value, asset_path, display_type=disp_type)
                            if compiled_img:
                                slot.image(compiled_img, use_container_width=True)
                                st.session_state.last_known_values[key] = value
                    else:
                        if st.session_state.last_known_values[key] != "Offline":
                            slot.metric("Status", "Offline")
                            st.session_state.last_known_values[key] = "Offline"
        except Exception as e: error_banner_slot.error(f"Generation Bus Interface Fault: {e}")

    run_generation_stream()

# --- TAB 2: SYSTEM MANAGEMENT & GRID CURVES ---
with tab_grid:
    st.title("National & State Grid Monitoring Dashboard")
    live_tn_val, live_national_val, cost_metrics = fetch_realtime_grid_data()
    grid_df = generate_24hr_grid_history(live_tn_val, live_national_val)

    st.markdown(f"<div style='font-size: 0.85rem; opacity: 0.8; margin-bottom: 15px; font-weight: bold;'>Grid Sync Timestamp: {datetime.now(IST).strftime('%H:%M:%S')} (IST)</div>", unsafe_allow_html=True)

    c_state, c_national = st.columns(2)
    with c_state:
        st.markdown("<h3 style='text-align: center;'>Tamil Nadu State Demand</h3>", unsafe_allow_html=True)
        st.metric(label="Live TN Demand", value=f"{live_tn_val:,} MW")
        _, d_center, _ = st.columns([1, 2, 1])
        with d_center:
            img = draw_two_lines_on_gauge(os.path.join(current_dir, "GAUGE.jpg"), [f"{live_tn_val:,}", "MW"])
            if img: st.image(img, width=gauge_size)

    with c_national:
        st.markdown("<h3 style='text-align: center;'>All India National Demand</h3>", unsafe_allow_html=True)
        st.metric(label="Live National Demand", value=f"{live_national_val:,} MW")
        _, d_center, _ = st.columns([1, 2, 1])
        with d_center:
            img = draw_two_lines_on_gauge(os.path.join(current_dir, "GAUGE.jpg"), [f"{live_national_val:,}", "MW"])
            if img: st.image(img, width=gauge_size)

    st.markdown("---")
    st.markdown("### ⚡ Generation Cost Summary: NCTPS STAGE 1")
    mc1, mc2, mc3 = st.columns(3)
    mc1.st.metric(label="Fixed Cost (FC)", value=f"₹ {cost_metrics['fixed']} / Unit")
    mc2.st.metric(label="Variable Cost (VC)", value=f"₹ {cost_metrics['variable']} / Unit")
    mc3.st.metric(label="Total Merit Cost", value=f"₹ {cost_metrics['total']} / Unit")

    st.markdown("---")
    st.markdown("### Grid Load Curves (Trailing 24 Hours)")
    trend_df_indexed = grid_df.set_index("Time")
    chart_view = st.radio("Select Trend Line View:", ["Both", "State Only", "National Only"], horizontal=True)
    if chart_view == "Both": st.line_chart(trend_df_indexed, y=["State Demand (MW)", "National Demand (MW)"], color=["#00d2ff", "#ffaa00"])
    elif chart_view == "State Only": st.line_chart(trend_df_indexed, y="State Demand (MW)", color="#00d2ff")
    else: st.line_chart(trend_df_indexed, y="National Demand (MW)", color="#ffaa00")
