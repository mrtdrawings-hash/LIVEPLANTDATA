import streamlit as st
import requests
import time
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

def draw_digital_display(value, image_filename, is_frequency=False):
    # CHANGED: Read files directly from the repository root directory
    image_path = image_filename
    try:
        png_img = Image.open(image_path).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        center_x = png_img.size[0] * 0.485
        center_y = png_img.size[1] * 0.825
        
        if is_frequency:
            display_text = f"{value} Hz"
            font_size = int(png_img.size[1] * 0.082)
            text_color = (0, 35, 102, 255)  # Royal Blue
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.065)
            text_color = (0, 240, 255, 255) # Cyan
            
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
            
        for ax in [-2, -1, 0, 1, 2]:
            for ay in [-2, -1, 0, 1, 2]:
                draw.text((center_x + ax, center_y + ay), display_text, fill=text_color, font=font, anchor="mm")
                
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
