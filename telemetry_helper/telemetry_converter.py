# script to convert large CSV telemetry data to Parquet format to upload to Supabase

import pandas as pd
import subprocess
import os

# --------------------------
# PATHS
# --------------------------
csv_path = "/Users/kristof/Desktop/virginia-international-raceway/VIR/Race_1/R1_vir_telemetry_data.csv"
safe_output_dir = os.path.dirname(os.path.abspath(__file__))
parquet_filename = "r1-vir-telemetry.parquet" 
parquet_path = os.path.join(safe_output_dir, parquet_filename)

# --------------------------
# READ CSV IN CHUNKS
# --------------------------
print("Reading CSV in chunks...")

chunks = []
try:
    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        engine="python",
        chunksize=200000,
        on_bad_lines="skip",
        encoding="latin-1" 
    ):
        chunks.append(chunk)

    df = pd.concat(chunks, ignore_index=True)

    # --------------------------
    # SAVE AS PROPER MULTI-COLUMN PARQUET
    # --------------------------
    
    # 🚀 CRITICAL FIX: Explicitly set the engine to ensure proper schema writing.
    # Requires 'pip install fastparquet'
    df.to_parquet(parquet_path, index=False, engine='fastparquet') 
    
    print(f"Converted CSV → Parquet successfully at: {parquet_path}")

    print("\n✅ SUCCESS: NEW FILE CREATED.")
    print("This file should now load with multiple columns.")

except Exception as e:
    print(f"An error occurred during CSV read or Parquet save: {e}")