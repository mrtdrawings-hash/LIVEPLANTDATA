import streamlit as st
import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

def draw_digital_display(value, image_filename, is_frequency=False):
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Exact digital display window centers
        center_x = png_img.size[0] * 0.485
        center_y = png_img.size[1] * 0.825
        
        if is_frequency:
            display_text = f"{value} Hz"
            font_size = int(png_img.size[1] * 0.095) 
            text_color = (0, 35, 102, 255)  # Royal Blue
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.085) 
            text_color = (0, 240, 255, 255) # Cyan
            
        # --- STREAMLIT CLOUD BULLETPROOF FONT ENGINE ---
        font = None
        # Explicitly checking root directory paths for deployed instances
        possible_paths = [
            "arialbd.ttf", 
            "./arialbd.ttf",
            os.path.join(os.path.dirname(__file__), "arialbd.ttf")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except IOError:
                    continue
                    
        # --- ADVANCED SEAMLESS LINUX SERVER FALLBACK ENGINE ---
        # If the server is strictly blocking custom files, we generate an ultra-bold 
        # pseudo-vector text block by over-sampling the coordinate offsets
        if font is None:
            font = ImageFont.load_default()
            # If we fall back to system default, we significantly increase the stroke
            # distribution matrix to manually build a bold, readable layout
            stroke_weight = range(-5, 6)
        else:
            stroke_weight = range(-3, 4)
        # ------------------------------------------------------
            
        # Heavy anti-aliased dark background shadow layer to bounce the color forward
        for ax in stroke_weight:
            for ay in stroke_weight:
                if ax != 0 or ay != 0:
                    draw.text((center_x + ax, center_y + ay), display_text, fill=(0, 0, 0, 255), font=font, anchor="mm")
                    
        # Crisp foreground metric color layer
        draw.text((center_x, center_y), display_text, fill=text_color, font=font, anchor="mm")
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

try:
    response = requests.get(url)
    if response.status_code == 200 and (nctps_data := response.json()):
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = [
            (col1, "UNIT1", "UNIT 1 Generation", "Gemini_U1.jpg", False),
            (col2, "UNIT2", "UNIT 2 Generation", "Gemini_U2.jpg", False),
            (col3, "UNIT3", "UNIT 3 Generation", "Gemini_U3.jpg", False),
            (col4, "HZ", "Grid Frequency", "HZ.jpg", True)
        ]
        
        for col, key, label, img_file, is_hz in metrics:
            with col:
                val = nctps_data.get(key, {}).get(key if is_hz else "MW", "N/A")
                st.metric(label=label, value=f"{val} {'Hz' if is_hz else 'MW'}")
                if val != "N/A":
                    img_out = draw_digital_display(val, img_file, is_frequency=is_hz)
                    if img_out:
                        st.image(img_out, use_container_width=True)
except Exception as e:
    st.error(f"Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
