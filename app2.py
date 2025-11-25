import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# ======================================================
# 🟩 Conversion Functions (self-contained – no utils.py)
# ======================================================

def dms_to_decimal(deg, minutes, seconds, direction):
    sign = 1 if direction.startswith("E") else -1
    return sign * (abs(deg) + minutes/60 + seconds/3600)

def decimal_to_dms(decimal_value):
    sign = 1 if decimal_value >= 0 else -1
    value = abs(decimal_value)
    d = int(value)
    m = int((value - d) * 60)
    s = (value - d - m/60) * 3600
    return sign, d, m, s

def hms_to_decimal_hours(h, m, s, sign):
    base = abs(h) + m/60 + s/3600
    return base if sign == "+" else -base

def decimal_hours_to_hms(hours_value):
    sign = "+" if hours_value >= 0 else "-"
    value = abs(hours_value)
    h = int(value)
    m = int((value - h) * 60)
    s = (value - h - m/60) * 3600
    return sign, h, m, s

def longitude_from_tz(decimal_hours):
    return decimal_hours * 15

# ======================================================
# Session State Defaults
# ======================================================

defaults = {
    "clicked_lon": 0.0,
    "clicked_lat": 0.0,
    "manual_lon": 0.0,
    "computed_lon": 0.0,
    "mode": "Longitude → Time Zone",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ======================================================
# Sidebar Inputs
# ======================================================

st.sidebar.header("Mode")
st.session_state.mode = st.sidebar.radio(
    "Select conversion direction",
    ["Longitude → Time Zone", "Time Zone → Longitude"]
)

st.sidebar.divider()
st.sidebar.header("Manual Input")

if st.session_state.mode == "Longitude → Time Zone":
    lon_direction = st.sidebar.selectbox("Direction", ["E (+)", "W (-)"])
    lon_deg = st.sidebar.number_input("Degrees", -180, 180, 0)
    lon_min = st.sidebar.number_input("Minutes", 0, 59, 0)
    lon_sec = st.sidebar.number_input("Seconds", 0.0, 59.999, 0.0)
    if st.sidebar.button("Compute Time Zone"):
        st.session_state.manual_lon = dms_to_decimal(lon_deg, lon_min, lon_sec, lon_direction)

else:
    tz_sign = st.sidebar.selectbox("Sign", ["+", "-"])
    tz_h = st.sidebar.number_input("Hours", 0, 18, 0)
    tz_m = st.sidebar.number_input("Minutes", 0, 59, 0)
    tz_s = st.sidebar.number_input("Seconds", 0.0, 59.999, 0.0)

    if st.sidebar.button("Compute Longitude"):
        dec_hours = hms_to_decimal_hours(tz_h, tz_m, tz_s, tz_sign)
        st.session_state.manual_lon = longitude_from_tz(dec_hours)

# ======================================================
# Layout
# ======================================================

left, right = st.columns([1, 1])

# ======================================================
# LEFT PANEL – Map + Slider
# ======================================================

with left:
    st.header("Interactive Map")

    # current longitude = last map click OR manual OR computed
    active_lon = st.session_state.manual_lon or st.session_state.clicked_lon

    # Map creation
    m = folium.Map(location=[st.session_state.clicked_lat, active_lon], zoom_start=3)

    # Green longitude line
    folium.PolyLine([[90, active_lon], [-90, active_lon]],
                    color="green", weight=4).add_to(m)

    map_data = st_folium(m, height=450, width=600)

    # Map click updates
    if map_data and map_data.get("last_clicked"):
        st.session_state.clicked_lat = map_data["last_clicked"]["lat"]
        st.session_state.clicked_lon = map_data["last_clicked"]["lng"]
        active_lon = st.session_state.clicked_lon

    st.write(f"### Selected Longitude: **{active_lon:.6f}°**")

    # Slider with pointy-hand cursor
    st.markdown(
        """
        <style>
        .stSlider > div > div > div > div {
            cursor: pointer;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    slider_lon = st.slider("Slide to adjust longitude", -180.0, 180.0, active_lon, 0.1)
    active_lon = slider_lon

# ======================================================
# RIGHT PANEL – Conversion Output + Explanation
# ======================================================

with right:
    st.header("Calculation Output")

    if st.session_state.mode == "Longitude → Time Zone":
        sign, d, m, s = decimal_to_dms(active_lon)
        dec_hours = active_lon / 15
        h_sign, hh, mm, ss = decimal_hours_to_hms(dec_hours)

        st.subheader("Result")
        st.write(f"**Longitude:** {active_lon:.6f}°")
        st.write(f"**Time Zone:** {h_sign}{hh}h {mm}m {ss:.3f}s")

        st.markdown("### Explanation")
        st.write(f"1. Decimal Degrees = input longitude = **{active_lon:.6f}°**")
        st.write(f"2. Convert degrees → hours: divide by 15 → **{active_lon:.6f} / 15 = {dec_hours:.6f}h**")
        st.write(f"3. Convert decimal hours → H:M:S → **{h_sign}{hh}:{mm}:{ss:.3f}**")

    else:
        # convert hours from manual input or slider (reverse)
        dec_hours = active_lon / 15
        h_sign, hh, mm, ss = decimal_hours_to_hms(dec_hours)

        st.subheader("Result")
        st.write(f"**Time Zone:** {h_sign}{hh}h {mm}m {ss:.3f}s")
        st.write(f"**Longitude:** {active_lon:.6f}°")

        st.markdown("### Explanation")
        st.write(f"1. Decimal Hours = longitude / 15 = **{active_lon:.6f}/15 = {dec_hours:.6f}h**")
        st.write(f"2. Convert decimal hours → D:M:S format")
        st.write(f"3. Output Longitude = **{active_lon:.6f}°**")

# ======================================================
# CSV / Excel Batch Processing
# ======================================================

st.divider()
st.header("Batch CSV / Excel Conversion")

uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded:
    df = pd.read_excel(uploaded) if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)

    st.write("Preview:", df.head())

    if st.button("Convert File"):
        if st.session_state.mode == "Longitude → Time Zone":
            df["DecimalHours"] = df["Longitude"] / 15
            df["TZ_Hours"] = df["DecimalHours"]
        else:
            df["Longitude"] = df["TZ_Hours"] * 15

        st.download_button("Download Converted File", df.to_csv(index=False), file_name="converted.csv")
        st.write(df)

