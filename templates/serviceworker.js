{% load static %}
const CACHE_VERSION = 'v1';
const CACHE_NAME = `kiri-${CACHE_VERSION}`;

const urlsToCache = [
    '/',
    // --- Core App Assets ---
    "{% static 'css/output.css' %}",
    "{% static 'css/forms.css' %}",
    "{% static 'css/fonts.css' %}",
    "{% static 'js/main.js' %}",
    "{% static 'js/htmx.min.js' %}",
    "{% static 'js/theme_init.js' %}",
    "{% static 'js/pwa_install.js' %}",

    // --- Studio Core ---
    "{% static 'js/kiri_studio_core.js' %}",
    "{% static 'js/studio.py.worker.js' %}",
    "{% static 'js/studio.js.worker.js' %}",

    // --- PyStudio Engine (Pyodide v0.25.0) ---
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.asm.wasm',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/python_stdlib.zip',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide-lock.json',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/repodata.json',

    // --- JS Studio Engine ---
    'https://cdn.jsdelivr.net/npm/@webcontainer/api@1.1.0/+esm',
    // CRITICAL FIX: Cache fflate for unzipping in JS Studio
    'https://cdn.jsdelivr.net/npm/fflate@0.8.2/+esm',

    // --- Vendor Assets ---
    "{% static 'images/icons/icon-192x192.png' %}",
    "{% static 'images/icons/icon-512x512.png' %}",
    "{% static 'vendor/font-awesome/css/all.min.css' %}",
    "{% static 'vendor/font-awesome/webfonts/fa-solid-900.woff2' %}",
    "{% static 'vendor/font-awesome/webfonts/fa-regular-400.woff2' %}",
    "{% static 'vendor/font-awesome/webfonts/fa-brands-400.woff2' %}",
    "{% static 'vendor/inter/Inter-Regular.woff2' %}",
    "{% static 'vendor/inter/Inter-Medium.woff2' %}",
    "{% static 'vendor/inter/Inter-SemiBold.woff2' %}",
    "{% static 'vendor/inter/Inter-Bold.woff2' %}",
    "{% static 'fonts/jetbrainsmono-regular.woff2' %}",
    "{% static 'vendor/xterm/xterm.css' %}",
    "{% static 'vendor/xterm/xterm.js' %}",
    "{% static 'vendor/xterm/xterm-addon-fit.js' %}",
    "{% static 'vendor/alpine/alpine.min.js' %}"
];

// Install Event: Cache everything
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
            .then(() => self.skipWaiting())
    );
});

// Fetch Event: Smart Caching with Headers
self.addEventListener('fetch', event => {
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                })
                .catch(() => caches.match(event.request) || caches.match('/offline/'))
        );
    } else {
        event.respondWith(
            caches.match(event.request).then(response => {
                if (response) {
                    // Inject Security Headers for WASM/WebContainers
                    const newHeaders = new Headers(response.headers);
                    newHeaders.set('Cross-Origin-Resource-Policy', 'cross-origin');
                    newHeaders.set('Cross-Origin-Embedder-Policy', 'require-corp');
                    newHeaders.set('Cross-Origin-Opener-Policy', 'same-origin');

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