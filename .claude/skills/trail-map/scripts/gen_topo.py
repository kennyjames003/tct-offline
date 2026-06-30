#!/usr/bin/env python3
"""Generate offline topographic contour lines (_topo.json) for a trail's region.

Downloads public-domain terrarium elevation tiles (AWS, no key) covering the
given lat/lon bounds, decodes them to an elevation grid, traces contour lines at
the requested interval, simplifies them, and writes a compact _topo.json that the
app draws under the trail line.

Usage:
  python gen_topo.py --bounds minLat minLon maxLat maxLon \
      --interval 100 --index 500 --out _topo.json [--zoom 14] [--cache DIR]

Requires: numpy, pillow, matplotlib  (pip install numpy pillow matplotlib)
Needs internet for the tile download (one-time; tiles are cached).
"""
import argparse, json, math, os, urllib.request

TILE_URL = "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png"


def deg2tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def build_grid(minLat, minLon, maxLat, maxLon, z, cache):
    import numpy as np
    from PIL import Image
    margin = 0.01
    x0f, y0f = deg2tile(maxLat + margin, minLon - margin, z)
    x1f, y1f = deg2tile(minLat - margin, maxLon + margin, z)
    x0, x1 = int(math.floor(x0f)), int(math.floor(x1f))
    y0, y1 = int(math.floor(y0f)), int(math.floor(y1f))
    TS = 256
    W, H = (x1 - x0 + 1) * TS, (y1 - y0 + 1) * TS
    elev = np.zeros((H, W), dtype="float32")
    os.makedirs(cache, exist_ok=True)
    ntiles = (x1 - x0 + 1) * (y1 - y0 + 1)
    print(f"[gen_topo] {ntiles} tiles at z{z} ({W}x{H} grid)")
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            fn = os.path.join(cache, f"{z}_{tx}_{ty}.png")
            if not os.path.exists(fn):
                url = TILE_URL.format(z=z, x=tx, y=ty)
                req = urllib.request.Request(url, headers={"User-Agent": "trail-map-topo"})
                open(fn, "wb").write(urllib.request.urlopen(req, timeout=30).read())
            a = np.asarray(Image.open(fn).convert("RGB"), dtype="float32")
            h = (a[:, :, 0] * 256.0 + a[:, :, 1] + a[:, :, 2] / 256.0) - 32768.0
            ox, oy = (tx - x0) * TS, (ty - y0) * TS
            elev[oy:oy + TS, ox:ox + TS] = h
    return elev, dict(z=z, x0=x0, y0=y0, TS=TS)


def _dp(pts, tol):
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        if L2 == 0:
            d = math.hypot(px - ax, py - ay)
        else:
            t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
            d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return _dp(pts[:idx + 1], tol)[:-1] + _dp(pts[idx:], tol)
    return [pts[0], pts[-1]]


def generate(bounds, interval, index, out, zoom=14, cache=None, tol=0.0001, minlen=0.0016):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    minLat, minLon, maxLat, maxLon = bounds
    cache = cache or os.path.join(os.path.dirname(out) or ".", ".tilecache")
    elev, meta = build_grid(minLat, minLon, maxLat, maxLon, zoom, cache)
    elev = np.clip(elev, 0, None)

    def blur(a):
        b = a.copy()
        b[1:-1, 1:-1] = (a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]) / 5.0
        return b
    for _ in range(2):
        elev = blur(elev)
    elev_ft = elev * 3.28084
    Z, x0, y0, TS = meta["z"], meta["x0"], meta["y0"], meta["TS"]

    def px2ll(col, row):
        gx, gy = x0 + col / TS, y0 + row / TS
        lon = gx / (2 ** Z) * 360.0 - 180.0
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy / (2 ** Z)))))
        return lon, lat

    def seglen(ll):
        return sum(math.hypot(ll[i + 1][0] - ll[i][0], ll[i + 1][1] - ll[i][1]) for i in range(len(ll) - 1))

    levels = list(range(interval, int(elev_ft.max()) + 1, interval))
    cs = plt.contour(elev_ft, levels=levels)
    out_levels, total = [], 0
    for lev, segs in zip(cs.levels, cs.allsegs):
        ft = int(round(lev))
        lines = []
        for seg in segs:
            if len(seg) < 5:
                continue
            ll = [px2ll(c, r) for (c, r) in seg]
            if seglen(ll) < minlen:
                continue
            ll = _dp(ll, tol)
            if len(ll) < 2:
                continue
            lines.append([[round(x, 5), round(y, 5)] for x, y in ll])
            total += len(ll)
        if lines:
            out_levels.append({"ft": ft, "i": 1 if ft % index == 0 else 0, "l": lines})
    json.dump({"interval": interval, "index": index, "levels": out_levels},
              open(out, "w"), separators=(",", ":"))
    sz = os.path.getsize(out)
    print(f"[gen_topo] {len(out_levels)} levels, {total} vertices, {sz/1024:.0f} KB -> {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bounds", nargs=4, type=float, required=True,
                    metavar=("minLat", "minLon", "maxLat", "maxLon"))
    ap.add_argument("--interval", type=int, default=100)
    ap.add_argument("--index", type=int, default=500)
    ap.add_argument("--zoom", type=int, default=14)
    ap.add_argument("--out", default="_topo.json")
    ap.add_argument("--cache", default=None)
    a = ap.parse_args()
    generate(tuple(a.bounds), a.interval, a.index, a.out, a.zoom, a.cache)
