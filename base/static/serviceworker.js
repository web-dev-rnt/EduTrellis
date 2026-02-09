// Service Worker for EduTrellis PWA
const CACHE_VERSION = 'edutrellis-v1.0.0';
const CACHE_NAME = `edutrellis-cache-${CACHE_VERSION}`;

// Files to cache immediately on install
const STATIC_CACHE_URLS = [
  '/',
  '/static/css/style.css',
  '/static/js/javascript.js',
  '/static/js/pwainstall.js',
  '/static/img/icon-192x192.png',
  '/static/img/icon-512x512.png',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS).catch((error) => {
          console.warn('[ServiceWorker] Some assets failed to cache:', error);
          // Continue installation even if some assets fail
        });
      })
      .then(() => {
        console.log('[ServiceWorker] Skip waiting...');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[ServiceWorker] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[ServiceWorker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[ServiceWorker] Claiming clients...');
        return self.clients.claim();
      })
  );
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Skip Chrome extensions and browser-specific URLs
  if (request.url.includes('chrome-extension://') || 
      request.url.includes('moz-extension://') ||
      request.url.startsWith('chrome://')) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Don't cache non-successful responses
        if (!response || response.status !== 200 || response.type === 'error') {
          return response;
        }

        // Clone the response
        const responseClone = response.clone();
        
        // Cache successful responses (except POST requests)
        if (request.method === 'GET') {
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(request, responseClone);
            });
        }
        
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(request)
          .then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            
            // Return offline page for navigation requests
            if (request.mode === 'navigate') {
              return caches.match('/').then(response => {
                return response || new Response('Offline - Please check your connection', {
                  status: 503,
                  headers: { 'Content-Type': 'text/html' }
                });
              });
            }
            
            // Return a basic response for other requests
            return new Response('Network error occurred', {
              status: 408,
              headers: { 'Content-Type': 'text/plain' }
            });
          });
      })
  );
});

// Listen for messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background sync (for future features)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

function syncData() {
  // Implement data sync logic here
  return Promise.resolve();
}
