// Offline support. Bump CACHE when you want phones to drop old files at once.
const CACHE = "baseline-season-22";
const SHELL = ["./", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "fonts/inter-tight.woff2", "vendor/motion.js", "icons/cloud.webp", "icons/fig-plyo.webp", "icons/fig-mob.webp", "icons/fig-cardio.webp", "icons/fig-lift.webp"];
self.addEventListener("install", e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
// Serve from cache at once, refresh the cache in the background: updates show on the next open.
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  // Preview pages change often while a design is being tried: always load them fresh.
  if (url.pathname.endsWith("-preview.html")) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
