
/* =========================================================
   SMPU - REKAP ABSENSI
   SPA COMPATIBLE • PREMIUM EMERALD
   Mendukung:
   - Full page refresh
   - SPA navigation
   - SPA back / forward
   - Re-initialize tanpa event listener bertumpuk
========================================================= */

(() => {
    'use strict';

    // Hindari instalasi event global berulang
    if (window.__SMPU_REKAP_ABSENSI_INIT__) return;
    window.__SMPU_REKAP_ABSENSI_INIT__ = true;

    let currentCleanup = null;
    let initSequence = 0;

    /* =====================================================
       GLOBAL SPA LIFECYCLE
    ===================================================== */

    function destroyPage() {
        if (typeof currentCleanup === 'function') {
            currentCleanup();
            currentCleanup = null;
        }
    }

    function initPage() {
        const page = document.querySelector('.ra-page');

        // Bukan halaman rekap absensi
        if (!page) {
            destroyPage();
            return;
        }

        // Bersihkan instance halaman sebelumnya
        destroyPage();

        const sequence = ++initSequence;
        const cleanups = [];

        function addCleanup(callback) {
            cleanups.push(callback);
        }

        function on(element, event, callback, options) {
            if (!element) return;

            element.addEventListener(event, callback, options);

            addCleanup(() => {
                element.removeEventListener(event, callback, options);
            });
        }

        function isCurrentPage() {
            return (
                sequence === initSequence &&
                document.querySelector('.ra-page') === page
            );
        }

        currentCleanup = function () {
            cleanups.forEach(callback => {
                try {
                    callback();
                } catch (error) {
                    console.warn('[Rekap Absensi] Cleanup:', error);
                }
            });

            cleanups.length = 0;
        };


        /* =================================================
           1. ANIMASI ANGKA
        ================================================= */

        page.querySelectorAll('.ra-count').forEach(element => {
            const target = Number(element.dataset.count);

            if (!Number.isFinite(target)) return;

            const hasPercent = element.textContent.includes('%');
            const duration = 1000;
            const startTime = performance.now();

            function animate(now) {
                if (!isCurrentPage()) return;

                const progress = Math.min(
                    (now - startTime) / duration,
                    1
                );

                const eased = 1 - Math.pow(1 - progress, 4);
                const current = target * eased;

                element.textContent = hasPercent
                    ? current.toFixed(1).replace(/\.0$/, '') + '%'
                    : Math.round(current).toLocaleString('id-ID');

                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.textContent = hasPercent
                        ? target.toLocaleString('id-ID', {
                            maximumFractionDigits: 1
                        }) + '%'
                        : Math.round(target).toLocaleString('id-ID');
                }
            }

            element.textContent = hasPercent ? '0%' : '0';

            requestAnimationFrame(animate);
        });


        /* =================================================
           2. HERO PROGRESS
        ================================================= */

        const progressFill = page.querySelector(
            '.ra-hero-progress-fill'
        );

        if (progressFill) {
            const target = Math.max(
                0,
                Math.min(
                    100,
                    Number(progressFill.dataset.progress) || 0
                )
            );

            progressFill.style.width = '0%';

            const progressTimer = setTimeout(() => {
                if (!isCurrentPage()) return;

                progressFill.style.width = target + '%';
            }, 120);

            addCleanup(() => clearTimeout(progressTimer));
        }


        /* =================================================
           3. DONUT CHART
        ================================================= */

        const donut = page.querySelector('#raDonut');

        if (donut) {
            const hadir = Number(donut.dataset.hadir) || 0;
            const terlambat = Number(donut.dataset.terlambat) || 0;
            const izin = Number(donut.dataset.izin) || 0;

            const total = hadir + terlambat + izin;

            const totalElement = page.querySelector(
                '#raDonutTotal'
            );

            if (totalElement) {
                totalElement.textContent =
                    total.toLocaleString('id-ID');
            }

            if (total > 0) {
                const hadirDeg = (hadir / total) * 360;
                const terlambatDeg = (terlambat / total) * 360;

                const batasHadir = hadirDeg;
                const batasTerlambat =
                    hadirDeg + terlambatDeg;

                const gradient = `
                    conic-gradient(
                        #07966c 0deg ${batasHadir}deg,
                        #f2b544 ${batasHadir}deg ${batasTerlambat}deg,
                        #6b9be8 ${batasTerlambat}deg 360deg
                    )
                `;

                donut.style.background =
                    'conic-gradient(#e8efeb 0deg 360deg)';

                const donutTimer = setTimeout(() => {
                    if (!isCurrentPage()) return;

                    donut.style.background = gradient;
                }, 150);

                addCleanup(() => clearTimeout(donutTimer));
            } else {
                donut.style.background =
                    'conic-gradient(#e8efeb 0deg 360deg)';
            }
        }


        /* =================================================
           4. FILTER RIWAYAT
        ================================================= */

        const searchInput = page.querySelector('#raSearch');
        const statusFilter = page.querySelector('#raStatusFilter');
        const tableBody = page.querySelector('#raTableBody');
        const noResult = page.querySelector('#raNoResult');

        function filterHistory() {
            if (!tableBody) return;

            const keyword = (
                searchInput?.value || ''
            ).toLowerCase().trim();

            const selectedStatus = (
                statusFilter?.value || ''
            ).toLowerCase();

            const rows = tableBody.querySelectorAll(
                'tr[data-status]'
            );

            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const status = (
                    row.dataset.status || ''
                ).toLowerCase();

                const matchKeyword =
                    !keyword || text.includes(keyword);

                const matchStatus =
                    !selectedStatus ||
                    status === selectedStatus;

                const visible =
                    matchKeyword && matchStatus;

                row.hidden = !visible;

                if (visible) visibleCount++;
            });

            if (noResult) {
                noResult.hidden =
                    visibleCount > 0 || rows.length === 0;
            }
        }

        on(searchInput, 'input', filterHistory);
        on(statusFilter, 'change', filterHistory);


        /* =================================================
           5. PERIOD PICKER
        ================================================= */

        const periodButton = page.querySelector(
            '#btn-pilih-bulan-tahun'
        );

        const periodPopover = page.querySelector(
            '#kalenderBulanTahunHP'
        );

        const closePeriod = page.querySelector(
            '#ra-close-period'
        );

        function closePeriodPicker() {
            periodPopover?.classList.remove('is-open');
            periodButton?.setAttribute('aria-expanded', 'false');
        }

        function togglePeriodPicker(event) {
            event?.stopPropagation();

            const isOpen =
                periodPopover?.classList.toggle('is-open');

            periodButton?.setAttribute(
                'aria-expanded',
                isOpen ? 'true' : 'false'
            );
        }

        on(periodButton, 'click', togglePeriodPicker);
        on(closePeriod, 'click', closePeriodPicker);

        on(periodPopover, 'click', event => {
            event.stopPropagation();
        });


        /* =================================================
           6. EXPORT DROPDOWN
        ================================================= */

        const exportTrigger = page.querySelector(
            '#exportSelectTrigger'
        );

        const exportDropdown = page.querySelector(
            '#exportSelectDropdown'
        );

        const exportLabel = page.querySelector(
            '#exportSelectLabel'
        );

        const jenisExport = page.querySelector(
            '#jenisExport'
        );

        const exportForm = page.querySelector(
            '.ra-export-form'
        );

        function closeExportDropdown() {
            exportDropdown?.classList.remove('is-open');

            exportTrigger?.setAttribute(
                'aria-expanded',
                'false'
            );
        }

        function toggleExportDropdown(event) {
            event?.stopPropagation();

            const isOpen =
                exportDropdown?.classList.toggle('is-open');

            exportTrigger?.setAttribute(
                'aria-expanded',
                isOpen ? 'true' : 'false'
            );
        }

        function setExportType(value, label) {
            if (jenisExport) {
                jenisExport.value = value;
            }

            if (exportLabel) {
                exportLabel.textContent = label;
            }

            exportDropdown?.querySelectorAll(
                'button[data-value]'
            ).forEach(button => {
                button.classList.toggle(
                    'active',
                    button.dataset.value === value
                );
            });

            const fieldGroups = {
                perbulan: page.querySelectorAll('.perbulan-field'),
                semua: page.querySelectorAll('.semua-field'),
                rentang: page.querySelectorAll('.rentang-field')
            };

            Object.entries(fieldGroups).forEach(
                ([key, elements]) => {
                    elements.forEach(element => {
                        element.hidden = key !== value;
                    });
                }
            );

            closeExportDropdown();
        }

        on(exportTrigger, 'click', toggleExportDropdown);

        on(exportDropdown, 'click', event => {
            const button = event.target.closest(
                'button[data-value]'
            );

            if (!button) {
                event.stopPropagation();
                return;
            }

            event.stopPropagation();

            setExportType(
                button.dataset.value,
                button.dataset.label ||
                button.textContent.trim()
            );
        });

        on(exportTrigger, 'keydown', event => {
            if (
                event.key === 'Enter' ||
                event.key === ' '
            ) {
                event.preventDefault();
                toggleExportDropdown(event);
            }

            if (event.key === 'Escape') {
                closeExportDropdown();
            }
        });


        /* =================================================
           7. VALIDASI EXPORT RENTANG
        ================================================= */

        on(exportForm, 'submit', event => {
            if (jenisExport?.value !== 'rentang') return;

            const bulanAwal = Number(
                exportForm.querySelector(
                    '[name="bulan_awal"]'
                )?.value
            );

            const tahunAwal = Number(
                exportForm.querySelector(
                    '[name="tahun_awal"]'
                )?.value
            );

            const bulanAkhir = Number(
                exportForm.querySelector(
                    '[name="bulan_akhir"]'
                )?.value
            );

            const tahunAkhir = Number(
                exportForm.querySelector(
                    '[name="tahun_akhir"]'
                )?.value
            );

            const periodeAwal =
                tahunAwal * 12 + bulanAwal;

            const periodeAkhir =
                tahunAkhir * 12 + bulanAkhir;

            if (
                !bulanAwal ||
                !tahunAwal ||
                !bulanAkhir ||
                !tahunAkhir ||
                periodeAwal > periodeAkhir
            ) {
                event.preventDefault();

                alert(
                    'Rentang bulan tidak valid. ' +
                    'Periksa kembali periode awal dan akhir.'
                );
            }
        });


        /* =================================================
           8. REVEAL ANIMATION
        ================================================= */

        const revealElements = page.querySelectorAll(
            '.ra-kpi-card, ' +
            '.ra-insight-card, ' +
            '.ra-history-card, ' +
            '.ra-export-card'
        );

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(
                entries => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add(
                                'ra-visible'
                            );

                            observer.unobserve(entry.target);
                        }
                    });
                },
                {
                    threshold: 0.08
                }
            );

            revealElements.forEach(element => {
                element.classList.remove('ra-visible');
                element.classList.add('ra-reveal');

                observer.observe(element);
            });

            addCleanup(() => observer.disconnect());
        }


        /* =================================================
           9. DOCUMENT CLICK - CLOSE DROPDOWNS
           Satu listener untuk semua dropdown halaman.
        ================================================= */

        function handleOutsideClick(event) {
            const target = event.target;

            if (
                periodPopover &&
                !periodPopover.contains(target) &&
                !periodButton?.contains(target)
            ) {
                closePeriodPicker();
            }

            if (
                exportDropdown &&
                !exportDropdown.contains(target) &&
                !exportTrigger?.contains(target)
            ) {
                closeExportDropdown();
            }
        }

        on(document, 'click', handleOutsideClick);


        /* =================================================
           10. DEFAULT EXPORT TYPE
        ================================================= */

        const defaultValue = jenisExport?.value || 'perbulan';

        const defaultButton = exportDropdown?.querySelector(
            `button[data-value="${defaultValue}"]`
        );

        setExportType(
            defaultValue,
            defaultButton?.dataset.label ||
            defaultButton?.textContent.trim() ||
            'Rekap Bulanan'
        );

        console.log(
            '[SMPU Rekap Absensi] Halaman berhasil diinisialisasi.'
        );
    }


    /* =====================================================
       EVENT SPA
    ===================================================== */

    document.addEventListener('spa:page-loaded', function () {
        initPage();
    });

    document.addEventListener('spa:before-page-unload', function () {
        destroyPage();
    });


    /* =====================================================
       FULL PAGE LOAD
    ===================================================== */

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            initPage,
            { once: true }
        );
    } else {
        initPage();
    }

})();
