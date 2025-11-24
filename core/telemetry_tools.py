import numpy as np
import pandas as pd
import math

def telemetry_tool (df: pd.DataFrame, car_number: int):
    """
    One funcion extracts all relevant stats from telemetry for a car
    in one go, so that the large telemetry data file is only read once.

    Args:
    telemetry_df: DataFrame containing telemetry data.
    car_number (int): Car number to filter data for.

    Returns:
    - Steerring trace data
    - Breaking smoothness score
    - Cornering smoothness score
    - Racing line consistency score (from GPS data)

    """

    # ----------------------------------------------------------------------------------
    # DATA CLEANING & PREP
    # ----------------------------------------------------------------------------------
    
    VEHICLE_COL = 'vehicle_number'
    df.columns = df.columns.str.strip()
    
    # Check if vehicle column exists
    if VEHICLE_COL not in df.columns:
        # Try to find a column that looks like it
        potential_cols = [c for c in df.columns if 'vehicle' in c.lower()]
        if potential_cols:
            VEHICLE_COL = potential_cols[0]
            raise Warning(f"Using column '{VEHICLE_COL}' as the vehicle identifier.")
        else:
            raise ValueError(f"Cannot find the required '{VEHICLE_COL}' column in the data.")
            return

    # Convert safely (invalid → NaT or NaN)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    #Convert vehicle number to numeric, fill NaNs with a known dummy value (-1), and force integer type.
    df[VEHICLE_COL] = pd.to_numeric(df[VEHICLE_COL], errors="coerce").fillna(-1).astype('int64')
    
    df["telemetry_value"] = pd.to_numeric(df["telemetry_value"], errors="coerce")
    
    # Drop invalid timestamps
    df = df.dropna(subset=["timestamp"])
    
    # ----------------------------------------------------------------------------------
    # VEHICLE FILTER
    # ----------------------------------------------------------------------------------
    user_df = df[df[VEHICLE_COL] == car_number].copy()

    if user_df.empty:
        raise Warning(f"No telemetry found for vehicle {car_number} after cleaning.")
        return 

    # ----------------------------------------------------------------------------------
    # Helper to extract telemetry signals
    # ----------------------------------------------------------------------------------
    def get_telemetry_value(telemetry_name):
        # Normalize comparison to handle case/whitespace errors
        normalized_data_names = user_df["telemetry_name"].astype(str).str.strip().str.lower()
        normalized_lookup = telemetry_name.strip().lower()
        
        # Filter rows
        mask = normalized_data_names == normalized_lookup
        
        # Select both columns and sort by time
        result_df = user_df.loc[mask, ["timestamp", "telemetry_value"]].copy() 
        return result_df.sort_values("timestamp")

    # ----------------------------------------------------------------------------------
    # EXTRACT STREAMS 
    # ----------------------------------------------------------------------------------
    speed_name = "Speed" 
    rpm_name = "nmot"
    throttle_name = "aps"
    front_brake_name = "pbrake_f"
    rear_brake_name = "pbrake_r"
    steering_angle_name = "steering_angle"
    
    GPS_LAT_NAME = "VBOX_Lat_Min" 
    GPS_LON_NAME = "VBOX_Long_Minutes"
   
    speed_data = get_telemetry_value(speed_name)
    engine_rpm_data = get_telemetry_value(rpm_name)
    throttle_pedal_data = get_telemetry_value(throttle_name)
    front_brake_pressure_data = get_telemetry_value(front_brake_name)
    rear_brake_pressure_data = get_telemetry_value(rear_brake_name)
    steering_angle_data = get_telemetry_value(steering_angle_name)
    gps_lat_data = get_telemetry_value(GPS_LAT_NAME)
    gps_lon_data = get_telemetry_value(GPS_LON_NAME)


    # ----------------------------------------------------------------------------------
    # Analysis
    # ----------------------------------------------------------------------------------


    # ----------------------------------------------------------------------------------
    # 1. STEERING ANALYSIS
    # ----------------------------------------------------------------------------------

    # --- 5a. Calculate Steering Rate (Rate of change of steering angle) ---
    # 1. Calculate time difference (dt) in seconds
    steering_angle_data['dt'] = steering_angle_data['timestamp'].diff().dt.total_seconds().fillna(0)
    
    # Remove large gaps that are unrealistic (e.g., > 1 second, signaling session breaks)
    MAX_DT_THRESHOLD = 0.5 
    
    # 2. Calculate steering angle difference (d_steer)
    steering_angle_data['d_steer'] = steering_angle_data['telemetry_value'].diff().fillna(0)
    
    # 3. Calculate Steering Rate (d_steer / dt) - units: degrees/second
    steering_angle_data['Steering_Rate'] = np.where(
        (steering_angle_data['dt'] > 0) & (steering_angle_data['dt'] <= MAX_DT_THRESHOLD),
        steering_angle_data['d_steer'] / steering_angle_data['dt'],
        np.nan # Mark rate invalid if gap is too large or dt is zero
    )
    
    steering_rate_df = steering_angle_data.dropna(subset=['Steering_Rate'])

    # --- 5b. Overall Steering Smoothness Score ---
    std_steering_rate = steering_rate_df['Steering_Rate'].abs().std()

    # The score is inversely related to the variability (Std Dev). We use an exponential decay:
    # Score = 100 * e^(-std / k), where k (e.g., 20) controls sensitivity.
    # Higher std_steering_rate (more erratic) gives a lower score.
    SENSITIVITY_FACTOR = 20.0
    
    if not math.isnan(std_steering_rate):
        steering_smoothness_score = 100 * math.exp(-std_steering_rate / SENSITIVITY_FACTOR)
        # Cap score at 100
        steering_smoothness_score = min(100.0, steering_smoothness_score) 
    else:
        steering_smoothness_score = None

    # --- 5c. Micro-Correction Analysis (Count of small, rapid reversals) ---
    # Look for rapid sign changes in the Steering Rate.
    # 1. Calculate the sign of the steering rate
    steering_rate_df['Rate_Sign'] = np.sign(steering_rate_df['Steering_Rate'].round(1)) # Round to ignore noise near zero
    
    # 2. Identify sign changes (where diff is not 0)
    steering_rate_df['Sign_Change'] = steering_rate_df['Rate_Sign'].diff().abs() > 0
    
    # 3. Define a threshold for micro-corrections (e.g., rate change is less than 5 deg/sec)
    MICRO_CORRECTION_THRESHOLD = 5.0 # degrees/second
    is_small_correction = steering_rate_df['Steering_Rate'].abs() < MICRO_CORRECTION_THRESHOLD
    
    # 4. Count small, rapid reversals
    micro_corrections_count = steering_rate_df[
        steering_rate_df['Sign_Change'] & is_small_correction
    ].shape[0]

    # Normalize the count by the total duration of the session in minutes
    total_time_seconds = steering_rate_df['dt'].sum()
    micro_corrections_per_minute = 0
    if total_time_seconds > 60:
         micro_corrections_per_minute = micro_corrections_count / (total_time_seconds / 60)
    
    # --- 5d. Usage Metrics ---
    max_abs_angle = steering_angle_data['telemetry_value'].abs().max()
    avg_abs_angle = steering_angle_data['telemetry_value'].abs().mean()

    #Conver Timestamp for safe JSON delivery
    # Convert timestamps to ISO strings
    steering_trace_records = steering_angle_data[
        ['timestamp', 'telemetry_value', 'Steering_Rate']
    ].copy()

    # Convert pandas.Timestamp → string
    steering_trace_records['timestamp'] = steering_trace_records['timestamp'].astype(str)


    # ----------------------------------------------------------------------------------
    # RETURN JSON SAFE RESULTS
    # ----------------------------------------------------------------------------------
    return {
        "car_number": car_number,
        "steering_smoothness_score": round(steering_smoothness_score, 2) if steering_smoothness_score is not None else None,
        "micro_corrections_per_minute": round(micro_corrections_per_minute, 2),
        "steering_usage": {
            "max_abs_angle": round(max_abs_angle, 2) if not math.isnan(max_abs_angle) else None,
            "avg_abs_angle": round(avg_abs_angle, 2) if not math.isnan(avg_abs_angle) else None,
            "std_steering_rate": round(std_steering_rate, 2) if not math.isnan(std_steering_rate) else None,
        },
    }
