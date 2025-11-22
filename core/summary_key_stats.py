import pandas as pd
import streamlit as st

def lap_to_seconds(x):
    if pd.isna(x):
        return None
    try:
        mm, ss = str(x).split(":")
        return int(mm) * 60 + float(ss)
    except:
        return None


def display_key_summary_stats(top_10_laps_file, car_number: int):

    # RESET pointer each time
    top_10_laps_file.seek(0)

    df = pd.read_csv(top_10_laps_file, sep=";")

    num_of_drivers = df["NUMBER"].nunique()


    # Filter driver
    driver_df = df[df["NUMBER"] == car_number]
    if driver_df.empty:
        st.error(f"Car {car_number} not found in session.")
        return

    # Extract lap-time columns (exclude _LAPNUM)
    lap_cols = [c for c in df.columns if c.startswith("BESTLAP_") and not c.endswith("_LAPNUM")]

    # Convert lap times from “M:SS.mmm” → seconds
    df_lap_times = df[lap_cols].applymap(lap_to_seconds)

    # DRIVER personal times
    driver_times = df_lap_times.loc[driver_df.index].values.flatten()
    driver_times = driver_times[pd.notnull(driver_times)]

    if len(driver_times) == 0:
        st.error("No lap times recorded for this driver.")
        return

    personal_best = min(driver_times)

    # Session times
    session_times = df_lap_times.values.flatten()
    session_times = session_times[pd.notnull(session_times)]

    session_fastest = min(session_times)
    session_sorted = sorted(session_times)
    driver_position = session_sorted.index(personal_best) + 1
    gap_to_fastest = session_fastest - personal_best

    # Display metrics
    col1,col2,col3 = st.columns(3, gap="small", width="stretch")
    with col1:
        st.metric(
            "⏱️ Driver Best Lap",
            f"{personal_best:.3f} s",
            delta=f"{gap_to_fastest:.3f} s vs session fastest"
        )
    with col2:
        st.metric("📊 Position in Session",
        f"{driver_position} / {num_of_drivers}")

    with col3:
        st.metric(
            "⚡ Fastest Lap in the Session",
            f"{session_fastest:.3f} s"
        )
    
    return {
        "personal_best": personal_best,
        "driver_position": driver_position,
        "session_fastest": session_fastest,
        "gap_to_fastest": gap_to_fastest
    }
