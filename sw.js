// Mt. Whitney trip offline PWA.
// HTML shell: network-first (always fresh when online; cached copy when offline).
// Topo tiles + icons: cache-first (fast, works with zero service on-trail).
const CACHE = 'whitney-v14';
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

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const req = e.request;
  const accept = req.headers.get('accept') || '';
  const isShell = req.mode === 'navigate' || accept.includes('text/html');

  if (isShell) {
    // Network-first for the page itself: online users always get the latest build;
    // offline users fall back to the last cached copy. No more stuck updates.
    e.respondWith(
      fetch(req).then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put('./index.html', copy)).catch(() => {});
        return resp;
      }).catch(() => caches.match('./index.html').then(h => h || caches.match('./')))
    );
    return;
  }

  // Cache-first for tiles/icons/manifest: fast and fully offline.
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(resp => {
      const copy = resp.clone();
      caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      return resp;
    }).catch(() => caches.match('./index.html')))
  );
});
