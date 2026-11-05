
// ==========================================
// SPA NAVIGATION — GLOBAL PAGE MANAGER
// ==========================================
(() => {
    "use strict";

    const CONTENT_ID = "spa-content";

    let navigating = false;
    let currentPagePath = location.pathname;
    let navigationController = null;

    const loadedScripts = new Map();
    const pageStyleIds = new Set();

    // ==========================================
    // UTILITAS
    // ==========================================
    function getPageUrl(url) {
        return new URL(url, location.origin);
    }

    function dispatchPageEvent(name, detail = {}) {
        document.dispatchEvent(
            new CustomEvent(name, { detail })
        );
    }

    // ==========================================
    // SIDEBAR ACTIVE MENU
    // ==========================================
    function normalizePath(path) {
        let result = path.replace(/\/+$/, "");

        return result || "/";
    }

    function updateSidebarActive(url) {
        const sidebar = document.querySelector(
            "#mainSidebar .sidebar-menu-wrapper"
        );

        // Simpan posisi scroll sebelum class active berubah.
        const posisiScroll = sidebar ? sidebar.scrollTop : 0;

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
                console.warn("Gagal menentukan menu aktif:", error);
            }
        });

        // Kembalikan posisi secara langsung setelah class diperbarui.
        if (sidebar) {
            sidebar.scrollTop = posisiScroll;
        }
    }

    // ==========================================
    // CEK LINK YANG BOLEH DI-SPA-KAN
    // ==========================================
    function isPageLink(link, event) {
        if (!link || !link.href) return false;
        if (event.defaultPrevented || event.button !== 0) return false;

        if (
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey ||
            event.metaKey
        ) return false;

        if (link.target && link.target !== "_self") return false;
        if (link.hasAttribute("download")) return false;
        if (link.hasAttribute("data-no-spa")) return false;
        if (link.hasAttribute("data-bs-toggle")) return false;

        const url = getPageUrl(link.href);

        if (url.origin !== location.origin) return false;
        if (!["http:", "https:"].includes(url.protocol)) return false;

        // Jangan mengambil alih navigasi hash halaman yang sama.
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
    // CSS HALAMAN
    // ==========================================
    function updatePageStyles(doc, newContent) {
        // Hapus CSS halaman sebelumnya.
        document.querySelectorAll(
            "[data-spa-page-style]"
        ).forEach(el => el.remove());

        pageStyleIds.clear();

        const styles = [];

        // CSS dari extra_css di HEAD.
        doc.head.querySelectorAll(
            'link[rel="stylesheet"]:not([data-spa-global])'
        ).forEach(el => styles.push(el.cloneNode(true)));

        // CSS dari block content.
        newContent.querySelectorAll(
            'link[rel="stylesheet"]:not([data-spa-global])'
        ).forEach(el => styles.push(el.cloneNode(true)));

        // Style inline dari konten halaman.
        newContent.querySelectorAll("style").forEach(el => {
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

        // Hilangkan CSS dari konten agar tidak terpasang dua kali.
        newContent.querySelectorAll(
            'link[rel="stylesheet"], style'
        ).forEach(el => el.remove());
    }

    // ==========================================
    // SCRIPT EKSTERNAL
    // ==========================================
    function loadExternalScript(src) {
        const absoluteSrc = getPageUrl(src).href;

        // Script global yang sudah ada tidak perlu dimuat ulang.
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

        // Script halaman yang sudah pernah dimuat.
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
                    new Error("Gagal memuat script: " + absoluteSrc)
                );
            };

            document.body.appendChild(script);
        });

        loadedScripts.set(absoluteSrc, promise);

        return promise;
    }

    // ==========================================
    // EKSEKUSI SCRIPT HALAMAN
    // ==========================================
    async function executePageScripts(doc, newContent) {
        // Ambil seluruh script sesuai urutan HTML asli.
        const scripts = Array.from(
            doc.querySelectorAll(
                "#spa-content script, body > script, head > script"
            )
        );

        for (const oldScript of scripts) {
            if (oldScript.hasAttribute("data-spa-global")) {
                continue;
            }

            const type = (oldScript.type || "").toLowerCase();

            // Abaikan JSON dan tipe script non-JavaScript.
            if (
                type &&
                type !== "text/javascript" &&
                type !== "application/javascript" &&
                type !== "module"
            ) {
                continue;
            }

            if (oldScript.src) {
                await loadExternalScript(oldScript.src);
                continue;
            }

            // Script module perlu perlakuan berbeda.
            if (type === "module") {
                const script = document.createElement("script");
                script.type = "module";
                script.textContent = oldScript.textContent;
                document.body.appendChild(script);
                continue;
            }

            // Isolasi deklarasi const/let agar tidak bentrok
            // ketika halaman dibuka kembali.
            const script = document.createElement("script");

            script.textContent =
                "{\n" + oldScript.textContent + "\n}";

            document.body.appendChild(script);
            script.remove();
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
            console.warn("Gagal menyimpan scroll sidebar:", error);
        }
    }

    // Hanya pulihkan saat halaman benar-benar dimuat ulang,
    // bukan setiap navigasi SPA.
    function restoreSidebarScroll() {
        const sidebar = getSidebarScrollElement();

        if (!sidebar) return;

        try {
            const posisi = Number(
                sessionStorage.getItem(SIDEBAR_SCROLL_KEY) || 0
            );

            sidebar.style.scrollBehavior = "auto";
            sidebar.scrollTop = posisi;

        } catch (error) {
            console.warn("Gagal memulihkan scroll sidebar:", error);
        }
    }

    // Simpan posisi setiap kali sidebar digulir.
    document.addEventListener("DOMContentLoaded", function() {
        const sidebar = getSidebarScrollElement();

        if (!sidebar) return;

        sidebar.addEventListener("scroll", saveSidebarScroll, {
            passive: true
        });

        restoreSidebarScroll();
    });

    window.addEventListener("pagehide", saveSidebarScroll);

    // ==========================================
    // NAVIGASI UTAMA
    // ==========================================
    async function navigateTo(url, options = {}) {
        if (navigating) return;

        const currentContent = document.getElementById(CONTENT_ID);

        if (!currentContent) {
            location.href = url;
            return;
        }

        const targetUrl = getPageUrl(url);

        if (targetUrl.origin !== location.origin) {
            location.href = url;
            return;
        }

        navigating = true;

        navigationController = new AbortController();

        currentContent.classList.add("spa-loading");

        try {
            const response = await fetch(targetUrl.href, {
                method: "GET",
                headers: {
                    "X-SPA-Request": "true",
                    "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin",
                signal: navigationController.signal
            });

            if (!response.ok) {
                throw new Error("HTTP " + response.status);
            }

            const html = await response.text();

            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");

            const newContent = doc.getElementById(CONTENT_ID);

            // Fallback jika server mengembalikan halaman tanpa layout SPA.
            if (!newContent) {
                location.href = response.url || targetUrl.href;
                return;
            }

            // Bersihkan halaman lama sebelum konten diganti.
            dispatchPageEvent("spa:before-page-unload", {
                url: targetUrl.href
            });

            // Pasang CSS halaman baru.
            updatePageStyles(doc, newContent);

            // Ganti konten utama.
            currentContent.innerHTML = newContent.innerHTML;

            // Update judul.
            if (doc.title) {
                document.title = doc.title;
            }

            const finalUrl = response.url || targetUrl.href;
            const finalPath = getPageUrl(finalUrl).pathname;

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

            updateSidebarActive(finalUrl);

            window.scrollTo({ top: 0, behavior: "instant" });

            // Jalankan script halaman setelah HTML terpasang.
            await executePageScripts(doc, newContent);

            dispatchPageEvent("spa:page-loaded", {
                url: finalUrl,
                path: finalPath,
                initial: false
            });

        } catch (error) {
            if (error.name === "AbortError") return;

            console.error("SPA Navigation Error:", error);
            location.href = targetUrl.href;

        } finally {
            currentContent.classList.remove("spa-loading");
            navigating = false;
            navigationController = null;
        }
    }

    // ==========================================
    // INTERCEPT LINK
    // ==========================================
    document.addEventListener("click", function(event) {
        const link = event.target.closest("a");

        if (!isPageLink(link, event)) return;

        event.preventDefault();

        saveSidebarScroll();

        navigateTo(link.href);
    });

    // ==========================================
    // BACK / FORWARD
    // ==========================================
    window.addEventListener("popstate", function() {
        const path = location.pathname;

        // Query pada halaman yang sama ditangani oleh
        // mekanisme halaman itu sendiri (misalnya Atur Gaji).
        if (path === currentPagePath) return;

        navigateTo(location.href, {
            popstate: true
        });
    });

    // ==========================================
    // HALAMAN PERTAMA
    // ==========================================
    document.addEventListener("DOMContentLoaded", function() {
        currentPagePath = location.pathname;
        updateSidebarActive(location.href);

        dispatchPageEvent("spa:page-loaded", {
            url: location.href,
            path: location.pathname,
            initial: true
        });
    });

})();
