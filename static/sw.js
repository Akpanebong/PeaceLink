const CACHE = "peacelink-shell-v2";
const CORE = ["/", "/static/css/peacelink.css", "/static/js/offline.js", "/static/manifest.json", "/static/offline.html", "/static/images/peacelink.png"];

self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting())));
self.addEventListener("activate", event => event.waitUntil(
  caches.keys().then(keys => Promise.all(
    keys.filter(key => key !== CACHE).map(key => caches.delete(key))
  )).then(() => self.clients.claim())
));
self.addEventListener("message", event => {
  if (event.data?.type !== "CACHE_URL") return;
  event.waitUntil((async () => {
    const response = await fetch(event.data.url, { credentials: "include" });
    if (response.ok) (await caches.open(CACHE)).put(event.data.url, response);
  })());
});
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const response = await fetch(event.request);
      if (response.ok && (event.request.mode === "navigate" || url.pathname.startsWith("/static/"))) cache.put(event.request, response.clone());
      return response;
    } catch (_) {
      return (await cache.match(event.request)) || (event.request.mode === "navigate" ? (await cache.match("/")) || cache.match("/static/offline.html") : Response.error());
    }
  })());
});
