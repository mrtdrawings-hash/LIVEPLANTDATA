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
        # Load the base dial gauge image
        png_img = Image.open(image_filename).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        base_img = solid_bg.convert("RGBA")
        
        # 1. Use the built-in fallback system font (Guaranteed to exist everywhere)
        font = ImageFont.load_default()
        display_text = f" {value} Hz " if is_frequency else f" {value} MW "
        
        # 2. Render text onto a tiny temporary blank canvas
        try:
            bbox = font.getbbox(display_text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = 80, 16  # Safe fallback dimensions
            
        text_img = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        
        # Choose clear high-visibility colors
        # Vibrant Yellow for Frequency, Electric Cyan for MW values
        text_color = (255, 220, 0, 255) if is_frequency else (0, 230, 255, 255)
        
        # Draw a clean drop shadow outline underneath the text
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            text_draw.text((2 + dx, 2 + dy), display_text, fill=(0, 0, 0, 255), font=font)
        text_draw.text((2, 2), display_text, fill=text_color, font=font)
        
        # 3. Scale up the text layer cleanly using crisp layout interpolation
        if is_frequency:
            # Sized perfectly for the white frequency center dial ring
            target_w, target_h = int(tw * 2.8), int(th * 2.8)
            scaled_text = text_img.resize((target_w, target_h), Image.Resampling.NEAREST)
            
            # Mask out the old central text on the gauge
            overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
            mask_draw = ImageDraw.Draw(overlay)
            mask_draw.ellipse([png_img.size[0]*0.36, png_img.size[1]*0.44, png_img.size[0]*0.62, png_img.size[1]*0.56], fill=(255, 255, 255, 255))
            base_img = Image.alpha_composite(base_img, overlay)
            
            cx, cy = int(png_img.size[0] * 0.49), int(png_img.size[1] * 0.495)
        else:
            # Sized perfectly for the lower black digital dashboard boxes
            target_w, target_h = int(tw * 2.5), int(th * 2.8)
            scaled_text = text_img.resize((target_w, target_h), Image.Resampling.NEAREST)
            cx, cy = int(png_img.size[0] * 0.485), int(png_img.size[1] * 0.835)
            
        # 4. Paste the finalized high-visibility text back onto the dial face
        final_overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        past_x = cx - (target_w // 2)
        past_y = cy - (target_h // 2)
        final_overlay.paste(scaled_text, (past_x, past_y), scaled_text)
        
        return Image.alpha_composite(base_img, final_overlay)
    except Exception:
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Static UI placeholders to eliminate refreshing page flickers entirely
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
        
        u1_val = nctps_data.get("UNIT1", {}).get("MW", "N/A")
        u2_val = nctps_data.get("UNIT2", {}).get("MW", "N/A")
        u3_val = nctps_data.get("UNIT3", {}).get("MW", "N/A")
        hz_val = nctps_data.get("HZ", {}).get("HZ", "N/A")
        
        # Display Unit 1
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
            if img1:
                i1.image(img1, use_container_width=True)
                
        # Display Unit 2
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
            if img2:
                i2.image(img2, use_container_width=True)
                
        # Display Unit 3
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
            if img3:
                i3.image(img3, use_container_width=True)
                
        # Display Grid Frequency
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
