import streamlit as st
import pandas as pd
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

def longitude_to_tz_explanation(deg, minu, sec):
    dec_deg = dms_to_decimal(deg, minu, sec, 1)
    tz_hours = dec_deg / 15
    sgn, h, m, s = tz_hours_to_hms(tz_hours)
    return dec_deg, tz_hours, sgn, h, m, s

def tz_to_longitude_explanation(h, m, s, sign_char):
    dec_hours = hms_to_decimal_hours(h, m, s, 1 if sign_char=="+" else -1)
    lon = longitude_from_timezone_hours(dec_hours)
    sgn, d, m_val, s_val = decimal_to_dms(lon)
    return dec_hours, lon, sgn, d, m_val, s_val

# ---------------- APP LAYOUT ----------------
st.title("🕰️ 🌍 Time Zone ↔ Longitude Calculator")
st.markdown("Click map or use slider for longitude selection, convert single values or batch CSV/Excel.")

left, right = st.columns([1,1])

# ---------------- LEFT PANEL ----------------
with left:
    st.header("Single Conversion")
    mode = st.radio("Conversion Direction", ["Longitude → Time Zone", "Time Zone → Longitude"])

    # Auto-fill longitude input only if map clicked and mode is Longitude→Time
    if mode == "Longitude → Time Zone" and st.session_state.clicked_lon is not None:
        sgn, d, m_val, s_val = decimal_to_dms(st.session_state.clicked_lon)
        st.session_state.lon_dir = "E (positive)" if sgn>=0 else "W (negative)"
        st.session_state.lon_deg = d
        st.session_state.lon_min = m_val
        st.session_state.lon_sec = round(s_val,6)

    if mode == "Longitude → Time Zone":
        st.subheader("Enter Longitude (D:M:S)")
        lon_dir = st.selectbox(
            "Direction",
            ["E (positive)","W (negative)"],
            index=["E (positive)","W (negative)"].index(st.session_state.lon_dir),
            key="lon_dir"
        )
        deg = st.number_input("Degrees", 0, 180, value=st.session_state.lon_deg, key="lon_deg")
        minu = st.number_input("Minutes", 0, 59, value=st.session_state.lon_min, key="lon_min")
        sec = st.number_input("Seconds", 0.0, 59.999, value=st.session_state.lon_sec, key="lon_sec", format="%.6f")

        if st.button("Compute Time Zone"):
            dec_deg, tz_hours, sgn, h, m, s = longitude_to_tz_explanation(deg, minu, sec)
            sign_char = "+" if sgn>=0 else "-"
            st.success(f"Time Zone: {sign_char}{h:02d}:{m:02d}:{s:06.3f}")
            st.markdown("### Explanation")
            st.write(f"**Step 1: Convert D:M:S → Decimal Degrees:** {deg} + {minu}/60 + {sec}/3600 = {dec_deg:.6f}°")
            st.write(f"**Step 2: Decimal Degrees → Time Zone (hours):** {dec_deg:.6f}/15 = {tz_hours:.6f} h")
            st.write(f"**Step 3: Decimal Hours → H:M:S:** {h}:{m}:{s:.3f}")

    else:
        st.subheader("Enter Time Zone Offset")
        tz_sign = st.selectbox("Sign", ["+","-"], key="tz_sign")
        tz_h = st.number_input("Hours", 0, 18, key="tz_h")
        tz_m = st.number_input("Minutes",0,59,key="tz_m")
        tz_s = st.number_input("Seconds",0.0,59.999,key="tz_s")
        if st.button("Compute Longitude"):
            dec_hours, lon, sgn, d, m_val, s_val = tz_to_longitude_explanation(tz_h, tz_m, tz_s, tz_sign)
            st.session_state.computed_lon = lon
            dir_char = "E" if sgn>=0 else "W"
            st.success(f"Longitude: {dir_char} {d}° {m_val}' {s_val:.3f}\"")
            st.markdown("### Explanation")
            st.write(f"**Step 1: Convert H:M:S → Decimal Hours:** {tz_h} + {tz_m}/60 + {tz_s}/3600 = {dec_hours:.6f} h")
            st.write(f"**Step 2: Decimal Hours → Longitude:** {dec_hours:.6f} * 15 = {lon:.6f}°")
            st.write(f"**Step 3: Decimal Degrees → D:M:S:** {d}° {m_val}' {s_val:.3f}\"")

    # ---------------- Batch Upload ----------------
    st.header("Batch Upload")
    uploaded_file = st.file_uploader("Upload CSV/Excel for batch conversion", type=["csv","xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            # Determine conversion type from columns
            if "Longitude_deg" in df.columns:
                # Longitude→Time
                results=[]
                for _,row in df.iterrows():
                    dec_deg = dms_to_decimal(row['Longitude_deg'], row.get('Longitude_min',0),
                                             row.get('Longitude_sec',0), 1)
                    tz_hours = dec_deg/15
                    sgn,h,m,s = tz_hours_to_hms(tz_hours)
                    results.append([f"{'+' if sgn>=0 else '-'}{h:02d}:{m:02d}:{s:06.3f}"])
                df['TimeZone'] = results
            elif "Time_h" in df.columns:
                # Time→Longitude
                results=[]
                for _,row in df.iterrows():
                    dec_hours = hms_to_decimal_hours(row['Time_h'], row.get('Time_m',0), row.get('Time_s',0),1)
                    lon = longitude_from_timezone_hours(dec_hours)
                    sgn,d,m_val,s_val = decimal_to_dms(lon)
                    results.append([f"{'E' if sgn>=0 else 'W'} {d}° {m_val}' {s_val:.3f}\""])
                df['Longitude'] = results
            else:
                st.error("Columns not recognized for conversion")
                df=None
            if df is not None:
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Result CSV", data=csv, file_name="converted.csv")
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ---------------- RIGHT PANEL ----------------
with right:
    st.header("Interactive Map")
    # green line uses computed_lon if exists else clicked_lon
    highlight_lon = st.session_state.computed_lon if st.session_state.computed_lon is not None else st.session_state.clicked_lon or 0.0
    highlight_lat = st.session_state.clicked_lat or 0.0

    m = folium.Map(location=[highlight_lat, highlight_lon], zoom_start=4)

    # gray meridians
    for lon_val in range(-180,181,30):
        folium.PolyLine([[90, lon_val],[-90, lon_val]],color="gray",weight=1).add_to(m)

    # green line
    folium.PolyLine([[90,highlight_lon],[-90,highlight_lon]],
                    color="green",weight=3,opacity=0.7,
                    tooltip=f"Selected/Computed Longitude: {highlight_lon:.4f}°").add_to(m)

    # add slider as map control for green line
    slider_lon = st.slider("Move Green Longitude Line", -180.0, 180.0, float(highlight_lon), step=0.1)
    highlight_lon = slider_lon
    folium.PolyLine([[90,highlight_lon],[-90,highlight_lon]],
                    color="green",weight=3,opacity=0.7).add_to(m)

    map_data = st_folium(m,width=700,height=450)

    # map click behavior
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.clicked_lat = lat
        st.session_state.clicked_lon = lon
        # Auto-fill longitude input ONLY in Longitude→Time mode
        if mode=="Longitude → Time Zone":
            st.experimental_rerun()

    st.markdown(f"**Last Map Click:** Latitude={st.session_state.clicked_lat:.6f}°, Longitude={st.session_state.clicked_lon if st.session_state.clicked_lon is not None else 0.0:.6f}°")
