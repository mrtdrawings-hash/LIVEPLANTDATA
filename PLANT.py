import streamlit as st
import requests
import os
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
    Renders text cleanly centered over the blank square on the dial panel face.
    display_type options: 'mw', 'hz', 'total'
    """
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Center layout positioning
        center_x = base_img.size[0] * 0.485
        center_y = base_img.size[1] * 0.49

        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        # Color profile routing
        if display_type == "hz":
            text_color = (255, 235, 0, 255) # Warning Yellow
        elif display_type == "total":
            text_color = (0, 255, 127, 255) # High-visibility Spring Green for Total Load
        else:
            text_color = (0, 240, 255, 255) # Standard Cyan

        # Calculate bounding dimensions 
        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]

        draw.text((x, y), text_str, fill=text_color, font=font)
        return Image.alpha_composite(base_img, overlay)
    except Exception as e:
        st.error(f"Render Error on {image_filename}: {e}")
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Layout expansion: Configured 5 columns to cleanly track U1, U2, U3, Total, and HZ
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
                    pass # Ignore strings/N/A parameters dynamically
            
            total_val_str = f"{total_load:.1f}" if valid_units > 0 else "N/A"

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
                img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", display_type="mw")
                if img3:
                    slot3.image(img3, use_container_width=True)

            # Total MW Dial Execution
            if total_val_str != "N/A":
                img_total = draw_digital_display(total_val_str, "Gemini_T.jpg", display_type="total")
                if img_total:
                    slot4.image(img_total, use_container_width=True)

            if hz_val != "N/A":
                img4 = draw_digital_display(hz_val, "HZ.jpg", display_type="hz")
                if img4:
                    slot5.image(img4, use_container_width=True)
        else:
            st.error(f"Server returned status code {response.status_code}")

    except Exception as e:
        st.error(f"Live Telemetry Link Error: {e}")

live_panel()
