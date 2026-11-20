#!/usr/bin/env python3
"""bais.bilkent.edu.tr/menu sayfasından menüyü çekip menu.json üretir.

menu.json formatı (uygulamadaki MN değişkeniyle birebir uyumlu):
{"days": {"2026-11-04": [kcalÖğle, "yemek|yemek|...", kcalAkşam, "yemek|...", "seçmeli|..."]},
 "updated": "2026-11-04T06:00:00"}
Vegan yemeklerin sonuna " · vegan" eklenir.
"""
import json, re, sys, datetime as dt
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL = "https://bais.bilkent.edu.tr/menu/"
OUT = Path(__file__).resolve().parent.parent / "menu.json"
KEEP_DAYS = 14  # eski günleri bu kadar gün tut

AYLAR = {"ocak":1,"şubat":2,"mart":3,"nisan":4,"mayıs":5,"haziran":6,"temmuz":7,
         "ağustos":8,"eylül":9,"ekim":10,"kasım":11,"aralık":12}

def fetch():
    r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 (menu-sync)"})
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text

def parse_date(line):
    """'04.11.2026' veya '4 Kasım 2026' -> '2026-11-04'"""
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", line)
    if m:
        d, mo, y = map(int, m.groups()); return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})", line)
    if m and m.group(2).lower() in AYLAR:
        return f"{int(m.group(3)):04d}-{AYLAR[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return None

def parse_menu(html):
    """!!! Sitenin gerçek HTML yapısına göre uyarlanması gereken tek bölüm !!!
    Şu an sayfa metnini satır satır tarayıp tarih / Öğle / Akşam / Seçmeli / kcal
    başlıklarına göre gruplar."""
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "footer"]): t.decompose()
    lines = [re.sub(r"\s+", " ", l).strip() for l in soup.get_text("\n").split("\n")]
    lines = [l for l in lines if l]

    days, cur, sec = {}, None, None
    def new_day(k): days[k] = {"o": [0, []], "a": [0, []], "s": []}

    for l in lines:
        d = parse_date(l)
        if d and len(l) < 40:
            cur, sec = d, None; new_day(d); continue
        if cur is None: continue
        low = l.lower()
        if low.startswith("öğle"):  sec = "o"
        elif low.startswith("akşam"): sec = "a"
        elif low.startswith("seçmeli") or "alternatif" in low: sec = "s"
        else:
            if sec is None: continue
            k = re.fullmatch(r"(\d{3,4})\s*kcal", low)
            if k and sec in ("o", "a"): days[cur][sec][0] = int(k.group(1)); continue
            item = l + (" · vegan" if "vegan" in low and "·" not in l else "")
            if sec == "s": days[cur]["s"].append(item)
            else: days[cur][sec][1].append(item)

    out = {}
    for k, v in days.items():
        if not (v["o"][1] or v["a"][1] or v["s"]): continue
        out[k] = [v["o"][0], "|".join(v["o"][1]), v["a"][0], "|".join(v["a"][1]), "|".join(v["s"])]
    return out

def main():
    new = parse_menu(fetch())
    if not new:  # parser hiçbir şey bulamadıysa eski dosyayı bozma
        sys.exit("HATA: Menü ayrıştırılamadı, menu.json değiştirilmedi (parse_menu'yu sayfaya göre uyarlayın).")
    old = {}
    if OUT.exists():
        try: old = json.loads(OUT.read_text("utf-8")).get("days", {})
        except Exception: pass
    old.update(new)  # yeni veri eskinin üstüne yazar
    cut = (dt.date.today() - dt.timedelta(days=KEEP_DAYS)).isoformat()
    days = {k: v for k, v in sorted(old.items()) if k >= cut}
    OUT.write_text(json.dumps({"days": days, "updated": dt.datetime.now().isoformat(timespec="seconds")},
                              ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(new)} gün çekildi, toplam {len(days)} gün kaydedildi -> {OUT}")

if __name__ == "__main__":
    main()
