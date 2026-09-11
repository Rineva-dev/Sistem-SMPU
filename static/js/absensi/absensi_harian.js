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
    alert(`[fas fa-exclamation-triangle] PERINGATAN: Sudah lewat jam ${BATAS_ABSENSI}\n\nAbsensi DITUTUP. Kehadiran Anda terhitung ALFA.`);
}
// ✅ === BARU: CEK BELUM JAM PULANG ===
const BATAS_PULANG = ABSENSI.BATAS_PULANG;
function belumJamPulang() {
    const jamSaatIni = ambilJamSaatIni();
    return jamKeMenit(jamSaatIni) < jamKeMenit(BATAS_PULANG);
}
function tampilkanPeringatanBelumJamPulang() {
    alert(`[fas fa-clock] BELUM JAM ${BATAS_PULANG}\n\nAbsen pulang baru diperbolehkan mulai jam ${BATAS_PULANG}.`);
}
// ✅ === SELESAI PENAMBAHAN ===
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
// ✅ === BARU: KIRIM ABSEN PULANG ===
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
// ✅ === SELESAI PENAMBAHAN ===
async function prosesHasilScan(dataQR) {
    // ✅ TUTUP KAMERA & MODAL DULU
    if (window._pemindaianAktifRef) window._pemindaianAktifRef.value = false;
    if (window._aliranKamera) {
        window._aliranKamera.getTracks().forEach(track => track.stop());
        window._aliranKamera = null;
    }
    const modalKameraOverlay = document.getElementById('modal-kamera-overlay');
    const modalKamera = document.getElementById('modal-kamera');
    if (modalKameraOverlay) modalKameraOverlay.style.display = 'none';
    if (modalKamera) modalKamera.style.display = 'none';
    // ... sisa kode (cek jam masuk/pulang) ...
    try {
        const res = await fetch(ABSENSI.URL_SCAN_QR_PROSES, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_qr: dataQR })
        });
        const hasil = await res.json();
        if (hasil.status === 'sukses' || hasil.status === 'info') {
            // ✅ TAMPILKAN NAMA & STATUS
            alert(`[fas fa-check-circle] ${hasil.pesan || 'Absensi berhasil tercatat!'}`);
            setTimeout(() => location.reload(), 1000);
        } else {
            // ❌ TAMPILKAN ALASAN GAGAL
            alert(`[fas fa-times-circle] ${hasil.pesan || 'Gagal memproses QR'}`);
        }
    } catch (err) {
        alert(`[fas fa-exclamation-circle] Kesalahan: ${err.message}`);
    }
}
// --- BACA QR DARI KAMERA ---
function bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef) {
    if (!pemindaianAktifRef.value) return;
    // ⛔ TUNGGU VIDEO SIAP
    if (!videoKamera || videoKamera.readyState < 2 ||
        videoKamera.videoWidth === 0 || videoKamera.videoHeight === 0) {
        requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
        return;
    }
    // ✅ SET UKURAN CANVAS SESUAI VIDEO
    kanvasPemindai.width = videoKamera.videoWidth;
    kanvasPemindai.height = videoKamera.videoHeight;
    // ✅ TAMBAH willReadFrequently: true ← HILANGKAN PERINGATAN CONSOLE
    const konteks = kanvasPemindai.getContext('2d', { willReadFrequently: true });
    
    konteks.drawImage(videoKamera, 0, 0, kanvasPemindai.width, kanvasPemindai.height);
    // Indikasi status
    const kameraStatus = document.getElementById('kamera-status');
    if (kameraStatus) {
        kameraStatus.innerHTML = '<i class="fas fa-search"></i> Sedang memindai... arahkan kode QR ke bingkai';
        kameraStatus.style.color = '#2563eb';
    }
    try {
        // ✅ Pastikan jsQR sudah dimuat
        if (!window.jsQR) {
            if (kameraStatus) {
                kameraStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menunggu pustaka pemindai...';
                kameraStatus.style.color = '#f59e0b';
            }
            requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
            return;
        }
        // ✅ Baca area TENGAH saja agar lebih cepat & akurat
        const lebar = kanvasPemindai.width;
        const tinggi = kanvasPemindai.height;
        const skala = 0.6; // baca 60% area tengah
        const potongX = lebar * (1 - skala) / 2;
        const potongY = tinggi * (1 - skala) / 2;
        const potongLebar = lebar * skala;
        const potongTinggi = tinggi * skala;
        const gambarData = konteks.getImageData(
            Math.floor(potongX), Math.floor(potongY),
            Math.floor(potongLebar), Math.floor(potongTinggi)
        );
        // Validasi ukuran data
        if (gambarData.data.length < 100 || gambarData.width < 50 || gambarData.height < 50) {
            requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
            return;
        }
        // ✅ Scan QR
        const kodeQR = window.jsQR(gambarData.data, gambarData.width, gambarData.height, {
            inversionAttempts: 'dontInvert' // opsi tambahan: 'attemptBoth' jika perlu
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
        // Diam saja, jangan spam console
    }
    // Lanjut frame berikutnya
    requestAnimationFrame(() => bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef));
}
// ==========================================
// INISIALISASI SEMUA EVENT SETELAH HALAMAN SIAP
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
    // Mulai jam
    updateClock();
    setInterval(updateClock, 1000);
    // ==========================================
    // MODAL 1: IZIN / SAKIT
    // ==========================================
    const btnExcuse = document.getElementById('btn-excuse');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalForm = document.getElementById('modal-form');
    const modalCancel = document.getElementById('modal-cancel');
    const modalSubmit = document.getElementById('modal-submit');
    if (btnExcuse && modalOverlay && modalForm) {
        btnExcuse.addEventListener('click', () => {
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
        });
    }
    function tutupModalIzin() {
        modalOverlay.classList.remove('active');
        modalForm.classList.remove('active');
        setTimeout(() => {
            modalOverlay.style.display = 'none';
            modalForm.style.display = 'none';
        }, 350);
    }
    if (modalCancel) modalCancel.addEventListener('click', tutupModalIzin);
    if (modalSubmit) {
        modalSubmit.addEventListener('click', () => {
            const alasan = document.getElementById('modal-reason').value.trim();
            kirimAbsenMasuk(alasan);
        });
    }
    // ==========================================
    // MODAL 2: QR ABSENSI
    // ==========================================
    const btnTampilkanQR = document.getElementById('btn-tampilkan-qr');
    const modalQrOverlay = document.getElementById('modal-qr-overlay');
    const modalQr = document.getElementById('modal-qr');
    const modalQrTutup = document.getElementById('modal-qr-tutup');
    function bukaModalQR() {
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
    if (btnTampilkanQR && modalQrOverlay && modalQr) {
        btnTampilkanQR.addEventListener('click', async () => {
            // === CEK JAM MASUK vs JAM PULANG ===
            const sudahMasuk = !!ABSENSI.SUDAH_ABSEN_MASUK;
            if (!sudahMasuk) {
            // BELUM ABSEN MASUK → cek batas jam
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }
            } else {
            // SUDAH MASUK → ini QR untuk PULANG, cek jam
            if (belumJamPulang()) {
                tampilkanPeringatanBelumJamPulang();
                return;
            }
            }
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
                `<em style="color:red;"><i class="fas fa-exclamation-circle"></i> ${data.pesan || 'Gambar QR gagal dimuat'}</em>`;
            }
            } catch (err) {
            document.getElementById('qr-tempat-tampil').innerHTML =
                `<em style="color:red;"><i class="fas fa-exclamation-circle"></i> Gagal memuat QR</em>`;
            }
        });
    }
    if (modalQrTutup) modalQrTutup.addEventListener('click', tutupModalQR);
    // ==========================================
    // MODAL 3: ALASAN TERLAMBAT
    // ==========================================
    const btnCheckIn = document.getElementById('btn-checkin');
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
    if (btnCheckIn) {
        btnCheckIn.addEventListener('click', () => {
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
        });
    }
    if (modalTelatBatal) modalTelatBatal.addEventListener('click', tutupModalTelat);
    if (modalTelatSimpan) {
        modalTelatSimpan.addEventListener('click', () => {
            const alasan = document.getElementById('alasan-keterlambatan').value.trim();
            kirimAbsenMasuk(alasan);
        });
    }
    // ✅ === BARU: TOMBOL ABSEN PULANG ===
    const btnCheckOut = document.getElementById('btn-checkout');
    if (btnCheckOut) {
        btnCheckOut.addEventListener('click', () => {
            if (belumJamPulang()) {
                tampilkanPeringatanBelumJamPulang();
                return;
            }
            kirimAbsenPulang();
        });
    }
    // ✅ === SELESAI PENAMBAHAN ===
    // ==========================================
    // MODAL 4: KAMERA SCAN QR
    // ==========================================
    const btnBukaKameraEl = document.getElementById('btn-buka-kamera');
    const btnTutupKameraEl = document.getElementById('btn-tutup-kamera');
    const modalKameraOverlay = document.getElementById('modal-kamera-overlay');
    const modalKamera = document.getElementById('modal-kamera');
    async function bukaKamera() {
        // Cek sesuai tipe
        const tipe = ABSENSI.SUDAH_ABSEN_MASUK ? "pulang" : "masuk";
        if (tipe === "pulang") {
            if (belumJamPulang()) {
                tampilkanPeringatanBelumJamPulang();
                return;
            }
        } else {
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }
        }
        let aliranKamera = null;
        let pemindaianAktifRef = { value: false };
        try {
            const cekIzin = await navigator.permissions.query({ name: 'camera' });
            if (cekIzin.state === 'denied') {
                alert('[fas fa-exclamation-triangle] Izin kamera DIBLOKIR.\n\nKlik ikon gembok <i class="fas fa-lock"></i> di bilah alamat → Pengaturan Situs → Ubah Kamera jadi Izinkan');
                return;
            }
            aliranKamera = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } 
            });
            const videoKamera = document.getElementById('video-kamera');
            videoKamera.srcObject = aliranKamera;
            const kameraStatus = document.getElementById('kamera-status');
            kameraStatus.innerHTML = tipe === "pulang"
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
            let pesan = '[fas fa-exclamation-circle] Tidak bisa membuka kamera.\n\n';
            if (err.name === 'NotAllowedError') {
                pesan += '→ <i class="fas fa-ban"></i> Akses kamera DITOLAK/BLOKIR.\n→ Klik ikon gembok <i class="fas fa-lock"></i> di alamat → Izinkan Kamera';
            } else if (err.name === 'NotFoundError') {
                pesan += '→ <i class="fas fa-video-slash"></i> Kamera tidak ditemukan di perangkat.';
            } else if (err.name === 'NotReadableError') {
                pesan += '→ <i class="fas fa-video"></i> Kamera sedang dipakai aplikasi lain.';
            } else {
                pesan += `→ <i class="fas fa-code"></i> Error: ${err.message}`;
            }
            alert(pesan);
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
    if (btnBukaKameraEl) btnBukaKameraEl.addEventListener('click', bukaKamera);
    if (btnTutupKameraEl) btnTutupKameraEl.addEventListener('click', tutupKamera);
});