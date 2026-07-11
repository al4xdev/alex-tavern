/* ══════════════════════════════════════════════════════════════════════
   sw.js — service worker: precache the app shell, cache-first for static
   assets, network-only for the API. Gives installability + offline shell.
   ══════════════════════════════════════════════════════════════════════ */

const CACHE = 'rpt-shell-v1';
const SHELL = [
    '/',
    '/index.html',
    '/style.css',
    '/api.js',
    '/setup.js',
    '/app.js',
    '/manifest.webmanifest',
    '/icon.svg',
    '/icon-192.png',
    '/icon-512.png',
    '/icon-maskable-512.png',
    '/apple-touch-icon.png',
];

// Backend routes must never be served from cache.
const API_PREFIXES = ['/session', '/defaults', '/health'];

function isApi(pathname) {
    return API_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE)
            .then((c) => c.addAll(SHELL))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    if (request.method !== 'GET') return; // POST turns/etc → straight to network

    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;
    if (isApi(url.pathname)) return; // let the API hit the network directly

    // Navigations: network-first, fall back to cached shell (offline).
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(() => caches.match('/'))
        );
        return;
    }

    // Static assets: cache-first, then network (and populate cache).
    event.respondWith(
        caches.match(request).then((cached) => {
            if (cached) return cached;
            return fetch(request).then((res) => {
                if (res && res.ok) {
                    const clone = res.clone();
                    caches.open(CACHE).then((c) => c.put(request, clone));
                }
                return res;
            });
        })
    );
});
