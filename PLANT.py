import streamlit as st
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS 1 LIVE MW DASHBOARD ⚡")

# ---------------- SETTINGS ----------------
st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ---------------- IMAGE LOAD ----------------
@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename,
    ]
    path = next((p for p in paths if os.path.exists(p)), None)
    if not path:
        return None

    img = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, (0, 0), img)
    return bg.convert("RGBA")

# ---------------- FONT ----------------
def get_font(size=130):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        return ImageFont.load_default()

# ---------------- NON-LINEAR CALIBRATION ----------------
# 🔴 Tune these values once to match dial exactly
MW_TABLE = [0, 100, 200, 300, 400, 500, 600, 700, 750]
ANGLE_TABLE = [140, 110, 80, 40, 10, -20, -60, -110, -140]

def get_angle(mw):
    mw = max(0, min(750, mw))
    for i in range(len(MW_TABLE) - 1):
        if MW_TABLE[i] <= mw <= MW_TABLE[i+1]:
            frac = (mw - MW_TABLE[i]) / (MW_TABLE[i+1] - MW_TABLE[i])
            return ANGLE_TABLE[i] + frac * (ANGLE_TABLE[i+1] - ANGLE_TABLE[i])
    return ANGLE_TABLE[0]

# ---------------- DRAW FUNCTION ----------------
def draw_display(value, image_file, dtype="mw"):
    base = load_base_image(image_file)
    if base is None:
        return None

    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # -------- TEXT --------
    font = get_font(130)
    text = str(value)

    color = (0, 240, 255, 255)
    if dtype == "hz":
        color = (255, 235, 0, 255)
    if dtype == "total":
        color = (0, 0, 0, 255)

    bbox = draw.textbbox((0, 0), text, font=font)

    # Default center
    x = (w - (bbox[2]-bbox[0])) / 2
    y = (h - (bbox[3]-bbox[1])) / 2

    # 🔴 FIXED POSITION FOR TOTAL DIAL
    if dtype == "total":
        x = w * 0.50 - (bbox[2]-bbox[0]) / 2
        y = h * 0.62 - (bbox[3]-bbox[1]) / 2   # shifted down

    draw.text((x, y), text, fill=color, font=font)

    # -------- POINTER ONLY FOR TOTAL --------
    if dtype == "total":
        try:
            val = float(value)
        except:
            val = 0

        angle = get_angle(val)

        cx, cy = w * 0.5, h * 0.5
        radius = w * 0.45
        length = w * 0.08
        width_p = w * 0.015

        ang = math.radians(270 - angle)
        cos_a, sin_a = math.cos(ang), math.sin(ang)

        px = cx + radius * cos_a
        py = cy + radius * sin_a

        tx = cx + (radius - length) * cos_a
        ty = cy + (radius - length) * sin_a

        perp = math.pi / 2
        lx = px + width_p * math.cos(ang + perp)
        ly = py + width_p * math.sin(ang + perp)
        rx = px + width_p * math.cos(ang - perp)
        ry = py + width_p * math.sin(ang - perp)

        draw.polygon([(lx, ly), (tx, ty), (rx, ry)], fill=(220, 30, 30))

    return Image.alpha_composite(base, overlay)

# ---------------- DATA SOURCE ----------------
url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

col1, col2, col3, col4, col5 = st.columns(5)
s1, s2, s3, s4, s5 = col1.empty(), col2.empty(), col3.empty(), col4.empty(), col5.empty()

# ---------------- LIVE PANEL ----------------
@st.fragment(run_every=refresh_interval if auto_refresh else None)
def live():
    try:
        r = requests.get(url, timeout=4)
        data = r.json() if r.status_code == 200 else {}

        u1 = str(data.get("UNIT1", {}).get("MW", "0"))
        u2 = str(data.get("UNIT2", {}).get("MW", "0"))
        u3 = str(data.get("UNIT3", {}).get("MW", "0"))
        hz = str(data.get("HZ", {}).get("HZ", "0"))

        try:
            total = int(float(u1) + float(u2) + float(u3))
        except:
            total = 0

        s1.image(draw_display(u1, "Gemini_U1.jpg"), use_container_width=True)
        s2.image(draw_display(u2, "Gemini_U2.jpg"), use_container_width=True)
        s3.image(draw_display(u3, "Gemini_U3.jpg"), use_container_width=True)
        s4.image(draw_display(total, "Gemini_T.jpg", "total"), use_container_width=True)
        s5.image(draw_display(hz, "HZ.jpg", "hz"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")

live()
