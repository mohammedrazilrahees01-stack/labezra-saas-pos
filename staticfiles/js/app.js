/* ============================================================
   LABEZRA ERP — MAIN JavaScript
   NOTE: Sidebar toggle logic lives entirely in partials/sidebar.html
         (its own IIFE). This file only handles topbar, calculator,
         dropdowns, alerts, loader, and table helpers.
   ============================================================ */


/* ===== TOPBAR HAMBURGER =====
   Handled entirely by sidebar.html's own IIFE — no code needed here.
   (sidebar.html wires both #sidebarToggle and #topbarMenuBtn to the
    same toggle logic so nothing fires twice.)
   ===== */


/* ===== DROPDOWNS (Topbar) ===== */
/* Handled by makeDropdown() inside IIFE below — v7 fix */


/* ===== LANGUAGE SELECT ===== */
(function () {
    var sel = document.getElementById('langSelect');
    if (!sel) return;
    var saved = localStorage.getItem('labezra_lang');
    if (saved) sel.value = saved;
    sel.addEventListener('change', function () {
        localStorage.setItem('labezra_lang', this.value);
        document.documentElement.dir = this.value === 'ar' ? 'rtl' : 'ltr';
    });
    if (saved === 'ar') document.documentElement.dir = 'rtl';
})();


/* ===== FLOATING CALCULATOR (open/close + drag) ===== */
(function () {

    var calcWidget  = document.getElementById('calcWidget');
    var calcOpenBtn = document.getElementById('calcOpen');
    var calcClose   = document.getElementById('calcClose');

    if (!calcWidget) return;

    /* ---- Open / Close ---- */
    if (calcOpenBtn) {
        calcOpenBtn.addEventListener('click', function () {
            calcWidget.classList.toggle('open');
        });
    }
    if (calcClose) {
        calcClose.addEventListener('click', function () {
            calcWidget.classList.remove('open');
        });
    }

    /* ---- Drag (mouse + touch) ---- */
    var header = calcWidget.querySelector('.calc-header');
    if (header) {
        var isDragging = false;
        var startX, startY, origLeft, origBottom;

        /* Helper: convert bottom/right positioning to top/left so CSS
           transitions don't fight us during drag.                       */
        function toTopLeft() {
            var rect = calcWidget.getBoundingClientRect();
            calcWidget.style.left   = rect.left + 'px';
            calcWidget.style.top    = rect.top  + 'px';
            calcWidget.style.right  = 'auto';
            calcWidget.style.bottom = 'auto';
        }

        /* MOUSE */
        header.addEventListener('mousedown', function (e) {
            isDragging = true;
            toTopLeft();
            startX = e.clientX - calcWidget.offsetLeft;
            startY = e.clientY - calcWidget.offsetTop;
            calcWidget.style.transition = 'none';
            e.preventDefault();
        });

        document.addEventListener('mousemove', function (e) {
            if (!isDragging) return;
            var nx = e.clientX - startX;
            var ny = e.clientY - startY;
            /* Keep inside viewport */
            nx = Math.max(0, Math.min(window.innerWidth  - calcWidget.offsetWidth,  nx));
            ny = Math.max(0, Math.min(window.innerHeight - calcWidget.offsetHeight, ny));
            calcWidget.style.left = nx + 'px';
            calcWidget.style.top  = ny + 'px';
        });

        document.addEventListener('mouseup', function () {
            isDragging = false;
            calcWidget.style.transition = '';
        });

        /* TOUCH */
        header.addEventListener('touchstart', function (e) {
            isDragging = true;
            toTopLeft();
            var t = e.touches[0];
            startX = t.clientX - calcWidget.offsetLeft;
            startY = t.clientY - calcWidget.offsetTop;
            calcWidget.style.transition = 'none';
        }, { passive: true });

        document.addEventListener('touchmove', function (e) {
            if (!isDragging) return;
            var t = e.touches[0];
            var nx = t.clientX - startX;
            var ny = t.clientY - startY;
            nx = Math.max(0, Math.min(window.innerWidth  - calcWidget.offsetWidth,  nx));
            ny = Math.max(0, Math.min(window.innerHeight - calcWidget.offsetHeight, ny));
            calcWidget.style.left = nx + 'px';
            calcWidget.style.top  = ny + 'px';
        }, { passive: true });

        document.addEventListener('touchend', function () {
            isDragging = false;
            calcWidget.style.transition = '';
        });
    }

    /* ---- Calculator Logic ---- */
    var display = document.getElementById('calcDisplay');
    if (!display) return;

    var expr = '';

    document.querySelectorAll('.calc-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var val = this.dataset.val;
            if (val === 'C') {
                expr = '';
                display.value = '';
            } else if (val === '⌫') {
                expr = expr.slice(0, -1);
                display.value = expr;
            } else if (val === '=') {
                try {
                    var result = Function('"use strict"; return (' + expr + ')')();
                    display.value = result;
                    expr = String(result);
                } catch (err) {
                    display.value = 'Error';
                    expr = '';
                }
            } else {
                expr += val;
                display.value = expr;
            }
        });
    });

})();


/* ===== ALERT AUTO-CLOSE ===== */
document.querySelectorAll('.alert-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
        var alert = this.closest('.alert');
        if (alert) alert.remove();
    });
});


/* ===== PAGE LOADER ===== */
window.addEventListener('load', function () {
    var loader = document.getElementById('globalLoader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(function () { loader.style.display = 'none'; }, 300);
    }
});


/* ===== TABLE SEARCH HELPER ===== */
function initTableSearch(inputId, rowSelector, cellSelector) {
    var input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('keyup', function () {
        var q = this.value.toLowerCase();
        document.querySelectorAll(rowSelector).forEach(function (row) {
            var text = cellSelector
                ? (row.querySelector(cellSelector) || row).textContent.toLowerCase()
                : row.textContent.toLowerCase();
            row.style.display = text.includes(q) ? '' : 'none';
        });
    });
}

/* ═══════════════════════════════════════════════════════════════
   LABEZRA ERP — PHASE 3 INTERACTIVE FEATURES
   Dark Mode | FAB | Search | Clock | Shortcuts | Page Transitions
═══════════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    /* ─── PAGE TRANSITION LOADER ─── */
    var loader = document.getElementById('globalLoader');
    function showLoader() {
        if (loader) { loader.classList.add('active'); }
    }
    function hideLoader() {
        if (loader) { loader.classList.remove('active'); }
    }
    // Intercept all internal nav clicks
    document.addEventListener('click', function (e) {
        var a = e.target.closest('a[href]');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href) return;
        // Skip: external, anchors, new tab, js:, download
        if (href.startsWith('http') || href.startsWith('#') || href.startsWith('javascript') ||
            a.target === '_blank' || a.hasAttribute('download')) return;
        showLoader();
    });
    // Hide on load/back
    window.addEventListener('pageshow', hideLoader);
    window.addEventListener('load', hideLoader);
    setTimeout(hideLoader, 4000); // Safety fallback

    /* ─── LIVE CLOCK (UAE / KSA Time) ─── */
    var clockEl = document.getElementById('clockTime');
    function updateClock() {
        if (!clockEl) return;
        try {
            var now = new Date();
            var opts = { timeZone: 'Asia/Dubai', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
            clockEl.textContent = now.toLocaleTimeString('en-AE', opts);
        } catch (e) {
            clockEl.textContent = new Date().toLocaleTimeString();
        }
    }
    updateClock();
    setInterval(updateClock, 1000);

    /* ─── DARK MODE ─── */
    var darkBtn = document.getElementById('darkModeBtn');
    var isDark = localStorage.getItem('labezra_dark') === '1';

    function applyDark(d) {
        document.body.classList.toggle('dark-mode', d);
        if (darkBtn) {
            var icon = darkBtn.querySelector('i');
            if (icon) {
                icon.className = d ? 'ri-sun-line' : 'ri-moon-line';
            }
        }
    }
    applyDark(isDark);
    if (darkBtn) {
        darkBtn.addEventListener('click', function () {
            isDark = !isDark;
            localStorage.setItem('labezra_dark', isDark ? '1' : '0');
            applyDark(isDark);
        });
    }

    /* ─── FLOATING ACTION BUTTON ─── */
    /* NOTE: FAB is fully handled by inline script in base.html (runs after this file loads) */
    /* window.closeFab and window.openFab are set there. Stub them here just in case. */
    window.closeFab = window.closeFab || function() {};
    window.openFab  = window.openFab  || function() {};

    /* ─── GLOBAL SEARCH ─── */
    var searchOverlay = document.getElementById('searchOverlay');
    var searchInput = document.getElementById('searchInput');
    var searchResults = document.getElementById('searchResults');
    var searchBtn = document.getElementById('searchBtn');

    // Search data — quick nav items
    var NAV_ITEMS = [
        { title: 'Dashboard', url: '/dashboard/', icon: 'ri-home-4-line', group: 'Pages' },
        { title: 'POS Screen', url: '/pos/', icon: 'ri-computer-line', group: 'Pages' },
        { title: 'Sales Invoices', url: '/pos/invoices/', icon: 'ri-file-list-3-line', group: 'Pages' },
        { title: 'Inventory', url: '/inventory/', icon: 'ri-box-3-line', group: 'Pages' },
        { title: 'Add Product', url: '/inventory/add/', icon: 'ri-add-box-line', group: 'Actions' },
        { title: 'Customers', url: '/customers/', icon: 'ri-group-line', group: 'Pages' },
        { title: 'Add Customer', url: '/customers/add/', icon: 'ri-user-add-line', group: 'Actions' },
        { title: 'Employees', url: '/employees/', icon: 'ri-team-line', group: 'Pages' },
        { title: 'Add Employee', url: '/employees/add/', icon: 'ri-user-add-line', group: 'Actions' },
        { title: 'Cashiers', url: '/cashiers/', icon: 'ri-user-star-line', group: 'Pages' },
        { title: 'Expenses', url: '/expenses/', icon: 'ri-wallet-3-line', group: 'Pages' },
        { title: 'Payroll', url: '/payroll/', icon: 'ri-bank-card-line', group: 'Pages' },
        { title: 'Daily Report', url: '/pos/daily-report/', icon: 'ri-calendar-check-line', group: 'Reports' },
        { title: 'Monthly Report', url: '/pos/monthly-report/', icon: 'ri-calendar-2-line', group: 'Reports' },
        { title: 'Shift Report', url: '/pos/shift-report/', icon: 'ri-time-line', group: 'Reports' },
        { title: 'Cashier Analytics', url: '/pos/cashier-analytics/', icon: 'ri-user-chart-line', group: 'Reports' },
        { title: 'VAT Return', url: '/pos/monthly-report/', icon: 'ri-government-line', group: 'Reports' },
        { title: 'Branches', url: '/settings/branches/', icon: 'ri-building-4-line', group: 'Pages' },
        { title: 'Company Settings', url: '/settings/company/', icon: 'ri-building-line', group: 'Settings' },
        { title: 'My Profile', url: '/profile/', icon: 'ri-user-3-line', group: 'Settings' },
        { title: 'Suppliers', url: '/inventory/suppliers/', icon: 'ri-store-2-line', group: 'Pages' },
        { title: 'Stock History', url: '/inventory/stock-history/', icon: 'ri-history-line', group: 'Pages' },
        { title: 'Purchases', url: '/inventory/purchases/', icon: 'ri-truck-line', group: 'Pages' },
        { title: 'B2B Invoices', url: '/accounting/business-invoices/', icon: 'ri-file-paper-2-line', group: 'Pages' },
        { title: 'Activity Log', url: '/activity/', icon: 'ri-pulse-line', group: 'Pages' },
        { title: 'Upgrade Plan', url: '/upgrade/', icon: 'ri-vip-crown-line', group: 'Settings' },
    ];

    function openSearch() {
        if (!searchOverlay) return;
        searchOverlay.classList.add('active');
        searchOverlay.setAttribute('aria-hidden', 'false');
        if (searchInput) { setTimeout(function () { searchInput.focus(); }, 50); }
    }
    function closeSearch() {
        if (!searchOverlay) return;
        searchOverlay.classList.remove('active');
        searchOverlay.setAttribute('aria-hidden', 'true');
        if (searchInput) searchInput.value = '';
        if (searchResults) searchResults.innerHTML = '<div class="search-empty"><i class="ri-search-2-line"></i><span>Start typing to search...</span></div>';
    }
    if (searchBtn) searchBtn.addEventListener('click', openSearch);
    if (searchOverlay) {
        searchOverlay.addEventListener('click', function (e) {
            if (e.target === searchOverlay) closeSearch();
        });
    }
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            var q = this.value.trim().toLowerCase();
            if (!q || q.length < 1) {
                searchResults.innerHTML = '<div class="search-empty"><i class="ri-search-2-line"></i><span>Start typing to search...</span></div>';
                return;
            }
            var filtered = NAV_ITEMS.filter(function (item) {
                return item.title.toLowerCase().includes(q) || item.group.toLowerCase().includes(q);
            });
            if (!filtered.length) {
                searchResults.innerHTML = '<div class="search-empty"><i class="ri-search-2-line"></i><span>No results found</span></div>';
                return;
            }
            // Group results
            var groups = {};
            filtered.forEach(function (item) {
                if (!groups[item.group]) groups[item.group] = [];
                groups[item.group].push(item);
            });
            var html = '';
            Object.keys(groups).forEach(function (g) {
                html += '<div class="search-group-label">' + g + '</div>';
                groups[g].forEach(function (item) {
                    html += '<a class="search-result-item" href="' + item.url + '">' +
                        '<div class="search-result-icon"><i class="' + item.icon + '"></i></div>' +
                        '<div><div class="search-result-title">' + item.title + '</div>' +
                        '<div class="search-result-sub">' + item.url + '</div></div></a>';
                });
            });
            searchResults.innerHTML = html;
        });
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeSearch();
        });
    }

    /* ─── KEYBOARD SHORTCUTS ─── */
    var shortcutsPanel = document.getElementById('shortcutsPanel');
    var shortcutsClose = document.getElementById('shortcutsClose');

    function openShortcuts() {
        if (shortcutsPanel) { shortcutsPanel.classList.add('active'); }
    }
    function closeShortcuts() {
        if (shortcutsPanel) { shortcutsPanel.classList.remove('active'); }
    }
    if (shortcutsClose) shortcutsClose.addEventListener('click', closeShortcuts);
    if (shortcutsPanel) {
        shortcutsPanel.addEventListener('click', function (e) {
            if (e.target === shortcutsPanel) closeShortcuts();
        });
    }

    // Global keyboard handler
    document.addEventListener('keydown', function (e) {
        var tag = document.activeElement ? document.activeElement.tagName : '';
        var typing = (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT');

        // Ctrl+K — Search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (searchOverlay && searchOverlay.classList.contains('active')) {
                closeSearch();
            } else {
                openSearch();
            }
        }
        // ? — Shortcuts
        if (e.key === '?' && !typing) {
            e.preventDefault();
            openShortcuts();
        }
        // ESC — close overlays
        if (e.key === 'Escape') {
            closeSearch();
            closeShortcuts();
        }
        // Alt+P — POS
        if (e.altKey && e.key === 'p') {
            e.preventDefault();
            window.location.href = '/pos/';
        }
        // Alt+D — Dashboard
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/dashboard/';
        }
        // Alt+I — New Invoice
        if (e.altKey && e.key === 'i') {
            e.preventDefault();
            window.location.href = '/sales/invoices/create/';
        }
    });

    /* ─── TOAST SYSTEM ─── */
    window.showToast = function (message, type) {
        var container = document.getElementById('toastContainer');
        if (!container) return;
        type = type || 'info';
        var icons = { success: 'ri-checkbox-circle-line', error: 'ri-error-warning-line',
                      warning: 'ri-alert-line', info: 'ri-information-line' };
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.innerHTML = '<i class="toast-icon ' + (icons[type] || icons.info) + '"></i>' +
            '<span class="toast-message">' + message + '</span>' +
            '<button class="toast-close" onclick="this.parentElement.remove()"><i class="ri-close-line"></i></button>';
        container.appendChild(toast);
        setTimeout(function () {
            toast.classList.add('toast-exit');
            setTimeout(function () { if (toast.parentElement) toast.remove(); }, 350);
        }, 4000);
    };

    /* ─── PROFILE & NOTIFICATION DROPDOWNS ─── */
    function makeDropdown(toggleId, dropdownId) {
        var toggle = document.getElementById(toggleId);
        var dropdown = document.getElementById(dropdownId);
        if (!toggle || !dropdown) return;
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = dropdown.classList.contains('open');
            // Close ALL dropdowns first
            document.querySelectorAll('.profile-dropdown, .notification-dropdown').forEach(function(d) {
                d.classList.remove('open');
            });
            // Then toggle this one
            if (!isOpen) dropdown.classList.add('open');
        });
    }
    makeDropdown('profileToggle', 'profileDropdown');
    makeDropdown('notificationToggle', 'notificationDropdown');
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.profile-wrapper') && !e.target.closest('.notification-wrapper')) {
            document.querySelectorAll('.profile-dropdown.open, .notification-dropdown.open').forEach(function (d) {
                d.classList.remove('open');
            });
        }
    });

    /* ─── MOBILE SIDEBAR ─── */
    var mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function () {
            if (window.sbOpenMobile) window.sbOpenMobile();
        });
    }

    /* ─── SCROLL ANIMATIONS ─── */
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08 });
        document.querySelectorAll('.kpi-card, .chart-card, .card, .qa-btn, .table-row-animate').forEach(function (el) {
            observer.observe(el);
        });
    }

    /* ─── RIPPLE EFFECT ON BUTTONS ─── */
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.btn, .qa-btn, .filter-pill, .fab-main');
        if (!btn) return;
        var circle = document.createElement('span');
        var rect = btn.getBoundingClientRect();
        var size = Math.max(rect.width, rect.height);
        circle.style.cssText = 'position:absolute;border-radius:50%;background:rgba(255,255,255,0.3);' +
            'width:' + size + 'px;height:' + size + 'px;' +
            'left:' + (e.clientX - rect.left - size / 2) + 'px;' +
            'top:' + (e.clientY - rect.top - size / 2) + 'px;' +
            'transform:scale(0);animation:ripple 0.5s ease;pointer-events:none;';
        btn.style.position = btn.style.position || 'relative';
        btn.style.overflow = 'hidden';
        btn.appendChild(circle);
        setTimeout(function () { if (circle.parentElement) circle.remove(); }, 600);
    });

    /* ─── ALERT AUTO-DISMISS ─── */
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            if (alert.parentElement) {
                alert.style.transition = 'opacity 0.4s, height 0.4s';
                alert.style.opacity = '0';
                setTimeout(function () { if (alert.parentElement) alert.remove(); }, 400);
            }
        }, 6000);
    });

    // Add ripple keyframes if not in CSS
    if (!document.getElementById('rippleStyle')) {
        var style = document.createElement('style');
        style.id = 'rippleStyle';
        style.textContent = '@keyframes ripple { to { transform: scale(2.5); opacity: 0; } }';
        document.head.appendChild(style);
    }

})();
