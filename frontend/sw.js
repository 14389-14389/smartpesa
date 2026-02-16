// SmartPesa Service Worker - Fixed Version
const CACHE_NAME = 'smartpesa-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/css/styles.css',
  '/js/app.js',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install service worker
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache opened');
        return cache.addAll(urlsToCache);
      })
  );
});

// IMPORTANT: Only cache static assets, NEVER API calls
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Skip API calls - let them go to network
  if (url.pathname.startsWith('/users/') || 
      url.pathname.startsWith('/businesses/') || 
      url.pathname.startsWith('/transactions/') || 
      url.pathname.startsWith('/forecast/') ||
      url.port === '8000') {
    // Just pass through to network, don't cache
    return;
  }
  
  // For static assets, try cache first
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

// Clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
