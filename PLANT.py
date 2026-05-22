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
        # Load the dial background image layout cleanly
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        # Use fallback standard bitmap font engine to protect server environment execution
        font = ImageFont.load_default()
        display_text = f" {value} Hz " if is_frequency else f" {value} MW "
        
        # Calculate text boundaries
        try:
            bbox = font.getbbox(display_text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = 75, 15
            
        # Draw temporary vector text array onto micro-canvas matrix
        text_canvas = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(text_canvas)
        
        # Set text color configuration
        text_color = (255, 235, 0, 255) if is_frequency else (0, 240, 255, 255)
        
        # Generate clean drop-shadow outlines behind the text
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            canvas_draw.text((2 + dx, 2 + dy), display_text, fill=(0, 0, 0, 255), font=font)
        canvas_draw.text((2, 2), display_text, fill=text_color, font=font)
        
        # --- SCALE UP FONT SIZE TO MATCH THE TEMPLATE DISPLAY WINDOWS ---
        scale_w = int((tw + 4) * 3.8)
        scale_h = int((th + 4) * 4.2)
        scaled_text = text_canvas.resize((scale_w, scale_h), Image.Resampling.NEAREST)
        
        # Create an asset overlay layer
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        
        # --- POSITION THE READINGS EXACTLY AT THE GEOMETRIC CENTER ---
        center_x = png_img.size[0] * 0.50
        center_y = png_img.size[1] * 0.50
        
        past_x = int(center_x - (scale_w / 2.0))
        past_y = int(center_y - (scale_h / 2.0))
        overlay.paste(scaled_text, (past_x, past_y), scaled_text)
                
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Persistent layout infrastructure frame configuration (bypasses page flicker entirely)
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
        
        # UNIT 1 Generation Block
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
            if img1:
                i1.image(img1, use_container_width=True, clamp=True)

        # UNIT 2 Generation Block
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
            if img2:
                i2.image(img2, use_container_width=True, clamp=True)

        # UNIT 3 Generation Block
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
            if img3:
                i3.image(img3, use_container_width=True, clamp=True)

        # GRID FREQUENCY Dial Block
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
