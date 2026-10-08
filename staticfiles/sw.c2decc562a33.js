/**
 * Free Food Progressive Web App — Production Service Worker
 * Version: 1.0.0
 */

const CACHE_VERSION = 'freefood-pwa-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const OFFLINE_CACHE = `${CACHE_VERSION}-offline`;

// Critical assets to pre-cache on install
const PRECACHE_ASSETS = [
  '/offline/',
  '/static/css/base.css',
  '/static/css/components.css',
  '/static/css/pages.css',
  '/static/css/notifications.css',
  '/static/js/main.js',
  '/static/js/geolocation.js',
  '/static/js/map.js',
  '/static/js/notifications.js',
  '/static/manifest.json',
  '/static/images/icons/icon-192.png',
  '/static/images/icons/icon-512.png',
  '/static/images/icons/icon-maskable-512.png',
  '/static/images/icons/apple-touch-icon.png',
  '/static/images/icons/favicon.png',
  '/static/images/default_food.jpg'
];

// Paths that must NEVER be cached (Dynamic / Authenticated / Administrative)
const NEVER_CACHE_PATTERNS = [
  /^\/admin\//,
  /^\/django-admin\//,
  /^\/login\//,
  /^\/logout\//,
  /^\/register\//,
  /^\/password-reset/,
  /^\/notifications\/api\//,
  /^\/api\/locations\//,
  /\/live-status\//,
  /\/claim-rescue\//,
  /\/favorite\//,
  /\/report\//
];

// 1. Install Event — Pre-cache static shell & offline fallback
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      // Precache critical resources with individual error resilience
      return Promise.allSettled(
        PRECACHE_ASSETS.map((url) =>
          fetch(url, { cache: 'no-cache' })
            .then((response) => {
              if (response.ok) {
                return cache.put(url, response);
              }
            })
            .catch((err) => {
              console.warn(`[SW] Precache skipped for ${url}:`, err);
            })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// 2. Activate Event — Clean up outdated caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => (cacheName.startsWith('dona-pwa-') || (cacheName.startsWith('freefood-pwa-') && cacheName !== STATIC_CACHE && cacheName !== OFFLINE_CACHE)))
          .map((cacheName) => {
            console.log(`[SW] Removing outdated cache: ${cacheName}`);
            return caches.delete(cacheName);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch Event — Safe Caching Strategies
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Strictly ignore non-GET requests (POST, PUT, DELETE, PATCH, etc.)
  if (request.method !== 'GET') {
    return;
  }

  // Strictly ignore chrome-extension or other non-HTTP schemes
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Strictly bypass sensitive, authenticated, and administrative routes
  const isNeverCache = NEVER_CACHE_PATTERNS.some((pattern) => pattern.test(url.pathname));
  if (isNeverCache) {
    return;
  }

  // Strategy A: HTML Page Navigation Requests -> Network-First with Offline Fallback
  if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          // If valid response, return it
          return networkResponse;
        })
        .catch(async () => {
          // Network failed (offline) -> Return pre-cached branded offline fallback
          const cache = await caches.open(STATIC_CACHE);
          const cachedOffline = await cache.match('/offline/');
          if (cachedOffline) {
            return cachedOffline;
          }
          // Fallback minimal offline response if cache was somehow missed
          return new Response(
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Offline — Free Food</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:sans-serif;text-align:center;padding:3rem 1rem;color:#111827;}h1{color:#dc2626;}button{background:#dc2626;color:#fff;border:none;padding:12px 20px;border-radius:10px;font-size:1rem;cursor:pointer;margin-top:1rem;}</style></head><body><h1>Connection Lost</h1><p>Free Food needs an internet connection to discover live food events.</p><button onclick="window.location.reload()">Retry Connection</button></body></html>',
            { headers: { 'Content-Type': 'text/html' } }
          );
        })
    );
    return;
  }

  // Strategy B: Static Assets (CSS, JS, Fonts, Images, Icons) -> Stale-While-Revalidate
  const isStaticAsset = (
    url.pathname.startsWith('/static/') ||
    url.hostname.includes('unpkg.com') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.jpg') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.ico')
  );

  if (isStaticAsset) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200 && networkResponse.type !== 'opaque') {
              const responseToCache = networkResponse.clone();
              caches.open(STATIC_CACHE).then((cache) => {
                cache.put(request, responseToCache);
              });
            }
            return networkResponse;
          })
          .catch(() => {
            // Network fetch failed, cache match (if any) will be returned
          });

        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // Default: Pass through to network
  event.respondWith(fetch(request));
});

// 4. Message Event — Manual update trigger / skip waiting
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
