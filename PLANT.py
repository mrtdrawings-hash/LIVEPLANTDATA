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

# --- 2. SECURITY CONTROL LAYER (AUTHENTICATION GATEWAY) ---
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
