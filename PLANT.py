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
div[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
}
.stImage > img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

current_dir = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))

# --- IMAGE HELPERS ---
@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    paths = [
        os.path.join(current_dir, image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename,
    ]
    target = next((p for p in paths if os.path.exists(p)), None)
    if not target:
        return None
    img = Image.open(target).convert("RGBA")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, (0, 0), img)
    return bg.convert("RGBA")

def get_font(size=135):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        return ImageFont.load_default()

def draw_digital_display(value, image_filename):
    base = load_base_image(image_filename)
    if base is None:
        return None

    overlay = Image.new("RGBA", base.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    font = get_font(135)
    text = str(value)

    w, h = base.size
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]

    x = (w - tw) / 2
    y = (h - th) / 2

    draw.text((x, y), text, fill=(255,255,0,255), font=font)
    return Image.alpha_composite(base, overlay)

# --- SIDEBAR ---
st.sidebar.header("Settings")
refresh_interval = st.sidebar.slider("Refresh Seconds", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Auto Refresh", True)

# --- TABS ---
tab1, tab2 = st.tabs(["Generation", "Grid"])

# =========================
# 🔥 TAB 1 FIXED (NO FLICKER)
# =========================
with tab1:
    st.title("NCTPS LIVE MW")

    # ✅ CREATE STATIC CONTAINERS ONCE
    col1, col2, col3, col4, col5 = st.columns(5)
    slot1 = col1.empty()
    slot2 = col2.empty()
    slot3 = col3.empty()
    slot4 = col4.empty()
    slot5 = col5.empty()

    @st.fragment(run_every=refresh_interval if auto_refresh else None)
    def update_generation():
        url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

        try:
            res = requests.get(url, timeout=4)
            data = res.json() if res.status_code == 200 else {}

            u1 = str(data.get("UNIT1", {}).get("MW", "0"))
            u2 = str(data.get("UNIT2", {}).get("MW", "0"))
            u3 = str(data.get("UNIT3", {}).get("MW", "0"))
            hz = str(data.get("HZ", {}).get("HZ", "0"))

            total = int(float(u1) + float(u2) + float(u3))

            # ✅ ONLY UPDATE CONTENT (NO RE-CREATION)
            slot1.image(draw_digital_display(u1, "Gemini_U1.jpg"), use_container_width=True)
            slot2.image(draw_digital_display(u2, "Gemini_U2.jpg"), use_container_width=True)
            slot3.image(draw_digital_display(u3, "Gemini_U3.jpg"), use_container_width=True)
            slot4.image(draw_digital_display(total, "Gemini_T.jpg"), use_container_width=True)
            slot5.image(draw_digital_display(hz, "HZ.jpg"), use_container_width=True)

        except Exception as e:
            st.error(e)

    update_generation()

# =========================
# 🌐 TAB 2 (UNCHANGED)
# =========================
with tab2:
    st.title("Grid Monitoring")

    val1 = 15000 + np.random.randint(-200,200)
    val2 = 200000 + np.random.randint(-2000,2000)

    c1, c2 = st.columns(2)

    with c1:
        st.metric("State Demand", f"{val1} MW")

    with c2:
        st.metric("National Demand", f"{val2} MW")
