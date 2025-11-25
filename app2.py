# app.py
import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# ---------------------------
# Conversion helpers
# ---------------------------
def decimal_to_dms(decimal_deg):
    """Return (sign, deg, min, sec) where sign = 1 (E) or -1 (W)"""
    sign = 1 if decimal_deg >= 0 else -1
    x = abs(decimal_deg)
    d = int(math.floor(x))
    rem = (x - d) * 60
    m = int(math.floor(rem))
    s = (rem - m) * 60
    return sign, d, m, s

def dms_to_decimal(direction_str, deg, minutes, seconds):
    """direction_str: 'E (+)' or 'W (-)'"""
    sign = 1
    if isinstance(direction_str, str) and direction_str.strip().upper().startswith("W"):
        sign = -1
    dec = abs(int(deg)) + int(minutes) / 60.0 + float(seconds) / 3600.0
    return sign * dec

def decimal_hours_to_hms(hours):
    sign = 1 if hours >= 0 else -1
    x = abs(hours)
    h = int(math.floor(x))
    rem = (x - h) * 60
    m = int(math.floor(rem))
    s = (rem - m) * 60
    return sign, h, m, s

def hms_to_decimal_hours(sign_char, h, m, s):
    total = abs(int(h)) + int(m) / 60.0 + float(s) / 3600.0
    return total if sign_char == "+" else -total

def hours_to_longitude(decimal_hours):
    return decimal_hours * 15.0

def longitude_to_hours(longitude):
    return longitude / 15.0

# ---------------------------
# Session state defaults
# ---------------------------
if "active_lon" not in st.session_state:
    st.session_state.active_lon = 0.0  # master longitude in decimal degrees
if "clicked_lat" not in st.session_state:
    st.session_state.clicked_lat = 0.0
if "mode" not in st.session_state:
    st.session_state.mode = "Longitude → Time Zone"
if "slider_lon" not in st.session_state:
    st.session_state.slider_lon = 0.0

# ---------------------------
# Page header & intro (friendly, professional)
# ---------------------------
st.title("Time Zone ↔ Longitude Converter")
st.markdown(
    """
    **A friendly, professional tool to convert between geographic longitude and time zone offsets.**
    
    Use this app to:
    - Enter longitude (D° M′ S″) manually or pick it visually on the interactive map.
    - Enter time offsets (H:M:S) and convert to longitude.
    - Move the green longitude marker by *clicking*, *dragging*, or using the *slider* — everything stays synchronized.
    - Upload CSV/Excel batches for bulk conversions and download results.
    
    The interface keeps manual inputs, the slider, and the map fully synchronized so you can interact however you prefer.
    """
)

st.markdown("---")

# ---------------------------
# Two-column layout: Manual inputs (left) and map (right)
# ---------------------------
left_col, right_col = st.columns([1, 2.2])  # map gets more space

with left_col:
    st.header("Manual Input & Controls")

    # Mode selection
    st.radio("Conversion mode", ["Longitude → Time Zone", "Time Zone → Longitude"], index=0 if st.session_state.mode.startswith("Longitude") else 1, key="mode")
    mode = st.session_state.mode

    st.markdown("**Manual values (edit & click Apply to commit)**")

    if mode == "Longitude → Time Zone":
        # Show current active_lon as DMS
        sign, cur_deg, cur_min, cur_sec = decimal_to_dms(st.session_state.active_lon)
        dir_default = "E (+)" if sign >= 0 else "W (-)"

        direction = st.selectbox("Direction", ["E (+)", "W (-)"], index=0 if dir_default.startswith("E") else 1, key="man_dir")
        deg = st.number_input("Degrees (0–180)", min_value=0, max_value=180, value=cur_deg, step=1, key="man_deg")
        minu = st.number_input("Minutes (0–59)", min_value=0, max_value=59, value=cur_min, step=1, key="man_min")
        sec = st.number_input("Seconds (0.000–59.999)", min_value=0.0, max_value=59.999, value=round(cur_sec, 6), format="%.6f", key="man_sec")

        # Apply manual -> update active_lon
        if st.button("Apply Manual Longitude"):
            # enforce caps
            if deg > 180:
                st.error("Degrees must be ≤ 180")
            else:
                new_lon = dms_to_decimal(direction, deg, minu, sec)
                # clamp
                if new_lon < -180: new_lon = -180.0
                if new_lon > 180: new_lon = 180.0
                st.session_state.active_lon = float(new_lon)
                st.session_state.slider_lon = float(new_lon)
                # no need to store map; instruct rerun to reflect changes everywhere
                st.experimental_rerun()

    else:
        # Time → Longitude manual inputs (cap ±12 hours)
        # We'll store sign separately and hours (0..12), minutes, seconds
        # show current active_lon converted to hours for defaults
        cur_hours = longitude_to_hours(st.session_state.active_lon)
        cur_sign, cur_h, cur_m, cur_s = decimal_hours_to_hms(cur_hours)
        sign_choice = st.selectbox("Sign", ["+", "-"], index=0 if cur_sign >= 0 else 1, key="man_tz_sign")
        h = st.number_input("Hours (0–12)", min_value=0, max_value=12, value=cur_h, key="man_tz_h")
        m = st.number_input("Minutes (0–59)", min_value=0, max_value=59, value=cur_m, key="man_tz_m")
        s = st.number_input("Seconds (0.0–59.999)", min_value=0.0, max_value=59.999, value=round(cur_s, 6), format="%.6f", key="man_tz_s")

        if st.button("Apply Manual Time"):
            dec_hours = hms_to_decimal_hours(sign_choice, h, m, s)
            # cap hours to +/-12
            if abs(dec_hours) > 12.0 + 1e-9:
                st.error("Time offset must be within ±12 hours")
            else:
                new_lon = hours_to_longitude(dec_hours)
                # clamp to ±180
                if new_lon < -180: new_lon = -180.0
                if new_lon > 180: new_lon = 180.0
                st.session_state.active_lon = float(new_lon)
                st.session_state.slider_lon = float(new_lon)
                st.experimental_rerun()

    st.markdown("---")
    # Batch upload section (simple)
    st.subheader("Batch CSV / Excel")
    st.write("Upload rows either as longitude (columns: `dir,deg,min,sec`) or timezone (`sign,h,m,s`).")
    uploaded = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.write("Preview:")
            st.dataframe(df.head(8))
            if st.button("Convert Uploaded File"):
                results = []
                for _, r in df.iterrows():
                    try:
                        if {"dir","deg","min","sec"}.issubset(r.index):
                            lon_val = dms_to_decimal(r["dir"], int(r["deg"]), int(r["min"]), float(r["sec"]))
                            dh = longitude_to_hours(lon_val)
                            sign_h, hh, mm, ss = decimal_hours_to_hms(dh)
                            results.append({
                                "input_type":"lon->tz",
                                "longitude_decimal": lon_val,
                                "tz_sign": "+" if sign_h>=0 else "-",
                                "tz_h": hh, "tz_m": mm, "tz_s": round(ss,6)
                            })
                        elif {"sign","h","m","s"}.issubset(r.index):
                            dh = hms_to_decimal_hours(r["sign"], int(r["h"]), int(r["m"]), float(r["s"]))
                            lon_val = hours_to_longitude(dh)
                            sgn, dd, dm, ds = decimal_to_dms(lon_val)
                            results.append({
                                "input_type":"tz->lon",
                                "longitude_decimal": lon_val,
                                "lon_dir": "E" if sgn>=0 else "W",
                                "lon_deg": dd, "lon_min": dm, "lon_sec": round(ds,6)
                            })
                        else:
                            results.append({"error":"unrecognized row format"})
                    except Exception as e:
                        results.append({"error": str(e)})
                out = pd.DataFrame(results)
                st.write("Converted results:")
                st.dataframe(out.head(20))
                st.download_button("Download CSV", out.to_csv(index=False), file_name="converted.csv")
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")

with right_col:
    st.header("Interactive Map (large)")

    # Compose map centered at (clicked_lat, active_lon)
    center = [st.session_state.clicked_lat, st.session_state.active_lon]
    m = folium.Map(location=center, zoom_start=3, control_scale=True, prefer_canvas=True)

    # Draw green vertical longitude line
    folium.PolyLine([[85, st.session_state.active_lon], [-85, st.session_state.active_lon]],
                    color="green", weight=4, opacity=0.9, tooltip=f"Longitude {st.session_state.active_lon:.6f}°").add_to(m)

    # Draggable marker - use DivIcon so cursor is pointer-like
    icon_html = '<div style="font-size:22px; cursor:pointer; transform:translate(-50%,-50%);">📍</div>'
    folium.Marker([st.session_state.clicked_lat, st.session_state.active_lon], draggable=True,
                  icon=folium.DivIcon(html=icon_html), tooltip="Drag or click map to change longitude").add_to(m)

    # Render map (large)
    map_result = st_folium(m, width=1100, height=650, returned_objects=["last_clicked", "last_object"])

    # Slider under map (keeps full-width in right column)
    st.markdown("#### Adjust longitude with slider")
    # use state default slider_lon if exists
    if "slider_lon" not in st.session_state:
        st.session_state.slider_lon = st.session_state.active_lon
    slider_val = st.slider("Longitude slider (±180°)", -180.0, 180.0, float(st.session_state.active_lon), step=0.1, key="slider_lon")

    # If slider changed relative to active_lon, update active_lon (synchronization)
    if abs(slider_val - st.session_state.active_lon) > 1e-9:
        st.session_state.active_lon = float(slider_val)
        # update clicked_lat remains same, but re-render next run to update map
        # don't force rerun here; streamlit will re-run this script on interaction

    # Process map interactions after rendering
    try:
        if map_result:
            # Map click
            if map_result.get("last_clicked"):
                clicked = map_result["last_clicked"]
                if isinstance(clicked, dict) and clicked.get("lng") is not None:
                    lng = float(clicked["lng"])
                    lat = float(clicked.get("lat", 0.0))
                    # Cap
                    if lng < -180: lng = -180.0
                    if lng > 180: lng = 180.0
                    st.session_state.clicked_lat = lat
                    st.session_state.active_lon = lng
                    st.session_state.slider_lon = lng
                    # re-run so manual inputs update immediately
                    st.experimental_rerun()

            # Marker drag: many streamlit-folium versions return 'last_object' when dragging marker
            last_object = map_result.get("last_object")
            if last_object and isinstance(last_object, dict):
                lng = None
                if "lng" in last_object and last_object["lng"] is not None:
                    lng = float(last_object["lng"])
                elif "lon" in last_object and last_object["lon"] is not None:
                    lng = float(last_object["lon"])
                elif "longitude" in last_object and last_object["longitude"] is not None:
                    lng = float(last_object["longitude"])
                lat = None
                if "lat" in last_object and last_object["lat"] is not None:
                    lat = float(last_object["lat"])
                elif "latitude" in last_object and last_object["latitude"] is not None:
                    lat = float(last_object["latitude"])
                if lng is not None:
                    # Cap
                    if lng < -180: lng = -180.0
                    if lng > 180: lng = 180.0
                    st.session_state.active_lon = lng
                    if lat is not None:
                        st.session_state.clicked_lat = lat
                    st.session_state.slider_lon = lng
                    st.experimental_rerun()
    except Exception:
        # swallow map parsing errors to avoid app crash across versions
        pass

    # Show selected longitude (in DMS) and latitude (decimal informational)
    sgn, d_deg, d_min, d_sec = decimal_to_dms(st.session_state.active_lon)
    dir_text = "E" if sgn >= 0 else "W"
    st.markdown(f"**Selected Longitude (DMS):** {d_deg}° {d_min}' {d_sec:.3f}\" {dir_text}")
    st.markdown(f"**Selected Latitude (decimal):** {st.session_state.clicked_lat:.6f}°")

# ---------------------------
# Results (full width, below columns)
# ---------------------------
st.markdown("---")
st.header("Result")

lon = float(st.session_state.active_lon)

if st.session_state.mode == "Longitude → Time Zone":
    # Convert longitude (DMS shown above) -> decimal degrees -> hours -> HMS
    # We'll present both the intermediate decimal value and final HMS
    # Step: DMS -> decimal (showed in explanation)
    dec_deg = lon
    dec_hours = longitude_to_hours(dec_deg)
    sgn_h, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    sign_char = "+" if sgn_h >= 0 else "-"

    st.subheader("Computed Time Zone")
    st.write(f"**UTC offset:** {sign_char}{hh} h {mm} m {ss:.3f} s")

    # Explanation follows
    st.markdown("### Explanation")
    st.write("**Step 1 — Convert D:M:S to decimal degrees (if needed):**")
    # show the DMS -> decimal formula only if DMS input was used or to clarify
    st.write(f"`{d_deg} + {d_min}/60 + {d_sec:.6f}/3600 = {dec_deg:.6f}°`")
    st.write("**Step 2 — Convert decimal degrees to decimal hours:**")
    st.write(f"`{dec_deg:.6f} ÷ 15 = {dec_hours:.6f} hours`")
    st.write("**Step 3 — Convert decimal hours to H:M:S:**")
    st.write(f"`{sign_char}{hh} hours, {mm} minutes, {ss:.6f} seconds`")

else:
    # Time -> Longitude
    # For display, get hours from active lon (we keep all synced): but manual time inputs are used to apply new lon
    dec_hours = longitude_to_hours(lon)  # derived hours from current master lon
    sign_h, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    st.subheader("Computed Longitude")
    dir_text = "E" if sign_h >= 0 else "W"
    # Convert hours -> degrees
    deg_from_hours = hours_to_longitude(dec_hours)
    sgn2, d_deg2, d_min2, d_sec2 = decimal_to_dms(deg_from_hours)

    st.write(f"**Longitude:** {d_deg2}° {d_min2}' {d_sec2:.3f}\" {dir_text}  (decimal: {deg_from_hours:.6f}°)")

    # Explanation (time-first)
    st.markdown("### Explanation")
    st.write("**Step 1 — Time (H:M:S) → decimal hours**")
    st.write(f"`{sign_h}{hh} + {mm}/60 + {ss:.6f}/3600 = {dec_hours:.6f} hours`")
    st.write("**Step 2 — decimal hours → decimal degrees**")
    st.write(f"`{dec_hours:.6f} × 15 = {deg_from_hours:.6f}°`")
    st.write("**Step 3 — decimal degrees → D:M:S**")
    st.write(f"`{d_deg2}° {d_min2}' {d_sec2:.6f}\"`")

st.markdown("---")
st.caption("Notes: Manual input, map clicks/drags, and the slider are synchronized. Latitude shown is informational only; time ↔ longitude conversion uses only longitude values.")
