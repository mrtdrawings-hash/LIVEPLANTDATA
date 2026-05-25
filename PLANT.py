import streamlit as st
import requests
import os
from PIL import Image, ImageDraw

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NOCTPS 1 LIVE MW DASHBOARD ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ------------------------------------------------------------------
# CACHED IMAGES - ELIMINATES FILESYSTEM LAG & FLICKERING
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# MULTI-STYLE GEOMETRIC VECTOR ENGINE 
# ------------------------------------------------------------------
def draw_custom_vector_digit(draw, x, y, char, w, h, thickness, color, slant=0.0):
    """
    Renders 7-segment style numbers with optional slant styling factor 
    to dramatically transform the font style face while maintaining size.
    """
    t = thickness
    mid_y = h / 2

    # Map baseline coordinates for standard segments
    segments = {
        'a': (t, 0, w - 2*t, t),               # Top
        'b': (w - t, t, t, mid_y - t),         # Top Right
        'c': (w - t, mid_y, t, mid_y - t),     # Bottom Right
        'd': (t, h - t, w - 2*t, t),           # Bottom
        'e': (0, mid_y, t, mid_y - t),         # Bottom Left
        'f': (0, t, t, mid_y - t),             # Top Left
        'g': (t, mid_y - t/2, w - 2*t, t)      # Middle
    }

    mapping = {
        '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abcdg', '4': 'fgbc',
        '5': 'afgcd', '6': 'afedcg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
        '-': 'g'
    }

    if char == '.':
        # Apply slant offset calculation to decimal point positioning
        slant_offset = slant * (h - t)
        draw.rectangle([x + w/2 - t + slant_offset, y + h - 1.5*t, x + w/2 + t + slant_offset, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        
        # Stylize font geometry: calculate progressive shift based on height coordinate
        shift_top = slant * sy
        shift_bottom = slant * (sy + sh)
        
        # Convert standard rectangles into elegant slanted quad shapes
        poly_points = [
            (x + sx + shift_top, y + sy),
            (x + sx + sw + shift_top, y + sy),
            (x + sx + sw + shift_bottom, y + sy + sh),
            (x + sx + shift_bottom, y + sy + sh)
        ]
        draw.polygon(poly_points, fill=color)

def draw_vector_string(draw, text, cx, cy, color, is_frequency):
    # PRESERVED FONT SIZE DIMENSIONS EXACTLY
    digit_w = 80
    digit_h = 138
    thickness = 18
    spacing = 14

    # Apply style transformation variable: Slanted for MW, Classic Upright for HZ
    slant_factor = 0.0 if is_frequency else -0.08

    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)

    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color, slant=slant_factor)
        curr_x += digit_w + spacing

def draw_digital_display(value, image_filename, is_frequency=False):
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        center_x = base_img.size[0] *
