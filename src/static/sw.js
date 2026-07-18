/* ══════════════════════════════════════════════════════════════════════
   sw.js — service worker: precache the app shell, network-first (falling
   back to cache) for static assets, network-only for the API. Gives
   installability + offline shell without ever serving a stale bundle
   while the dev server is reachable.
   ══════════════════════════════════════════════════════════════════════ */

const CACHE = 'rpt-shell-v16';
const SHELL = [
    '/',
    '/index.html',
    '/style.css',
    '/api.js',
    '/i18n.js',
    '/runtime-config.js',
    '/plugin-runtime.js',
    '/slash-registry.js',
    '/plugin-center.js',
    '/adapters/base.js',
    '/adapters/llama-cpp.js',
    '/adapters/deepseek.js',
    '/adapters/index.js',
    '/setup.js',
    '/slash-commands.js',
    '/slash-command-parser.js',
    '/app.js',
    '/manifest.webmanifest',
    '/icon.svg',
    '/icon-192.png',
    '/icon-512.png',
    '/icon-maskable-512.png',
    '/apple-touch-icon.png',
];

// Backend routes must never be served from cache.
const API_PREFIXES = [
    '/session', '/sessions', '/scenario-defaults', '/scenarios', '/config',
    '/plugins', '/experiences', '/commands', '/presets', '/health', '/version',
    // Never cache /bootstrap: it carries the per-process access token, which
    // must never be persisted (Cache Storage lives on disk).
    '/bootstrap',
];

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

    // Static assets: network-first (always fresh while the server is up),
    // falling back to the cached copy only when the network fails — so
    // editing a file always takes effect on the next load, cache is purely
    // an offline fallback, not a source of stale bundles.
    event.respondWith(
        fetch(request)
            .then((res) => {
                if (res && res.ok) {
                    const clone = res.clone();
                    caches.open(CACHE).then((c) => c.put(request, clone));
                }
                return res;
            })
            .catch(() => caches.match(request))
    );
});
