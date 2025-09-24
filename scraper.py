import openai 
from openai import OpenAI
import os
from bs4 import BeautifulSoup
import requests

#Web Scraping
url = "https://www.nba.com/news"
headers = {"User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15'}
page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.content, 'html.parser')
all_text = soup.get_text()
print(all_text)
with open("data/raw_data.txt", "w", encoding="utf-8") as f:
    f.write(all_text)



# endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
# deployment_name = "gpt-4o"
# client = OpenAI(
#     base_url=endpoint,
#     api_key=api_key
# )

# response = client.chat.completions.create(
#     model=deployment_name,
#     messages=[
#         {
#             "role": "developer",
#             "content": "Talk like a pirate."
#         },
#         {
#             "role": "user",
#             "content": "Are semicolons optional in JavaScript?"
#         }
#     ]
# )

# print(response.choices[0].message.content)
