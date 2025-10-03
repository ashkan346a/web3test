// Simple Service Worker for caching static assets
const CACHE_NAME = 'pharmaweb-v1';
const urlsToCache = [
  '/static/css/home.css',
  '/static/css/styles.css',
  '/static/favicon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      }
    )
  );
});