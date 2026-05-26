import streamlit as st
import requests
import os
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NORTH CHENNAI THERMAL POWER STATION 1 LIVE MW ⚡")

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
    # 1. Look for a custom digital font if you uploaded one to your repository
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

    # 2. Linux server standard fallback paths (Streamlit Cloud environment)
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

    # 3. Windows standard local fallback paths
    windows_paths = [
        "arialbd.ttf",       # Arial Bold
        "trebucbd.ttf",     # Trebuchet MS Bold
        "consola.ttf"       # Consolas
    ]
    for font_name in windows_paths:
        try:
            return ImageFont.truetype(font_name, font_size)
        except Exception:
            pass

    # 4. Fallback safe layout scaling
    try:
        return ImageFont.load_default(size=font_size)
    except Exception:
        return ImageFont.load_default()

def draw_digital_display(value, image_filename, is_frequency=False):
    base_img = load_base_image(image_filename)
    if base_img is None:
        return None

    try:
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # ADJUSTED: Shifted center_y from 0.515 to 0.49 to move text UP
        center_x = base_img.size[0] * 0.50
        center_y = base_img.size[1] * 0.49

        # INCREASED: Font size bumped from 95 to 135 to fill the box
        font = get_scalable_font(font_size=135)
        text_str = str(value)
        
        # Color profiling
        text_color = (255, 235, 0, 255) if (is_frequency or "HZ" in image_filename.upper()) else (0, 240, 255, 255)

        # Calculate bounding dimensions 
        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Calculate exact center positions
        x = center_x - (text_w / 2)
        y = center_y - (text_h / 2) - bbox[1]

        draw.text((x, y), text_str, fill=text_color, font=font)
        return Image.alpha_composite(base_img, overlay)
    except Exception as e:
        st.error(f"Render Error: {e}")
        return None

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

col1, col2, col3, col4 = st.columns(4)
slot1 = col1.empty()
slot2 = col2.empty()
slot3 = col3.empty()
slot4 = col4.empty()

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

            if u1_val != "N/A":
                img1 = draw_digital_display(u1_val, "Gemini_U1.jpg", is_frequency=False)
                if img1:
                    slot1.image(img1, use_container_width=True)

            if u2_val != "N/A":
                img2 = draw_digital_display(u2_val, "Gemini_U2.jpg", is_frequency=False)
                if img2:
                    slot2.image(img2, use_container_width=True)

            if u3_val != "N/A":
                img3 = draw_digital_display(u3_val, "Gemini_U3.jpg", is_frequency=False)
                if img3:
                    slot3.image(img3, use_container_width=True)

            if hz_val != "N/A":
                img4 = draw_digital_display(hz_val, "HZ.jpg", is_frequency=True)
                if img4:
                    slot4.image(img4, use_container_width=True)
        else:
            st.error(f"Server returned status code {response.status_code}")

    except Exception as e:
        st.error(f"Live Telemetry Link Error: {e}")

live_panel()
