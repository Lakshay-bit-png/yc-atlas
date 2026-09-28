"""Pre-compute the dotted-continent points into land.js (so the page needs no texture download).

Uses the same Fibonacci-sphere sampling the globe used at runtime.
"""
import json
import math
from pathlib import Path

from PIL import Image

# downloaded from https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-water.png
MASK = Path(__file__).parent / "data" / "earth-water.png"
N = 75000


def main():
    img = Image.open(MASK).convert("L").resize((1024, 512))
    W, H = img.size
    px = img.load()
    at = lambda lat, lng: px[min(W - 1, int((lng + 180) / 360 * W)), min(H - 1, int((90 - lat) / 180 * H))]
    water = at(0, -150)
    golden = math.pi * (3 - math.sqrt(5))
    pts = []
    for i in range(N):
        lat = math.degrees(math.asin(1 - (i / (N - 1)) * 2))
        lng = (math.degrees(golden * i) % 360) - 180
        if abs(at(lat, lng) - water) > 100:
            pts += [round(lat, 2), round(lng, 2)]
    out = Path(__file__).parent / "land.js"
    out.write_text("window.YC_LAND=" + json.dumps(pts, separators=(",", ":")) + ";")
    print(f"{len(pts) // 2} land dots -> land.js ({out.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
