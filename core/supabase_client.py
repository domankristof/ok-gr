from supabase import create_client
import os

SUPABASE_URL = "https://nlpoglsfvykbkepfhast.supabase.co"
SUPABASE_KEY = "SUPABASE_KEY"   # Not anon key
BUCKET = "telemetry"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
