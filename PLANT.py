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
        
        # Set text and sizes based on gauge type (All use Crisp White Color)
        if is_frequency:
            display_text = f"{value} Hz"
            font_size = int(png_img.size[1] * 0.095) 
        else:
            display_text = f"{value} MW"
            font_size = int(png_img.size[1] * 0.085) 
            
        text_color = (255, 255, 255, 255) # Clear White font color for everything
            
        # --- ROBUST SCALED BITMAP FONT SYSTEM ---
        # Loads default fallback font to prevent missing font errors on server environment
        default_font = ImageFont.load_default()
        
        # Calculate tiny bounding dimensions safely across all Pillow versions
        try:
            tw, th = draw.textsize(display_text, font=default_font)
        except AttributeError:
            bbox = draw.textbbox((0, 0), display_text, font=default_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
        tw = max(1, tw)
        th = max(1, th)
        
        # Render text with structural borders onto a micro temporary canvas
        pad = 6  # Expanded padding for ultra-bold shadow distribution
        text_canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(text_canvas)
        
        # --- ULTRA-BOLD STROKE GENERATION ENGINE ---
        # Draw multiple multi-directional offset passes to simulate a bold, clean typeface
        for ax in [-2, -1, 0, 1, 2]:
            for ay in [-2, -1, 0, 1, 2]:
                canvas_draw.text((pad + ax, pad + ay), display_text, fill=text_color, font=default_font)
                
        # Draw thick dark stroke outline backdrop layers underneath to separate white text from dark background
        bg_canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(bg_canvas)
        for ax in
