import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# ======================================================
# Conversion Utilities
# ======================================================

def dms_to_decimal(deg, minutes, seconds, direction):
    sign = 1 if direction.startswith("E") else -1
    value = abs(deg) + minutes/60 + seconds/3600
    return sign * value

def decimal_to_dms(decimal_value):
    sign = 1 if decimal_value >= 0 else -1
    value = abs(decimal_value)
    d = int(value)
    m = int((value - d) * 60)
    s = (value - d - m/60) * 3600
    return sign, d, m, s

def hms_to_decimal_hours(h, m, s, sign):
    total = abs(h) + m/60 + s/3600
    return total if sign == "+" else -total

def decimal_hours_to_hms(hours_value):
    sign = "+" if hours_value >= 0 else "-"
    value = abs(hours_value)
    h = int(value)
    m = int((value - h) * 60)
    s = (value - h - m/60) * 3600
    return sign, h, m, s

def longitude_from_tz(hours_value):
    return hours_value * 15

# ======================================================
# Session State Defaults
# ======================================================

defaults = {
    "active_lon": 0.0,     # master longitude (slider/map/manual synced)
    "clicked_lat": 0.0,
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
    "Select Direction",
    ["Longitude → Time Zone", "Time Zone → Longitude"]
)

st.sidebar.markdown("### Manual Input")

# Manual input synced to master longitude
if st.session_state.mode == "Longitude → Time Zone":
    dir_val = st.sidebar.selectbox("Direction", ["E (+)", "W (-)"])
    lon_deg = st.sidebar.number_input("Degrees (±180°)", -180, 180, value=0)
    lon_min = st.sidebar.number_input("Minutes", 0, 59, value=0)
    lon_sec = st.sidebar.number_input("Seconds", 0.0, 59.999, value=0.0)

    if st.sidebar.button("Apply Longitude"):
        st.session_state.active_lon = dms_to_decimal(lon_deg, lon_min, lon_sec, dir_val)

else:
    tz_sign = st.sidebar.selectbox("Sign", ["+", "-"])
    tz_h = st.sidebar.number_input("Hours (±12)", 0, 12, value=0)
    tz_m = st.sidebar.number_input("Minutes", 0, 59, value=0)
    tz_s = st.sidebar.number_input("Seconds", 0.0, 59.999, value=0.0)

    if st.sidebar.button("Apply Time Zone"):
        hours_dec = hms_to_decimal_hours(tz_h, tz_m, tz_s, tz_sign)
        st.session_state.active_lon = longitude_from_tz(hours_dec)

# ======================================================
# Main Layout
# ======================================================

st.header("Interactive Longitude & Time Zone Converter")

# ---------------- MAP ----------------

st.markdown("## Interactive Map")

m = folium.Map(location=[st.session_state.clicked_lat, st.session_state.active_lon], zoom_start=3)

# green longitude line
folium.PolyLine([[90, st.session_state.active_lon], [-90, st.session_state.active_lon]],
                color="green", weight=4).add_to(m)

map_data = st_folium(m, height=500, width=1000)

# map click sync
if map_data and map_data.get("last_clicked"):
    st.session_state.clicked_lat = map_data["last_clicked"]["lat"]
    st.session_state.active_lon = map_data["last_clicked"]["lng"]

# ---------------- SLIDER ----------------

st.markdown("### Adjust Longitude")

# slider sync
slider_val = st.slider(
    "Drag to modify longitude",
    min_value=-180.0, max_value=180.0,
    value=float(st.session_state.active_lon),
    step=0.1
)

st.session_state.active_lon = slider_val

st.markdown(f"### Selected Longitude: **{st.session_state.active_lon:.6f}°**")

# ======================================================
# CALCULATIONS BELOW INPUT + MAP
# ======================================================

st.divider()
st.header("Result")

lon = st.session_state.active_lon

if st.session_state.mode == "Longitude → Time Zone":
    # convert longitude → time
    dec_hours = lon / 15
    sign, h, m, s = decimal_hours_to_hms(dec_hours)

    st.subheader("Computed Time Zone")
    st.write(f"**Time Zone:** {sign}{h}h {m}m {s:.3f}s")

    # Explanation
    st.markdown("### Explanation")
    st.write(f"1. Convert longitude → decimal hours: `{lon:.6f}° ÷ 15 = {dec_hours:.6f}` hours")
    st.write(f"2. Convert decimal hours → H:M:S = `{sign}{h}:{m}:{s:.3f}`")

else:
    # convert time → longitude
    dec_hours = lon / 15  # reverse-derived hours
    # but for explanation, reverse compute sign/h/m/s
    sign, h, m, s = decimal_hours_to_hms(dec_hours)

    st.subheader("Computed Longitude")
    st.write(f"**Longitude:** {lon:.6f}°")

    # Explanation
    st.markdown("### Explanation")
    st.write(f"1. Input time (synced from manual/map/slider) converts to decimal hours: `{sign}{h}h {m}m {s:.3f}s` → `{dec_hours:.6f}` hours")
    st.write(f"2. Convert hours → longitude: `{dec_hours:.6f} × 15 = {lon:.6f}°`")

# ======================================================
# Batch Upload
# ======================================================

st.divider()
st.header("Batch CSV / Excel Converter")

uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded:
    df = pd.read_excel(uploaded) if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)
    st.write(df.head())

    if st.button("Convert File"):
        if st.session_state.mode == "Longitude → Time Zone":
            df["DecimalHours"] = df["Longitude"] / 15
        else:
            df["Longitude"] = df["TZ_Hours"] * 15

        st.download_button("Download Converted File", df.to_csv(index=False), "converted.csv")
        st.write(df)
