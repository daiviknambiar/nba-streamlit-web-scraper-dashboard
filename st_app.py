# st_app.py
import os
import json
import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

st.set_page_config(page_title="NBA News Browser", page_icon="🏀", layout="wide")
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME   = os.getenv("TABLE_NAME", "nba_news_data")  

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Missing SUPABASE_URL or SUPABASE_KEY env vars.")
    st.stop()

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=120)
def fetch_rows(table: str) -> pd.DataFrame:
    data = (
        sb.table(table)
          .select("*")
          .order("extracted_at", desc=True)   
          .execute()
          .data
    )
    return pd.DataFrame(data or [])

def to_list(x):
    if isinstance(x, list):
        return x
    if x is None:
        return []
    if isinstance(x, str):
        if x.strip().startswith("[") and x.strip().endswith("]"):
            try:
                v = json.loads(x)
                return v if isinstance(v, list) else [str(v)]
            except Exception:
                pass
        parts = [p.strip() for p in x.split(",") if p.strip()]
        return parts
    return [str(x)]

def join_list(x):
    if isinstance(x, list):
        x = [str(i) for i in x if str(i).strip()]
        return ", ".join(x) if x else "—"
    return str(x) if str(x).strip() else "—"

def fmt_date(x):
    if not x:
        return "—"
    dt = pd.to_datetime(x, utc=True, errors="coerce")
    if pd.isna(dt):
        return str(x)
    return dt.tz_convert("UTC").strftime("%b %d, %Y")

def tag_html(label, value):
    return f"""
    <div class="row">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
    </div>
    """


st.markdown("""
<style>
.card {
  background: #0f1320;
  border: 1px solid #2a3042;
  border-radius: 16px;
  padding: 20px 22px;
  margin-bottom: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.25);
  transition: all 0.2s ease-in-out;
}
.card:hover {
  background: #18203a;
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0,0,0,0.35);
}
.title {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: .2px;
  margin: 0 0 10px 0;
  color: #e9edf6;
}
.info-box {
  background: #12192b;
  border: 1px solid #2b3350;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.row {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 10px;
  padding: 6px 0;
  align-items: start;
  border-bottom: 1px dashed #2a3042;
}
.row:last-child { border-bottom: 0; }
.label {
  color: #9fb0d1;
  font-weight: 700;
  font-size: 0.9rem;
}
.value {
  color: #dfe6f3;
  font-size: 0.95rem;
}
.summary-title {
  margin-top: 6px;
  color: #9fb0d1;
  font-weight: 700;
  font-size: 0.95rem;
}
.summary {
  color: #e1e7f7;
  line-height: 1.55;
  margin-top: 4px;
}
.link a {
  color: #87b7ff !important;
  text-decoration: none;
  font-weight: 600;
}
.link a:hover { text-decoration: underline; }
.sidebar-label {
  font-weight: 600;
  color: #cfd6e3;
}
</style>
""", unsafe_allow_html=True)


df = fetch_rows(TABLE_NAME)
if df.empty:
    st.info("No news found.")
    st.stop()

for col in ("players", "teams"):
    if col in df.columns:
        df[col] = df[col].apply(to_list)

if "extracted_at" in df.columns:
    df["_extracted_fmt"] = df["extracted_at"].apply(fmt_date)
else:
    df["_extracted_fmt"] = "—"

# --------------------------
# Sidebar filters
# --------------------------
st.sidebar.header("🔎 Filters")
topics = sorted([t for t in df.get("topic", pd.Series()).dropna().unique().tolist() if t])
teams_all = sorted({t for arr in df.get("teams", pd.Series()).dropna().tolist() for t in to_list(arr)})

topic_pick = st.sidebar.multiselect("Topic", topics, default=[])
team_pick  = st.sidebar.multiselect("Team", teams_all, default=[])
search_q   = st.sidebar.text_input("Search (title / summary / players / teams)")

f = df.copy()
if topic_pick:
    f = f[f["topic"].isin(topic_pick)]
if team_pick:
    f = f[f["teams"].apply(lambda arr: any(t in arr for t in team_pick))]
if search_q:
    q = search_q.lower()
    def hits(row):
        hay = " ".join([
            str(row.get("title","")),
            str(row.get("summary","")),
            " ".join(row.get("players", [])),
            " ".join(row.get("teams", []))
        ]).lower()
        return q in hay
    f = f[f.apply(hits, axis=1)]

if "extracted_at" in f.columns:
    f = f.sort_values(by="extracted_at", ascending=False)

st.title("🏀 NBA News Web Scraper App")
st.subheader("By Daivik Nambiar - DTSC 3601")
st.text("This tool web scrapes the most up-to-date news on the NBA via nba.com/news and utilizes data conversion from raw -> JSON -> dataframe -> Open AI LLM to display an interactive news browser")
st.caption(f"Showing {len(f)} of {len(df)} articles")


for _, row in f.iterrows():
    title   = (row.get("title") or "Untitled")
    topic   = (row.get("topic") or "—")
    players = join_list(row.get("players", []))
    teams   = join_list(row.get("teams", []))
    extracted = row.get("_extracted_fmt", "—")
    summary = (row.get("summary") or "—")
    url     = row.get("source_url") or ""

    info_html = "".join([
        tag_html("Topic", topic.title()),
        tag_html("Players", players),
        tag_html("Teams", teams),
        tag_html("Extracted", extracted),
    ])

    st.markdown(f"""
    <div class="card">
      <div class="title">{title}</div>
      <div class="info-box">{info_html}</div>
      <div class="summary-title">AI Generated Summary</div>
      <div class="summary">{summary}</div>
      <div class="link" style="margin-top:10px;">
        {"<a href='{0}' target='_blank'>Read the full article →</a>".format(url) if url else ""}
      </div>
    </div>
    """, unsafe_allow_html=True)
