# app.py
import io
import math
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import plugins

st.set_page_config(page_title="Time Zone ↔ Longitude (Sync Map & Inputs)", layout="wide")

# -------------------------
# Helper conversion functions
# -------------------------
def dms_to_decimal(deg: int, minutes: int, seconds: float, direction: str) -> float:
    sign = 1 if str(direction).strip().upper().startswith("E") else -1
    dec = abs(int(deg)) + abs(int(minutes)) / 60.0 + float(seconds) / 3600.0
    return sign * dec

def decimal_to_dms(decimal_deg: float):
    sign = 1 if decimal_deg >= 0 else -1
    dd = abs(decimal_deg)
    deg = int(math.floor(dd))
    rem = (dd - deg) * 60
    minutes = int(math.floor(rem))
    seconds = (rem - minutes) * 60
    return sign, deg, minutes, seconds

def hms_to_decimal_hours(sign: str, h: int, m: int, s: float) -> float:
    dec = abs(int(h)) + abs(int(m)) / 60.0 + float(s) / 3600.0
    return dec if str(sign) == "+" else -dec

def decimal_hours_to_hms(dec_hours: float):
    sign = "+" if dec_hours >= 0 else "-"
    dh = abs(dec_hours)
    hours = int(math.floor(dh))
    rem = (dh - hours) * 60
    minutes = int(math.floor(rem))
    seconds = (rem - minutes) * 60
    return sign, hours, minutes, seconds

def longitude_from_decimal_hours(dec_hours: float) -> float:
    return dec_hours * 15.0

def decimal_longitude_to_decimal_hours(lon: float) -> float:
    return lon / 15.0

# -------------------------
# Session state defaults
# -------------------------
defaults = {
    "mode": "Longitude → Time Zone",
    "last_action": None,           # "manual" or "map" or "slider"
    "computed_lon": 0.0,           # currently selected longitude (primitive)
    "clicked_lat": 0.0,
    "clicked_lon": 0.0,
    # Manual DMS fields (Longitude)
    "lon_dir": "E (+)",
    "lon_deg": 0,
    "lon_min": 0,
    "lon_sec": 0.0,
    # Manual HMS fields (Time zone)
    "tz_sign": "+",
    "tz_h": 0,
    "tz_m": 0,
    "tz_s": 0.0,
    # Slider
    "slider_lon": 0.0,
    # Uploaded conversion output
    "last_batch_out": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------
# Callbacks to keep in-sync
# -------------------------
def on_manual_longitude_change():
    """
    Called when user edits manual longitude (DMS) fields and hits 'Apply'.
    Will compute decimal longitude, cap to [-180,180], update computed_lon and slider.
    """
    try:
        lon = dms_to_decimal(st.session_state["lon_deg"], st.session_state["lon_min"], st.session_state["lon_sec"], st.session_state["lon_dir"])
        # cap
        lon = max(-180.0, min(180.0, lon))
        st.session_state["computed_lon"] = lon
        st.session_state["slider_lon"] = lon
        st.session_state["last_action"] = "manual"
    except Exception as e:
        st.error(f"Invalid manual longitude: {e}")

def on_manual_timezone_change():
    """
    Called when user edits manual timezone (HMS) fields and hits 'Apply'.
    Compute longitude = hours * 15, cap hours to [-12,12], cap longitude to [-180,180].
    """
    try:
        # make sure hours are within 0..12 and sign handles +/-; we store sign separately
        hours = st.session_state["tz_h"]
        if hours < 0:
            hours = 0
            st.session_state["tz_h"] = 0
        if hours > 12:
            hours = 12
            st.session_state["tz_h"] = 12

        dec_hours = hms_to_decimal_hours(st.session_state["tz_sign"], st.session_state["tz_h"], st.session_state["tz_m"], st.session_state["tz_s"])
        # cap decimal hours to [-12,12]
        dec_hours = max(-12.0, min(12.0, dec_hours))
        lon = longitude_from_decimal_hours(dec_hours)
        lon = max(-180.0, min(180.0, lon))
        st.session_state["computed_lon"] = lon
        st.session_state["slider_lon"] = lon
        st.session_state["last_action"] = "manual"
    except Exception as e:
        st.error(f"Invalid manual timezone: {e}")

def on_slider_change():
    """
    Called when slider value changes.
    Update computed_lon and sync manual fields (both DMS and HMS) if 'sync' is desired.
    """
    lon = float(st.session_state["slider_lon"])
    # cap
    lon = max(-180.0, min(180.0, lon))
    st.session_state["computed_lon"] = lon
    st.session_state["last_action"] = "slider"
    # Update manual DMS
    sgn, d, m, s = decimal_to_dms(lon)
    st.session_state["lon_dir"] = "E (+)" if sgn >= 0 else "W (-)"
    st.session_state["lon_deg"] = d
    st.session_state["lon_min"] = m
    st.session_state["lon_sec"] = round(s, 6)
    # Update manual HMS
    dec_hours = decimal_longitude_to_decimal_hours(lon)
    sgn2, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    st.session_state["tz_sign"] = sgn2
    st.session_state["tz_h"] = hh if hh <= 12 else 12
    st.session_state["tz_m"] = mm
    st.session_state["tz_s"] = round(ss, 6)

# -------------------------
# Top controls & layout
# -------------------------
st.title("Time Zone ↔ Longitude — Synchronized Map & Inputs")

# Top columns: left (manual inputs) narrower, right (map) larger
left_col, right_col = st.columns([1, 1.8])

with left_col:
    st.subheader("Manual Inputs")

    st.radio_label = st.radio("Conversion mode", ["Longitude → Time Zone", "Time Zone → Longitude"], index=0 if st.session_state["mode"].startswith("Longitude") else 1, key="mode")
    # enforce mode in session_state
    st.session_state["mode"] = st.session_state["mode"]

    st.write("**Longitude (D° M' S\")** (cap ±180°)")
    st.selectbox("Direction", options=["E (+)", "W (-)"], key="lon_dir")
    st.number_input("Degrees", min_value=0, max_value=180, value=int(st.session_state["lon_deg"]), key="lon_deg")
    st.number_input("Minutes", min_value=0, max_value=59, value=int(st.session_state["lon_min"]), key="lon_min")
    st.number_input("Seconds", min_value=0.0, max_value=59.999999, format="%.6f", value=float(st.session_state["lon_sec"]), key="lon_sec")
    if st.button("Apply manual longitude"):
        on_manual_longitude_change()

    st.markdown("---")
    st.write("**Time zone (H : M : S)** (cap ±12 hours)")
    st.selectbox("TZ Sign", options=["+", "-"], key="tz_sign")
    st.number_input("Hours (0–12)", min_value=0, max_value=12, value=int(st.session_state["tz_h"]), key="tz_h")
    st.number_input("Minutes", min_value=0, max_value=59, value=int(st.session_state["tz_m"]), key="tz_m")
    st.number_input("Seconds", min_value=0.0, max_value=59.999999, format="%.6f", value=float(st.session_state["tz_s"]), key="tz_s")
    if st.button("Apply manual timezone"):
        on_manual_timezone_change()

    st.markdown("---")
    st.write("Auto-sync: manual ↔ slider ↔ map — always in sync.")

    st.markdown("### Batch (CSV / Excel)")
    st.write("Upload rows with either `lon_dir, lon_deg, lon_min, lon_sec` OR `tz_sign, tz_h, tz_m, tz_s`.")
    uploaded = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            df = None

        if df is not None:
            st.write("Preview:")
            st.dataframe(df.head(5))
            if st.button("Convert uploaded"):
                rows = []
                for _, r in df.iterrows():
                    try:
                        # longitude -> tz
                        if {"lon_dir","lon_deg","lon_min","lon_sec"}.issubset(r.index):
                            lon = dms_to_decimal(int(r.lon_deg), int(r.lon_min), float(r.lon_sec), r.lon_dir)
                            dh = decimal_longitude_to_decimal_hours(lon)
                            sgn, hh, mm, ss = decimal_hours_to_hms(dh)
                            rows.append({
                                "input_type":"lon->tz",
                                "lon_decimal": lon,
                                "tz_sign": "+" if sgn == "+" else "-",
                                "tz_h": hh, "tz_m": mm, "tz_s": round(ss,6)
                            })
                        elif {"tz_sign","tz_h","tz_m","tz_s"}.issubset(r.index):
                            dh = hms_to_decimal_hours(r.tz_sign, int(r.tz_h), int(r.tz_m), float(r.tz_s))
                            lon = longitude_from_decimal_hours(dh)
                            sgn, d, m, s = decimal_to_dms(lon)
                            rows.append({
                                "input_type":"tz->lon",
                                "lon_decimal": lon,
                                "lon_dir": "E" if sgn >= 0 else "W",
                                "lon_deg": d, "lon_min": m, "lon_sec": round(s,6)
                            })
                        else:
                            rows.append({"error":"unrecognized format"})
                    except Exception as e:
                        rows.append({"error": str(e)})
                out = pd.DataFrame(rows)
                st.session_state["last_batch_out"] = out
                st.success("Converted uploaded file.")
                st.dataframe(out.head(10))
                # downloads
                st.download_button("Download converted CSV", out.to_csv(index=False), "converted.csv")
                buf = io.BytesIO()
                out.to_excel(buf, index=False)
                buf.seek(0)
                st.download_button("Download converted XLSX", buf, "converted.xlsx")

with right_col:
    st.subheader("Interactive Map (click or drag marker)")

    # Ensure slider key exists and use on_change callback to sync
    # We'll use on_change via st.session_state trick: create slider widget bound to 'slider_lon' with an on_change name via st.experimental_set_query_params is not necessary.
    # Instead, we'll check differences and call on_slider_change when widget changes.
    # Determine initial lon for map center: prefer computed_lon, else clicked_lon, else slider_lon
    start_lon = st.session_state["computed_lon"] if st.session_state["computed_lon"] is not None else st.session_state["slider_lon"]
    start_lat = st.session_state["clicked_lat"]

    # Map: build folium map centered at (start_lat, start_lon)
    m = folium.Map(location=[start_lat, start_lon], zoom_start=3, control_scale=True)
    plugins.MiniMap().add_to(m)

    # Draw green vertical line at computed longitude
    folium.PolyLine([[85, st.session_state["slider_lon"]], [-85, st.session_state["slider_lon"]]],
                    color="green", weight=3, opacity=0.9, tooltip=f"Longitude {st.session_state['slider_lon']:.4f}°").add_to(m)

    # Add draggable marker on the green line (lat=0)
    icon_html = '<div style="font-size:22px; cursor:pointer; transform:translate(-50%,-50%);">📍</div>'
    icon = folium.DivIcon(html=icon_html)
    folium.Marker(location=[0, st.session_state["slider_lon"]], draggable=True, icon=icon, tooltip="Drag to change longitude").add_to(m)

    # Render the map — st_folium returns a dictionary of interactions
    map_result = st_folium(m, width=900, height=600, returned_objects=["last_clicked", "last_object"])

    # ---------- handle slider (placed below map for more space) ----------
    st.markdown("### Adjust longitude with slider (±180°)")
    # Use the slider widget; on change detect difference vs last session value
    slider_val = st.slider("Longitude slider", -180.0, 180.0, float(st.session_state["slider_lon"]), step=0.1, key="slider_lon")
    # If slider changed, the session state slider_lon is already updated by widget; call handler
    # But guard against repeated triggers — only call handler if last_action is not "slider" or value changed
    if st.session_state.get("last_action") != "slider" and abs(slider_val - st.session_state["computed_lon"]) > 1e-9:
        # sync fields from slider
        on_slider_change()
        # avoid infinite rerun loops: do not call experimental_rerun; the widget update is sufficient

    # ---------- handle map interactions ----------
    if map_result:
        # Clicks
        try:
            if map_result.get("last_clicked"):
                clicked = map_result["last_clicked"]
                if isinstance(clicked, dict) and clicked.get("lng") is not None:
                    lng = float(clicked["lng"])
                    lat = float(clicked.get("lat", 0.0))
                    # cap
                    lng = max(-180.0, min(180.0, lng))
                    st.session_state["clicked_lon"] = lng
                    st.session_state["clicked_lat"] = lat
                    st.session_state["slider_lon"] = lng
                    st.session_state["computed_lon"] = lng
                    st.session_state["last_action"] = "map"
                    # sync manual fields
                    sgn, d, m, s = decimal_to_dms(lng)
                    st.session_state["lon_dir"] = "E (+)" if sgn >= 0 else "W (-)"
                    st.session_state["lon_deg"] = d
                    st.session_state["lon_min"] = m
                    st.session_state["lon_sec"] = round(s, 6)
                    # tz fields
                    dec_hours = decimal_longitude_to_decimal_hours(lng)
                    sgn2, hh, mm, ss = decimal_hours_to_hms(dec_hours)
                    st.session_state["tz_sign"] = sgn2
                    st.session_state["tz_h"] = hh if hh <= 12 else 12
                    st.session_state["tz_m"] = mm
                    st.session_state["tz_s"] = round(ss, 6)
        except Exception:
            pass

        # Marker drag (returned as last_object sometimes)
        try:
            last_obj = map_result.get("last_object")
            if isinstance(last_obj, dict):
                # handle possible key names
                lng = None
                for key_candidate in ("lng","lon","longitude"):
                    if key_candidate in last_obj and last_obj[key_candidate] is not None:
                        lng = float(last_obj[key_candidate])
                        break
                if lng is not None:
                    lng = max(-180.0, min(180.0, lng))
                    st.session_state["slider_lon"] = lng
                    st.session_state["computed_lon"] = lng
                    st.session_state["last_action"] = "map"
                    # sync manual
                    sgn, d, m, s = decimal_to_dms(lng)
                    st.session_state["lon_dir"] = "E (+)" if sgn >= 0 else "W (-)"
                    st.session_state["lon_deg"] = d
                    st.session_state["lon_min"] = m
                    st.session_state["lon_sec"] = round(s, 6)
                    dec_hours = decimal_longitude_to_decimal_hours(lng)
                    sgn2, hh, mm, ss = decimal_hours_to_hms(dec_hours)
                    st.session_state["tz_sign"] = sgn2
                    st.session_state["tz_h"] = hh if hh <= 12 else 12
                    st.session_state["tz_m"] = mm
                    st.session_state["tz_s"] = round(ss, 6)
        except Exception:
            pass

# -------------------------
# Full-width Results & Explanation (below map & inputs)
# -------------------------
st.markdown("---")
st.header("Results")

# Selected longitude is the computed primitive in session_state
sel_lon = st.session_state["computed_lon"]

# Make sure it's capped
sel_lon = max(-180.0, min(180.0, float(sel_lon)))

if st.session_state["mode"] == "Longitude → Time Zone":
    # Show degree first then time
    st.subheader("Degrees → Time Zone Result")
    st.write(f"**Selected Longitude:** {sel_lon:.6f}°")
    dec_hours = decimal_longitude_to_decimal_hours(sel_lon)
    sgn, hh, mm, ss = decimal_hours_to_hms(dec_hours)
    st.write(f"**Time zone offset:** {sgn}{hh}h {mm}m {ss:.6f}s")

    st.markdown("### Explanation (Degrees → Time)")
    # Detailed step-by-step
    sgn_d, d_deg, d_min, d_sec = decimal_to_dms(sel_lon)
    st.write(f"1. D:M:S representation (from decimal degrees): direction={'E' if sgn_d>=0 else 'W'}, {d_deg}° {d_min}' {d_sec:.6f}\"")
    st.write(f"2. Decimal degrees → Decimal hours: {sel_lon:.6f} / 15 = {dec_hours:.6f} hours")
    st.write(f"3. Decimal hours → H:M:S: {sgn}{hh} h, {mm} m, {ss:.6f} s")

else:
    # Time → Degrees: show time first then result
    st.subheader("Time → Degrees Result")
    # compute based on current tz fields (they'll be synced with slider/map)
    dec_hours = hms_to_decimal_hours(st.session_state["tz_sign"], st.session_state["tz_h"], st.session_state["tz_m"], st.session_state["tz_s"])
    # cap hours
    dec_hours = max(-12.0, min(12.0, dec_hours))
    lon_from_time = longitude_from_decimal_hours(dec_hours)
    lon_from_time = max(-180.0, min(180.0, lon_from_time))

    st.write(f"**Input Time (TZ):** {st.session_state['tz_sign']}{st.session_state['tz_h']}h {st.session_state['tz_m']}m {st.session_state['tz_s']:.6f}s")
    st.write(f"**Computed Longitude:** {lon_from_time:.6f}°")

    st.markdown("### Explanation (Time → Degrees)")
    st.write(f"1. H:M:S → Decimal hours: {st.session_state['tz_h']} + {st.session_state['tz_m']}/60 + {st.session_state['tz_s']}/3600 = {dec_hours:.6f} h")
    st.write(f"2. Decimal hours → Degrees: {dec_hours:.6f} × 15 = {lon_from_time:.6f}°")
    sgn, d_deg, d_min, d_sec = decimal_to_dms(lon_from_time)
    st.write(f"3. Degrees → D:M:S: {'E' if sgn>=0 else 'W'} {d_deg}° {d_min}' {d_sec:.6f}\"")

# -------------------------
# Footer: optional debug info
# -------------------------
st.markdown("---")
st.write("**Selected (computed) longitude (primitive):**", f"{st.session_state['computed_lon']:.6f}°")
st.write("**Last action:**", st.session_state.get("last_action"))
if st.session_state.get("clicked_lon") is not None:
    st.write("**Last click:** lat=", st.session_state.get("clicked_lat"), " lon=", st.session_state.get("clicked_lon"))
