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
    rain_detected = "Rain Detected" if df["RAIN"].sum() > 0 else "No Rain"


    air_temp_data = df["AIR_TEMP"]
    track_temp_data = df["TRACK_TEMP"]
    wind_speed_data = df["WIND_SPEED"]

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
        <div style="font-size: 26px; font-weight: 600; margin-top: -10px;">
            Session Conditions
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="font-size: 22px; font-weight: 400; margin-top: 10px;">
            {icon} {status}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # --- METRICS ROW 1 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Air Temp (°C)", f"{avg_air:.1f}",chart_type="line", chart_data=air_temp_data)
    with col2:
        st.metric("Track Temp (°C)", f"{avg_track:.1f}",chart_type="line", chart_data=track_temp_data)
    with col3:
        st.metric("Wind Speed (m/s)", f"{avg_wind:.1f}",chart_type="line", chart_data=wind_speed_data)
    with col4:
        st.metric("Humidity (%)", f"{avg_humidity:.1f}")
        st.metric("Rain Events", f"{rain_detected}")