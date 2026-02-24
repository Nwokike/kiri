{% load static %}
const CACHE_VERSION = 'v2';
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

    // --- PWA Icons ---
    "{% static 'images/icons/icon-192x192.png' %}",
    "{% static 'images/icons/icon-512x512.png' %}",

    // --- Vendor: Fonts ---
    "{% static 'vendor/font-awesome/css/all.min.css' %}",
    "{% static 'vendor/font-awesome/webfonts/fa-solid-900.woff2' %}",
    "{% static 'vendor/font-awesome/webfonts/fa-regular-400.woff2' %}",
    "{% static 'vendor/font-awesome/webfonts/fa-brands-400.woff2' %}",
    "{% static 'vendor/inter/Inter-Regular.woff2' %}",
    "{% static 'vendor/inter/Inter-Medium.woff2' %}",
    "{% static 'vendor/inter/Inter-SemiBold.woff2' %}",
    "{% static 'vendor/inter/Inter-Bold.woff2' %}",

    // --- Vendor: Alpine.js ---
    "{% static 'vendor/alpine/alpine.min.js' %}",

    // --- Vendor: xterm (SQL Workbench terminal output) ---
    "{% static 'vendor/xterm/xterm.css' %}",
    "{% static 'vendor/xterm/xterm.js' %}",
    "{% static 'vendor/xterm/xterm-addon-fit.js' %}",

    // --- Tools: Pyodide (Python Studio — cached lazily below, not in install) ---
    // Pyodide 0.29.3 loaded on demand via tool pages, not pre-cached here
    // to avoid huge install payload (~10MB wasm). Listed for fetch-cache strategy.
];

// Pyodide files that are fetch-cached on use (not pre-cached in install)
const PYODIDE_BASE = 'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/';
const PYODIDE_CACHE_URLS = [
    `${PYODIDE_BASE}pyodide.js`,
    `${PYODIDE_BASE}pyodide.asm.wasm`,
    `${PYODIDE_BASE}python_stdlib.zip`,
    `${PYODIDE_BASE}pyodide-lock.json`,
];


// Install Event: Cache core app assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                // Graceful individual adds — a single 404 won't abort the whole SW
                return Promise.all(urlsToCache.map(url =>
                    cache.add(url).catch(e => console.warn(`SW: Could not cache ${url}`, e))
                ));
            })
            .then(() => self.skipWaiting())
    );
});


// Activate Event: Clear old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames =>
            Promise.all(
                cacheNames
                    .filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            )
        ).then(() => self.clients.claim())
    );
});


// Fetch Event: Network-first for navigation, cache-first for assets
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET or cross-origin API requests (GitHub API, Groq, etc.)
    if (request.method !== 'GET') return;
    if (url.pathname.startsWith('/projects/api/')) return;

    if (request.mode === 'navigate') {
        // Navigation: network-first, fall back to cached page, then /offline/
        event.respondWith(
            fetch(request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
                    return response;
                })
                .catch(() => caches.match(request).then(r => r || caches.match('/offline/')))
        );
    } else {
        // Assets: cache-first; inject CORP headers for WASM/SharedArrayBuffer
        event.respondWith(
            caches.match(request).then(cached => {
                if (cached) {
                    return injectCORPHeaders(cached);
                }
                return fetch(request).then(response => {
                    // Lazily cache Pyodide files on first use
                    if (PYODIDE_CACHE_URLS.some(u => request.url.startsWith(u))) {
                        caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
                    }
                    return response;
                });
            })
        );
    }
});


function injectCORPHeaders(response) {
    const headers = new Headers(response.headers);
    headers.set('Cross-Origin-Resource-Policy', 'cross-origin');
    headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
    headers.set('Cross-Origin-Opener-Policy', 'same-origin');
    return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
    });
}