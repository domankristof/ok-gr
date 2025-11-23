import streamlit as st
import pandas as pd
import numpy as np

def render_weather_summary(weather_file):
    """
    First-pass analysis of the uploaded weather file.
    Shows key metrics and a simple weather status icon.
    """
    # RESET pointer each time so that the data isn't lost
    weather_file.seek(0)

    # --- BASIC CLEANUP ---
    df = pd.read_csv(weather_file, sep=";")
    df["TIME_UTC_STR"] = pd.to_datetime(df["TIME_UTC_STR"])

    avg_air = df["AIR_TEMP"].mean()
    avg_track = df["TRACK_TEMP"].mean()
    avg_humidity = df["HUMIDITY"].mean()
    avg_wind = df["WIND_SPEED"].mean()
    rain_detected = df["RAIN"].sum() > 0

    # --- WEATHER ICON LOGIC ---
    if rain_detected:
        icon = "🌧️"
        status = "Rainy Conditions"
    elif avg_wind > 8:
        icon = "💨"
        status = "Windy"
    elif avg_humidity > 70:
        icon = "⛅"
        status = "Humid / Cloudy"
    else:
        icon = "☀️"
        status = "Clear & Dry"


    st.markdown(
        f"""
        <div style="font-size: 26px; font-weight: 400; margin-top: -10px;">
            {icon} Session Conditions: {status}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # --- METRICS ROW 1 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Air Temp (°C)", f"{avg_air:.1f}")
    with col2:
        st.metric("Track Temp (°C)", f"{avg_track:.1f}")
    with col3:
        st.metric("Humidity (%)", f"{avg_humidity:.1f}")

    # --- METRICS ROW 2 ---
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Wind Speed (m/s)", f"{avg_wind:.1f}")
    with col5:
        st.metric("Pressure (hPa)", f"{df['PRESSURE'].mean():.1f}")
    with col6:
        st.metric("Rain Events", "Yes" if rain_detected else "No")
