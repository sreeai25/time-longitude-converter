# app.py
import io
import math
from typing import Tuple, Optional

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import plugins

# -----------------------
# Utilities (self-contained)
# -----------------------

def decimal_to_dms(decimal_deg: float) -> Tuple[int, int, int, float]:
    """
    Returns (sign, deg, minutes, seconds)
    sign: 1 for positive (E), -1 for negative (W)
    deg: integer degrees (abs)
    minutes: integer minutes
    seconds: float seconds
    """
    sign = 1 if decimal_deg >= 0 else -1
    dd = abs(decimal_deg)
    deg = int(math.floor(dd))
    rem = (dd - deg) * 60
    minutes = int(math.floor(rem))
    seconds = (rem - minutes) * 60
    return sign, deg, minutes, seconds

def dms_to_decimal(sign_str: str, deg: int, minutes: int, seconds: float) -> float:
    """
    sign_str: "E" or "W" or "+" or "-"
    """
    sign = 1
    if isinstance(sign_str, str) and sign_str.strip().upper().startswith("W") or sign_str == "-":
        sign = -1
    dec = deg + minutes / 60.0 + seconds / 3600.0
    return sign * dec

def tz_hms_to_decimal_hours(sign_str: str, h: int, m: int, s: float) -> float:
    """Convert sign + H:M:S -> decimal hours"""
    dec = h + m / 60.0 + s / 3600.0
    if (isinstance(sign_str, str) and sign_str.strip() == "-") or sign_str == -1:
        dec = -dec
    return dec

def decimal_hours_to_hms(dec_hours: float) -> Tuple[int, int, int, float]:
    """Return (sign, hours, minutes, seconds)"""
    sign = 1 if dec_hours >= 0 else -1
    dh = abs(dec_hours)
    hours = int(math.floor(dh))
    rem = (dh - hours) * 60
    minutes = int(math.floor(rem))
    seconds = (rem - minutes) * 60
    return sign, hours, minutes, seconds

def longitude_from_decimal_hours(dec_hours: float) -> float:
    """Longitude = hours * 15"""
    return dec_hours * 15.0

def decimal_longitude_to_decimal_hours(lon: float) -> float:
    """Decimal hours = lon / 15"""
    return lon / 15.0

# -----------------------
# Streamlit app
# -----------------------
st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# Initialize session state
defaults = {
    "clicked_lon": None,
    "clicked_lat": 0.0,
    "computed_lon": None,
    "mode": "Longitude → Time Zone",
    "lon_sign": "E (+)",
    "lon_deg": 0,
    "lon_min": 0,
    "lon_sec": 0.0,
    "tz_sign": "+",
    "tz_h": 0,
    "tz_m": 0,
    "tz_s": 0.0,
    "auto_from_map": True,
    "slider_lon": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Time Zone ↔ Longitude")
st.write("Convert between longitude and time zone offsets. Use manual inputs, click on the map, drag the marker, or use the slider. Upload/download CSV/Excel batches.")

# Layout: left controls, right map
left, right = st.columns([1, 1.2])

with left:
    # Mode selector
    st.subheader("Mode & Inputs")
    mode = st.radio("Choose conversion direction", ["Longitude → Time Zone", "Time Zone → Longitude"], index=0 if st.session_state["mode"].startswith("Longitude") else 1)
    st.session_state["mode"] = mode

    st.checkbox("Auto-update time from map interactions", value=st.session_state["auto_from_map"], key="auto_from_map")

    # If user wants to use manual input fields:
    if mode == "Longitude → Time Zone":
        st.markdown("#### Manual longitude input (deg / min / sec)")
        lon_sign = st.selectbox("Longitude direction", ["E (+)", "W (-)"], index=0 if st.session_state["lon_sign"].startswith("E") else 1, key="lon_sign")
        lon_deg = st.number_input("Degrees", min_value=0, max_value=180, value=int(st.session_state["lon_deg"]), key="lon_deg")
        lon_min = st.number_input("Minutes", min_value=0, max_value=59, value=int(st.session_state["lon_min"]), key="lon_min")
        lon_sec = st.number_input("Seconds", min_value=0.0, max_value=59.999999, value=float(st.session_state["lon_sec"]), format="%.6f", key="lon_sec")

        if st.button("Compute Time Zone from Manual Longitude"):
            try:
                lon_decimal = dms_to_decimal(lon_sign, int(lon_deg), int(lon_min), float(lon_sec))
                st.session_state["computed_lon"] = lon_decimal
                # compute tz
                dec_hours = decimal_longitude_to_decimal_hours(lon_decimal)
                sgn, hours, minutes, seconds = decimal_hours_to_hms(dec_hours)
                # update tz inputs
                st.session_state["tz_sign"] = "+" if sgn >= 0 else "-"
                st.session_state["tz_h"] = hours
                st.session_state["tz_m"] = minutes
                st.session_state["tz_s"] = round(seconds, 6)
                st.success(f"Computed timezone: {st.session_state['tz_sign']}{hours}:{minutes}:{round(seconds,3)} (from longitude {lon_decimal:.6f}°)")
            except Exception as e:
                st.error(f"Error computing timezone: {e}")

        # Explanation area (always show dynamic explanation)
        st.markdown("### Explanation (Longitude → Time Zone)")
        try:
            lon_decimal_preview = dms_to_decimal(lon_sign, int(lon_deg), int(lon_min), float(lon_sec))
            dec_hours_preview = decimal_longitude_to_decimal_hours(lon_decimal_preview)
            sgnh, h, m, s = decimal_hours_to_hms(dec_hours_preview)
            st.write(f"**DMS → Decimal degrees:** {lon_deg} + {lon_min}/60 + {lon_sec}/3600 = {lon_decimal_preview:.6f}°")
            st.write(f"**Decimal degrees → Decimal hours:** {lon_decimal_preview:.6f} / 15 = {dec_hours_preview:.6f} hours")
            st.write(f"**Decimal hours → H:M:S:** {h} h {m} m {s:.6f} s (sign {'+' if sgnh>=0 else '-'})")
        except Exception as e:
            st.write("Enter values above to see step-by-step explanation.")

    else:
        st.markdown("#### Manual timezone input (H:M:S)")
        tz_sign = st.selectbox("Sign", ["+","-"], index=0 if st.session_state["tz_sign"] == "+" else 1, key="tz_sign")
        tz_h = st.number_input("Hours", min_value=0, max_value=18, value=int(st.session_state["tz_h"]), key="tz_h")
        tz_m = st.number_input("Minutes", min_value=0, max_value=59, value=int(st.session_state["tz_m"]), key="tz_m")
        tz_s = st.number_input("Seconds", min_value=0.0, max_value=59.999999, value=float(st.session_state["tz_s"]), format="%.6f", key="tz_s")

        if st.button("Compute Longitude from Manual Time Zone"):
            try:
                dec_hours = tz_hms_to_decimal_hours(tz_sign, int(tz_h), int(tz_m), float(tz_s))
                lon = longitude_from_decimal_hours(dec_hours)
                st.session_state["computed_lon"] = lon
                # update DMS fields for display
                sgn, d, m_val, s_val = decimal_to_dms(lon)
                st.session_state["lon_sign"] = "E (+)" if sgn >= 0 else "W (-)"
                st.session_state["lon_deg"] = d
                st.session_state["lon_min"] = m_val
                st.session_state["lon_sec"] = round(s_val, 6)
                st.success(f"Computed longitude: {lon:.6f}°")
            except Exception as e:
                st.error(f"Error computing longitude: {e}")

        # Explanation
        st.markdown("### Explanation (Time Zone → Longitude)")
        try:
            dec_hours_preview = tz_hms_to_decimal_hours(tz_sign, int(tz_h), int(tz_m), float(tz_s))
            lon_preview = longitude_from_decimal_hours(dec_hours_preview)
            sgn, d, m_val, s_val = decimal_to_dms(lon_preview)
            st.write(f"**H:M:S → Decimal hours:** {tz_h} + {tz_m}/60 + {tz_s}/3600 = {dec_hours_preview:.6f} h (sign {tz_sign})")
            st.write(f"**Decimal hours → Decimal degrees:** {dec_hours_preview:.6f} * 15 = {lon_preview:.6f}°")
            st.write(f"**Decimal degrees → D:M:S:** {d}° {m_val}' {s_val:.6f}\" (direction {'E' if sgn>=0 else 'W'})")
        except Exception as e:
            st.write("Enter values above to see step-by-step explanation.")

    st.markdown("---")

    # ---------------- Batch Upload ----------------
    st.subheader("Batch Conversion (CSV / Excel)")
    st.write(
        "Upload a CSV or Excel with columns for either: "
        "`lon_deg, lon_min, lon_sec, lon_dir` (E/W) **or** `tz_sign, tz_h, tz_m, tz_s`."
    )
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    sample_button_col1, sample_button_col2 = st.columns(2)
    with sample_button_col1:
        if st.button("Download sample (Longitude rows)"):
            sample_df = pd.DataFrame({
                "lon_dir": ["E", "W"],
                "lon_deg": [30, 45],
                "lon_min": [15, 0],
                "lon_sec": [30.0, 0.0],
            })
            csv_bytes = sample_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv_bytes, file_name="sample_longitude.csv", mime="text/csv")
    with sample_button_col2:
        if st.button("Download sample (Timezone rows)"):
            sample_df = pd.DataFrame({
                "tz_sign": ["+","-"],
                "tz_h": [2, 5],
                "tz_m": [30, 0],
                "tz_s": [0.0, 30.0],
            })
            csv_bytes = sample_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv_bytes, file_name="sample_timezone.csv", mime="text/csv")

    if uploaded is not None:
        try:
            if uploaded.type in ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"):
                df = pd.read_excel(uploaded)
            else:
                df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")
            df = None

        if df is not None:
            st.write("Preview of uploaded data (first 10 rows):")
            st.dataframe(df.head(10))

            # Determine type of rows
            out_rows = []
            # We'll allow mixed rows; try to convert each row intelligently.
            for _, row in df.iterrows():
                row_out = {}
                try:
                    if all(col in row.index for col in ["lon_deg","lon_min","lon_sec","lon_dir"]):
                        # longitude -> timezone
                        lon_dir = str(row.get("lon_dir")).strip() if not pd.isna(row.get("lon_dir")) else "E"
                        deg = int(row.get("lon_deg", 0))
                        minu = int(row.get("lon_min", 0))
                        sec = float(row.get("lon_sec", 0.0))
                        lon_decimal = dms_to_decimal(lon_dir, deg, minu, sec)
                        dec_hours = decimal_longitude_to_decimal_hours(lon_decimal)
                        sgnh, h, m, s = decimal_hours_to_hms(dec_hours)
                        row_out.update({
                            "input_type": "lon->tz",
                            "lon_decimal": lon_decimal,
                            "tz_sign": "+" if sgnh >= 0 else "-",
                            "tz_h": h, "tz_m": m, "tz_s": round(s,6)
                        })
                    elif all(col in row.index for col in ["tz_sign","tz_h","tz_m","tz_s"]):
                        # timezone -> longitude
                        tz_sign = str(row.get("tz_sign")).strip()
                        h = int(row.get("tz_h", 0))
                        m = int(row.get("tz_m", 0))
                        s = float(row.get("tz_s", 0.0))
                        dec_hours = tz_hms_to_decimal_hours(tz_sign, h, m, s)
                        lon = longitude_from_decimal_hours(dec_hours)
                        sgn, d, mm, ss = decimal_to_dms(lon)
                        row_out.update({
                            "input_type": "tz->lon",
                            "lon_decimal": lon,
                            "lon_dir": "E" if sgn >= 0 else "W",
                            "lon_deg": d, "lon_min": mm, "lon_sec": round(ss,6)
                        })
                    else:
                        row_out.update({"error":"unrecognized row format"})
                except Exception as e:
                    row_out.update({"error": str(e)})
                out_rows.append(row_out)

            result_df = pd.DataFrame(out_rows)
            st.write("Conversion results (first 20 rows):")
            st.dataframe(result_df.head(20))

            # Offer downloads (CSV and Excel)
            csv_bytes = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download results as CSV", data=csv_bytes, file_name="converted_results.csv", mime="text/csv")

            try:
                towrite = io.BytesIO()
                result_df.to_excel(towrite, index=False, sheet_name="results")
                towrite.seek(0)
                st.download_button("Download results as Excel", data=towrite, file_name="converted_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception:
                st.info("Excel download not available (openpyxl missing?)")

with right:
    st.header("Interactive Map")
    # Choose initial highlight longitude
    highlight_lon = st.session_state["computed_lon"] if st.session_state["computed_lon"] is not None else (st.session_state["clicked_lon"] if st.session_state["clicked_lon"] is not None else st.session_state["slider_lon"])
    highlight_lat = st.session_state["clicked_lat"] if st.session_state["clicked_lat"] is not None else 0.0

    # Add a small UI control in Streamlit keeping a slider (this is synchronized to the map green line)
    st.markdown("**Move green longitude line** — use the slider, drag the marker, or click on the map.")
    slider_col, map_col = st.columns([1, 3])
    with slider_col:
        slider_lon = st.slider("Move Green Longitude Line", -180.0, 180.0, value=float(highlight_lon), step=0.1, key="slider_lon")
        # Show current computed or clicked lon
        st.markdown(f"**Selected / Computed longitude:** {st.session_state.get('computed_lon') if st.session_state.get('computed_lon') is not None else (st.session_state.get('clicked_lon') if st.session_state.get('clicked_lon') is not None else slider_lon):.6f}°")

    # synchronize slider to session state
    st.session_state["slider_lon"] = slider_lon
    # If user is in Longitude->Time and auto_from_map or they used slider, update the manual inputs
    if st.session_state["mode"] == "Longitude → Time Zone":
        # update DMS fields based on slider_lon if auto allowed
        if st.session_state["auto_from_map"]:
            try:
                sgn, d, m_val, s_val = decimal_to_dms(slider_lon)
                st.session_state["lon_sign"] = "E (+)" if sgn >= 0 else "W (-)"
                st.session_state["lon_deg"] = d
                st.session_state["lon_min"] = m_val
                st.session_state["lon_sec"] = round(s_val, 6)
                # update computed lon
                st.session_state["computed_lon"] = float(slider_lon)
            except Exception:
                pass
    else:
        # Time zone -> longitude: update tz fields if auto
        if st.session_state["auto_from_map"]:
            try:
                dec_hours = decimal_longitude_to_decimal_hours(slider_lon)
                sgn, hh, mm, ss = decimal_hours_to_hms(dec_hours)
                st.session_state["tz_sign"] = "+" if sgn >= 0 else "-"
                st.session_state["tz_h"] = hh
                st.session_state["tz_m"] = mm
                st.session_state["tz_s"] = round(ss, 6)
                st.session_state["computed_lon"] = float(slider_lon)
            except Exception:
                pass

    # Build folium map: show vertical line at slider_lon and a draggable marker at lat=0
    center = [highlight_lat, float(slider_lon)]
    m = folium.Map(location=center, zoom_start=3, control_scale=True)

    # Add world tiles and minimap
    plugins.MiniMap().add_to(m)

    # Add green vertical line (simple polyline from lat 85 to -85 at slider_lon)
    folium.PolyLine([[85, slider_lon], [-85, slider_lon]],
                    color="green", weight=3, opacity=0.8, tooltip=f"Longitude {slider_lon:.4f}°").add_to(m)

    # Add draggable marker at lat=0 on the green line: moving marker updates the latitude/longitude in map_data (streamlit-folium)
    # Marker popup shows pointer text. We'll try to style cursor to pointer using custom icon HTML.
    icon_html = """
    <div style="
      font-size:20px;
      transform: translate(-50%, -50%);
      cursor: pointer;
      ">
      📍
    </div>
    """
    icon = folium.DivIcon(html=icon_html)
    draggable_marker = folium.Marker(location=[0, slider_lon], draggable=True, icon=icon, tooltip="Drag me left/right to change longitude")
    draggable_marker.add_to(m)

    # Add click handler hint
    folium.map.LayerControl(position='topright').add_to(m)

    # Render map and collect interaction data
    st_map = st_folium(m, width=700, height=500, returned_objects=["last_clicked", "last_object_clicked", "last_object", "all_drawings"])

    # Process map interactions if any
    # 1) Map clicks (last_clicked)
    if st_map and "last_clicked" in st_map and st_map["last_clicked"] is not None:
        last_click = st_map["last_clicked"]
        lng = last_click.get("lng")
        lat = last_click.get("lat")
        if lng is not None:
            # Update session state
            st.session_state["clicked_lon"] = float(lng)
            st.session_state["clicked_lat"] = float(lat)
            # If auto_from_map is enabled, use the clicked lon to update computed values
            if st.session_state["auto_from_map"]:
                st.session_state["slider_lon"] = float(lng)
                st.session_state["computed_lon"] = float(lng)
                # Sync the manual inputs depending on mode
                if st.session_state["mode"] == "Longitude → Time Zone":
                    sgn, d, m_val, s_val = decimal_to_dms(float(lng))
                    st.session_state["lon_sign"] = "E (+)" if sgn >= 0 else "W (-)"
                    st.session_state["lon_deg"] = d
                    st.session_state["lon_min"] = m_val
                    st.session_state["lon_sec"] = round(s_val, 6)
                else:
                    dec_hours = decimal_longitude_to_decimal_hours(float(lng))
                    sgnh, hh, mm, ss = decimal_hours_to_hms(dec_hours)
                    st.session_state["tz_sign"] = "+" if sgnh >= 0 else "-"
                    st.session_state["tz_h"] = hh
                    st.session_state["tz_m"] = mm
                    st.session_state["tz_s"] = round(ss, 6)
                # force re-run so UI updates instantly
                st.experimental_rerun()

    # 2) Marker drag / last_object -- streamlit-folium returns 'last_object' when marker is dragged in many versions.
    # We'll attempt to capture it.
    if st_map:
        last_obj = st_map.get("last_object")
        if last_obj and isinstance(last_obj, dict):
            # some versions return {"lat":..., "lng":...}
            lng = last_obj.get("lng") or last_obj.get("lon") or last_obj.get("longitude")
            lat = last_obj.get("lat") or last_obj.get("latitude")
            try:
                if lng is not None:
                    st.session_state["slider_lon"] = float(lng)
                    st.session_state["computed_lon"] = float(lng)
                    # sync manual
                    if st.session_state["mode"] == "Longitude → Time Zone":
                        sgn, d, m_val, s_val = decimal_to_dms(float(lng))
                        st.session_state["lon_sign"] = "E (+)" if sgn >= 0 else "W (-)"
                        st.session_state["lon_deg"] = d
                        st.session_state["lon_min"] = m_val
                        st.session_state["lon_sec"] = round(s_val, 6)
                    else:
                        dec_hours = decimal_longitude_to_decimal_hours(float(lng))
                        sgnh, hh, mm, ss = decimal_hours_to_hms(dec_hours)
                        st.session_state["tz_sign"] = "+" if sgnh >= 0 else "-"
                        st.session_state["tz_h"] = hh
                        st.session_state["tz_m"] = mm
                        st.session_state["tz_s"] = round(ss, 6)
                    st.experimental_rerun()
            except Exception:
                pass

    # Show final selected longitude under the map prominently
    final_lon = st.session_state.get("computed_lon") if st.session_state.get("computed_lon") is not None else (st.session_state.get("clicked_lon") if st.session_state.get("clicked_lon") is not None else st.session_state.get("slider_lon"))
    st.markdown(f"### Selected / Computed longitude: **{float(final_lon):.6f}°**")

    # Also show last raw click coordinates for debugging/confirmation for the user
    clicked_preview = st.session_state.get("clicked_lon")
    if clicked_preview is not None:
        st.markdown(f"**Last map click:** lat={st.session_state.get('clicked_lat'):.6f}, lon={st.session_state.get('clicked_lon'):.6f}")

# Footer notes
st.markdown("---")
st.markdown(
    """
    **Notes & behavior**
    - You can use manual inputs OR interact with the map. If *Auto-update from map interactions* is checked, map clicks/drags/slider will overwrite the manual fields and compute the counterpart conversion automatically.
    - Batch upload accepts CSV or Excel. Rows must contain either `lon_dir, lon_deg, lon_min, lon_sec` or `tz_sign, tz_h, tz_m, tz_s`.
    - The green vertical line represents the selected longitude. The slider and draggable marker both update it and keep the input form synchronized.
    - Explanations show each step of the conversion with intermediate arithmetic.
    """
)
