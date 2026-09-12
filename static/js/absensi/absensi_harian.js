// ==========================================
// ABSENSI HARIAN — SCRIPT LENGKAP & BENAR
// ==========================================

// --- JAM DIGITAL ---
function updateClock() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const wita = new Date(utc + (8 * 3600000));
    const h = String(wita.getHours()).padStart(2, '0');
    const m = String(wita.getMinutes()).padStart(2, '0');
    const s = String(wita.getSeconds()).padStart(2, '0');
    document.getElementById('jam-digital').textContent = `${h}.${m}.${s}`;
}

// --- FUNGSI NOTIFIKASI (jika belum ada di layout) ---
function notifSukses(pesan) { alert('✅ SUKSES: ' + pesan); }
function notifError(pesan) { alert('❌ GAGAL: ' + pesan); }
function notifInfo(pesan) { alert('ℹ️ INFO: ' + pesan); }
function notifPeringatan(pesan) { alert('⚠️ PERINGATAN: ' + pesan); }

// --- FILTER BULAN & TAHUN ---
function terapkanFilter() {
    const bulan = document.getElementById('filter-bulan').value;
    const tahun = document.getElementById('filter-tahun').value;
    let url = ABSENSI.URL_ABSENSI_HARIAN;
    const params = new URLSearchParams();
    if (bulan) params.append('bulan', bulan);
    if (tahun) params.append('tahun', tahun);
    if (params.toString()) url += '?' + params.toString();
    window.location.href = url;
}

// --- UBAH JAM KE MENIT ---
function jamKeMenit(jamStr) {
    const [j, m] = jamStr.split(':').map(Number);
    return j * 60 + m;
}

// --- AMBIL JAM SAAT INI (WITA) ---
function ambilJamSaatIni() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const wita = new Date(utc + (8 * 3600000));
    const h = String(wita.getHours()).padStart(2, '0');
    const m = String(wita.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
}

// --- CEK: SUDAH LEWAT BATAS WAKTU? ---
const BATAS_ABSENSI = ABSENSI.BATAS_TUTUP_ABSENSI;
function sudahLewatBatasWaktu() {
    const jamSaatIni = ambilJamSaatIni();
    return jamKeMenit(jamSaatIni) >= jamKeMenit(BATAS_ABSENSI);
}
function tampilkanPeringatanAlfa() {
    notifPeringatan(`Sudah lewat jam ${BATAS_ABSENSI}\n\nAbsensi DITUTUP.`);
}

// --- CEK: BELUM JAM PULANG? ---
const BATAS_PULANG = ABSENSI.BATAS_PULANG;
function belumJamPulang() {
    const jamSaatIni = ambilJamSaatIni();
    return jamKeMenit(jamSaatIni) < jamKeMenit(BATAS_PULANG);
}
function tampilkanPeringatanBelumJamPulang() {
    notifInfo(`BELUM JAM ${BATAS_PULANG}\n\nAbsen pulang baru bisa mulai jam ${BATAS_PULANG}.`);
}

// --- KIRIM ABSEN MASUK ---
function kirimAbsenMasuk(alasan = '') {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = ABSENSI.URL_ABSEN_MASUK;
    if (alasan) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'alasan_keterlambatan';
        input.value = alasan;
        form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
}

// --- KIRIM ABSEN PULANG ---
function kirimAbsenPulang() {
    if (belumJamPulang()) {
        tampilkanPeringatanBelumJamPulang();
        return;
    }
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = ABSENSI.URL_ABSEN_PULANG;
    document.body.appendChild(form);
    form.submit();
}

// --- PROSES HASIL SCAN QR ---
async function prosesHasilScan(dataQR) {
    // Tutup kamera & modal dulu
    if (window._pemindaianAktifRef) window._pemindaianAktifRef.value = false;
    if (window._aliranKamera) {
        window._aliranKamera.getTracks().forEach(track => track.stop());
        window._aliranKamera = null;
    }
    const modalKameraOverlay = document.getElementById('modal-kamera-overlay');
    const modalKamera = document.getElementById('modal-kamera');
    if (modalKameraOverlay) modalKameraOverlay.style.display = 'none';
    if (modalKamera) modalKamera.style.display = 'none';

    try {
        const res = await fetch(ABSENSI.URL_SCAN_QR_PROSES, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_qr: dataQR })
        });
        const hasil = await res.json();
        if (hasil.status === 'sukses' || hasil.status === 'info') {
            notifSukses(hasil.pesan || 'Absensi berhasil tercatat!');
            setTimeout(() => location.reload(), 1000);
        } else {
            notifError(hasil.pesan || 'Gagal memproses QR.');
        }
    } catch (err) {
        notifError(`Kesalahan: ${err.message}`);
    }
}

// --- BACA QR DARI KAMERA ---
function bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef) {
    if (!pemindaianAktifRef.value) return;
    if (!videoKamera || videoKamera.readyState < 2 ||
        videoKamera.videoWidth === 0 || videoKamera.videoHeight === 0) {
        requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
        return;
    }
    kanvasPemindai.width = videoKamera.videoWidth;
    kanvasPemindai.height = videoKamera.videoHeight;
    const konteks = kanvasPemindai.getContext('2d', { willReadFrequently: true });
    konteks.drawImage(videoKamera, 0, 0, kanvasPemindai.width, kanvasPemindai.height);

    const kameraStatus = document.getElementById('kamera-status');
    if (kameraStatus) {
        kameraStatus.innerHTML = '<i class="fas fa-search"></i> Sedang memindai... arahkan QR ke bingkai';
        kameraStatus.style.color = '#2563eb';
    }

    try {
        if (!window.jsQR) {
            if (kameraStatus) {
                kameraStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menunggu pustaka...';
                kameraStatus.style.color = '#f59e0b';
            }
            requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
            return;
        }
        const lebar = kanvasPemindai.width;
        const tinggi = kanvasPemindai.height;
        const skala = 0.6;
        const potongX = lebar * (1 - skala) / 2;
        const potongY = tinggi * (1 - skala) / 2;
        const potongLebar = lebar * skala;
        const potongTinggi = tinggi * skala;
        const gambarData = konteks.getImageData(
            Math.floor(potongX), Math.floor(potongY),
            Math.floor(potongLebar), Math.floor(potongTinggi)
        );
        if (gambarData.data.length < 100 || gambarData.width < 50 || gambarData.height < 50) {
            requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
            return;
        }
        const kodeQR = window.jsQR(gambarData.data, gambarData.width, gambarData.height, {
            inversionAttempts: 'dontInvert'
        });
        if (kodeQR && kodeQR.data) {
            pemindaianAktifRef.value = false;
            if (kameraStatus) {
                kameraStatus.innerHTML = '<i class="fas fa-check-circle"></i> QR Terdeteksi! Memproses...';
                kameraStatus.style.color = '#16a34a';
            }
            prosesHasilScan(kodeQR.data);
            return;
        }
    } catch (e) {
        // Diam saja
    }
    requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
}

// ==========================================
// INISIALISASI SETELAH HALAMAN SIAP
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
    updateClock();
    setInterval(updateClock, 1000);

    // ==========================================
    // MODAL IZIN / SAKIT
    // ==========================================
    const semuaBtnIzin = document.querySelectorAll('.btn-aksi-izin');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalForm = document.getElementById('modal-form');
    const modalCancel = document.getElementById('modal-cancel');
    const modalSubmit = document.getElementById('modal-submit');

    function bukaModalIzin() {
        if (sudahLewatBatasWaktu()) {
            tampilkanPeringatanAlfa();
            return;
        }
        modalOverlay.style.display = 'block';
        modalForm.style.display = 'block';
        setTimeout(() => {
            modalOverlay.classList.add('active');
            modalForm.classList.add('active');
        }, 10);
    }
    function tutupModalIzin() {
        modalOverlay.classList.remove('active');
        modalForm.classList.remove('active');
        setTimeout(() => {
            modalOverlay.style.display = 'none';
            modalForm.style.display = 'none';
        }, 350);
    }
    semuaBtnIzin.forEach(btn => btn.addEventListener('click', bukaModalIzin));
    if (modalCancel) modalCancel.addEventListener('click', tutupModalIzin);
    if (modalSubmit) {
        modalSubmit.addEventListener('click', () => {
            const alasan = document.getElementById('modal-reason').value.trim();
            kirimAbsenMasuk(alasan);
        });
    }

    // ==========================================
    // MODAL TAMPILKAN QR
    // ==========================================
    const semuaBtnQR = document.querySelectorAll('.btn-aksi-qr');
    const modalQrOverlay = document.getElementById('modal-qr-overlay');
    const modalQr = document.getElementById('modal-qr');
    const modalQrTutup = document.getElementById('modal-qr-tutup');

    function bukaModalQR() {
        const sudahMasuk = !!ABSENSI.SUDAH_ABSEN_MASUK;
        if (!sudahMasuk) {
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }
        } else {
            if (belumJamPulang()) {
                tampilkanPeringatanBelumJamPulang();
                return;
            }
        }
        modalQrOverlay.style.display = 'block';
        modalQr.style.display = 'block';
        setTimeout(() => {
            modalQrOverlay.classList.add('active');
            modalQr.classList.add('active');
        }, 10);
    }
    function tutupModalQR() {
        modalQrOverlay.classList.remove('active');
        modalQr.classList.remove('active');
        setTimeout(() => {
            modalQrOverlay.style.display = 'none';
            modalQr.style.display = 'none';
        }, 350);
    }
    semuaBtnQR.forEach(btn => btn.addEventListener('click', async () => {
        bukaModalQR();
        try {
            const res = await fetch(ABSENSI.URL_QR_DATA);
            const data = await res.json();
            if (data.status === 'sukses') {
                document.getElementById('qr-tempat-tampil').innerHTML =
                    `<img src="data:image/png;base64,${data.qr_code}" alt="QR Absensi">`;
                document.getElementById('qr-nama-guru').textContent = data.nama;
                document.getElementById('qr-nip-guru').textContent = data.nip || '-';
                document.getElementById('qr-tanggal-hariini').textContent = data.hari_ini;
            } else {
                document.getElementById('qr-tempat-tampil').innerHTML =
                    `<em style="color:red;"><i class="fas fa-exclamation-circle"></i> ${data.pesan || 'QR gagal dimuat'}</em>`;
            }
        } catch (err) {
            document.getElementById('qr-tempat-tampil').innerHTML =
                `<em style="color:red;"><i class="fas fa-exclamation-circle"></i> Gagal memuat QR</em>`;
        }
    }));
    if (modalQrTutup) modalQrTutup.addEventListener('click', tutupModalQR);

    // ==========================================
    // MODAL ALASAN TERLAMBAT — ABSEN MASUK
    // ==========================================
    const semuaBtnMasuk = document.querySelectorAll('.btn-aksi-masuk');
    const modalTelatOverlay = document.getElementById('modal-telat-overlay');
    const modalTelat = document.getElementById('modal-telat');
    const modalTelatBatal = document.getElementById('modal-telat-batal');
    const modalTelatSimpan = document.getElementById('modal-telat-simpan');

    function bukaModalAlasanTelat(jamSaatIni) {
        document.getElementById('jam-saat-ini').textContent = jamSaatIni;
        document.getElementById('alasan-keterlambatan').value = '';
        modalTelatOverlay.style.display = 'block';
        modalTelat.style.display = 'block';
        setTimeout(() => {
            modalTelatOverlay.classList.add('active');
            modalTelat.classList.add('active');
        }, 10);
    }
    function tutupModalTelat() {
        modalTelatOverlay.classList.remove('active');
        modalTelat.classList.remove('active');
        setTimeout(() => {
            modalTelatOverlay.style.display = 'none';
            modalTelat.style.display = 'none';
        }, 350);
    }
    semuaBtnMasuk.forEach(btn => btn.addEventListener('click', () => {
        if (sudahLewatBatasWaktu()) {
            tampilkanPeringatanAlfa();
            return;
        }
        const jamSaatIni = ambilJamSaatIni();
        const batasMenit = jamKeMenit(ABSENSI.BATAS_TEPAT_WAKTU);
        const saatIniMenit = jamKeMenit(jamSaatIni);
        if (saatIniMenit > batasMenit) {
            bukaModalAlasanTelat(jamSaatIni);
        } else {
            kirimAbsenMasuk();
        }
    }));
    if (modalTelatBatal) modalTelatBatal.addEventListener('click', tutupModalTelat);
    if (modalTelatSimpan) {
        modalTelatSimpan.addEventListener('click', () => {
            const alasan = document.getElementById('alasan-keterlambatan').value.trim();
            kirimAbsenMasuk(alasan);
        });
    }

    // ==========================================
    // ABSEN PULANG
    // ==========================================
    const semuaBtnPulang = document.querySelectorAll('.btn-aksi-pulang');
    semuaBtnPulang.forEach(btn => btn.addEventListener('click', () => {
        if (belumJamPulang()) {
            tampilkanPeringatanBelumJamPulang();
            return;
        }
        kirimAbsenPulang();
    }));

    // ==========================================
    // MODAL KAMERA SCAN QR
    // ==========================================
    const semuaBtnScan = document.querySelectorAll('.btn-aksi-scan');
    const btnTutupKameraEl = document.getElementById('btn-tutup-kamera');
    const modalKameraOverlay = document.getElementById('modal-kamera-overlay');
    const modalKamera = document.getElementById('modal-kamera');

    async function bukaKamera() {
        const sudahMasuk = !!ABSENSI.SUDAH_ABSEN_MASUK;
        if (!sudahMasuk) {
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }
        } else {
            if (belumJamPulang()) {
                tampilkanPeringatanBelumJamPulang();
                return;
            }
        }
        let aliranKamera = null;
        let pemindaianAktifRef = { value: false };
        try {
            const cekIzin = await navigator.permissions.query({ name: 'camera' });
            if (cekIzin.state === 'denied') {
                notifError('Izin kamera DIBLOKIR.\n\nKlik ikon gembok 🔒 di bilah alamat → Pengaturan Situs → Izinkan Kamera');
                return;
            }
            aliranKamera = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } 
            });
            const videoKamera = document.getElementById('video-kamera');
            videoKamera.srcObject = aliranKamera;
            const kameraStatus = document.getElementById('kamera-status');
            kameraStatus.innerHTML = sudahMasuk
                ? '<i class="fas fa-qrcode"></i> Scan QR untuk Absen Pulang'
                : '<i class="fas fa-qrcode"></i> Scan QR untuk Absen Masuk';
            modalKameraOverlay.style.display = 'block';
            modalKamera.style.display = 'block';
            setTimeout(() => {
                modalKameraOverlay.classList.add('active');
                modalKamera.classList.add('active');
            }, 10);
            pemindaianAktifRef.value = true;
            const kanvasPemindai = document.getElementById('kanvas-pemindai');
            setTimeout(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef), 500);
        } catch (err) {
            let pesan = '⚠️ Tidak bisa membuka kamera.\n\n';
            if (err.name === 'NotAllowedError') {
                pesan += '→ Akses kamera DITOLAK/BLOKIR.\n→ Klik ikon gembok 🔒 di alamat → Izinkan Kamera';
            } else if (err.name === 'NotFoundError') {
                pesan += '→ Kamera tidak ditemukan di perangkat.';
            } else if (err.name === 'NotReadableError') {
                pesan += '→ Kamera sedang dipakai aplikasi lain.';
            } else {
                pesan += `→ Error: ${err.message}`;
            }
            notifError(pesan);
        }
        window._aliranKamera = aliranKamera;
        window._pemindaianAktifRef = pemindaianAktifRef;
    }
    function tutupKamera() {
        if (window._pemindaianAktifRef) window._pemindaianAktifRef.value = false;
        if (window._aliranKamera) {
            window._aliranKamera.getTracks().forEach(track => track.stop());
            window._aliranKamera = null;
        }
        modalKameraOverlay.classList.remove('active');
        modalKamera.classList.remove('active');
        setTimeout(() => {
            modalKameraOverlay.style.display = 'none';
            modalKamera.style.display = 'none';
        }, 350);
    }
    semuaBtnScan.forEach(btn => btn.addEventListener('click', bukaKamera));
    if (btnTutupKameraEl) btnTutupKameraEl.addEventListener('click', tutupKamera);
});