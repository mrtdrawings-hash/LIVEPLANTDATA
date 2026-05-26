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
    paths_to_check = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), image_filename),
        os.path.join(os.getcwd(), image_filename),
        image_filename,
    ]
    target_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if not target_path:
        return None

    png_img = Image.open(target_path).convert("RGBA")
    solid_bg = Image.new("RGB", png_img.size, (255, 255, 255))
    solid_bg.paste(png_img, (0, 0), png_img)
    return solid_bg.convert("RGBA")

def get_scalable_font(font_size=135):
    """
    Safely loads a clean, scalable font across both local machines and 
    Linux-based web servers (like Streamlit Cloud).
    """
    custom_font_name = "digital-7.ttf"
    paths_to_check = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), custom_font_name),
        os.path.join(os.getcwd(), custom_font_name),
        custom_font_name
    ]
    font_path = next((p for p in paths_to_check if os.path.exists(p)), None)
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass

    linux_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for path in linux_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                pass

    windows_paths = [
        "arialbd.ttf",       
        "trebucbd.ttf",     
        "consola.ttf"       
    ]
    for font_name in windows_paths:
        try:
            return ImageFont.truetype(font_name, font_size)
        except Exception:
            pass

    try:
        return ImageFont.load_default(size=font_size)
    except Exception:
        return ImageFont.load_default()

def draw_digital_display(value, image_filename, display_type="mw"):
    """
    Renders text centered over the panel face and handles a precisely calibrated
    overhead rim-mounted sweeping pointer exclusively for the Total MW dial.
    """
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Center positioning for text
        center_x = width * 0.485
        center_y = height * 0.49

        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        # Color profile routing
        if display_type == "hz":
            text_color = (255, 235, 0, 255)  # Warning Yellow
        elif display_type == "total":
            text_color = (0, 0, 0, 255)      # Crisp Solid Black for White Dial Face
        else:
            text_color = (0, 240, 255, 255)  # Standard Cyan for Units 1, 2, 3

        # Calculate text bounding dimensions and draw string safely in the center
        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)

        # --- EXCLUSIVE CALIBRATED OVERHEAD POINTER LOGIC FOR TOTAL MW DIAL ---
        if display_type == "total":
            try:
                numeric_val = float(value)
            except ValueError:
                numeric_val = 0.0

            # Limit values within the dial scope (0 to 750 MW)
            numeric_val = max(0.0, min(numeric_val, 750.0))

            # Non-linear breakpoint mapping arrays for explicit tick matching
            mw_breakpoints = [0, 75, 150, 225, 300, 375, 450, 525, 600, 675, 750]
            angle_breakpoints = [223, 193, 163, 131, 99, 66, 34, 2, -30, -62, -93]

            # Find the segment the current MW reading falls into
            angle_deg = angle_breakpoints[0]
            for i in range(len(mw_breakpoints) - 1):
                if mw_breakpoints[i] <= numeric_val <= mw_breakpoints[i+1]:
                    # Linear interpolation within this specific segment
                    mw_start = mw_breakpoints[i]
                    mw_end = mw_breakpoints[i+1]
                    ang_start = angle_breakpoints[i]
                    ang_end = angle_breakpoints[i+1]
                    
                    fraction = (numeric_val - mw_start) / (mw_end - mw_start)
                    angle_deg = ang_start + fraction * (ang_end - ang_start)
                    break
            
            angle_rad = math.radians(angle_deg)

            # Outer track baseline radius alignment configuration
            outer_rim_radius = width * 0.415
            pointer_length = width * 0.085
            base_width = width * 0.016

            # Outer anchor base point
            pivot_x = center_x + outer_rim_radius * math.cos(angle_rad)
            pivot_y = center_y - outer_rim_radius * math.sin(angle_rad)

            # Inward pointing arrow tip marker coord calculations
            tip_x = center_x + (outer_rim_radius - pointer_length) * math.cos(angle_rad)
            tip_y = center_y - (outer_rim_radius - pointer_length) * math.sin(angle_rad)

            # Wedge geometry construction variables
            perp_l = angle_rad + (math.pi / 2)
            perp_r = angle_rad - (math.pi / 2)

            base_l_x = pivot_x + base_width * math.cos(perp_l)
            base_l_y = pivot_y - base_width * math.sin(perp_l)
            base_r_x = pivot_x + base_width * math.cos(perp_r)
            base_r_y = pivot_y - base_width * math.sin(perp_r)

            # Draw top hanging arrow marker (High-visibility crimson red)
            draw.polygon(
                [(base_l_x, base_l_y), (tip_x, tip_y), (base_r_x, base_r_y)],
                fill=(235, 40, 30, 255)
            )

            # Clean micro-rivet base cap on the track line
            cap_radius = width * 0.008
            draw.ellipse(
                [pivot_x - cap_radius, pivot_y - cap_radius, pivot_x + cap_radius, pivot_y + cap_radius],
                fill=(90, 90, 90, 255)
            )

        return Image.alpha_composite(base_img, overlay)
    except Exception as e:
        st.error(f"Render Error on {image_filename}: {e}")
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Layout framework: Configured 5 columns to track U1, U2, U3, Total, and HZ
col1, col2, col3, col4, col5 = st.columns(5)
slot1 = col1.empty()
slot2 = col2.empty()
slot3 = col3.empty()
slot4 = col4.empty()
slot5 = col5.empty()

@st.fragment(run_every=refresh_interval if auto_refresh else None)
def live_panel():
    try:
        response = requests.get(url, timeout=4)

        if response.status_code == 200:
            nctps_data = response.json() or {}

            u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
            u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
            u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
            hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))

            # Calculate total generation load dynamically
            total_load = 0.0
            valid_units = 0

            for val in [u1_val, u2_val, u3_val]:
                try:
                    total_load += float(val)
                    valid_units += 1
                except ValueError:
                    pass  # Safely ignore missing data parameters
            
            # Formatted to standard whole integer string to strip out .0 decimal fractions
            total_val_str = str(int(total_load)) if valid_units > 0 else "N/A"

            # Render UI slots
            if u1_val != "N/A":
                img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", display_type="mw")
                if img1:
                    slot1.image(img1, use_container_width=True)

            if u2_val != "N/A":
                img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", display_type="mw")
                if img2:
                    slot2.image(img2, use_container_width=True)

            if u3_val != "N/A":
                img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", display_type="
