import streamlit as st
import requests
import time
import base64
import os
from PIL import Image, ImageDraw

st.set_page_config(page_title="NCTPS1MW Dashboard", layout="wide")
st.title("⚡ NCTPS1MW LIVE PLANT DATA ⚡")

st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Interval (seconds)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)

# ------------------------------------------------------------------
# BULLETPROOF CLOUD LOCAL ENCODER (Bypasses GitHub URL Handshakes)
# ------------------------------------------------------------------
@st.cache_resource
def get_cached_base64_background(filename):
    """
    Reads the file directly from the cloned repository instance on the cloud server,
    converts it to a Base64 text string, and keeps it permanently in server memory.
    """
    # Check current directory and script directory
    paths_to_check = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        os.path.join(os.getcwd(), filename),
        filename
    ]
    
    target_path = None
    for p in paths_to_check:
        if os.path.exists(p):
            target_path = p
            break

    try:
        if target_path:
            with open(target_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception:
        pass

    # If the file is completely missing or unreadable, generate a stable virtual dark panel background
    fallback = Image.new("RGBA", (400, 250), (20, 25, 35, 255))
    import io
    buf = io.BytesIO()
    fallback.convert("RGB").save(buf, format="JPEG")
    fallback_b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{fallback_b64}"

# ------------------------------------------------------------------
# ORIGINAL SEVEN-SEGMENT VECTOR LOGIC
# ------------------------------------------------------------------
def draw_custom_vector_digit(draw, x, y, char, w, h, thickness, color):
    t = thickness
    mid_y = h / 2
    
    segments = {
        'a': (t, 0, w - 2*t, t),               # Top
        'b': (w - t, t, t, mid_y - t),         # Top Right
        'c': (w - t, mid_y, t, mid_y - t),     # Bottom Right
        'd': (t, h - t, w - 2*t, t),           # Bottom
        'e': (0, mid_y, t, mid_y - t),         # Bottom Left
        'f': (0, t, t, mid_y - t),             # Top Left
        'g': (t, mid_y - t/2, w - 2*t, t)      # Middle
    }
    
    mapping = {
        '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abcdg', '4': 'fgbc',
        '5': 'afgcd', '6': 'afedcg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
        '-': 'g'
    }
    
    if char == '.':
        draw.rectangle([x + w/2 - t, y + h - 1.5*t, x + w/2 + t, y + h], fill=color)
        return

    active = mapping.get(char, '')
    for seg in active:
        sx, sy, sw, sh = segments[seg]
        draw.rectangle([x + sx, y + sy, x + sx + sw, y + sy + sh], fill=color)

def draw_vector_string(draw, text, cx, cy, color):
    digit_w = 64       
    digit_h = 110       
    thickness = 15      
    spacing = 12       
    
    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)
    start_y = cy - (digit_h / 2)
    
    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(draw, curr_x, start_y, char, digit_w, digit_h, thickness, color)
        curr_x += digit_w + spacing

# ------------------------------------------------------------------
# HIGH-SPEED DYNAMIC PAYLOAD COUPLER (ZERO VANISHING/FLASHING)
# ------------------------------------------------------------------
def render_live_instrument_card(value, filename, is_frequency=False):
    """
    Combines the cached server-side base64 background string with a 
    dynamically calculated transparent text string to achieve instant browser loads.
    """
    # Fetch permanent background data URI instantly from cache memory
    bg_b64_uri = get_cached_base64_background(filename)
    
    if is_frequency:
        text_color = (255, 235, 0, 255)  # Vibrant Safety Yellow
    else:
        text_color = (0, 240, 255, 255)  # Electric Cyan
        
    # Generate dynamic transparent overlay containing your vector string digits
    overlay = Image.new("RGBA", (400, 250), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_vector_string(draw, str(value), 200, 125, text_color)
    
    # Save transient layer text matrix directly to a Base64 text string data URI
    import io
    txt_buffer = io.BytesIO()
    overlay.save(txt_buffer, format="PNG")
    txt_b64 = base64.b64encode(txt_buffer.getvalue()).decode()
    txt_uri = f"data:image/png;base64,{txt_b64}"
    
    # Nested completely local HTML layout block - ensures zero cloud-network refresh delays
    html_layout = f"""
    <div style="position: relative; width: 100%; display: inline-block;">
        <img src="{bg_b64_uri}" style="width: 100%; height: auto; display: block; border-radius: 4px;">
        <img src="{txt_uri}" style="position: absolute; top: 0; left: 0; width: 100%; height: auto; display: block; mix-blend-mode: screen;">
    </div>
    """
    return html_layout

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Static structural setup columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    m1 = st.empty()
    i1 = st.empty()
with col2:
    m2 = st.empty()
    i2 = st.empty()
with col3:
    m3 = st.empty()
    i3 = st.empty()
with col4:
    m4 = st.empty()
    i4 = st.empty()

try:
    response = requests.get(url)
    if response.status_code == 200 and (nctps_data := response.json()):
        
        u1_val = str(nctps_data.get("UNIT1", {}).get("MW", "N/A"))
        u2_val = str(nctps_data.get("UNIT2", {}).get("MW", "N/A"))
        u3_val = str(nctps_data.get("UNIT3", {}).get("MW", "N/A"))
        hz_val = str(nctps_data.get("HZ", {}).get("HZ", "N/A"))
        
        # UNIT 1 DISPLAY FRAME
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            card1 = render_live_instrument_card(u1_val, "Gemini_U1.jpg", is_frequency=False)
            i1.markdown(card1, unsafe_style_with_html=True)

        # UNIT 2 DISPLAY FRAME
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            card2 = render_live_instrument_card(u2_val, "Gemini_U2.jpg", is_frequency=False)
            i2.markdown(card2, unsafe_style_with_html=True)

        # UNIT 3 DISPLAY FRAME
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            card3 = render_live_instrument_card(u3_val, "Gemini_U3.jpg", is_frequency=False)
            i3.markdown(card3, unsafe_style_with_html=True)

        # GRID FREQUENCY DISPLAY FRAME
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        if hz_val != "N/A":
            card4 = render_live_instrument_card(hz_val, "HZ.jpg", is_frequency=True)
            i4.markdown(card4, unsafe_style_with_html=True)

except Exception as e:
    st.error(f"Network Connection Timeout/Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
