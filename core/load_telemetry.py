import pandas as pd
import tempfile
from core.supabase_client import supabase, BUCKET
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

def load_parquet_from_supabase(filename: str) -> pd.DataFrame:

    # 1. Download bytes from Supabase
    response = supabase.storage.from_(BUCKET).download(filename)

    if not response:
        raise ValueError(f"Could not download telemetry file: {filename}")

    # Ensure we have raw bytes (Supabase sometimes returns a stream)
    data = bytes(response)

    # 2. Read parquet from memory
    table = pq.read_table(pa.BufferReader(data))

    # ---------------------------------------------
    # Detect SINGLE-COLUMN "fake parquet" structure
    # ---------------------------------------------
    if table.num_columns == 1:
        col_name = table.column_names[0]       # long header string
        header = [h.strip() for h in col_name.split(",")]

        # Split rows FAST using pyarrow compute
        parts = pc.split_pattern(
            table[col_name],
            pattern=",",
            max_splits=len(header) - 1
        )

        # Rebuild table with correct columns
        table = pa.table({header[i]: parts[i] for i in range(len(header))})

    # Convert to pandas
    df = table.to_pandas(split_blocks=True, self_destruct=True)

    # Strip whitespace from all string columns
    df.columns = df.columns.str.strip()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].str.strip()

    return df
