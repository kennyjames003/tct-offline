# Trans Catalina Trail — Offline GPS Companion

A self-contained offline web app (PWA) for hiking the Trans Catalina Trail. Built from a recorded GPX track (~38.8 mi). Works fully offline once installed; uses your phone's GPS to show where you are on the trail, what's ahead (camps, water, bailouts), and context-aware troubleshooting.

## Install on iPhone (do this at home, with wifi)
1. Open the Pages URL in **Safari**.
2. Tap **Share → Add to Home Screen**.
3. Open the app once from the Home Screen icon while still online so it caches everything.
4. Allow **Location** when prompted. (Settings → Privacy → Location → Safari/this app → While Using.)
5. Now it works with no signal. Airplane mode is fine — GPS still works.

## On the trail
- **Where am I**: on-trail / off-trail (with a bearing back to the line), trail mile, elevation.
- **Next up**: next camp, next reliable water, next town/airport, nearest bailout — with distance, ETA, and climb.
- **Map**: the trail line + your live dot. Pinch/drag to explore, tap a marker for details. (No satellite/topo tiles — trail line only.)
- **Elevation profile** with your position.
- **Troubleshoot / safety**: bison, heat/water strategy, emergency notes.
- ☀︎ toggles high-contrast (sunlight) mode; ☾ keeps the screen awake.

## Preview without being on-trail
Append `#sim=lat,lon` to the URL to simulate a position, e.g. `…/index.html#sim=33.4015,-118.4759` (Little Harbor).

## ⚠️ Verify before you go
Water availability, camp reservations, and Airport/store hours change. Confirm with the **Catalina Island Conservancy** and **Two Harbors Visitor Services** before your trip — especially **Parsons Landing has no reliable on-site water** (buy water + locker key at Two Harbors). This app is a companion, not a substitute for a real map and good judgment.
