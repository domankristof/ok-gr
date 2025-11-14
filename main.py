import io
import pandas as pd
import streamlit as st
from core.assign import assign_roles_by_name

# Welcome
st.badge("New", color="red")
st.title("Hi, I'm GR")
st.divider()

# Upload
st.subheader("Please Upload Your Data to Begin")
files = st.file_uploader(
    "Select multiple CSV files",
    type=["csv"],
    accept_multiple_files=True
)

dfs = {}  # will hold DataFrames by role

if files:
    # (filename, bytes) pairs
    bundle = [(f.name, f.getvalue()) for f in files]

    # auto-assign by filename only (case-insensitive)
    picks = assign_roles_by_name(bundle)

    st.subheader("Detected files (by filename only)")
    # IMPORTANT: keys should match what assign_roles_by_name() returns, e.g. "laps" not "lap times"
    for role in ["telemetry", "laps", "weather", "results", "sectors"]:
        st.write(f"**{role.capitalize()}** → {picks.get(role, {}).get('filename', '_not detected_')}")

    # Build DataFrames only for roles we actually matched
    for role, info in picks.items():
        idx = info["index"]
        dfs[role] = pd.read_csv(io.BytesIO(bundle[idx][1]))

    # Optional preview
    if "telemetry" in dfs:
        st.write("Telemetry preview:")
        st.dataframe(dfs["telemetry"].head())