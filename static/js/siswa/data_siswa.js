
/* ==========================================================
   SMPU STUDENT HUB — INTERACTION ENGINE
   ========================================================== */

(function () {

    function initStudentHub() {

        const root = document.querySelector('.student-hub');

        if (!root || root.dataset.shInitialized === 'true') return;

        root.dataset.shInitialized = 'true';

        const search = root.querySelector('#cariSiswa');
        const statusSelect = root.querySelector('#filterStatusSiswa');
        const rows = Array.from(
            root.querySelectorAll('.sh-student-row')
        );

        const tabs = root.querySelectorAll('.sh-tab');
        const visibleCount = root.querySelector('#shVisibleCount');
        const totalCount = root.querySelector('#shTotalCount');
        const noResult = root.querySelector('#shNoResult');
        const resetButton = root.querySelector('#shResetFilter');

        let activeTab = 'all';

        /* =====================================
           STATUS NORMALIZATION
        ===================================== */

        function cocokStatus(status, filter) {

            if (!filter || filter === 'all') return true;

            if (filter === 'nonaktif') {
                return status !== 'aktif' && status !== 'lulus';
            }

            return status === filter;
        }

        /* =====================================
           MAIN FILTER ENGINE
        ===================================== */

        function filterSiswa() {

            const keyword = (search?.value || '')
                .toLowerCase()
                .trim();

            const dropdownFilter = statusSelect?.value || '';

            let jumlah = 0;

            rows.forEach(row => {

                const teks = row.textContent
                    .toLowerCase()
                    .replace(/\s+/g, ' ');

                const status = row.dataset.status || '';

                const cocokKeyword = teks.includes(keyword);

                const cocokTab = cocokStatus(
                    status,
                    activeTab
                );

                const cocokDropdown = cocokStatus(
                    status,
                    dropdownFilter
                );

                const tampil =
                    cocokKeyword &&
                    cocokTab &&
                    cocokDropdown;

                row.hidden = !tampil;

                if (tampil) jumlah++;

            });

            if (visibleCount) {
                visibleCount.textContent = jumlah;
            }

            if (totalCount) {
                totalCount.textContent = rows.length;
            }

            if (noResult) {
                noResult.hidden = jumlah !== 0;
            }
        }

        /* =====================================
           SEARCH
        ===================================== */

        if (search) {
            search.addEventListener('input', filterSiswa);
        }

        /* =====================================
           DROPDOWN STATUS
        ===================================== */

        if (statusSelect) {

            statusSelect.addEventListener('change', function () {

                // Dropdown menjadi filter utama.
                // Quick tab kembali ke Semua.
                activeTab = 'all';

                tabs.forEach(tab => {
                    tab.classList.toggle(
                        'active',
                        tab.dataset.filter === 'all'
                    );
                });

                filterSiswa();
            });
        }

        /* =====================================
           QUICK FILTER TABS
        ===================================== */

        tabs.forEach(tab => {

            tab.addEventListener('click', function () {

                activeTab = this.dataset.filter || 'all';

                tabs.forEach(item => {
                    item.classList.remove('active');
                });

                this.classList.add('active');

                // Reset dropdown agar tidak terjadi
                // dua filter yang saling bertentangan.
                if (statusSelect) {
                    statusSelect.value = '';
                }

                filterSiswa();
            });

        });

        /* =====================================
           RESET FILTER
        ===================================== */

        if (resetButton) {

            resetButton.addEventListener('click', function () {

                if (search) search.value = '';

                if (statusSelect) {
                    statusSelect.value = '';
                }

                activeTab = 'all';

                tabs.forEach(tab => {
                    tab.classList.toggle(
                        'active',
                        tab.dataset.filter === 'all'
                    );
                });

                filterSiswa();
            });

        }

        /* =====================================
           INITIAL STATE
        ===================================== */

        filterSiswa();

        /* =====================================
           TAHUN PENDAFTARAN
           Tetap dipertahankan
        ===================================== */

        const tanggalDiterima =
            document.getElementById('tanggalDiterima');

        const tahunDiterima =
            document.getElementById('tahunDiterima');

        function ambilTahunDariTanggal() {

            if (!tanggalDiterima || !tahunDiterima) return;

            tahunDiterima.value = tanggalDiterima.value
                ? tanggalDiterima.value.split('-')[0]
                : '';
        }

        if (tanggalDiterima) {
            tanggalDiterima.addEventListener(
                'change',
                ambilTahunDariTanggal
            );

            ambilTahunDariTanggal();
        }

        /* =====================================
           STATUS MODAL CONTROLLER
        ===================================== */

        window.tampilkanFormNonAktif = function (id) {

            const status = document.getElementById(
                `status${id}`
            )?.value;

            const form = document.getElementById(
                `formNonAktif${id}`
            );

            if (form) {
                form.classList.toggle(
                    'd-none',
                    status !== 'Non Aktif'
                );
            }

        };

        window.tampilkanSekolahTujuan = function (id) {

            const jenis = document.getElementById(
                `jenis${id}`
            )?.value;

            const kolom = document.getElementById(
                `kolomSekolah${id}`
            );

            if (kolom) {
                kolom.classList.toggle(
                    'd-none',
                    jenis !== 'Pindah'
                );
            }

        };

        // Pasang event sekali agar tidak berulang
        // ketika navigasi SPA memuat halaman kembali.
        if (!document.documentElement.dataset.shModalListener) {

            document.documentElement.dataset.shModalListener = 'true';

            document.addEventListener(
                'shown.bs.modal',
                function (event) {

                    const modal = event.target;

                    if (!modal.id ||
                        !modal.id.startsWith('modalStatus')) return;

                    const id = modal.id.replace(
                        'modalStatus',
                        ''
                    );

                    window.tampilkanFormNonAktif(id);
                    window.tampilkanSekolahTujuan(id);
                }
            );
        }

    }

    // Normal load dan SPA navigation
    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initStudentHub,
            { once: true }
        );

    } else {

        initStudentHub();

    }

})();
