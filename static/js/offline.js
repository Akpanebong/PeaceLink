(function () {
  "use strict";

  const DB_NAME = "peacelink-offline";
  const STORE = "outbox";
  const installPrompt = document.querySelector("[data-install-prompt]");
  const toast = document.querySelector("[data-offline-toast]");
  let deferredInstallPrompt = null;
  let toastTimer;

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 6500);
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: "id" });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async function queueRequest(request) {
    const db = await openDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(request);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  }

  async function readQueue() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const request = tx.objectStore(STORE).getAll();
      request.onsuccess = () => resolve(request.result.sort((a, b) => a.createdAt - b.createdAt));
      request.onerror = () => reject(request.error);
    });
  }

  async function removeQueued(id) {
    const db = await openDb();
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(id);
  }

  async function syncQueue() {
    if (!navigator.onLine) return;
    let items;
    try { items = await readQueue(); } catch (_) { return; }
    let synced = 0;
    for (const item of items) {
      try {
        const response = await fetch(item.url, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "X-Offline-Queue-ID": item.id },
          body: item.body
        });
        if (!response.ok && response.status >= 500) break;
        if (response.ok || (response.status >= 400 && response.status < 403)) {
          await removeQueued(item.id);
          synced += 1;
        } else if (response.status === 401 || response.status === 403) break;
      } catch (_) { break; }
    }
    if (synced) showToast(`${synced} offline update${synced === 1 ? "" : "s"} synchronized.`);
  }

  function updateConnectivity() {
    const status = document.querySelector("[data-connectivity-status]");
    const label = document.querySelector("[data-connectivity-label]");
    const offline = !navigator.onLine;
    if (status) status.classList.toggle("is-offline", offline);
    if (label) label.textContent = offline ? "Offline" : "Online";
    if (offline) showToast("You’re offline. Supported updates will be saved on this device.");
    else syncQueue();
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post" || form.enctype === "multipart/form-data") return;
    const action = new URL(form.action || location.href, location.href);
    if (["/account/login/", "/account/logout/", "/account/language/"].includes(action.pathname)) return;
    if (navigator.onLine) return;
    event.preventDefault();
    const body = new URLSearchParams(new FormData(form)).toString();
    await queueRequest({ id: crypto.randomUUID(), url: action.href, body, createdAt: Date.now() });
    form.reset();
    showToast("Saved offline. PeaceLink will synchronize it when you’re back online.");
  });

  window.addEventListener("online", updateConnectivity);
  window.addEventListener("offline", updateConnectivity);
  updateConnectivity();
  syncQueue();

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    if (!localStorage.getItem("peacelink-install-dismissed") && installPrompt) installPrompt.hidden = false;
  });
  document.querySelector("[data-install-app]")?.addEventListener("click", async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    if (installPrompt) installPrompt.hidden = true;
  });
  document.querySelector("[data-dismiss-install]")?.addEventListener("click", () => {
    localStorage.setItem("peacelink-install-dismissed", "1");
    if (installPrompt) installPrompt.hidden = true;
  });
  window.addEventListener("appinstalled", () => { if (installPrompt) installPrompt.hidden = true; });

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(() => {});
})();
