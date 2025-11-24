    # -------------------------
    # PLOTS
    # -------------------------
    st.subheader(f"Telemetry Summary for Vehicle {vehicle_number}")
    
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
                    st.map(gps_map_data, zoom=25, size=0.01, width="stretch")
                else:
                    st.warning("GPS data (lat/lon) is available but contains no valid numeric points after conversion.")
            except Exception as e:
                st.error(f"Error drawing st.map (likely non-numeric GPS data): {e}")
    else:
        st.warning(f"GPS data not found. Check signal names: Lat='{GPS_LAT_NAME}', Lon='{GPS_LON_NAME}'")