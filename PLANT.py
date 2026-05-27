import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Total MW Dial Monitor", layout="centered")
st.title("⚡ Power Plant Total MW Monitor")
st.write("Live angular tracking dashboard based on custom non-linear dial calibration.")

# --- NON-LINEAR CALIBRATION DATABASE ---
# Sorted by ascending MW values for proper mathematical interpolation
CALIBRATION_DATA = {
    "MW":     [0.0,   75.0,  150.0,  225.0,  300.0, 375.0, 450.0, 525.0, 600.0, 675.0, 750.0],
    "Angle":  [211.5, 196.5, 178.5,  156.5,  126.0, 87.0,  48.5,  19.5,  356.5, 344.5, 328.0]
}

def mw_to_procircle_angle(mw_value):
    """
    Translates an incoming live MW value to its corresponding Procircle angle.
    Handles the cross-over discontinuity at the 0°/360° boundary smoothly.
    """
    # Bound the input value within the physical scale limits
    mw_value = max(0.0, min(750.0, mw_value))
    
    # Unroll angles past the 360 boundary to keep the interpolation continuous/monotonic
    # 600MW = 356.5, 675MW = 344.5 (which is 360 + 344.5 = 704.5 relative to upper scale)
    unrolled_angles = []
    for angle in CALIBRATION_DATA["Angle"]:
        if angle > 220:  # Adjusting the wrap-around baseline
            unrolled_angles.append(angle - 360.0)
        else:
            unrolled_angles.append(angle)
            
    # Compute the interpolated angle
    interpolated_angle = float(np.interp(mw_value, CALIBRATION_DATA["MW"], unrolled_angles))
    
    # Normalize back to standard 0-360 range
    if interpolated_angle < 0:
        interpolated_angle += 360.0
        
    return round(interpolated_angle, 2)


# --- INTERACTIVE USER INTERFACE ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Control Input")
    # Live simulation input slider
    live_mw = st.slider("Simulate Live Generation (MW):", 
                        min_value=0.0, 
                        max_value=750.0, 
                        value=375.0, 
                        step=5.0)
    
    # Calculate target vector coordinates
    target_angle = mw_to_procircle_angle(live_mw)
    
    # Display digital metrics
    st.metric(label="Current Power", value=f"{live_mw} MW")
    st.metric(label="Target Pointer Angle", value=f"{target_angle}°")

with col2:
    st.subheader("Procircle Pointer Alignment")
    
    # Generate vector plot mimicking your gauge structure
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={'projection': 'polar'})
    
    # Convert degrees to radians for matplotlib polar projection
    # Note: Polar plots natively start at 3 o'clock (0 rad) counter-clockwise
    angle_rad = np.deg2rad(target_angle)
    
    # Draw vector line representing the physical dial pointer needle
    ax.arrow(angle_rad, 0, 0.95, 0, 
             alpha=0.9, 
             edgecolor='red', 
             facecolor='red', 
             lw=3, 
             zorder=5, 
             head_width=0.1, 
             head_length=0.1)
    
    # Configure the polar display to closely match your layout
    ax.set_theta_zero_location("E")  # 0 Degrees at East / 3 o'clock
    ax.set_theta_direction(1)       # 1 = Counter-Clockwise progression
    
    # Add a center cap point
    ax.plot(0, 0, color='black', marker='o', markersize=10, zorder=6)
    
    # Scale layout adjustments
    ax.set_ylim(0, 1)
    ax.set_yticklabels([]) # Hide distance rings
    ax.grid(True, linestyle='--', alpha=0.6)
    
    st.pyplot(fig)

# --- TECHNICAL DATABASE UTILITY DISPLAY ---
with st.expander("Show Calibration Reference Matrix"):
    st.table({
        "MW Value": CALIBRATION_DATA["MW"],
        "Procircle Gauge Line (° )": CALIBRATION_DATA["Angle"]
    })
