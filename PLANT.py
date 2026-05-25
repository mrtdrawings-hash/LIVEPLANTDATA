import streamlit as st
import requests
import time
import base64
import os

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS STAGE 1 LIVE MW ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ------------------------------------------------------------------
# SYSTEM ASSET CACHING LAYER (Loaded into memory exactly once)
# ------------------------------------------------------------------
@st.cache_resource
def load_base64_backgrounds():
    filenames = {
        "u1": "Gemini_U1.jpg",
        "u2": "Gemini_U2.jpg",
        "u3": "Gemini_U3.jpg",
        "hz": "HZ.jpg"
    }
    
    encoded_b64 = {}
    for key, filename in filenames.items():
        paths_to_check = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
            os.path.join(os.getcwd(), filename),
            filename
        ]
        
        target_path = None
        for p in paths_to_check:
            if os.path.exists(p):
                target_path = p
                break
                
        b64_str = ""
        if target_path:
            try:
                with open(target_path, "rb") as img_file:
                    b64_str = base64.b64encode(img_file.read()).decode()
            except Exception:
                pass
        encoded_b64[key] = b64_str
        
    return encoded_b64

bg_images = load_base64_backgrounds()

# ------------------------------------------------------------------
# DYNAMIC PERSISTENT FRAMEWORK (HTML, CSS & JAVASCRIPT INJECTION)
# ------------------------------------------------------------------
# This combined layout matrix mounts onto the browser engine once.
# Streamlit will never wipe or rebuild these container elements.
core_dashboard_layout = f"""
<style>
.dashboard-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 20px;
    width: 100%;
    margin-top: 15px;
}}
.instrument-wrapper {{
    position: relative;
    width: 100%;
    aspect-ratio: 400 / 250;
    background-size: 100% 100%;
    background-repeat: no-repeat;
    background-position: center;
    border-radius: 6px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    overflow: hidden;
}}
.bg-u1 {{ background-image: url('data:image/jpeg;base64,{bg_images["u1"]}'); }}
.bg-u2 {{ background-image: url('data:image/jpeg;base64,{bg_images["u2"]}'); }}
.bg-u3 {{ background-image: url('data:image/jpeg;base64,{bg_images["u3"]}'); }}
.bg-hz {{ background-image: url('data:image/jpeg;base64,{bg_images["hz"]}'); }}

.telemetry-overlay {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    pointer-events: none;
}}
.digital-text {{
    font-family: 'Courier New', Courier, monospace;
    font-weight: 200;
    font-size: clamp(1.8rem, 4.2vw, 2.8rem);
    letter-spacing: 1px;
    text-shadow: 0px 0px 10px rgba(0,0,0,0.9);
    margin-top: 5px;
    user-select: none;
    transition: color 0.2s ease;
}}
.color-cyan {{ color: #00f0ff; }}
.color-yellow {{ color: #ffeb00; }}
</style>

<div class="dashboard-grid">
    <div class="instrument-wrapper bg-u1">
        <div class="telemetry-overlay"><span id="val-u1" class="digital-text color-cyan">---</span></div>
    </div>
    <div class="instrument-wrapper bg-u2">
        <div class="telemetry-overlay"><span id="val-u2" class="digital-text color-cyan">---</span></div>
    </div>
    <div class="instrument-wrapper bg-u3">
        <div class="telemetry-overlay"><span id="val-u3" class="digital-text color-cyan">---</span></div>
    </div>
    <div class="instrument-wrapper bg-hz">
        <div class="telemetry-overlay"><span id="val-hz" class="digital-text color-yellow">---</span></div>
    </div>
</div>

<script>
// Micro-injector function that bypasses Streamlit re-renders
function updateTelemetryFrame(elementId, freshValue) {{
    const targetEl = window.parent.document.getElementById(elementId);
    if (targetEl) {{
        if (targetEl.innerText !== freshValue) {{
            targetEl.innerText = freshValue;
        }}
    }}
}}
</script>
"""

# Render layout shell structure onto browser DOM canvas
st.html(core_dashboard_layout)

# ------------------------------------------------------------------
# RUNTIME DATA RETRIEVAL & DOM PUSHING LOOP
# ------------------------------------------------------------------
url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

try:
    response = requests.get(url, timeout=4)
    if response.status_code == 200 and (nctps_data := response.json()):
        
        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))
        
        # Inject tiny script blocks that update only the plain text characters directly inside the browser elements
        st.components.v1.html(f"""
            <script>
                updateTelemetryFrame('val-u1', '{u1_val}');
                updateTelemetryFrame('val-u2', '{u2_val}');
                updateTelemetryFrame('val-u3', '{u3_val}');
                updateTelemetryFrame('val-hz', '{hz_val}');
            </script>
        """, height=0, width=0)
        
        # Upper standard metrics fallback display monitoring array
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        col2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        col3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        col4.metric(label="Grid Frequency", value=f"{hz_val} Hz")

except Exception as e:
    st.error(f"Live Telemetry Timeout/Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
