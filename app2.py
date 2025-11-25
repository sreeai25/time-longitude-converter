# app.py
import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium

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
    # clamp
    m = min(m, 59)
    s = min(s, 59.999)
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
    return sign, h, m, s

def hms_to_decimal_hours(sign_char, h, m, s):
    total = abs(int(h)) + int(m)/60.0 + float(s)/3600.0
    return total if sign_char == "+" else -total

def hours_to_longitude(decimal_hours):
    return decimal_hours * 15.0

def longitude_to_hours(longitude):
    return longitude / 15.0

# ---------------------------
# Session state defaults
# ---------------------------
for key, val in [("active_lon", 0.0), ("clicked_lat", 0.0),
                 ("mode", "Longitude → Time Zone"),
                 ("slider_lon", 0.0), ("uploaded_df", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------
# Header & introduction
# ---------------------------
st.title("Time Zone ↔ Longitude Converter")
st.markdown("""
**A professional tool to convert between geographic longitude and UTC offsets.**

Features:
- Enter longitude manually (D° M′ S″) or pick on the interactive map.
- Enter time offsets (H:M:S) and convert to longitude.
- Green longitude marker moves with slider, map, or manual input.
- Latitude is displayed for reference.
- Black reference lines every 15° for time zones.
- Batch CSV/Excel upload and download supported.
""")
st.markdown("---")

# ---------------------------
# Layout: Manual Input (left) + Map (right)
# ---------------------------
left_col, right_col = st.columns([1, 2.2])

with left_col:
    st.header("Manual Input")
    mode = st.radio("Conversion mode", ["Longitude → Time Zone", "Time Zone → Longitude"],
                    index=0 if st.session_state.mode.startswith("Longitude") else 1,
                    key="mode")

    if mode == "Longitude → Time Zone":
        # Manual Longitude Inputs with on_change callbacks
        def update_lon():
            new_lon = dms_to_decimal(st.session_state.man_dir,
                                     st.session_state.man_deg,
                                     st.session_state.man_min,
                                     st.session_state.man_sec)
            new_lon = max(-180.0, min(180.0, new_lon))
            st.session_state.active_lon = new_lon
            st.session_state.slider_lon = new_lon

        sgn, cur_deg, cur_min, cur_sec = decimal_to_dms(st.session_state.active_lon)
        cur_sec_clamped = min(max(cur_sec, 0.0), 59.999)
        cur_min_clamped = min(max(cur_min, 0), 59)

        direction = st.selectbox("Direction", ["E (+)", "W (-)"], key="man_dir",
                                 index=0 if sgn>=0 else 1, on_change=update_lon)
        deg = st.number_input("Degrees (0–180)", 0, 180, value=cur_deg, key="man_deg", on_change=update_lon)
        minu = st.number_input("Minutes (0–59)", 0, 59, value=cur_min_clamped, key="man_min", on_change=update_lon)
        sec = st.number_input("Seconds (0–59.999)", 0.0, 59.999, value=round(cur_sec_clamped,6), format="%.6f",
                              key="man_sec", on_change=update_lon)

    else:
        # Manual Time Inputs with on_change
        def update_time():
            dec_hours = hms_to_decimal_hours(st.session_state.man_tz_sign,
                                             st.session_state.man_tz_h,
                                             st.session_state.man_tz_m,
                                             st.session_state.man_tz_s)
            if abs(dec_hours) > 12:
                st.warning("Time offset must be ±12h")
                return
            new_lon = hours_to_longitude(dec_hours)
            new_lon = max(-180.0, min(180.0, new_lon))
            st.session_state.active_lon = new_lon
            st.session_state.slider_lon = new_lon

        dec_hours = longitude_to_hours(st.session_state.active_lon)
        sgn, h_cur, m_cur, s_cur = decimal_hours_to_hms(dec_hours)
        st.selectbox("Sign", ["+", "-"], key="man_tz_sign", index=0 if sgn>=0 else 1, on_change=update_time)
        st.number_input("Hours (0–12)", 0, 12, value=h_cur, key="man_tz_h", on_change=update_time)
        st.number_input("Minutes (0–59)", 0, 59, value=m_cur, key="man_tz_m", on_change=update_time)
        st.number_input("Seconds (0–59.999)", 0.0, 59.999, value=round(s_cur,6), key="man_tz_s",
                        format="%.6f", on_change=update_time)

with right_col:
    st.header("Interactive Map")
    center = [st.session_state.clicked_lat, st.session_state.active_lon]
    m = folium.Map(location=center, zoom_start=3, control_scale=True, prefer_canvas=True)

    # Black vertical lines every 15°
    for lon15 in range(-180, 181, 15):
        folium.PolyLine([[90, lon15], [-90, lon15]], color="black", weight=1, opacity=0.5).add_to(m)

    # Green line: current longitude
    folium.PolyLine([[85, st.session_state.active_lon], [-85, st.session_state.active_lon]],
                    color="green", weight=4, opacity=0.9,
                    tooltip=f"Longitude {st.session_state.active_lon:.6f}°").add_to(m)

    # Marker showing current lat/lon
    icon_html = '<div style="font-size:22px; cursor:pointer; transform:translate(-50%,-50%);">📍</div>'
    folium.Marker([st.session_state.clicked_lat, st.session_state.active_lon], draggable=True,
                  icon=folium.DivIcon(html=icon_html),
                  tooltip="Drag or click map to change longitude").add_to(m)

    map_result = st_folium(m, width=1100, height=650, returned_objects=["last_clicked"])

    # Slider for longitude
    slider_val = st.slider("Longitude slider (±180°)", -180.0, 180.0,
                           st.session_state.active_lon, step=0.1, key="lon_slider")
    if abs(slider_val - st.session_state.active_lon) > 1e-9:
        st.session_state.active_lon = slider_val

    # Map click updates
    if map_result and map_result.get("last_clicked"):
        clicked = map_result["last_clicked"]
        lng = float(clicked.get("lng", st.session_state.active_lon))
        lat = float(clicked.get("lat", st.session_state.clicked_lat))
        st.session_state.active_lon = max(-180.0, min(180.0, lng))
        st.session_state.slider_lon = st.session_state.active_lon
        st.session_state.clicked_lat = max(-90.0, min(90.0, lat))
        st.experimental_rerun()

    # Display selected coordinates
    sgn, d_deg, d_min, d_sec = decimal_to_dms(st.session_state.active_lon)
    dir_text = "E" if sgn >= 0 else "W"
    st.markdown(f"**Selected Longitude (DMS):** {d_deg}° {d_min}' {d_sec:.3f}\" {dir_text}")
    st.markdown(f"**Selected Latitude (decimal):** {st.session_state.clicked_lat:.6f}°")

st.markdown("---")

# ---------------------------
# Result & Explanation
# ---------------------------
st.header("Result & Explanation")
lon = float(st.session_state.active_lon)

if mode == "Longitude → Time Zone":
    dec_deg = lon
    dec_hours = longitude_to_hours(dec_deg)
    sgn_h, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    sign_char = "+" if sgn_h >=0 else "-"
    st.subheader("Computed Time Zone")
    st.write(f"**UTC offset:** {sign_char}{hh} h {mm} m {ss:.3f} s")

    st.markdown("### Explanation")
    st.write(f"Step 1: Convert DMS → decimal degrees: `{d_deg} + {d_min}/60 + {d_sec:.6f}/3600 = {dec_deg:.6f}°`")
    st.write(f"Step 2: Decimal degrees → decimal hours: `{dec_deg:.6f} ÷ 15 = {dec_hours:.6f} hours`")
    st.write(f"Step 3: Decimal hours → H:M:S: `{sign_char}{hh} h {mm} m {ss:.6f} s`")

else:
    dec_hours = longitude_to_hours(lon)
    sgn_h, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    deg_from_hours = hours_to_longitude(dec_hours)
    sgn2, d_deg2, d_min2, d_sec2 = decimal_to_dms(deg_from_hours)
    dir_text = "E" if sgn2>=0 else "W"
    st.subheader("Computed Longitude")
    st.write(f"**Longitude:** {d_deg2}° {d_min2}' {d_sec2:.3f}\" {dir_text}  (decimal: {deg_from_hours:.6f}°)")

    st.markdown("### Explanation")
    st.write(f"Step 1: Time → decimal hours: `{sgn_h}{hh} + {mm}/60 + {ss:.6f}/3600 = {dec_hours:.6f} hours`")
    st.write(f"Step 2: Decimal hours → decimal degrees: `{dec_hours:.6f} × 15 = {deg_from_hours:.6f}°`")
    st.write(f"Step 3: Decimal degrees → D:M:S: `{d_deg2}° {d_min2}' {d_sec2:.6f}\"`")

st.markdown("---")

# ---------------------------
# Batch CSV/Excel Upload (bottom)
# ---------------------------
st.header("Batch CSV / Excel Conversion")
st.write("Upload CSV/XLSX with either longitude (`dir,deg,min,sec`) or time (`sign,h,m,s`) columns.")

uploaded = st.file_uploader("Upload file", type=["csv","xlsx"])
if uploaded:
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        st.dataframe(df.head(8))
        st.session_state.uploaded_df = df

        if st.button("Convert Uploaded File"):
            results = []
            for _, r in df.iterrows():
                try:
                    if {"dir","deg","min","sec"}.issubset(r.index):
                        lon_val = dms_to_decimal(r["dir"], int(r["deg"]), int(r["min"]), float(r["sec"]))
                        dh = longitude_to_hours(lon_val)
                        sgn_h, hh, mm, ss = decimal_hours_to_hms(dh)
                        results.append({
                            "input_type":"lon->tz",
                            "longitude_decimal": lon_val,
                            "tz_sign": "+" if sgn_h>=0 else "-",
                            "tz_h": hh, "tz_m": mm, "tz_s": round(ss,6)
                        })
                    elif {"sign","h","m","s"}.issubset(r.index):
                        dh = hms_to_decimal_hours(r["sign"], int(r["h"]), int(r["m"]), float(r["s"]))
                        lon_val = hours_to_longitude(dh)
                        sgn2, d_deg2, d_min2, d_sec2 = decimal_to_dms(lon_val)
                        results.append({
                            "input_type":"tz->lon",
                            "longitude_decimal": lon_val,
                            "lon_dir": "E" if sgn2>=0 else "W",
                            "lon_deg": d_deg2, "lon_min": d_min2, "lon_sec": round(d_sec2,6)
                        })
                    else:
                        results.append({"error":"unrecognized row format"})
                except Exception as e:
                    results.append({"error": str(e)})
            out = pd.DataFrame(results)
            st.dataframe(out.head(20))
            st.download_button("Download CSV", out.to_csv(index=False), file_name="converted.csv")
    except Exception as e:
        st.error(f"Could not read uploaded file: {e}")
