import pandas as pd
import tempfile
from core.supabase_client import supabase, BUCKET

def load_parquet_from_supabase(filename: str) -> pd.DataFrame:
    """
    Downloads the Parquet file from Supabase Storage,
    stores it temporarily locally, and loads it as a Pandas df.
    """

    # 1. Download bytes from Supabase
    response = supabase.storage.from_(BUCKET).download(filename)

    if not response:
        raise ValueError(f"Could not download telemetry file: {filename}")

    # 2. Write to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp.write(response)
        tmp_path = tmp.name

    # 3. Load with pandas/pyarrow
    df = pd.read_parquet(tmp_path)

    return df
