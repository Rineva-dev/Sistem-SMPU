
/* =========================================================
   ABSENSI SISWA — EMERALD WORKSPACE
========================================================= */

(function () {
    'use strict';

    function initAbsensiSiswa() {
        const page = document.getElementById('absensiSiswaPage');

        if (!page || page.dataset.initialized === 'true') {
            return;
        }

        page.dataset.initialized = 'true';

        const form = document.getElementById('asAttendanceForm');
        const search = document.getElementById('asSearch');
        const filter = document.getElementById('asFilter');
        const studentList = document.getElementById('asStudentList');
        const noResults = document.getElementById('asNoResults');
        const allPresentButton = document.getElementById('asAllPresent');
        const saveButton = document.getElementById('asSaveButton');

        if (!form || !studentList) {
            return;
        }

        const rows = Array.from(
            studentList.querySelectorAll('.as-student-row')
        );

        const statusSelects = Array.from(
            studentList.querySelectorAll('.as-status-select')
        );

        const participationInputs = Array.from(
            studentList.querySelectorAll('.as-participation-input')
        );

        const participationNotes = Array.from(
            studentList.querySelectorAll('.as-participation-note')
        );

        const counters = {
            hadir: document.getElementById('asHadir'),
            izin: document.getElementById('asIzin'),
            sakit: document.getElementById('asSakit'),
            alpha: document.getElementById('asAlpha')
        };

        const totalElement = document.getElementById('asTotal');

        const labels = {
            hadir: 'Hadir',
            izin: 'Izin',
            sakit: 'Sakit',
            alpha: 'Alpa',
            belum: 'Belum dipilih'
        };


        // =====================================================
        // PENGELOLAAN INPUT PARTISIPASI
        // =====================================================

        function updateParticipationState(select, reset = false) {
            const row = select.closest('.as-student-row');

            if (!row) return;

            const isHadir = select.value === 'hadir';

            const nilaiInput = row.querySelector(
                '.as-participation-input'
            );

            const catatanInput = row.querySelector(
                '.as-participation-note'
            );

            if (nilaiInput) {
                nilaiInput.disabled = !isHadir;

                if (!isHadir || reset) {
                    nilaiInput.value = '';
                }
            }

            if (catatanInput) {
                catatanInput.disabled = !isHadir;

                if (!isHadir || reset) {
                    catatanInput.value = '';
                }
            }
        }

        // =====================================================
        // UPDATE STATUS VISUAL
        // =====================================================

        function updateStatusAppearance(select) {
            const value = select.value || 'belum';
            const wrapper = select.closest('.as-status-select-wrap');
            const indicator = wrapper
                ? wrapper.querySelector('.as-status-indicator')
                : null;

            select.dataset.status = value;

            if (indicator) {
                indicator.className =
                    'as-status-indicator status-' + value;
            }

            const row = select.closest('.as-student-row');

            if (row) {
                row.dataset.status = value;
            }
        }

        // =====================================================
        // HITUNG STATISTIK
        // =====================================================

        function updateStatistics() {
            const counts = {
                hadir: 0,
                izin: 0,
                sakit: 0,
                alpha: 0,
                belum: 0
            };

            statusSelects.forEach(function (select) {
                const status = select.value || 'belum';

                if (Object.prototype.hasOwnProperty.call(counts, status)) {
                    counts[status]++;
                }
            });

            Object.keys(counters).forEach(function (status) {
                if (counters[status]) {
                    counters[status].textContent = counts[status];
                }
            });

            if (totalElement) {
                totalElement.textContent = rows.length;
            }

            if (saveButton) {
                const belumDipilih = counts.belum;

                saveButton.disabled =
                    rows.length === 0 || belumDipilih > 0;

                const text = saveButton.querySelector('span');

                if (text) {
                    text.textContent = belumDipilih > 0
                        ? belumDipilih + ' Status Belum Dipilih'
                        : 'Simpan Absensi';
                }
            }

            return counts;
        }

        // =====================================================
        // PENCARIAN DAN FILTER
        // =====================================================

        function filterStudents() {
            const keyword = (search?.value || '')
                .trim()
                .toLowerCase();

            const selectedFilter = filter?.value || 'all';

            let visibleCount = 0;

            rows.forEach(function (row) {
                const nama = row.dataset.name || '';
                const nis = row.dataset.nis || '';
                const status = row.dataset.status || 'belum';

                const matchKeyword =
                    nama.includes(keyword) ||
                    nis.includes(keyword);

                const matchStatus =
                    selectedFilter === 'all' ||
                    status === selectedFilter;

                const visible = matchKeyword && matchStatus;

                row.hidden = !visible;

                if (visible) {
                    visibleCount++;
                }
            });

            if (noResults) {
                noResults.hidden = visibleCount !== 0;
            }
        }

        // =====================================================
        // EVENT STATUS SELECT
        // =====================================================
        
        statusSelects.forEach(function (select) {

            updateStatusAppearance(select);

            // Sinkronkan input partisipasi saat halaman dibuka
            updateParticipationState(select);

            select.addEventListener('change', function () {

                updateStatusAppearance(select);

                // Reset nilai dan catatan jika bukan hadir
                updateParticipationState(select, true);

                updateStatistics();
                filterStudents();
            });
        });


        // =====================================================
        // EVENT SEARCH DAN FILTER
        // =====================================================

        if (search) {
            search.addEventListener('input', filterStudents);
        }

        if (filter) {
            filter.addEventListener('change', filterStudents);
        }

        // =====================================================
        // SEMUA HADIR
        // =====================================================

        if (allPresentButton) {
            allPresentButton.addEventListener('click', function () {
                if (rows.length === 0) {
                    return;
                }

                const belumHadir = statusSelects.some(function (select) {
                    return select.value !== 'hadir';
                });

                if (!belumHadir) {
                    return;
                }

                const confirmed = window.confirm(
                    'Ubah status seluruh siswa menjadi HADIR? ' +
                    'Status yang sudah dipilih akan ikut diganti.'
                );

                if (!confirmed) {
                    return;
                }

                statusSelects.forEach(function (select) {
                    select.value = 'hadir';
                    updateStatusAppearance(select);
                    updateParticipationState(select);
                });

                updateStatistics();
                filterStudents();
            });
        }

        // =====================================================
        // VALIDASI SEBELUM SIMPAN
        // =====================================================
        
        if (form) {
            form.addEventListener('submit', function (event) {

                const belumDipilih = statusSelects.filter(function (select) {
                    return !select.value;
                });

                if (belumDipilih.length > 0) {
                    event.preventDefault();

                    const firstSelect = belumDipilih[0];

                    firstSelect.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });

                    firstSelect.focus();

                    window.alert(
                        'Masih ada ' + belumDipilih.length +
                        ' siswa yang belum dipilih status kehadirannya.'
                    );

                    return;
                }

                // =========================================
                // VALIDASI NILAI PARTISIPASI
                // =========================================

                for (const input of participationInputs) {

                    if (input.disabled || input.value.trim() === '') {
                        continue;
                    }

                    const nilai = Number(input.value);

                    if (
                        !Number.isFinite(nilai) ||
                        nilai < 0 ||
                        nilai > 100
                    ) {
                        event.preventDefault();

                        input.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });

                        input.focus();

                        window.alert(
                            'Nilai partisipasi harus berada antara 0 sampai 100.'
                        );

                        return;
                    }
                }

                // =========================================
                // KONFIRMASI SIMPAN
                // =========================================

                const confirmed = window.confirm(
                    'Simpan absensi untuk ' + rows.length +
                    ' siswa pada sesi pembelajaran ini?'
                );

                if (!confirmed) {
                    event.preventDefault();
                    return;
                }

                if (saveButton) {
                    saveButton.disabled = true;

                    const text = saveButton.querySelector('span');

                    if (text) {
                        text.textContent = 'Menyimpan...';
                    }

                    const icon = saveButton.querySelector(
                        '.fa-floppy-disk'
                    );

                    if (icon) {
                        icon.className = 'fa-solid fa-spinner fa-spin';
                    }
                }
            });
        }


        // =====================================================
        // INITIALIZATION
        // =====================================================

        updateStatistics();
        filterStudents();

        console.info(
            '[Absensi Siswa] Berhasil diinisialisasi.',
            {
                jurnalId: page.dataset.jurnalId,
                totalSiswa: rows.length
            }
        );
    }

    // Mendukung pemuatan halaman biasa maupun navigasi SPA.
    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            initAbsensiSiswa,
            { once: true }
        );
    } else {
        initAbsensiSiswa();
    }

    // Jika script dieksekusi ulang oleh SPA, inisialisasi langsung.
    initAbsensiSiswa();

})();
