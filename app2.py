import io
import math
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import plugins

from utils import (
    decimal_to_dms,
    dms_to_decimal,
    tz_hms_to_decimal_hours,
    decimal_hours_to_hms,
    longitude_from_decimal_hours,
    decimal_longitude_to_decimal_hours
)

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(page_title="Time Zone ↔ Longitude", layout="wide")

# -----------------------------------------------------
# SESSION STATE
# -----------------------------------------------------
DEFAULTS = {
    "clicked_lon": None,
    "clicked_lat": 0.0,
    "computed_lon": None,
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
    "mode": "Longitude → Time Zone"
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# -----------------------------------------------------
# TITLE
# -----------------------------------------------------
st.title("🌍 Time Zone ↔ Longitude Converter")
st.write("Use **manual inputs**, **upload CSV/Excel**, or **interact with the map**. All methods stay synchronized.")


# =====================================================
# LAYOUT
# =====================================================
left, right = st.columns([1, 1.2])

# -----------------------------------------------------
# LEFT SIDE — INPUT PANELS
# -----------------------------------------------------
with left:

    st.subheader("Mode Selection")
    st.session_state["mode"] = st.radio(
        "Conversion Direction",
        ["Longitude → Time Zone", "Time Zone → Longitude"],
        index=0
    )

    # Auto toggle
    st.checkbox("Auto-update values from map (drag, click, slider)", key="auto_from_map")

    mode = st.session_state["mode"]

    # =========================
    # LONGITUDE → TIME ZONE
    # =========================
    if mode == "Longitude → Time Zone":
        st.markdown("### Manual Longitude Input")

        st.selectbox("Direction", ["E (+)", "W (-)"], key="lon_sign")
        st.number_input("Degrees", 0, 180, key="lon_deg")
        st.number_input("Minutes", 0, 59, key="lon_min")
        st.number_input("Seconds", 0.0, 59.999999, key="lon_sec", format="%.6f")

        if st.button("Compute Time Zone"):
            try:
                lon_decimal = dms_to_decimal(
                    st.session_state["lon_sign"],
                    st.session_state["lon_deg"],
                    st.session_state["lon_min"],
                    st.session_state["lon_sec"]
                )
                st.session_state["computed_lon"] = lon_decimal

                dec_hours = decimal_longitude_to_decimal_hours(lon_decimal)
                sgn, h, m, s = decimal_hours_to_hms(dec_hours)

                st.session_state.update({
                    "tz_sign": "+" if sgn >= 0 else "-",
                    "tz_h": h,
                    "tz_m": m,
                    "tz_s": s
                })

                st.success(f"Computed Time Zone Offset: {st.session_state['tz_sign']}{h}:{m}:{s:.6f}")

            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("### Explanation")
        try:
            lon_decimal = dms_to_decimal(
                st.session_state["lon_sign"],
                st.session_state["lon_deg"],
                st.session_state["lon_min"],
                st.session_state["lon_sec"]
            )
            dec_hours = lon_decimal / 15
            sgn, h, m, s = decimal_hours_to_hms(dec_hours)

            st.write(f"**1. Convert DMS → Decimal Degrees**")
            st.write(f"   `{st.session_state['lon_deg']} + {st.session_state['lon_min']}/60 + {st.session_state['lon_sec']}/3600 = {lon_decimal:.6f}°`")

            st.write(f"**2. Convert Degrees → Decimal Hours**")
            st.write(f"   `{lon_decimal:.6f} / 15 = {dec_hours:.6f}`")

            st.write(f"**3. Convert Decimal Hours → H:M:S**")
            st.write(f"   `{h} hours, {m} minutes, {s:.6f} seconds`")

        except:
            pass

    # =========================
    # TIME ZONE → LONGITUDE
    # =========================
    else:
        st.markdown("### Manual Time Zone Input")

        st.selectbox("Sign", ["+", "-"], key="tz_sign")
        st.number_input("Hours", 0, 18, key="tz_h")
        st.number_input("Minutes", 0, 59, key="tz_m")
        st.number_input("Seconds", 0.0, 59.999999, key="tz_s", format="%.6f")

        if st.button("Compute Longitude"):
            try:
                dec_hours = tz_hms_to_decimal_hours(
                    st.session_state["tz_sign"],
                    st.session_state["tz_h"],
                    st.session_state["tz_m"],
                    st.session_state["tz_s"]
                )
                lon = longitude_from_decimal_hours(dec_hours)
                st.session_state["computed_lon"] = lon

                sgn, d, m, s = decimal_to_dms(lon)
                st.session_state.update({
                    "lon_sign": "E (+)" if sgn >= 0 else "W (-)",
                    "lon_deg": d,
                    "lon_min": m,
                    "lon_sec": s
                })

                st.success(f"Computed Longitude: {lon:.6f}°")

            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("### Explanation")
        try:
            dec_hours = tz_hms_to_decimal_hours(
                st.session_state["tz_sign"],
                st.session_state["tz_h"],
                st.session_state["tz_m"],
                st.session_state["tz_s"]
            )
            lon = longitude_from_decimal_hours(dec_hours)
            sgn, d, mm, ss = decimal_to_dms(lon)

            st.write(f"**1. Convert H:M:S → Decimal Hours**")
            st.write(f"   `{st.session_state['tz_h']} + {st.session_state['tz_m']}/60 + {st.session_state['tz_s']}/3600 = {dec_hours:.6f}`")

            st.write(f"**2. Convert Hours → Longitude Degrees**")
            st.write(f"   `{dec_hours:.6f} × 15 = {lon:.6f}°`")

            st.write(f"**3. Convert Decimal Degrees → D:M:S**")
            st.write(f"   `{d}° {mm}' {ss:.6f}\"`")

        except:
            pass


    # --------------------------------------------------
    # BATCH CSV/EXCEL
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("Batch Conversion (CSV / Excel)")

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)

            st.write("Preview:")
            st.dataframe(df.head())

            results = []

            for _, r in df.iterrows():
                row_result = {}

                try:
                    # LONGITUDE ROW
                    if {"lon_dir", "lon_deg", "lon_min", "lon_sec"}.issubset(r.index):
                        lon = dms_to_decimal(r.lon_dir, r.lon_deg, r.lon_min, r.lon_sec)
                        dh = lon / 15
                        sgn, h, m, s = decimal_hours_to_hms(dh)

                        row_result = {
                            "input_type": "longitude",
                            "longitude_decimal": lon,
                            "tz_sign": "+" if sgn >= 0 else "-",
                            "tz_h": h,
                            "tz_m": m,
                            "tz_s": s
                        }

                    # TIME ZONE ROW
                    elif {"tz_sign", "tz_h", "tz_m", "tz_s"}.issubset(r.index):
                        dh = tz_hms_to_decimal_hours(r.tz_sign, r.tz_h, r.tz_m, r.tz_s)
                        lon = dh * 15
                        sgn, d, m, s = decimal_to_dms(lon)

                        row_result = {
                            "input_type": "timezone",
                            "longitude_decimal": lon,
                            "lon_dir": "E" if sgn >= 0 else "W",
                            "lon_deg": d,
                            "lon_min": m,
                            "lon_sec": s
                        }

                    else:
                        row_result = {"error": "Unrecognized row format"}

                except Exception as e:
                    row_result = {"error": str(e)}

                results.append(row_result)

            out = pd.DataFrame(results)
            st.write("Results:")
            st.dataframe(out)

            st.download_button("Download CSV", out.to_csv(index=False), "converted.csv")

            excel_bytes = io.BytesIO()
            out.to_excel(excel_bytes, index=False)
            excel_bytes.seek(0)

            st.download_button("Download Excel", excel_bytes, "converted.xlsx")

        except Exception as e:
            st.error(f"Error reading file: {e}")


# -----------------------------------------------------
# RIGHT SIDE — INTERACTIVE MAP
# -----------------------------------------------------
with right:
    st.header("Interactive Map")

    # Determine highlight longitude
    if st.session_state["computed_lon"] is not None:
        highlight_lon = st.session_state["computed_lon"]
    elif st.session_state["clicked_lon"] is not None:
        highlight_lon = st.session_state["clicked_lon"]
    else:
        highlight_lon = st.session_state["slider_lon"]

    # --------------------------
    # SLIDER
    # --------------------------
    st.session_state["slider_lon"] = st.slider(
        "Move the green longitude line",
        -180.0, 180.0,
        float(highlight_lon), 0.1
    )

    # --------------------------
    # SYNC SLIDER → INPUT FIELDS
    # --------------------------
    if st.session_state["auto_from_map"]:
        lon = st.session_state["slider_lon"]
        st.session_state["computed_lon"] = lon

        if st.session_state["mode"] == "Longitude → Time Zone":
            sgn, d, m, s = decimal_to_dms(lon)
            st.session_state["lon_sign"] = "E (+)" if sgn >= 0 else "W (-)"
            st.session_state["lon_deg"] = d
            st.session_state["lon_min"] = m
            st.session_state["lon_sec"] = s
        else:
            dh = lon / 15
            sgn, h, m, s = decimal_hours_to_hms(dh)
            st.session_state["tz_sign"] = "+" if sgn >= 0 else "-"
            st.session_state["tz_h"] = h
            st.session_state["tz_m"] = m
            st.session_state["tz_s"] = s

    # --------------------------
    # FOLIUM MAP
    # --------------------------
    center = [0, st.session_state["slider_lon"]]
    m = folium.Map(location=center, zoom_start=3, control_scale=True)
    plugins.MiniMap().add_to(m)

    # Green line
    folium.PolyLine(
        [[80, st.session_state["slider_lon"]], [-80, st.session_state["slider_lon']]],
        color="green", weight=3, opacity=0.8
    ).add_to(m)

    # Draggable marker for precise longitude
    icon = folium.DivIcon(html="""
    <div style="font-size:22px; cursor:pointer; transform:translate(-50%, -50%);">📍</div>
    """)
    marker = folium.Marker(
        [0, st.session_state["slider_lon"]],
        draggable=True,
        icon=icon
    )
    marker.add_to(m)

    map_data = st_folium(m, width=750, height=500)

    # --------------------------
    # MAP CLICK HANDLING
    # --------------------------
    if map_data and map_data.get("last_clicked"):
        lng = map_data["last_clicked"]["lng"]
        lat = map_data["last_clicked"]["lat"]

        st.session_state["clicked_lon"] = lng
        st.session_state["clicked_lat"] = lat

        if st.session_state["auto_from_map"]:
            st.session_state["slider_lon"] = lng
            st.experimental_rerun()

    # --------------------------
    # MARKER DRAG HANDLING
    # --------------------------
    if map_data and map_data.get("last_object"):
        obj = map_data["last_object"]
        if isinstance(obj, dict) and obj.get("lng") is not None:
            lng = obj["lng"]
            st.session_state["slider_lon"] = lng

            if st.session_state["auto_from_map"]:
                st.experimental_rerun()

    # --------------------------
    # SHOW SELECTED LON VALUE
    # --------------------------
    st.markdown(f"### Selected / Computed Longitude: **{st.session_state['slider_lon']:.6f}°**")

    if st.session_state["clicked_lon"] is not None:
        st.write(f"Last map click → lat: {st.session_state['clicked_lat']:.6f}, lon: {st.session_state['clicked_lon']:.6f}")
