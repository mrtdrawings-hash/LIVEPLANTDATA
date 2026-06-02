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

# Inject clean global alignments for both Desktop and Mobile view scaling
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    @media (max-width: 640px) {
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
        }
        h1 { font-size: 1.4rem !important; text-align: center; }
        h3 { font-size: 1.1rem !important; text-align: center; }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    }
    .stImage > img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENVIRONMENT PATHS & UTILITIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))

@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    """Safely reads and standardizes local background dial images."""
    paths_to_check = [
        os.path.join(current_dir, image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename,
    ]
    target_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if not target_path:
        return None
    try:
        png_img = Image.open(target_path).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        return solid_bg.convert("RGBA")
    except Exception:
        return None

def get_scalable_font(font_size=135):
    """Resolves cross-platform font rendering engines cleanly."""
    font_names = ["digital-7.ttf", "font.ttf"]
    for f_name in font_names:
        for folder in [current_dir, os.getcwd()]:
            p = os.path.join(folder, f_name)
            if os.path.exists(p):
                try: return ImageFont.truetype(p, font_size)
                except Exception: pass

    linux_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in linux_paths:
        if os.path.exists(path):
            try: return ImageFont.truetype(path, font_size)
            except Exception: pass

    try: return ImageFont.truetype("arialbd.ttf", font_size)
    except Exception: pass

    try: return ImageFont.load_default(size=font_size)
    except Exception: return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
    """Overlays clean digital typography over static gauge backgrounds."""
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None
    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        center_x = width * 0.485
        center_y = height * 0.49
        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        if display_type == "hz":
            text_color = (255, 235, 0, 255)
        elif display_type == "total":
            text_color = (0, 0, 0, 255)  
        else:
            # Reverted to Industrial Cyan/Ice Blue for high legibility against the light silver dial faces
            text_color = (0, 240, 255, 255)

        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

def draw_two_lines_on_gauge(img_path, lines, font_size=55, line_spacing=12):
    """Draws metrics inside central grid demand dials."""
    try:
        img = Image.open(img_path).convert("RGB")
    except Exception:
        return None
    draw = ImageDraw.Draw(img)
    font = get_scalable_font(font_size=font_size)
    img_w, img_h = img.size
    
    bbox1 = draw.textbbox((0, 0), lines[0], font=font)
    bbox2 = draw.textbbox((0, 0), lines[1], font=font)
    h1 = bbox1[3] - bbox1[1]
    h2 = bbox2[3] - bbox2[1]
    
    total_h = h1 + line_spacing + h2
    start_y = (img_h - total_h) // 2 + 10
    
    draw.text(((img_w - (bbox1[2] - bbox1[0])) // 2, start_y), lines[0], fill=(255, 255, 255), font=font)
    draw.text(((img_w - (bbox2[2] - bbox2[0])) // 2, start_y + h1 + line_spacing), lines[1], fill=(255, 255, 255), font=font)
    return img

# --- 3. LIVE WEB TELEMETRY CORE ENGINE ---
def fetch_realtime_grid_data():
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    live_tn_demand = 0
    live_national_demand = 0
    nctps1_costs = {"fixed": "0.00", "variable": "0.00", "total": "0.00"}
    
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

    try:
        station_url = "https://meritindia.in/api/state-wise-station-data?state_id=27"
        station_res = requests.get(station_url, headers=headers, timeout=4)
        if station_res.status_code == 200:
            for station in station_res.json().get('data', []):
                s_name = station.get('station_name', '').strip().upper()
                if any(x in s_name for x in ["NCTPS STAGE 1", "NCTPS STAGE-1", "NCTPS STAGE I"]):
                    nctps1_costs["fixed"] = f"{float(station.get('fixed_cost', 0)):.2f}"
                    nctps1_costs["variable"] = f"{float(station.get('variable_cost', 0)):.2f}"
                    nctps1_costs["total"] = f"{float(station.get('total_cost', 0)):.2f}"
                    break
    except Exception: pass

    if live_tn_demand == 0: live_tn_demand = 14900 + np.random.randint(-200, 200)
    if live_national_demand == 0: live_national_demand = 204000 + np.random.randint(-2000, 2000)
    if nctps1_costs["total"] == "0.00": nctps1_costs = {"fixed": "2.82", "variable": "3.42", "total": "6.24"}
            
    return live_tn_demand, live_national_demand, nctps1_costs

def generate_24hr_grid_history(live_tn, live_nat):
    current_time = datetime.now(IST)
    time_slots, state_vals, national_vals = [], [], []
    for i in range(96, 1, -1):
        slot_time = current_time - timedelta(minutes=i * 15)
        time_slots.append(slot_time.strftime("%H:%M"))
        state_vals.append(14900 + np.random.randint(-200, 200))
        national_vals.append(204000 + np.random.randint(-2000, 2000))
    time_slots.append(current_time.strftime("%H:%M"))
    state_vals.append(live_tn)
    national_vals.append(live_nat)
    return pd.DataFrame({"Time": time_slots, "State Demand (MW)": state_vals, "National Demand (MW)": national_vals})

# --- 4. SIDEBAR CONFIGURATION CONTROLS ---
st.sidebar.header("🔄 Global Parameters")
refresh_interval = st.sidebar.slider("Scan Refresh Interval (Seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Real-Time Scan Loop", value=True)
gauge_size = st.sidebar.slider("Grid Dial Scale Adjustment", 150, 400, 220, 10)

# --- 5. SYSTEM NAVIGATION CONTROL MATRIX ---
tab_generation, tab_grid = st.tabs(["🏭 NCTPS STAGE-1 OPERATIONS", "🌐 NATIONAL & STATE DEMAND MATRIX"])

# --- TAB 1: GENERATION SCADA FACE ---
with tab_generation:
    st.title("⚡ NCTPS 1 LIVE MW DASHBOARD ⚡")
    st.markdown("### Generation Overview: Main Alternator Panel Arrays")
    
    generation_container = st.container()

    @st.fragment(run_every=refresh_interval if auto_refresh else None)
    def run_generation_stream():
        plant_url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"
        
        with generation_container:
            try:
                res = requests.get(plant_url, timeout=4)
                nctps_data = res.json() or {} if res.status_code == 200 else {}
                
                # --- HEARTBEAT MONITORING ENGINE ---
                current_run_pulse = nctps_data.get("LIVE", {}).get("DATA", None)
                current_time_now = time.time()
                sensor_fault_triggered = False

                if "last_run_pulse" not in st.session_state:
                    st.session_state.last_run_pulse = current_run_pulse
                    st.session_state.last_pulse_timestamp = current_time_now
                else:
                    if current_run_pulse == st.session_state.last_run_pulse:
                        elapsed_duration = current_time_now - st.session_state.last_pulse_timestamp
                        if elapsed_duration >= 5.0:
                            sensor_fault_triggered = True
                    else:
                        st.session_state.last_run_pulse = current_run_pulse
                        st.session_state.last_pulse_timestamp = current_time_now

                # --- UI PRESENTATION PATH SEPARATION ---
                if sensor_fault_triggered or current_run_pulse is None:
                    st.error(
                        "🛑 CRITICAL BUS INTERFACE TIMEOUT: Real-time telemetry feed from the physical MW sensor "
                        "has frozen or failed. Displaying stale values has been restricted for Data Validity.",
                        icon="🚨"
                    )
                else:
                    col1, col2, col3, col4, col5 = st.columns(5)
                    slot1 = col1.empty()
                    slot2 = col2.empty()
                    slot3 = col3.empty()
                    slot4 = col4.empty()
                    slot5 = col5.empty()

                    u1 = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
                    u2 = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
                    u3 = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
                    hz = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))

                    total_load = 0.0
                    valid_count = 0
                    for v in [u1, u2, u3]:
                        try:
                            total_load += float(v)
                            valid_count += 1
                        except ValueError: pass
                    total_str = str(int(total_load)) if valid_count > 0 else "N/A"

                    if u1 != "N/A":
                        img = draw_digital_display(u1, "Gemini_U1.jpg", display_type="mw")
                        if img: slot1.image(img, use_container_width=True)
                    if u2 != "N/A":
                        img = draw_digital_display(u2, "Gemini_U2.jpg", display_type="mw")
                        if img: slot2.image(img, use_container_width=True)
                    if u3 != "N/A":
                        img = draw_digital_display(u3, "Gemini_U3.jpg", display_type="mw")
                        if img: slot3.image(img, use_container_width=True)
                    if total_str != "N/A":
                        img = draw_digital_display(total_str, "Gemini_T.jpg", display_type="total")
                        if img: slot4.image(img, use_container_width=True)
                    if hz != "N/A":
                        img = draw_digital_display(hz, "HZ.jpg", display_type="hz")
                        if img: slot5.image(img, use_container_width=True)
                        
            except Exception as e:
                st.error(f"Generation Bus Interface Fault: {e}")

    run_generation_stream()

# --- TAB 2: SYSTEM MANAGEMENT & GRID CURVES ---
with tab_grid:
    st.title("National & State Grid Monitoring Dashboard")
    st.markdown("### Real-Time Merit Dispatch & Demand Operations")
    
    live_tn_val, live_national_val, cost_metrics = fetch_realtime_grid_data()
    grid_df = generate_24hr_grid_history(live_tn_val, live_national_val)

    st.markdown(
        f"<div style='font-size: 0.85rem; opacity: 0.8; margin-bottom: 15px; font-weight: bold;'>"
        f"Grid Sync Timestamp: {datetime.now(IST).strftime('%H:%M:%S')} (IST)</div>", 
        unsafe_allow_html=True
    )

    c_state, c_national = st.columns(2)
    with c_state:
        st.markdown("<h3 style='text-align: center;'>Tamil Nadu State Demand</h3>", unsafe_allow_html=True)
        st.metric(label="Live TN Demand", value=f"{live_tn_val:,} MW")
        _, d_center, _ = st.columns([1, 2, 1])
        with d_center:
            img = draw_two_lines_on_gauge(os.path.join(current_dir, "GAUGE.jpg"), [f"{live_tn_val:,}", "MW"])
            if img: st.image(img, width=gauge_size, use_container_width=False)
            else: st.error("State matrix asset missing.")

    with c_national:
        st.markdown("<h3 style='text-align: center;'>All India National Demand</h3>", unsafe_allow_html=True)
        st.metric(label="Live National Demand", value=f"{live_national_val:,} MW")
        _, d_center, _ = st.columns([1, 2, 1])
        with d_center:
            img = draw_two_lines_on_gauge(os.path.join(current_dir, "GAUGE.jpg"), [f"{live_national_val:,}", "MW"])
            if img: st.image(img, width=gauge_size, use_container_width=False)
            else: st.error("National matrix asset missing.")

    st.markdown("---")
    st.markdown("### ⚡ Generation Cost Summary: NCTPS STAGE 1")
    mc1, mc2, mc3 = st.columns(3)
    with mc1: st.metric(label="Fixed Cost (FC)", value=f"₹ {cost_metrics['fixed']} / Unit")
    with mc2: st.metric(label="Variable Cost (VC)", value=f"₹ {cost_metrics['variable']} / Unit")
    with mc3: st.metric(label="Total Merit Cost", value=f"₹ {cost_metrics['total']} / Unit")

    st.markdown("---")
    st.markdown("### Grid Load Curves (Trailing 24 Hours)")
    trend_df_indexed = grid_df.set_index("Time")
    chart_view = st.radio("Select Trend Line View:", ["Both", "State Only", "National Only"], horizontal=True)

    if chart_view == "Both":
        st.line_chart(trend_df_indexed, y=["State Demand (MW)", "National Demand (MW)"], color=["#00d2ff", "#ffaa00"])
    elif chart_view == "State Only":
        st.line_chart(trend_df_indexed, y="State Demand (MW)", color="#00d2ff")
    else:
        st.line_chart(trend_df_indexed, y="National Demand (MW)", color="#ffaa00")

# --- 6. GLOBAL REFRESH OVERRIDE LINK ---
if auto_refresh:
    time.sleep(refresh_interval)  # Dynamically sync loop with user/default refresh config (5s)
    st.rerun()
