from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

def load_reports_from_text():
    file_path = "fraud_reports.txt"

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    rows = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            year = 2023  # change later if needed
            title = line[:60] + "..." if len(line) > 60 else line

            rows.append({
                "year": year,
                "title": title,
                "report_text": line,
            })

    if not rows:
        print("No non-empty lines in fraud_reports.txt")
        return

    response = supabase.table("fraud_reports").insert(rows).execute()
    print(f"Inserted {len(rows)} rows into fraud_reports.")

if __name__ == "__main__":
    load_reports_from_text()
