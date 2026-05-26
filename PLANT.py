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
    """
    Safely loads a clean, scalable font across both local machines and 
    Linux-based web servers (like Streamlit Cloud).
    """
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

    windows_paths = [
        "arialbd.ttf",       
        "trebucbd.ttf",     
        "consola.ttf"       
    ]
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
    """
    Renders text centered over the panel face and handles an overhead 
    rim-mounted sweeping pointer exclusively for the Total MW dial.
    """
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Center positioning for text
        center_x = width * 0.485
        center_y = height * 0.49

        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        # Color profile routing
        if display_type == "hz":
            text_color = (255, 235, 0, 255)  # Warning Yellow
        elif display_type == "total":
            text_color = (0, 0, 0, 255)      # Crisp Solid Black for White Dial Face
        else:
            text_color = (0, 240, 255, 255)  # Standard Cyan for Units 1, 2, 3

        # Calculate text bounding dimensions and draw string safely in the center
        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)

        # --- OVERHEAD POINTER LOGIC FOR TOTAL MW DIAL ---
        if display_type == "total":
            try:
                numeric_val = float(value)
            except ValueError:
                numeric_val = 0.0

            # Constrain values within the calibrated dial limit (0 to 750 MW)
            numeric_val = max(0.0, min(numeric_val, 750.0))

            # Calibrate the angle map trajectory along the outer numeric rim scale
            # 0 MW is at 220° (bottom-left), 750 MW is at -40° (bottom-right)
            start_angle = 220
            end_angle = -40
            
            angle_deg = start_angle + (numeric_val - 0) * (end_angle - start_angle) / (750 - 0)
            angle_rad = math.radians(angle_deg)

            # Outer boundary scale radius near the numbers
            outer_rim_radius = width * 0.41
            
            # Pointer drops inward from the upper numbers, stopping well short of the center text
            pointer_length = width * 0.14
            base_width = width * 0.016

            # The base pivot point is anchored out on the top numeric scale track line
            pivot_x = center_x + outer_rim_radius * math.cos(angle_rad)
            pivot_y = center_y - outer_rim_radius * math.sin(angle_rad)

            # The pointer tip projects inward toward the center, acting as a clean hanging marker
            tip_x = center_x + (outer_rim_radius - pointer_length) * math.cos(angle_rad)
            tip_y = center_y - (outer_rim_radius - pointer_length) * math.sin(angle_rad)

            # Calculate perpendicular shoulders for a sharp wedge indicator arrow
            perp_angle_l = angle_rad + (math.pi / 2)
            perp_angle_r = angle_rad - (math.pi / 2)

            base_l_x = pivot_x + base_width * math.cos(perp_angle_l)
            base_l_y = pivot_y - base_width * math.sin(perp_angle_l)
            base_r_x = pivot_x + base_width * math.cos
