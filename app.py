import streamlit as st
from utils import (
    dms_to_decimal,
    decimal_to_dms,
    tz_hours_to_hms,
    hms_to_decimal_hours,
    longitude_from_timezone_hours,
)
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import folium
import io

st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# Session state for map clicks
if "map_lon" not in st.session_state:
    st.session_state.map_lon = None
if "map_lat" not in st.session_state:
    st.session_state.map_lat = None

def update_from_map(lat, lon):
    """Auto-fill the left panel from map click."""
    st.session_state.map_lat = lat
    st.session_state.map_lon = lon

    # Convert longitude to DMS
    sgn, d, m, s = decimal_to_dms(lon)
    st.session_state.lon_dir = "E (positive)" if sgn >= 0 else "W (negative)"
    st.session_state.lon_deg = d
    st.session_state.lon_min = m
    st.session_state.lon_sec = float(f"{s:.6f}")

st.title("🕰️ 🌍 Time Zone ↔ Longitude Calculator")

st.markdown(
"""
This app converts **longitude ↔ time zone offset**, with map clicking, CSV batch processing, 
and educational explanations.
"""
)

# ---------------- Layout -----------------
left, right = st.columns(2)

# ------------ LEFT COLUMN (Calculator) --------------
with left:
    st.markdown("## 🧮 Single Conversion")

    with st.container():
        st.markdown("### Mode Selection")
        mode = st.radio("Choose conversion:", ["Longitude → Time Zone", "Time Zone → Longitude"])

    if mode == "Longitude → Time Zone":
        st.markdown("### 📌 Enter Longitude (or click on map)")

        lon_dir = st.selectbox(
            "Direction", ["E (positive)", "W (negative)"], key="lon_dir"
        )
        deg = st.number_input("Degrees", min_value=0, max_value=180, step=1, key="lon_deg")
        minu = st.number_input("Minutes", min_value=0, max_value=59, step=1, key="lon_min")
        sec = st.number_input("Seconds", min_value=0.0, max_value=59.999, format="%.6f", key="lon_sec")

        if st.button("Compute Time Zone", use_container_width=True):
            sign = 1 if lon_dir.startswith("E") else -1
            dec_lon = dms_to_decimal(deg, minu, sec, sign)
            tz = dec_lon / 15

            sgn, h, m, s = tz_hours_to_hms(tz)
            sign_char = "+" if sgn >= 0 else "-"

            st.success(f"Computed Time Zone: {sign_char}{h:02d}:{m:02d}:{s:06.3f}")

            st.markdown("### Explanation")
            st.write(f"1. Decimal longitude = {dec_lon:.6f}°")
            st.write(f"2. Divide by 15°/hour → Time = {tz:.6f} h")
            st.write(f"3. Converted to H:M:S → {sign_char}{h}:{m}:{s:.3f}")

    else:
        st.markdown("### 📌 Enter Time Zone Offset")

        tz_sign = st.selectbox("Sign", ["+", "-"])
        tz_h = st.number_input("Hours", min_value=0, max_value=18)
        tz_m = st.number_input("Minutes", min_value=0, max_value=59)
        tz_s = st.number_input("Seconds", min_value=0.0, max_value=59.999)

        if st.button("Compute Longitude", use_container_width=True):
            dec_hours = hms_to_decimal_hours(tz_h, tz_m, tz_s, 1 if tz_sign == "+" else -1)
            lon = longitude_from_timezone_hours(dec_hours)

            sgn, d, m, s = decimal_to_dms(lon)
            dir = "E" if sgn >= 0 else "W"

            st.success(f"Longitude = {dir} {d}° {m}' {s:.3f}\"")

            st.markdown("### Explanation")
            st.write(f"1. Decimal hours = {dec_hours:.6f}")
            st.write(f"2. ×15° gives longitude = {lon:.6f}°")
            st.write(f"3. Converted to DMS → {dir} {d}° {m}' {s:.3f}\"")

# ----------------- RIGHT COLUMN (Map & CSV) ------------------
with right:
    st.markdown("## 🗺️ Interactive Map")

    m = folium.Map(location=[0, 0], zoom_start=2)

    # Draw meridians
    for lon in range(-180, 181, 30):
        folium.PolyLine([[90, lon], [-90, lon]], color="gray", weight=1).add_to(m)

    map_data = st_folium(m, width=700, height=450)

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        update_from_map(lat, lon)
        st.success(f"Selected: Latitude {lat:.4f}°, Longitude {lon:.4f}°")

    st.markdown("---")
    st.markdown("## 📦 Batch CSV Conversion")

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)
        st.dataframe(df.head())

        if set(["deg", "min", "sec", "dir"]).issubset(df.columns):
            results = []
            for _, r in df.iterrows():
                sign = 1 if r["dir"].upper().startswith("E") else -1
                dec = dms_to_decimal(r.deg, r.min, r.sec, sign)
                tz = dec / 15
                sgn, h, m, s = tz_hours_to_hms(tz)
                results.append(f"{'+' if sgn>=0 else '-'}{h:02d}:{m:02d}:{s:05.2f}")
            df["tz"] = results

        elif set(["tz_sign", "h", "m", "s"]).issubset(df.columns):
            results = []
            for _, r in df.iterrows():
                hours = hms_to_decimal_hours(r.h, r.m, r.s, 1 if r.tz_sign == "+" else -1)
                lon = longitude_from_timezone_hours(hours)
                sgn, d, m, s = decimal_to_dms(lon)
                results.append(f"{'E' if sgn>=0 else 'W'} {d}° {m}' {s:05.2f}\"")
            df["longitude"] = results

        st.dataframe(df)
        st.download_button("Download Results", df.to_csv(index=False), file_name="results.csv")
