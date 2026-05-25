import streamlit as st
import requests
import time
import os
from PIL import Image, ImageDraw

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ------------------------------------------------------------------
# SYSTEM PATH RESOLVER (Multi-Location Check)
# ------------------------------------------------------------------
def find_image_file(filename):
    """
    Checks multiple potential directories to find the absolute path of the image.
    This bypasses any virtual environment or streamlit cache folder redirection.
    """
    # Location 1: Where the script is saved
    script_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(script_dir_path):
        return script_dir_path
        
    # Location 2: Current working directory (where you typed the streamlit run command)
    cwd_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(cwd_path):
        return cwd_path

    # Location 3: Safe fallback if not found anywhere
    return None

# ------------------------------------------------------------------
# CACHING LAYER WITH SEAMLESS IMAGE LOADING
# ------------------------------------------------------------------
@st.cache_resource
def load_base_template(filename):
    """
    Finds, opens, and retains background assets in system RAM.
    If the file does not exist, returns a dynamically generated template
    to prevent NoneType errors.
    """
    abs_path = find_image_file(filename)
    try:
        if abs_path and os.path.exists(abs_path):
            png_img = Image.open(abs_path).convert("RGBA")
            solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
            solid_bg.paste(png_img, (0, 0), png_img)
            return solid_bg.convert("RGBA")
    except Exception:
        pass
    
    # Fallback Template: If file is missing or errors out, create a clean 400x250 panel in memory
    fallback = Image.new("RGBA", (400, 250), (20, 25, 35, 255))
    draw = ImageDraw.Draw(fallback)
    # Draw a subtle border line to indicate a placeholder panel
    draw.rectangle([0, 0, 399, 249], outline=(50, 60, 80, 255), width=3)
    
    # Text alert on the fallback panel helping you troubleshoot
    draw.text((20, 20), f"File Missing From Directory", fill=(255,100,100,255))
    draw.text((20, 45), f"Expected: {filename}", fill=(200,200,200,255))
    return fallback

# ------------------------------------------------------------------
# ORIGINAL VECTOR DIGIT CODES
# ------------------------------------------------------------------
def draw_custom_vector_digit(draw, x, y, char, w, h, thickness, color):
    t = thickness
    mid_y = h / 2
    
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
        draw.rectangle([x + w/2 - t, y + h - 1.5*t, x + w/2 + t, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_vector_string(draw, text, cx, cy, color):
    digit_w = 64       
    digit_h = 110       
    thickness = 15      
    spacing = 12       
    
    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)
    
    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color)
        curr_x += digit_w + spacing

def draw_digital_display(value, image_filename, **kwargs):
    # Guaranteed to return a valid PIL image canvas (either your file or a fallback block)
    base_img = load_base_template(image_filename)
        
    try:
        # Generate text overlay layer
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        center_x = base_img.size[0] * 0.50
        center_y = base_img.size[1] * 0.50
        
        display_text = f"{value}"
        is_frequency = kwargs.get('is_frequency', False)
        
        if "HZ" in image_filename.upper() or "HZ" in value:
            is_frequency = True
            
        if is_frequency:
            text_color = (255, 235, 0, 255)  # Vibrant Safety Yellow
        else:
            text_color = (0, 240, 255, 255)  # Electric Cyan
            
        draw_vector_string(draw, display_text, center_x, center_y, text_color)
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return base_img

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Permanent display layout configuration
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
                i1.image(img1, use_container_width=True, clamp=True)

        # UNIT 2
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
            if img2:
                i2.image(img2, use_container_width=True, clamp=True)

        # UNIT 3
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
            if img3:
                i3.image(img3, use_container_width=True, clamp=True)

        # GRID FREQUENCY
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        if hz_val != "N/A":
            img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
            if img4:
                i4.image(img4, use_container_width=True, clamp=True)

except Exception as e:
    st.error(f"Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
