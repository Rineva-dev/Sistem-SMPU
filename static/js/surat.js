
(() => {
    "use strict";

    // =====================================================
    // PANEL SURAT GLOBAL — SPA SAFE
    // =====================================================

    // Hindari controller dipasang berkali-kali.
    if (window.smpuSuratControllerReady) return;
    window.smpuSuratControllerReady = true;

    // =====================================================
    // STATE
    // =====================================================

    let idSuratAktif = null;

    const CSRF_TOKEN =
        document.querySelector('meta[name="csrf-token"]')?.content || '';

    let tabAktifTerakhir = 'perlu';

    const guruIdSaya = Number(
        typeof GURU_ID_SAYA !== 'undefined' ? GURU_ID_SAYA : 0
    ) || 0;

    let intervalSurat = null;
    let requestDaftarSurat = null;
    let requestDetailSurat = null;
    let requestTindakanSurat = null;

    let modalSuratInstance = null;

    // =====================================================
    // HELPER DOM
    // =====================================================

    function el(id) {
        return document.getElementById(id);
    }

    function panelSurat() {
        return el('panelSurat');
    }

    function tombolSurat() {
        return el('tombolSurat');
    }

    function kontenPanelSurat() {
        return el('kontenPanelSurat');
    }

    function isiDetailSurat() {
        return el('isiDetailSurat');
    }

    function modalDetailSurat() {
        return el('modalDetailSurat');
    }

    function escapeHTML(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function amanURL(value) {
        try {
            const url = new URL(value, window.location.origin);

            if (
                url.protocol === 'http:' ||
                url.protocol === 'https:'
            ) {
                return url.href;
            }

            return '';
        } catch {
            return '';
        }
    }

    function formatTanggal(value) {
        if (!value) return '-';

        const tanggal = new Date(value);

        if (Number.isNaN(tanggal.getTime())) {
            return escapeHTML(value);
        }

        return tanggal.toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    }

    function statusClass(status) {
        return String(status || '')
            .toLowerCase()
            .replace(/[^a-z0-9_-]/g, '-');
    }

    function tampilkanError(wadah, pesan) {
        if (!wadah) return;

        wadah.innerHTML = `
            <div class="text-center p-4 text-danger">
                ${escapeHTML(pesan)}
            </div>
        `;
    }

    // =====================================================
    // FETCH HELPER
    // =====================================================

    async function fetchJSON(url, options = {}) {

        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
            ...options.headers
        };

        if (CSRF_TOKEN) {
            headers['X-CSRFToken'] = CSRF_TOKEN;
        }

        const response = await fetch(url, {
            credentials: 'same-origin',
            ...options,
            headers
        });

        if (!response.ok) {
            throw new Error(`Status: ${response.status}`);
        }

        const contentType =
            response.headers.get('Content-Type') || '';

        if (!contentType.includes('application/json')) {
            throw new Error(
                'Respons bukan JSON. Mungkin sesi login berakhir.'
            );
        }

        return response.json();
    }

    // =====================================================
    // PANEL SURAT
    // =====================================================

    function bukaPanelSurat() {

        const panel = panelSurat();
        const tombol = tombolSurat();

        if (!panel || !tombol) return;

        panel.style.display = 'flex';

        const ikon = tombol.querySelector('.ikon-panah');

        if (ikon) {
            ikon.classList.remove('fa-chevron-up');
            ikon.classList.add('fa-chevron-down');
        }

        muatDaftarSurat(tabAktifTerakhir);
    }

    function tutupPanelSurat() {

        const panel = panelSurat();
        const tombol = tombolSurat();

        if (panel) {
            panel.style.display = 'none';
        }

        const ikon = tombol?.querySelector('.ikon-panah');

        if (ikon) {
            ikon.classList.remove('fa-chevron-down');
            ikon.classList.add('fa-chevron-up');
        }
    }

    function togglePanelSurat() {

        const panel = panelSurat();

        if (!panel) return;

        if (panel.style.display === 'flex') {
            tutupPanelSurat();
        } else {
            bukaPanelSurat();
        }
    }

    // =====================================================
    // TAB SURAT
    // =====================================================

    function pilihTabSurat(tab) {

        if (!tab) return;

        tabAktifTerakhir = tab;

        document.querySelectorAll('.tab-surat').forEach(item => {

            item.classList.toggle(
                'active',
                item.dataset.target === tab
            );

        });

        muatDaftarSurat(tabAktifTerakhir);
    }

    // =====================================================
    // MUAT DAFTAR SURAT
    // =====================================================

    async function muatDaftarSurat(jenis = 'perlu') {

        const wadah = kontenPanelSurat();

        if (!wadah) return;

        // Batalkan request daftar sebelumnya.
        if (requestDaftarSurat) {
            requestDaftarSurat.abort();
        }

        requestDaftarSurat = new AbortController();

        const signal = requestDaftarSurat.signal;

        wadah.innerHTML = `
            <div class="text-center p-4 text-muted">
                <i class="fas fa-spinner fa-spin"></i>
                Memuat daftar surat...
            </div>
        `;

        try {

            const data = await fetchJSON(
                `/surat-global/daftar-surat?jenis=${encodeURIComponent(jenis)}`,
                {
                    signal
                }
            );

            // Jangan update DOM jika halaman sudah berganti.
            if (!document.contains(wadah)) return;

            wadah.innerHTML = '';

            if (!Array.isArray(data.surat) || data.surat.length === 0) {

                wadah.innerHTML = `
                    <div class="text-center p-4 text-muted">
                        Tidak ada surat di kategori ini.
                    </div>
                `;

            } else {

                data.surat.forEach(surat => {

                    const elemen = document.createElement('div');

                    elemen.className =
                        `item-surat status-${statusClass(surat.status)}`;

                    elemen.innerHTML = `
                        <div class="judul-surat">
                            ${escapeHTML(surat.perihal)}
                        </div>

                        <div class="info-surat">
                            No: ${escapeHTML(surat.nomor_surat)}
                            |
                            ${escapeHTML(surat.tanggal_surat)}
                        </div>

                        <div class="info-surat">
                            Status: ${escapeHTML(surat.status)}
                        </div>
                    `;

                    elemen.dataset.suratId = surat.id;

                    wadah.appendChild(elemen);

                });

            }

            // Badge notifikasi.
            const badge = el('jumlahNotif');

            if (badge) {

                const jumlah = Number(data.jumlah || 0);

                if (jumlah > 0) {
                    badge.textContent = jumlah;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }

            }

        } catch (error) {

            if (error.name === 'AbortError') return;

            console.error(
                'Gagal memuat daftar surat:',
                error
            );

            if (document.contains(wadah)) {
                tampilkanError(wadah, error.message);
            }

        }

    }

    // =====================================================
    // DETAIL SURAT
    // =====================================================

    async function bukaDetailSurat(id) {

        if (!id) return;

        idSuratAktif = id;

        tutupPanelSurat();

        const wadah = isiDetailSurat();

        if (!wadah) return;

        if (requestDetailSurat) {
            requestDetailSurat.abort();
        }

        requestDetailSurat = new AbortController();

        const signal = requestDetailSurat.signal;

        wadah.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-spinner fa-spin"></i>
                Memuat detail surat...
            </div>
        `;

        try {

            const surat = await fetchJSON(
                `/surat-global/ambil-detail/${encodeURIComponent(id)}`,
                {
                    signal
                }
            );

            if (!document.contains(wadah)) return;

            wadah.innerHTML = buatHTMLDetailSurat(surat);

            const footerAksi = el('aksiSuratFooter');

            if (footerAksi) {
                footerAksi.style.display =
                    surat.status === 'Diajukan' ? 'flex' : 'none';
            }

            const judulModal = el('judulModalSurat');

            if (judulModal) {
                judulModal.textContent =
                    surat.status === 'Diajukan'
                        ? 'Pemeriksaan Surat'
                        : `Detail Surat - Status: ${surat.status}`;
            }

            tampilkanModalSurat();

        } catch (error) {

            if (error.name === 'AbortError') return;

            console.error(
                'Gagal memuat detail surat:',
                error
            );

            tampilkanError(wadah, error.message);

        }

    }

    // =====================================================
    // HTML DETAIL SURAT
    // =====================================================

    function buatHTMLDetailSurat(surat) {

        const tanggalSurat = formatTanggal(surat.tanggal_surat);

        const tujuan = escapeHTML(surat.tujuan || '-');

        const tujuanHTML = tujuan.replace(
            /(^Kepada\s*[\r\n]*Yth\.\s*)([\s\S]*?)([\r\n]+\s*di\s+[\s\S]*)$/i,
            '$1<strong>$2</strong>$3'
        );

        const daftarTtd = Array.isArray(surat.penandatangan)
            ? surat.penandatangan
            : [];

        const posisiKepala = daftarTtd.findIndex(ttd =>
            String(ttd.jabatan || '').trim().toLowerCase() ===
            'kepala sekolah'
        );

        const adaKepala = posisiKepala !== -1;

        const htmlTtd = buatHTMLTandaTangan(
            daftarTtd,
            posisiKepala,
            adaKepala,
            surat
        );

        return `
            <!-- KOP SURAT -->

            <div class="kop-surat">

                <div class="kop-konten">

                    <img
                        src="/static/img/logo-school.svg"
                        alt="Logo SMP Unggulan Hamzanwadi"
                        class="kop-logo"
                    >

                    <div class="kop-pemisah"></div>

                    <div class="kop-teks-kanan">

                        <div class="kop-izin">
                            IZIN OPERASIONAL:
                            500.16.7.2/97/PMPTSP-SMP/01/2025
                        </div>

                        <div class="kop-kontak">

                            <i class="fa-brands fa-whatsapp-square"></i>
                            <span>081915780964</span>

                            <i class="fa-solid fa-envelope"></i>
                            <span>smpu@hamzanwadi.ac.id</span>

                        </div>

                        <div class="kop-alamat">
                            Jl. Dr. Ciptromangun Kusumo, Sawing,
                            Kel. Majidi, Kec. Selong,
                            Kab. Lombok Timur - NTB
                        </div>

                    </div>

                </div>

            </div>

            <!-- ISI SURAT -->

            <div class="surat-kepala">

                <span class="label">Nomor</span>
                <span class="value">
                    : ${escapeHTML(surat.nomor_surat)}
                </span>

                <span class="label">Lampiran</span>
                <span class="value">
                    : ${escapeHTML(surat.lampiran || '-')}
                </span>

                <span class="label">Hal</span>
                <span class="value">
                    : <strong>${escapeHTML(surat.perihal)}</strong>
                </span>

            </div>

            <div class="surat-tujuan">
                <p>${tujuanHTML}</p>
            </div>

            <div class="surat-isi">

                <p>
                    <strong>
                        <em>Bismillahiwabihamdihi</em>
                    </strong>
                </p>

                <p class="salam">
                    <em>
                        <strong>
                            Assalamu'alaikum Warahmatullahi Wabarakatuh
                        </strong>
                    </em>
                </p>

                <p>
                    Semoga kami menjumpai Bapak/Ibu dalam keadaan
                    sehat wal'afiat serta dalam limpahan Rahmat dan
                    taufik dari Allah SWT. sehingga dapat beraktivitas
                    seperti biasanya. Aamiin ya Rabbal Alamin.
                </p>

                <p class="isi">
                    ${escapeHTML(surat.isi_surat)}
                </p>

                <p class="wassalam">
                    <strong>
                        <em>
                            Wallohul Muwaffiq Wal Hadi ila Sabi Lirrosyad
                        </em>
                    </strong>
                </p>

                <p>
                    <strong>
                        <em>
                            Wassalamu'alaikum Warahmatullahi Wabarakatuh
                        </em>
                    </strong>
                </p>

            </div>

            <!-- TANDA TANGAN -->

            <div class="surat-ttd" style="color: black;">

                <p style="text-align:right; margin:1rem 0 0;">
                    Majidi, ${tanggalSurat}
                </p>

                ${htmlTtd}

            </div>
        `;

    }

    // =====================================================
    // BLOK TANDA TANGAN
    // =====================================================

    function buatBlokTtd(ttd, surat) {

        const jabatan = escapeHTML(ttd.jabatan || '');
        const nama = escapeHTML(ttd.nama || '');
        const nip = escapeHTML(ttd.nip || '-');

        let qr = '';

        if (ttd.ttd_selesai && ttd.qr_code) {

            const qrPath = amanURL(
                `/static/${String(ttd.qr_code).replace(/^\/+/, '')}`
            );

            qr = qrPath
                ? `
                    <div
                        class="qr-verifikasi"
                        style="margin:0 auto;text-align:center;"
                    >

                        <img
                            src="${escapeHTML(qrPath)}"
                            alt="QR Verifikasi Elektronik"
                            style="
                                width:80px;
                                height:80px;
                                object-fit:contain;
                            "
                        >

                        <p style="font-size:8pt;margin:0;color:#333;">
                            Ditandatangani secara elektronik
                        </p>

                    </div>
                `
                : '';

        } else {

            qr = `
                <p style="font-size:9pt;color:#888;margin:0 auto;">
                    Belum ditandatangani
                </p>
            `;

        }

        let tombolTtd = '';

        if (
            surat.status === 'Diajukan' &&
            !ttd.ttd_selesai &&
            Number(ttd.id_guru) === guruIdSaya
        ) {

            tombolTtd = `
                <button
                    type="button"
                    class="btn btn-sm btn-primary mt-2"
                    data-aksi-surat="setuju"
                    data-id-ttd="${escapeHTML(ttd.id)}"
                >
                    Tanda Tangan &amp; Setujui
                </button>
            `;

        }

        return `
            <div style="text-align:center;">

                <p style="margin:0 0 .75rem 0;">
                    ${jabatan}
                </p>

                ${qr}

                <p style="margin:0;">
                    <strong>${nama}</strong>
                </p>

                <p style="margin:0;">
                    NIP. ${nip}
                </p>

                ${tombolTtd}

            </div>
        `;

    }

    // =====================================================
    // LAYOUT TANDA TANGAN
    // =====================================================

    function buatHTMLTandaTangan(
        daftarTtd,
        posisiKepala,
        adaKepala,
        surat
    ) {

        const jumlah = daftarTtd.length;

        if (!jumlah) {
            return '';
        }

        const blok = ttd =>
            buatBlokTtd(ttd, surat);

        const kolom = (a, b) => `
            <div
                style="
                    display:flex;
                    justify-content:space-between;
                    width:100%;
                    padding:0 8%;
                "
            >
                <div style="width:45%;text-align:center;">
                    ${blok(a)}
                </div>

                <div style="width:45%;text-align:center;">
                    ${blok(b)}
                </div>
            </div>
        `;

        const labelMengetahui = (posisi) => `
            <div
                style="
                    display:flex;
                    justify-content:space-between;
                    width:100%;
                    padding:0 8%;
                "
            >
                <p style="width:45%;text-align:center;margin:0;">
                    ${posisi === 0 ? 'Mengetahui,' : '&nbsp;'}
                </p>

                <p style="width:45%;text-align:center;margin:0;">
                    ${posisi === 1 ? 'Mengetahui,' : '&nbsp;'}
                </p>
            </div>
        `;

        // ---------------------------------------------
        // 1 PENANDATANGAN
        // ---------------------------------------------

        if (jumlah === 1) {

            return `
                <div
                    style="
                        margin-left:65%;
                        text-align:left;
                        width:max-content;
                    "
                >
                    ${blok(daftarTtd[0])}
                </div>
            `;

        }

        // ---------------------------------------------
        // 2 PENANDATANGAN
        // ---------------------------------------------

        if (jumlah === 2) {

            if (adaKepala) {

                return `
                    ${labelMengetahui(posisiKepala)}
                    ${kolom(daftarTtd[0], daftarTtd[1])}
                `;

            }

            return kolom(
                daftarTtd[0],
                daftarTtd[1]
            );

        }

        // ---------------------------------------------
        // 3 PENANDATANGAN
        // ---------------------------------------------

        if (jumlah === 3) {

            if (adaKepala && posisiKepala === 2) {

                return `
                    ${kolom(daftarTtd[0], daftarTtd[1])}

                    <div
                        style="
                            width:100%;
                            text-align:center;
                            margin-top:1rem;
                        "
                    >
                        <p style="margin:0;">Mengetahui,</p>
                        ${blok(daftarTtd[2])}
                    </div>
                `;

            }

            return `
                ${labelMengetahui(posisiKepala)}
                ${kolom(daftarTtd[0], daftarTtd[1])}

                <div
                    style="
                        width:100%;
                        text-align:center;
                        margin-top:1.5rem;
                    "
                >
                    ${blok(daftarTtd[2])}
                </div>
            `;

        }

        // ---------------------------------------------
        // 4 PENANDATANGAN
        // ---------------------------------------------

        if (jumlah === 4) {

            if (adaKepala && posisiKepala >= 2) {

                return `
                    ${kolom(daftarTtd[0], daftarTtd[1])}

                    ${labelMengetahui(posisiKepala - 2)}

                    ${kolom(daftarTtd[2], daftarTtd[3])}
                `;

            }

            return `
                ${labelMengetahui(posisiKepala)}

                ${kolom(daftarTtd[0], daftarTtd[1])}

                ${kolom(daftarTtd[2], daftarTtd[3])}
            `;

        }

        // ---------------------------------------------
        // LEBIH DARI 4 PENANDATANGAN
        // ---------------------------------------------

        let hasil = '';

        for (let i = 0; i < jumlah; i += 2) {

            const pertama = daftarTtd[i];
            const kedua = daftarTtd[i + 1];

            if (kedua) {

                hasil += kolom(pertama, kedua);

            } else {

                hasil += `
                    <div
                        style="
                            width:100%;
                            text-align:center;
                            margin-top:1rem;
                        "
                    >
                        ${blok(pertama)}
                    </div>
                `;

            }

        }

        return hasil;

    }

    // =====================================================
    // MODAL DETAIL
    // =====================================================

    function tampilkanModalSurat() {

        const modalElement = modalDetailSurat();

        if (!modalElement) return;

        if (
            typeof bootstrap === 'undefined' ||
            !bootstrap.Modal
        ) {
            console.warn('Bootstrap Modal belum tersedia.');
            return;
        }

        modalSuratInstance =
            bootstrap.Modal.getOrCreateInstance(modalElement);

        modalSuratInstance.show();

    }

    function tutupModalSurat() {

        const modalElement = modalDetailSurat();

        if (!modalElement) return;

        if (
            typeof bootstrap !== 'undefined' &&
            bootstrap.Modal
        ) {

            const instance =
                bootstrap.Modal.getInstance(modalElement);

            if (instance) {
                instance.hide();
            }

        }

    }

    // =====================================================
    // PROSES PERSETUJUAN / TANDA TANGAN
    // =====================================================

    async function prosesTindakan(tindakan, idTtd = null) {

        if (!idSuratAktif) {
            alert('ID surat tidak ditemukan.');
            return;
        }

        const catatan =
            el('catatanPersetujuan')?.value.trim() || '';

        // Validasi perbaiki / tolak.
        if (
            (tindakan === 'perbaiki' || tindakan === 'tolak') &&
            !catatan
        ) {

            alert(
                '⚠️ Silakan tulis alasan/catatan terlebih dahulu!'
            );

            return;
        }

        // Validasi tanda tangan.
        if (tindakan === 'setuju' && !idTtd) {

            alert(
                '❌ ID penandatangan tidak ditemukan, gunakan tombol di bawah nama Anda!'
            );

            return;
        }

        if (requestTindakanSurat) {
            requestTindakanSurat.abort();
        }

        requestTindakanSurat = new AbortController();

        const signal = requestTindakanSurat.signal;

        const body = new URLSearchParams();

        body.set('tindakan', tindakan);
        body.set('id_ttd', idTtd || '');
        body.set('catatan', catatan);

        try {

            const hasil = await fetchJSON(
                `/surat-global/proses-persetujuan/${encodeURIComponent(idSuratAktif)}`,
                {
                    method: 'POST',
                    signal,
                    headers: {
                        'Content-Type':
                            'application/x-www-form-urlencoded'
                    },
                    body: body.toString()
                }
            );

            if (hasil.success === false) {
                throw new Error(
                    hasil.pesan || 'Proses surat gagal.'
                );
            }

            alert(hasil.pesan || 'Surat berhasil diproses.');

            tutupModalSurat();

            const inputCatatan = el('catatanPersetujuan');

            if (inputCatatan) {
                inputCatatan.value = '';
            }

            await muatDaftarSurat(tabAktifTerakhir);

        } catch (error) {

            if (error.name === 'AbortError') return;

            console.error(
                'Gagal memproses surat:',
                error
            );

            alert(
                error.message ||
                '❌ Terjadi kesalahan saat memproses surat'
            );

        }

    }

    // =====================================================
    // EVENT DELEGATION
    //
    // Listener dipasang sekali di document.
    // Tidak perlu init ulang setelah SPA.
    // =====================================================

    document.addEventListener('click', function (event) {

        const target = event.target;

        if (!(target instanceof Element)) return;

        // ---------------------------------------------
        // BUKA / TUTUP PANEL SURAT
        // ---------------------------------------------

        const tombol = target.closest('#tombolSurat');

        if (tombol) {

            event.preventDefault();
            event.stopPropagation();

            togglePanelSurat();

            return;
        }

        // ---------------------------------------------
        // PILIH TAB
        // ---------------------------------------------

        const tab = target.closest('.tab-surat');

        if (tab) {

            event.preventDefault();

            pilihTabSurat(tab.dataset.target);

            return;
        }

        // ---------------------------------------------
        // PILIH ITEM SURAT
        // ---------------------------------------------

        const itemSurat = target.closest('.item-surat');

        if (itemSurat) {

            const id = itemSurat.dataset.suratId;

            if (id) {
                bukaDetailSurat(id);
            }

            return;
        }

        // ---------------------------------------------
        // TOMBOL TANDA TANGAN
        // ---------------------------------------------

        const tombolTtd = target.closest(
            '[data-aksi-surat="setuju"]'
        );

        if (tombolTtd) {

            event.preventDefault();

            const idTtd = tombolTtd.dataset.idTtd;

            prosesTindakan('setuju', idTtd);

            return;
        }

        // ---------------------------------------------
        // PANEL SURAT
        // ---------------------------------------------

        const panel = panelSurat();
        const tombolPanel = tombolSurat();

        if (
            panel &&
            tombolPanel &&
            !panel.contains(target) &&
            !tombolPanel.contains(target)
        ) {

            tutupPanelSurat();

        }

    });

    // =====================================================
    // SPA LIFECYCLE
    // =====================================================

    function bersihkanRequest() {

        if (requestDaftarSurat) {
            requestDaftarSurat.abort();
            requestDaftarSurat = null;
        }

        if (requestDetailSurat) {
            requestDetailSurat.abort();
            requestDetailSurat = null;
        }

        if (requestTindakanSurat) {
            requestTindakanSurat.abort();
            requestTindakanSurat = null;
        }

    }

    function hentikanPollingSurat() {

        if (intervalSurat !== null) {

            clearInterval(intervalSurat);

            intervalSurat = null;

        }

    }

    function mulaiPollingSurat() {

        hentikanPollingSurat();

        intervalSurat = setInterval(() => {

            const panel = panelSurat();

            if (!panel) return;

            if (panel.style.display === 'flex') {

                muatDaftarSurat(tabAktifTerakhir);

            }

        }, 10000);

    }

    function initSurat() {

        // Set tab awal dari tab aktif di HTML.
        const tabAktif = document.querySelector(
            '.tab-surat.active'
        );

        if (tabAktif?.dataset.target) {
            tabAktifTerakhir = tabAktif.dataset.target;
        }

        // Muat daftar awal.
        muatDaftarSurat(tabAktifTerakhir);

        // Polling satu kali saja.
        mulaiPollingSurat();

    }

    // Ketika SPA akan mengganti halaman.
    document.addEventListener(
        'spa:before-page-unload',
        function () {

            tutupPanelSurat();

            tutupModalSurat();

            bersihkanRequest();

            hentikanPollingSurat();

        }
    );

    // Ketika SPA selesai memuat halaman.
    document.addEventListener(
        'spa:page-loaded',
        function () {

            // Header / panel surat mungkin tidak ada di halaman ini.
            if (!tombolSurat() || !panelSurat()) {

                hentikanPollingSurat();

                bersihkanRequest();

                return;
            }

            initSurat();

        }
    );

    // =====================================================
    // INITIAL LOAD
    // =====================================================

    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initSurat,
            { once: true }
        );

    } else {

        initSurat();

    }

    // =====================================================
    // GLOBAL API
    //
    // Dibutuhkan jika ada tombol HTML lain yang masih
    // memanggil prosesTindakan() secara inline.
    // =====================================================

    window.prosesTindakan = prosesTindakan;

    window.muatDaftarSurat = muatDaftarSurat;

    window.bukaDetailSurat = bukaDetailSurat;

    window.tutupPanelSurat = tutupPanelSurat;

})();
