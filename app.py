import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium

# ---------------- UTILITY FUNCTIONS ----------------
def dms_to_decimal(degrees, minutes, seconds, sign=1):
    return sign * (degrees + minutes/60 + seconds/3600)

def decimal_to_dms(decimal_deg):
    sgn = 1 if decimal_deg >= 0 else -1
    decimal_deg = abs(decimal_deg)
    d = int(decimal_deg)
    m = int((decimal_deg - d) * 60)
    s = (decimal_deg - d - m/60)*3600
    return sgn, d, m, s

def hms_to_decimal_hours(h, m, s, sign=1):
    return sign * (h + m/60 + s/3600)

def tz_hours_to_hms(tz_hours):
    sgn = 1 if tz_hours >=0 else -1
    tz_hours = abs(tz_hours)
    h = int(tz_hours)
    m = int((tz_hours - h)*60)
    s = (tz_hours - h - m/60)*3600
    return sgn, h, m, s

def longitude_from_timezone_hours(decimal_hours):
    return decimal_hours * 15

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Time Zone ↔ Longitude Calculator", layout="wide")

# ---------------- SESSION STATE DEFAULTS ----------------
defaults = {
    "clicked_lon": 0.0,
    "clicked_lat": 0.0,
    "computed_lon": None,
    "lon_dir": "E (positive)",
    "lon_deg": 0,
    "lon_min": 0,
    "lon_sec": 0.0,
    "tz_sign_auto": True,
    "tz_sign": "+",
    "tz_h": 0,
    "tz_m": 0,
    "tz_s": 0.0
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- LAYOUT ----------------
st.title("🕰️ 🌍 Time Zone ↔ Longitude Calculator")
st.markdown("Click map or move slider for longitude selection. Single conversion or batch CSV/Excel upload.")

left, right = st.columns([1,1])

# ---------------- LEFT PANEL ----------------
with left:
    st.header("Single Conversion")
    mode = st.radio("Conversion Direction", ["Longitude → Time Zone", "Time Zone → Longitude"])

    # ---------------- Longitude → Time Zone ----------------
    if mode == "Longitude → Time Zone":
        st.subheader("Enter Longitude (D:M:S)")
        lon_dir = st.selectbox(
            "Direction",
            ["E (positive)","W (negative)"],
            index=["E (positive)","W (negative)"].index(st.session_state.get("lon_dir","E (positive)")),
            key="lon_dir"
        )
        deg = st.number_input("Degrees", 0, 180, value=st.session_state.get("lon_deg",0), key="lon_deg")
        minu = st.number_input("Minutes", 0, 59, value=st.session_state.get("lon_min",0), key="lon_min")
        sec = st.number_input("Seconds", 0.0, 59.999, value=st.session_state.get("lon_sec",0.0), key="lon_sec", format="%.6f")

        if st.button("Compute Time Zone"):
            sign = 1 if lon_dir.startswith("E") else -1
            dec_deg = dms_to_decimal(deg, minu, sec, sign)
            tz_hours = dec_deg / 15
            sgn_tz, h, m, s = tz_hours_to_hms(tz_hours)
            sign_char = "+" if sgn_tz>=0 else "-"

            st.success(f"Time Zone: {sign_char}{h:02d}:{m:02d}:{s:06.3f}")

            st.markdown("### Step-by-Step Explanation")
            st.write(f"**Step 1:** Convert D:M:S → Decimal Degrees = {deg} + {minu}/60 + {sec}/3600 = {dec_deg:.6f}°")
            st.write(f"**Step 2:** Decimal Degrees → Time Zone (hours) = {dec_deg:.6f} / 15 = {tz_hours:.6f} h")
            hours = int(tz_hours)
            minutes = int(abs(tz_hours - hours)*60)
            seconds = (abs(tz_hours - hours)*60 - minutes)*60
            st.write(f"**Step 3:** Decimal Hours → H:M:S = {hours}:{minutes}:{seconds:.3f}")

    # ---------------- Time Zone → Longitude ----------------
    else:
        st.subheader("Enter Time Zone Offset")
        st.checkbox("Auto-update time from map click", value=True, key="tz_sign_auto")
        tz_sign = st.selectbox("Sign", ["+","-"], index=["+","-"].index(st.session_state.get("tz_sign","+")), key="tz_sign")
        tz_h = st.number_input("Hours", 0, 12, value=st.session_state.get("tz_h",0), key="tz_h")
        tz_m = st.number_input("Minutes",0,59,value=st.session_state.get("tz_m",0),key="tz_m")
        tz_s = st.number_input("Seconds",0.0,59.999,value=st.session_state.get("tz_s",0.0),key="tz_s")
        if st.button("Compute Longitude"):
            sign_val = 1 if tz_sign=="+" else -1
            dec_hours = hms_to_decimal_hours(tz_h, tz_m, tz_s, sign_val)
            lon = longitude_from_timezone_hours(dec_hours)
            st.session_state["computed_lon"] = lon
            sgn_lon, d, m_val, s_val = decimal_to_dms(lon)
            st.success(f"Longitude: {'E' if sgn_lon>=0 else 'W'} {d}° {m_val}' {s_val:.3f}\"")

            st.markdown("### Step-by-Step Explanation")
            st.write(f"**Step 1:** Convert H:M:S → Decimal Hours = {tz_h} + {tz_m}/60 + {tz_s}/3600 = {dec_hours:.6f} h")
            st.write(f"**Step 2:** Decimal Hours → Longitude = {dec_hours:.6f} * 15 = {lon:.6f}°")
            st.write(f"**Step 3:** Decimal Degrees → D:M:S = {d}° {m_val}' {s_val:.3f}\"")

    # ---------------- Batch Upload ----------------
    st.header("Batch Upload")
    uploaded_file = st.file_uploader("Upload CSV/Excel for batch conversion", type=["csv","xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            results=[]
            if "Longitude_deg" in df.columns:
                for _, row in df.iterrows():
                    dec_deg = dms_to_decimal(row['Longitude_deg'], row.get('Longitude_min',0), row.get('Longitude_sec',0), 1)
                    tz_hours = dec_deg / 15
                    sgn, h, m, s = tz_hours_to_hms(tz_hours)
                    results.append(f"{'+' if sgn>=0 else '-'}{h:02d}:{m:02d}:{s:06.3f}")
                df['TimeZone'] = results
            elif "Time_h" in df.columns:
                for _, row in df.iterrows():
                    dec_hours = hms_to_decimal_hours(row['Time_h'], row.get('Time_m',0), row.get('Time_s',0),1)
                    lon = longitude_from_timezone_hours(dec_hours)
                    sgn, d, m_val, s_val = decimal_to_dms(lon)
                    results.append(f"{'E' if sgn>=0 else 'W'} {d}° {m_val}' {s_val:.3f}\"")
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
    highlight_lon = float(st.session_state.get("computed_lon") or st.session_state.get("clicked_lon") or 0.0)
    highlight_lat = float(st.session_state.get("clicked_lat") or 0.0)

    m = folium.Map(location=[highlight_lat, highlight_lon], zoom_start=4)
    # Gray meridians
    for lon_val in range(-180, 181, 30):
        folium.PolyLine([[90, lon_val], [-90, lon_val]], color="gray", weight=1).add_to(m)
    # Green line
    folium.PolyLine([[90, highlight_lon], [-90, highlight_lon]], color="green", weight=3, opacity=0.7, tooltip=f"Longitude: {highlight_lon:.4f}°").add_to(m)

    # Slider for green line
    slider_lon = st.slider("Move Green Longitude Line", -180.0, 180.0, value=highlight_lon, step=0.1)
    highlight_lon = slider_lon

    # Update session state safely
    st.session_state["clicked_lon"] = highlight_lon
    if mode=="Longitude → Time Zone":
        sgn, d, m_val, s_val = decimal_to_dms(highlight_lon)
        st.session_state["lon_dir"] = "E (positive)" if sgn>=0 else "W (negative)"
        st.session_state["lon_deg"] = d
        st.session_state["lon_min"] = m_val
        st.session_state["lon_sec"] = round(s_val,6)
    elif mode=="Time Zone → Longitude" and st.session_state.tz_sign_auto:
        dec_hours = highlight_lon / 15
        sgn, h, m, s = tz_hours_to_hms(dec_hours)
        st.session_state["tz_sign"] = "+" if sgn>=0 else "-"
        st.session_state["tz_h"] = h
        st.session_state["tz_m"] = m
        st.session_state["tz_s"] = s

    # Add green line for slider
    folium.PolyLine([[90, highlight_lon], [-90, highlight_lon]], color="green", weight=3, opacity=0.7).add_to(m)

    # Render map
    map_data = st_folium(m, width=700, height=450)

    # Handle map clicks
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state["clicked_lat"] = lat
        st.session_state["clicked_lon"] = lon
        st.experimental_rerun()

    st.markdown(f"**Last Map Click:** Latitude={st.session_state.clicked_lat:.6f}°, Longitude={st.session_state.clicked_lon:.6f}°")
