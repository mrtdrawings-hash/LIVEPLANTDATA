import streamlit as st
import requests
import time
import io
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

@st.cache_data
def load_digital_font(font_size):
    """Downloads a premium digital font directly into memory to avoid missing local font errors."""
    try:
        # Direct URL to a clean, open-source Digital-7 TrueType font file
        font_url = "https://github.com/thefontsproject/digital-7/raw/master/digital-7%20(mono).ttf"
        response = requests.get(font_url, timeout=5)
        if response.status_code == 200:
            return ImageFont.truetype(io.BytesIO(response.content), font_size)
    except Exception:
        pass
    return ImageFont.load_default()

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
        center_y = png_img.size[1] * 0.835
        
        # Set text and dynamic sizing based on gauge layout
        if is_frequency:
            display_text = f"{value} Hz"
            font_size = int(png_img.size[1] * 0.085)
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.105) # Increased size factor for massive presence
            
        text_color = (255, 255, 255, 255) # High-visibility solid white
        
        # Load the crisp vector digital font engine
        font = load_digital_font(font_size)
        
        # Heavy high-contrast drop shadow pass for clean separation from dark gauge areas
        for ax in [-2, -1, 0, 1, 2]:
            for ay in [-2, -1, 0, 1, 2]:
                draw.text((center_x + ax, center_y + ay), display_text, fill=(0, 0, 0, 255), font=font, anchor="mm")
                
        # Main premium foreground indicator text layer
        draw.text((center_x, center_y), display_text, fill=text_color, font=font, anchor="mm")
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

try:
    response = requests.get(url)
    if response.status_code == 200 and (nctps_data := response.json()):
        col1, col2, col3, col4 = st.columns(4)
        
        # Fetch data points explicitly to stay completely stable
        u1_val = nctps_data.get("UNIT1", {}).get("MW", "N/A")
        u2_val = nctps_data.get("UNIT2", {}).get("MW", "N/A")
        u3_val = nctps_data.get("UNIT3", {}).get("MW", "N/A")
        hz_val = nctps_data.get("HZ", {}).get("HZ", "N/A")
        
        # Render Column 1: Unit 1
        with col1:
            st.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
            if u1_val != "N/A":
                img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
                if img1:
                    st.image(img1, use_container_width=True)
                    
        # Render Column 2: Unit 2
        with col2:
            st.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
            if u2_val != "N/A":
                img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
                if img2:
                    st.image(img2, use_container_width=True)
                    
        # Render Column 3: Unit 3
        with col3:
            st.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
            if u3_val != "N/A":
                img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
                if img3:
                    st.image(img3, use_container_width=True)
                    
        # Render Column 4: Grid Frequency
        with col4:
            st.metric(label="Grid Frequency", value=f"{hz_val} Hz")
            if hz_val != "N/A":
                img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
                if img4:
                    st.image(img4, use_container_width=True)

except Exception as e:
    st.error(f"Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
