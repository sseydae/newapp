import json, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

URL = "https://bais.bilkent.edu.tr/menu/"
html = requests.get(URL, timeout=30, headers={"User-Agent": "Bilkenters-menu-bot"}).text
soup = BeautifulSoup(html, "html.parser")

days = []
out = {"updated": datetime.now(timezone.utc).isoformat(), "days": days}
with open("data/menu.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
