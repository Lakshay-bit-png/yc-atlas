"""Geocode every unique location in data/all.json via OpenStreetMap Nominatim.

Resumable (keeps data/geo.json between runs). Nominatim allows 1 req/sec.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent / "data"
OUT = ROOT / "geo.json"
UA = "yc-globe personal project"


def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    res = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if res:
        return {"lat": float(res[0]["lat"]), "lng": float(res[0]["lon"])}
    # fall back to dropping the most specific part ("Bengaluru, KA, India" -> "KA, India")
    parts = [p.strip() for p in q.split(",")]
    return geocode(", ".join(parts[1:])) if len(parts) > 1 else None


def main():
    geo = json.loads(OUT.read_text()) if OUT.exists() else {}
    places = set()
    for c in json.loads((ROOT / "all.json").read_text()):
        for loc in (c.get("all_locations") or "").split(";"):
            loc = loc.strip()
            if loc and loc != "Remote":
                places.add(loc)
    todo = sorted(p for p in places if p not in geo)
    print(len(places), "places,", len(todo), "to geocode", flush=True)
    for i, p in enumerate(todo, 1):
        try:
            geo[p] = geocode(p)
        except Exception as e:
            print("fail", p, e, flush=True)
        time.sleep(1.1)
        if i % 25 == 0:
            OUT.write_text(json.dumps(geo, indent=1, ensure_ascii=False))
            print(i, flush=True)
    OUT.write_text(json.dumps(geo, indent=1, ensure_ascii=False))
    print("done", sum(1 for v in geo.values() if v), "/", len(geo), flush=True)


if __name__ == "__main__":
    main()
