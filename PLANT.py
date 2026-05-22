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
    try:
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Centering positions for the black display cutout boxes
        center_x = png_img.size[0] * 0.49
        center_y = png_img.size[1] * 0.835
        
        # Apply high-contrast text configurations
        if is_frequency:
            display_text = f"{value} Hz"
            text_color = (255, 235, 0, 255)  # Vibrant Yellow text
            font_size = 85                    # Large readable font size
        else:
            display_text = f"{value} MW"
            text_color = (0, 240, 255, 255) # Electric Cyan text
            font_size = 90                    # Extra large readable font size
            
        # Load the default Linux server vector bold font structure
        try:
            font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
        
        # Heavy multi-layered silhouette border to separate text from background
        for ox in [-3, -2, -1, 0, 1, 2, 3]:
            for oy in [-3, -2, -1, 0, 1, 2, 3]:
                if ox != 0 or oy != 0:
                    draw.text((center_x + ox, center_y + oy), display_text, fill=(0, 0, 0, 255), font=font, anchor="mm")
                    
        # Crisp foreground indicator value layer placement
        draw.text((center_x, center_y), display_text, fill=text_color, font=font, anchor="mm")
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Permanent display layout blocks to stop page flickers
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
        
        # Explicit data parsing values
        u1_val = nctps_data.get("UNIT1", {}).get("MW", "N/A")
        u2_val = nctps_data.get("UNIT2", {}).get("MW", "N/A")
        u3_val = nctps_data.get("UNIT3", {}).get("MW", "N/A")
        hz_val = nctps_data.get("HZ", {}).get("HZ", "N/A")
        
        # Render Column 1
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
            if img1:
                i1.image(img1, use_container_width=True)
                
        # Render Column 2
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
            if img2:
                i2.image(img2, use_container_width=True)
                
        # Render Column 3
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
            if img3:
                i3.image(img3, use_container_width=True)
                
        # Render Column 4
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
