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

# Inject clean global alignments, desktop/mobile styles, and robust login branding fixes
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
    
    /* --- Login Window Premium UI Overrides --- */
    .login-container {
        max-width: 450px;
        margin: 40px auto;
        padding: 25px;
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
    }
    
    /* Dedicated Single Dark Heading Block */
    .tnpgcl-heading-box {
        background-color: #111827 !important;
        padding: 20px 10px !important;
        border-radius: 8px !important;
        text-align: center !important;
        margin: 15px 0px 25px 0px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);
    }
    
    .tnpgcl-heading-box h1 {
        color: #ffffff !important;
        margin: 0 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.4rem !important;
        letter-spacing: 3px !important;
    }

    /* Target the Streamlit Form Submit button directly to style it dark with white text */
    div[data-testid="stForm"] button[type="submit"] {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #111827 !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
        border-radius: 6px !important;
        transition: background-color 0.2s ease !important;
    }
    
    div[data-testid="stForm"] button[type="submit"]:hover {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border-color: #1f2937 !important;
    }
    
    div[data-testid="stForm"] button[type="submit"]:active {
        background-color: #030712 !important;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY CONTROL LAYER (AUTHENTICATION GATEWAY) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Render Login Gateway if Unauthorized
if not st.session_state.authenticated:
    # Use HTML wrapping inside a singular column layout to eliminate rogue markdown container blocks
    _, main_wrapper_col, _ = st.columns([1, 1.8, 1])
    
    with main_wrapper_col:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # 1. Corporate Branded Logo Rendering
        logo_filename = "TNPGCL LOGO.jpg"
        if os.path.exists(logo_filename):
            st.image(logo_filename, width=150)
        else:
            # Fallback for alternative directory mapping configurations
            fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), logo_filename)
            if os.path.exists(fallback_path):
                st.image(fallback_path, width=150)
            else:
                st.warning("⚠️ Company logo asset ('TNPGCL LOGO.jpg') not detected in the root directory hierarchy.")
        
        # 2. Crisp Single Solid Dark Branding Header
        st.markdown('<div class="tnpgcl-heading-box"><h1>TNPGCL</h1></div>', unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center; color: #1e293b; margin-top: 0;'>🔒 SCADA Secure Access Portal</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.95rem; margin-bottom: 20px;'>NCTPS Stage-I Operations Engine</p>", unsafe_allow_html=True)
        
        # 3. Interactive Login Form Block
        with st.form("security_gateway_form", clear_on_submit=False):
            username_input = st.text_input("User Name", placeholder="Enter official mobile / registry ID")
            password_input = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Authenticate & Initialize Panel", use_container_width=True)
            
            if submit_btn:
                if username_input == "9445856695" and password_input == "Passme":
                    st.session_state.authenticated = True
                else:
                    st.error("🚨 Invalid Credentials
