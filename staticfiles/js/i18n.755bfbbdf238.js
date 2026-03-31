/* ═══════════════════════════════════════════════════════════════
   LABEZRA ERP — i18n Engine v3
   Features:
   - Reads en.json / ar.json from /static/translations/
   - Applies data-i18n, data-i18n-placeholder, data-i18n-title attrs
   - Toggles RTL layout on <html> and loads rtl.css
   - Persists language choice in cookie + localStorage
   - Fires 'langChanged' custom event for pages to hook into
   - Watches DOM mutations to translate dynamic content
   - Updates topbar lang-btn active state
═══════════════════════════════════════════════════════════════ */

(function (win, doc) {
    'use strict';

    // ── Config ────────────────────────────────────────────────
    var STATIC_BASE = win.__STATIC_URL || '/static/';
    var TRANSLATIONS = {};
    var CURRENT_LANG = 'en';
    var RTL_LINK_ID = 'rtlStylesheet';
    var COOKIE_NAME = 'labezra_lang';
    var LS_KEY = 'labezra_lang';

    // ── Read cookie ───────────────────────────────────────────
    function getCookie(name) {
        var m = doc.cookie.match('(?:^|;)\\s*' + name + '=([^;]*)');
        return m ? decodeURIComponent(m[1]) : null;
    }

    function setCookie(name, value, days) {
        var d = new Date();
        d.setTime(d.getTime() + days * 86400000);
        doc.cookie = name + '=' + encodeURIComponent(value) +
            ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
    }

    function getSavedLang() {
        return getCookie(COOKIE_NAME) ||
               localStorage.getItem(LS_KEY) ||
               (navigator.language || 'en').split('-')[0];
    }

    // ── Load JSON (with cache) ────────────────────────────────
    function loadTranslations(lang, cb) {
        if (TRANSLATIONS[lang]) { cb(TRANSLATIONS[lang]); return; }

        var url = STATIC_BASE + 'translations/' + lang + '.json?v=3';
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.onload = function () {
            if (xhr.status === 200) {
                try {
                    TRANSLATIONS[lang] = JSON.parse(xhr.responseText);
                } catch (e) {
                    TRANSLATIONS[lang] = {};
                    console.warn('[i18n] Failed to parse ' + lang + '.json');
                }
            } else {
                TRANSLATIONS[lang] = {};
            }
            cb(TRANSLATIONS[lang]);
        };
        xhr.onerror = function () {
            TRANSLATIONS[lang] = {};
            cb({});
        };
        xhr.send();
    }

    // ── Translate a single element ────────────────────────────
    function t(key) {
        var dict = TRANSLATIONS[CURRENT_LANG] || {};
        return dict[key] || (TRANSLATIONS['en'] && TRANSLATIONS['en'][key]) || key;
    }

    function applyNode(el) {
        var key;
        // data-i18n → innerText/innerHTML (if no child elements) or just textContent
        key = el.getAttribute('data-i18n');
        if (key) {
            var translation = t(key);
            // Only update leaf-level text to not destroy child HTML
            if (el.children.length === 0) {
                el.textContent = translation;
            } else {
                // Update only the text node, not child elements
                var nodes = el.childNodes;
                for (var n = 0; n < nodes.length; n++) {
                    if (nodes[n].nodeType === 3) { // TEXT_NODE
                        nodes[n].textContent = translation;
                        break;
                    }
                }
            }
        }
        // data-i18n-placeholder → input placeholder
        key = el.getAttribute('data-i18n-placeholder');
        if (key) { el.placeholder = t(key); }
        // data-i18n-title → tooltip/title
        key = el.getAttribute('data-i18n-title');
        if (key) { el.title = t(key); }
        // data-i18n-label → aria-label
        key = el.getAttribute('data-i18n-label');
        if (key) { el.setAttribute('aria-label', t(key)); }
    }

    function applyAll(scope) {
        scope = scope || doc;
        var els = scope.querySelectorAll(
            '[data-i18n],[data-i18n-placeholder],[data-i18n-title],[data-i18n-label]'
        );
        for (var i = 0; i < els.length; i++) { applyNode(els[i]); }
    }

    // ── RTL / LTR Toggle ─────────────────────────────────────
    function applyRTL(lang) {
        var isRTL = (lang === 'ar');
        var html = doc.documentElement;
        html.setAttribute('dir', isRTL ? 'rtl' : 'ltr');
        html.setAttribute('lang', lang);
        html.classList.remove('ltr', 'rtl');
        html.classList.add(isRTL ? 'rtl' : 'ltr');
        doc.body.classList.toggle('rtl', isRTL);
        doc.body.classList.toggle('ltr', !isRTL);

        // Inject or remove RTL stylesheet
        var existing = doc.getElementById(RTL_LINK_ID);
        if (isRTL && !existing) {
            var link = doc.createElement('link');
            link.id = RTL_LINK_ID;
            link.rel = 'stylesheet';
            link.href = STATIC_BASE + 'css/rtl.css?v=3';
            doc.head.appendChild(link);
        } else if (!isRTL && existing) {
            existing.parentNode.removeChild(existing);
        }
    }

    // ── Update button active states ───────────────────────────
    function updateLangButtons(lang) {
        var btns = doc.querySelectorAll('.lang-btn');
        for (var i = 0; i < btns.length; i++) {
            var b = btns[i];
            var isActive = (b.getAttribute('data-lang') === lang);
            b.classList.toggle('active', isActive);
        }
        // Also update body lang class
        doc.body.classList.remove('lang-en', 'lang-ar');
        doc.body.classList.add('lang-' + lang);
    }

    // ── Set language ──────────────────────────────────────────
    function setLang(lang, persist) {
        if (!lang || (lang !== 'en' && lang !== 'ar')) lang = 'en';
        CURRENT_LANG = lang;
        if (persist !== false) {
            setCookie(COOKIE_NAME, lang, 365);
            try { localStorage.setItem(LS_KEY, lang); } catch (e) {}
        }
        applyRTL(lang);
        updateLangButtons(lang);

        loadTranslations(lang, function () {
            // Also preload English as fallback
            loadTranslations('en', function () {
                applyAll();
                // Fire custom event for pages to hook in
                var ev;
                try {
                    ev = new CustomEvent('langChanged', { detail: { lang: lang } });
                } catch (e) {
                    ev = doc.createEvent('CustomEvent');
                    ev.initCustomEvent('langChanged', true, true, { lang: lang });
                }
                doc.dispatchEvent(ev);
            });
        });
    }

    // ── Wire lang toggle buttons ──────────────────────────────
    function wireButtons() {
        doc.addEventListener('click', function (e) {
            var btn = e.target.closest('.lang-btn');
            if (!btn) return;
            var lang = btn.getAttribute('data-lang');
            if (lang && lang !== CURRENT_LANG) {
                setLang(lang, true);
            }
        });
    }

    // ── MutationObserver — translate dynamic content ──────────
    function watchMutations() {
        if (!win.MutationObserver) return;
        var observer = new MutationObserver(function (mutations) {
            for (var m = 0; m < mutations.length; m++) {
                var added = mutations[m].addedNodes;
                for (var n = 0; n < added.length; n++) {
                    var node = added[n];
                    if (node.nodeType === 1) { // ELEMENT_NODE
                        applyAll(node);
                        applyNode(node);
                    }
                }
            }
        });
        observer.observe(doc.body, { childList: true, subtree: true });
    }

    // ── Public API ────────────────────────────────────────────
    win.LabezraI18n = {
        setLang: setLang,
        t: function (key) { return t(key); },
        getCurrentLang: function () { return CURRENT_LANG; }
    };

    // ── Bootstrap ─────────────────────────────────────────────
    function bootstrap() {
        wireButtons();
        watchMutations();

        // Preload both languages in parallel
        var saved = getSavedLang();
        var startLang = (saved === 'ar') ? 'ar' : 'en';

        // Load English first (always as fallback)
        loadTranslations('en', function () {
            if (startLang === 'ar') {
                loadTranslations('ar', function () {
                    CURRENT_LANG = 'ar';
                    applyRTL('ar');
                    updateLangButtons('ar');
                    applyAll();
                });
            } else {
                CURRENT_LANG = 'en';
                applyRTL('en');
                updateLangButtons('en');
                applyAll();
            }
        });
    }

    if (doc.readyState === 'loading') {
        doc.addEventListener('DOMContentLoaded', bootstrap);
    } else {
        bootstrap();
    }

}(window, document));
