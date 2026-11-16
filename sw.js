// Offline support. Bump CACHE when you want phones to drop old files at once.
const CACHE = "baseline-season-28";
const SHELL = ["./", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "fonts/inter-tight.woff2", "vendor/motion.js", "icons/shot-plyo.webp", "icons/shot-mob.webp", "icons/shot-cardio.webp", "icons/shot-lift.webp"];
self.addEventListener("install", e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
// Pictures, fonts and scripts: saved copy at once, refreshed in the background.
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  // Preview pages change often while a design is being tried: always load them fresh.
  if (url.pathname.endsWith("-preview.html")) return;
  // The build marker is how an open app learns a newer version is out: never answer it from the saved copy.
  if (url.pathname.endsWith("/version.json")) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    // The page itself: newest copy when online (so an update shows the first time you open it), saved copy when offline or slow.
    if (e.request.mode === "navigate") return Promise.race([net, new Promise(done => setTimeout(() => done(hit), hit ? 2500 : 60000))]).then(r => r || hit || net);
    return hit || net;
  }));
});
