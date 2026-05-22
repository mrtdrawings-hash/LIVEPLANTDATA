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
        
        # Set text layout properties based on gauge type
        if is_frequency:
            display_text = f"{value} Hz"
            font_size = int(png_img.size[1] * 0.095) 
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.085) 
            
        text_color = (255, 255, 255, 255) # Pure White font color for all displays
            
        # --- ROBUST SCALED BITMAP FONT SYSTEM ---
        default_font = ImageFont.load_default()
        
        # Calculate bounding dimensions safely across all Pillow versions
        try:
            tw, th = draw.textsize(display_text, font=default_font)
        except AttributeError:
            bbox = draw.textbbox((0, 0), display_text, font=default_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
        tw = max(1, tw)
        th = max(1, th)
        
        # Create a temporary canvas for scaling
        pad = 10  
        text_canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(text_canvas)
        
        # --- COMPLETELY FLATTENED EXPLICIT BOLD OFFSET DRAWS ---
        # Draw background contrast outline borders explicitly to stay error-proof
        canvas_draw.text((pad - 3, pad - 3), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad - 3, pad), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad - 3, pad + 3), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad, pad - 3), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad, pad + 3), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad + 3, pad - 3), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad + 3, pad), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad + 3, pad + 3), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad - 2, pad - 2), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad + 2, pad + 2), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad - 2, pad + 2), display_text, fill=(0, 0, 0, 255), font=default_font)
        canvas_draw.text((pad + 2, pad - 2), display_text, fill=(0, 0, 0, 255), font=default_font)
            
        # Draw multiple foreground white layers directly to build a solid bold look
        canvas_draw.text((pad, pad), display_text, fill=text_color, font=default_font)
        canvas_draw.text((pad - 1, pad), display_text, fill=text_color, font=default_font)
        canvas_draw.text((pad + 1, pad), display_text, fill=text_color, font=default_font)
        canvas_draw.text((pad, pad - 1), display_text, fill=text_color, font=default_font)
        canvas_draw.text((pad, pad + 1), display_text, fill=text_color, font=default_font)
        canvas_draw.text((pad - 1, pad - 1), display_text, fill=text_color, font=default_font)
        canvas_draw.text((pad + 1, pad + 1), display_text, fill=text_color, font=default_font)
        
        # Target scaling dimensions matching your layout proportions
        target_w = font_size * (tw / 9.0)
        target_h = font_size * (th / 9.0)
        
        # Scale text up to make it look clean, crisp, and bold on screen
        scaled_text = text_canvas.resize((int(target_w), int(target_h)), Image.Resampling.NEAREST)
        
        # Position and paste scaled text layer onto the center coordinates
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
        
        # Fetch individual data points explicitly without looping patterns to maximize stability
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
