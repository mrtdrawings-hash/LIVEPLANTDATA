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
# SYSTEM PATH RESOLVER
# ------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_absolute_path(filename):
    """Combines script directory with filename to guarantee absolute paths."""
    return os.path.join(SCRIPT_DIR, filename)

# ------------------------------------------------------------------
# CACHING LAYER WITH ERROR FALLBACK
# ------------------------------------------------------------------
@st.cache_resource
def load_base_template(filename):
    """
    Finds, opens, and retains background assets in system RAM.
    If the file does not exist, returns a dynamically generated template
    to prevent NoneType errors.
    """
    abs_path = get_absolute_path(filename)
    try:
        if os.path.exists(abs_path):
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

url = "https://nctps1-594d5
