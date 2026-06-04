import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import requests
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# --- 1. GLOBAL LAYOUT CONFIGURATION & CUSTOM STYLES ---
st.set_page_config(
    page_title="NCTPS Stage-I & Grid Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject clean global alignments, desktop/mobile styles, and a custom container for the login card
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    @media (max-width: 640px) {
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
        }
        h1 { font-size: 1.4rem !important; text-align: center; }
        h3 { font-size: 1.1rem !important; text-align: center; }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    }
    .stImage > img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 8px;
    }
    /* Login Screen Container Custom Style */
    .login-box {
        background-color: #1e222b;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #3e4451;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY CONTROL LAYER (AUTHENTICATION GATEWAY) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Render Login Gateway if Unauthorized
if not st.session_state.authenticated:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.title("🔒 SCADA Secure Access Portal")
        st.subheader("NCTPS Stage-I Operations Engine")
        
        with st.form("security_gateway_form", clear_on_submit=False):
            username_input = st.text_input("User Name", placeholder="Enter official mobile / registry ID")
            password_input = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Authenticate & Initialize Panel", use_container_width=True)
            
            if submit_btn:
                if username_input == "9445856695" and password_input == "Passme":
                    st.session_state.authenticated = True
                    st.rerun()  # Now running safely in the main execution tree to instantly clear the screen
                else:
                    st.error("🚨 Invalid Credentials. Please check your Username or Password.")
                    
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()  # Aborts execution of the dashboard until authenticated=True

# --- 3. ENVIRONMENT PATHS & UTILITIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))

@st.cache_data(show_spinner=False)
def load_base_image(image_filename):
    """Safely reads and standardizes local background dial images."""
    paths_to_check = [
        os.path.join(current_dir, image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename,
    ]
    target_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if not target_path:
        return None
    try:
        png_img = Image.open(target_path).convert("RGBA")
        solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
        solid_bg.paste(png_img, (0, 0), png_img)
        return solid_bg.convert("RGBA")
    except Exception:
        return None

def get_scalable_font(font_size=135):
    """Resolves cross-platform font rendering engines cleanly."""
    font_names = ["digital-7.ttf", "font.ttf"]
    for f_name in font_names:
        for folder in [current_dir, os.getcwd()]:
            p = os.path.join(folder, f_name)
            if os.path.exists(p):
                try: return ImageFont.truetype(p, font_size)
                except Exception: pass

    linux_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in linux_paths:
        if os.path.exists(path):
            try: return ImageFont.truetype(path, font_size)
            except Exception: pass

    try: return ImageFont.truetype("arialbd.ttf", font_size)
    except Exception: pass

    try: return ImageFont.load_default(size=font_size)
    except Exception: return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
    """Overlays clean digital typography over static gauge backgrounds."""
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None
    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        center_x = width * 0.485
        center_y = height * 0.49
        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        if display_type == "hz":
            text_color = (255, 255, 255, 255)
        elif display_type == "total":
            text_color = (0, 0, 0, 255)  
        else:
            text_color = (255, 255, 0, 255)

        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)
        return Image.alpha_composite(base_img, overlay)
    except Exception:
        return None

def draw_two_lines_on_gauge(img_path, lines, font_size=55, line_spacing=12):
    """Draws metrics inside central grid demand dials."""
    try:
        img = Image.open(img_path).convert("RGB")
    except Exception:
        return None
    draw = ImageDraw.Draw(img)
    font = get_scalable_font(font_size=font_size)
    img_w, img_h = img.size
    
    bbox1 = draw.textbbox((0, 0), lines[0], font=font)
    bbox2 = draw.textbbox((0, 0), lines[1], font=font)
    h1 = bbox1[3] - bbox1[1]
    h2 = bbox2[3] - bbox2[1]
    
    total_h = h1 + line_spacing + h
