import openai 
from openai import OpenAI
from dotenv import load_dotenv
import os, json, datetime as dt
from bs4 import BeautifulSoup
import requests
from pathlib import Path

#Web Scraping
url = "https://www.nba.com/news"
headers = {"User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15'}
page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.content, 'html.parser')
all_text = soup.get_text()
Path("data").mkdir(parents=True, exist_ok=True) 
with open("data/raw_data.txt", "w", encoding="utf-8") as f:
    f.write(all_text)


endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
api_key = "supersecretkey"
deployment_name = "gpt-4o"
client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

schema = {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": "string"},
      "title": {"type": "string"},
      "source_url": {"type": ["string","null"]},
      "topic": {"type": "string", "description": "recap | injury | trade | award | analysis | rumor | signing | staff | preseason preview | feature | other"},
      "players": {"type": "array", "items": {"type": "string"}},
      "teams": {"type": "array", "items": {"type": "string"}, "description": "NBA team names"},
      "summary": {"type": "string", "description": "<= 2 sentences"},
      "extracted_at": {"type": "string"}
    },
    "required": ["id","title","summary","topic","players","teams","extracted_at"]
  }
}

captured_at = dt.datetime.now(dt.timezone.utc).isoformat()

rules = (
  "You are a strict JSON API. "
  "Return ONLY valid JSON with no prose or code fences. "
  "Output MUST be a top-level JSON array following the provided schema. "
  "Use ONLY information present in HOMEPAGE_BLOB. "
  "Do NOT invent titles, players, teams, dates, or URLs. "
  "If a field is unknown, set it to N/A (or [] for arrays). "
  "If a topic is not easily found, set the topic as 'feature'"
  "Teams must be their full name with the city + team name (e.g. Boston Celtics, Cleveland Cavaliers, etc.). "
  "Summaries must be at most 2 sentences. "
  f"For each item, set extracted_at to '{captured_at}'. "
  "For id, use a lowercase-kebab-case slug of the title (append '-YYYY-MM-DD' if a date appears)."
)

user_instructions = f"""From this NBA news HOMEPAGE blob, extract the TOP 12 distinct stories/headlines.

For each story, include:
- topic (recap, injury, trade, award, analysis, rumor, signing, other)
- players (proper names that appear in the blob)
- teams (NBA abbreviations ONLY if the matching team clearly appears; else [])
- <=2 sentence summary strictly grounded in the blob
- published_at and source_url ONLY if they appear in the blob

Schema:
{json.dumps(schema, ensure_ascii=False)}


Return ONLY a JSON array.

HOMEPAGE_BLOB:
{all_text[:120000]}"""

response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {"role": "developer", "content": rules},
        {"role": "user", "content": user_instructions}
    ],
    temperature=0.2
)

raw = response.choices[0].message.content.strip()
print(raw)