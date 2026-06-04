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

# Inject CSS to remove default Streamlit spacing, clean duplicate elements, and fix themes
st.markdown("""
    <style>
    /* Global Overrides */
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
    
    /* Centered Logo Layout Styling */
    .logo-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: -10px;
    }
    .logo-wrapper img {
        border-radius: 50%;
        object-fit: contain;
    }

    /* Fixed Dark Rectangle styling with zero top-margins to eliminate duplicate headers */
    .tnpgcl-header-panel {
        background-color: #111622 !important;
        padding: 22px 10px !important;
        border-radius: 10px !important;
        text-align: center !important;
        margin: 20px 0px 20px 0px !important;
        border: 1px solid #232a3b;
    }
    
    .tnpgcl-header-panel h1 {
        color: #ffffff !important;
        margin: 0 !important;
        padding: 0 !important;
        font-family: 'Arial Black', Gadget, sans-serif !important;
        font-weight: 900 !important;
        font-size: 2.5rem !important;
        letter-spacing: 4px !important;
    }

    /* Button Styling - Forces strict Dark Background with White Text */
    div[data-testid="stForm"] button[type="submit"] {
        background-color: #111622 !important;
        color: #ffffff !important;
        border: 1px solid #232a3b !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        border-radius: 6px !important;
        font-size: 1rem !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stForm"] button[type="submit"]:hover {
        background-color: #1c2336 !important;
        color: #ffffff !important;
        border-color: #3b4766 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENVIRONMENT PATHS & UTILITIES (Moved Up to Fix NameError) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))

# --- 3. SECURITY CONTROL LAYER (AUTHENTICATION GATEWAY) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Centered design structural grid layout
    _, login_grid_col, _ = st.columns([1, 1.2, 1])
    
    with login_grid_col:
        # 1. Render Logo directly using absolute path checks
        logo_asset_name = "TNPGCL LOGO.jpg"
        logo_located = False
        target_logo_path = ""
        
        for p in [logo_asset_name, os.path.join(current_dir, logo_asset_name), os.path.join(os.getcwd(), logo_asset_name)]:
            if os.path.exists(p):
                target_logo_path = p
                logo_located = True
                break
                
        if logo_located:
            st.markdown('<div class="logo-wrapper">', unsafe_allow_html=True)
            st.image(target_logo_path, width=140)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. Singular Dark Heading Block containing White Font
        st.markdown('<div class="tnpgcl-header-panel"><h1>TNPGCL</h1></div>', unsafe_allow_html=True)
        
        # 3. Form Input fields 
        with st.form("security_gateway_form", clear_on_submit=False):
            st.markdown("<h3 style='text-align: center; margin-top: 0; color: #1f2937;'>🔒 SCADA Secure Access Portal</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #6b7280; font-size: 0.9rem; margin-bottom: 20px;'>NCTPS Stage-I Operations Engine</p>", unsafe_allow_html=True)
            
            username_input = st.text_input("User Name", placeholder="Enter official mobile / registry ID")
            password_input = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Authenticate & Initialize Panel")
            
            if submit_btn:
                if username_input == "9445856695" and password_input == "Passme":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("🚨 Invalid Credentials. Please verify inputs.")
                    
    st.stop()

# --- 4. DATA PROCESSING & RENDERING ENGINE ---
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
        draw = ImageDraw.
