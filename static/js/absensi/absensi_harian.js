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
// --- CEK: SUDAH LEWAT JAM 11? ---
const BATAS_ABSENSI = '11:00';
function sudahLewatBatasWaktu() {
    const jamSaatIni = ambilJamSaatIni();
    return jamKeMenit(jamSaatIni) >= jamKeMenit(BATAS_ABSENSI);
}
function tampilkanPeringatanAlfa() {
    alert(`⚠️ PERINGATAN: Sudah lewat jam ${BATAS_ABSENSI}\n\nAbsensi DITUTUP. Kehadiran Anda terhitung ALFA.`);
}

// ✅ === BARU: CEK BELUM JAM 15:00 (TIDAK BOLEH PULANG) ===
const BATAS_PULANG = '15:00';
function belumJamPulang() {
    const jamSaatIni = ambilJamSaatIni();
    return jamKeMenit(jamSaatIni) < jamKeMenit(BATAS_PULANG);
}
function tampilkanPeringatanBelumJamPulang() {
    alert(`⚠️ BELUM JAM ${BATAS_PULANG}\n\nAbsen pulang baru diperbolehkan mulai jam ${BATAS_PULANG}.`);
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

// --- PROSES HASIL SCAN QR ---
async function prosesHasilScan(dataQR) {
    // Parse tipe dari QR
    let tipe = "masuk";
    if (dataQR.startsWith("guru:")) {
        const bagian = dataQR.split(":");
        if (bagian.length >= 6) tipe = bagian[5];
    }

    // ✅ CEK KHUSUS ABSEN PULANG
    if (tipe === "pulang") {
        if (belumJamPulang()) {
            tampilkanPeringatanBelumJamPulang();
            return;
        }
    } else {
        // CEK KHUSUS ABSEN MASUK
        if (sudahLewatBatasWaktu()) {
            tampilkanPeringatanAlfa();
            return;
        }
    }

    try {
        const res = await fetch(ABSENSI.URL_SCAN_QR_PROSES, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_qr: dataQR })
        });
        const hasil = await res.json();
        if (hasil.status === 'sukses' || hasil.status === 'info') {
            alert(hasil.pesan || 'Berhasil!');
            setTimeout(() => location.reload(), 800);
        } else {
            alert(hasil.pesan || 'Gagal memproses');
        }
    } catch (err) {
        alert('Gagal menghubungi server');
    }
}

// --- BACA QR DARI KAMERA (DENGAN INDIKASI VISUAL) ---
function bacaDariKanvas(kanvasPemindai, videoKamera, pemindaianAktifRef) {
    if (!pemindaianAktifRef.value) return;
    const konteks = kanvasPemindai.getContext('2d');
    kanvasPemindai.width = videoKamera.videoWidth;
    kanvasPemindai.height = videoKamera.videoHeight;
    konteks.drawImage(videoKamera, 0, 0);

    // === TAMBAHAN: INDIKASI SEDANG MEMINDAI ===
    const kameraStatus = document.getElementById('kamera-status');
    if (kameraStatus) {
        kameraStatus.textContent = '🔍 Sedang memindai... arahkan kode QR ke bingkai';
        kameraStatus.style.color = '#2563eb';
    }
    // =========================================

    try {
        const gambarData = konteks.getImageData(0, 0, kanvasPemindai.width, kanvasPemindai.height);
        const kodeQR = window.jsQR ? window.jsQR(gambarData) : null;

        if (kodeQR && kodeQR.data) {
            // === QR TERDETEKSI: UBAH INDIKASI DULU ===
            pemindaianAktifRef.value = false;
            if (kameraStatus) {
                kameraStatus.textContent = '✅ QR Terdeteksi! Memproses...';
                kameraStatus.style.color = '#16a34a';
            }
            // =======================================
            prosesHasilScan(kodeQR.data);
        }
    } catch (e) {
        console.error('Kesalahan baca kanvas:', e);
    }
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
            // BELUM ABSEN MASUK → cek batas jam 11:00
            if (sudahLewatBatasWaktu()) {
                tampilkanPeringatanAlfa();
                return;
            }
            } else {
            // SUDAH MASUK → ini QR untuk PULANG, cek jam 15:00
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
                `<em style="color:red;">${data.pesan || 'Gambar QR gagal dimuat'}</em>`;
            }
            } catch (err) {
            document.getElementById('qr-tempat-tampil').innerHTML =
                `<em style="color:red;">Gagal memuat QR</em>`;
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
                alert('❌ Izin kamera DIBLOKIR.\n\nKlik ikon gembok 🔒 di bilah alamat → Pengaturan Situs → Ubah Kamera jadi Izinkan');
                return;
            }
            aliranKamera = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } 
            });
            const videoKamera = document.getElementById('video-kamera');
            videoKamera.srcObject = aliranKamera;
            const kameraStatus = document.getElementById('kamera-status');
            kameraStatus.textContent = tipe === "pulang"
                ? 'Scan QR untuk Absen Pulang'
                : 'Scan QR untuk Absen Masuk';
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
            let pesan = '❌ Tidak bisa membuka kamera.\n\n';
            if (err.name === 'NotAllowedError') {
                pesan += '→ Akses kamera DITOLAK/BLOKIR.\n→ Klik ikon gembok 🔒 di alamat → Izinkan Kamera';
            } else if (err.name === 'NotFoundError') {
                pesan += '→ Kamera tidak ditemukan di perangkat.';
            } else if (err.name === 'NotReadableError') {
                pesan += '→ Kamera sedang dipakai aplikasi lain.';
            } else {
                pesan += '→ Error: ' + err.message;
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