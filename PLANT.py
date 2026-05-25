import streamlit as st
import requests
import time
import base64
import os

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

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
    Renders the background image using a base64 string directly inside the HTML structure.
    The text is overlaid cleanly over the image container.
    """
    b64_data = bg_images.get(bg_key, "")
    text_color = "#ffeb00" if is_frequency else "#00f0ff"
    
    # CSS overlay framework that centers the text without using flaky JavaScript
    html_layout = f"""
    <div style="position: relative; width: 100%; aspect-ratio: 400/250; 
                background-image: url('data:image/jpeg;base64,{b64_data}'); 
                background-size: 100% 100%; background-repeat: no-repeat; 
                border-radius: 6px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); overflow: hidden;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                    display: flex; justify-content: center; align-items: center; pointer-events: none;">
            <span style="font-family: 'Courier New', Courier, monospace; font-weight: 900; 
                         font-size: clamp(1.8rem, 4.5vw, 2.5rem); color: {text_color}; 
                         letter-spacing: 1px; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 0px 0px 8px rgba(0,0,0,0.8);
                         margin-top: 8px; user-select: none;">
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
    m1 = st.empty()
    i1 = st.empty()
with col2:
    m2 = st.empty()
    i2 = st.empty()
with col3:
    m3 = st.empty()
    i3 = st.empty()
with col4:
    m4 = st.empty()
    i4 = st.empty()

try:
    response = requests.get(url, timeout=4)
    if response.status_code == 200 and (nctps_data := response.json()):
        
        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))
        
        # UNIT 1 DISPLAY FRAME
        m1.metric(label="UNIT 1 Live Generation", value=f"{u1_val} MW")
        i1.markdown(render_instrument_card(u1_val, "u1", is_frequency=False), unsafe_allow_html=True)

        # UNIT 2 DISPLAY FRAME
        m2.metric(label="UNIT 2 Live Generation", value=f"{u2_val} MW")
        i2.markdown(render_instrument_card(u2_val, "u2", is_frequency=False), unsafe_allow_html=True)

        # UNIT 3 DISPLAY FRAME
        m3.metric(label="UNIT 3 Live Generation", value=f"{u3_val} MW")
        i3.markdown(render_instrument_card(u3_val, "u3", is_frequency=False), unsafe_allow_html=True)

        # GRID FREQUENCY DISPLAY FRAME
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        i4.markdown(render_instrument_card(hz_val, "hz", is_frequency=True), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Live Telemetry Timeout/Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
