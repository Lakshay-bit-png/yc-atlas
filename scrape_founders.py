"""Fetch founder + location details for every YC company in data/all.json.

Resumable: each company is cached in data/pages/<slug>.json, so re-running
only fetches what's missing. Output: data/founders.json
"""
import html
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent / "data"
CACHE = ROOT / "pages"
CACHE.mkdir(exist_ok=True)
WORKERS = 4
UA = "Mozilla/5.0 (yc-globe personal project)"

FOUNDER_KEYS = ["full_name", "title", "founder_bio", "linkedin_url", "twitter_url", "is_active"]
COMPANY_KEYS = ["location", "city", "country", "year_founded", "linkedin_url", "twitter_url", "github_url"]


def fetch(slug):
    out = CACHE / f"{slug}.json"
    if out.exists():
        return "cached"
    url = f"https://www.ycombinator.com/companies/{slug}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            body = urllib.request.urlopen(req, timeout=30).read().decode()
            m = re.search(r'data-page="([^"]+)"', body)
            company = json.loads(html.unescape(m.group(1)))["props"]["company"] if m else {}
            rec = {k: company.get(k) for k in COMPANY_KEYS}
            rec["founders"] = [{k: f.get(k) for k in FOUNDER_KEYS} for f in company.get("founders") or []]
            out.write_text(json.dumps(rec))
            time.sleep(0.25)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                out.write_text(json.dumps({"founders": [], "missing": True}))
                return "404"
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return "fail"


def main():
    companies = json.loads((ROOT / "all.json").read_text())
    slugs = [c["slug"] for c in companies]
    stats = {}
    with ThreadPoolExecutor(WORKERS) as pool:
        for i, r in enumerate(pool.map(fetch, slugs), 1):
            stats[r] = stats.get(r, 0) + 1
            if i % 250 == 0:
                print(i, len(slugs), stats, flush=True)
    print("done", stats, flush=True)

    merged = {}
    for s in slugs:
        p = CACHE / f"{s}.json"
        if p.exists():
            merged[s] = json.loads(p.read_text())
    (ROOT / "founders.json").write_text(json.dumps(merged, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
