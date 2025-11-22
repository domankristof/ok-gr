import pandas as pd
import numpy as np
import streamlit as st


# ---------------------------------------------------------
# REFERENCE LAP TOOL
# ---------------------------------------------------------

def compute_reference_laps(laps_file: str, car_number: int):
    """
    Given the 'Top 10 Laps' CSV, return:
        - fastest lap
        - the 10 best laps sorted
        - Streamlit visual
    """
    laps_file.seek(0)
    
    # Load CSV
    # IMPORTANT: semicolon separator
    df = pd.read_csv(laps_file, sep=";")
    
    # Filter to the specific car number
    driver_df = df[df["NUMBER"] == car_number]

    if driver_df.empty:
        raise ValueError(f"Car number {car_number} not found in dataset.")

    # Extract BESTLAP_1 ... BESTLAP_10
    lap_cols = [col for col in driver_df.columns if col.startswith("BESTLAP_")]

    # Convert lap times to seconds
    lap_times = []

    for col in lap_cols:
        raw = driver_df.iloc[0][col]

        if isinstance(raw, str):
            # Convert format "2:08.511" → seconds
            minutes, seconds = raw.split(":")
            total_seconds = int(minutes) * 60 + float(seconds)
            lap_times.append((col, total_seconds))

        elif isinstance(raw, (int, float)):
            # Already numeric
            lap_times.append((col, raw))

        else:
            # Missing or invalid
            continue

    # Sort by lap time
    lap_times_sorted = sorted(lap_times, key=lambda x: x[1])

    # Build a pretty dataframe
    display_df = pd.DataFrame([
        {"Lap": name, "Time (s)": time} for name, time in lap_times_sorted
    ])

    # Return computed values
    fastest_lap_name, fastest_lap_time = lap_times_sorted[0]


    # Also return values programmatically (important for OpenAI tool calling)
    return {
        "car_number": car_number,
        "fastest_lap_name": fastest_lap_name,
        "fastest_lap_time_seconds": fastest_lap_time,
        "lap_order": [{"lap": name, "time_seconds": time} for name, time in lap_times_sorted],
    }
