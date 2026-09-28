"""Download every startup logo and founder photo into images/.

Founder avatar URLs on YC pages are signed and expire after ~1 hour, so each
company page is re-fetched and its photos downloaded straight away.
Resumable: a company is skipped once it has an entry in data/images/<slug>.json.

Output:
  images/logos/<slug>.<ext>
  images/founders/<user_id>.<ext>
  data/images.json  -> {slug: {"logo": path, "founders": {full_name: path}}}
"""
import html
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).parent
ROOT = BASE / "data"
CACHE = ROOT / "images"
LOGOS = BASE / "images" / "logos"
FACES = BASE / "images" / "founders"
for d in (CACHE, LOGOS, FACES):
    d.mkdir(parents=True, exist_ok=True)
WORKERS = 4
UA = "Mozilla/5.0 (yc-globe personal project)"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()


def ext_of(url, default):
    m = re.search(r"\.(png|jpe?g|gif|webp|svg)(\?|$)", url, re.I)
    return m.group(1).lower() if m else default


def save(url, dest_dir, name, default_ext):
    if not url or "missing" in url:
        return None
    path = dest_dir / f"{name}.{ext_of(url, default_ext)}"
    if not path.exists():
        path.write_bytes(get(url))
    return str(path.relative_to(BASE))


def process(company):
    slug = company["slug"]
    out = CACHE / f"{slug}.json"
    if out.exists():
        return "cached"
    for attempt in range(4):
        try:
            try:
                logo = save(company.get("small_logo_thumb_url"), LOGOS, slug, "png")
            except urllib.error.HTTPError:
                logo = None  # logo deleted on YC's side; still grab founders
            rec = {"logo": logo, "founders": {}}
            body = get(f"https://www.ycombinator.com/companies/{slug}").decode()
            m = re.search(r'data-page="([^"]+)"', body)
            founders = json.loads(html.unescape(m.group(1)))["props"]["company"].get("founders") or [] if m else []
            for f in founders:
                rec["founders"][f["full_name"]] = save(f.get("avatar_thumb_url"), FACES, f["user_id"], "jpg")
            out.write_text(json.dumps(rec))
            time.sleep(0.25)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                out.write_text(json.dumps({"logo": None, "founders": {}, "error": e.code}))
                return str(e.code)
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return "fail"


def main():
    companies = json.loads((ROOT / "all.json").read_text())
    stats = {}
    with ThreadPoolExecutor(WORKERS) as pool:
        for i, r in enumerate(pool.map(process, companies), 1):
            stats[r] = stats.get(r, 0) + 1
            if i % 250 == 0:
                print(i, len(companies), stats, flush=True)
    print("done", stats, flush=True)

    merged = {}
    for c in companies:
        p = CACHE / f"{c['slug']}.json"
        if p.exists():
            merged[c["slug"]] = json.loads(p.read_text())
    (ROOT / "images.json").write_text(json.dumps(merged, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
