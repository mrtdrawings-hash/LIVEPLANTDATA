import streamlit as st
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS 1 LIVE MW DASHBOARD ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    paths_to_check = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename,
    ]
    target_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if not target_path:
        return None

    png_img = Image.open(target_path).convert("RGBA")
    solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
    solid_bg.paste(png_img, (0, 0), png_img)
    return solid_bg.convert("RGBA")

def get_scalable_font(font_size=135):
    # Fallback font handling
    try:
        return ImageFont.truetype("arialbd.ttf", font_size)
    except:
        return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
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
        text_color = (0, 0, 0, 255) if display_type == "total" else (0, 240, 255, 255)

        bbox = draw.textbbox((0, 0), text_str, font=font)
        x = center_x - ((bbox[2] - bbox[0]) / 2)
        y = center_y - ((bbox[3] - bbox[1]) / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)

        if display_type == "total":
            numeric_val = max(0.0, min(float(value), 750.0))
            dial_center_x, dial_center_y = width * 0.50, height * 0.50

            # Linear 240-degree calibration
            mw_bp = [0.0, 75.0, 150.0, 225.0, 300.0, 375.0, 450.0, 525.0, 600.0, 675.0, 750.0]
            ang_bp = [240.0, 216.0, 192.0, 168.0, 144.0, 120.0, 96.0, 72.0, 48.0, 24.0, 0.0]

            angle_deg = 240.0
            for i in range(len(mw_bp) - 1):
                if mw_bp[i] <= numeric_val <= mw_bp[i+1]:
                    fraction = (numeric_val - mw_bp[i]) / (mw_bp[i+1] - mw_bp[i])
                    angle_deg = ang_bp[i] + fraction * (ang_bp[i+1] - ang_bp[i])
                    break
            
            angle_rad = math.radians(angle_deg + 180) 
            outer_rim_radius = width * 0.448
            pointer_length = width * 0.072
            base_width = width * 0.015

            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
            pivot_x = dial_center_x + outer_rim_radius * cos_a
            pivot_y = dial_center_y + outer_rim_radius * sin_a
            tip_x = dial_center_x + (outer_rim_radius - pointer_length) * cos_a
            tip_y = dial_center_y + (outer_rim_radius - pointer_length) * sin_a

            perp_l = angle_rad + (math.pi / 2.0)
            perp_r = angle_rad - (math.pi / 2.0)

            draw.polygon(
                [(pivot_x + base_width * math.cos(perp_l), pivot_y + base_width * math.sin(perp_l)),
                 (tip_x, tip_y),
                 (pivot_x + base_width * math.cos(perp_r), pivot_y + base_width * math.sin(perp_r))],
                fill=(220, 35, 25, 255)
            )

        return Image.alpha_composite(base_img, overlay)
    except Exception as e:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

col1, col2, col3, col4, col5 = st.columns(5)
slots = [col1.empty(), col2.empty(), col3.empty(), col4.empty(), col5.empty()]

@st.fragment(run_every=refresh_interval if auto_refresh else None)
def live_panel():
    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            data = response.json() or {}
            # Update slots... (Add your specific unit extraction logic here)
            img_total = draw_digital_display(str(int(sum(float(data[u]["MW"]) for u in ["UNIT1","UNIT2","UNIT3"]))), "Gemini_T.jpg", "total")
            if img_total: slots[3].image(img_total, use_container_width=True)
    except Exception as e:
        st.error(f"Telemetry Link Error: {e}")

live_panel()
