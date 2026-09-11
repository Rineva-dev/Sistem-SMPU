// ==========================================
// FUNGSI MODAL NOTIFIKASI GLOBAL
// Pengganti fungsi alert() bawaan browser
// Bisa dipakai DI SEMUA HALAMAN secara langsung!
// ==========================================

// === BUAT ELEMEN MODAL OTOMATIS ===
// Karena sudah global, elemen dibuat lewat JS saja
function siapkanElemenModalNotif() {
    if (document.getElementById('modal-notif-global')) return;

    const html = `
    <div id="modal-notif-global" class="modal-notif-overlay">
        <div class="modal-notif-kotak">
            <div class="modal-notif-isi">
                <span id="modal-notif-ikon-teks" class="modal-notif-ikon"></span>
                <div id="modal-notif-teks-pesan" class="modal-notif-teks"></div>
            </div>
            <button id="modal-notif-btn-ok" class="modal-notif-tombol">OK</button>
        </div>
    </div>`;

    const temp = document.createElement('div');
    temp.innerHTML = html.trim();
    document.body.appendChild(temp.firstChild);

    // Pasang event tutup
    document.getElementById('modal-notif-btn-ok').addEventListener('click', tutupNotif);
}

// === TUTUP NOTIFIKASI ===
function tutupNotif() {
    document.getElementById('modal-notif-global').classList.remove('aktif');
}

// === FUNGSI UTAMA: TAMPILKAN NOTIFIKASI ===
// Cara pakai: tampilkanNotif('peringatan', '<i class="fas fa-clock"></i>', 'Pesan di sini')
function tampilkanNotif(jenis, ikonHtml, pesanHtml) {
    // Pastikan elemen sudah ada
    siapkanElemenModalNotif();

    const overlay = document.getElementById('modal-notif-global');
    const kotakIkon = document.getElementById('modal-notif-ikon-teks');
    const kotakPesan = document.getElementById('modal-notif-teks-pesan');

    // Isi konten
    kotakIkon.className = `modal-notif-ikon ${jenis}`;
    kotakIkon.innerHTML = ikonHtml;
    kotakPesan.innerHTML = pesanHtml;

    // Tampilkan modal
    overlay.classList.add('aktif');
}

// === ALIAS SINGKAT untuk lebih mudah dipakai ===
window.notifSukses = function(pesan) {
    tampilkanNotif('sukses', '<i class="fas fa-check-circle"></i>', pesan);
};
window.notifPeringatan = function(pesan) {
    tampilkanNotif('peringatan', '<i class="fas fa-exclamation-triangle"></i>', pesan);
};
window.notifError = function(pesan) {
    tampilkanNotif('error', '<i class="fas fa-times-circle"></i>', pesan);
};
window.notifInfo = function(pesan) {
    tampilkanNotif('info', '<i class="fas fa-info-circle"></i>', pesan);
};