# Mount Whitney Trail — Offline GPS Companion

A self-contained offline web app (PWA) for the **Mount Whitney Trail** (Whitney Portal → summit, out-and-back). Built from a recorded GPX track. Works fully offline once installed; uses your phone's GPS to show where you are on the trail, what's ahead (water, camps, the summit), an offline **topographic contour map**, and altitude/weather safety notes.

**~11 mi one-way · +6,100 ft · summit 14,505 ft.** Out-and-back: you summit and return the same way.

## Install on iPhone (do this at home, on wifi)
1. Open the Pages URL in **Safari**: `https://kennyjames003.github.io/tct-offline/whitney/`
2. Tap **Share → Add to Home Screen** (it installs as **WHITNEY**, separate from any other trail app).
3. Open it once from the Home Screen icon while still online so it caches the map + topo contours.
4. Allow **Location** when prompted (Settings → Privacy → Location → Safari → While Using).
5. Now it works with no signal. Airplane mode is fine — GPS still works.

## On the trail
- **Where am I**: on-trail / off-trail (with a bearing back to the line), trail mile, elevation, pace.
- **Next up**: next water, next camp, and the next landmark — works on the way **up** (toward the summit) and on the way **down** (toward Whitney Portal), with ▲/▼ elevation change.
- **Bail-out**: a route-safe retreat — it points you **back down the trail** to the nearest camp/trailhead, never a cross-country shortcut.
- **Map**: trail line + your live dot over **topographic contours** (200 ft, bold every 1,000 ft). Pinch/drag to explore, tap a marker for details. "◭ Topo" toggles contours; "⤢ Full route" fits the whole trail.
- **Elevation profile** with your position.
- **Troubleshoot / safety**: altitude, storms, water, switchbacks, marmots, permits.
- ☀︎ toggles high-contrast (sunlight) mode; ☾ keeps the screen awake.

## Preview without being on-trail
Append `#sim=lat,lon` to the URL to simulate a position. Examples:
- Whitney Portal — `…/whitney/index.html#sim=36.58707,-118.24014`
- Outpost Camp — `#sim=36.57114,-118.26155`
- Trail Camp — `#sim=36.56297,-118.27918`
- Trail Crest — `#sim=36.56652,-118.29250`
- Summit — `#sim=36.57847,-118.29247`

## ⚠️ Verify before you go
This is a companion, not a substitute for a map, a permit, and good judgment. On Mount Whitney the real dangers are **altitude** and **afternoon thunderstorms** — summit early and turn around if storms build. Confirm with **Inyo National Forest**:
- Your **Whitney Zone permit** (overnight via lottery/reservation) and the required **bear canister**.
- **Water** availability by season — treat everything; **Trail Camp is the last normal water** before the summit push, and there is **none above it**.
- **Snow/ice** on the 99 switchbacks and the cables (an ice axe + microspikes may be needed into mid-July after a heavy winter).
- Pack out everything, including **WAG bags** — human waste must be carried out of the Whitney Zone.

Trail distances/elevations are approximate (derived from a GPX trace) — don't treat the mile markers as exact.
