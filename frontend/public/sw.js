// Network-only worker: never persist authenticated API responses or stale app shells.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('eduplatform-')).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
