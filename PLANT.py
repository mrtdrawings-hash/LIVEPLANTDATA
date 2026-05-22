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
    Renders sharp, crisp industrial 7-segment digits with crisp flat edges
    and drop-shadow structure for high-contrast visibility.
    """
    t = thickness
    mid_y = h / 2
    
    # 7-Segment structural matrix parameters
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
        # Sharp high-visibility decimal block
        draw.rectangle([x + w/2 - t, y + h - 1.5*t, x + w/2 + t, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        # Crisp high-contrast shadow layer placement
        draw.rectangle([x + sx + 2, y + sy + 2, x + sx + sw + 2, y + sy + sh + 2], fill=(0, 0, 0, 220))
        # Crisp solid front text color layer placement
        draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_vector_string(draw, text, cx, cy, color):
    """Aligns and scales sharp digital strings precisely into the geometric center."""
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
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Centering layout coordinates at the exact middle of the images
        center_x = png_img.size[0] * 0.50
        center_y = png_img.size[1] * 0.50
        
        # Pure numeric string parsing
        display_text = f"{value}"
        
        # Caching-safe tracking flags to decide output hue attributes
        is_frequency = kwargs.get('is_frequency', False)
        if "HZ" in image_filename.upper() or "HZ" in value:
            is_frequency = True
            
        if is_frequency:
            text_color = (255, 235, 0,
