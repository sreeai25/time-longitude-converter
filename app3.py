# app_final_updated.py
import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium
import io

st.set_page_config(page_title="Time Zone ↔ Longitude Converter", layout="wide")

# ---------------------------
# Conversion helpers
# ---------------------------
def decimal_to_dms(decimal_deg):
    sign = 1 if decimal_deg >= 0 else -1
    x = abs(decimal_deg)
    d = int(math.floor(x))
    rem = (x - d) * 60
    m = int(math.floor(rem))
    s = (rem - m) * 60
    return sign, d, m, s

def dms_to_decimal(direction_str, deg, minutes, seconds):
    sign = 1
    if direction_str.strip().upper().startswith("W"):
        sign = -1
    dec = abs(int(deg)) + int(minutes)/60.0 + float(seconds)/3600.0
    return sign * dec

def decimal_hours_to_hms(hours):
    sign = 1 if hours >= 0 else -1
    x = abs(hours)
    h = int(math.floor(x))
    rem = (x - h) * 60
    m = int(math.floor(rem))
    s = (rem - m) * 60
    # Clamp
    m = min(m, 59)
    s = min(s, 59.999)
    return sign, h, m, s

def hms_to_decimal_hours(sign_char, h, m, s):
    total = abs(int(h)) + int(m)/60.0 + float(s)/3600.0
    return total if sign_char == "+" else -total

def hours_to_longitude(decimal_hours):
    return decimal_hours * 15.0

def longitude_to_hours(longitude):
    return longitude / 15.0

# ---------------------------
# Initialize session state
# ---------------------------
for key in ["active_lon", "clicked_lat", "mode"]:
    if key not in st.session_state:
        st.session_state[key] = 0.0 if "lon" in key or "lat" in key else "Longitude → Time Zone"

# ---------------------------
# Header & Introduction
# ---------------------------
st.title("Time Zone ↔ Longitude Converter")
st.markdown("""
**Convert between geographic longitude and UTC offsets interactively.**

**Features:**
- Manual input of longitude (D:M:S) or UTC offset (H:M:S)
- Interactive map with green longitude line
- Longitude slider for precise adjustments
- Latitude display for map position
- Black reference lines every 15° for time zones
- Batch CSV/Excel upload for multiple conversions
""")
st.markdown("---")

# ---------------------------
# Layout: Manual input + Map
# ---------------------------
left_col, right_col = st.columns([1,2])

# ---------------------------
# Update functions
# ---------------------------
def update_from_manual_lon():
    lon = dms_to_decimal(st.session_state.man_dir,
                         st.session_state.man_deg,
                         st.session_state.man_min,
                         st.session_state.man_sec)
    st.session_state.active_lon = max(-180.0, min(180.0, lon))

def update_from_manual_time():
    # Use manual time input directly
    dh = hms_to_decimal_hours(st.session_state.man_tz_sign,
                              st.session_state.man_tz_h,
                              st.session_state.man_tz_m,
                              st.session_state.man_tz_s)
    dh = max(-12.0, min(12.0, dh))  # cap ±12h
    lon = hours_to_longitude(dh)
    st.session_state.active_lon = max(-180.0, min(180.0, lon))

# ---------------------------
# Manual Input Column
# ---------------------------
with left_col:
    st.header("Manual Input")
    mode = st.radio("Conversion mode", ["Longitude → Time Zone", "Time Zone → Longitude"],
                    index=0 if st.session_state.mode.startswith("Longitude") else 1)
    st.session_state.mode = mode

    if mode == "Longitude → Time Zone":
        sgn, d, m, s = decimal_to_dms(st.session_state.active_lon)
        st.selectbox("Direction", ["E (+)","W (-)"],
                     index=0 if sgn>=0 else 1,
                     key="man_dir", on_change=update_from_manual_lon)
        st.number_input("Degrees (0–180)", 0, 180, value=d,
                        key="man_deg", on_change=update_from_manual_lon)
        st.number_input("Minutes (0–59)", 0, 59, value=m,
                        key="man_min", on_change=update_from_manual_lon)
        st.number_input("Seconds (0–59.999)", 0.0, 59.999, value=round(s,3),
                        format="%.3f", key="man_sec", on_change=update_from_manual_lon)
        # Display result here
        dec_hours = longitude_to_hours(st.session_state.active_lon)
        sgn_h, hh, mm, ss = decimal_hours_to_hms(dec_hours)
        sign_char = "+" if sgn_h>=0 else "-"
        st.subheader(f"Computed UTC offset: UTC{sign_char}{hh}:{mm}:{ss:.3f}")
    else:
        dh = longitude_to_hours(st.session_state.active_lon)
        sgn_h, hh, mm, ss = decimal_hours_to_hms(dh)
        st.selectbox("Sign", ["+","-"], index=0 if sgn_h>=0 else 1,
                     key="man_tz_sign", on_change=update_from_manual_time)
        st.number_input("Hours (0–12)", 0, 12, value=hh,
                        key="man_tz_h", on_change=update_from_manual_time)
        st.number_input("Minutes (0–59)", 0, 59, value=mm,
                        key="man_tz_m", on_change=update_from_manual_time)
        st.number_input("Seconds (0–59.999)", 0.0, 59.999, value=round(ss,3),
                        format="%.3f", key="man_tz_s", on_change=update_from_manual_time)
        # Display result here
        dh_manual = hms_to_decimal_hours(st.session_state.man_tz_sign,
                                         st.session_state.man_tz_h,
                                         st.session_state.man_tz_m,
                                         st.session_state.man_tz_s)
        dh_capped = max(-12.0, min(12.0, dh_manual))
        lon_calc = hours_to_longitude(dh_capped)
        sgn2, d_deg2, d_min2, d_sec2 = decimal_to_dms(lon_calc)
        dir_text2 = "E" if sgn2>=0 else "W"
        st.subheader(f"Computed Longitude: {d_deg2}° {d_min2}' {d_sec2:.3f}\" {dir_text2}")

# ---------------------------
# Map Column
# ---------------------------
with right_col:
    st.header("Interactive Map")
    m = folium.Map(location=[st.session_state.clicked_lat, st.session_state.active_lon],
                   zoom_start=3, control_scale=True)
    # Black lines every 15°
    for lon15 in range(-180,181,15):
        folium.PolyLine([[90,lon15],[-90,lon15]], color="black", weight=1, opacity=0.5).add_to(m)
    # Green line
    folium.PolyLine([[85,st.session_state.active_lon],[-85,st.session_state.active_lon]],
                    color="green", weight=4, opacity=0.9).add_to(m)
    # Marker
    folium.Marker([st.session_state.clicked_lat, st.session_state.active_lon],
                  icon=folium.Icon(color="blue"), draggable=True).add_to(m)
    map_data = st_folium(m, width=1100, height=600, returned_objects=["last_clicked"])

# ---------------------------
# Slider
# ---------------------------
slider_val = st.slider("Longitude slider (±180°)", -180.0, 180.0,
                       value=st.session_state.active_lon, step=0.1)
if slider_val != st.session_state.active_lon:
    st.session_state.active_lon = slider_val

# ---------------------------
# Map click updates
# ---------------------------
if map_data and map_data.get("last_clicked"):
    clicked = map_data["last_clicked"]
    lat = float(clicked.get("lat", st.session_state.clicked_lat))
    lng = float(clicked.get("lng", st.session_state.active_lon))
    st.session_state.clicked_lat = max(-90, min(90, lat))
    st.session_state.active_lon = max(-180, min(180, lng))
    st.experimental_rerun()

# ---------------------------
# Display selected coordinates
# ---------------------------
sgn, d_deg, d_min, d_sec = decimal_to_dms(st.session_state.active_lon)
dir_text = "E" if sgn>=0 else "W"
st.markdown(f"**Selected Longitude (DMS):** {d_deg}° {d_min}' {d_sec:.3f}\" {dir_text}")
st.markdown(f"**Selected Latitude (decimal):** {st.session_state.clicked_lat:.6f}°")

# ---------------------------
# Explanation (after map)
# ---------------------------
st.header("Detailed Explanation")
if mode == "Longitude → Time Zone":
    st.write(f"DMS → decimal degrees: {d_deg} + {d_min}/60 + {d_sec:.3f}/3600 = {st.session_state.active_lon:.6f}°")
    dec_hours = longitude_to_hours(st.session_state.active_lon)
    sgn_h, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    st.write(f"Decimal degrees → hours: {st.session_state.active_lon:.6f} ÷ 15 = {dec_hours:.6f} h")
    sign_char = "+" if sgn_h>=0 else "-"
    st.write(f"Decimal hours → H:M:S = {sign_char}{hh}:{mm}:{ss:.3f}")
else:
    dh_manual = hms_to_decimal_hours(st.session_state.man_tz_sign,
                                     st.session_state.man_tz_h,
                                     st.session_state.man_tz_m,
                                     st.session_state.man_tz_s)
    dh_capped = max(-12.0, min(12.0, dh_manual))
    lon_calc = hours_to_longitude(dh_capped)
    sgn2, d_deg2, d_min2, d_sec2 = decimal_to_dms(lon_calc)
    dir_text2 = "E" if sgn2>=0 else "W"
    st.write(f"Time → decimal hours: {st.session_state.man_tz_h} + "
             f"{st.session_state.man_tz_m}/60 + {st.session_state.man_tz_s}/3600 = {dh_manual:.6f} h")
    st.write(f"Decimal hours → Longitude: {dh_capped:.6f} × 15 = {lon_calc:.6f}°")
    st.write(f"Decimal degrees → D:M:S = {d_deg2}° {d_min2}' {d_sec2:.3f}\" {dir_text2}")

# ---------------------------
# Batch CSV/Excel Upload with Guidance + Templates
# ---------------------------
st.header("Batch CSV / Excel Conversion")
st.markdown("""
**Upload Instructions:**

- Supported file types: **CSV** or **Excel (.xlsx)**.
- For **Longitude → Time Zone**, include columns: `dir` (E/W), `deg` (0–180), `min` (0–59), `sec` (0.0–59.999)
- For **Time Zone → Longitude**, include columns: `sign` (+/-), `h` (0–12), `m` (0–59), `s` (0.0–59.999)
- Column names must **match exactly**. Empty/invalid rows will be flagged.
""")

# Templates
lon_to_tz_template = pd.DataFrame([{"dir":"E","deg":45,"min":30,"sec":0.0}])
tz_to_lon_template = pd.DataFrame([{"sign":"+","h":3,"m":30,"s":0.0}])

col1, col2 = st.columns(2)
with col1:
    csv_buffer = io.StringIO()
    lon_to_tz_template.to_csv(csv_buffer, index=False)
    st.download_button("Download Longitude → Time Zone CSV Template",
                       csv_buffer.getvalue(),
                       "lon_to_tz_template.csv","text/csv")
with col2:
    csv_buffer2 = io.StringIO()
    tz_to_lon_template.to_csv(csv_buffer2, index=False)
    st.download_button("Download Time Zone → Longitude CSV Template",
                       csv_buffer2.getvalue(),
                       "tz_to_lon_template.csv","text/csv")

uploaded = st.file_uploader("Upload your CSV/Excel file", type=["csv","xlsx"])
if uploaded:
    df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
    st.dataframe(df.head())
    if st.button("Convert Uploaded File"):
        results = []
        for _, r in df.iterrows():
            try:
                if {"dir","deg","min","sec"}.issubset(r.index):
                    lon_val = dms_to_decimal(r["dir"], int(r["deg"]), int(r["min"]), float(r["sec"]))
                    dh = longitude_to_hours(lon_val)
                    sgn_h, hh, mm, ss = decimal_hours_to_hms(dh)
                    results.append({"input_type":"lon->tz","longitude_decimal":lon_val,
                                    "tz_sign":"+" if sgn_h>=0 else "-","tz_h":hh,"tz_m":mm,"tz_s":round(ss,3)})
                elif {"sign","h","m","s"}.issubset(r.index):
                    dh = hms_to_decimal_hours(r["sign"], int(r["h"]), int(r["m"]), float(r["s"]))
                    dh_capped = max(-12, min(12, dh))
                    lon_val = hours_to_longitude(dh_capped)
                    sgn2, d_deg2, d_min2, d_sec2 = decimal_to_dms(lon_val)
                    results.append({"input_type":"tz->lon","longitude_decimal":lon_val,
                                    "lon_dir":"E" if sgn2>=0 else "W",
                                    "lon_deg":d_deg2,"lon_min":d_min2,"lon_sec":round(d_sec2,3)})
            except:
                results.append({"error":"invalid row"})
        st.dataframe(pd.DataFrame(results))
