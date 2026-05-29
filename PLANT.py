import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import requests
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# --- MATHEMATICAL DE-OBFUSCATION ENGINE ---
def get_math_salt_from_timestamp(timestamp_val):
    """Recreates the exact dynamic offset used by Node-RED."""
    try:
        time_window = int(float(timestamp_val)) // 60
        # Must perfectly match the formula used in Node-RED
        math_salt = (time_window % 12345) + 54321
        return math_salt
    except Exception:
        return 0

# ... [Keep layout styles and helper image functions here] ...

# --- TAB 1: GENERATION SCADA FACE ---
with tab_generation:
    st.title("⚡ NCTPS 1 LIVE MW DASHBOARD ⚡")
    st.markdown("### Generation Overview: Main Alternator Panel Arrays")
    
    generation_container = st.container()

    @st.fragment(run_every=refresh_interval if auto_refresh else None)
    def run_generation_stream():
        plant_url = "https://nctps1-594d5-default-rtdb.asia-southeast1.firebasedatabase.app/NCTPS1MW.json"
        
        with generation_container:
            try:
                res = requests.get(plant_url, timeout=4)
                nctps_data = res.json() or {} if res.status_code == 200 else {}
                
                # --- HEARTBEAT MONITORING ENGINE ---
                current_run_pulse = nctps_data.get("LIVE", {}).get("RUN", None)
                current_time_now = time.time()
                sensor_fault_triggered = False

                if "last_run_pulse" not in st.session_state:
                    st.session_state.last_run_pulse = current_run_pulse
                    st.session_state.last_pulse_timestamp = current_time_now
                else:
                    if current_run_pulse == st.session_state.last_run_pulse:
                        elapsed_duration = current_time_now - st.session_state.last_pulse_timestamp
                        if elapsed_duration >= 5.0:
                            sensor_fault_triggered = True
                    else:
                        st.session_state.last_run_pulse = current_run_pulse
                        st.session_state.last_pulse_timestamp = current_time_now

                # --- UI PRESENTATION PATH SEPARATION ---
                if sensor_fault_triggered or current_run_pulse is None:
                    st.error(
                        "🛑 CRITICAL BUS INTERFACE TIMEOUT: Real-time telemetry feed from the physical MW sensor "
                        "has frozen or failed. Displaying stale values has been restricted for Data Validity.",
                        icon="🚨"
                    )
                else:
                    # Calculate the dynamic salt from the incoming timestamp
                    salt = get_math_salt_from_timestamp(current_run_pulse)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    slot1 = col1.empty()
                    slot2 = col2.empty()
                    slot3 = col3.empty()
                    slot4 = col4.empty()
                    slot5 = col5.empty()

                    # Extract Firebase values safely
                    fb_u1 = nctps_data.get("UNIT1", {}).get("MW", "N/A")
                    fb_u2 = nctps_data.get("UNIT2", {}).get("MW", "N/A")
                    fb_u3 = nctps_data.get("UNIT3", {}).get("MW", "N/A")
                    fb_hz = nctps_data.get("HZ", {}).get("HZ", "N/A")

                    # Decode values by subtracting the dynamic salt on-the-fly
                    u1 = str(int(float(fb_u1) - salt)) if fb_u1 != "N/A" else "N/A"
                    u2 = str(int(float(fb_u2) - salt)) if fb_u2 != "N/A" else "N/A"
                    u3 = str(int(float(fb_u3) - salt)) if fb_u3 != "N/A" else "N/A"
                    hz = f"{(float(fb_hz) - (salt / 1000)):.2f}" if fb_hz != "N/A" else "N/A"

                    total_load = 0.0
                    valid_count = 0
                    for v in [u1, u2, u3]:
                        try:
                            total_load += float(v)
                            valid_count += 1
                        except ValueError: pass
                    total_str = str(int(total_load)) if valid_count > 0 else "N/A"

                    if u1 != "N/A":
                        img = draw_digital_display(u1, "Gemini_U1.jpg", display_type="mw")
                        if img: slot1.image(img, use_container_width=True)
                    if u2 != "N/A":
                        img = draw_digital_display(u2, "Gemini_U2.jpg", display_type="mw")
                        if img: slot2.image(img, use_container_width=True)
                    if u3 != "N/A":
                        img = draw_digital_display(u3, "Gemini_U3.jpg", display_type="mw")
                        if img: slot3.image(img, use_container_width=True)
                    if total_str != "N/A":
                        img = draw_digital_display(total_str, "Gemini_T.jpg", display_type="total")
                        if img: slot4.image(img, use_container_width=True)
                    if hz != "N/A":
                        img = draw_digital_display(hz, "HZ.jpg", display_type="hz")
                        if img: slot5.image(img, use_container_width=True)
                        
            except Exception as e:
                st.error(f"Generation Bus Interface Fault: {e}")

    run_generation_stream()

# ... [Keep rest of file unchanged] ...
