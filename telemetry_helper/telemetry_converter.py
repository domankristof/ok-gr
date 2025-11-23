# script to convert large CSV telemetry data to Parquet format to upload to Supabase

import pandas as pd
import subprocess

# --------------------------
# PATHS
# --------------------------
csv_path = "/Users/kristof/Desktop/virginia-international-raceway/VIR/Race 1/R1_vir_telemetry_data.csv"
parquet_path = "/Users/kristof/Desktop/virginia-international-raceway/VIR/Race 1/R1_vir_telemetry_data.parquet"

# --------------------------
# READ CSV IN CHUNKS
# --------------------------
print("Reading CSV in chunks...")

chunks = []
for chunk in pd.read_csv(
    csv_path,
    sep=";",
    engine="python",
    chunksize=200000,
    on_bad_lines="skip"
):
    chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)

# --------------------------
# SAVE AS PARQUET
# --------------------------
df.to_parquet(parquet_path, index=False)
print("Converted CSV → Parquet successfully")
download_link = f"file://{parquet_path}"
print(f"Parquet file available at: {download_link}")
subprocess.run(["open", parquet_path])

