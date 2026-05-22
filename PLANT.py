import streamlit as st
import requests
import time
from PIL import Image, ImageDraw

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

def draw_custom_vector_digit(draw, x, y, char, w, h, thickness, color):
    """
    Renders thick, bold 7-segment style numbers directly onto pixel coordinates.
    Bypasses all server font system dependencies permanently.
    """
    t = thickness
    mid_y = h / 2
    
    # 7-Segment coordinate line maps: (rel_x, rel_y, width, height)
    segments = {
        'a': (t, 0, w - 2*t, t),              # Top
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
        # Enhanced thick decimal point block
        draw.rectangle([x + w/2 - t, y + h - 1.5*t, x + w/2 + t, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_vector_string(draw, text, cx, cy, color):
    """Aligns and scales massive digital strings precisely into the geometric center."""
    # ------------------------------------------------------------------
    # FONT SIZE MAXIMIZED: Increased sizes dramatically to match the template image
    # ------------------------------------------------------------------
    digit_w = 46       
    digit_h = 80       
    thickness = 11      
    spacing = 10       
    
    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)
    
    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color)
        else:
            # High-visibility block letters for MW and Hz
            if char == 'M':
                draw.rectangle([curr_x, start_y, curr_x + 10, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 10, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y, curr_x + digit_w, start_y + 10], fill=color)
                draw.rectangle([curr_x + digit_w/2 - 5, start_y, curr_x + digit_w/2 + 5, start_y + digit_h], fill=color)
            elif char == 'W':
                draw.rectangle([curr_x, start_y, curr_x + 10, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 10, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 10, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w/2 - 5, start_y + 25, curr_x + digit_w/2 + 5, start_y + digit_h], fill=color)
            elif char == 'H':
                draw.rectangle([curr_x, start_y, curr_x + 10, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 10, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y + digit_h/2 - 5, curr_x + digit_w, start_y + digit_h/2 + 5], fill=color)
            elif char == 'z':
                draw.rectangle([curr_x, start_y + 20, curr_x + digit_w, start_y + 30], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 10, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + 10, start_y + 30, curr_x + digit_w - 10, start_y + digit_h - 10], fill=color)
        curr_x += digit_w + spacing

def draw_digital_display(value, image_filename, is_frequency=False):
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 🎯 GEOMETRIC DEAD CENTER ALIGNMENT FOR ALL IMAGES
        center_x = png_img.size[0] * 0.50
        center_y = png_img.size[1] * 0.50
        
        if is_frequency:
            display_text = f"{value} Hz"
            text_color = (255, 235, 0, 255)  # Vibrant Safety Yellow
        else:
            display_text = f"{value} MW"
            text_color = (0, 240, 255, 255) # Electric Cyan
            
        # Draw clean geometric digital string layouts
        draw_vector_string(draw, display_text, center_x, center_y, text_color)
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Permanent layout placeholders to eliminate page refresh flickering completely
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
        
        # UNIT 1
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
            if img1:
                i1.image(img1, use_container_width=True,
