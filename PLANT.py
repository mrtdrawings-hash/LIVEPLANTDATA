import streamlit as st
import requests
import time
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

# ================================
# SIDEBAR SETTINGS
# ================================
st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ================================
# LED TEXT RENDER (SCADA STYLE)
# ================================
def draw_led_text(draw, base_img, text, cx, cy, color):
    try:
        font = ImageFont.truetype("digital-7.ttf", 140)
    except:
        font = ImageFont.load_default()

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = cx - text_w / 2
    y = cy - text_h / 2

    # Animation pulse
    t = time.time()
    glow_intensity = int(120 + 80 * math.sin(t * 2))

    # Shadow
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 180))

    # Glow layer
    glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for i in range(6, 0, -1):
        glow_color = (color[0], color[1], color[2], glow_intensity // (i + 1))
        glow_draw.text((x, y), text, font=font, fill=glow_color)

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=6))
    base_img.alpha_composite(glow_layer)

    # Main crisp text
    draw.text((x, y), text, font=font, fill=color)

# ================================
# MAIN DISPLAY FUNCTION
# ================================
def draw_digital_display(value, image_filename, **kwargs):
    try:
        png_img = Image.open(image_filename).convert("RGBA")

        # White base
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")

        # SCADA dark glass overlay
        panel = Image.new("RGBA", base_img.size, (0, 0, 0, 140))
        base_img = Image.alpha_composite(base_img, panel)

        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        center_x = base_img.size[0] * 0.50
        center_y = base_img.size[1] * 0.50

        display_text = f"{value}"

        is_frequency = kwargs.get('is_frequency', False)

        if "HZ" in image_filename.upper():
            is_frequency = True

        # SCADA color scheme
        if is_frequency:
            text_color = (255, 200, 0, 255)   # amber
        else:
            text_color = (0, 255, 255, 255)   # cyan

        draw_led_text(draw, base_img, display_text, center_x, center_y, text_color)

        return Image.alpha_composite(base_img, overlay)

    except Exception as e:
        print(e)
        return None

# ================================
# DATA SOURCE
# ================================
url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# ================================
# UI LAYOUT
# ================================
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

# ================================
# FETCH DATA
# ================================
try:
    response = requests.get(url)

    if response.status_code == 200 and (nctps_data := response.json()):

        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))

        # UNIT 1
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg")
            if img1:
                i1.image(img1, use_container_width=True)

        # UNIT 2
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg")
            if img2:
                i2.image(img2, use_container_width=True)

        # UNIT 3
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg")
            if img3:
                i3.image(img3, use_container_width=True)

        # FREQUENCY
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        if hz_val != "N/A":
            img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
            if img4:
                i4.image(img4, use_container_width=True)

except Exception as e:
    st.error(f"Connection Error: {e}")

# ================================
# AUTO REFRESH
# ================================
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
