// Mt. Whitney trip offline PWA — cache-first service worker.
// App shell is inlined in index.html; USGS topo tiles (./tiles) are precached from tiles/manifest.json.
const CACHE = 'whitney-v12';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './tiles/manifest.json', './icon-180.png', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await c.addAll(ASSETS).catch(() => {});
    // Precache all topo tiles so the map works with zero service on-trail.
    try {
      const tiles = await fetch('./tiles/manifest.json', { cache: 'no-cache' }).then(r => r.json());
      for (let i = 0; i < tiles.length; i += 30) {
        await c.addAll(tiles.slice(i, i + 30)).catch(() => {});
      }
    } catch (e) {}
  })());
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
