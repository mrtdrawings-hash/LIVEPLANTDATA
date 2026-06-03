import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import requests
from datetime import timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# --- CONFIG ---
st.set_page_config(page_title="NCTPS Stage-I Dashboard", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))

# --- IMAGE LOAD ---
@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    paths = [
        os.path.join(current_dir, image_filename),
        image_filename
    ]
    for p in paths:
        if os.path.exists(p):
            img = Image.open(p).convert("RGBA")
            bg = Image.new("RGB", img.size, (255,255,255))
            bg.paste(img, (0,0), img)
            return bg.convert("RGBA")
    return None

def get_font(size=100):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        return ImageFont.load_default()

# --- 🔥 UPDATED DISPLAY FUNCTION ---
def draw_digital_display(value, image_filename, display_type="mw"):
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    overlay = Image.new("RGBA", base_img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    width, height = base_img.size

    # ✅ AUTO FONT SIZE (BIGGER & RESPONSIVE)
    font_size = int(height * 0.22)
    font = get_font(font_size)

    text = str(value)

    # ✅ COLORS
    if display_type == "hz":
        color = (255,255,255,255)
    elif display_type == "total":
        color = (0,0,0,255)
    else:
        color = (255,255,0,255)

    # ✅ TEXT SIZE
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # ✅ CENTER ALIGNMENT (TUNED)
    x = (width - tw) / 2

    y_offset = {
        "mw": 0.05,
        "total": 0.08,
        "hz": 0.02
    }.get(display_type, 0.05)

    y = (height - th) / 2 + (height * y_offset)

    draw.text((x, y), text, fill=color, font=font)

    return Image.alpha_composite(base_img, overlay)

# --- SIDEBAR ---
refresh_interval = st.sidebar.slider("Refresh (sec)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Auto Refresh", True)

# --- TABS ---
tab1, tab2 = st.tabs(["Generation", "Grid"])

# =========================
# ⚡ GENERATION TAB
# =========================
with tab1:
    st.title("⚡ NCTPS LIVE MW DASHBOARD")

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

            def safe(v):
                try:
                    if v is None or v == "":
                        return "0"
                    return str(v)
                except:
                    return "0"

            u1 = safe(data.get("UNIT1", {}).get("MW"))
            u2 = safe(data.get("UNIT2", {}).get("MW"))
            u3 = safe(data.get("UNIT3", {}).get("MW"))
            hz = safe(data.get("HZ", {}).get("HZ"))

            # ✅ TOTAL
            total = 0
            for v in [u1, u2, u3]:
                try:
                    total += float(v)
                except:
                    pass
            total_str = str(int(total))

            # 🔥 FORCE UI UPDATE (KEY FIX)
            ts = str(time.time())

            img1 = draw_digital_display(u1, "Gemini_U1.jpg", "mw")
            if img1:
                slot1.image(img1, use_container_width=True, key="u1_" + ts)

            img2 = draw_digital_display(u2, "Gemini_U2.jpg", "mw")
            if img2:
                slot2.image(img2, use_container_width=True, key="u2_" + ts)

            img3 = draw_digital_display(u3, "Gemini_U3.jpg", "mw")
            if img3:
                slot3.image(img3, use_container_width=True, key="u3_" + ts)

            img4 = draw_digital_display(total_str, "Gemini_T.jpg", "total")
            if img4:
                slot4.image(img4, use_container_width=True, key="total_" + ts)

            img5 = draw_digital_display(hz, "HZ.jpg", "hz")
            if img5:
                slot5.image(img5, use_container_width=True, key="hz_" + ts)

            # 🔍 DEBUG (remove later)
            # st.write("DEBUG:", u1, u2, u3, hz)

        except Exception as e:
            st.error(f"Update Error: {e}")

    update_generation()

# =========================
# 🌐 GRID TAB
# =========================
with tab2:
    st.title("🌐 Grid Monitoring")

    val1 = 15000 + np.random.randint(-200,200)
    val2 = 200000 + np.random.randint(-2000,2000)

    c1, c2 = st.columns(2)

    with c1:
        st.metric("State Demand", f"{val1} MW")

    with c2:
        st.metric("National Demand", f"{val2} MW")
