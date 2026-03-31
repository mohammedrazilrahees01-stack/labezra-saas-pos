/**
 * LABEZRA ERP — OFFLINE SYSTEM
 * IndexedDB-based offline support for POS transactions.
 * Syncs to server when connectivity is restored.
 */

(function () {
  'use strict';

  const DB_NAME = 'labezra_offline';
  const DB_VERSION = 1;
  const STORE_TRANSACTIONS = 'pending_transactions';
  const STORE_PRODUCTS = 'products_cache';
  const STORE_CUSTOMERS = 'customers_cache';
  const STORE_SETTINGS = 'settings';

  let db = null;
  let isOnline = navigator.onLine;

  // ─── INIT DB ───────────────────────────────────────────────────────
  function initDB() {
    return new Promise(function (resolve, reject) {
      if (!window.indexedDB) {
        console.warn('[Offline] IndexedDB not supported');
        resolve(null);
        return;
      }

      const req = indexedDB.open(DB_NAME, DB_VERSION);

      req.onerror = function () {
        console.error('[Offline] DB open error:', req.error);
        reject(req.error);
      };

      req.onsuccess = function () {
        db = req.result;
        console.log('[Offline] DB ready');
        resolve(db);
      };

      req.onupgradeneeded = function (e) {
        const _db = e.target.result;

        // Pending transactions store
        if (!_db.objectStoreNames.contains(STORE_TRANSACTIONS)) {
          const store = _db.createObjectStore(STORE_TRANSACTIONS, {
            keyPath: 'id',
            autoIncrement: true
          });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('synced', 'synced', { unique: false });
        }

        // Products cache
        if (!_db.objectStoreNames.contains(STORE_PRODUCTS)) {
          const ps = _db.createObjectStore(STORE_PRODUCTS, { keyPath: 'id' });
          ps.createIndex('barcode', 'barcode', { unique: false });
          ps.createIndex('name', 'name', { unique: false });
        }

        // Customers cache
        if (!_db.objectStoreNames.contains(STORE_CUSTOMERS)) {
          _db.createObjectStore(STORE_CUSTOMERS, { keyPath: 'id' });
        }

        // Settings
        if (!_db.objectStoreNames.contains(STORE_SETTINGS)) {
          _db.createObjectStore(STORE_SETTINGS, { keyPath: 'key' });
        }
      };
    });
  }

  // ─── STORE TRANSACTION OFFLINE ─────────────────────────────────────
  window.saveTransactionOffline = function (txData) {
    if (!db) return Promise.reject('DB not ready');
    return new Promise(function (resolve, reject) {
      const tx = db.transaction(STORE_TRANSACTIONS, 'readwrite');
      const store = tx.objectStore(STORE_TRANSACTIONS);
      const record = Object.assign({}, txData, {
        timestamp: Date.now(),
        synced: false,
        offline: true
      });
      const req = store.add(record);
      req.onsuccess = function () {
        console.log('[Offline] Transaction saved, id:', req.result);
        updatePendingBadge();
        resolve(req.result);
      };
      req.onerror = function () { reject(req.error); };
    });
  };

  // ─── GET PENDING COUNT ─────────────────────────────────────────────
  function getPendingCount() {
    if (!db) return Promise.resolve(0);
    return new Promise(function (resolve) {
      const tx = db.transaction(STORE_TRANSACTIONS, 'readonly');
      const store = tx.objectStore(STORE_TRANSACTIONS);
      const idx = store.index('synced');
      const req = idx.count(IDBKeyRange.only(false));
      req.onsuccess = function () { resolve(req.result); };
      req.onerror = function () { resolve(0); };
    });
  }

  // ─── UPDATE PENDING BADGE ──────────────────────────────────────────
  function updatePendingBadge() {
    getPendingCount().then(function (count) {
      const badge = document.getElementById('offlinePendingBadge');
      if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-flex' : 'none';
      }
      const syncEl = document.getElementById('syncStatusText');
      if (syncEl) {
        syncEl.textContent = count > 0 ? count + ' pending sync' : 'All synced';
      }
    });
  }

  // ─── CACHE PRODUCTS ────────────────────────────────────────────────
  window.cacheProducts = function (products) {
    if (!db || !Array.isArray(products)) return;
    const tx = db.transaction(STORE_PRODUCTS, 'readwrite');
    const store = tx.objectStore(STORE_PRODUCTS);
    products.forEach(function (p) { store.put(p); });
    console.log('[Offline] Cached', products.length, 'products');
  };

  // ─── SEARCH PRODUCTS OFFLINE ───────────────────────────────────────
  window.searchProductsOffline = function (query) {
    if (!db) return Promise.resolve([]);
    return new Promise(function (resolve) {
      const tx = db.transaction(STORE_PRODUCTS, 'readonly');
      const store = tx.objectStore(STORE_PRODUCTS);
      const results = [];
      store.openCursor().onsuccess = function (e) {
        const cursor = e.target.result;
        if (cursor) {
          const p = cursor.value;
          const q = query.toLowerCase();
          if (p.name.toLowerCase().includes(q) ||
              (p.barcode && p.barcode.includes(query))) {
            results.push(p);
          }
          cursor.continue();
        } else {
          resolve(results.slice(0, 20));
        }
      };
    });
  };

  // ─── GET PRODUCT BY BARCODE OFFLINE ───────────────────────────────
  window.getProductByBarcodeOffline = function (barcode) {
    if (!db) return Promise.resolve(null);
    return new Promise(function (resolve) {
      const tx = db.transaction(STORE_PRODUCTS, 'readonly');
      const store = tx.objectStore(STORE_PRODUCTS);
      const idx = store.index('barcode');
      const req = idx.get(barcode);
      req.onsuccess = function () { resolve(req.result || null); };
      req.onerror = function () { resolve(null); };
    });
  };

  // ─── SYNC TO SERVER ────────────────────────────────────────────────
  window.syncOfflineTransactions = function () {
    if (!db || !navigator.onLine) return;

    const tx = db.transaction(STORE_TRANSACTIONS, 'readwrite');
    const store = tx.objectStore(STORE_TRANSACTIONS);
    const idx = store.index('synced');
    const req = idx.getAll(IDBKeyRange.only(false));

    req.onsuccess = function () {
      const pending = req.result;
      if (!pending.length) return;

      setSyncStatus('syncing');
      console.log('[Offline] Syncing', pending.length, 'transactions...');

      // Get CSRF token
      const csrfToken = document.cookie.split(';')
        .find(function (c) { return c.trim().startsWith('csrftoken='); });
      const token = csrfToken ? csrfToken.split('=')[1].trim() : '';

      fetch('/pos/sync-offline/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': token
        },
        body: JSON.stringify({ transactions: pending })
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.synced) {
            // Mark all as synced
            const updateTx = db.transaction(STORE_TRANSACTIONS, 'readwrite');
            const updateStore = updateTx.objectStore(STORE_TRANSACTIONS);
            pending.forEach(function (item) {
              item.synced = true;
              updateStore.put(item);
            });
            setSyncStatus('synced');
            updatePendingBadge();
            if (typeof window.showToast === 'function') {
              window.showToast(data.synced + ' transactions synced successfully', 'success');
            }
          }
        })
        .catch(function (err) {
          console.error('[Offline] Sync failed:', err);
          setSyncStatus('error');
        });
    };
  };

  // ─── SYNC STATUS UI ────────────────────────────────────────────────
  function setSyncStatus(status) {
    const el = document.querySelector('.sync-indicator');
    if (!el) return;
    el.className = 'sync-indicator ' + status;
    const icons = { syncing: 'ri-loader-2-line', synced: 'ri-check-line', error: 'ri-error-warning-line' };
    const texts = { syncing: 'Syncing...', synced: 'Synced', error: 'Sync failed' };
    el.innerHTML = '<i class="' + (icons[status] || 'ri-cloud-line') + '"></i><span>' + (texts[status] || status) + '</span>';
  }

  // ─── ONLINE / OFFLINE EVENTS ───────────────────────────────────────
  function handleOnline() {
    isOnline = true;
    document.body.classList.remove('offline');
    const bar = document.getElementById('offlineBar');
    if (bar) bar.classList.remove('show');
    window.syncOfflineTransactions();
    if (typeof window.showToast === 'function') {
      window.showToast('Connection restored — syncing data', 'success');
    }
  }

  function handleOffline() {
    isOnline = false;
    document.body.classList.add('offline');
    const bar = document.getElementById('offlineBar');
    if (bar) bar.classList.add('show');
    if (typeof window.showToast === 'function') {
      window.showToast('You are offline — transactions will sync when connected', 'warning');
    }
  }

  window.addEventListener('online',  handleOnline);
  window.addEventListener('offline', handleOffline);

  if (!navigator.onLine) { handleOffline(); }

  // ─── AUTO-SYNC EVERY 30s WHEN ONLINE ──────────────────────────────
  setInterval(function () {
    if (navigator.onLine) window.syncOfflineTransactions();
  }, 30000);

  // ─── INIT ──────────────────────────────────────────────────────────
  initDB().then(function () {
    updatePendingBadge();
    // Auto-sync on page load if online
    if (navigator.onLine) {
      setTimeout(window.syncOfflineTransactions, 2000);
    }
  });

  // Expose for external use
  window.offlineDB = {
    isOnline: function () { return isOnline; },
    getPendingCount: getPendingCount,
    cacheProducts: window.cacheProducts,
    sync: window.syncOfflineTransactions
  };

})();
