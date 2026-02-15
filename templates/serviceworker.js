{% load static %}
const CACHE_VERSION = 'v2';
const CACHE_NAME = `kiri-${CACHE_VERSION}`;
const urlsToCache = [
    '/',
    '{% static "css/output.css" %}',
    '{% static "css/forms.css" %}',
    '{% static "css/fonts.css" %}',
    '{% static "js/htmx.min.js" %}',
    '{% static "js/theme_init.js" %}',
    '{% static "js/main.js" %}',
    '{% static "js/pwa_install.js" %}',
    '{% static "images/icons/icon-192x192.png" %}',
    '{% static "images/icons/icon-512x512.png" %}',
    '{% static "vendor/font-awesome/css/all.min.css" %}',
    '{% static "vendor/alpine/alpine.min.js" %}',
    '{% static "vendor/inter/Inter-Regular.woff2" %}',
    '{% static "vendor/inter/Inter-Medium.woff2" %}',
    '{% static "vendor/inter/Inter-SemiBold.woff2" %}',
    '{% static "vendor/inter/Inter-Bold.woff2" %}',
    '{% static "vendor/font-awesome/webfonts/fa-solid-900.woff2" %}',
    '{% static "vendor/font-awesome/webfonts/fa-regular-400.woff2" %}',
    '{% static "vendor/font-awesome/webfonts/fa-brands-400.woff2" %}',
    '{% static "vendor/font-awesome/webfonts/fa-solid-900.ttf" %}',
    '{% static "vendor/font-awesome/webfonts/fa-regular-400.ttf" %}',
    '{% static "vendor/font-awesome/webfonts/fa-brands-400.ttf" %}',
    '{% static "vendor/font-awesome/webfonts/fa-v4compatibility.woff2" %}',
    '{% static "vendor/font-awesome/webfonts/fa-v4compatibility.ttf" %}',
    '{% static "vendor/xterm/xterm.js.map" %}',
    '{% static "vendor/xterm/xterm-addon-fit.js.map" %}',
    '{% static "vendor/alpine/alpine.min.js.map" %}'
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
                    if (response) {
                        // Ensure cached response has CORP to satisfy COEP: require-corp
                        const newHeaders = new Headers(response.headers);
                        if (!newHeaders.has('Cross-Origin-Resource-Policy')) {
                            newHeaders.set('Cross-Origin-Resource-Policy', 'cross-origin');
                        }
                        return new Response(response.body, {
                            status: response.status,
                            statusText: response.statusText,
                            headers: newHeaders
                        });
                    }
                    return fetch(event.request);
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
