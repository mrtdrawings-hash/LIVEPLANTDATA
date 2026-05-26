import streamlit as st
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS 1 LIVE MW DASHBOARD ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    paths_to_check = [os.path.join(os.path.dirname(os.path.abspath(__file__)), image_filename), 
                      os.path.join(os.getcwd(), image_filename), image_filename]
    target_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if not target_path: return None
    png_img = Image.open(target_path).convert("RGBA")
    solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
    solid_bg.paste(png_img, (0, 0), png_img)
    return solid_bg.convert("RGBA")

def get_scalable_font(font_size=135):
    # (Existing font logic remains unchanged)
    return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
    base_img = load_base_image(image_filename)
    if base_img is None: return None
    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        center_x, center_y = width * 0.485, height * 0.49
        
        # Draw Digital Text
        font = get_scalable_font(font_size=135)
        text_color = (0, 0, 0, 255) if display_type == "total" else (0, 240, 255, 255)
        draw.text((center_x, center_y), str(value), fill=text_color, font=font, anchor="mm")

        if display_type == "total":
            val = max(0.0, min(float(value), 750.0))
            mw_bp = [0.0, 75.0, 150.0, 225.0, 300.0, 375.0, 450.0, 525.0, 600.0, 675.0, 750.0]
            ang_bp = [145.0, 116.0, 86.0, 54.0, 24.0, 0.0, -24.0, -54.0, -86.0, -116.0, -145.0]
            
            # Interpolate angle
            angle = ang_bp[0]
            for i in range(len(mw_bp)-1):
                if mw_bp[i] <= val <= mw_bp[i+1]:
                    f = (val - mw_bp[i]) / (mw_bp[i+1] - mw_bp[i])
                    angle = ang_bp[i] + f * (ang_bp[i+1] - ang_bp[i])
            
            # Draw Pointer
            rad = math.radians(270.0 - angle)
            tip_x = width*0.5 + (width*0.37) * math.cos(rad)
            tip_y = height*0.5 - (width*0.37) * math.sin(rad)
            draw.line([(width*0.5, height*0.5), (tip_x, tip_y)], fill=(220, 35, 25, 255), width=8)

            # Draw Status LEDs (Red at 0, Green at 750)
            draw.ellipse([width*0.25-10, height*0.75-10, width*0.25+10, height*0.75+10], fill=(255, 0, 0))
            draw.ellipse([width*0.75-10, height*0.75-10, width*0.75+10, height*0.75+10], fill=(0, 255, 0))

        return Image.alpha_composite(base_img, overlay)
    except: return base_img

# Layout
c1, c2, c3, c4, c5 = st.columns(5)
slots = [c1.empty(), c2.empty(), c3.empty(), c4.empty(), c5.empty()]

@st.fragment(run_every=refresh_interval if auto_refresh else None)
def live_panel(s):
    try:
        data = requests.get(url, timeout=4).json()
        vals = [str(data.get(f"UNIT{i}", {}).get("MW", 0)) for i in range(1, 4)]
        total = sum(float(v) for v in vals)
        
        for i, (v, img) in enumerate(zip(vals, ["Gemini_U1.jpg", "Gemini_U2.jpg", "Gemini_U3.jpg"])):
            s[i].image(draw_digital_display(v, img), use_container_width=True)
        s[3].image(draw_digital_display(int(total), "Gemini_T.jpg", "total"), use_container_width=True)
    except: pass

live_panel(slots)
