import numpy as np
import streamlit as st
import pandas as pd



def compute_gg_data(user_df):
    # Filter acceleration channels
    lat_df = user_df[user_df["telemetry_name"].isin(GPS_LAT_NAME)]
    lon_df = user_df[user_df["telemetry_name"].isin(GPS_LON_NAME)]
    
    # Pivot into columns
    lat_df = lat_df.rename(columns={"telemetry_value": "lat_g"})
    lon_df = lon_df.rename(columns={"telemetry_value": "long_g"})

    merged = pd.merge(
        lat_df[["timestamp", "lap_number", "lat_g"]],
        lon_df[["timestamp", "lap_number", "long_g"]],
        on=["timestamp", "lap_number"],
        how="inner"
    )
    return merged


