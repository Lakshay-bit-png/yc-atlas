# YC Atlas

Every Y Combinator startup on a 3D globe — where it was built and who built it.

6,253 companies · 11,799 founders · 383 cities, with a 2005→today timeline, industry/status filters, search across startups, founders and cities, live day/night lighting and generated sound.

## Run locally

```sh
python3 -m http.server 8765
# open http://127.0.0.1:8765
```

(Serve it over http — browsers block some of the assets when opened as a file.)

## Data pipeline

| Script | Output |
|---|---|
| `curl https://yc-oss.github.io/api/companies/all.json` | `data/all.json` — company list |
| `scrape_founders.py` | `data/founders.json` — founders + locations from YC company pages |
| `geocode.py` | `data/geo.json` — city coordinates (OpenStreetMap Nominatim) |
| `download_images.py` | `images/` + `data/images.json` — logos and founder photos |
| `build_dataset.py` | `data/yc.json` — everything merged |
| `build_globe_data.py` | `globe-data.js` — compact data the page loads |
| `build_land.py` | `land.js` — pre-computed continent dots |

Logos and photos are served from [yc-images](https://github.com/Lakshay-bit-png/yc-images) via GitHub Pages (`IMG_BASE` in `index.html`).

## Visitor counter (Vercel + Upstash Redis)

`api/visit.js` is a Vercel function that counts total visits (one per browser session) and unique visitors (anonymous random id per browser) in Upstash Redis. It reads `KV_REST_API_URL` / `KV_REST_API_TOKEN` (or `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN`), which the Vercel Marketplace Upstash integration sets for you. On hosts without the API the counter simply stays hidden.

Built with three.js. Data from public Y Combinator company pages.
