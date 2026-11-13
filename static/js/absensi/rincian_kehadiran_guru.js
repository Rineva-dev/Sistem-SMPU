
(() => {
    "use strict";

    const GLOBAL_KEY = "__SMPU_RKH_EMERALD__";

    // External script hanya perlu didaftarkan sekali.
    if (window[GLOBAL_KEY]) {
        window[GLOBAL_KEY].init();
        return;
    }

    let cleanupCurrentPage = null;

    function destroyPage() {
        if (typeof cleanupCurrentPage === "function") {
            cleanupCurrentPage();
            cleanupCurrentPage = null;
        }
    }

    function initPage() {
        destroyPage();

        const root = document.querySelector(".rkh-page");
        if (!root) return;

        const controller = new AbortController();
        const signal = controller.signal;

        let revealObserver = null;
        let counterObserver = null;

        const prefersReducedMotion =
            window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        function listen(element, event, callback, options = {}) {
            if (!element) return;

            element.addEventListener(event, callback, {
                ...options,
                signal
            });
        }

        // -----------------------------------------
        // REVEAL ON SCROLL
        // -----------------------------------------
        const revealItems = root.querySelectorAll("[data-rkh-reveal]");

        if (prefersReducedMotion || !("IntersectionObserver" in window)) {
            revealItems.forEach(item => item.classList.add("is-visible"));
        } else {
            revealObserver = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) return;

                    entry.target.classList.add("is-visible");
                    revealObserver.unobserve(entry.target);
                });
            }, {
                threshold: 0.08,
                rootMargin: "0px 0px -35px 0px"
            });

            revealItems.forEach(item => revealObserver.observe(item));
        }

        // -----------------------------------------
        // ANIMATED NUMBER COUNTERS
        // -----------------------------------------
        function animateCounter(element) {
            const target = Number(element.dataset.rkhCount || 0);

            if (!Number.isFinite(target)) {
                element.textContent = "0";
                return;
            }

            if (prefersReducedMotion || target === 0) {
                element.textContent = target.toLocaleString("id-ID");
                return;
            }

            const duration = 1100;
            const startTime = performance.now();

            function frame(now) {
                const progress = Math.min((now - startTime) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 4);
                const current = Math.round(target * eased);

                element.textContent = current.toLocaleString("id-ID");

                if (progress < 1) {
                    requestAnimationFrame(frame);
                } else {
                    element.textContent = target.toLocaleString("id-ID");
                }
            }

            requestAnimationFrame(frame);
        }

        const counters = root.querySelectorAll("[data-rkh-count]");

        if (!prefersReducedMotion && "IntersectionObserver" in window) {
            counterObserver = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) return;

                    animateCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                });
            }, {
                threshold: 0.5
            });

            counters.forEach(counter => counterObserver.observe(counter));
        } else {
            counters.forEach(animateCounter);
        }

        // -----------------------------------------
        // AUTO SUBMIT PERIOD FILTER
        // -----------------------------------------
        const filterForm = root.querySelector("[data-rkh-filter-form]");
        const filterSelects = filterForm
            ? filterForm.querySelectorAll("select")
            : [];

        filterSelects.forEach(select => {
            listen(select, "change", () => {
                if (!filterForm) return;

                const submitButton = filterForm.querySelector(
                    'button[type="submit"]'
                );

                if (submitButton) {
                    submitButton.classList.add("is-loading");
                    submitButton.disabled = true;

                    const label = submitButton.querySelector("span");
                    if (label) label.textContent = "Memuat data...";
                }

                if (typeof filterForm.requestSubmit === "function") {
                    filterForm.requestSubmit();
                } else {
                    filterForm.submit();
                }
            });
        });

        // -----------------------------------------
        // EXPORT FEEDBACK
        // Jangan prevent submit: biarkan POST asli bekerja.
        // -----------------------------------------
        const exportForm = root.querySelector("[data-rkh-export-form]");
        const exportButton = exportForm
            ? exportForm.querySelector("button[type='submit']")
            : null;

        listen(exportForm, "submit", () => {
            if (!exportButton) return;

            exportButton.classList.add("is-loading");
            exportButton.setAttribute("aria-busy", "true");

            const title = exportButton.querySelector(".rkh-export-text strong");
            const icon = exportButton.querySelector(".rkh-export-icon i");

            if (title) title.textContent = "Menyiapkan...";
            if (icon) icon.className = "fas fa-circle-notch";
        });

        // -----------------------------------------
        // MICRO INTERACTION: TABLE ROW
        // -----------------------------------------
        const tableRows = root.querySelectorAll(".rkh-table tbody tr");

        tableRows.forEach((row, index) => {
            row.style.setProperty("--rkh-row-index", index);
        });

        // -----------------------------------------
        // CLEANUP
        // -----------------------------------------
        root.classList.add("rkh-ready");

        cleanupCurrentPage = () => {
            controller.abort();

            if (revealObserver) {
                revealObserver.disconnect();
                revealObserver = null;
            }

            if (counterObserver) {
                counterObserver.disconnect();
                counterObserver = null;
            }

            root.classList.remove("rkh-ready");
        };
    }

    // Simpan controller global agar script eksternal tidak
    // mendaftarkan listener berulang saat navigasi SPA.
    window[GLOBAL_KEY] = {
        init: initPage,
        destroy: destroyPage
    };

    // Halaman lama dibersihkan sebelum konten SPA diganti.
    document.addEventListener("spa:before-page-unload", destroyPage);

    // Halaman baru diinisialisasi setelah konten SPA selesai dimuat.
    document.addEventListener("spa:page-loaded", initPage);

    // Initial page load biasa.
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPage, {
            once: true
        });
    } else {
        initPage();
    }
})();
