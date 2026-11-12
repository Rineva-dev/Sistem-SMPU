document.addEventListener('DOMContentLoaded', function () {
    const page = document.querySelector('.ra-page');
    if (!page) return;

    /* =========================================
       1. ANIMASI ANGKA
    ========================================= */
    const counters = page.querySelectorAll('.ra-count');

    counters.forEach(function (element) {
        const target = Number(element.dataset.count);

        if (!Number.isFinite(target)) return;

        const hasPercent = element.textContent.includes('%');
        const duration = 1000;
        const startTime = performance.now();

        function animateCounter(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            const current = target * eased;

            element.textContent = hasPercent
                ? current.toFixed(1).replace(/\.0$/, '') + '%'
                : Math.round(current).toLocaleString('id-ID');

            if (progress < 1) {
                requestAnimationFrame(animateCounter);
            } else {
                element.textContent = hasPercent
                    ? target.toLocaleString('id-ID', {
                        maximumFractionDigits: 1
                    }) + '%'
                    : Math.round(target).toLocaleString('id-ID');
            }
        }

        element.textContent = hasPercent ? '0%' : '0';
        requestAnimationFrame(animateCounter);
    });


    /* =========================================
       2. PROGRESS BAR HERO
    ========================================= */
    const progressFill = page.querySelector('.ra-hero-progress-fill');

    if (progressFill) {
        const target = Math.max(
            0,
            Math.min(100, Number(progressFill.dataset.progress) || 0)
        );

        progressFill.style.width = '0%';

        requestAnimationFrame(function () {
            setTimeout(function () {
                progressFill.style.width = target + '%';
            }, 120);
        });
    }


    /* =========================================
       3. DONUT CHART TANPA LIBRARY TAMBAHAN
    ========================================= */
    const donut = document.getElementById('raDonut');

    if (donut) {
        const hadir = Number(donut.dataset.hadir) || 0;
        const terlambat = Number(donut.dataset.terlambat) || 0;
        const izin = Number(donut.dataset.izin) || 0;
        const total = hadir + terlambat + izin;

        const totalElement = document.getElementById('raDonutTotal');

        if (totalElement) {
            totalElement.textContent = total.toLocaleString('id-ID');
        }

        if (total > 0) {
            const hadirDeg = (hadir / total) * 360;
            const terlambatDeg = (terlambat / total) * 360;
            const izinDeg = (izin / total) * 360;

            const batasHadir = hadirDeg;
            const batasTerlambat = hadirDeg + terlambatDeg;
            const batasIzin = batasTerlambat + izinDeg;

            const finalGradient = `
                conic-gradient(
                    #07966c 0deg ${batasHadir}deg,
                    #f2b544 ${batasHadir}deg ${batasTerlambat}deg,
                    #6b9be8 ${batasTerlambat}deg ${batasIzin}deg
                )
            `;

            donut.style.background =
                'conic-gradient(#e8efeb 0deg 360deg)';

            requestAnimationFrame(function () {
                setTimeout(function () {
                    donut.style.background = finalGradient;
                }, 150);
            });
        } else {
            donut.style.background =
                'conic-gradient(#e8efeb 0deg 360deg)';
        }
    }


    /* =========================================
       4. FILTER PENCARIAN RIWAYAT
    ========================================= */
    const searchInput = document.getElementById('raSearch');
    const statusFilter = document.getElementById('raStatusFilter');
    const tableBody = document.getElementById('raTableBody');
    const noResult = document.getElementById('raNoResult');

    function filterHistory() {
        if (!tableBody) return;

        const keyword = (searchInput?.value || '').toLowerCase().trim();
        const selectedStatus = (statusFilter?.value || '').toLowerCase();

        const rows = Array.from(
            tableBody.querySelectorAll('tr[data-status]')
        );

        let visibleCount = 0;

        rows.forEach(function (row) {
            const text = row.textContent.toLowerCase();
            const status = (row.dataset.status || '').toLowerCase();

            const matchKeyword = !keyword || text.includes(keyword);
            const matchStatus = !selectedStatus ||
                status === selectedStatus;

            const visible = matchKeyword && matchStatus;

            row.hidden = !visible;

            if (visible) visibleCount++;
        });

        if (noResult) {
            noResult.hidden = visibleCount > 0 || rows.length === 0;
        }
    }

    searchInput?.addEventListener('input', filterHistory);
    statusFilter?.addEventListener('change', filterHistory);


    /* =========================================
       5. MOBILE / DESKTOP PERIOD PICKER
    ========================================= */
    const periodButton = document.getElementById('btn-pilih-bulan-tahun');
    const periodPopover = document.getElementById('kalenderBulanTahunHP');
    const closePeriod = document.getElementById('ra-close-period');

    function closePeriodPicker() {
        periodPopover?.classList.remove('is-open');
    }

    periodButton?.addEventListener('click', function (event) {
        event.stopPropagation();

        periodPopover?.classList.toggle('is-open');
    });

    closePeriod?.addEventListener('click', closePeriodPicker);

    periodPopover?.addEventListener('click', function (event) {
        event.stopPropagation();
    });

    document.addEventListener('click', function (event) {
        if (
            periodPopover &&
            !periodPopover.contains(event.target) &&
            !periodButton?.contains(event.target)
        ) {
            closePeriodPicker();
        }
    });


    /* =========================================
       6. EXPORT SELECTOR
    ========================================= */
    const exportTrigger = document.getElementById('exportSelectTrigger');
    const exportDropdown = document.getElementById('exportSelectDropdown');
    const exportLabel = document.getElementById('exportSelectLabel');
    const jenisExport = document.getElementById('jenisExport');

    const exportForm = document.querySelector('.ra-export-form');

    function closeExportDropdown() {
        exportDropdown?.classList.remove('is-open');
        exportTrigger?.setAttribute('aria-expanded', 'false');
    }

    function setExportType(value, label) {
        if (jenisExport) jenisExport.value = value;
        if (exportLabel) exportLabel.textContent = label;

        exportDropdown?.querySelectorAll('button').forEach(function (button) {
            button.classList.toggle(
                'active',
                button.dataset.value === value
            );
        });

        const fields = {
            perbulan: page.querySelectorAll('.perbulan-field'),
            semua: page.querySelectorAll('.semua-field'),
            rentang: page.querySelectorAll('.rentang-field')
        };

        Object.entries(fields).forEach(function ([key, elements]) {
            elements.forEach(function (element) {
                element.hidden = key !== value;
            });
        });

        closeExportDropdown();
    }

    exportTrigger?.addEventListener('click', function (event) {
        event.stopPropagation();

        const isOpen = exportDropdown?.classList.toggle('is-open');

        exportTrigger.setAttribute(
            'aria-expanded',
            isOpen ? 'true' : 'false'
        );
    });

    exportDropdown?.querySelectorAll('button[data-value]').forEach(
        function (button) {
            button.addEventListener('click', function () {
                setExportType(
                    button.dataset.value,
                    button.dataset.label
                );
            });
        }
    );

    exportDropdown?.addEventListener('click', function (event) {
        event.stopPropagation();
    });

    document.addEventListener('click', function (event) {
        if (
            exportDropdown &&
            !exportDropdown.contains(event.target) &&
            !exportTrigger?.contains(event.target)
        ) {
            closeExportDropdown();
        }
    });

    exportTrigger?.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            exportTrigger.click();
        }

        if (event.key === 'Escape') {
            closeExportDropdown();
        }
    });

    // Default export
    setExportType('perbulan', 'Rekap Bulanan');


    /* =========================================
       7. VALIDASI RENTANG EXPORT
    ========================================= */
    exportForm?.addEventListener('submit', function (event) {
        if (jenisExport?.value !== 'rentang') return;

        const bulanAwal = Number(
            exportForm.querySelector('[name="bulan_awal"]')?.value
        );
        const tahunAwal = Number(
            exportForm.querySelector('[name="tahun_awal"]')?.value
        );
        const bulanAkhir = Number(
            exportForm.querySelector('[name="bulan_akhir"]')?.value
        );
        const tahunAkhir = Number(
            exportForm.querySelector('[name="tahun_akhir"]')?.value
        );

        const periodeAwal = tahunAwal * 12 + bulanAwal;
        const periodeAkhir = tahunAkhir * 12 + bulanAkhir;

        if (
            !bulanAwal || !tahunAwal ||
            !bulanAkhir || !tahunAkhir ||
            periodeAwal > periodeAkhir
        ) {
            event.preventDefault();
            alert('Rentang bulan tidak valid. Periksa kembali periode awal dan akhir.');
        }
    });


    /* =========================================
       8. REVEAL ANIMATION SAAT SCROLL
    ========================================= */
    const revealElements = page.querySelectorAll(
        '.ra-kpi-card, .ra-insight-card, .ra-history-card, .ra-export-card'
    );

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('ra-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.08
        });

        revealElements.forEach(function (element) {
            element.classList.add('ra-reveal');
            observer.observe(element);
        });
    }
});