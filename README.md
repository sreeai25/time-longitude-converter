# 🌍🕰️ Time Zone ↔ Longitude Calculator

An interactive **Streamlit web app** that converts:

-   **Longitude → Time Zone**
-   **Time Zone → Longitude**

with support for:\
✅ DMS (Degrees--Minutes--Seconds)\
✅ H:M:S (Hours--Minutes--Seconds)\
✅ Interactive map click to auto-fill longitude\
✅ Batch CSV file conversions\
✅ Plots and explanations\
✅ Clean UI and easy deployment

------------------------------------------------------------------------

## 🚀 Features

### 🔹 1. Convert Longitude → Time Zone Offset

-   Enter longitude in **DMS** format\
-   Or simply **click on the world map**\
-   View result in **±HH:MM:SS** format\
-   Includes **step-by-step explanation** of the calculation

### 🔹 2. Convert Time Zone Offset → Longitude

-   Enter offset in **±HH:MM:SS**\
-   Output shown in **DMS** format\
-   Includes explanation of each step

### 🔹 3. Interactive Map

-   Click anywhere on Earth\
-   Longitude (and latitude) auto-filled into calculator\
-   Great for students learning geography

### 🔹 4. CSV Batch Processing

Upload a CSV to convert multiple values at once.

#### Example: Longitude → Time Zone

    deg,min,sec,dir
    75,0,0,E
    120,30,0,E
    45,15,30,W

#### Example: Time Zone → Longitude

    tz_sign,h,m,s
    +,5,30,0
    -,3,0,0
    +,9,45,30

The app adds a new output column automatically.

------------------------------------------------------------------------

## 📁 Repository Structure

    project-folder/
    │
    ├── app.py                     # Main Streamlit application
    ├── utils.py                   # Conversion helper functions
    ├── requirements.txt           # Python dependencies
    │
    ├── .streamlit/
    │   └── config.toml            # Streamlit theme & settings
    │
    └── tests/
        └── test_utils.py          # Unit tests (optional)

⚠️ **No GitHub workflows**, since this project is used by a single
developer\
Streamlit Cloud will still install your dependencies automatically.

------------------------------------------------------------------------

## 🎨 Streamlit Theme

You can modify theme settings inside:

    .streamlit/config.toml

Example:

``` toml
[theme]
primaryColor="#3A7AFE"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F5F7FA"
textColor="#000000"
font="sans serif"
```

------------------------------------------------------------------------

## ▶️ Running the App Locally

### **1. Install dependencies**

    pip install -r requirements.txt

### **2. Run the Streamlit app**

    streamlit run app.py

The browser will open automatically.

------------------------------------------------------------------------

## 🌐 Deployment (Streamlit Cloud)

1.  Push your repository to GitHub\
2.  Go to https://share.streamlit.io\
3.  Connect your GitHub repo\
4.  Streamlit Cloud automatically installs:
    -   Python\
    -   Dependencies from `requirements.txt`\
    -   Runs `app.py`

No workflow files or CI configuration required.

------------------------------------------------------------------------

## 🧪 Unit Tests

Optional but included for completeness.

Run tests:

    pytest

Tests cover: - DMS ↔ decimal degrees\
- H:M:S ↔ decimal hours\
- Longitude ↔ timezone conversion\
- Edge cases (±180°, ±14h)

------------------------------------------------------------------------

## 📚 Educational Notes

### 🌍 Longitude → Time Zone

Earth rotates **15° per hour**.\
So:

    Time offset = Longitude / 15

### 🕰️ Time Zone → Longitude

Reverse:

    Longitude = Offset × 15°

The app also provides step-by-step explanations in the UI.

------------------------------------------------------------------------


## 📝 License

Free for personal and educational use.
