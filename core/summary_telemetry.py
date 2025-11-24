import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
# Assuming core.load_telemetry.py is fixed and available

def summarize_telemetry(df: pd.DataFrame, vehicle_number: int):
    """
    Summaries telemetry for a single vehicle:
        - Speed over time
        - RPM over time
        - Throttle & Brake over time
        - GPS trace
    """
    
    # -------------------------
    # DATA CLEANING & PREP
    # -------------------------
    
    # Identify the key columns defensively
    VEHICLE_COL = 'vehicle_number'
    
    # Ensure all column names are stripped for safety
    df.columns = df.columns.str.strip()
    
    # Check if the critical vehicle column exists
    if VEHICLE_COL not in df.columns:
        # Try to find a column that looks like it
        potential_cols = [c for c in df.columns if 'vehicle' in c.lower()]
        if potential_cols:
            VEHICLE_COL = potential_cols[0]
            st.warning(f"Using column '{VEHICLE_COL}' as the vehicle identifier.")
        else:
            st.error(f"Cannot find the required '{VEHICLE_COL}' column in the data.")
            return

    # Convert safely (invalid → NaT or NaN)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df[VEHICLE_COL] = pd.to_numeric(df[VEHICLE_COL], errors="coerce").fillna(-1).astype('int64')
    df["telemetry_value"] = pd.to_numeric(df["telemetry_value"], errors="coerce")
    # Drop invalid timestamps
    df = df.dropna(subset=["timestamp"])
    
    # -------------------------
    # VEHICLE FILTER
    # -------------------------
    # Now filter using the guaranteed-to-be-integer column
    user_df = df[df[VEHICLE_COL] == vehicle_number].copy()

    if user_df.empty:
        st.warning(f"No telemetry found for vehicle {vehicle_number} after cleaning.")
        return 

    # --- DEBUGGING TELEMETRY NAMES ---
    # 🌟 IMPORTANT: This list shows the exact signal names you must use below.
    # If the GPS trace doesn't show, check this list for the correct Lat/Lon names.
    all_signals = user_df['telemetry_name'].unique()
    st.info(f"Unique Signals for Vehicle {vehicle_number}: {all_signals}")
    # ---------------------------------

    # -------------------------
    # Helper to extract telemetry signals (using user_df now)
    # -------------------------
    def get_telemetry_value(telemetry_name):
        # Normalize comparison to handle case/whitespace errors
        normalized_data_names = user_df["telemetry_name"].astype(str).str.strip().str.lower()
        normalized_lookup = telemetry_name.strip().lower()
        
        # Filter rows
        mask = normalized_data_names == normalized_lookup
        
        # Select both columns and sort by time
        result_df = user_df.loc[mask, ["timestamp", "telemetry_value"]].copy() 
        return result_df.sort_values("timestamp")

    # -------------------------
    # EXTRACT STREAMS 
    # -------------------------
    # Example placeholders for other signals (these seem correct for your data)
    speed_name = "Speed" 
    rpm_name = "nmot"
    throttle_name = "aps"
    brake_name = "pbrake_f"
    
    GPS_LAT_NAME = "VBOX_Lat_Min" 
    GPS_LON_NAME = "VBOX_Long_Minutes"
   
    speed_data = get_telemetry_value(speed_name)
    engine_rpm_data = get_telemetry_value(rpm_name)
    throttle_pedal_data = get_telemetry_value(throttle_name)
    brake_pressure_data = get_telemetry_value(brake_name)

    # -------------------------
    # PLOTS
    # -------------------------
    st.header(f"Telemetry Summary for Vehicle {vehicle_number}")

    # SPEED PLOT
    if not speed_data.empty:
        st.subheader(f"Speed Over Time ({speed_name})")

        df_smooth = speed_data.copy()
        df_smooth["smooth_speed"] = df_smooth["telemetry_value"].rolling(window=200, min_periods=1).mean()

        # --- FIX: convert to python datetime ---
        min_t = pd.to_datetime(df_smooth["timestamp"].min()).to_pydatetime()
        max_t = pd.to_datetime(df_smooth["timestamp"].max()).to_pydatetime()

        start_t, end_t = st.slider(
            "Select time window",
            min_value=min_t,
            max_value=max_t,
            value=(min_t, max_t),
            format="HH:mm:ss"
        )

        # --- FIX: Also convert df timestamps to python datetime ---
        speed_data["ts_py"] = pd.to_datetime(speed_data["timestamp"]).apply(lambda x: x.to_pydatetime())

        mask = (speed_data["ts_py"] >= start_t) & (speed_data["ts_py"] <= end_t)
        cropped = speed_data[mask]

        st.line_chart(
            data=cropped.set_index("ts_py")["telemetry_value"],
            height=300,
            use_container_width=True,
        )

    
    # RPM PLOT
    if not engine_rpm_data.empty:
         st.subheader(f"Engine RPM ({rpm_name})")
         st.line_chart(
            data=engine_rpm_data.set_index("timestamp"),
            height=300,
            use_container_width=True,
        )

    # THROTTLE & BRAKE PLOT (Combined)
    if not throttle_pedal_data.empty or not brake_pressure_data.empty:
        st.subheader("Throttle and Brake Pedal Position")
        
        # Combine into a single DF for multi-line chart
        pedal_data = pd.merge_asof(
            throttle_pedal_data.rename(columns={'telemetry_value': 'Throttle'}),
            brake_pressure_data.rename(columns={'telemetry_value': 'Brake'}),
            on="timestamp",
            direction="nearest"
        )
        
        if not pedal_data.empty:
             st.line_chart(
                data=pedal_data.set_index("timestamp"),
                height=300,
                use_container_width=True,
            )

    # === GPS Path (match timestamps via merge_asof) ===
    gps_lon = get_telemetry_value(GPS_LON_NAME)
    gps_lat = get_telemetry_value(GPS_LAT_NAME)
    
    if not gps_lon.empty and not gps_lat.empty:
        st.subheader("GPS Trace")
        gps = pd.merge_asof(
            gps_lon.rename(columns={'telemetry_value': 'lon'}),
            gps_lat.rename(columns={'telemetry_value': 'lat'}),
            on="timestamp",
            direction="nearest"
        )

        if not gps.empty:
            # Use Streamlit's native map function for simpler GPS plotting
            try:
                # Need to convert to float because telemetry_value is sometimes read as object/string initially
                gps_map_data = gps[['lat', 'lon']].astype(float).dropna()
                if not gps_map_data.empty:
                    st.map(gps_map_data, zoom=30, size=0.01, width="stretch")
                else:
                    st.warning("GPS data (lat/lon) is available but contains no valid numeric points after conversion.")
            except Exception as e:
                st.error(f"Error drawing st.map (likely non-numeric GPS data): {e}")
    else:
        st.warning(f"GPS data not found. Check signal names: Lat='{GPS_LAT_NAME}', Lon='{GPS_LON_NAME}'")