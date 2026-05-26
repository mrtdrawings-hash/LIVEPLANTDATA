import streamlit as st
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont

# --- [Keep existing config and helper functions as provided previously] ---

def draw_digital_display(value, image_filename, display_type="mw"):
    base_img = load_base_image(image_filename)
    if base_img is None: return None

    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 1. Text Rendering
        center_x, center_y = width * 0.485, height * 0.49
        font = get_scalable_font(font_size=135)
        text_str = str(value)
        text_color = (0, 0, 0, 255) if display_type == "total" else (0, 240, 255, 255)
        
        bbox = draw.textbbox((0, 0), text_str, font=font)
        draw.text((center_x - (bbox[2]-bbox[0])/2, center_y - (bbox[3]-bbox[1])/2 - bbox[1]), 
                  text_str, fill=text_color, font=font)

        # 2. Pointer Rendering (Fixed Geometry)
        if display_type == "total":
            numeric_val = float(value) if value != "N/A" else 0.0
            numeric_val = max(0.0, min(numeric_val, 750.0))

            # Breakpoints: MW -> Clockwise degrees from Top (0 MW is 145 deg from top)
            mw_bp = [0.0, 75.0, 150.0, 225.0, 300.0, 375.0, 450.0, 525.0, 600.0, 675.0, 750.0]
            ang_bp = [145.0, 116.0, 86.0, 54.0, 24.0, 0.0, -24.0, -54.0, -86.0, -116.0, -145.0]

            angle_deg = ang_bp[0]
            for i in range(len(mw_bp) - 1):
                if mw_bp[i] <= numeric_val <= mw_bp[i+1]:
                    f = (numeric_val - mw_bp[i]) / (mw_bp[i+1] - mw_bp[i])
                    angle_deg = ang_bp[i] + f * (ang_bp[i+1] - ang_bp[i])
                    break
            
            # Radians relative to top (90 deg in unit circle is top)
            angle_rad = math.radians(90.0 - angle_deg)

            # Draw
            r_outer = width * 0.448
            p_len = width * 0.072
            pivot_x, pivot_y = width * 0.50, height * 0.50
            
            tip_x = pivot_x + (r_outer - p_len) * math.cos(angle_rad)
            tip_y = pivot_y - (r_outer - p_len) * math.sin(angle_rad)
            
            # Draw needle polygon...
            draw.polygon([(pivot_x, pivot_y), (tip_x, tip_y)], outline=(220, 35, 25, 255), width=8)

        return Image.alpha_composite(base_img, overlay)
    except Exception: return base_img
