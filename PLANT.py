import streamlit as st
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont

# ... [Keep load_base_image and get_scalable_font functions as they were] ...

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

        # 2. Pointer and LED Rendering
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
            
            # Draw Pointer
            angle_rad = math.radians(90.0 - angle_deg)
            r_outer, p_len = width * 0.448, width * 0.072
            pivot_x, pivot_y = width * 0.50, height * 0.50
            tip_x = pivot_x + (r_outer - p_len) * math.cos(angle_rad)
            tip_y = pivot_y - (r_outer - p_len) * math.sin(angle_rad)
            draw.line([(pivot_x, pivot_y), (tip_x, tip_y)], fill=(220, 35, 25, 255), width=8)

            # Draw Status LEDs at bottom (Red at 0 MW, Green at 750 MW)
            led_radius = width * 0.015
            # Red LED Position (Near 0 MW)
            draw.ellipse([width*0.28-led_radius, height*0.78-led_radius, width*0.28+led_radius, height*0.78+led_radius], fill=(255, 0, 0))
            # Green LED Position (Near 750 MW)
            draw.ellipse([width*0.72-led_radius, height*0.78-led_radius, width*0.72+led_radius, height*0.78+led_radius], fill=(0, 255, 0))

        return Image.alpha_composite(base_img, overlay)
    except Exception as e:
        st.error(f"Render Error: {e}")
        return base_img

# ... [Keep the rest of your live_panel function as it was] ...
