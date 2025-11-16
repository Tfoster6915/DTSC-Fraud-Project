from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("Client created. Now trying a simple SELECT...")

try:
    response = supabase.table("fraud_keywords").select("*").limit(1).execute()
    print("Request successful. Rows returned:", len(response.data))
except Exception as e:
    print("Request FAILED with error:")
    print(repr(e))
