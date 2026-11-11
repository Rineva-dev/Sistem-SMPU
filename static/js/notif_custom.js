
/* =========================================================
   SMPU GLOBAL NOTIFICATION
   Premium SaaS Emerald
========================================================= */

(function () {
    'use strict';

    const ID_MODAL = 'modal-notif-global';

    const konfigurasiNotif = {
        sukses: {
            judul: 'Berhasil!',
            deskripsi: 'Proses berhasil diselesaikan.',
            ikon: '<i class="fas fa-check"></i>'
        },
        peringatan: {
            judul: 'Perhatian',
            deskripsi: 'Periksa kembali informasi berikut.',
            ikon: '<i class="fas fa-exclamation"></i>'
        },
        error: {
            judul: 'Terjadi Kesalahan',
            deskripsi: 'Ada sesuatu yang perlu diperiksa.',
            ikon: '<i class="fas fa-times"></i>'
        },
        info: {
            judul: 'Informasi',
            deskripsi: 'Berikut informasi untuk Anda.',
            ikon: '<i class="fas fa-info"></i>'
        }
    };

    let elemenSebelumnya = null;

    /* =====================================================
       BUAT MODAL OTOMATIS
    ===================================================== */

    function siapkanElemenModalNotif() {
        if (document.getElementById(ID_MODAL)) return;

        const html = `
            <div
                id="${ID_MODAL}"
                class="modal-notif-overlay"
                aria-hidden="true"
            >
                <div
                    class="modal-notif-kotak"
                    role="alertdialog"
                    aria-modal="true"
                    aria-labelledby="modal-notif-judul"
                    aria-describedby="modal-notif-teks-pesan"
                >

                    <div class="modal-notif-accent"></div>

                    <button
                        type="button"
                        class="modal-notif-close"
                        aria-label="Tutup notifikasi"
                        data-notif-close
                    >
                        <i class="fas fa-times"></i>
                    </button>

                    <div class="modal-notif-header">
                        <div
                            id="modal-notif-ikon-teks"
                            class="modal-notif-ikon"
                        ></div>

                        <div class="modal-notif-heading">
                            <span class="modal-notif-label">
                                SMPU NOTIFICATION
                            </span>

                            <h3 id="modal-notif-judul">
                                Informasi
                            </h3>
                        </div>
                    </div>

                    <div
                        id="modal-notif-teks-pesan"
                        class="modal-notif-teks"
                    ></div>

                    <div class="modal-notif-footer">
                        <span class="modal-notif-footer-info">
                            <i class="fas fa-shield-alt"></i>
                            Sistem Informasi SMPU
                        </span>

                        <button
                            type="button"
                            id="modal-notif-btn-ok"
                            class="modal-notif-tombol"
                        >
                            <span>Mengerti</span>
                            <i class="fas fa-arrow-right"></i>
                        </button>
                    </div>

                </div>
            </div>
        `;

        const temp = document.createElement('div');
        temp.innerHTML = html.trim();

        document.body.appendChild(temp.firstElementChild);

        const overlay = document.getElementById(ID_MODAL);

        overlay.querySelectorAll('[data-notif-close]').forEach(btn => {
            btn.addEventListener('click', tutupNotif);
        });

        document.getElementById('modal-notif-btn-ok')
            .addEventListener('click', tutupNotif);

        // Klik area luar untuk menutup.
        overlay.addEventListener('click', function (event) {
            if (event.target === overlay) {
                tutupNotif();
            }
        });

        // Tutup dengan tombol Escape.
        document.addEventListener('keydown', function (event) {
            if (
                event.key === 'Escape' &&
                overlay.classList.contains('aktif')
            ) {
                tutupNotif();
            }
        });
    }


    /* =====================================================
       TUTUP MODAL
    ===================================================== */

    function tutupNotif() {
        const overlay = document.getElementById(ID_MODAL);

        if (!overlay || !overlay.classList.contains('aktif')) {
            return;
        }

        overlay.classList.remove('aktif');
        overlay.setAttribute('aria-hidden', 'true');

        document.body.classList.remove('modal-notif-terbuka');

        if (elemenSebelumnya && elemenSebelumnya.isConnected) {
            elemenSebelumnya.focus({ preventScroll: true });
        }

        elemenSebelumnya = null;
    }


    /* =====================================================
       TAMPILKAN NOTIFIKASI
    ===================================================== */

    function tampilkanNotif(jenis, ikonHtml, pesanHtml) {
        siapkanElemenModalNotif();

        const overlay = document.getElementById(ID_MODAL);
        const kotakIkon = document.getElementById('modal-notif-ikon-teks');
        const kotakPesan = document.getElementById('modal-notif-teks-pesan');
        const judul = document.getElementById('modal-notif-judul');

        const tipe = konfigurasiNotif[jenis]
            ? jenis
            : 'info';

        const config = konfigurasiNotif[tipe];

        elemenSebelumnya = document.activeElement;

        // Atur jenis notifikasi.
        overlay.dataset.jenis = tipe;

        // Ikon dan judul.
        kotakIkon.className = `modal-notif-ikon ${tipe}`;
        kotakIkon.innerHTML = ikonHtml || config.ikon;

        judul.textContent = config.judul;

        // Isi pesan mendukung HTML seperti <strong>.
        kotakPesan.innerHTML = pesanHtml ?? config.deskripsi;

        // Tampilkan modal.
        overlay.setAttribute('aria-hidden', 'false');
        overlay.classList.add('aktif');

        document.body.classList.add('modal-notif-terbuka');

        // Fokus ke tombol agar bisa langsung menggunakan keyboard.
        requestAnimationFrame(() => {
            document.getElementById('modal-notif-btn-ok')?.focus({
                preventScroll: true
            });
        });
    }


    /* =====================================================
       GLOBAL ALIAS
    ===================================================== */

    window.tampilkanNotif = tampilkanNotif;
    window.tutupNotif = tutupNotif;

    window.notifSukses = function (pesan) {
        tampilkanNotif(
            'sukses',
            '<i class="fas fa-check"></i>',
            pesan
        );
    };

    window.notifPeringatan = function (pesan) {
        tampilkanNotif(
            'peringatan',
            '<i class="fas fa-exclamation"></i>',
            pesan
        );
    };

    window.notifError = function (pesan) {
        tampilkanNotif(
            'error',
            '<i class="fas fa-times"></i>',
            pesan
        );
    };

    window.notifInfo = function (pesan) {
        tampilkanNotif(
            'info',
            '<i class="fas fa-info"></i>',
            pesan
        );
    };

})();
