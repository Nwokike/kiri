{% load static %}
const CACHE_NAME = 'kiri';
const urlsToCache = [
    '/',
    '{% static "css/output.css" %}',
    '{% static "css/forms.css" %}',
    '{% static "js/htmx.min.js" %}',
    '{% static "js/theme_init.js" %}',
    '{% static "js/theme_toggle.js" %}',
    '{% static "js/universal_translator.js" %}',
    '{% static "js/pwa_install.js" %}',
    '{% static "images/icons/icon-192x192.png" %}',
    '{% static "images/icons/icon-512x512.png" %}',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@500;700&display=swap'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    // HTML: Network First, then Cache
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                })
                .catch(() => {
                    return caches.match(event.request);
                })
        );
    } else {
        // Assets: Cache First, then Network
        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    return response || fetch(event.request);
                })
        );
    }
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(cacheName => cacheName !== CACHE_NAME)
                    .map(cacheName => caches.delete(cacheName))
            );
        })
    );
});
