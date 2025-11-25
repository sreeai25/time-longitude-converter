import streamlit as st
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
if "map_lon" not in st.session_state:
    st.session_state.map_lon = 0.0
if "map_lat" not in st.session_state:
    st.session_state.map_lat = 0.0

if "map_lon_dir" not in st.session_state:
    st.session_state.map_lon_dir = "E (positive)"
if "map_lon_deg" not in st.session_state:
    st.session_state.map_lon_deg = 0
if "map_lon_min" not in st.session_state:
    st.session_state.map_lon_min = 0
if "map_lon_sec" not in st.session_state:
    st.session_state.map_lon_sec = 0.0

if "computed_lon" not in st.session_state:
    st.session_state.computed_lon = None

# ---------------- FUNCTIONS ----------------
def update_from_map(lat, lon):
    """Update session state with map click and auto-fill longitude fields safely."""
    st.session_state.map_lat = lat
    st.session_state.map_lon = lon

    sgn, d, m, s = decimal_to_dms(lon)

    st.session_state.map_lon_dir = "E (positive)" if sgn >= 0 else "W (negative)"
    st.session_state.map_lon_deg = d
    st.session_state.map_lon_min = m
    st.session_state.map_lon_sec = round(s, 6)

    # Only update widget keys if they exist to avoid APIException
    for key, value in [
        ("lon_dir", st.session_state.map_lon_dir),
        ("lon_deg", st.session_state.map_lon_deg),
        ("lon_min", st.session_state.map_lon_min),
        ("lon_sec", st.session_state.map_lon_sec),
    ]:
        if key in st.session_state:
            st.session_state[key] = value

    # Update computed longitude for green line highlighting
    st.session_state.computed_lon = lon

def compute_decimal_from_dms():
    sign = 1 if st.session_state.lon_dir.startswith("E") else -1
    return dms_to_decimal(
        st.session_state.lon_deg, st.session_state.lon_min, st.session_state.lon_sec, sign
    )

def compute_decimal_hours():
    sign = 1 if st.session_state.tz_sign == "+" else -1
    return hms_to_decimal_hours(
        st.session_state.tz_h, st.session_state.tz_m, st.session_state.tz_s, sign
    )

# ---------------- APP LAYOUT ----------------
st.title("🕰️ 🌍 Time Zone ↔ Longitude Calculator")
st.markdown(
    "Convert **longitude ↔ time zone offset**, click on the map to auto-fill values, "
    "and see detailed step-by-step explanations."
)

left, right = st.columns([1, 1])

# ---------------- LEFT PANEL ----------------
with left:
    st.header("Single Conversion")
    mode = st.radio("Conversion Direction", ["Longitude → Time Zone", "Time Zone → Longitude"])

    if mode == "Longitude → Time Zone":
        st.subheader("Enter Longitude (D:M:S)")

        lon_dir = st.selectbox(
            "Direction",
            ["E (positive)", "W (negative)"],
            key="lon_dir",
            index=["E (positive)", "W (negative)"].index(
                st.session_state.get("map_lon_dir", "E (positive)")
            ),
        )
        deg = st.number_input(
            "Degrees",
            min_value=0,
            max_value=180,
            value=st.session_state.get("map_lon_deg", 0),
            key="lon_deg",
        )
        minu = st.number_input(
            "Minutes",
            min_value=0,
            max_value=59,
            value=st.session_state.get("map_lon_min", 0),
            key="lon_min",
        )
        sec = st.number_input(
            "Seconds",
            min_value=0.0,
            max_value=59.999,
            value=st.session_state.get("map_lon_sec", 0.0),
            key="lon_sec",
            format="%.6f",
        )

        if st.button("Compute Time Zone"):
            dec_lon = compute_decimal_from_dms()
            tz_hours = dec_lon / 15
            sgn, h, m, s = tz_hours_to_hms(tz_hours)
            sign_char = "+" if sgn >= 0 else "-"

            st.success(f"Time Zone: {sign_char}{h:02d}:{m:02d}:{s:06.3f}")

            st.markdown("### Explanation")
            st.write(f"**Step 1: Convert DMS → Decimal Degrees**")
            st.write(
                f"Decimal Degrees = degrees + (minutes / 60) + (seconds / 3600)\n"
                f"= {deg} + ({minu}/60) + ({sec}/3600)\n"
                f"= {dec_lon:.6f}°"
            )
            st.write("**Step 2: Decimal Degrees → Time Zone (hours)**")
            st.write(f"Time offset = decimal longitude / 15\n= {dec_lon:.6f}/15 = {tz_hours:.6f} h")
            st.write("**Step 3: Decimal Hours → H:M:S**")
            st.write(f"H = {h}, M = {m}, S = {s:.3f}")
            st.write(f"Result: {sign_char}{h:02d}:{m:02d}:{s:06.3f}")

    else:
        st.subheader("Enter Time Zone Offset")
        tz_sign = st.selectbox("Sign", ["+", "-"], key="tz_sign")
        tz_h = st.number_input("Hours", min_value=0, max_value=18, key="tz_h")
        tz_m = st.number_input("Minutes", min_value=0, max_value=59, key="tz_m")
        tz_s = st.number_input("Seconds", min_value=0.0, max_value=59.999, key="tz_s")

        if st.button("Compute Longitude"):
            dec_hours = compute_decimal_hours()
            lon = longitude_from_timezone_hours(dec_hours)
            st.session_state.computed_lon = lon
            sgn, d, m, s = decimal_to_dms(lon)
            dir_char = "E" if sgn >= 0 else "W"
            st.success(f"Longitude: {dir_char} {d}° {m}' {s:.3f}\"")

            st.markdown("### Explanation")
            st.write("**Step 1: Convert H:M:S → Decimal Hours**")
            st.write(f"Decimal Hours = hours + (minutes / 60) + (seconds / 3600)")
            st.write(f"= {tz_h} + ({tz_m}/60) + ({tz_s}/3600) = {dec_hours:.6f} h")
            st.write("**Step 2: Decimal Hours → Longitude (Decimal Degrees)**")
            st.write(f"Longitude = decimal hours × 15 = {lon:.6f}°")
            st.write("**Step 3: Decimal Degrees → D:M:S**")
            st.write(f"D = {d}, M = {m}, S = {s:.3f}")
            st.write(f"Result: {dir_char} {d}° {m}' {s:.3f}\"")

# ---------------- RIGHT PANEL ----------------
with right:
    st.header("Interactive Map")

    # Highlight longitude: computed if exists, else map click
    highlight_lon = (
        st.session_state.computed_lon
        if st.session_state.computed_lon is not None
        else st.session_state.map_lon
    )

    center_lon = highlight_lon
    center_lat = st.session_state.map_lat

    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

    # Gray meridians
    for lon_val in range(-180, 181, 30):
        folium.PolyLine([[90, lon_val], [-90, lon_val]], color="gray", weight=1).add_to(m)

    # Green line for selected/computed longitude
    folium.PolyLine(
        locations=[[90, highlight_lon], [-90, highlight_lon]],
        color="green",
        weight=3,
        opacity=0.7,
        tooltip=f"Selected/Computed Longitude: {highlight_lon:.4f}°"
    ).add_to(m)

    map_data = st_folium(m, width=700, height=450)

    # Map click updates
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        update_from_map(lat, lon)
        st.success(f"Map clicked: Latitude {lat:.4f}°, Longitude {lon:.4f}°")
