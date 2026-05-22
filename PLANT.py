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
        
        # Set text and sizes based on gauge type (All use Crisp White Color)
        if is_frequency:
            display_text = f"{value} Hz"
            font_size = int(png_img.size[1] * 0.095) 
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.085) 
            
        text_color = (255, 255, 255, 255) # Clear White font color for everything
            
        # --- ROBUST SCALED BITMAP FONT SYSTEM ---
        # Loads default fallback font to prevent missing font errors on server environment
        default_font = ImageFont.load_default()
        
        # Calculate tiny bounding dimensions safely across all Pillow versions
        try:
            tw, th = draw.textsize(display_text, font=default_font)
        except AttributeError:
            bbox = draw.textbbox((0, 0), display_text, font=default_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
        tw = max(1, tw)
        th = max(1, th)
        
        # Render text with structural borders onto a micro temporary canvas
        pad = 4
        text_canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(text_canvas)
        
        # Thick dark stroke outline backdrop layers
        for ax in [-1, 0, 1]:
            for ay in [-1, 0, 1]:
                canvas_draw.text((pad + ax, pad + ay), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad, pad), display_text, fill=text_color, font=default_font)
        
        # Target dimensions scale map matching your UI layout proportion
        target_w = font_size * (tw / 10.0)
        target_h = font_size * (th / 10.0)
        
        # Scale micro canvas to final visual design size smoothly
        scaled_text = text_canvas.resize((int(target_w), int(target_h)), Image.Resampling.NEAREST)
        
        # Position and composite scaled text layer directly onto dashboard gauge center
        past_x = int(center_x - (target_w / 2.0))
        past_y = int(center_y - (target_h / 2.0))
        overlay.paste(scaled_text, (past_x, past_y), scaled_text)
        # ---------------------------------------------------------------------
                
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
