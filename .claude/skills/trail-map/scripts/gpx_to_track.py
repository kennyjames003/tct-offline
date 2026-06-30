#!/usr/bin/env python3
"""Convert a GPX track into the app's compact track structure.

Reads <trkpt lat lon><ele></trkpt> points, computes cumulative miles, and emits:
  {"name", "lat":[...], "lon":[...], "eleFt":[...], "cumMi":[...], "totalMi", "bounds"}

Elevation: taken from GPX <ele> (meters -> feet). If a point lacks elevation and
--fill-elev is set, missing values are filled from terrarium tiles (needs internet).

Usage:
  python gpx_to_track.py route.gpx --name "Mount Whitney Trail" \
      --out track.json [--simplify-m 8] [--fill-elev]

For an OUT-AND-BACK hike, supply the ONE-WAY trace (trailhead -> summit). The app
handles the return automatically by snapping your live position onto the line.
"""
import argparse, json, math, re, xml.etree.ElementTree as ET


def hav_m(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_gpx(path):
    txt = open(path, "r", encoding="utf-8", errors="replace").read()
    # strip namespaces so plain tag names work (and so leftover prefixes don't orphan)
    txt = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", txt)   # xmlns declarations
    txt = re.sub(r'\s\w+:\w+="[^"]*"', "", txt)          # namespaced attrs (e.g. xsi:schemaLocation)
    txt = re.sub(r'(</?)\w+:', r"\1", txt)               # namespaced element tags -> local name
    root = ET.fromstring(txt)
    def elev_of(node):
        # elevation may be a child <ele> (standard) or an attribute ele="" (Gaia etc.)
        if node.get("ele") is not None:
            try:
                return float(node.get("ele"))
            except ValueError:
                return None
        ele = node.find("ele")
        return float(ele.text) if (ele is not None and ele.text) else None

    pts = []
    for tp in root.iter("trkpt"):
        pts.append([float(tp.get("lat")), float(tp.get("lon")), elev_of(tp)])
    if not pts:  # fall back to route points
        for rp in root.iter("rtept"):
            pts.append([float(rp.get("lat")), float(rp.get("lon")), elev_of(rp)])
    return pts


def simplify(pts, min_m):
    if min_m <= 0 or len(pts) < 3:
        return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        if hav_m(out[-1][0], out[-1][1], p[0], p[1]) >= min_m:
            out.append(p)
    out.append(pts[-1])
    return out


def fill_elev(pts, zoom=14):
    import numpy as np
    from PIL import Image
    import urllib.request, os, tempfile
    cache = os.path.join(tempfile.gettempdir(), "trailmap_tiles")
    os.makedirs(cache, exist_ok=True)

    def sample(lat, lon):
        n = 2 ** zoom
        x = (lon + 180.0) / 360.0 * n
        y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
        tx, ty = int(x), int(y)
        fn = os.path.join(cache, f"{zoom}_{tx}_{ty}.png")
        if not os.path.exists(fn):
            url = f"https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{zoom}/{tx}/{ty}.png"
            req = urllib.request.Request(url, headers={"User-Agent": "trail-map"})
            open(fn, "wb").write(urllib.request.urlopen(req, timeout=30).read())
        im = np.asarray(Image.open(fn).convert("RGB"), dtype="float32")
        px, py = int((x - tx) * 256), int((y - ty) * 256)
        px, py = min(255, max(0, px)), min(255, max(0, py))
        r, g, b = im[py, px]
        return (r * 256 + g + b / 256) - 32768.0
    for p in pts:
        if p[2] is None:
            p[2] = sample(p[0], p[1])
    return pts


def truncate_out_and_back(pts):
    """For a round-trip recording (start≈end, high point in the middle), keep only
    the outbound leg up to the highest point so the app's mile/snap logic is clean."""
    if not pts or pts[0][2] is None:
        return pts
    si = max(range(len(pts)), key=lambda i: (pts[i][2] if pts[i][2] is not None else -1e9))
    if si < len(pts) - 5:   # a real round-trip, not already one-way
        return pts[:si + 1]
    return pts


def smooth_elev(pts, window=5):
    """Light moving-average on elevation to cut GPS jitter (which inflates climb totals).
    Preserves the first point and the high point."""
    e = [p[2] for p in pts]
    if any(v is None for v in e) or len(e) < window:
        return pts
    n, half = len(e), window // 2
    hi = max(range(n), key=lambda i: e[i])
    sm = e[:]
    for i in range(n):
        a, b = max(0, i - half), min(n, i + half + 1)
        sm[i] = round(sum(e[a:b]) / (b - a), 1)
    sm[0] = e[0]
    sm[hi] = e[hi]
    for i in range(n):
        pts[i][2] = sm[i]
    return pts


def build_track(pts, name):
    lat = [round(p[0], 5) for p in pts]
    lon = [round(p[1], 5) for p in pts]
    eleFt = [round((p[2] or 0.0) * 3.28084, 1) for p in pts]
    cum, d = [0.0], 0.0
    for i in range(1, len(pts)):
        d += hav_m(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]) / 1609.344
        cum.append(round(d, 3))
    return {
        "name": name,
        "lat": lat, "lon": lon, "eleFt": eleFt, "cumMi": cum,
        "totalMi": round(d, 2),
        "bounds": {"minLat": min(lat), "maxLat": max(lat), "minLon": min(lon), "maxLon": max(lon)},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("gpx")
    ap.add_argument("--name", default="Trail")
    ap.add_argument("--out", default="track.json")
    ap.add_argument("--simplify-m", type=float, default=8.0, help="drop points closer than N meters")
    ap.add_argument("--fill-elev", action="store_true", help="fill missing elevations from terrarium tiles")
    ap.add_argument("--out-and-back", action="store_true",
                    help="track is a round-trip recording; keep only the outbound leg (up to the high point)")
    ap.add_argument("--no-smooth", action="store_true", help="disable elevation smoothing")
    a = ap.parse_args()
    pts = parse_gpx(a.gpx)
    print(f"[gpx] {len(pts)} points read")
    pts = simplify(pts, a.simplify_m)
    if a.fill_elev or any(p[2] is None for p in pts):
        pts = fill_elev(pts)
    if a.out_and_back:
        before = len(pts)
        pts = truncate_out_and_back(pts)
        print(f"[gpx] out-and-back: truncated {before} -> {len(pts)} points at the high point")
    if not a.no_smooth:
        pts = smooth_elev(pts)
    track = build_track(pts, a.name)
    json.dump(track, open(a.out, "w"), separators=(",", ":"))
    print(f"[gpx] {len(pts)} points, {track['totalMi']} mi -> {a.out}")
