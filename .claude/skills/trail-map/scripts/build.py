#!/usr/bin/env python3
"""Assemble a complete offline trail-map PWA from a trip.json.

Reads a trip config, projects waypoints onto the track, injects everything into
the engine template, generates the topo contour layer, and writes a ready-to-
deploy folder: index.html, _topo.json, sw.js, manifest.webmanifest, icons, .nojekyll

Usage:
  python build.py trip.json out/ [--skip-topo] [--zoom 14]

trip.json shape (see examples/tct.trip.json):
  {
    "name": "Trail Name", "short": "TRL",
    "tripEndMi": 24.67,                 # optional: mile your trip ends (beyond greyed)
    "contour": {"interval": 100, "index": 500},
    "theme": {"accent": "#34d399"},     # optional, for icons/manifest
    "track": {...} | "trackFile": "track.json",
    "land": {...},                       # optional coastline/landmass rings (omit for inland)
    "features": [{name,cat,lat,lon,water,notes, stay?, beyond?, end?}, ...],
    "global":   [{name,cat,notes}, ...], # hazard/strategy cards
    "itinerary":[{n?,date,dow,camp,cat,sub,depart?}, ...],
    "plan":     {summary, autoOpen:[...], blocks:[...]}
  }
Waypoint mi/off are computed from the track if absent.
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.normpath(os.path.join(HERE, "..", "templates"))


def hav_m(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    a = (math.sin(math.radians(la2 - la1) / 2) ** 2 +
         math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def project_features(features, track):
    """Fill mi/off for any feature missing them, by snapping onto the track."""
    lat, lon, cum = track["lat"], track["lon"], track["cumMi"]
    for f in features:
        if "mi" in f and "off" in f:
            continue
        best, bi = 1e18, 0
        for i in range(len(lat)):
            d = hav_m(f["lat"], f["lon"], lat[i], lon[i])
            if d < best:
                best, bi = d, i
        f.setdefault("mi", round(cum[bi], 2))
        f.setdefault("off", int(round(best)))
    return features


def make_icons(outdir, accent, label):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("[build] PIL not available, skipping icon generation")
        return
    def hexrgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    bg = hexrgb(accent)
    for sz in (180, 192, 512):
        im = Image.new("RGB", (sz, sz), (11, 20, 16))
        d = ImageDraw.Draw(im)
        pad = int(sz * 0.14)
        d.rounded_rectangle([pad, pad, sz - pad, sz - pad], radius=int(sz * 0.18), fill=bg)
        txt = (label or "T")[:3].upper()
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(sz * 0.34))
        except Exception:
            font = ImageFont.load_default()
        tb = d.textbbox((0, 0), txt, font=font)
        d.text(((sz - (tb[2] - tb[0])) / 2, (sz - (tb[3] - tb[1])) / 2 - tb[1]),
               txt, fill=(11, 20, 16), font=font)
        im.save(os.path.join(outdir, f"icon-{sz}.png"))
    print("[build] icons generated")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trip")
    ap.add_argument("outdir")
    ap.add_argument("--skip-topo", action="store_true")
    ap.add_argument("--zoom", type=int, default=14)
    ap.add_argument("--tilecache", default=None)
    a = ap.parse_args()

    trip = json.load(open(a.trip))
    os.makedirs(a.outdir, exist_ok=True)

    # track (inline or referenced file)
    if "track" in trip:
        track = trip["track"]
    elif "trackFile" in trip:
        tf = trip["trackFile"]
        if not os.path.isabs(tf):
            tf = os.path.join(os.path.dirname(os.path.abspath(a.trip)), tf)
        track = json.load(open(tf))
    else:
        sys.exit("trip.json needs 'track' or 'trackFile'")

    features = project_features(trip.get("features", []), track)
    contour = trip.get("contour", {"interval": 100, "index": 500})

    TRIP = {
        "name": trip.get("name", "Trail"),
        "short": trip.get("short", "TRL"),
        "tripEndMi": trip.get("tripEndMi"),
        "contour": contour,
        "tct": {
            "track": track,
            "features": features,
            "global": trip.get("global", []),
            "land": trip.get("land"),
            "disclaimer": trip.get("disclaimer", ""),
        },
        "itinerary": trip.get("itinerary", []),
        "plan": trip.get("plan"),
    }

    # inject into engine template
    tpl = open(os.path.join(TEMPLATES, "app.template.html")).read()
    data = json.dumps(TRIP, ensure_ascii=False, separators=(",", ":"))
    if "__TRIP_DATA__" not in tpl:
        sys.exit("template missing __TRIP_DATA__ marker")
    open(os.path.join(a.outdir, "index.html"), "w").write(tpl.replace("__TRIP_DATA__", data))
    print(f"[build] index.html written ({len(features)} waypoints, {len(track['lat'])} track pts)")

    # manifest
    accent = (trip.get("theme") or {}).get("accent", "#34d399")
    man = open(os.path.join(TEMPLATES, "manifest.template.webmanifest")).read()
    man = (man.replace("__NAME__", TRIP["name"]).replace("__SHORT__", TRIP["short"])
              .replace("__ACCENT__", accent))
    open(os.path.join(a.outdir, "manifest.webmanifest"), "w").write(man)

    # service worker (unique cache name)
    sw = open(os.path.join(TEMPLATES, "sw.template.js")).read()
    sw = sw.replace("__CACHE__", TRIP["short"].lower().replace(" ", "-") + "-v1")
    open(os.path.join(a.outdir, "sw.js"), "w").write(sw)

    open(os.path.join(a.outdir, ".nojekyll"), "w").write("")
    make_icons(a.outdir, accent, TRIP["short"])

    # topo contours
    if not a.skip_topo:
        sys.path.insert(0, HERE)
        import gen_topo
        b = track["bounds"]
        gen_topo.generate((b["minLat"], b["minLon"], b["maxLat"], b["maxLon"]),
                          contour["interval"], contour["index"],
                          os.path.join(a.outdir, "_topo.json"),
                          zoom=a.zoom, cache=a.tilecache)
    else:
        print("[build] --skip-topo: remember to generate _topo.json before deploy")

    print(f"[build] done -> {a.outdir}")


if __name__ == "__main__":
    main()
