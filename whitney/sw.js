// Offline trail-map PWA — cache-first service worker.
// Code + trail data are inlined in index.html; topo contours load from ./_topo.json (precached below).
// Bump the version below whenever you redeploy so clients pick up the new files.
const CACHE = 'whitney-v4';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './_topo.json', './icon-180.png', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).catch(() => {}));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Cache-first: works fully offline; falls back to network only for cache misses.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(hit => {
      if (hit) return hit;
      return fetch(e.request).then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        return resp;
      }).catch(() => caches.match('./index.html'));
    })
  );
});
