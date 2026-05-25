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
# MULTI-STYLE VECTOR ENGINE (ELEGANT FOR MW / BOLD FOR HZ)
# ------------------------------------------------------------------
def draw_custom_vector_digit(draw, x, y, char, w, h, thickness, color):
    t = thickness
    mid_y = h / 2

    segments = {
        'a': (t, 0, w - 2*t, t),
        'b': (w - t, t, t, mid_y - t),
        'c': (w - t, mid_y, t, mid_y - t),
        'd': (t, h - t, w - 2*t, t),
        'e': (0, mid_y, t, mid_y - t),
        'f': (0, t, t, mid_y - t),
        'g': (t, mid_y - t/2, w - 2*t, t)
    }

    mapping = {
        '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abcdg', '4': 'fgbc',
        '5': 'afgcd', '6': 'afedcg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
        '-': 'g'
    }

    if char == '.':
        draw.rectangle([x + w/2 - t, y + h - 1.5*t, x + w/2 + t, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_vector_string(draw, text, cx, cy, color, is_frequency):
    # DYNAMIC CONFIGURATION ACCORDING TO INSTRUMENT TYPE
    if is_frequency:
        # Kept exactly the same as your original layout configuration
        digit_w = 80
        digit_h = 138
        thickness = 18
        spacing = 14
    else:
        # High-elegance styling configuration: Taller, slimmer, sleeker line profile
        digit_w = 66
        digit_h = 142
        thickness = 10
        spacing = 16

    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)

    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color)
        curr_x += digit_w + spacing

def draw_digital_display(value, image_filename, is_frequency=False):
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        center_x = base_img.size[0] * 0.50
        center_y = base_img.size[1] * 0.52

        text_color = (255, 235, 0, 255) if (is_frequency or "HZ" in image_filename.upper()) else (0, 240, 255, 255)

        draw_vector_string(draw, str(value), center_x, center_y, text_color, is_frequency)
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Permanent outer layout columns to prevent layout jumps
col1, col2, col3, col4 = st.columns(4)
slot1 = col1.empty()
slot2 = col2.empty()
slot3 = col3.empty()
slot4 = col4.empty()

# Dynamically binding refresh loop directly to slider state adjustments
@st.fragment(run_every=refresh_interval if auto_refresh else None)
def live_panel():
    try:
        response = requests.get(url, timeout=4)

        if response.status_code == 200:
            nctps_data = response.json() or {}

            u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
            u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
            u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
            hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))

            if u1_val != "N/A":
                img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
                if img1:
                    slot1.image(img1, use_container_width=True)

            if u2_val != "N/A":
                img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
                if img2:
                    slot2.image(img2, use_container_width=True)

            if u3_val != "N/A":
                img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
                if img3:
                    slot3.image(img3, use_container_width=True)

            if hz_val != "N/A":
                img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
                if img4:
                    slot4.image(img4, use_container_width=True)
        else:
            st.error(f"Server Error Status Code: {response.status_code}")

    except Exception as e:
        st.error(f"Live Telemetry Link Error: {e}")

live_panel()
