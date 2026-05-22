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
            
        text_color = (255, 255, 255, 255) # White font color for all displays
            
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
        pad = 6  
        text_canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(text_canvas)
        
        # --- FIXED SYNTAX: FLAT EXTRA-BOLD BORDER & SHADOW DROPS ---
        # 1. Thick Black Outline Pass for clear background contrast separation
        offsets_bg = [(-3,-3), (-3,0), (-3,3), (0,-3), (0,3), (3,-3), (3,0), (3,3), (-2,-2), (2,2), (-2,2), (2,-2)]
        for ox, oy in offsets_bg:
            canvas_draw.text((pad + ox, pad + oy), display_text, fill=(0, 0, 0, 255), font=default_font)
            
        # 2. Multi-layered White Pass to simulate a bold font weight beautifully
        offsets_fg = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]
        for ox, oy in offsets_fg:
            canvas_draw.text((pad + ox, pad + oy), display_text, fill=text_color, font=default_font)
        
        # Target scaling map dimensions matching your layout proportions
        target_w = font_size * (tw / 9.0)
        target_h = font_size * (th / 9.0)
        
        # Scale text up to make it look clean, crisp, and readable on screen
        scaled_text = text_canvas.resize((int(target_w), int(target_h)), Image.Resampling.NEAREST)
        
        # Position and paste scaled text layer onto the center coordinates
        past_x = int(center_x - (target_w / 2.0))
        past_y = int(center_y - (target_h / 2.0))
        overlay.paste(scaled_text, (past_x, past_y), scaled_text)
        # ---------------------------------------------------------------------
