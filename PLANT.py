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
# HIGH-SPEED ASSET PRE-LOADER & DIMENSION RESOLVER
# ------------------------------------------------------------------
@st.cache_resource
def load_image_dimensions_and_bg():
    """
    Locates image files once, extracts native dimensions to prevent scaling 
    distortions, and encodes backgrounds into permanent system RAM cache.
    """
    filenames = {
        "u1": "Gemini_U1.jpg",
        "u2": "Gemini_U2.jpg",
        "u3": "Gemini_U3.jpg",
        "hz": "HZ.jpg"
    }
    
    bg_data = {}
    
    for key, filename in filenames.items():
        paths_to_check = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
            os.path.join(os.getcwd(), filename),
            filename,
            filename.lower(),
            filename.upper()
        ]
        
        target_path = None
        for p in paths_to_check:
            if os.path.exists(p):
                target_path = p
                break
                
        width, height = 400, 250  # Default safe fallbacks
        encoded_string = ""
        
        if target_path:
            try:
                with Image.open(target_path) as img:
                    width, height = img.size
                with open(target_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode()
            except Exception:
                pass
                
        bg_data[key] = {
            "width": width,
            "height": height,
            "b64": encoded_string
        }
    return bg_data

# Initialize asset cache memory
bg_metadata = load_image_dimensions_and_bg()

# Construct permanent CSS layout injection rules
css_rules = []
for key, data in bg_metadata.items():
    if data["b64"]:
        css_rules.append(f"""
        .bg-{key} {{
            background-image: url('data:image/jpeg;base64,{data["b64"]}');
        }}
        """)
    else:
        # Sleek dark fallback panel background rule if physical asset file missing
        css_rules.append(f"""
        .bg-{key} {{
            background-color: #141923;
            border: 2px solid #323c50;
        }}
        """)

# Inject style parameters to browser engine once (Prevents image flash)
st.markdown(f"""
<style>
{" ".join(css_rules)}
.plant-card {{
    position: relative;
    width: 100%;
    background-size: 100% 100%;
    background-repeat: no-repeat;
    background-position: center;
    border-radius: 6px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
    overflow: hidden;
}}
.overlay-container {{
    width: 100%;
    height: auto;
    display: block;
}}
.overlay-container img {{
    width: 100%;
    height: auto;
    display: block;
    mix-blend-mode: screen;
}}
</style>
""", unsafe_allow_html=True)

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
# INTERFACE COUPLER (ZERO VANISHING/FLASHING)
# ------------------------------------------------------------------
def render_live_instrument_card(value, key, is_frequency=False):
    """
    Generates a transient transparent image overlay containing only the text string 
    digits and nests it inside a parent container styled with the static background rule.
    """
    data = bg_metadata[key]
    w = data["width"]
    h = data["height"]
    
    # Generate transparent dynamic text vector layer matching exact layout dimensions
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    center_x = w * 0.50
    center_y = h * 0.50
    
    if is_frequency:
        text_color = (255, 235, 0, 255)  # Vibrant Safety Yellow
    else:
        text_color = (0, 240, 255, 255)  # Electric Cyan
        
    draw_vector_string(draw, str(value), center_x, center_y, text_color)
    
    import io
    txt_buffer = io.BytesIO()
    overlay.save(txt_buffer, format="PNG")
    txt_b64 = base64.b64encode(txt_buffer.getvalue()).decode()
    txt_uri = f"data:image/png;base64,{txt_b64}"
    
    # Render layout. Parent container classes (bg-u1 etc) do not reload, preventing flashes.
    html_layout = f"""
    <div class="plant-card bg-{key}">
        <div class="overlay-container">
            <img src="{txt_uri}">
        </div>
    </div>
    """
    return html_layout

url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"

# Unchanging layout block setup
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
        
        # UNIT 1
        m1.metric(label="UNIT 1 Generation", value=f"{u1_val} MW")
        if u1_val != "N/A":
            card1 = render_live_instrument_card(u1_val, "u1", is_frequency=False)
            i1.markdown(card1, unsafe_allow_html=True)

        # UNIT 2
        m2.metric(label="UNIT 2 Generation", value=f"{u2_val} MW")
        if u2_val != "N/A":
            card2 = render_live_instrument_card(u2_val, "u2", is_frequency=False)
            i2.markdown(card2, unsafe_allow_html=True)

        # UNIT 3
        m3.metric(label="UNIT 3 Generation", value=f"{u3_val} MW")
        if u3_val != "N/A":
            card3 = render_live_instrument_card(u3_val, "u3", is_frequency=False)
            i3.markdown(card3, unsafe_allow_html=True)

        # GRID FREQUENCY
        m4.metric(label="Grid Frequency", value=f"{hz_val} Hz")
        if hz_val != "N/A":
            card4 = render_live_instrument_card(hz_val, "hz", is_frequency=True)
            i4.markdown(card4, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Connection Error: {e}")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
