
/* =========================================================
   SMPU ATTENDANCE CENTER
   Premium Attendance Workspace
   SPA-safe · QR · Camera · Modal · Pagination
========================================================= */

(function () {
    'use strict';

    const runtime = window.__absensiHarianRuntime || {
        intervalJam: null,
        root: null,
        kameraStream: null,
        pemindaianAktif: false,
        dataQRTerlambat: null,
        frameScan: null,
        serverTimeAnchor: null,
        intervalSinkronisasi: null
    };

    window.__absensiHarianRuntime = runtime;

    const getConfig = () => window.ABSENSI || {};
    const getPagination = () => window.PAGINASI || {};

    /* =====================================================
       NOTIFICATION FALLBACK
    ===================================================== */

    
    function tampilkanNotifikasi(pesan, tipe = 'info') {

        // Gunakan sistem notifikasi global jika tersedia.
        if (window.notif && typeof window.notif.tampil === 'function') {
            const ikon = {
                sukses: 'fa-check-circle',
                error: 'fa-times-circle',
                peringatan: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };

            window.notif.tampil(
                `<i class="fas ${ikon[tipe] || ikon.info}"></i> ${pesan}`,
                tipe
            );

            return;
        }

        // Gunakan modal premium dari notif_custom.js.
        const notifGlobal = {
            sukses: window.notifSukses,
            error: window.notifError,
            peringatan: window.notifPeringatan,
            info: window.notifInfo
        };

        const tampilkan = notifGlobal[tipe] || window.notifInfo;

        if (typeof tampilkan === 'function') {
            tampilkan(pesan);
            return;
        }

        // Fallback terakhir jika sistem notifikasi belum tersedia.
        window.alert(pesan);
    }


    function notifSukses(pesan) {
        tampilkanNotifikasi(pesan, 'sukses');
    }

    function notifError(pesan) {
        tampilkanNotifikasi(pesan, 'error');
    }

    function notifInfo(pesan) {
        tampilkanNotifikasi(pesan, 'info');
    }

    function notifPeringatan(pesan) {
        tampilkanNotifikasi(pesan, 'peringatan');
    }
    
    
    /* =========================================================
    WITA CLOCK — SERVER SYNCHRONIZED
    ========================================================= */

    function ambilWaktuWITA() {
        if (runtime.serverTimeAnchor) {
            const elapsed =
                performance.now() - runtime.serverTimeAnchor.performanceTime;

            return new Date(
                runtime.serverTimeAnchor.timestamp + elapsed
            );
        }

        // Fallback sebelum sinkronisasi server berhasil.
        return new Date();
    }


    /* FORMAT JAM WITA */

    function formatJamWITA(denganDetik = true) {
        const waktu = ambilWaktuWITA();

        return new Intl.DateTimeFormat('id-ID', {
            timeZone: 'Asia/Makassar',
            hour: '2-digit',
            minute: '2-digit',
            ...(denganDetik ? { second: '2-digit' } : {}),
            hourCycle: 'h23'
        }).format(waktu).replace(/\./g, ':');
    }


    /* JAM UNTUK VALIDASI ABSENSI */

    function ambilJamSaatIni() {
        return formatJamWITA(true).slice(0, 5);
    }


    /* SINKRONISASI DENGAN SERVER */

    async function sinkronkanWaktuServer() {
        const config = getConfig();
        const url = config.URL_SERVER_TIME || '/api/server-time';

        // Simpan halaman yang sedang aktif.
        const rootSaatMulai = runtime.root;

        try {
            const waktuMulai = performance.now();

            const response = await fetch(url, {
                method: 'GET',
                cache: 'no-store',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const waktuSelesai = performance.now();

            if (!response.ok) {
                throw new Error('Gagal mengambil waktu server.');
            }

            const data = await response.json();

            if (
                data.status !== 'success' ||
                !Number.isFinite(Number(data.timestamp))
            ) {
                throw new Error('Format waktu server tidak valid.');
            }

            // Jangan memperbarui waktu jika halaman sudah ditinggalkan.
            if (
                !rootSaatMulai ||
                runtime.root !== rootSaatMulai ||
                !rootSaatMulai.isConnected
            ) {
                return false;
            }

            // Gunakan titik tengah waktu request untuk mengurangi
            // pengaruh keterlambatan jaringan.
            runtime.serverTimeAnchor = {
                timestamp: Number(data.timestamp),
                performanceTime: (waktuMulai + waktuSelesai) / 2
            };

            updateClock();

            return true;

        } catch (error) {
            console.warn(
                'Sinkronisasi waktu server gagal:',
                error
            );

            return false;
        }
    }


    /* PERBARUI JAM DIGITAL */

    function updateClock() {
        const jam = formatJamWITA(true);
        const jamTanpaDetik = formatJamWITA(false);

        const jamDigital = document.getElementById('jam-digital');

        if (jamDigital) {
            jamDigital.textContent = jam;
        }

        const jamHP = document.getElementById('hp-jam');

        if (jamHP) {
            const ikon = jamHP.querySelector('i');

            jamHP.textContent = '';

            if (ikon) {
                jamHP.appendChild(ikon);
            }

            jamHP.appendChild(
                document.createTextNode(` ${jamTanpaDetik}`)
            );
        }
    }


    /* =====================================================
       TIME VALIDATION — CLIENT SIDE ONLY
    ===================================================== */

    function jamKeMenit(jamStr) {
        if (!jamStr || typeof jamStr !== 'string') {
            return 0;
        }

        const bagian = jamStr.split(':').map(Number);

        if (
            bagian.length < 2 ||
            !Number.isFinite(bagian[0]) ||
            !Number.isFinite(bagian[1])
        ) {
            return 0;
        }

        return (bagian[0] * 60) + bagian[1];
    }

    function sudahLewatBatasWaktu() {
        const batas = getConfig().BATAS_TUTUP_ABSENSI;
        return jamKeMenit(ambilJamSaatIni()) >= jamKeMenit(batas);
    }

    function belumJamPulang() {
        const batas = getConfig().BATAS_PULANG;
        return jamKeMenit(ambilJamSaatIni()) < jamKeMenit(batas);
    }

    function tampilkanPeringatanAlfa() {
        const batas =
            getConfig().BATAS_TUTUP_ABSENSI || '--:--';

        notifPeringatan(
            `Absensi sudah ditutup pada pukul <strong>${batas}</strong>.`
        );
    }

    function tampilkanPeringatanBelumJamPulang() {
        notifInfo(
            `Absen pulang baru dapat dilakukan mulai pukul ${getConfig().BATAS_PULANG}.`
        );
    }


    /* =====================================================
       FORM POST
    ===================================================== */

    function kirimFormPost(url, data = {}) {
        const form = document.createElement('form');

        form.method = 'POST';
        form.action = url;
        form.style.display = 'none';

        Object.entries(data).forEach(([nama, nilai]) => {
            const input = document.createElement('input');

            input.type = 'hidden';
            input.name = nama;
            input.value = nilai;

            form.appendChild(input);
        });

        document.body.appendChild(form);
        form.submit();
    }

    function kirimAbsenMasuk(alasan = '') {
        const config = getConfig();

        const data = {};

        if (alasan) {
            data.alasan_keterlambatan = alasan;
        }

        kirimFormPost(config.URL_ABSEN_MASUK, data);
    }

    function kirimAbsenPulang() {
        if (belumJamPulang()) {
            tampilkanPeringatanBelumJamPulang();
            return;
        }

        kirimFormPost(getConfig().URL_ABSEN_PULANG);
    }


    /* =====================================================
       MODAL HELPERS
    ===================================================== */

    function bukaModal(overlay, modal) {
        if (!overlay || !modal) return false;

        overlay.style.display = 'block';
        modal.style.display = 'block';

        requestAnimationFrame(() => {
            overlay.classList.add('active');
            modal.classList.add('active');
        });

        return true;
    }

    function tutupModal(overlay, modal) {
        if (!overlay || !modal) return;

        overlay.classList.remove('active');
        modal.classList.remove('active');

        window.setTimeout(() => {
            overlay.style.display = 'none';
            modal.style.display = 'none';
        }, 280);
    }


    /* =====================================================
       CAMERA CLEANUP
    ===================================================== */

    function hentikanKamera() {
        runtime.pemindaianAktif = false;

        if (runtime.frameScan) {
            cancelAnimationFrame(runtime.frameScan);
            runtime.frameScan = null;
        }

        if (runtime.kameraStream) {
            runtime.kameraStream.getTracks().forEach(track => {
                track.stop();
            });

            runtime.kameraStream = null;
        }

        const video = document.getElementById('video-kamera');

        if (video) {
            video.pause();
            video.srcObject = null;
        }
    }

    function tutupModalKamera() {
        hentikanKamera();

        const overlay = document.getElementById('modal-kamera-overlay');
        const modal = document.getElementById('modal-kamera');

        tutupModal(overlay, modal);
    }

    /* =====================================================
       QR RESULT
    ===================================================== */

    async function kirimHasilQR(dataQR, alasanKeterlambatan = '') {
        const config = getConfig();

        try {
            const response = await fetch(config.URL_SCAN_QR_PROSES, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    data_qr: dataQR,
                    alasan_keterlambatan: alasanKeterlambatan
                })
            });

            const hasil = await response.json();

            if (
                response.ok &&
                (hasil.status === 'sukses' || hasil.status === 'info')
            ) {
                notifSukses(hasil.pesan || 'Absensi berhasil dicatat.');

                window.setTimeout(() => {
                    window.location.reload();
                }, 1000);

                return true;
            }

            notifError(hasil.pesan || 'QR tidak dapat diproses.');
            return false;

        } catch (error) {
            notifError(`Terjadi kesalahan: ${error.message}`);
            return false;
        }
    }

    async function prosesHasilScan(dataQR) {
        hentikanKamera();

        const overlayKamera = document.getElementById('modal-kamera-overlay');
        const modalKamera = document.getElementById('modal-kamera');

        tutupModal(overlayKamera, modalKamera);

        const sudahMasuk = !!getConfig().SUDAH_ABSEN_MASUK;

        if (!sudahMasuk) {
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }

            const sekarang = jamKeMenit(ambilJamSaatIni());
            const batasTerlambat = jamKeMenit(
                getConfig().BATAS_TERLAMBAT
            );

            if (sekarang > batasTerlambat) {
                runtime.dataQRTerlambat = dataQR;
                bukaModalAlasanTelat(ambilJamSaatIni());
                return;
            }
        } else if (belumJamPulang()) {
            tampilkanPeringatanBelumJamPulang();
            return;
        }

        await kirimHasilQR(dataQR);
    }


    /* =====================================================
       LATE ARRIVAL MODAL
    ===================================================== */

    function bukaModalAlasanTelat(jamSaatIni) {
        const overlay = document.getElementById('modal-telat-overlay');
        const modal = document.getElementById('modal-telat');
        const jam = document.getElementById('jam-saat-ini');
        const textarea = document.getElementById('alasan-keterlambatan');

        if (jam) {
            jam.textContent = jamSaatIni;
        }

        if (textarea) {
            textarea.value = '';
        }

        bukaModal(overlay, modal);

        window.setTimeout(() => {
            textarea?.focus();
        }, 300);
    }

    function tutupModalTelat() {
        tutupModal(
            document.getElementById('modal-telat-overlay'),
            document.getElementById('modal-telat')
        );
    }

    async function simpanAlasanTerlambat() {
        const textarea = document.getElementById('alasan-keterlambatan');
        const tombol = document.getElementById('modal-telat-simpan');

        const alasan = textarea?.value.trim() || '';

        if (!alasan) {
            notifPeringatan('Silakan tuliskan alasan keterlambatan terlebih dahulu.');
            textarea?.focus();
            return;
        }

        if (tombol?.disabled) return;

        if (tombol) {
            tombol.disabled = true;
        }

        const dataQR = runtime.dataQRTerlambat;

        if (dataQR) {
            tutupModalTelat();

            const berhasil = await kirimHasilQR(dataQR, alasan);

            if (berhasil) {
                runtime.dataQRTerlambat = null;
            }
        } else {
            kirimAbsenMasuk(alasan);
        }

        if (tombol) {
            tombol.disabled = false;
        }
    }


    /* =====================================================
       QR DISPLAY MODAL
    ===================================================== */

    async function bukaModalQR() {
        const config = getConfig();
        const sudahMasuk = !!config.SUDAH_ABSEN_MASUK;

        if (!sudahMasuk && sudahLewatBatasWaktu()) {
            tampilkanPeringatanAlfa();
            return;
        }

        if (sudahMasuk && belumJamPulang()) {
            tampilkanPeringatanBelumJamPulang();
            return;
        }

        const overlay = document.getElementById('modal-qr-overlay');
        const modal = document.getElementById('modal-qr');

        const tempatQR = document.getElementById('qr-tempat-tampil');
        const namaGuru = document.getElementById('qr-nama-guru');
        const nipGuru = document.getElementById('qr-nip-guru');
        const tanggal = document.getElementById('qr-tanggal-hariini');

        if (tempatQR) {
            tempatQR.innerHTML = '<em>Menyiapkan QR absensi...</em>';
        }

        if (namaGuru) namaGuru.textContent = '';
        if (nipGuru) nipGuru.textContent = '-';
        if (tanggal) tanggal.textContent = '';

        bukaModal(overlay, modal);

        try {
            const response = await fetch(config.URL_QR_DATA, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (!response.ok || data.status !== 'sukses') {
                throw new Error(data.pesan || 'QR gagal dimuat.');
            }

            if (tempatQR) {
                const image = document.createElement('img');

                image.src = `data:image/png;base64,${data.qr_code}`;
                image.alt = 'QR Absensi';

                tempatQR.replaceChildren(image);
            }

            if (namaGuru) namaGuru.textContent = data.nama || '';
            if (nipGuru) nipGuru.textContent = data.nip || '-';
            if (tanggal) tanggal.textContent = data.hari_ini || '-';

        } catch (error) {
            if (tempatQR) {
                tempatQR.textContent = error.message || 'Gagal memuat QR.';
            }

            notifError(error.message || 'Gagal memuat QR absensi.');
        }
    }


    /* =====================================================
       CAMERA SCANNER
    ===================================================== */

    async function bukaKamera() {
        const config = getConfig();
        const sudahMasuk = !!config.SUDAH_ABSEN_MASUK;

        if (!sudahMasuk && sudahLewatBatasWaktu()) {
            tampilkanPeringatanAlfa();
            return;
        }

        if (sudahMasuk && belumJamPulang()) {
            tampilkanPeringatanBelumJamPulang();
            return;
        }

        if (!navigator.mediaDevices?.getUserMedia) {
            notifError(
                'Browser tidak mendukung kamera. Pastikan halaman dibuka melalui HTTPS.'
            );
            return;
        }

        const video = document.getElementById('video-kamera');
        const status = document.getElementById('kamera-status');

        if (!video) return;

        try {
            hentikanKamera();

            if (status) {
                status.textContent = 'Meminta akses kamera...';
            }

            runtime.kameraStream =
                await navigator.mediaDevices.getUserMedia({
                    audio: false,
                    video: {
                        facingMode: { ideal: 'environment' },
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                });

            video.srcObject = runtime.kameraStream;

            await video.play();

            if (status) {
                status.innerHTML = sudahMasuk
                    ? '<i class="fas fa-qrcode"></i> Scan QR untuk Absen Pulang'
                    : '<i class="fas fa-qrcode"></i> Scan QR untuk Absen Masuk';

                status.classList.add('scanning');
            }

            bukaModal(
                document.getElementById('modal-kamera-overlay'),
                document.getElementById('modal-kamera')
            );

            runtime.pemindaianAktif = true;

            const canvas = document.getElementById('kanvas-pemindai');

            if (!canvas) {
                throw new Error('Elemen pemindai tidak ditemukan.');
            }

            window.setTimeout(() => {
                bacaDariKanvas(canvas, video);
            }, 400);

        } catch (error) {
            hentikanKamera();

            let pesan = 'Tidak dapat membuka kamera.';

            if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
                pesan =
                    'Akses kamera ditolak. Periksa izin kamera pada pengaturan browser.';
            } else if (error.name === 'NotFoundError') {
                pesan = 'Kamera tidak ditemukan pada perangkat.';
            } else if (error.name === 'NotReadableError') {
                pesan = 'Kamera sedang digunakan aplikasi lain.';
            } else if (error.name === 'OverconstrainedError') {
                pesan = 'Kamera tidak mendukung konfigurasi yang diminta.';
            } else {
                pesan = error.message || pesan;
            }

            if (status) {
                status.textContent = pesan;
            }

            notifError(pesan);
        }
    }

    function bacaDariKanvas(canvas, video) {
        if (!runtime.pemindaianAktif) return;

        if (
            !video ||
            video.readyState < 2 ||
            !video.videoWidth ||
            !video.videoHeight
        ) {
            runtime.frameScan = requestAnimationFrame(
                () => bacaDariKanvas(canvas, video)
            );
            return;
        }

        if (!window.jsQR) {
            const status = document.getElementById('kamera-status');

            if (status) {
                status.textContent = 'Menunggu pustaka pemindai QR...';
            }

            runtime.frameScan = requestAnimationFrame(
                () => bacaDariKanvas(canvas, video)
            );
            return;
        }

        try {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            const context = canvas.getContext('2d', {
                willReadFrequently: true
            });

            if (!context) {
                throw new Error('Canvas tidak dapat diinisialisasi.');
            }

            context.drawImage(
                video,
                0,
                0,
                canvas.width,
                canvas.height
            );

            const skala = 0.72;
            const lebarPotong = Math.floor(canvas.width * skala);
            const tinggiPotong = Math.floor(canvas.height * skala);

            const x = Math.floor((canvas.width - lebarPotong) / 2);
            const y = Math.floor((canvas.height - tinggiPotong) / 2);

            const gambar = context.getImageData(
                x,
                y,
                lebarPotong,
                tinggiPotong
            );

            const hasil = window.jsQR(
                gambar.data,
                gambar.width,
                gambar.height,
                {
                    inversionAttempts: 'attemptBoth'
                }
            );

            if (hasil?.data) {
                runtime.pemindaianAktif = false;

                const status = document.getElementById('kamera-status');

                if (status) {
                    status.innerHTML =
                        '<i class="fas fa-check-circle"></i> QR terdeteksi, memproses...';

                    status.classList.remove('scanning');
                }

                prosesHasilScan(hasil.data);
                return;
            }

        } catch (error) {
            // Pemindaian dilanjutkan pada frame berikutnya.
        }

        runtime.frameScan = requestAnimationFrame(
            () => bacaDariKanvas(canvas, video)
        );
    }


    /* =====================================================
       FILTER & PAGINATION
    ===================================================== */

    function buatURLDenganParameter(parameter = {}) {
        const config = getConfig();
        const url = new URL(
            config.URL_ABSENSI_HARIAN,
            window.location.origin
        );

        Object.entries(parameter).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                url.searchParams.set(key, value);
            }
        });

        return url.toString();
    }

    function terapkanFilterDanPaginasi() {
        const bulan = document.getElementById('filter-bulan')?.value || '';
        const tahun = document.getElementById('filter-tahun')?.value || '';

        const pagination = getPagination();

        const url = buatURLDenganParameter({
            bulan,
            tahun,
            halaman: pagination.halaman_sekarang || 1,
            per_halaman: pagination.per_halaman || 10
        });

        window.location.href = url;
    }

    function terapkanFilter() {
        const pagination = getPagination();

        pagination.halaman_sekarang = 1;

        terapkanFilterDanPaginasi();
    }

    function terapkanFilterTanggal(nilai) {
        if (!nilai) return;

        const url = buatURLDenganParameter({
            tanggal: nilai
        });

        window.location.href = url;
    }

    window.terapkanFilter = terapkanFilter;
    window.terapkanFilterTanggal = terapkanFilterTanggal;


    function perbaruiTeksPaginasi() {
        const pagination = getPagination();

        const total = document.getElementById('total-data');
        const jumlah = document.getElementById('jumlah-per-halaman');

        if (total) {
            total.textContent = pagination.total_data || 0;
        }

        if (jumlah) {
            jumlah.value = pagination.per_halaman || 10;
        }
    }

    function hitungTotalHalaman() {
        const pagination = getPagination();

        const totalData = Math.max(
            0,
            Number(pagination.total_data) || 0
        );

        const perHalaman = Math.max(
            1,
            Number(pagination.per_halaman) || 10
        );

        return Math.max(1, Math.ceil(totalData / perHalaman));
    }

    function renderTombolPaginasi() {
        const wadah = document.getElementById('tombol-paginasi');

        if (!wadah) return;

        const pagination = getPagination();

        const totalHalaman = hitungTotalHalaman();
        const halamanAktif = Math.max(
            1,
            Math.min(
                totalHalaman,
                Number(pagination.halaman_sekarang) || 1
            )
        );

        const batas = Math.max(
            3,
            Number(pagination.batas_tampil_tombol) || 5
        );

        wadah.replaceChildren();

        function buatTombol(label, halaman, aktif = false, disabled = false) {
            const tombol = document.createElement('button');

            tombol.type = 'button';
            tombol.className =
                'page-btn' +
                (aktif ? ' active' : '') +
                (disabled ? ' disabled' : '');

            tombol.textContent = label;
            tombol.disabled = disabled;

            if (!disabled && halaman !== null) {
                tombol.addEventListener('click', () => {
                    pagination.halaman_sekarang = halaman;
                    terapkanFilterDanPaginasi();
                });
            }

            wadah.appendChild(tombol);
        }

        buatTombol('Prev', halamanAktif - 1, false, halamanAktif <= 1);

        let mulai = Math.max(
            1,
            halamanAktif - Math.floor(batas / 2)
        );

        let akhir = Math.min(
            totalHalaman,
            mulai + batas - 1
        );

        if (akhir - mulai + 1 < batas) {
            mulai = Math.max(1, akhir - batas + 1);
        }

        if (mulai > 1) {
            buatTombol('1', 1);

            if (mulai > 2) {
                const titik = document.createElement('span');
                titik.textContent = '...';
                wadah.appendChild(titik);
            }
        }

        for (let halaman = mulai; halaman <= akhir; halaman++) {
            buatTombol(
                String(halaman),
                halaman,
                halaman === halamanAktif
            );
        }

        if (akhir < totalHalaman) {
            if (akhir < totalHalaman - 1) {
                const titik = document.createElement('span');
                titik.textContent = '...';
                wadah.appendChild(titik);
            }

            buatTombol(
                String(totalHalaman),
                totalHalaman
            );
        }

        buatTombol(
            'Next',
            halamanAktif + 1,
            false,
            halamanAktif >= totalHalaman
        );
    }


    /* =====================================================
       INITIALIZE PAGE EVENTS
    ===================================================== */

    function initAbsensiHarian() {
        const root = document.querySelector('.attendance-workspace');

        if (!root) return;

        // Halaman yang sama sudah aktif: jangan pasang event lagi.
        if (runtime.root === root) return;

        // Bersihkan resource halaman sebelumnya.
        cleanupAbsensiHarian();

        runtime.root = root;

        // Tampilkan jam sementara, lalu sinkronkan dengan server.
        updateClock();

        sinkronkanWaktuServer();

        runtime.intervalJam = window.setInterval(
            updateClock,
            1000
        );

        // Sinkronisasi ulang setiap 60 detik.
        runtime.intervalSinkronisasi = window.setInterval(
            sinkronkanWaktuServer,
            60000
        );


        /* ---------------------------------------------
           MODAL IZIN
        --------------------------------------------- */

        const overlayIzin = document.getElementById('modal-overlay');
        const modalIzin = document.getElementById('modal-form');

        const tombolIzin = root.querySelectorAll('.btn-aksi-izin');
        const tombolBatalIzin = document.getElementById('modal-cancel');
        const tombolKirimIzin = document.getElementById('modal-submit');

        function bukaModalIzin() {
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }

            const textarea = document.getElementById('modal-reason');

            if (textarea) textarea.value = '';

            bukaModal(overlayIzin, modalIzin);

            window.setTimeout(() => textarea?.focus(), 300);
        }

        function tutupModalIzin() {
            tutupModal(overlayIzin, modalIzin);
        }

        tombolIzin.forEach(tombol => {
            tombol.addEventListener('click', bukaModalIzin);
        });

        tombolBatalIzin?.addEventListener('click', tutupModalIzin);

        overlayIzin?.addEventListener('click', tutupModalIzin);

        tombolKirimIzin?.addEventListener('click', () => {
            const textarea = document.getElementById('modal-reason');
            const alasan = textarea?.value.trim() || '';

            if (!alasan) {
                notifPeringatan('Alasan izin atau sakit wajib diisi.');
                textarea?.focus();
                return;
            }

            kirimFormPost(
                getConfig().URL_AJUKAN_IZIN,
                { alasan_izin: alasan }
            );
        });


        /* ---------------------------------------------
           MODAL QR
        --------------------------------------------- */

        const overlayQR = document.getElementById('modal-qr-overlay');
        const modalQR = document.getElementById('modal-qr');

        root.querySelectorAll('.btn-aksi-qr').forEach(tombol => {
            tombol.addEventListener('click', bukaModalQR);
        });

        document.getElementById('modal-qr-tutup')
            ?.addEventListener('click', () => {
                tutupModal(overlayQR, modalQR);
            });

        overlayQR?.addEventListener('click', () => {
            tutupModal(overlayQR, modalQR);
        });


        /* ---------------------------------------------
           ABSEN MASUK
        --------------------------------------------- */

        root.querySelectorAll('.btn-aksi-masuk').forEach(tombol => {
            tombol.addEventListener('click', () => {
                if (sudahLewatBatasWaktu()) {
                    tampilkanPeringatanAlfa();
                    return;
                }

                const sekarang = jamKeMenit(ambilJamSaatIni());
                const batas = jamKeMenit(
                    getConfig().BATAS_TERLAMBAT
                );

                if (sekarang > batas) {
                    runtime.dataQRTerlambat = null;
                    bukaModalAlasanTelat(ambilJamSaatIni());
                } else {
                    kirimAbsenMasuk();
                }
            });
        });


        /* ---------------------------------------------
           MODAL TERLAMBAT
        --------------------------------------------- */

        const overlayTelat = document.getElementById('modal-telat-overlay');
        const modalTelat = document.getElementById('modal-telat');

        document.getElementById('modal-telat-batal')
            ?.addEventListener('click', () => {
                runtime.dataQRTerlambat = null;
                tutupModalTelat();
            });

        overlayTelat?.addEventListener('click', () => {
            runtime.dataQRTerlambat = null;
            tutupModalTelat();
        });

        // Hanya satu listener untuk tombol simpan.
        document.getElementById('modal-telat-simpan')
            ?.addEventListener('click', simpanAlasanTerlambat);


        /* ---------------------------------------------
           ABSEN PULANG
        --------------------------------------------- */

        root.querySelectorAll('.btn-aksi-pulang').forEach(tombol => {
            tombol.addEventListener('click', kirimAbsenPulang);
        });


        /* ---------------------------------------------
           SCAN QR
        --------------------------------------------- */

        root.querySelectorAll('.btn-aksi-scan').forEach(tombol => {
            tombol.addEventListener('click', bukaKamera);
        });

        document.getElementById('btn-tutup-kamera')
            ?.addEventListener('click', tutupModalKamera);

        document.getElementById('modal-kamera-overlay')
            ?.addEventListener('click', tutupModalKamera);


        /* ---------------------------------------------
           PAGINATION
        --------------------------------------------- */

        const inputPerHalaman =
            document.getElementById('jumlah-per-halaman');

        inputPerHalaman?.addEventListener('change', function () {
            const pagination = getPagination();

            const nilai = parseInt(this.value, 10) || 10;

            pagination.per_halaman = Math.max(
                1,
                Math.min(100, nilai)
            );

            pagination.halaman_sekarang = 1;

            terapkanFilterDanPaginasi();
        });

        perbaruiTeksPaginasi();
        renderTombolPaginasi();
    }


    /* =====================================================
       CLEANUP — SPA NAVIGATION
    ===================================================== */

    function cleanupAbsensiHarian() {

        // Hentikan interval jam digital
        if (runtime.intervalJam) {
            clearInterval(runtime.intervalJam);
            runtime.intervalJam = null;
        }

        // Hentikan interval sinkronisasi waktu server
        if (runtime.intervalSinkronisasi) {
            clearInterval(runtime.intervalSinkronisasi);
            runtime.intervalSinkronisasi = null;
        }

        // Hentikan kamera jika masih aktif
        hentikanKamera();

        // Bersihkan referensi halaman
        runtime.root = null;
        runtime.dataQRTerlambat = null;
        runtime.serverTimeAnchor = null;
    }


    /* =====================================================
       GLOBAL LIFECYCLE BINDING
       Bind sekali, tetap bekerja saat script dieksekusi ulang.
    ===================================================== */

    window.initAbsensiHarian = initAbsensiHarian;
    window.cleanupAbsensiHarian = cleanupAbsensiHarian;

    if (!window.__absensiHarianLifecycleBound) {
        window.__absensiHarianLifecycleBound = true;

        document.addEventListener(
            'DOMContentLoaded',
            () => window.initAbsensiHarian?.()
        );

        document.addEventListener(
            'spa:page-loaded',
            () => window.initAbsensiHarian?.()
        );

        document.addEventListener(
            'spa:before-page-unload',
            () => window.cleanupAbsensiHarian?.()
        );
    }

    // Script bisa dieksekusi setelah DOMContentLoaded oleh SPA.
    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            initAbsensiHarian,
            { once: true }
        );
    } else {
        initAbsensiHarian();
    }

})();
