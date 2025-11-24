import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def time_to_seconds(t):
    """Convert time formats like '1:25.342' or '55.123' into seconds as float.
    Handles NaN/None gracefully.
    """
    if pd.isna(t) or t is None:
        return None
    
    # If it's already a number, return it as a float
    if isinstance(t, (float, int)):
        return float(t)

    t = str(t).strip()
    if not t: # Handle empty string
        return None

    parts = t.split(":")

    try:
        if len(parts) == 1:         # SS.sss
            return float(parts[0])
        elif len(parts) == 2:       # M:SS.sss
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 3:       # H:MM:SS.sss
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        # Catch errors from non-convertible strings
        return None

    return None


def deltas_tool(sectors_file, car_number: int):
    """
    Compute:
    - Sector deltas (PB + leader)
    - Lap deltas (PB + leader)
    - Driver consistency score
    - Optimal lap
    - JSON-safe output
    """
    # Load + clean
    df = pd.read_csv(sectors_file, sep=";", engine='python', skipinitialspace=True)
    df.columns = df.columns.str.strip()

    # Column names
    vehicle_number_col = "NUMBER"
    lap_number_col = "LAP_NUMBER"
    lap_time_col = "LAP_TIME"
    sector1_col = "S1_SECONDS"
    sector2_col = "S2_SECONDS"
    sector3_col = "S3_SECONDS"

    # Filter driver
    driver_df = df[df[vehicle_number_col] == car_number].copy()
    if driver_df.empty:
        raise ValueError(f"Car {car_number} not found.")

    # Convert lap times → seconds
    df["LAP_TIME_S"] = df[lap_time_col].apply(time_to_seconds)
    driver_df["LAP_TIME_S"] = driver_df[lap_time_col].apply(time_to_seconds)

    # Personal bests
    personal_bests = {
        "S1": driver_df[sector1_col].min(),
        "S2": driver_df[sector2_col].min(),
        "S3": driver_df[sector3_col].min(),
        "LAP": driver_df["LAP_TIME_S"].min()
    }

    # Optimal lap
    optimal_lap = personal_bests["S1"] + personal_bests["S2"] + personal_bests["S3"]

    # Global bests (leader)
    session_bests = {
        "S1": df[sector1_col].min(),
        "S2": df[sector2_col].min(),
        "S3": df[sector3_col].min(),
        "LAP": df["LAP_TIME_S"].min()
    }

    # Build lap-by-lap deltas
    deltas = []
    for _, row in driver_df.iterrows():
        deltas.append({
            "Lap": int(row[lap_number_col]),
            "S1": row[sector1_col],
            "S2": row[sector2_col],
            "S3": row[sector3_col],
            "LapTime": row["LAP_TIME_S"],

            "Delta_S1_PB": row[sector1_col] - personal_bests["S1"],
            "Delta_S2_PB": row[sector2_col] - personal_bests["S2"],
            "Delta_S3_PB": row[sector3_col] - personal_bests["S3"],
            "Delta_Lap_PB": row["LAP_TIME_S"] - personal_bests["LAP"],

            "Delta_S1_Leader": row[sector1_col] - session_bests["S1"],
            "Delta_S2_Leader": row[sector2_col] - session_bests["S2"],
            "Delta_S3_Leader": row[sector3_col] - session_bests["S3"],
            "Delta_Lap_Leader": row["LAP_TIME_S"] - session_bests["LAP"],
        })

    deltas_df = pd.DataFrame(deltas).sort_values("Lap")

    # Return JSON-safe output
    return {
        "car_number": car_number,
        "personal_bests": personal_bests,
        "session_bests": session_bests,
        "optimal_lap": optimal_lap,
        "deltas": deltas_df,  # wrapper will convert to JSON
    }