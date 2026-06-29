// Minimal service worker: cache the app shell so the PWA opens offline.
// API calls are always network-first (never cached) — results must be live.

const SHELL = "r2a-shell-v1";
const ASSETS = ["/", "/index.html", "/style.css", "/app.js", "/manifest.webmanifest", "/icon.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api/")) return; // live, uncached
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request))
  );
});
