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
            
        text_color = (255, 255, 255, 255) # Pure White font color
            
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
        
        # Create a temporary canvas for high-definition rendering
        pad = 12  
        text_canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(text_canvas)
        
        # --- SMOOTH ULTRA-BOLD HIGH-CONTRAST ENGINE ---
        # 1. Broad Black Outline Pass for clear separation from backgrounds (Dense matrix layout)
        offsets_bg = [
            (-2,-2), (-2,-1), (-2,0), (-2,1), (-2,2),
            (-1,-2), (-1,-1), (-1,0), (-1,1), (-1,2),
            (0,-2),  (0,-1),  (0,0),  (0,1),  (0,2),
            (1,-2),  (1,-1),  (1,0),  (1,1),  (1,2),
            (2,-2),  (2,-1),  (2,0),  (2,1),  (2,2)
        ]
        for ox, oy in offsets_bg:
            canvas_draw.text((pad + ox, pad + oy), display_text, fill=(0, 0, 0, 255), font=default_font)
            
        # 2. Multi-pass foreground layer distribution to form clean bold bodies
        offsets_fg = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for ox, oy in offsets_fg:
            canvas_draw.text((pad + ox, pad + oy), display_text, fill=text_color, font=default_font)
        
        # --- INCREASED FONT SIZE RATIO ENGINE ---
        # Lowering the division denominator (from 8.5 to 6.8) scales up the final font canvas size significantly
        target_w = font_size * (tw / 6.8)
        target_h = font_size * (th / 5.8)  # Scaled slightly higher for better vertical box coverage
        
        # Scale text up using LANCZOS antialiasing filter for crisp, smooth, premium fonts
        scaled_text = text_canvas.resize((int(target_w), int(target_h)), Image.Resampling.LANCZOS)
        
        # Position and paste scaled text layer onto the center coordinates
        past_x = int(center_x - (target_w / 2.0))
        past_y = int(center_y - (target_h / 2.0))
        overlay.paste(scaled_text, (past_x, past_y), scaled_text)
        # ---------------------------------------------------------------------
                
        return Image.alpha_composite(base_img, overlay)
