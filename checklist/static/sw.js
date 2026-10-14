// Guarda los archivos de la app para que abra aunque no haya señal.
const CACHE = "checklist-pmm-v3";
const ARCHIVOS = [
  "./", "./style.css", "./app.js", "./manifest.webmanifest",
  "./vendor/jspdf.umd.min.js", "./logo.jpg",
  "./golpe_lado_izq.jpg", "./golpe_lado_der.jpg", "./golpe_frente.jpg", "./golpe_trasera.jpg",
  "./icon-192.png", "./icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ARCHIVOS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return; // el envío del correo siempre va a la red
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
