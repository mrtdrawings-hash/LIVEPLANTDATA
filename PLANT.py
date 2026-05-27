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

    windows_paths = ["arialbd.ttf", "trebucbd.ttf", "consola.ttf"]
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
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        width, height = base_img.size
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # High visibility absolute central placement
        center_x = width * 0.485
        center_y = height * 0.49

        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        if display_type == "hz":
            text_color = (255, 235, 0, 255)
        elif display_type == "total":
            text_color = (0, 0, 0, 255)  # Clean sharp black contrast over white background
        else:
            text_color = (0, 240, 255, 255)

        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]
        draw.text((x, y), text_str, fill=text_color, font=font)

        # --- NON-LINEAR PIECEWISE CO-ORDINATE SYSTEM FOR TOTAL MW DIAL ---
        if display_type == "total":
            try:
                numeric_val = float(value)
            except ValueError:
                numeric_val = 0.0

            numeric_val = max(0.0, min(numeric_val, 750.0))

            # Symmetric absolute frame alignment center positions
            dial_center_x = width * 0.50
            dial_center_y = height * 0.50

            # True Physical Breakpoints calibrated directly against the image layout
            # True Physical Breakpoints calibrated for a 300-degree sweep
            # 0 MW = 240 degrees, 750 MW = -60 degrees
            mw_bp = [0.0, 75.0, 150.0, 225.0, 300.0, 375.0, 450.0, 525.0, 600.0, 675.0, 750.0]
            ang_bp = [240.0, 210.0, 180.0, 150.0, 120.0, 90.0, 60.0, 30.0, 0.0, -30.0, -60.0]

            angle_deg = ang_bp[0]
            for i in range(len(mw_bp) - 1):
                if mw_bp[i] <= numeric_val <= mw_bp[i+1]:
                    fraction = (numeric_val - mw_bp[i]) / (mw_bp[i+1] - mw_bp[i])
                    angle_deg = ang_bp[i] + fraction * (ang_bp[i+1] - ang_bp[i])
                    break
            
            # Map standard unit orientation tracking space
            angle_rad = math.radians(270.0 - angle_deg)

            # Sizing matrices tracking along the copper border frame
            outer_rim_radius = width * 0.448
            pointer_length = width * 0.072
            base_width = width * 0.015

            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            # Outer rim baseline contact tracks
            pivot_x = dial_center_x + outer_rim_radius * cos_a
            pivot_y = dial_center_y + outer_rim_radius * sin_a

            # Sharp inner-pointing arrow apex definitions
            tip_x = dial_center_x + (outer_rim_radius - pointer_length) * cos_a
            tip_y = dial_center_y + (outer_rim_radius - pointer_length) * sin_a

            perp_l = angle_rad + (math.pi / 2.0)
            perp_r = angle_rad - (math.pi / 2.0)

            base_l_x = pivot_x + base_width * math.cos(perp_l)
            base_l_y = pivot_y + base_width * math.sin(perp_l)
            base_r_x = pivot_x + base_width * math.cos(perp_r)
            base_r_y = pivot_y + base_width * math.sin(perp_r)

            # Render structured wedge indicator (Deep Red)
            draw.polygon(
                [(base_l_x, base_l_y), (tip_x, tip_y), (base_r_x, base_r_y)],
                fill=(220, 35, 25, 255)
            )

            # Alignment hub accent cap rivet
            cap_r = width * 0.007
            draw.ellipse(
                [pivot_x - cap_r, pivot_y - cap_r, pivot_x + cap_r, pivot_y + cap_r],
                fill=(70, 70, 70, 255)
            )

        return Image.alpha_composite(base_img, overlay)
    except Exception as e:
        st.error(f"Render Error on {image_filename}: {e}")
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

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

            total_load = 0.0
            valid_units = 0
            for val in [u1_val, u2_val, u3_val]:
                try:
                    total_load += float(val)
                    valid_units += 1
                except ValueError:
                    pass
            
            total_val_str = str(int(total_load)) if valid_units > 0 else "N/A"

            if u1_val != "N/A":
                img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", display_type="mw")
                if img1:
                    slot1.image(img1, use_container_width=True)

            if u2_val != "N/A":
                img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", display_type="mw")
                if img2:
                    slot2.image(img2, use_container_width=True)

            if u3_val != "N/A":
                img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", display_type="mw")
                if img3:
                    slot3.image(img3, use_container_width=True)

            if total_val_str != "N/A":
                img_total = draw_digital_display(total_val_str, "Gemini_T.jpg", display_type="total")
                if img_total:
                    slot4.image(img_total, use_container_width=True)

            if hz_val != "N/A":
                img4 = draw_digital_display(hz_val, "HZ.jpg", display_type="hz")
                if img4:
                    slot5.image(img4, use_container_width=True)
        else:
            st.error(f"Server error: {response.status_code}")
    except Exception as e:
        st.error(f"Telemetry Link Error: {e}")

live_panel()
