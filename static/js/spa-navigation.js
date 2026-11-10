
 // ==========================================
 // SMPU SPA NAVIGATION
 // PREMIUM EMERALD PAGE LOADING SYSTEM
 // Sidebar + Header tetap terpisah
 // ==========================================

 (() => {
     "use strict";

     console.log(
         "%c SMPU SPA + EMERALD LOADER ",
         "background:#047857;color:white;padding:6px;font-weight:bold"
     );

     const CONTENT_ID = "spa-content";
     const PAGE_CONTENT_ID = "spa-page-content";
     const LOADER_ID = "spa-page-loader";
     const CONNECTION_ID = "spa-connection-state";

     let navigating = false;
     let currentPagePath = location.pathname;
     let navigationController = null;
     let navigationSequence = 0;
     let retryUrl = null;

     const loadedScripts = new Map();

     // ==========================================
     // ELEMENT
     // ==========================================

     function getContent() {
         return document.getElementById(CONTENT_ID);
     }

     function getPageContent() {
         return document.getElementById(PAGE_CONTENT_ID);
     }

     function getLoader() {
         return document.getElementById(LOADER_ID);
     }

     function getConnectionState() {
         return document.getElementById(CONNECTION_ID);
     }

     // ==========================================
    // SPA LOADER POSITION CONTROLLER
    // ==========================================

    function updateSpaLoaderPosition() {

        const sidebar = document.getElementById('mainSidebar');

        const sidebarVisible =
            window.innerWidth > 1024 &&
            sidebar &&
            !sidebar.classList.contains('hidden-sidebar');

        const sidebarWidth = sidebarVisible
            ? sidebar.getBoundingClientRect().width
            : 0;

        document.documentElement.style.setProperty(
            '--spa-content-left',
            `${sidebarWidth}px`
        );
    }

    // Perubahan ukuran layar
    window.addEventListener(
        'resize',
        updateSpaLoaderPosition
    );

    // Perubahan kondisi sidebar
    const sidebarObserver = new MutationObserver(() => {
        updateSpaLoaderPosition();
    });

    function observeSidebarPosition() {

        const sidebar = document.getElementById('mainSidebar');

        if (!sidebar) return;

        sidebarObserver.observe(sidebar, {
            attributes: true,
            attributeFilter: ['class', 'style']
        });

        updateSpaLoaderPosition();
    }

     function getPageUrl(url) {
         return new URL(url, location.origin);
     }

     function dispatchPageEvent(name, detail = {}) {
         document.dispatchEvent(
             new CustomEvent(name, { detail })
         );
     }

     function normalizePath(path) {
         return path.replace(/\/+$/, "") || "/";
     }

     // ==========================================
     // LOADING STATE
     // ==========================================

     const loadingState = {
         progress: 0,
         timer: null,
         finishTimer: null,
         active: false,
         startedAt: 0
     };

     function setLoaderProgress(value) {
         const progress = Math.max(
             0,
             Math.min(100, Math.round(value))
         );

         loadingState.progress = progress;

         const bar = document.getElementById(
             "spa-loader-progress-bar"
         );

         const percent = document.getElementById(
             "spa-loader-percent"
         );

         if (bar) {
             bar.style.width = progress + "%";
         }

         if (percent) {
             percent.textContent = progress + "%";
         }
     }

     function setLoaderText(title, subtitle, status) {
         const titleEl = document.getElementById(
             "spa-loader-title"
         );

         const subtitleEl = document.getElementById(
             "spa-loader-subtitle"
         );

         const statusEl = document.getElementById(
             "spa-loader-status"
         );

         if (titleEl) titleEl.textContent = title;
         if (subtitleEl) subtitleEl.textContent = subtitle;
         if (statusEl) statusEl.textContent = status;
     }

     function clearLoadingTimers() {
         if (loadingState.timer) {
             clearInterval(loadingState.timer);
             loadingState.timer = null;
         }

         if (loadingState.finishTimer) {
             clearTimeout(loadingState.finishTimer);
             loadingState.finishTimer = null;
         }
     }

     function startLoading() {
        console.log("[SMPU LOADER] startLoading dipanggil");
         const loader = getLoader();
         const content = getContent();

         if (!loader || !content) return;

         clearLoadingTimers();

         loadingState.active = true;
         loadingState.progress = 0;
         loadingState.startedAt = performance.now();

         loader.classList.remove("is-leaving");
         loader.classList.add("is-active");

         loader.setAttribute("aria-hidden", "false");

         content.classList.add("spa-loading");

         setLoaderProgress(0);

         setLoaderText(
             "Menyiapkan halaman",
         "Menghubungkan ke sistem SMPU...",
         "Menghubungkan halaman"
         );

         // Progress visual:
         // Tidak mengklaim render selesai sebelum benar-benar siap.
         loadingState.timer = setInterval(() => {

             if (!loadingState.active) return;

             const progress = loadingState.progress;

             let nextProgress;

             if (progress < 35) {
                 nextProgress = progress + 3;
             } else if (progress < 70) {
                 nextProgress = progress + 1.5;
             } else if (progress < 88) {
                 nextProgress = progress + .5;
             } else {
                 nextProgress = progress + .12;
             }

             setLoaderProgress(Math.min(92, nextProgress));

             if (progress < 35) {
                 setLoaderText(
                     "Menyiapkan halaman",
                     "Menghubungkan ke sistem SMPU...",
                     "Menghubungkan halaman"
                 );
             } else if (progress < 70) {
                 setLoaderText(
                     "Memuat konten",
                     "Menyiapkan tampilan halaman...",
                     "Memuat konten"
                 );
             } else {
                 setLoaderText(
                     "Menyempurnakan tampilan",
                     "Menyiapkan komponen halaman...",
                     "Menyiapkan tampilan"
                 );
             }

         }, 120);

     }

     function hideLoading() {
         const loader = getLoader();
         const content = getContent();

         clearLoadingTimers();

         loadingState.active = false;

         if (!loader) {
             if (content) {
                 content.classList.remove("spa-loading");
             }
             return;
         }

         setLoaderProgress(100);

         setLoaderText(
             "Halaman siap",
             "Selamat datang di SMP Unggulan Hamzanwadi",
             "Selesai"
         );

         loader.classList.add("is-leaving");

         loadingState.finishTimer = setTimeout(() => {

             loader.classList.remove("is-active");
             loader.classList.remove("is-leaving");

             loader.setAttribute("aria-hidden", "true");

             if (content) {
                 content.classList.remove("spa-loading");
             }

         }, 320);

     }

     // ==========================================
     // CONNECTION STATE
     // ==========================================

     function showConnectionError(options = {}) {
         const state = getConnectionState();
         const content = getContent();

         const loader = getLoader();

        if (loader) {
            loader.classList.remove("is-active");
            loader.classList.remove("is-leaving");
            loader.setAttribute("aria-hidden", "true");
        }

         if (!state) return;

         clearLoadingTimers();

         loadingState.active = false;

         if (content) {
             content.classList.remove("spa-loading");
         }

         state.classList.add("is-active");
         state.setAttribute("aria-hidden", "false");

         const title = document.getElementById(
             "spa-connection-title"
         );

         const message = document.getElementById(
             "spa-connection-message"
         );

         const retryButton = document.getElementById(
             "spa-retry-button"
         );

         if (options.offline || !navigator.onLine) {

             if (title) {
                 title.textContent = "No Connection";
             }

             if (message) {
                 message.textContent =
                     "Koneksi internet terputus. " +
                     "Periksa jaringan Anda lalu coba kembali.";
             }

         } else {

             if (title) {
                 title.textContent = "Halaman tidak dapat dimuat";
             }

             if (message) {
                 message.textContent =
                     "Server tidak dapat menyelesaikan permintaan. " +
                     "Silakan coba kembali beberapa saat lagi.";
             }

         }

         if (retryButton) {
             retryButton.disabled = false;
             retryButton.innerHTML =
                 '<i class="fa-solid fa-rotate-right"></i>' +
                 '<span>Coba Lagi</span>';
         }

     }

     function hideConnectionError() {
         const state = getConnectionState();

         if (!state) return;

         state.classList.remove("is-active");
         state.setAttribute("aria-hidden", "true");
     }

     // ==========================================
     // SIDEBAR ACTIVE MENU
     // ==========================================

     function updateSidebarActive(url) {

         const sidebar = document.querySelector(
             "#mainSidebar .sidebar-menu-wrapper"
         );

         const posisiScroll = sidebar
             ? sidebar.scrollTop
             : 0;

         const currentPath = normalizePath(
             getPageUrl(url).pathname
         );

         document.querySelectorAll(
             "#mainSidebar .sidebar-menu .menu-link"
         ).forEach(link => {

             try {

                 const linkPath = normalizePath(
                     getPageUrl(link.href).pathname
                 );

                 link.classList.toggle(
                     "active",
                     linkPath === currentPath
                 );

             } catch (error) {
                 console.warn(
                     "Gagal menentukan menu aktif:",
                     error
                 );
             }

         });

         if (sidebar) {
             sidebar.scrollTop = posisiScroll;
         }

     }

     // ==========================================
     // SIDEBAR SCROLL PERSISTENCE
     // ==========================================

     const SIDEBAR_SCROLL_KEY = "smpu_sidebar_scroll";

     function getSidebarScrollElement() {
         return document.querySelector(
             "#mainSidebar .sidebar-menu-wrapper"
         );
     }

     function saveSidebarScroll() {

         const sidebar = getSidebarScrollElement();

         if (!sidebar) return;

         try {

             sessionStorage.setItem(
                 SIDEBAR_SCROLL_KEY,
                 String(sidebar.scrollTop)
             );

         } catch (error) {
             console.warn(
                 "Gagal menyimpan scroll sidebar:",
                 error
             );
         }

     }

     function restoreSidebarScroll() {

         const sidebar = getSidebarScrollElement();

         if (!sidebar) return;

         try {

             const posisi = Number(
                 sessionStorage.getItem(
                     SIDEBAR_SCROLL_KEY
                 ) || 0
             );

             sidebar.style.scrollBehavior = "auto";
             sidebar.scrollTop = posisi;

         } catch (error) {
             console.warn(
                 "Gagal memulihkan scroll sidebar:",
                 error
             );
         }

     }

     // ==========================================
     // LINK VALIDATION
     // ==========================================

     function isPageLink(link, event) {

         if (!link || !link.href) return false;

         if (
             event.defaultPrevented ||
             event.button !== 0
         ) return false;

         if (
             event.ctrlKey ||
             event.shiftKey ||
             event.altKey ||
             event.metaKey
         ) return false;

         if (
             link.target &&
             link.target !== "_self"
         ) return false;

         if (link.hasAttribute("download")) return false;
         if (link.hasAttribute("data-no-spa")) return false;
         if (link.hasAttribute("data-bs-toggle")) return false;

         const url = getPageUrl(link.href);

         if (url.origin !== location.origin) return false;

         if (
             !["http:", "https:"].includes(url.protocol)
         ) return false;

         if (
             url.pathname === location.pathname &&
             url.search === location.search &&
             url.hash
         ) return false;

         if (
             url.pathname === location.pathname &&
             url.search === location.search &&
             url.hash === location.hash
         ) return false;

         return true;

     }

     // ==========================================
     // PAGE CSS
     // ==========================================

     function updatePageStyles(doc, newContent) {

         document.querySelectorAll(
             "[data-spa-page-style]"
         ).forEach(el => el.remove());

         const styles = [];

         // CSS eksternal HEAD
         doc.head.querySelectorAll(
             'link[rel="stylesheet"]:not([data-spa-global])'
         ).forEach(el => {
             styles.push(el.cloneNode(true));
         });

         // CSS inline HEAD
         doc.head.querySelectorAll(
             "style[data-spa-page-style]"
         ).forEach(el => {
             styles.push(el.cloneNode(true));
         });

         // CSS eksternal konten
         newContent.querySelectorAll(
             'link[rel="stylesheet"]:not([data-spa-global])'
         ).forEach(el => {
             styles.push(el.cloneNode(true));
         });

         // CSS inline konten
         newContent.querySelectorAll(
             "style:not([data-spa-global])"
         ).forEach(el => {
             styles.push(el.cloneNode(true));
         });

         const seen = new Set();

         styles.forEach(style => {

             if (style.tagName === "LINK") {

                 const href = getPageUrl(style.href).href;

                 if (seen.has(href)) return;

                 seen.add(href);

             }

             style.dataset.spaPageStyle = "true";

             document.head.appendChild(style);

         });

         newContent.querySelectorAll(
             'link[rel="stylesheet"], style'
         ).forEach(el => el.remove());

     }

     // ==========================================
     // SCRIPT EXTERNAL
     // ==========================================

     function loadExternalScript(src) {

         const absoluteSrc = getPageUrl(src).href;

         const existingGlobal = Array.from(
             document.querySelectorAll("script[src]")
         ).find(script => {

             return (
                 getPageUrl(script.src).href === absoluteSrc &&
                 script.hasAttribute("data-spa-global")
             );

         });

         if (existingGlobal) {
             return Promise.resolve();
         }

         if (loadedScripts.has(absoluteSrc)) {
             return loadedScripts.get(absoluteSrc);
         }

         const promise = new Promise((resolve, reject) => {

             const script = document.createElement("script");

             script.src = absoluteSrc;
             script.async = false;

             script.dataset.spaPageScript = "true";

             script.onload = () => resolve();

             script.onerror = () => {

                 loadedScripts.delete(absoluteSrc);

                 reject(
                     new Error(
                         "Gagal memuat script: " + absoluteSrc
                     )
                 );

             };

             document.body.appendChild(script);

         });

         loadedScripts.set(absoluteSrc, promise);

         return promise;

     }

     // ==========================================
     // PAGE SCRIPT
     // ==========================================

     async function executePageScripts(doc, newContent) {

         const scripts = Array.from(
             doc.querySelectorAll(
                 "#spa-content script, " +
                 "#spa-page-content script, " +
                 "body > script, head > script"
             )
         );

         for (const oldScript of scripts) {

             if (
                 oldScript.hasAttribute("data-spa-global")
             ) {
                 continue;
             }

             const type = (
                 oldScript.type || ""
             ).toLowerCase();

             if (
                 type &&
                 type !== "text/javascript" &&
                 type !== "application/javascript" &&
                 type !== "module"
             ) {
                 continue;
             }

             if (oldScript.src) {

                 await loadExternalScript(
                     oldScript.src
                 );

                 continue;

             }

             if (type === "module") {

                 const script = document.createElement(
                     "script"
                 );

                 script.type = "module";

                 script.textContent =
                     oldScript.textContent;

                 document.body.appendChild(script);

                 continue;

             }

             const script = document.createElement(
                 "script"
             );

             script.textContent =
                 "{\n" +
                 oldScript.textContent +
                 "\n}";

             document.body.appendChild(script);

             script.remove();

         }

     }

     // ==========================================
     // FETCH + PARSE
     // ==========================================

     async function fetchPage(url, signal) {

         const response = await fetch(url, {
             method: "GET",

             headers: {
                 "X-SPA-Request": "true",
                 "X-Requested-With": "XMLHttpRequest"
             },

             credentials: "same-origin",

             signal
         });

         if (!response.ok) {

             const error = new Error(
                 "HTTP " + response.status
             );

             error.httpStatus = response.status;

             throw error;

         }

         const html = await response.text();

         const parser = new DOMParser();

         const doc = parser.parseFromString(
             html,
             "text/html"
         );

         const newContent = doc.getElementById(
             CONTENT_ID
         );

         if (!newContent) {

             const error = new Error(
                 "spa-content tidak ditemukan"
             );

             error.fullPageFallback = true;

             throw error;

         }

         // Layout baru menggunakan wrapper page-content.
         const pageContent = newContent.querySelector(
             "#" + PAGE_CONTENT_ID
         );

         return {
             response,
             doc,
             newContent,
             pageContent: pageContent || newContent
         };

     }

     // ==========================================
     // NAVIGASI UTAMA
     // ==========================================

     async function navigateTo(url, options = {}) {

         if (navigating) {

             // Navigasi terbaru menggantikan navigasi lama.
             if (navigationController) {
                 navigationController.abort();
             }

         }

         const currentContent = getContent();

         if (!currentContent) {

             location.href = url;

             return;

         }

         const targetUrl = getPageUrl(url);

         if (targetUrl.origin !== location.origin) {

             location.href = url;

             return;

         }

         const sequence = ++navigationSequence;

         navigating = true;

         navigationController = new AbortController();

         retryUrl = targetUrl.href;

         hideConnectionError();

         startLoading();

         try {

             // ----------------------------------
             // FETCH HTML
             // ----------------------------------

             const result = await fetchPage(
                 targetUrl.href,
                 navigationController.signal
             );

             if (sequence !== navigationSequence) {
                 return;
             }

             const {
                 response,
                 doc,
                 newContent,
                 pageContent
             } = result;

             // ----------------------------------
             // BEFORE PAGE UNLOAD
             // ----------------------------------

             dispatchPageEvent(
                 "spa:before-page-unload",
                 {
                     url: targetUrl.href
                 }
             );

             // ----------------------------------
             // CSS
             // ----------------------------------

             updatePageStyles(
                 doc,
                 newContent
             );

             // ----------------------------------
             // HTML
             // ----------------------------------

             const currentPageContent = getPageContent();

             if (!currentPageContent) {

                 location.href = response.url || targetUrl.href;

                 return;

             }

             currentPageContent.innerHTML =
                 pageContent.innerHTML;

             // ----------------------------------
             // TITLE
             // ----------------------------------

             if (doc.title) {
                 document.title = doc.title;
             }

             // ----------------------------------
             // URL
             // ----------------------------------

             const finalUrl =
                 response.url || targetUrl.href;

             const finalPath =
                 getPageUrl(finalUrl).pathname;

             currentPagePath = finalPath;

             if (!options.popstate) {

                 history.pushState(
                     {
                         spaPage: true,
                         path: finalPath
                     },
                     "",
                     finalUrl
                 );

             }

             // ----------------------------------
             // SIDEBAR
             // ----------------------------------

             updateSidebarActive(finalUrl);

             // ----------------------------------
             // PAGE SCROLL
             // ----------------------------------

             window.scrollTo({
                 top: 0,
                 behavior: "instant"
             });

             // ----------------------------------
             // EXECUTE PAGE SCRIPT
             // ----------------------------------

             setLoaderText(
                 "Menyiapkan halaman",
                 "Menjalankan komponen halaman...",
                 "Menyiapkan komponen"
             );

             await executePageScripts(
                 doc,
                 newContent
             );

             if (sequence !== navigationSequence) {
                 return;
             }

             // ----------------------------------
             // PAGE LOADED
             // ----------------------------------

             dispatchPageEvent(
                 "spa:page-loaded",
                 {
                     url: finalUrl,
                     path: finalPath,
                     initial: false
                 }
             );

             // ----------------------------------
             // LOADING COMPLETE
             // ----------------------------------

             hideLoading();

         } catch (error) {

             if (sequence !== navigationSequence) {
                 return;
             }

             if (error.name === "AbortError") {
                 return;
             }

             console.error(
                 "[SMPU SPA] Navigation error:",
                 error
             );

             // ----------------------------------
             // FULL PAGE FALLBACK
             // ----------------------------------

             if (error.fullPageFallback) {

                 location.href =
                     targetUrl.href;

                 return;

             }

             // ----------------------------------
             // NETWORK ERROR
             // ----------------------------------

             const networkError =
                 error instanceof TypeError ||
                 !navigator.onLine;

             if (networkError) {

                 showConnectionError({
                     offline: true
                 });

                 return;

             }

             // ----------------------------------
             // SERVER ERROR
             // ----------------------------------

             showConnectionError({
                 offline: false
             });

         } finally {

             if (sequence === navigationSequence) {

                 navigating = false;

                 navigationController = null;

             }

         }

     }

     // ==========================================
     // RETRY
     // ==========================================

     document.addEventListener(
         "click",
         function(event) {

             const button = event.target.closest(
                 "#spa-retry-button"
             );

             if (!button) return;

             if (!retryUrl) {
                 retryUrl = location.href;
             }

             button.disabled = true;

             button.innerHTML =
                 '<i class="fa-solid fa-spinner fa-spin"></i>' +
                 '<span>Mencoba kembali...</span>';

             hideConnectionError();

             navigateTo(
                 retryUrl,
                 {
                     popstate: true
                 }
             );

         }
     );

     // ==========================================
     // INTERCEPT LINK
     // ==========================================

     document.addEventListener(
         "click",
         function(event) {

             const target =
                 event.target instanceof Element
                     ? event.target
                     : event.target?.parentElement;

             const link = target?.closest("a");

             if (!link) return;

             if (
                 link.closest(
                     ".halaman-pemilih-wrapper"
                 )
             ) {
                 return;
             }

             const isSidebarMenu = link.matches(
                 "#mainSidebar .sidebar-menu-wrapper a.menu-link"
             );

             if (!isSidebarMenu) {

                 if (!isPageLink(link, event)) {
                     return;
                 }

             } else {

                 if (
                     event.button !== 0 ||
                     event.ctrlKey ||
                     event.shiftKey ||
                     event.altKey ||
                     event.metaKey ||
                     (
                         link.target &&
                         link.target !== "_self"
                     ) ||
                     link.hasAttribute("download") ||
                     link.hasAttribute("data-no-spa") ||
                     link.hasAttribute("data-bs-toggle")
                 ) {
                     return;
                 }

                 const url = getPageUrl(
                     link.href
                 );

                 if (
                     url.origin !== location.origin ||
                     !["http:", "https:"].includes(
                         url.protocol
                     )
                 ) {
                     return;
                 }

                 if (
                     url.pathname === location.pathname &&
                     url.search === location.search &&
                     url.hash === location.hash
                 ) {

                     event.preventDefault();

                     return;

                 }

             }

             event.preventDefault();

             saveSidebarScroll();

             navigateTo(link.href);

         },
         true
     );

     // ==========================================
     // BACK / FORWARD
     // ==========================================

     window.addEventListener(
         "popstate",
         function() {

             const path = location.pathname;

             if (path === currentPagePath) {
                 return;
             }

             navigateTo(
                 location.href,
                 {
                     popstate: true
                 }
             );

         }
     );

     // ==========================================
     // ONLINE / OFFLINE
     // ==========================================

     window.addEventListener(
         "offline",
         function() {

             if (navigating) {

                 if (navigationController) {
                     navigationController.abort();
                 }

                 showConnectionError({
                     offline: true
                 });

             }

         }
     );

     window.addEventListener(
         "online",
         function() {

             // Tidak otomatis reload halaman.
             // User dapat menekan Coba Lagi.
             console.log(
                 "[SMPU] Koneksi internet kembali."
             );

         }
     );

     // ==========================================
    // INITIAL PAGE
    // ==========================================

    document.addEventListener(
        "DOMContentLoaded",
        function() {

            // Atur posisi loader sesuai sidebar
            observeSidebarPosition();

            currentPagePath = location.pathname;

            updateSidebarActive(
                location.href
            );

            restoreSidebarScroll();

            dispatchPageEvent(
                "spa:page-loaded",
                {
                    url: location.href,
                    path: location.pathname,
                    initial: true
                }
            );

        }
    );

     // ==========================================
     // SIDEBAR SCROLL
     // ==========================================

     document.addEventListener(
         "DOMContentLoaded",
         function() {

             const sidebar =
                 getSidebarScrollElement();

             if (!sidebar) return;

             sidebar.addEventListener(
                 "scroll",
                 saveSidebarScroll,
                 {
                     passive: true
                 }
             );

         }
     );

     window.addEventListener(
         "pagehide",
         saveSidebarScroll
     );

 })();
