import pandas as pd
import numpy as np
import streamlit as st

from core.delta_tool import time_to_seconds


def summary_deltas(sectors_file, car_number: int):
    """
    Compute:
    - Sector deltas (PB + leader)
    - Lap deltas (PB + leader)
    - Driver consistency score (0–100)
    - Optimal lap (sum of best sectors)
    - JSON-safe output for the agent

    Args:
        sectors_file (str): Path to the semicolon-separated CSV file.
        car_number (int): The car number to analyze.
    
    Returns:
        dict: A JSON-safe dictionary containing the analysis results.
    """
    sectors_file.seek(0)  # Ensure we're at the start of the file
    # ------------------------------------------
    # 1. LOAD FILE + FIX COLUMN NAMES
    # ------------------------------------------
    # FIX: Using 'python' engine and 'skipinitialspace' for maximum robustness
    try:
        df = pd.read_csv(sectors_file, sep=";", engine='python', skipinitialspace=True)
    except pd.errors.EmptyDataError:
        st.write("The file could not be parsed. Check if the file is completely empty or if the first line is malformed.")
        raise pd.errors.EmptyDataError(
            "The file could not be parsed. Check if the file is completely empty or if the first line is malformed."
        )

    #Names for columns
    vehicle_number_col = "NUMBER"
    lap_number_col = "LAP_NUMBER"
    lap_time_col = "LAP_TIME"

    sector1_col = "S1_SECONDS"
    sector2_col = "S2_SECONDS"
    sector3_col = "S3_SECONDS"

    # ------------------------------------------
    # 3. FILTER DRIVER
    # ------------------------------------------
    driver_df = df[df[vehicle_number_col] == car_number].copy()

    # ------------------------------------------
    # 4. PERSONAL BESTS
    # ------------------------------------------
    if driver_df.empty:
        # Check if the driver exists at all (might be float vs int comparison issue)
        if not df[df[vehicle_number_col].astype(str) == str(car_number)].empty:
            driver_df = df[df[vehicle_number_col].astype(str) == str(car_number)].copy()
        
        if driver_df.empty:
            st.write(f"Car {car_number} not found in the dataset.")
            raise ValueError(f"Car {car_number} not found in the dataset.")
        
    personal_bests = {
        sector1_col: driver_df[sector1_col].min(),
        sector2_col: driver_df[sector2_col].min(),
        sector3_col: driver_df[sector3_col].min(),
        lap_time_col: driver_df[lap_time_col].min(),
    }
    st.write("Personal Bests:")
    st.write(personal_bests)

    # Calculate Optimal Lap (sum of the personal best sectors)
    optimal_lap = (
        personal_bests[sector1_col]
        + personal_bests[sector2_col]
        + personal_bests[sector3_col]
    )
    st.write(f"Optimal Lap Time: {optimal_lap}")

    # Global best sectors (leader)
    session_bests = {
        sector1_col: df[sector1_col].min(),
        sector2_col: df[sector2_col].min(),
        sector3_col: df[sector3_col].min(),
        lap_time_col: df[lap_time_col].min(),
    }
    st.write("Session Bests (Leader):")
    st.write(session_bests)

    # ---------- GLOBAL BEST DELTAS ----------
    # Convert lap times to seconds for correct math
    driver_best_lap_s = driver_df[lap_time_col].apply(time_to_seconds).min()
    session_best_lap_s = df[lap_time_col].apply(time_to_seconds).min()

    sector_deltas = {
        "Sector 1 PB Delta": personal_bests[sector1_col] - session_bests[sector1_col],
        "Sector 2 PB Delta": personal_bests[sector2_col] - session_bests[sector2_col],
        "Sector 3 PB Delta": personal_bests[sector3_col] - session_bests[sector3_col],
        "Lap PB Delta": driver_best_lap_s - session_best_lap_s,
        "Optimal Lap Delta": optimal_lap - session_best_lap_s,
    }

    st.write("### Global Best Deltas")

    cols = st.columns(3)

    cols[0].metric("S1 PB Δ", f"{sector_deltas['Sector 1 PB Delta']:+.3f}s")
    cols[1].metric("S2 PB Δ", f"{sector_deltas['Sector 2 PB Delta']:+.3f}s")
    cols[2].metric("S3 PB Δ", f"{sector_deltas['Sector 3 PB Delta']:+.3f}s")

    cols = st.columns(2)
    cols[0].metric("Lap PB Δ", f"{sector_deltas['Lap PB Delta']:+.3f}s")
    cols[1].metric("Optimal Lap Δ", f"{sector_deltas['Optimal Lap Delta']:+.3f}s")