import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import io
from core.supabase_client import supabase, BUCKET
import streamlit as st

# Define a list of fallback encodings to try
ENCODING_FALLBACK = ['utf-8', 'latin-1', 'iso-8859-1']

def load_parquet_from_supabase(filename: str) -> pd.DataFrame:
    """
    Downloads a Parquet file from Supabase Storage.
    It attempts Parquet load first, and falls back to a multi-encoding CSV parser.
    """
    try:
        response = supabase.storage.from_(BUCKET).download(filename)
    except Exception as e:
        raise ValueError(f"Could not download telemetry file: {filename}. Error: {e}")

    if isinstance(response, (bytes, bytearray)):
        data = bytes(response)
    else:
        data = response.read()

    # Attempt to load as Parquet first
    try:
        table = pq.read_table(pa.BufferReader(data))
        
        # If loaded successfully and has > 1 column, return it
        if table.num_columns > 1 and table.num_rows > 1:
            df = table.to_pandas(split_blocks=True, self_destruct=True)
            df.columns = df.columns.str.strip()
            return df

    except pa.ArrowIOError:
        # If Parquet load fails, proceed to CSV fallback
        st.warning("PyArrow failed to read data as standard Parquet (ArrowIOError).")
        pass
    
    st.warning("Data is in single-column or incorrect Parquet format. Attempting multi-encoding CSV parse.")
    st.error("The Parquet file is corrupted or incorrectly structured. You MUST re-run 'telemetry_converter.py' and re-upload the file named 'R1_telemetry_final.parquet'.")
    return _handle_fake_parquet(data)


def _handle_fake_parquet(data: bytes) -> pd.DataFrame:
    """
    Reads the raw bytes as a CSV stream, attempting multiple common encodings.
    """
    csv_data = None
    
    # 1. Try multiple encodings
    for encoding in ENCODING_FALLBACK:
        try:
            csv_data = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue # Try the next encoding

    if csv_data is None:
        st.error(f"Failed to decode file using any of the fallback encodings: {', '.join(ENCODING_FALLBACK)}")
        return pd.DataFrame()

    # 2. Parse the decoded text as a CSV
    try:
        data_buffer = io.StringIO(csv_data)
        df = pd.read_csv(data_buffer, sep=';', header=0, on_bad_lines='skip') 
        
    except Exception as e:
        st.error(f"Failed to parse decoded text as CSV. Error: {e}")
        return pd.DataFrame()
    
    # 3. Final cleanup
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    return df


def load_parquet_from_supabase_filtered(fname: str, columns: list):
    """
    Downloads a Parquet file from Supabase and loads ONLY the columns requested.
    """
    data = supabase.storage.from_(BUCKET).download(fname)
    table = pq.read_table(io.BytesIO(data), columns=columns)
    return table.to_pandas()