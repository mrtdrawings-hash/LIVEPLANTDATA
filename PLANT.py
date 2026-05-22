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

def draw_vector_string(draw, text, cx, cy, color, is_frequency=False):
    """Aligns and scales digital strings precisely into target display windows."""
    # Scale up geometry metrics for high visibility
    digit_w = 28 if is_frequency else 26
    digit_h = 50 if is_frequency else 46
    thickness = 7 if is_frequency else 6
    spacing = 6
    
    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)
    
    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color)
        else:
            # High-visibility vector letter configurations
            if char == 'M':
                draw.rectangle([curr_x, start_y, curr_x + 6, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 6, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y, curr_x + digit_w, start_y + 6], fill=color)
                draw.rectangle([curr_x + digit_w/2 - 3, start_y, curr_x + digit_w/2 + 3, start_y + digit_h], fill=color)
            elif char == 'W':
                draw.rectangle([curr_x, start_y, curr_x + 6, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 6, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 6, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w/2 - 3, start_y + 15, curr_x + digit_w/2 + 3, start_y + digit_h], fill=color)
            elif char == 'H':
                draw.rectangle([curr_x, start_y, curr_x + 6, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 6, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y + digit_h/2 - 3, curr_x + digit_w, start_y + digit_h/2 + 3], fill=color)
            elif char == 'z':
                draw.rectangle([curr_x, start_y + 14, curr_x + digit_w, start_y + 20], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 6, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + 6, start_y + 20, curr_x + digit_w - 6, start_y + digit_h - 6], fill=color)
        curr_x += digit_w + spacing

def draw_digital_display(value, image_filename, is_frequency=False):
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img,
