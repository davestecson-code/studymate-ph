const CACHE_NAME = 'cramly-pwa-v1';
const SHELL = ['/offline', '/static/cramly-icon.svg', '/manifest.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('cramly-pwa-') && k !== CACHE_NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('message', event => {
  if (event.data === 'CLEAR_CRAMLY_CACHE') event.waitUntil(caches.delete(CACHE_NAME));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (request.method !== 'GET') {
    if (request.mode === 'navigate') event.respondWith(fetch(request).catch(async () => (await caches.match('/offline'))));
    return;
  }
  if (url.pathname === '/logout') {
    event.respondWith(fetch(request).finally(() => caches.delete(CACHE_NAME)));
    return;
  }
  // Do not retain API responses, password-reset pages, premium/payment pages, or uploaded files.
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/static/group_uploads/') || url.pathname.startsWith('/static/premium_receipts/') || url.pathname.startsWith('/reset-password/') || url.pathname.startsWith('/premium')) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).then(response => {
      if (response.ok && response.headers.get('content-type')?.includes('text/html')) {
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.put(request, copy)));
      }
      return response;
    }).catch(async () => (await caches.match(request)) || (await caches.match('/offline'))));
    return;
  }
  // Network first keeps assets fresh and uses saved copies when the device is offline.
  event.respondWith(fetch(request).then(response => {
    if (response.ok && response.type === 'basic') {
      const copy = response.clone();
      event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.put(request, copy)));
    }
    return response;
  }).catch(async () => (await caches.match(request)) || Response.error()));
});
