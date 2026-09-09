// ==========================================
// SISTEM NOTIFIKASI GLOBAL
// ==========================================

class Notifikasi {
    constructor() {
        this.waktuTampil = 3500; // 3,5 detik
        this.container = document.querySelector('.notif-container');
        if (!this.container) this.buatContainer();
    }

    // Buat wadah notifikasi jika belum ada
    buatContainer() {
        const wadah = document.createElement('div');
        wadah.className = 'notif-container';
        document.body.appendChild(wadah);
        this.container = wadah;
    }

    // Tampilkan notifikasi
    tampil(teks, tipe = 'info', waktu = null) {
        const elemen = document.createElement('div');
        elemen.className = `notif ${tipe}`;
        elemen.innerHTML = `
            <span>${teks}</span>
            <button class="notif-tutup" onclick="this.parentElement.classList.add('hilang'); setTimeout(() => this.parentElement.remove(), 400);">&times;</button>
        `;

        // Masukkan ke wadah
        this.container.appendChild(elemen);

        // Efek muncul
        setTimeout(() => elemen.classList.add('muncul'), 10);

        // Hilang otomatis
        const durasi = waktu || this.waktuTampil;
        setTimeout(() => {
            if (elemen.parentElement) {
                elemen.classList.add('hilang');
                setTimeout(() => elemen.remove(), 400);
            }
        }, durasi);
    }

    // Baca pesan flash dari Flask
    bacaFlash() {
        if (window.pesanFlash && Array.isArray(window.pesanFlash)) {
            window.pesanFlash.forEach(pesan => {
                let tipe = 'info';
                if (pesan[0] === 'success') tipe = 'sukses';
                if (pesan[0] === 'danger') tipe = 'error';
                if (pesan[0] === 'warning') tipe = 'peringatan';
                if (pesan[0] === 'info') tipe = 'info';

                this.tampil(pesan[1], tipe);
            });
        }
    }
}

// Inisialisasi otomatis
const notif = new Notifikasi();
document.addEventListener('DOMContentLoaded', () => notif.bacaFlash());