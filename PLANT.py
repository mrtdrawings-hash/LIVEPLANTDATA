import streamlit as st
import requests
import time
from PIL import Image, ImageDraw

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

def draw_vector_digit(draw, x, y, char, w, h, thickness, color):
    """
    Manually draws a robust, thick, scalable 7-segment style digital character 
    directly onto the pixel canvas using coordinate geometry.
    """
    # Define coordinate lines for the 7 segments
    t = thickness
    half_h = h / 2
    
    # Segment maps: (x_start_rel, y_start_rel, width_rel, height_rel, is_vertical)
    segments = {
        'a': (t, 0, w - 2*t, t, False),            # Top
        'b': (w - t, t, t, half_h - t, True),       # Top Right
        'c': (w - t, half_h, t, half_h - t, True),  # Bottom Right
        'd': (t, h - t, w - 2*t, t, False),         # Bottom
        'e': (0, half_h, t, half_h - t, True),      # Bottom Left
        'f': (0, t, t, half_h - t, True),           # Top Left
        'g': (t, half_h - t/2, w - 2*t, t, False)   # Middle
    }
    
    # Characters mapped to active segments
    char_map = {
        '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abcdg', '4': 'fgbc',
        '5': 'afgcd', '6': 'afedcg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
        '.': 'dot', 'M': 'top_m', 'W': 'top_w', 'H': 'top_h', 'z': 'top_z',
        'N': 'top_n', 'A': 'top_a', '/': 'dash', '-': 'g'
    }
    
    active_segs = char_map.get(char, '')
    
    # Render standard segments safely
    if active_segs == 'dot':
        draw.rectangle([x + w/2 - t, y + h - t, x + w/2, y + h], fill=color)
        return
        
    for seg, (sx, sy, sw, sh, is_vert) in segments.items():
        if seg in active_segs:
            draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_custom_string(draw, text, cx, cy, is_hz=False):
    """Renders customized massive text strings layout directly over gauge windows."""
    # Scale geometry based on industry standards
    digit_w = 40
    digit_h = 68
    thickness = 9
    spacing = 10
    
    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)
    
    # Multi-pass shadow system for maximum high-contrast separation
    for ox in [-2, 0, 2]:
        for oy in [-2, 0, 2]:
            curr_x = start_x + ox
            curr_y = start_y + oy
            bg_color = (0, 0, 0, 255) if (ox != 0 or oy != 0) else (255, 255, 255, 255)
            
            # Temporary single letter loop processing
            letter_x = curr_x
            for char in text:
                # Custom alphanumeric vector overrides
                if char in '0123456789.-':
                    draw_vector_digit(draw, letter_x, curr_y, char, digit_w, digit_h, thickness, bg_color)
                else:
                    # Clean vector backup blocks for unit labels (MW / Hz)
                    draw.rectangle([letter_x, curr_y + digit_h*0.3, letter_x + digit_w, curr_y + digit_h], fill=bg_color)
                    draw.text((letter_x + digit_w/2, curr_y + digit_h*0.6), char, fill=(0,0,0,255) if bg_color==(0,0,0,255) else (255,165,0,255), anchor="mm")
                letter_x += digit_w + spacing

def draw_digital_display(value, image_filename, is_frequency=False):
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Center target position coordinates inside the window area
        center_x = png_img.size[0] * 0.49
        center_y = png_img.size[1] * 0.835
        
        display_text = f"{value} H" if is_frequency else f"{value} M"
        
        # Draw custom vector text engine layout
        draw_custom_string(draw, display_text, center_x, center_y, is_hz=is_frequency)
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Setup persistent grid containers to fully eliminate flickering and page fading
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
        
        # Fetch active plant values
        u1_val = nctps_data.get("UNIT1", {}).get("MW", "N/A")
        u2_val = nctps_data.get("UNIT2", {}).get("MW", "N/A")
        u3_val = nctps_data.get("UNIT3", {}).get("MW", "N/A")
        hz_val = nctps_data.get("HZ", {}).get("HZ", "N/A")
        
        # Process Column 1 updates
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
            if img1:
                i1.image(img1, use_container_width=True)
                
        # Process Column 2 updates
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
            if img2:
                i2.image(img2, use_container_width=True)
                
        # Process Column 3 updates
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
            if img3:
                i3.image(img3, use_container_width=True)
                
        # Process Column 4 updates
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        if hz_val != "N/A":
            img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
            if img4:
                i4.image(img4, use_container_width=True)

except Exception as e:
    st.error(f"Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
