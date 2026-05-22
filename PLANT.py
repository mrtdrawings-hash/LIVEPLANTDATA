import streamlit as st
import requests
import time
import os
import math
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
            
            # --- DYNAMIC POINTER NEEDLE ENGINE FOR HZ ONLY ---
            try:
                val_float = float(value)
                # Keep within safe physical dial limits (45 to 55 Hz)
                val_float = max(45.0, min(55.0, val_float))
                
                # 50 Hz is straight up (90°). Total dial span is 240° over 10 units
                theta = (val_float - 50.0) * 24.0
                alpha = math.radians(90.0 - theta)
                
                w_img, h_img = png_img.size
                cx, cy = w_img / 2.0, h_img / 2.0
                radius = w_img / 2.0
                
                # Needle dimensions proportional to gauge face layout
                cap_radius = radius * 0.15
                pointer_length = radius * 0.75
                base_width = radius * 0.025
                
                # Tip coordinates of the needle
                tx = cx + pointer_length * math.cos(alpha)
                ty = cy - pointer_length * math.sin(alpha)
                
                # Base perpendicular alignment vectors
                perp_alpha1 = alpha + math.pi / 2.0
                perp_alpha2 = alpha - math.pi / 2.0
                
                bx1 = cx + cap_radius * math.cos(alpha) + base_width * math.cos(perp_alpha1)
                by1 = cy - cap_radius * math.sin(alpha) - base_width * math.sin(perp_alpha1)
                
                bx2 = cx + cap_radius * math.cos(alpha) + base_width * math.cos(perp_alpha2)
                by2 = cy - cap_radius * math.sin(alpha) - base_width * math.sin(perp_alpha2)
                
                # Draw vibrant high-contrast red needle body
                draw.polygon([(bx1, by1), (tx, ty), (bx2, by2)], fill=(255, 50, 50, 255))
                # Render crisp high-definition black borders for maximum clarity
                draw.line([(bx1, by1), (tx, ty)], fill=(0, 0, 0, 255), width=2)
                draw.line([(tx, ty), (bx2, by2)], fill=(0, 0, 0, 255), width=2)
                draw.line([(bx2, by2), (bx1, by1)], fill=(0, 0, 0, 255), width=2)
            except Exception:
                pass
            # --------------------------------------------------
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.085) 
            text_color = (0, 240, 255, 255) # Cyan
            
        # --- FIXED FONT ENGINE ADAPTED FROM DEMAND.PY ---
        font_loaded = False
        font = None
        
        # Try loading TrueType files from root context paths
        possible_paths = [
            "arialbd.ttf", 
            "./arialbd.ttf",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "arialbd.ttf")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    font_loaded = True
                    break
                except Exception:
                    pass
                    
        # Fallback processing architecture exactly matching DEMAND.py logic
        if not font_loaded:
            try:
                font = ImageFont.truetype("LiberationSans-Bold.ttf", font_size)
                font_loaded = True
            except IOError:
                pass
                
        if not font_loaded:
            base_font = ImageFont.load_default()
            try:
                # Forcefully scales the system layout so characters do not shrink on the web
                font = base_font.font_variant(size=font_size)
            except AttributeError:
                font = base_font
        # ------------------------------------------------------
            
        # Clear thick text outline border for high contrast readability
        for ax in [-3, -2, -1, 0, 1, 2, 3]:
            for ay in [-3, -2, -1, 0, 1, 2, 3]:
                if ax != 0 or ay != 0:
                    draw.text((center_x + ax, center_y + ay), display_text, fill=(0, 0, 0, 255), font=font, anchor="mm")
                    
        # Sharp foreground metric color layer
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
