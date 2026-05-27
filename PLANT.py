import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import io

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="NCTPS Stage-I Generation Dashboard", layout="wide")
st.title("⚡ NCTPS Stage-I Online Monitoring System (EMS)")
st.write("Real-time telemetry and non-linear gauge calibration matrix.")

# --- DIALS CONFIGURATION DATABASE ---
# Every physical dial has its own unique scale, markings, and geometric wrap boundaries.
DIALS_DATABASE = {
    "Total MW": {
        "unit": "MW",
        "min_val": 0.0,
        "max_val": 750.0,
        "step": 5.0,
        "default": 375.0,
        "calibration": {
            "MW":     [0.0,   75.0,  150.0,  225.0,  300.0, 375.0, 450.0, 525.0, 600.0, 675.0, 750.0],
            "Angle":  [211.5, 196.5, 178.5,  156.5,  126.0, 87.0,  48.5,  19.5,  356.5, 344.5, 328.0]
        },
        "wrap_threshold": 220.0  # Split point where values wrap past 360/0
    },
    "Unit 1 Load": {
        "unit": "MW",
        "min_val": 0.0,
        "max_val": 250.0,
        "step": 2.0,
        "default": 210.0,
        "calibration": {
            # Example non-linear calibration curve for a 210MW class machine
            "MW":     [0.0,   50.0,  100.0,  150.0,  200.0,  210.0,  250.0],
            "Angle":  [220.0, 185.0, 145.0,  105.0,  65.0,   55.0,   20.0]
        },
        "wrap_threshold": 180.0
    },
    "Grid Frequency": {
        "unit": "Hz",
        "min_val": 47.5,
        "max_val": 51.5,
        "step": 0.01,
        "default": 50.00,
        "calibration": {
            # Symmetrical scale centered precisely around 50.0 Hz
            "MW":     [47.5,  48.5,  49.5,  50.0,  50.5,  51.5],
            "Angle":  [225.0, 180.0, 135.0, 90.0,  45.0,  0.0]
        },
        "wrap_threshold": 180.0
    }
}

# --- CALIBRATION INTERPOLATION ENGINE ---
def calculate_pointer_angle(value, dial_config):
    """
    Calculates the exact procircle matching angle for a given raw telemetry value
    by unrolling continuous geometric curves across the 0/360 boundary.
    """
    cal = dial_config["calibration"]
    x_points = cal["MW"]
    y_points = cal["Angle"]
    threshold = dial_config["wrap_threshold"]
    
    # Boundary capping
    value = max(dial_config["min_val"], min(dial_config["max_val"], value))
    
    # Unroll the angles cleanly past the circular axis crossover
    unrolled_angles = []
    for angle in y_points:
        if angle > threshold:
            unrolled_angles.append(angle - 360.0)
        else:
            unrolled_angles.append(angle)
            
    # Linearly interpolate within the local piecewise grid segment
    target_angle = float(np.interp(value, x_points, unrolled_angles))
    
    # Normalise results back to standard 0-360 Procircle limits
    if target_angle < 0:
        target_angle += 360.0
        
    return round(target_angle, 2)

# --- DYNAMIC IMAGE GENERATION ENGINE ---
def generate_gauge_face(angle_deg, label_text):
    """
    Generates an on-the-fly digital representation of a clear Procircle plate 
    with a needle dynamically positioned at the calibrated angle.
    """
    # Create a transparent square canvas
    img_size = 400
    center = img_size // 2
    image = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw outer procircle ring boundary line
    draw.ellipse([10, 10, img_size-10, img_size-10], outline="#1E1E1E", width=3)
    draw.ellipse([15, 15, img_size-15, img_size-15], outline="#A0A0A0", width=1)
    
    # Convert procircle orientation: 0 degrees is East (3 o'clock), running Counter-Clockwise.
    # PIL's rotate function rotates counter-clockwise naturally.
    
    # Create a separate layer purely for the pointer needle (pointing along 0° / East initially)
    needle_layer = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 0))
    needle_draw = ImageDraw.Draw(needle_layer)
    
    # Draw high-visibility tapered technical pointer needle pointing right (0 degrees)
    needle_draw.polygon([
        (center, center - 4),
        (img_size - 30, center - 1),
        (img_size - 15, center),      # Tip point
        (img_size - 30, center + 1),
        (center, center + 4)
    ], fill="#D32F2F", outline="#B71C1C")
    
    # Rotate needle by target calibration angle (pivoting on center axis)
    rotated_needle = needle_layer.rotate(angle_deg, resample=Image.BICUBIC, center=(center, center))
    
    # Composite the needle layer onto the primary gauge face base
    image = Image.alpha_composite(image, rotated_needle)
    
    # Standard center hub cap detailing
    draw.ellipse([center-8, center-8, center+8, center+8], fill="#263238", outline="#000000", width=2)
    draw.ellipse([center-3, center-3, center+3, center+3], fill="#CFD8DC")
    
    # Injected reference texts inside the rendering box
    draw.text((center - 40, center + 40), label_text, fill="#333333")
    
    return image


# --- MAIN UI WORKSPACE LAYOUT ---
st.subheader("📊 Live Telemetry Overrides")
user_inputs = {}

# Dynamically render inputs for all tracking systems in parallel columns
input_cols = st.columns(len(DIALS_DATABASE))
for idx, (dial_name, config) in enumerate(DIALS_DATABASE.items()):
    with input_cols[idx]:
        st.markdown(f"**{dial_name} ({config['unit']})**")
        user_inputs[dial_name] = st.slider(
            f"Adjust {dial_name}:",
            min_value=config["min_val"],
            max_value=config["max_val"],
            value=config["default"],
            step=config["step"],
            key=f"slider_{dial_name}",
            label_visibility="collapsed"
        )

st.markdown("---")
st.subheader("🎯 Real-Time Mechanical Gauge Alignments")

# Render matching dynamic gauges inside primary grid alignment
gauge_cols = st.columns(len(DIALS_DATABASE))
for idx, (dial_name, config) in enumerate(DIALS_DATABASE.items()):
    current_val = user_inputs[dial_name]
    
    # 1. Map telemetry value to precise mechanical angular matrix position
    calculated_angle = calculate_pointer_angle(current_val, config)
    
    # 2. Render physical pointer assembly alignment
    gauge_image = generate_gauge_face(calculated_angle, f"{current_val} {config['unit']}")
    
    with gauge_cols[idx]:
        st.markdown(f"<h3 style='text-align: center; color: #1E3A8A;'>{dial_name}</h3>", unsafe_allow_html=True)
        st.image(gauge_image, use_container_width=True)
        st.metric(
            label="Procircle Native Reading", 
            value=f"{calculated_angle}°", 
            delta=f"{current_val} {config['unit']}",
            delta_color="off"
        )

# --- TECHNICAL METRICS CALIBRATION DATABASES ---
with st.expander("🛠️ View Multi-Dial Internal Piecewise Calibration Matrices"):
    matrix_cols = st.columns(len(DIALS_DATABASE))
    for idx, (dial_name, config) in enumerate(DIALS_DATABASE.items()):
        with matrix_cols[idx]:
            st.markdown(f"**{dial_name} Matrix Map**")
            st.data_editor(
                {
                    f"Value ({config['unit']})": config["calibration"]["MW"],
                    "Procircle Mark Line (° )": config["calibration"]["Angle"]
                },
                key=f"editor_{dial_name}",
                disabled=True
            )
