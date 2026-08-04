import os
import sys
import requests
from bs4 import BeautifulSoup

# 브리핑할 언어. ""은 전체 트렌딩.
LANGUAGES = ["", "python", "typescript"]
TOP_N = 5
SINCE = "daily"  # daily | weekly | monthly


def fetch_trending(language):
    url = f"https://github.com/trending/{language}?since={SINCE}"
    res = requests.get(url, headers={"User-Agent": "trending-brief"}, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    repos = []
    for row in soup.select("article.Box-row")[:TOP_N]:
        link = row.select_one("h2 a")
        if not link:
            continue
        name = link.get("href", "").strip("/")
        desc = row.select_one("p")
        lang = row.select_one("span[itemprop=programmingLanguage]")
        stars_today = row.select_one("span.float-sm-right")
        repos.append({
            "name": name,
            "url": f"https://github.com/{name}",
            "desc": desc.get_text(strip=True) if desc else "",
            "lang": lang.get_text(strip=True) if lang else "?",
            "today": stars_today.get_text(strip=True) if stars_today else "",
        })
    return repos


def build_embed(language, repos):
    lines = []
    for i, r in enumerate(repos, 1):
        desc = r["desc"][:120] + ("..." if len(r["desc"]) > 120 else "")
        meta = " · ".join(x for x in [r["lang"], r["today"]] if x)
        lines.append(f"**{i}. [{r['name']}]({r['url']})**\n{desc}\n`{meta}`")

    return {
        "title": f"🔥 {language or 'All'} trending ({SINCE})",
        "description": "\n\n".join(lines) or "결과 없음",
        "color": 0x2EA043,
    }


def main():
    dry = "--dry-run" in sys.argv
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook and not dry:
        sys.exit("DISCORD_WEBHOOK_URL 없음")

    embeds = []
    for lang in LANGUAGES:
        repos = fetch_trending(lang)
        if repos:
            embeds.append(build_embed(lang, repos))

    if not embeds:
        sys.exit("트렌딩 파싱 실패 — GitHub HTML 구조 변경 가능성")

    if dry:
        for e in embeds:
            print(f"\n=== {e['title']} ===\n{e['description']}")
        return

    res = requests.post(webhook, json={"embeds": embeds}, timeout=20)
    res.raise_for_status()
    print(f"posted {len(embeds)} embeds")


if __name__ == "__main__":
    main()
