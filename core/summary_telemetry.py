import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import plotly.graph_objects as go

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
    # G-G CIRCLE (REAL ACC DATA)
    # -------------------------

    ACC_LONG_NAME = "accx_can"   # Longitudinal G
    ACC_LAT_NAME  = "accy_can"   # Lateral G

    # Extract channels using existing helper
    acc_long = user_df[user_df["telemetry_name"].str.lower() == ACC_LONG_NAME.lower()].copy()
    acc_lat  = user_df[user_df["telemetry_name"].str.lower() == ACC_LAT_NAME.lower()].copy()

    # Rename for clarity
    acc_long = acc_long.rename(columns={"telemetry_value": "long_g"})
    acc_lat  = acc_lat.rename(columns={"telemetry_value": "lat_g"})

    # Merge on timestamp and lap
    gg_df = pd.merge(
        acc_long[["timestamp", "lap", "long_g"]],
        acc_lat[["timestamp", "lap", "lat_g"]],
        on=["timestamp", "lap"],
        how="inner"
    )

    # Choose mid-session laps
    laps = sorted(gg_df["lap"].dropna().unique().tolist())
    if len(laps) > 10:
        mid_laps = laps[5:10]
    else:
        mid_laps = laps[1:-1]

    gg_mid = gg_df[gg_df["lap"].isin(mid_laps)]


    def compute_traction_ellipse(hull_points):
        """
        Fit a least squares ellipse around the convex hull boundary.
        Returns smoothed ellipse coordinates.
        """
        x = hull_points[:,0]
        y = hull_points[:,1]

        # Design matrix for least squares ellipse fit
        D = np.vstack([x*x, x*y, y*y, x, y, np.ones_like(x)]).T
        S = np.dot(D.T, D)
        C = np.zeros([6,6])
        C[0,2] = C[2,0] = 2
        C[1,1] = -1

        # Solve generalized eigenvalue problem
        eigenvals, eigenvecs = np.linalg.eig(np.linalg.inv(S) @ C)
        coef = eigenvecs[:, np.argmax(eigenvals)]

        A, B, Cc, Dd, Ee, Ff = coef

        # Generate ellipse points
        t = np.linspace(0, 2*np.pi, 400)
        ellipse_x = np.zeros_like(t)
        ellipse_y = np.zeros_like(t)

        # Approx ellipse solution (numeric sampling)
        for i, angle in enumerate(t):
            xv = np.cos(angle)
            yv = np.sin(angle)
            denom = A*xv*xv + B*xv*yv + Cc*yv*yv
            r = np.sqrt(-Ff / denom) if denom != 0 else 0
            ellipse_x[i] = r * xv
            ellipse_y[i] = r * yv

        return ellipse_x, ellipse_y

    def gg_circle_with_envelope(gg_df):
        st.subheader("G-G Circle with Traction Envelope")

        # Use the renamed, cleaned columns
        x = gg_df["long_g"].values
        y = gg_df["lat_g"].values

        # -----------------------------------------
        # 1. Compute convex hull
        # -----------------------------------------
        pts = np.vstack([x, y]).T
        hull = ConvexHull(pts)
        hull_pts = pts[hull.vertices]

        # -----------------------------------------
        # 2. Smoothed traction ellipse
        # -----------------------------------------
        ellipse_x, ellipse_y = compute_traction_ellipse(hull_pts)

        # -----------------------------------------
        # 3. Reference traction circles
        # -----------------------------------------
        t = np.linspace(0, 2*np.pi, 400)

        circle_08_x = 0.8 * np.cos(t)
        circle_08_y = 0.8 * np.sin(t)

        circle_12_x = 1.2 * np.cos(t)
        circle_12_y = 1.2 * np.sin(t)

        # -----------------------------------------
        # 4. Plotly figure
        # -----------------------------------------
        fig = go.Figure()

        # Raw points
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="markers",
            marker=dict(size=3, opacity=0.28, color="white"),
            name="G-G Points"
        ))

        # Convex hull
        #fig.add_trace(go.Scatter(
            #x=hull_pts[:, 0], y=hull_pts[:, 1],
            #mode="lines",
            #line=dict(color="red", width=2),
            #name="Outer Envelope"
        #))

        # Smoothed ellipse
        fig.add_trace(go.Scatter(
            x=ellipse_x, y=ellipse_y,
            mode="lines",
            line=dict(color="#a856ff", width=3),
            name="Smoothed Traction Ellipse"
        ))

        # 0.8 G circle
        fig.add_trace(go.Scatter(
            x=circle_08_x, y=circle_08_y,
            mode="lines",
            line=dict(color="#ffc34b", width=2, dash="dot"),
            name="0.8 G Limit"
        ))

        # 1.2 G circle
        fig.add_trace(go.Scatter(
            x=circle_12_x, y=circle_12_y,
            mode="lines",
            line=dict(color="#ff4c4c", width=2, dash="dot"),
            name="1.2 G Limit"
        ))

        # Circle labels
        fig.add_trace(go.Scatter(x=[0.8], y=[0], mode="text", text=["0.8 G"], showlegend=False))
        fig.add_trace(go.Scatter(x=[1.2], y=[0], mode="text", text=["1.2 G"], showlegend=False))

        fig.update_layout(
            width=550,
            height=550,
            template="plotly_dark",
            xaxis_title="Longitudinal G (Accel / Brake)",
            yaxis_title="Lateral G",
            yaxis_scaleanchor="x",

            # Transparent backgrounds
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            # Legend bottom-right overlay
            legend=dict(
                x=0.99,
                y=0.01,
                xanchor="right",
                yanchor="bottom",
                bgcolor="rgba(0,0,0,0.35)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1,
                font=dict(size=10)
            ),
        )

        st.plotly_chart(fig)

    # -------------------------
    # Call GG plot
    # -------------------------
    if not gg_mid.empty:
        gg_circle_with_envelope(gg_mid)
    else:
        st.warning("Not enough G-force data to compute traction map.")

    #-------------------------------------------------------------------
    #-------------------------------------------------------------------
    def speed_vs_distance_plot(user_df, laps_used):
        SPEED_SIGNAL = "Speed"  # change if your column is different

        # Extract speed rows
        speed_df = user_df[user_df["telemetry_name"].str.lower() == SPEED_SIGNAL.lower()].copy()
        speed_df = speed_df[["timestamp", "lap", "telemetry_value"]].rename(columns={
            "telemetry_value": "speed"
        })

        if speed_df.empty:
            st.warning("No speed data available for this vehicle.")
            return
        
        # Filter laps
        speed_df = speed_df[speed_df["lap"].isin(laps_used)]

        def compute_distance(df_lap):
            df_lap = df_lap.sort_values("timestamp").copy()
            df_lap["dt"] = df_lap["timestamp"].diff().dt.total_seconds().fillna(0)
            df_lap["distance"] = (df_lap["speed"] * df_lap["dt"]).cumsum()
            return df_lap

        dist_laps = []
        for lap in laps_used:
            lap_df = speed_df[speed_df["lap"] == lap]
            if not lap_df.empty:
                dist_laps.append(compute_distance(lap_df))

        if len(dist_laps) == 0:
            st.warning("No usable laps to compute speed–distance plot.")
            return

        # Normalize distance
        max_dist = min(df["distance"].max() for df in dist_laps)
        dist_grid = np.linspace(0, max_dist, 500)

        interp_speeds = []
        for lap_df in dist_laps:
            interp = np.interp(
                dist_grid,
                lap_df["distance"].values,
                lap_df["speed"].values
            )
            interp_speeds.append(interp)

        mean_speed = np.mean(np.vstack(interp_speeds), axis=0)

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dist_grid,
            y=mean_speed,
            mode="lines",
            line=dict(color="#23F0C7", width=3),
            name="Avg Speed"
        ))

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Distance (m approx.)",
            yaxis_title="Speed",
            width=650,
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.subheader("Speed vs Distance (Average of Mid-Session Laps)")
        st.plotly_chart(fig, use_container_width=True)
    # -------------------------
    # Call SPEED vs DISTANCE PLOT
    # -------------------------
    speed_vs_distance_plot(user_df, mid_laps)



def speed_distance_plot(telemetry_df: pd.DataFrame, vehicle_number: int):
    """
    Build a speed–distance plot:
      • Detects the fastest lap automatically from telemetry
      • Computes speed–distance traces for individual laps
      • Averages mid-session laps
      • Overlays FASTEST LAP vs AVERAGE MID-LAPS
    """

    # Clean columns
    df = telemetry_df.copy()
    df.columns = df.columns.str.strip()

    # Ensure correct formats
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["telemetry_value"] = pd.to_numeric(df["telemetry_value"], errors="coerce")
    df["vehicle_number"] = pd.to_numeric(df["vehicle_number"], errors="coerce")

    df = df.dropna(subset=["timestamp"])
    df = df[df["vehicle_number"] == vehicle_number]

    if df.empty:
        st.warning(f"No telemetry found for vehicle {vehicle_number}.")
        return

    # -----------------------------
    # Extract speed channel ONLY
    # -----------------------------
    SPEED_SIGNAL = "speed"

    speed_df = df[df["telemetry_name"].str.lower() == SPEED_SIGNAL.lower()].copy()

    if speed_df.empty:
        st.warning("No speed data found in telemetry.")
        return

    # Remove any NaNs, sort by time
    speed_df = speed_df.dropna(subset=["lap", "timestamp", "telemetry_value"])
    speed_df = speed_df.rename(columns={"telemetry_value": "speed"})
    speed_df = speed_df.sort_values("timestamp")

    laps = sorted(speed_df["lap"].unique())
    if len(laps) < 3:
        st.warning("Not enough laps for averaging.")
        return

    # -----------------------------
    # Compute speed-distance per lap
    # -----------------------------
    def compute_distance(df_lap):
        df_lap = df_lap.sort_values("timestamp").copy()
        df_lap["dt"] = df_lap["timestamp"].diff().dt.total_seconds().fillna(0)
        df_lap["distance"] = (df_lap["speed"] * df_lap["dt"]).cumsum()
        return df_lap

    per_lap_traces = {}
    lap_total_speed = {}

    for lap in laps:
        lap_df = speed_df[speed_df["lap"] == lap]
        if lap_df.empty:
            continue
        lap_dist = compute_distance(lap_df)
        per_lap_traces[lap] = lap_dist
        lap_total_speed[lap] = lap_dist["speed"].mean()   # fastest lap = highest avg speed

    # -----------------------------
    # Determine FASTEST LAP
    # -----------------------------
    fastest_lap = max(lap_total_speed, key=lap_total_speed.get)
    fastest_trace = per_lap_traces[fastest_lap]

    # -----------------------------
    # Determine MID SESSION LAPS
    # -----------------------------
    if len(laps) > 10:
        mid_laps = laps[5:10]
    else:
        mid_laps = laps[1:-1]  # skip out-lap & in-lap

    mid_lap_traces = [per_lap_traces[l] for l in mid_laps if l in per_lap_traces]

    if not mid_lap_traces:
        st.warning("Mid-session laps not available.")
        return

    # -----------------------------
    # Normalize distance & average mid-laps
    # -----------------------------
    min_end_dist = min(df_lap["distance"].max() for df_lap in mid_lap_traces)
    dist_grid = np.linspace(0, min_end_dist, 600)

    interp_speeds = []
    for lap_df in mid_lap_traces:
        interp = np.interp(dist_grid, lap_df["distance"].values, lap_df["speed"].values)
        interp_speeds.append(interp)

    mean_speed = np.mean(np.vstack(interp_speeds), axis=0)

    # -----------------------------
    # Build Plotly Figure
    # -----------------------------
    fig = go.Figure()

    # Average lap
    fig.add_trace(go.Scatter(
        x=dist_grid,
        y=mean_speed,
        mode="lines",
        line=dict(color="#23F0C7", width=3),
        name="Avg Mid-Session Lap"
    ))

    # Fastest lap interpolated
    fastest_interp = np.interp(
        dist_grid,
        fastest_trace["distance"].values,
        fastest_trace["speed"].values
    )

    fig.add_trace(go.Scatter(
        x=dist_grid,
        y=fastest_interp,
        mode="lines",
        line=dict(color="#FF4F4F", width=2),
        name=f"Fastest Lap (Lap {fastest_lap})"
    ))

    # Layout styling
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Distance (m approx.)",
        yaxis_title="Speed (km/h)",
        width=700,
        height=450,
        legend=dict(
            x=0.02, y=0.02,
            xanchor="left",
            yanchor="bottom",
            bgcolor="rgba(0,0,0,0.3)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.subheader("Speed vs Distance")
    st.caption(f"Vehicle {vehicle_number} — Fastest Lap vs Mid-Session Average")
    st.plotly_chart(fig, use_container_width=True)





def gg_plot(df: pd.DataFrame, vehicle_number: int):
    """
    Provides friction circle plot.
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
    # G-G CIRCLE (REAL ACC DATA)
    # -------------------------

    ACC_LONG_NAME = "accx_can"   # Longitudinal G
    ACC_LAT_NAME  = "accy_can"   # Lateral G

    # Extract channels using existing helper
    acc_long = user_df[user_df["telemetry_name"].str.lower() == ACC_LONG_NAME.lower()].copy()
    acc_lat  = user_df[user_df["telemetry_name"].str.lower() == ACC_LAT_NAME.lower()].copy()

    # Rename for clarity
    acc_long = acc_long.rename(columns={"telemetry_value": "long_g"})
    acc_lat  = acc_lat.rename(columns={"telemetry_value": "lat_g"})

    # Merge on timestamp and lap
    gg_df = pd.merge(
        acc_long[["timestamp", "lap", "long_g"]],
        acc_lat[["timestamp", "lap", "lat_g"]],
        on=["timestamp", "lap"],
        how="inner"
    )

    # Choose mid-session laps
    laps = sorted(gg_df["lap"].dropna().unique().tolist())
    if len(laps) > 10:
        mid_laps = laps[5:10]
    else:
        mid_laps = laps[1:-1]

    gg_mid = gg_df[gg_df["lap"].isin(mid_laps)]


    def compute_traction_ellipse(hull_points):
        """
        Fit a least squares ellipse around the convex hull boundary.
        Returns smoothed ellipse coordinates.
        """
        x = hull_points[:,0]
        y = hull_points[:,1]

        # Design matrix for least squares ellipse fit
        D = np.vstack([x*x, x*y, y*y, x, y, np.ones_like(x)]).T
        S = np.dot(D.T, D)
        C = np.zeros([6,6])
        C[0,2] = C[2,0] = 2
        C[1,1] = -1

        # Solve generalized eigenvalue problem
        eigenvals, eigenvecs = np.linalg.eig(np.linalg.inv(S) @ C)
        coef = eigenvecs[:, np.argmax(eigenvals)]

        A, B, Cc, Dd, Ee, Ff = coef

        # Generate ellipse points
        t = np.linspace(0, 2*np.pi, 400)
        ellipse_x = np.zeros_like(t)
        ellipse_y = np.zeros_like(t)

        # Approx ellipse solution (numeric sampling)
        for i, angle in enumerate(t):
            xv = np.cos(angle)
            yv = np.sin(angle)
            denom = A*xv*xv + B*xv*yv + Cc*yv*yv
            r = np.sqrt(-Ff / denom) if denom != 0 else 0
            ellipse_x[i] = r * xv
            ellipse_y[i] = r * yv

        return ellipse_x, ellipse_y

    def gg_circle_with_envelope(gg_df):
        st.subheader("'GG' Plot & Traction Margins")
        st.write("Traction envolope usage over mid-race pace laps")

        # Use the renamed, cleaned columns
        x = gg_df["long_g"].values
        y = gg_df["lat_g"].values

        # -----------------------------------------
        # 1. Compute convex hull
        # -----------------------------------------
        pts = np.vstack([x, y]).T
        hull = ConvexHull(pts)
        hull_pts = pts[hull.vertices]

        # -----------------------------------------
        # 2. Smoothed traction ellipse
        # -----------------------------------------
        ellipse_x, ellipse_y = compute_traction_ellipse(hull_pts)

        # -----------------------------------------
        # 3. Reference traction circles
        # -----------------------------------------
        t = np.linspace(0, 2*np.pi, 400)

        circle_08_x = 0.8 * np.cos(t)
        circle_08_y = 0.8 * np.sin(t)

        circle_12_x = 1.2 * np.cos(t)
        circle_12_y = 1.2 * np.sin(t)

        # -----------------------------------------
        # 4. Plotly figure
        # -----------------------------------------
        fig = go.Figure()

        # Raw points
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="markers",
            marker=dict(size=3, opacity=0.28, color="white"),
            name="G-G Points"
        ))

        # Convex hull
        #fig.add_trace(go.Scatter(
            #x=hull_pts[:, 0], y=hull_pts[:, 1],
            #mode="lines",
            #line=dict(color="red", width=2),
            #name="Outer Envelope"
        #))

        # Smoothed ellipse
        fig.add_trace(go.Scatter(
            x=ellipse_x, y=ellipse_y,
            mode="lines",
            line=dict(color="#a856ff", width=3),
            name="Smoothed Traction Ellipse"
        ))

        # 0.8 G circle
        fig.add_trace(go.Scatter(
            x=circle_08_x, y=circle_08_y,
            mode="lines",
            line=dict(color="#ffc34b", width=2, dash="dot"),
            name="0.8 G Limit"
        ))

        # 1.2 G circle
        fig.add_trace(go.Scatter(
            x=circle_12_x, y=circle_12_y,
            mode="lines",
            line=dict(color="#ff4c4c", width=2, dash="dot"),
            name="1.2 G Limit"
        ))

        # Circle labels
        fig.add_trace(go.Scatter(x=[0.8], y=[0], mode="text", text=["0.8 G"], showlegend=False))
        fig.add_trace(go.Scatter(x=[1.2], y=[0], mode="text", text=["1.2 G"], showlegend=False))

        fig.update_layout(
            width=550,
            height=550,
            template="plotly_dark",
            xaxis_title="Longitudinal Acceleration [G]",
            yaxis_title="Lateral Acceleration [G]",
            yaxis_scaleanchor="x",

            # Transparent backgrounds
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            # Legend bottom-right overlay
            legend=dict(
                x=0.99,
                y=0.01,
                xanchor="right",
                yanchor="bottom",
                bgcolor="rgba(0,0,0,0.35)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1,
                font=dict(size=10)
            ),
        )

        st.plotly_chart(fig)

    # -------------------------
    # Call GG plot
    # -------------------------
    if not gg_mid.empty:
        gg_circle_with_envelope(gg_mid)
    else:
        st.warning("Not enough G-force data to compute traction map.")