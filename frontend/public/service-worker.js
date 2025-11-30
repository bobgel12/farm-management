/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'farm-manager-v1';
const RUNTIME_CACHE = 'runtime-cache-v1';
const OFFLINE_URL = '/offline.html';

// Static assets to cache during installation
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
];

// API endpoints to cache for offline access
const API_CACHE_PATTERNS = [
  '/api/farms/',
  '/api/houses/',
  '/api/tasks/',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }

  // Handle static assets
  event.respondWith(handleStaticRequest(request));
});

// Handle API requests - network first, then cache
async function handleApiRequest(request) {
  const cache = await caches.open(RUNTIME_CACHE);

  try {
    const networkResponse = await fetch(request);
    
    // Cache successful GET requests
    if (request.method === 'GET' && networkResponse.ok) {
      const shouldCache = API_CACHE_PATTERNS.some(
        pattern => request.url.includes(pattern)
      );
      if (shouldCache) {
        cache.put(request, networkResponse.clone());
      }
    }
    
    return networkResponse;
  } catch (error) {
    // If network fails, try cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      console.log('[ServiceWorker] Serving API from cache:', request.url);
      return cachedResponse;
    }
    
    // Return offline response for API
    return new Response(
      JSON.stringify({ error: 'Offline', message: 'You are currently offline' }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

// Handle navigation requests - network first, then cache, then offline page
async function handleNavigationRequest(request) {
  try {
    const preloadResponse = await event.preloadResponse;
    if (preloadResponse) {
      return preloadResponse;
    }

    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match('/index.html');
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    return new Response('Offline', { status: 503 });
  }
}

// Handle static asset requests - cache first, then network
async function handleStaticRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[ServiceWorker] Fetch failed for:', request.url);
    
    // Return 404 for missing static assets
    return new Response('Not found', { status: 404 });
  }
}

// Handle background sync for offline submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-mortality') {
    event.waitUntil(syncMortality());
  }
  if (event.tag === 'sync-issues') {
    event.waitUntil(syncIssues());
  }
});

// Sync offline mortality records
async function syncMortality() {
  const db = await openDatabase();
  const pendingRecords = await getFromStore(db, 'pendingMortality');
  
  for (const record of pendingRecords) {
    try {
      await fetch('/api/mortality/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(record.data),
      });
      await removeFromStore(db, 'pendingMortality', record.id);
    } catch (error) {
      console.error('[ServiceWorker] Failed to sync mortality:', error);
    }
  }
}

// Sync offline issues
async function syncIssues() {
  const db = await openDatabase();
  const pendingIssues = await getFromStore(db, 'pendingIssues');
  
  for (const issue of pendingIssues) {
    try {
      await fetch('/api/issues/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(issue.data),
      });
      await removeFromStore(db, 'pendingIssues', issue.id);
    } catch (error) {
      console.error('[ServiceWorker] Failed to sync issue:', error);
    }
  }
}

// IndexedDB helpers
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('farm-manager-offline', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pendingMortality')) {
        db.createObjectStore('pendingMortality', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('pendingIssues')) {
        db.createObjectStore('pendingIssues', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

function getFromStore(db, storeName) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function removeFromStore(db, storeName, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(id);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Handle push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [100, 50, 100],
    data: data.url,
    actions: [
      { action: 'view', title: 'View' },
      { action: 'close', title: 'Close' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view' && event.notification.data) {
    event.waitUntil(
      clients.openWindow(event.notification.data)
    );
  }
});

