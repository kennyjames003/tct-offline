---
name: trail-map
description: Build a self-contained offline GPS PWA for any hiking trail from a GPX track — live position, waypoints (water/camps/hazards/bailouts), an offline topographic contour map, elevation profile, and per-trip customizable itinerary + "game plan" panels. Use when the user wants to create, scaffold, or clone an offline trail/hiking map app (e.g. "make a Mt. Whitney map", "build an offline GPS app for the JMT", "do one of these for <trail>"). Works fully offline once installed (iOS/Android PWA).
---

# trail-map — offline GPS hiking map generator

This skill generates a complete, self-contained offline hiking app (the same engine
as the Trans Catalina Trail app) for any trail. The output is a static folder you
push to a new GitHub Pages repo. No build server, no dependencies at runtime — code
+ trail data are inlined into one `index.html`, and the topo contours load from a
precached `_topo.json`.

## What you produce
A folder containing: `index.html`, `_topo.json`, `sw.js`, `manifest.webmanifest`,
`icon-{180,192,512}.png`, `.nojekyll`. Deploy = push to a repo with GitHub Pages on.

## Inputs you need from the user
1. **A GPX track** of the route (the one thing that can't be invented). For an
   **out-and-back**, use the one-way trace (trailhead → high point); the app handles
   the return by snapping live position onto the line.
2. **Trail intel** to curate into waypoints: trailheads, camps, water sources,
   hazards, bailouts, permits, hours. Ask for what they know; fill gaps from
   reliable sources and tell them what to verify.
3. **Trip specifics** (optional but it's the part people love): their dates,
   reservations, and a day-by-day plan → becomes the itinerary + game-plan panels.

## One-time setup
```bash
pip install numpy pillow matplotlib   # used by the topo + icon generators
```
`gen_topo.py` / `gpx_to_track.py --fill-elev` need internet (public AWS terrarium
elevation tiles, no key). Everything else is offline.

## Workflow

### 1. GPX → track
```bash
python scripts/gpx_to_track.py route.gpx --name "Mount Whitney Trail" \
    --out work/track.json --simplify-m 8 --out-and-back
```
- `--simplify-m` drops points closer than N meters (keeps the file small; 8 is good).
- `--out-and-back` — **use this if the GPX is a round-trip recording** (starts and
  ends at the trailhead). It keeps only the outbound leg up to the high point, so the
  app's "what mile am I" snap isn't confused by the overlapping return. Mark the high
  point `"end": true` in the waypoints. (Inspect first: if start≈end, it's a round-trip.)
- `--fill-elev` backfills elevation from terrain tiles if the GPX lacks elevation
  (handles both `<ele>` child elements and `ele="…"` attributes, e.g. GaiaGPS).
- Elevation is lightly smoothed by default (GPS jitter otherwise inflates climb totals);
  `--no-smooth` disables it.

### 2. Author `trip.json`
Copy `examples/tct.trip.json` as a model. Schema:
```jsonc
{
  "name": "Mount Whitney Trail", "short": "WHITNEY",
  "tripEndMi": 10.7,                       // optional: mile the trip "ends" (beyond greyed). For an out-and-back, set to the summit mile so the return isn't greyed — or omit.
  "contour": { "interval": 200, "index": 1000 },  // ft. Bigger relief → bigger interval (Whitney ~200/1000; Catalina 100/500).
  "theme": { "accent": "#34d399" },        // app/icon accent color
  "trackFile": "work/track.json",          // or inline "track": {...}
  "land": null,                            // omit/null for inland trails (no coastline). Contours carry the terrain.
  "features": [                            // waypoints. mi/off auto-computed from the track if omitted — you only need lat/lon.
    { "name": "Whitney Portal", "cat": "town", "lat": 36.5865, "lon": -118.2403, "water": "yes", "notes": "Trailhead, store, last water/food. Permit required." },
    { "name": "Trail Camp", "cat": "camp", "lat": 36.5599, "lon": -118.2783, "water": "seasonal",
      "notes": "Highest camp (~12,000′). Last water before the switchbacks — treat it.",
      "stay": { "dates": "Aug 9 → 10", "nights": 1, "unit": "Permit #12345 · 2 people" } },
    { "name": "Mt. Whitney Summit", "cat": "junction", "lat": 36.5785, "lon": -118.2920, "water": "no",
      "notes": "14,505 ft. Turnaround — same way down.", "end": true }
  ],
  "global": [                              // hazard/strategy cards (Troubleshoot tab)
    { "name": "Altitude", "cat": "hazard", "notes": "Acclimatize; watch for AMS. Descend if it worsens." },
    { "name": "Afternoon storms", "cat": "hazard", "notes": "Summit early; be below Trail Crest by noon in monsoon season." }
  ],
  "itinerary": [                           // "Your camp nights" card; current night auto-highlights by date
    { "n": 1, "date": "2026-08-09", "dow": "Sat Aug 9", "camp": "Trail Camp", "cat": "camp", "sub": "Hike Portal → Trail Camp (6.3 mi, +3,800′)" },
    { "date": "2026-08-10", "dow": "Sun Aug 10", "camp": "Summit → out", "cat": "end", "sub": "Summit day, then hike all the way out", "depart": true }
  ],
  "plan": {                                // collapsible "game plan" panel (fully data-driven)
    "summary": "🥾 Summit-day game plan",
    "autoOpen": ["2026-08-10"],            // ISO dates the panel auto-opens
    "blocks": [
      { "th": "⚠️ The big day", "accent": "rgba(251,191,36,.45)", "html": "<b>Trail Camp → summit → out.</b> Start ~3 AM..." },
      { "th": "🌅 Daylight", "daylight": { "First light": "5:40a", "Sunrise": "6:05a", "Sunset": "7:50p" }, "html": "Summit by ~9 AM." },
      { "th": "⏱️ Schedule", "sched": [
        { "tm": "~3:00a", "pl": "<b>Leave Trail Camp</b> · headlamp up the 99 switchbacks", "mi": "mi 6.3" },
        { "tm": "~9:00a", "pl": "<b>Summit</b> · photos, then turn around", "mi": "mi 10.7" }
      ] }
    ]
  }
}
```
**Waypoint `cat`:** `town`, `camp`, `water`, `airport`, `bailout`, `hazard`, `junction`.
**`water`:** `yes` | `seasonal` | `no`. **Flags:** `stay` (reservation badge + popup),
`end` (trip endpoint), `beyond` (greys a point as "beyond your trip"). Daylight times:
compute them (NOAA solar formula) for the trail's lat/lon and date — see the TCT history.

### 3. Build
```bash
python scripts/build.py trip.json out/ [--zoom 14] [--tilecache DIR]
```
Projects waypoints onto the track, injects everything into the engine template,
generates the contour `_topo.json`, and writes the icons/manifest/sw/.nojekyll.
Use `--skip-topo` to iterate fast, then run a full build before deploy.

### 4. Verify
Serve `out/` over HTTP (not file://, the topo fetch needs http) and load it.
Preview a position with `#sim=lat,lon`. Check: no console errors, contours draw,
waypoints + "next up" make sense, itinerary highlights the right night, plan panel
opens. A headless Playwright pass is ideal (see the TCT session for the harness).

### 5. Deploy
- New repo (or subfolder); push `out/` contents to the Pages branch.
- **Enable GitHub Pages** in repo Settings → Pages (source = the branch, root).
- `.nojekyll` is already included — **required**, or Pages' Jekyll hides `_topo.json`
  (underscore-prefixed files 404 without it).
- On every later update, **bump the `CACHE` version in `sw.js`** so installed apps
  pull the new files; users reload once on signal to refresh.

## Per-trail adaptation cheatsheet
- **Inland trail** → `"land": null` (no coastline); contours are the terrain.
- **Big vertical** (alpine) → larger `contour.interval` (200–400 ft) so lines aren't a blur.
- **Out-and-back** → one-way GPX, mark the high point `"end": true`; optionally set
  `tripEndMi` to the summit mile (or omit so nothing greys).
- **Loop / point-to-point** → set `tripEndMi` to the finish mile to grey anything past it.

## Gotchas
- Topo + elevation backfill need internet; tiles cache locally after first run.
- The engine is `templates/app.template.html` with a single `__TRIP_DATA__` injection
  point — edit the engine there, not in generated output.
- Keep the GPX simplified (~1–2k points) so `index.html` stays light.

## Files
- `templates/app.template.html` — the engine (data-driven; injection marker `__TRIP_DATA__`)
- `templates/sw.template.js`, `templates/manifest.template.webmanifest`
- `scripts/gpx_to_track.py` — GPX → track.json
- `scripts/gen_topo.py` — region → topo contour `_topo.json`
- `scripts/build.py` — trip.json → deployable folder
- `examples/tct.trip.json` — the Trans Catalina Trail as a complete worked example
