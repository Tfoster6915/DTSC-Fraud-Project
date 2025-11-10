import os, ast, json, math
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE"]  # safer for server scripts than anon
supabase: Client = create_client(URL, KEY)

CSV_PATH = "pdf_summaries.csv"
TABLE = "ic3_alerts"
BATCH_SIZE = 500  # keep payloads small

def parse_keyword_counts(val):
    """
    Accepts:
      - already-JSON strings like '{"ransomware": 3}'
      - python repr strings like "{'ransomware': 3}"
      - dicts
    Returns a real Python dict.
    """
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        val = val.strip()
        # Try JSON first
        try:
            return json.loads(val)
        except Exception:
            pass
        # Fallback: Python literal with single quotes
        try:
            py = ast.literal_eval(val)
            if isinstance(py, dict):
                return py
        except Exception:
            pass
    return {}  # last resort

def coerce_row(row):
    return {
        "title": str(row["title"]).strip(),
        "date": str(row["date"])[:10],           # ensure YYYY-MM-DD
        "quarter": int(row["quarter"]),
        "keyword_counts": parse_keyword_counts(row["keyword_counts"]),
        "summary": str(row["summary"]).strip(),
    }

def main():
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    # Cast quarter to int once here
    if "quarter" in df.columns:
        df["quarter"] = df["quarter"].astype(int)
    rows = [coerce_row(rec) for rec in df.to_dict(orient="records")]

    # Upsert in batches on (title, date) uniqueness
    total = len(rows)
    for i in range(0, total, BATCH_SIZE):
        chunk = rows[i:i+BATCH_SIZE]
        resp = supabase.table(TABLE)\
            .upsert(chunk, on_conflict="title,date")\
            .execute()
        # You can print or log resp.count or resp.data as needed
        print(f"Upserted {i + len(chunk)}/{total}")

if __name__ == "__main__":
    main()
