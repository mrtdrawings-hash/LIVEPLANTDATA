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
        draw.rectangle([x + w/2 - t, y + h - t, x + w/2 + t, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_vector_string(draw, text, cx, cy, color):
    digit_w = 34
    digit_h = 58
    thickness = 8
    spacing = 8
    
    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)
    
    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color)
        else:
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
                draw.rectangle([curr_x, start_y + 12, curr_x + digit_w, start_y + 18], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 6, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + 6, start_y + 18, curr_x + digit_w - 6, start_y + digit_h - 6], fill=color)
        curr_x += digit_w + spacing

def draw_digital_display(value, image_filename, is_frequency=False):
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        if is_frequency:
            center_x = png_img.size[0] * 0.495
            center_y = png_img.size[1] * 0.495
            display_text = f"{value} Hz"
            text_color = (255, 235, 0, 255)
            draw.ellipse([center_x - 70, center_y - 35, center_x + 70, center_y + 35], fill=(255, 255, 255, 255))
        else:
            center_x = png_img.size[0] * 0.485
            center_y = png_img.size[1] * 0.835
            display_text = f"{value} MW"
            text_color = (0, 240, 255, 255)
            
        draw_vector_string(draw, display_text, center_x, center_y, text_color)
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

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
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg")
            if img1:
                i1.image(img1, use_container_width=True, clamp=True)

        # UNIT 2
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg")
            if img2:
                i2.image(img2, use_container_width=True, clamp=True)

        # UNIT 3
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg")
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
