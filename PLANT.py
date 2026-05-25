import streamlit as st
import requests
import time
import base64
import os

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")

# Inject Custom CSS for stable, non-flashing image containers with absolute text overlays
st.markdown("""
<style>
    .card-container {
        position: relative;
        width: 100%;
        display: inline-block;
    }
    .card-image {
        width: 100%;
        height: auto;
        display: block;
        border-radius: 4px;
    }
    .overlay-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        font-size: 3.5vw; /* Scales dynamically with screen width */
        white-space: nowrap;
        text-shadow: 3px 3px 5px rgba(0,0,0,1); /* Deep shadow for heavy readability */
    }
    .color-cyan { color: #00f0ff; }
    .color-yellow { color: #ffeb00; }
</style>
""", unsafe_style_with_html=True)

st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ------------------------------------------------------------------
# BASE64 IMAGE ENCODER (Eliminates broken browser paths completely)
# ------------------------------------------------------------------
@st.cache_resource
def get_base64_image(image_path):
    """Loads a local image file and converts it into a Base64 string for direct HTML injection."""
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/jpeg;base64,{encoded}"
        else:
            # Fallback if image file is entirely missing from the directory
            return "https://via.placeholder.com/400x300?text=File+Not+Found"
    except Exception:
        return "https://via.placeholder.com/400x300?text=Error+Loading"

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Establish persistent grid columns
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
    response = requests.get(url)
    if response.status_code == 200 and (nctps_data := response.json()):
        
        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))
        
        # --- Pre-convert local images to Base64 (cached instantly) ---
        img1_b64 = get_base64_image("Gemini_U1.jpg")
        img2_b64 = get_base64_image("Gemini_U2.jpg")
        img3_b64 = get_base64_image("Gemini_U3.jpg")
        hz_b64 = get_base64_image("HZ.jpg")
        
        # --- UNIT 1 ---
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            i1.markdown(f"""
            <div class="card-container">
                <img src="{img1_b64}" class="card-image">
                <div class="overlay-text color-cyan">{u1_val}</div>
            </div>
            """, unsafe_style_with_html=True)

        # --- UNIT 2 ---
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            i2.markdown(f"""
            <div class="card-container">
                <img src="{img2_b64}" class="card-image">
                <div class="overlay-text color-cyan">{u2_val}</div>
            </div>
            """, unsafe_style_with_html=True)

        # --- UNIT 3 ---
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            i3.markdown(f"""
            <div class="card-container">
                <img src="{img3_b64}" class="card-image">
                <div class="overlay-text color-cyan">{u3_val}</div>
            </div>
            """, unsafe_style_with_html=True)

        # --- GRID FREQUENCY ---
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        if hz_val != "N/A":
            i4.markdown(f"""
            <div class="card-container">
                <img src="{hz_b64}" class="card-image">
                <div class="overlay-text color-yellow">{hz_val}</div>
            </div>
            """, unsafe_style_with_html=True)

except Exception as e:
    st.error(f"Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
