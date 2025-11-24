from supabase import create_client
import os

SUPABASE_URL = "https://nlpoglsfvykbkepfhast.supabase.co"
BUCKET = "telemetry"

supabase = create_client(SUPABASE_URL)
