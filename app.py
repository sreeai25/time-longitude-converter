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
for key, default in [
    ("clicked_lon", None),
    ("clicked_lat", 0.0),
    ("computed_lon", None),
    ("lon_dir", "E (positive)"),
    ("lon_deg", 0),
    ("lon_min", 0),
    ("lon_sec", 0.0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- FUNCTIONS ----------------
def compute_decimal_from_dms():
    sign = 1 if st.session_state.lon_dir.startswith("E") else -1
    return dms_to_decimal(
        st.session_state.lon_deg,
        st.session_state.lon_min,
        st.session_state.lon_sec,
        sign
    )

def compute_decimal_hours():
    sign = 1 if st.session_state.tz_sign == "+" else -1
    return hms_to_decimal_hours(
        st.session_state.tz_h,
        st.session_state.tz_m,
        st.session_state.tz_s,
        sign
    )

# ---------------- APP LAYOUT ----------------
st.title("🕰️ 🌍 Time Zone ↔ Longitude Calculator")
st.markdown(
    "Click on the map to set longitude (auto-filled), or enter manually. "
    "Compute time zone or longitude and see detailed explanations."
)

left, right = st.columns([1, 1])

# ---------------- LEFT PANEL ----------------
with left:
    st.header("Single Conversion")
    mode = st.radio("Conversion Direction", ["Longitude → Time Zone", "Time Zone → Longitude"])

    # ---------------- Auto-fill from map click ----------------
    if st.session_state.clicked_lon is not None:
        sgn, d, m_val, s_val = decimal_to_dms(st.session_state.clicked_lon)
        st.session_state.lon_dir = "E (positive)" if sgn >= 0 else "W (negative)"
        st.session_state.lon_deg = d
        st.session_state.lon_min = m_val
        st.session_state.lon_sec = round(s_val, 6)

    if mode == "Longitude → Time Zone":
        st.subheader("Enter Longitude (D:M:S)")

        lon_dir = st.selectbox(
            "Direction",
            ["E (positive)", "W (negative)"],
            index=["E (positive)", "W (negative)"].index(st.session_state.lon_dir),
            key="lon_dir"
        )
        deg = st.number_input(
            "Degrees",
            min_value=0,
            max_value=180,
            value=st.session_state.lon_deg,
            key="lon_deg"
        )
        minu = st.number_input(
            "Minutes",
            min_value=0,
            max_value=59,
            value=st.session_state.lon_min,
            key="lon_min"
        )
        sec = st.number_input(
            "Seconds",
            min_value=0.0,
            max_value=59.999,
            value=st.session_state.lon_sec,
            key="lon_sec",
            format="%.6f"
        )

        if st.button("Compute Time Zone"):
            dec_lon = compute_decimal_from_dms()
            tz_hours = dec_lon / 15
            sgn, h, m, s = tz_hours_to_hms(tz_hours)
            sign_char = "+" if sgn >= 0 else "-"
            st.success(f"Time Zone: {sign_char}{h:02d}:{m:02d}:{s:06.3f}")

            st.markdown("### Explanation")
            st.write(f"Decimal Degrees = {deg} + ({minu}/60) + ({sec}/3600) = {dec_lon:.6f}°")
            st.write(f"Time Zone (hours) = {dec_lon:.6f}/15 = {tz_hours:.6f} h")
            st.write(f"H:M:S = {h}:{m}:{s:.3f}")

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
            sgn, d, m_val, s_val = decimal_to_dms(lon)
            dir_char = "E" if sgn >= 0 else "W"
            st.success(f"Longitude: {dir_char} {d}° {m_val}' {s_val:.3f}\"")

            st.markdown("### Explanation")
            st.write(f"Decimal Hours = {tz_h} + ({tz_m}/60) + ({tz_s}/3600) = {dec_hours:.6f} h")
            st.write(f"Longitude = {dec_hours:.6f} * 15 = {lon:.6f}°")
            st.write(f"D:M:S = {d}:{m_val}:{s_val:.3f}")

# ---------------- RIGHT PANEL ----------------
with right:
    st.header("Interactive Map")

    # Highlight either computed longitude or last clicked longitude
    highlight_lon = st.session_state.computed_lon if st.session_state.computed_lon is not None else st.session_state.clicked_lon or 0.0
    highlight_lat = st.session_state.clicked_lat or 0.0

    m = folium.Map(location=[highlight_lat, highlight_lon], zoom_start=4)

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

    # ---------------- Map click updates ----------------
    if map_data and map_data.get("last_clicked"):
        st.session_state.clicked_lon = map_data["last_clicked"]["lng"]
        st.session_state.clicked_lat = map_data["last_clicked"]["lat"]
        st.experimental_rerun()

    # Display clicked coordinates
    st.markdown(
        f"**Last Map Click:** Latitude = {st.session_state.clicked_lat:.6f}°, "
        f"Longitude = {st.session_state.clicked_lon if st.session_state.clicked_lon is not None else 0.0:.6f}°"
    )
