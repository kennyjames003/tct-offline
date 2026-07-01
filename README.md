# Mt. Whitney Trip — Offline Planner

A self-contained offline web app (PWA) for a Mt. Whitney overnight trip. It bundles the day-by-day plan, a real USGS topographic map, and a pre-trip checklist so you can open it at any point — **with zero cell service** — and know where you are in the plan, what today's objective is, and what still needs verifying.

**Live:** https://kennyjames003.github.io/tct-offline/

## The trip it's built for (Jul 16–18)
- **Thu 7/16** — Drive to Whitney Portal in the afternoon (after getting off work early); camp at the Portal to start acclimating.
- **Fri 7/17** — Hike to Trail Camp. No need to leave early — it's an overnight, so hike it relaxed.
- **Sat 7/18** — Alpine start, summit Mt. Whitney via the switchbacks and Trail Crest, then descend all the way out.

## What's inside
- **Trip schedule** with an automatic "today" highlight and a pre-trip countdown (uses your device clock — works offline).
- **Interactive pre-trip checklist** (permit, weather, water, WAG bag, bear canister, snow/ice, headlamp, share-your-plan). Tap to check off; state is saved on your device.
- **Schematic trail map** — waypoints in order (Portal → Lone Pine Lake → Outpost Camp → Mirror Lake → Trail Camp → Trail Crest → Summit).
- **Topographic map (offline)** — real USGS topo tiles for the trail area, cached on-device, with the recorded GPX route overlaid and your live GPS position. Pan/zoom, "Whole route," and "My location." A readiness badge tells you exactly how many tiles are cached so you know it's truly offline-ready.
- **Elevation profile** of the climb (Portal → Trail Camp → Summit).

## Install on iPhone (do this at home, on wifi)
1. Open the live URL in **Safari**.
2. Tap **Share → Add to Home Screen**.
3. Open it once from the Home Screen icon **while still on wifi**, and scroll to the topo map — wait for the green **"✓ Offline maps ready — 237/237 tiles cached"** badge (~10–20 sec while it downloads the map tiles).
4. Now it works with no signal. Airplane mode is fine — the map, plan, and your GPS position all still work.

## How the offline part works
Everything is served over HTTPS via GitHub Pages and cached by a service worker (`sw.js`):
- The **page shell is network-first** — online, you always get the latest version; offline, it falls back to the last cached copy. (So updates never get stuck.)
- The **topo tiles and icons are cache-first** — fast, and fully available with no service once cached.

## ⚠️ Verify before you go
Distances, elevations, permit rules, water availability, and weather **change** and are shown as planning estimates. Confirm your permit/quota, current conditions, and weather with **Inyo National Forest / recreation.gov** before the trip. The maps are **schematic / not a substitute for a paper topo** and good judgment — carry a real map.

## Notes
- Map data: **USGS** (The National Map, public domain). Route from a GaiaGPS GPX export.
- A separate, earlier Whitney build lives at `/whitney/` in this repo; the app at the root is the current one.
