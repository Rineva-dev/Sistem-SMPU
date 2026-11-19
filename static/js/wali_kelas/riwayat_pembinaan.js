
/* ==========================================================
   SMPU - RIWAYAT PEMBINAAN SISWA
   SPA COMPATIBLE
   MODAL, FORM, DETAIL, FILTER SISWA, EDIT, DAN HAPUS
========================================================== */

(function () {
    'use strict';

    // Elemen modal yang terakhir berhasil diinisialisasi.
    // Jika SPA mengganti HTML, elemen modal akan berbeda
    // sehingga halaman bisa diinisialisasi kembali.
    let initializedModal = null;

    // ======================================================
    // INISIALISASI HALAMAN
    // ======================================================

    function initRiwayatPembinaan() {

        const $ = (id) => document.getElementById(id);

        const modalForm = $('rpModalForm');
        const modalDetail = $('rpModalDetail');
        const form = $('rpForm');
        const formHapus = $('rpFormHapus');

        const siswaSelect = $('rpSiswa');
        const kelasSelect = $('rpKelas');

        const pemantauanCheckbox = $('rpPemantauan');
        const tanggalPemantauan = $('rpTanggalPemantauan');
        const tanggalPemantauanGroup = $('rpTanggalPemantauanGroup');

        // Halaman bukan Riwayat Pembinaan.
        if (!modalForm || !modalDetail || !form || !formHapus) {
            return;
        }

        // Cegah pemasangan event listener berulang
        // pada elemen halaman yang sama.
        if (initializedModal === modalForm) {
            return;
        }

        initializedModal = modalForm;

        const baseTambahUrl = form.action;
        let scrollPosition = 0;

        console.log(
            '[SMPU] Menginisialisasi Riwayat Pembinaan.'
        );


        // ==================================================
        // UTILITAS
        // ==================================================

        function setValue(id, value) {
            const element = $(id);

            if (!element) return;

            if (
                element.tagName === 'INPUT' ||
                element.tagName === 'SELECT' ||
                element.tagName === 'TEXTAREA'
            ) {
                element.value = value ?? '';
            } else {
                element.textContent = value ?? '-';
            }
        }

        function getData(button, key) {
            return button?.dataset?.[key] ?? '';
        }

        function getBasePath() {
            return new URL(
                baseTambahUrl,
                window.location.origin
            ).pathname.replace(/\/tambah\/?$/, '');
        }


        // ==================================================
        // SCROLL LOCK
        // ==================================================

        function lockScroll() {

            // Jangan mengunci scroll dua kali.
            if (
                document.body.dataset.rpScrollLocked === '1'
            ) {
                return;
            }

            scrollPosition = window.scrollY;

            document.body.dataset.rpScrollLocked = '1';
            document.body.style.position = 'fixed';
            document.body.style.top = `-${scrollPosition}px`;
            document.body.style.left = '0';
            document.body.style.right = '0';
            document.body.style.width = '100%';
            document.body.style.overflow = 'hidden';
        }

        function unlockScroll() {

            if (
                document.body.dataset.rpScrollLocked !== '1'
            ) {
                return;
            }

            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.left = '';
            document.body.style.right = '';
            document.body.style.width = '';
            document.body.style.overflow = '';

            delete document.body.dataset.rpScrollLocked;

            window.scrollTo(0, scrollPosition);
        }


        // ==================================================
        // MODAL CONTROLLER
        // ==================================================

        function bukaModal(modal) {

            if (!modal) return;

            tutupSemuaModal(false);

            lockScroll();

            modal.classList.add('active');
            modal.setAttribute('aria-hidden', 'false');
        }

        function tutupModal(modal, restoreScroll = true) {

            if (!modal) return;

            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');

            if (restoreScroll) {
                unlockScroll();
            }
        }

        function tutupSemuaModal(restoreScroll = true) {

            tutupModal(modalForm, false);
            tutupModal(modalDetail, false);

            if (restoreScroll) {
                unlockScroll();
            }
        }


        // ==================================================
        // FILTER SISWA BERDASARKAN KELAS
        // ==================================================

        function filterSiswa(
            kelasId,
            selectedSiswa = ''
        ) {

            if (!siswaSelect || !kelasSelect) return;

            const options = Array.from(
                siswaSelect.options
            );

            options.forEach((option, index) => {

                if (index === 0) {
                    option.hidden = false;
                    return;
                }

                const kelasSiswa =
                    option.dataset.kelas || '';

                const sesuaiKelas = (
                    !kelasId ||
                    kelasSiswa === String(kelasId)
                );

                option.hidden = !sesuaiKelas;
            });

            if (selectedSiswa) {

                const option = options.find(
                    item =>
                        item.value === String(selectedSiswa)
                );

                if (option && !option.hidden) {
                    siswaSelect.value = String(selectedSiswa);
                } else {
                    siswaSelect.value = '';
                }

            } else {

                const currentOption =
                    siswaSelect.selectedOptions[0];

                if (
                    currentOption &&
                    currentOption.value &&
                    currentOption.hidden
                ) {
                    siswaSelect.value = '';
                }

            }
        }


        // ==================================================
        // EVENT FILTER KELAS DAN SISWA
        // ==================================================

        if (kelasSelect && siswaSelect) {

            kelasSelect.addEventListener(
                'change',
                function () {
                    filterSiswa(this.value);
                }
            );

            siswaSelect.addEventListener(
                'change',
                function () {

                    const option =
                        this.selectedOptions[0];

                    if (!option || !option.value) return;

                    const kelasId =
                        option.dataset.kelas;

                    if (kelasId) {

                        kelasSelect.value = kelasId;

                        filterSiswa(
                            kelasId,
                            this.value
                        );
                    }
                }
            );
        }


        // ==================================================
        // PEMANTAUAN
        // ==================================================

        function updatePemantauan() {

            if (
                !pemantauanCheckbox ||
                !tanggalPemantauan ||
                !tanggalPemantauanGroup
            ) {
                return;
            }

            const aktif =
                pemantauanCheckbox.checked;

            tanggalPemantauanGroup.classList.toggle(
                'hidden',
                !aktif
            );

            tanggalPemantauan.required = aktif;

            if (!aktif) {
                tanggalPemantauan.value = '';
            }
        }

        if (pemantauanCheckbox) {

            pemantauanCheckbox.addEventListener(
                'change',
                updatePemantauan
            );
        }


        // ==================================================
        // RESET FORM
        // ==================================================

        function resetForm() {

            form.reset();

            form.action = baseTambahUrl;

            if ($('rpFormTitle')) {
                $('rpFormTitle').textContent =
                    'Tambah Riwayat Pembinaan';
            }

            if (pemantauanCheckbox) {
                pemantauanCheckbox.checked = true;
            }

            if (tanggalPemantauan) {
                tanggalPemantauan.value = '';
                tanggalPemantauan.required = true;
            }

            if (tanggalPemantauanGroup) {
                tanggalPemantauanGroup.classList.remove(
                    'hidden'
                );
            }

            if (kelasSelect) {
                kelasSelect.value = '';
            }

            if (siswaSelect) {
                siswaSelect.value = '';
            }

            if ($('rpStatus')) {
                $('rpStatus').value =
                    'dalam_pemantauan';
            }

            if ($('rpTingkat')) {
                $('rpTingkat').value =
                    'pembinaan_awal';
            }

            if ($('rpKomunikasi')) {
                $('rpKomunikasi').checked = false;
            }

            updatePemantauan();
        }


        // ==================================================
        // MODAL TAMBAH
        // ==================================================

        window.rpBukaTambah = function () {

            resetForm();

            form.action = baseTambahUrl;

            bukaModal(modalForm);
        };


        // ==================================================
        // TUTUP FORM
        // ==================================================

        window.rpTutupForm = function () {

            tutupModal(modalForm);
        };


        // ==================================================
        // MODAL EDIT
        // ==================================================

        window.rpBukaEdit = function (button) {

            if (!button) return;

            resetForm();

            const id = getData(button, 'id');

            if (!id) {

                alert(
                    'ID riwayat pembinaan tidak ditemukan.'
                );

                return;
            }

            const path = getBasePath();

            form.action =
                `${path}/${encodeURIComponent(id)}/edit`;

            if ($('rpFormTitle')) {
                $('rpFormTitle').textContent =
                    'Edit Riwayat Pembinaan';
            }

            const kelasId =
                getData(button, 'kelas');

            const siswaId =
                getData(button, 'siswa');

            if (kelasSelect) {
                kelasSelect.value = kelasId;
            }

            filterSiswa(kelasId, siswaId);

            setValue(
                'rpTanggal',
                getData(button, 'tanggal')
            );

            setValue(
                'rpKategori',
                getData(button, 'kategori')
            );

            setValue(
                'rpTingkat',
                getData(button, 'tingkat')
            );

            setValue(
                'rpJudul',
                getData(button, 'judul')
            );

            setValue(
                'rpKronologi',
                getData(button, 'kronologi')
            );

            setValue(
                'rpTindakan',
                getData(button, 'tindakan')
            );

            setValue(
                'rpHasil',
                getData(button, 'hasil')
            );

            setValue(
                'rpStatus',
                getData(button, 'status')
            );

            setValue(
                'rpTanggalPemantauan',
                getData(button, 'tanggalPemantauan')
            );

            setValue(
                'rpCatatanOrangTua',
                getData(button, 'catatanOrangTua')
            );

            if (pemantauanCheckbox) {

                pemantauanCheckbox.checked =
                    getData(button, 'pemantauan') === '1';
            }

            const komunikasi = $('rpKomunikasi');

            if (komunikasi) {

                komunikasi.checked =
                    getData(button, 'komunikasi') === '1';
            }

            updatePemantauan();

            bukaModal(modalForm);
        };


        // ==================================================
        // LABEL DETAIL
        // ==================================================

        const labelKategori = {
            kedisiplinan: 'Kedisiplinan',
            akademik: 'Akademik',
            perilaku: 'Perilaku',
            sosial: 'Sosial',
            kehadiran: 'Kehadiran',
            lainnya: 'Lainnya'
        };

        const labelTingkat = {
            pembinaan_awal: 'Pembinaan Awal',
            pembinaan_lanjutan: 'Pembinaan Lanjutan',
            pembinaan_khusus: 'Pembinaan Khusus'
        };

        const labelStatus = {
            dalam_pemantauan: 'Dalam Pemantauan',
            membaik: 'Membaik',
            selesai: 'Selesai',
            dirujuk_bk: 'Dirujuk BK'
        };


        // ==================================================
        // DETAIL PEMBINAAN
        // ==================================================

        window.rpLihatDetail = function (button) {

            if (!button) return;

            const data = {

                nama: getData(button, 'nama'),
                kelas: getData(button, 'kelas'),
                tanggal: getData(button, 'tanggal'),
                kategori: getData(button, 'kategori'),
                tingkat: getData(button, 'tingkat'),
                judul: getData(button, 'judul'),
                kronologi: getData(button, 'kronologi'),
                tindakan: getData(button, 'tindakan'),
                hasil: getData(button, 'hasil'),
                pemantauan: getData(button, 'pemantauan'),
                tanggalPemantauan:
                    getData(button, 'tanggalPemantauan'),
                status: getData(button, 'status'),
                komunikasi: getData(button, 'komunikasi'),
                catatanOrangTua:
                    getData(button, 'catatanOrangTua')
            };

            setValue('rpDetailNama', data.nama);
            setValue('rpDetailKelas', data.kelas);
            setValue('rpDetailTanggal', data.tanggal);

            setValue(
                'rpDetailKategori',
                labelKategori[data.kategori] ||
                data.kategori
            );

            setValue(
                'rpDetailTingkat',
                labelTingkat[data.tingkat] ||
                data.tingkat
            );

            setValue(
                'rpDetailJudul',
                data.judul
            );

            setValue(
                'rpDetailKronologi',
                data.kronologi
            );

            setValue(
                'rpDetailTindakan',
                data.tindakan
            );

            setValue(
                'rpDetailHasil',
                data.hasil ||
                'Belum ada hasil pembinaan.'
            );

            setValue(
                'rpDetailPemantauan',
                data.pemantauan === '1'
                    ? 'Diperlukan'
                    : 'Tidak diperlukan'
            );

            setValue(
                'rpDetailTanggalPemantauan',
                data.tanggalPemantauan ||
                'Belum ditentukan'
            );

            setValue(
                'rpDetailStatus',
                labelStatus[data.status] ||
                data.status
            );

            setValue(
                'rpDetailKomunikasi',
                data.komunikasi === '1'
                    ? 'Sudah'
                    : 'Belum'
            );

            setValue(
                'rpDetailCatatanOrangTua',
                data.catatanOrangTua ||
                'Belum ada catatan komunikasi.'
            );

            bukaModal(modalDetail);
        };


        // ==================================================
        // TUTUP DETAIL
        // ==================================================

        window.rpTutupDetail = function () {

            tutupModal(modalDetail);
        };


        // ==================================================
        // HAPUS PEMBINAAN
        // ==================================================

        window.rpKonfirmasiHapus = function (id) {

            if (!id) return;

            const konfirmasi = window.confirm(
                'Apakah Anda yakin ingin menghapus riwayat pembinaan ini?\n\n' +
                'Data yang dihapus tidak dapat dikembalikan.'
            );

            if (!konfirmasi) return;

            const path = getBasePath();

            formHapus.action =
                `${path}/${encodeURIComponent(id)}/hapus`;

            formHapus.submit();
        };


        // ==================================================
        // TUTUP MODAL DENGAN ESCAPE
        // ==================================================

        // Listener dibuat khusus untuk modal halaman ini.
        document.addEventListener(
            'keydown',
            function (event) {

                if (event.key !== 'Escape') return;

                if (modalForm.classList.contains('active')) {

                    window.rpTutupForm();

                } else if (
                    modalDetail.classList.contains('active')
                ) {

                    window.rpTutupDetail();
                }
            }
        );


        // ==================================================
        // INISIALISASI AWAL
        // ==================================================

        updatePemantauan();

        modalForm.setAttribute('aria-hidden', 'true');
        modalDetail.setAttribute('aria-hidden', 'true');

        console.log(
            '[SMPU] Riwayat Pembinaan berhasil diinisialisasi.'
        );

    }


    // ======================================================
    // HALAMAN PERTAMA KALI DIBUKA
    // ======================================================

    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initRiwayatPembinaan,
            { once: true }
        );

    } else {

        initRiwayatPembinaan();

    }


    // ======================================================
    // KETIKA HALAMAN DIBUKA KEMBALI MELALUI SPA
    // ======================================================

    document.addEventListener(
        'spa:page-loaded',
        function () {
            initRiwayatPembinaan();
        }
    );


    // ======================================================
    // KETIKA MENINGGALKAN HALAMAN
    // ======================================================

    document.addEventListener(
        'spa:before-page-unload',
        function () {

            // Bersihkan scroll lock jika modal masih terbuka.
            if (
                document.body.dataset.rpScrollLocked === '1'
            ) {

                document.body.style.position = '';
                document.body.style.top = '';
                document.body.style.left = '';
                document.body.style.right = '';
                document.body.style.width = '';
                document.body.style.overflow = '';

                delete document.body.dataset.rpScrollLocked;
            }

        }
    );

})();
