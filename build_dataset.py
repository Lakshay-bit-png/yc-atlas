"""Merge all.json + founders.json + geo.json into data/yc.json (one record per company)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent / "data"


def batch_year(batch):
    m = re.search(r"(\d{4})", batch or "")
    return int(m.group(1)) if m else None


def main():
    companies = json.loads((ROOT / "all.json").read_text())
    founders = json.loads((ROOT / "founders.json").read_text())
    geo = json.loads((ROOT / "geo.json").read_text())
    images_path = ROOT / "images.json"
    images = json.loads(images_path.read_text()) if images_path.exists() else {}

    out = []
    for c in companies:
        page = founders.get(c["slug"], {})
        imgs = images.get(c["slug"], {})
        locs = [l.strip() for l in (c.get("all_locations") or "").split(";") if l.strip()]
        out.append({
            "name": c["name"],
            "slug": c["slug"],
            "one_liner": c.get("one_liner"),
            "description": c.get("long_description"),
            "batch": c.get("batch"),
            "year": batch_year(c.get("batch")),
            "status": c.get("status"),
            "industry": c.get("industry"),
            "subindustry": c.get("subindustry"),
            "tags": c.get("tags"),
            "team_size": c.get("team_size"),
            "top_company": c.get("top_company"),
            "website": c.get("website"),
            "logo": c.get("small_logo_thumb_url"),
            "logo_file": imgs.get("logo"),
            "yc_url": c.get("url"),
            "locations": [{"name": l, **(geo.get(l) or {})} for l in locs],
            "remote": "Remote" in locs,
            "year_founded": page.get("year_founded"),
            "linkedin": page.get("linkedin_url") or None,
            "twitter": page.get("twitter_url") or None,
            "founders": [{**f, "photo": imgs.get("founders", {}).get(f["full_name"])} for f in page.get("founders", [])],
        })
    (ROOT / "yc.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

    n_f = sum(len(c["founders"]) for c in out)
    n_geo = sum(1 for c in out if any("lat" in l for l in c["locations"]))
    print(f"{len(out)} companies, {n_f} founders, {n_geo} companies on the map")


if __name__ == "__main__":
    main()
