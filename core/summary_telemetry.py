import pandas as pd
import numpy as np
import streamlit as st
from core.load_telemetry import load_parquet_from_supabase
from core.supabase_client import supabase, BUCKET

import matplotlib.pyplot as plt


def summarize_telemetry(df: pd.DataFrame, vehicle_number: int):
    """
    Summaries telemetry for a single vehicle:
        - Speed over time
        - RPM over time
        - Throttle & Brake over time
        - GPS trace
    """

    # Columns of interests
    vehicle_number = df['vehicle_number']
    telemetry_name = df['telemetry_name']
    telemetry_value = df['telemetry_value']
    timestamp = pd.to_datetime(df["timestamp"])

    # -------------------------
    # Auto-detect timestamp column
    timestamp_candidates = ["timestamp", "TIME_UTC_STR", "TIME_UTC", "time", "time_utc"]
    ts_col = next((c for c in timestamp_candidates if c in df.columns), None)

    if ts_col is None:
        st.error("No timestamp column found.")
        return

    # Convert safely (invalid → NaT)
    df["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce")

    # Remove bad rows such as "1"
    before = len(df)
    df = df.dropna(subset=["timestamp"])
    after = len(df)

    if before != after:
        st.warning(f"Dropped {before - after} rows with invalid timestamps.")

    # -------------------------

    #Filtering for the user's vehicle number
    user_df = df[df['vehicle_number'] == vehicle_number].copy()

    if user_df.empty:
        st.warning(f"No telemetry data found for vehicle number {vehicle_number}.")
        return
    
    # Convert timestamp column to datetime
    user_df['timestamp'] = pd.to_datetime(user_df['timestamp'])


    #Helper function to filter telemetry data by name
    def filter_telemetry_by_name(name):
        return user_df[user_df["telemetry_name"] == name][["timestamp", "telemetry_value"]]
    
    #Extracting telemetry data
    speed_data = filter_telemetry_by_name('Speed')
    gear_data = filter_telemetry_by_name('Gear')
    engine_rpm_data = filter_telemetry_by_name('nmot')
    throttle_blade_data = filter_telemetry_by_name('ath')
    throttle_pedal_data = filter_telemetry_by_name('aps')
    front_brake_pressure_data = filter_telemetry_by_name('pbrake_f')
    rear_brake_pressure_data = filter_telemetry_by_name('pbrake_r')
    longitudinal_accel_data = filter_telemetry_by_name('accx_can')
    lateral_accel_data = filter_telemetry_by_name('accy_can')
    steering_angle_data = filter_telemetry_by_name('Steering_Angle')
    gps_longitude_data = filter_telemetry_by_name('VBOX_Long_Minutes')
    gps_latitude_data = filter_telemetry_by_name('VBOX_Lat_Min')
    dist_from_start_data = filter_telemetry_by_name('Laptrigger_lapdist_dls')
    

    # -------------------------
    # PLOTS
    # -------------------------

    # === Speed Over Time ===
    if not speed_data.empty:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(speed_data["timestamp"], speed_data["telemetry_value"], color="#E10600")
        ax.set_title("Speed Over Time")
        ax.set_xlabel("Time")
        ax.set_ylabel("Speed (km/h)")
        ax.grid(True)
        st.pyplot(fig)

    # === GPS Path ===
    if not gps_longitude_data.empty and not gps_latitude_data.empty:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot(gps_longitude_data["telemetry_value"], gps_latitude_data["telemetry_value"], color="#23F0C7")
        ax.set_title("GPS Trace")
        ax.set_xlabel("Longitude (Minutes)")
        ax.set_ylabel("Latitude (Minutes)")
        ax.axis('equal')
        ax.grid(True)
        st.pyplot(fig)



