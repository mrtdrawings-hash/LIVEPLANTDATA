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
        st.warning(f"Missing background image: {image_filename}")
        return None

    png_img = Image.open(target_path).convert("RGBA")
    solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
    solid_bg.paste(png_img, (0, 0), png_img)
    return solid_bg.convert("RGBA")

def get_scalable_font(font_size=135):
    custom_font_name = "digital-7.ttf"
    paths_to_check = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), custom_font_name),
        os.path.join(os.getcwd(), custom_font_name),
        custom_font_name
    ]
    font_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass

    linux_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for path in linux_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                pass

    windows_paths = ["arialbd.ttf", "trebucbd.ttf", "consola.ttf"]
    for font_name in windows_paths:
        try:
            return ImageFont.truetype(font_name, font_size)
        except Exception:
            pass

    try:
        return ImageFont.load_default(size=font_size)
    except Exception:
        return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # High visibility absolute central placement
        center_x = width * 0.485
        center_y = height * 0.49

        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        if display_type == "hz":
            text_color = (255, 235, 0, 255)
        elif display_type == "total":
            text_color = (0, 0, 0, 255)  # Clean sharp black contrast over white background
        else:
            text_color = (0, 240, 255, 255)

        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)

        # --- PERFECT LINEAR CALIBRATION FOR TOTAL MW DIAL ---
        if display_type == "total":
            try:
                numeric_val = float(value)
            except ValueError:
                numeric_val = 0.0

            numeric_val = max(0.0, min(numeric_val, 750.0))

            # Symmetric absolute frame alignment center positions
            dial_center_x = width * 0.50
            dial_center_y = height * 0.50

            # PIL Angles: 0=Right, 90=Down, 180=Left, 270=Up
            # Dial maps: 150 MW to 180 deg (Left), 375 MW to 270 deg (Up), 600 MW to 360 deg (Right)
            # Math: 180 degree span / 450 MW = 0.4 degrees per MW. 
            # 0 MW starting point = 180 - (150 * 0.4) = 120 degrees
            
            angle_deg = 120.0 + (numeric_val * 0.4)
            angle_rad = math.radians(angle_deg)

            # Sizing matrices tracking along the copper border frame
            outer_rim_radius = width * 0.448
            pointer_length = width * 0.072
            base_width = width * 0.015

            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            # Outer rim baseline contact tracks
            pivot_x = dial_center_x + outer_rim_radius * cos_a
            pivot_y = dial_center_y + outer_rim_radius * sin_a

            # Sharp inner-pointing arrow apex definitions
            tip_x = dial_center_x + (outer_rim_radius - pointer_length) * cos_a
            tip_y = dial_center_y + (outer_rim_radius - pointer_length) * sin_a

            perp_l = angle_rad + (math.pi / 2.0)
            perp_r = angle_rad - (math.pi / 2.0)

            base_l_x = pivot_x + base_width * math.cos(perp_l)
            base_l_y = pivot_y + base_width * math.sin(perp_l)
            base_r_x = pivot_x + base_width * math.cos(perp_r)
            base_r_y = pivot_y + base_width * math.sin(perp_r)

            # Render structured wedge indicator (Deep Red)
            draw.polygon(
                [(base_l_x, base_l_y), (tip_x, tip_y), (base_r_x, base_r_y)],
                fill=(220, 35, 25, 255)
            )
