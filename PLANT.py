import streamlit as st
import requests
import time
import base64
import os

st.set_page_config(page_title="NCTPS STAGE 1 LIVE MW DASHBOARD", layout="wide")
st.title("⚡ NCTPS STAGE 1 LIVE MW DATA ⚡")

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
# DYNAMIC FLICKER-FREE CARD RENDERER
# ------------------------------------------------------------------
def render_instrument_card(value, bg_key, is_frequency=False):
    """
    Renders the background image precisely sized inside the columns.
    Ensures background image repeats are disabled permanently.
    """
    b64_data = bg_images.get(bg_key, "")
    text_color = "#ffeb00" if is_frequency else "#00f0ff"
    
    html_layout = f"""
    <div style="position: relative; width: 100%; max-width: 400px; aspect-ratio: 400/250; 
                margin: 0 auto; background-image: url('data:image/jpeg;base64,{b64_data}'); 
                background-size: contain; background-repeat: no-repeat; background-position: center;
                border-radius: 6px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); overflow: hidden;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                    display: flex; justify-content: center; align-items: center; pointer-events: none;">
            <span style="font-family: 'Courier New', Courier, monospace; font-weight: 900; 
                         font-size: clamp(1.6rem, 4vw, 2.3rem); color: {text_color}; 
                         letter-spacing: 1px; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 0px 0px 8px rgba(0,0,0,0.8);
                         margin-top: 10px; user-select: none;">
                {value}
            </span>
        </div>
    </div>
    """
    return html_layout

# ------------------------------------------------------------------
# MAIN TELEMETRY LOOP
# ------------------------------------------------------------------
url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

col1, col2, col3, col4 = st.columns(4)

with col1:
    i1 = st.empty()
with col2:
    i2 = st.empty()
with col3:
    i3 = st.empty()
with col4:
    i4 = st.empty()

try:
    response = requests.get(url, timeout=4)
    if response.status_code == 200 and (nctps_data := response.json()):
        
        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))
        
        # UNIT 1 DISPLAY FRAME
        i1.markdown(render_instrument_card(u1_val, "u1", is_frequency=False), unsafe_allow_html=True)

        # UNIT 2 DISPLAY FRAME
        i2.markdown(render_instrument_card(u2_val, "u2", is_frequency=False), unsafe_allow_html=True)

        # UNIT 3 DISPLAY FRAME
        i3.markdown(render_instrument_card(u3_val, "u3", is_frequency=False), unsafe_allow_html=True)

        # GRID FREQUENCY DISPLAY FRAME
        i4.markdown(render_instrument_card(hz_val, "hz", is_frequency=True), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Live Telemetry Timeout/Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
