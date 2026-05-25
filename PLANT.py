import streamlit as st
import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NORTH CHENNAI THERMAL POWER STATION 1 LIVE MW ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ------------------------------------------------------------------
# TAHOMA TRUE TYPE FONT ENGINE LOGIC
# ------------------------------------------------------------------
def get_tahoma_font(font_size):
    """
    Locates and loads Tahoma font across Windows and Linux (Streamlit Cloud) envs.
    """
    # Common system font paths for Tahoma
    possible_paths = [
        "C:\\Windows\\Fonts\\tahoma.ttf",          # Windows Local
        "C:\\Windows\\Fonts\\tahomabd.ttf",        # Windows Bold Local
        "/usr/share/fonts/truetype/tahoma/tahoma.ttf", # Linux/Cloud standard
        "tahoma.ttf"                               # App root directory
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
                
    # Fallback to default engine font if Tahoma isn't installed anywhere on the host system
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def draw_digital_display(value, image_filename, is_frequency=False):
    paths_to_check = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename
    ]
    
    target_path = None
    for p in paths_to_check:
        if os.path.exists(p):
            target_path = p
            break
            
    if not target_path:
        return None

    try:
        png_img = Image.open(target_path).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Determine Color
        if is_frequency or "HZ" in image_filename.upper():
            text_color = (255, 235, 0, 255)  # Yellow
            font_size = 110                  # Big, crisp font scale for Hz
        else:
            text_color = (0, 240, 255, 255)  # Cyan
            font_size = 135                  # Big, crisp font scale for MW
            
        # Load Tahoma font dynamically
        font = get_tahoma_font(font_size)
        
        # Calculate text boundaries for dynamic centering
        text_str = str(value)
        if font:
            # Get text bounding box dimensions: (left, top, right, bottom)
            bbox = draw.textbbox((0, 0), text_str, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        else:
            text_w, text_h = 150, 80 # Generic fallbacks
            
        # Calculate precise canvas placements
        center_x = (png_img.size[0] - text_w) / 2
        # Offset adjusted slightly upward to perfectly mirror your dial configurations
        center_y = ((png_img.size[1] - text_h) / 2) - (text_h * 0.15) 
        
        # Render clean true type font directly onto the layout
        draw.text((center_x, center_y), text_str, fill=text_color, font=font)
        
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

# ------------------------------------------------------------------
# LAYOUT FRAME SETUP
# ------------------------------------------------------------------
url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

col1, col2, col3, col4 = st.columns(4)

with col1:
    i1 = st.empty()
with col2:
    i2 = st.empty()
with col3:
    i3 = st.empty()
with col4:
    i4 = st.empty()

try:
    response = requests.get(url, timeout=4)
    if response.status_code == 200 and (nctps_data := response.json()):
        
        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))
        
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
            if img1:
                i1.image(img1, use_container_width=True)

        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
            if img2:
                i2.image(img2, use_container_width=True)

        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
            if img3:
                i3.image(img3, use_container_width=True)

        if hz_val != "N/A":
            img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
            if img4:
                i4.image(img4, use_container_width=True)

except Exception as e:
    st.error(f"Live Telemetry Link Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
