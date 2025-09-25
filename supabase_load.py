import os, pandas as pd
import json
from dotenv import load_dotenv
from supabase import create_client, Client

TABLE_NAME = "nba_news_data"

def get_client() -> Client:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    return create_client(url, key)

def ensure_list(x):
    if isinstance(x, list):
        return x
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return []
    try:
        # if it's a JSON-looking string like '["BOS","LAL"]'
        v = json.loads(x)
        return v if isinstance(v, list) else [str(v)]
    except Exception:
        return [str(x)]

def to_iso_utc_series(s: pd.Series) -> pd.Series:
    # parse to datetime, coerce errors to NaT, set to UTC, format ISO
    s = pd.to_datetime(s, utc=True, errors="coerce")
    return s.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    supabase = get_client()
    nba_news_df = pd.read_json("data/structured_data.json")
    
    for col in ("players", "teams"):
        if col in nba_news_df.columns:
            nba_news_df[col] = nba_news_df[col].apply(ensure_list)

    # 4) Convert datetime-like columns to ISO strings
    for col in ("published_at", "extracted_at", "updated_at"):
        if col in nba_news_df.columns:
            nba_news_df[col] = to_iso_utc_series(nba_news_df[col])
    nba_news_df["players"] = nba_news_df["players"].apply(
    lambda x: ", ".join(x) if isinstance(x, list) else (x or "")
)
    nba_news_df["teams"] = nba_news_df["teams"].apply(
    lambda x: ", ".join(x) if isinstance(x, list) else (x or "")
)
    rows = nba_news_df.to_dict(orient="records")
    res = supabase.table("nba_news_data").upsert(rows, on_conflict="id").execute()
    print("Inserted/Updated rows:", len(res.data))

if __name__ == "__main__":
    main()
