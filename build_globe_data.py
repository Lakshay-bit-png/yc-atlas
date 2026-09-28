"""Pack data/yc.json into a compact globe-data.js the globe page loads via <script>.

Nearby locations (e.g. "New York, NY" and "New York City, NY") are merged into
one city point, so spikes don't double up.
"""
import json
import math
from pathlib import Path

BASE = Path(__file__).parent
MERGE_KM = 12
BIO_LEN = 260
DESC_LEN = 320


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def main():
    data = json.loads((BASE / "data" / "yc.json").read_text())

    # count usage per raw location so the busiest name becomes the city's label
    counts = {}
    for c in data:
        for l in c["locations"]:
            if "lat" in l:
                counts[l["name"]] = counts.get(l["name"], (l, 0))[0], counts.get(l["name"], (l, 0))[1] + 1
    cities, raw_to_city = [], {}
    for name, (loc, _) in sorted(counts.items(), key=lambda kv: -kv[1][1]):
        hit = next((i for i, c in enumerate(cities) if km(c, loc) < MERGE_KM), None)
        if hit is None:
            parts = [p.strip() for p in name.split(",")]
            cities.append({"n": parts[0], "full": name, "c": parts[-1], "lat": round(loc["lat"], 4), "lng": round(loc["lng"], 4)})
            hit = len(cities) - 1
        raw_to_city[name] = hit

    companies = []
    for c in data:
        city_ids = sorted({raw_to_city[l["name"]] for l in c["locations"] if l["name"] in raw_to_city})
        companies.append([
            c["name"],
            c["slug"],
            clip(c["one_liner"], 140),
            clip(c["description"], DESC_LEN),
            c["batch"] or "",
            c["year"] or 0,
            c["status"] or "",
            c["industry"] or "Other",
            city_ids,
            c["logo_file"] or "",
            c["team_size"] or 0,
            c["website"] or "",
            1 if c["top_company"] else 0,
            1 if c["remote"] else 0,
            [[f["full_name"], f["title"] or "", f["photo"] or "", f["linkedin_url"] or "", f["twitter_url"] or "",
              clip(f["founder_bio"], BIO_LEN)] for f in c["founders"]],
            (c["tags"] or [])[:5],
        ])

    payload = {
        "cityFields": ["n", "full", "c", "lat", "lng"],
        "companyFields": ["name", "slug", "oneLiner", "desc", "batch", "year", "status", "industry", "cities",
                          "logo", "team", "website", "top", "remote", "founders", "tags"],
        "cities": cities,
        "companies": companies,
    }
    out = BASE / "globe-data.js"
    out.write_text("window.YC_DATA=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";")
    print(f"{len(cities)} cities, {len(companies)} companies -> {out.name} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
