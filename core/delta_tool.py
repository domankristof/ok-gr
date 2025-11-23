import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def time_to_seconds(t):
    """Convert strings like '2:15.432' → seconds as float."""
    if pd.isna(t):
        return np.nan
    if isinstance(t, (int, float)):
        return float(t)

    t = str(t)
    parts = t.split(":")
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    elif len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    return np.nan


def deltas_tool(sectors_file, car_number: int):
    """
    Compute:
    - Sector deltas vs personal best
    - Sector deltas vs session best
    - Lap deltas vs PB and reference
    - Optimal lap
    - Driver consistency score (0–100)
    """

    sectors_file.seek(0)
    df = pd.read_csv(sectors_file, sep=";")
    df.columns = df.columns.str.strip() # Clean column names

    # Convert lap time to seconds
    df["LAP_TIME_S"] = df["LAP_TIME"].apply(time_to_seconds)

    # Sector columns available in your dataset
    sector_cols = ["S1_SECONDS", "S2_SECONDS", "S3_SECONDS"]

    # Filter rows for this driver
    driver_df = df[df["NUMBER"] == car_number].copy()
    if driver_df.empty:
        raise ValueError(f"Car {car_number} not found in file.")

    # ---------------------------------------
    # Personal bests
    # ---------------------------------------
    personal_best = {
        "S1": driver_df["S1_SECONDS"].min(),
        "S2": driver_df["S2_SECONDS"].min(),
        "S3": driver_df["S3_SECONDS"].min(),
        "LAP": driver_df["LAP_TIME_S"].min(),
    }

    # Optimal lap = sum of best sectors
    optimal_lap = (
        personal_best["S1"]
        + personal_best["S2"]
        + personal_best["S3"]
    )

    # ---------------------------------------
    # Session-best references
    # ---------------------------------------
    reference_bests = {
        "S1": df["S1_SECONDS"].min(),
        "S2": df["S2_SECONDS"].min(),
        "S3": df["S3_SECONDS"].min(),
        "LAP": df["LAP_TIME_S"].min(),
    }

    # ---------------------------------------
    # Per-lap deltas
    # ---------------------------------------
    deltas = []

    for _, row in driver_df.iterrows():
        lap = int(row["LAP_NUMBER"])
        s1 = row["S1_SECONDS"]
        s2 = row["S2_SECONDS"]
        s3 = row["S3_SECONDS"]
        lap_time = row["LAP_TIME_S"]

        deltas.append({
            "Lap": lap,
            "Delta_S1_Personal": s1 - personal_best["S1"],
            "Delta_S2_Personal": s2 - personal_best["S2"],
            "Delta_S3_Personal": s3 - personal_best["S3"],
            "Delta_Lap_Personal": lap_time - personal_best["LAP"],

            "Delta_S1_Reference": s1 - reference_bests["S1"],
            "Delta_S2_Reference": s2 - reference_bests["S2"],
            "Delta_S3_Reference": s3 - reference_bests["S3"],
            "Delta_Lap_Reference": lap_time - reference_bests["LAP"],
        })

    deltas_df = pd.DataFrame(deltas).sort_values("Lap")

    # ---------------------------------------
    # Driver consistency score (0–100)
    # ---------------------------------------
    lap_times = driver_df["LAP_TIME_S"].dropna()

    if len(lap_times) > 1:
        mean_lap = lap_times.mean()
        std_lap = lap_times.std()
        coeff_var = std_lap / mean_lap  # relative variation

        consistency_score = 100 - (coeff_var * 100)
        consistency_score = max(0, min(100, consistency_score))  # clamp
    else:
        consistency_score = None


    # -------------------------------------------------------
    # Return everything including plot path
    # -------------------------------------------------------
    return {
        "car_number": car_number,
        "personal_best": personal_best,
        "optimal_lap": optimal_lap,
        "reference_bests": reference_bests,
        "consistency_score": round(consistency_score, 2) if consistency_score else None,
        "deltas": deltas_df,
        #"plot_path": filename,
    }