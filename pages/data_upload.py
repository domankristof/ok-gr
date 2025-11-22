import pandas as pd
import streamlit as st
import numpy as np

from core.determine_reference import compute_reference_laps

st.set_page_config(
    page_title="Upload Data - OK GR",
    page_icon="📊",
    layout="centered",
)

# Apply the same CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap');

:root{
  --bg:#0B0D10;            /* night track */
  --panel:#12151A;         /* pit-wall console */
  --muted:#1A1F26;         /* shadow panels */
  --text:#E6EAF0;          /* light text */
  --subtle:#98A2B3;        /* secondary text */
  --accent:#E10600;        /* F1 red */
  --neon:#23F0C7;          /* telemetry neon */
  --good:#2ED573;
  --warn:#FFC107;
  --bad:#FF4757;
  --border:#262C36;
}

html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 800px at 10% -10%, #12151A 0%, #0B0D10 45%) no-repeat var(--bg);
  color: var(--text);
  font-family: 'Rajdhani', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica Neue, Arial, "Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol";
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E1116 0%, #0B0D10 100%);
  border-right: 1px solid var(--border);
}

h1, h2, h3, h4, h5 { letter-spacing: 0.5px; }

.hr-line {
  height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 0.8rem 0 1.2rem 0;
}

/* Checkered banner */
.banner {
  position: relative;
  padding: 18px 22px;
  border-radius: 12px;
  background: linear-gradient(180deg, #12151A 0%, #0E1014 100%);
  border: 1px solid var(--border);
  overflow: hidden;
}
.banner:before {
  content: "";
  position: absolute;
  top: 0; right: -80px;
  width: 820px; height: 100%;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.05) 25%, transparent 25%) -20px 0/40px 40px,
    linear-gradient(225deg, rgba(255,255,255,0.05) 25%, transparent 25%) -20px 0/40px 40px,
    linear-gradient(315deg, rgba(255,255,255,0.05) 25%, transparent 25%) 0 0/40px 40px,
    linear-gradient(45deg, rgba(255,255,255,0.05) 25%, transparent 25%) 0 0/40px 40px;
  transform: rotate(-10deg);
  opacity: 0.6;
}
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent);
  color: white; font-weight: 700; font-size: 12px;
  letter-spacing: .4px;
}

/* Cards */
.card {
  border: 1px solid var(--border);
  background: linear-gradient(180deg, #101319 0%, #0C0F14 100%);
  border-radius: 14px;
  padding: 14px 16px;
}
.card h4{
  margin: 0 0 6px 0; color: var(--text); font-weight: 700;
}
.card .meta{ color: var(--subtle); font-size: 13.5px; }
.card .ok { color: var(--good); font-weight: 700; }
.card .miss { color: var(--warn); font-weight: 700; }

/* Upload box tweak */
.css-1v0mbdj, .e1b2p2ww15 { border-radius: 12px !important; }
            
.stFileUploader>div>div {
    background-color: #12151A;
    border: 2px dashed #262C36;
    border-radius: 10px;
    color: #ffffff;
    }

/* Hide the label since you're using label_visibility="hidden" */
.stFileUploader label {
    display: none;
}

.stButton>button {
    background-color: var(--accent);
    color: white;
    font-weight: 700;
    border-radius: 8px;
    border: none;
}
.stButton>button:hover {
    background-color: #bf0500;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="banner" style="position: relative; padding-right: 50px;">
  <span class="badge">Toyota Gazoo Racing</span>
  <img src="https://upload.wikimedia.org/wikipedia/commons/e/e6/Toyota_Gazoo_Racing_emblem.svg"
       style="position: absolute; top: 20px; right: 15px; height: 40px; width: auto;">
  <div style="text-align: left;">
    <h1 style="margin:0;font-weight:800;">OK-GR</h1>
    <h3 style="margin:0;font-weight:500;margin-top:0px;">Data Upload Center</h3>
    <div style="color:#23F0C7;font-weight:400;margin-top:0px;">Upload Your Racing Data</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)

# File Upload Section
st.markdown("""<h4 style="font-weight:500">📁 Upload Your Racing Data</h4>""", unsafe_allow_html=True)

with st.expander("📁 Upload CSVs", expanded=True):
    st.markdown("""<h5 style="font-weight:500">Telemetry File</h5>""", unsafe_allow_html=True)
    telemetry_file = st.file_uploader(
        "telemetry file",
        type=["csv"],
        accept_multiple_files=False,
        key="telemetry_uploader",
        label_visibility="hidden"
    )
    
    st.markdown("""<h5 style="font-weight:500">Lap Times File</h5>""", unsafe_allow_html=True)
    laps_file = st.file_uploader(
        "lap times file",
        type=["csv"],
        accept_multiple_files=False,
        key="laps_uploader",
        label_visibility="hidden"
    )
    
    st.markdown("""<h5 style="font-weight:500">Weather File</h5>""", unsafe_allow_html=True)
    weather_file = st.file_uploader(
        "weather file",
        type=["csv"],
        accept_multiple_files=False,
        key="weather_uploader",
        label_visibility="hidden"
    )
    
    st.markdown("""<h5 style="font-weight:500">Results File</h5>""", unsafe_allow_html=True)
    results_file = st.file_uploader(
        "results file",
        type=["csv"],
        accept_multiple_files=False,
        key="results_uploader",
        label_visibility="hidden"
    )
    
    st.markdown("""<h5 style="font-weight:500">Sectors File</h5>""", unsafe_allow_html=True)
    sectors_file = st.file_uploader(
        "sectors file",
        type=["csv"],
        accept_multiple_files=False,
        key="sectors_uploader",
        label_visibility="hidden"
    )
    
    st.caption("Upload one file containing the relevant data in CSV format to each cell.")

    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Process Files & Analyze", type="primary", use_container_width=True):
            if not any([telemetry_file, laps_file, weather_file, results_file, sectors_file]):
                st.error("Please upload at least one file before submitting.")
            else:
                # Store files in session state
                st.session_state.telemetry_file = telemetry_file
                st.session_state.laps_file = laps_file
                st.session_state.weather_file = weather_file
                st.session_state.results_file = results_file
                st.session_state.sectors_file = sectors_file
                
                st.success("Files submitted for processing!")
                # You can add navigation to analysis page here later
                

    # Display uploaded files
    uploaded_files = [f for f in [telemetry_file, laps_file, weather_file, results_file, sectors_file] if f is not None]
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        for i, file in enumerate(uploaded_files):
            if file is not None:
                st.write(f"{i+1}. {file.name}")



#For debugging:

if laps_file is None:
    st.warning("No laps file uploaded yet.")

    if laps_file is not None:
        st.success("Laps file uploaded.")
        compute_reference_laps(laps_file, car_number=72)


# Footer ----------------------------
st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)
st.caption("OK GR © — Built for the paddock. Python · Streamlit · Plotly")