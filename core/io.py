#Input/Output Functions -- CSV ingest/validation (and upload to storadge if needed)
import pandas as pd
import numpy  as np
import io
import re


#Check CSV --> take the race data csv as input and loads it correctly
"""
Robust CSV loader with:
- delimiter inference
- encoding fallback
- BOM stripping
- numeric 'NA' handling
Returns raw DataFrame (no validation or renaming).
`file_obj` can be a Streamlit UploadedFile, file-like object, or bytes.
 """
def read_csv (file_obj: Any) -> pd.DataFrame:
    raw_bytes = file_obj.read()

    # Try UTF-8 with automatic delimiter detection
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            buf = io.StringIO(raw_bytes.decode(encoding, errors="strict"))
            # sep=None + engine="python" triggers delimiter sniffing
            df = pd.read_csv(
                buf,
                sep=None,
                engine="python",
                na_values=["", "NA", "NaN", "nan", "null", "NULL", "-"],
                keep_default_na=True,
            )
            break
        except Exception:
            df = None
    if df is None or df.empty:
        raise ValueError("Could not read CSV: unsupported encoding/delimiter or empty file.")

    # Drop completely empty columns
    df = df.dropna(axis=1, how="all")
    
    # Trim whitespace from headers
    df.columns = [c.strip() for c in df.columns]
    return df