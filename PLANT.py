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
# PERMANENT ASSET CACHING LAYER (Bypasses Re-loads)
# ------------------------------------------------------------------
@st.cache_resource
def load_base64_backgrounds():
    """
    Reads local image files once and saves them into the RAM cache.
    Bypasses file system lookups during rapid refresh intervals.
    """
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

# Load backgrounds into memory cache
bg_images = load_base64_backgrounds()

# ------------------------------------------------------------------
# NO-FLASH STYLING BLOCKS (Pure HTML Layouts)
# ------------------------------------------------------------------
css_styles = """
<style>
.instrument-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 400 / 250; /* Matches instrument card proportions */
    background-size: 100% 100%;
    background-repeat: no-repeat;
    background-position: center;
    border-radius: 6px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    overflow: hidden;
}

/* Base64 styling injected straight into the container background */
.bg-u1 { background-image: url('data:image/jpeg;base64,""" + bg_images["u1"] + """'); }
.bg-u2 { background-image: url('data:image/jpeg;base64,""" + bg_images["u2"] + """'); }
.bg-u3 { background-image: url('data:image/jpeg;base64,""" + bg_images["u3"] + """'); }
.bg-hz { background-image: url('data:image/jpeg;base64,""" + bg_images["hz"] + """'); }

/* Fallbacks if files are not present in the current workspace directory */
.instrument-wrapper:not([style*="data:image"]) {
    background-color: #111622;
    border: 2px solid #283143;
}

/* Dynamic Numeric Text Layer centered over the dials */
.telemetry-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    pointer-events: none;
}

/* Digital LED Panel Character Looks */
.digital-text {
    font-family: 'Courier New', Courier, monospace;
    font-weight: 450;
    font-size: clamp(2.5rem, 6vw, 4.2rem); /* Scalable font based on column widths */
    letter-spacing: 2px;
    text-shadow: 0px 0px 12px rgba(0,0,0,0.8);
    user-select: none;
}

.color-cyan {
    color: #00f0ff;
}

.color-yellow {
    color: #ffeb00;
}
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# ------------------------------------------------------------------
# LIGHTWEIGHT INTERFACE INJECTOR
# ------------------------------------------------------------------
def display_flicker_free_card(value, bg_key, is_frequency=False):
    """
    Renders standard text characters directly on top of the cached background container.
    Since only text variations update, the browser never clears or re-renders the panel container.
    """
    text_color_class = "color-yellow" if is_frequency else "color-cyan"
    
    html_card = f"""
    <div class="instrument-wrapper bg-{bg_key}">
        <div class="telemetry-overlay">
            <span class="digital-text {text_color_class}">{value}</span>
        </div>
    </div>
    """
    return html_card

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
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        card1 = display_flicker_free_card(u1_val, "u1", is_frequency=False)
        i1.markdown(card1, unsafe_allow_html=True)

        # UNIT 2 DISPLAY FRAME
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        card2 = display_flicker_free_card(u2_val, "u2", is_frequency=False)
        i2.markdown(card2, unsafe_allow_html=True)

        # UNIT 3 DISPLAY FRAME
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        card3 = display_flicker_free_card(u3_val, "u3", is_frequency=False)
        i3.markdown(card3, unsafe_allow_html=True)

        # GRID FREQUENCY DISPLAY FRAME
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        card4 = display_flicker_free_card(hz_val, "hz", is_frequency=True)
        i4.markdown(card4, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Live Telemetry Timeout/Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
