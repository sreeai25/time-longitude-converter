import streamlit as st
import pandas as pd
from utils import (
    dms_to_decimal,
    decimal_to_dms,
    tz_hours_to_hms,
    hms_to_decimal_hours,
    longitude_from_timezone_hours,
)
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# ---------------- SESSION STATE ----------------
for key, default in [
    ("clicked_lon", None),
    ("clicked_lat", 0.0),
    ("computed_lon", None),
    ("lon_dir", "E (positive)"),
    ("lon_deg", 0),
    ("lon_min", 0),
    ("lon_sec", 0.0),
    ("tz_sign_auto", True),  # auto-update time from map click
]:
    if key not in st.session_state:
        st.session_state[key] = default
        st.markdown("### Explanation")
            st.write(f"**Step 1: Convert D:M:S → Decimal Degrees:** {deg} + {minu}/60 + {sec}/3600 = {dec_deg:.6f}°")
            st.write(f"**Step 2: Decimal Degrees → Time Zone (hours):** {dec_deg:.6f}/15 = {tz_hours:.6f} h")
            st.write(f"**Step 3: Decimal Hours → H:M:S:** {h}:{m}:{s:.3f}")
            hours = int(tz_hours)
            minutes = int(abs(tz_hours - hours)*60)
            seconds = (abs(tz_hours - hours)*60 - minutes)*60
            st.write(f"**Step 3: Decimal Hours → H:M:S:** {hours}:{minutes}:{seconds:.3f}")

    else:
        st.subheader("Enter Time Zone Offset")
        st.checkbox("Auto-update time from map click", value=True, key="tz_sign_auto")
        tz_sign = st.selectbox("Sign", ["+","-"], key="tz_sign")
        tz_h = st.number_input("Hours", 0, 18, key="tz_h")
        tz_h = st.number_input("Hours", 0, 12, key="tz_h")
        tz_m = st.number_input("Minutes",0,59,key="tz_m")
        tz_s = st.number_input("Seconds",0.0,59.999,key="tz_s")
        if st.button("Compute Longitude"):
           st.markdown("### Explanation")
            st.write(f"**Step 1: Convert H:M:S → Decimal Hours:** {tz_h} + {tz_m}/60 + {tz_s}/3600 = {dec_hours:.6f} h")
            st.write(f"**Step 2: Decimal Hours → Longitude:** {dec_hours:.6f} * 15 = {lon:.6f}°")
            sgn, d, m_val, s_val = decimal_to_dms(lon)
            st.write(f"**Step 3: Decimal Degrees → D:M:S:** {d}° {m_val}' {s_val:.3f}\"")

    # ---------------- Batch Upload ----------------

with right:
    st.header("Interactive Map")
    # green line uses computed_lon if exists else clicked_lon
    highlight_lon = st.session_state.computed_lon if st.session_state.computed_lon is not None else st.session_state.clicked_lon or 0.0
    highlight_lat = st.session_state.clicked_lat or 0.0
    highlight_lon = float(st.session_state.computed_lon) if st.session_state.computed_lon is not None else float(st.session_state.clicked_lon or 0.0)
    highlight_lat = float(st.session_state.clicked_lat if st.session_state.clicked_lat is not None else 0.0)

    m = folium.Map(location=[highlight_lat, highlight_lon], zoom_start=4)
                    color="green",weight=3,opacity=0.7,
                    tooltip=f"Selected/Computed Longitude: {highlight_lon:.4f}°").add_to(m)

    # add slider as map control for green line
    # slider for green line
    slider_lon = st.slider("Move Green Longitude Line", -180.0, 180.0, float(highlight_lon), step=0.1)
    highlight_lon = slider_lon
    folium.PolyLine([[90,highlight_lon],[-90,highlight_lon]],
                    color="green",weight=3,opacity=0.7).add_to(m)

    # Auto-update input fields based on slider
    if mode=="Longitude → Time Zone":
        sgn, d, m_val, s_val = decimal_to_dms(highlight_lon)
        st.session_state.lon_dir = "E (positive)" if sgn>=0 else "W (negative)"
        st.session_state.lon_deg = d
        st.session_state.lon_min = m_val
        st.session_state.lon_sec = round(s_val,6)
    elif mode=="Time Zone → Longitude" and st.session_state.tz_sign_auto:
        dec_hours = highlight_lon / 15
        sgn, h, m, s = tz_hours_to_hms(dec_hours)
        st.session_state.tz_sign = "+" if sgn>=0 else "-"
        st.session_state.tz_h = h
        st.session_state.tz_m = m
        st.session_state.tz_s = s

    # add green line for slider position
    folium.PolyLine([[90,highlight_lon],[-90,highlight_lon]], color="green", weight=3, opacity=0.7).add_to(m)
    map_data = st_folium(m,width=700,height=450)
        lon = map_data["last_clicked"]["lng"]
        st.session_state.clicked_lat = lat
        st.session_state.clicked_lon = lon
        # Auto-fill longitude input ONLY in Longitude→Time mode
        if mode=="Longitude → Time Zone":
        # Auto-fill input fields based on mode
        if mode=="Longitude → Time Zone" or (mode=="Time Zone → Longitude" and st.session_state.tz_sign_auto):
            st.experimental_rerun()

    st.markdown(f"**Last Map Click:** Latitude={st.session_state.clicked_lat:.6f}°, Longitude={st.session_state.clicked_lon if st.session_state.clicked_lon is not None else 0.0:.6f}°")
