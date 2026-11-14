
/* =========================================================
   TEACHER SCHEDULE — SPA READY
   SMPU PREMIUM EMERALD WORKSPACE
========================================================= */

(function () {
    'use strict';

    // Hindari memasang event SPA berulang kali
    if (window.__TJM_SPA_CONTROLLER__) {
        window.__TJM_SPA_CONTROLLER__.destroy();
    }

    const controller = {
        root: null,
        interval: null,
        initializedRoot: null,

        // ==========================================
        // INISIALISASI
        // ==========================================
        init() {
            const root = document.querySelector('.tjm-page');

            if (!root) {
                this.stop();
                return;
            }

            // Jika halaman yang sama sudah diinisialisasi,
            // jangan membuat listener dan timer baru.
            if (this.initializedRoot === root) {
                this.updateStatus();
                return;
            }

            this.stop();

            this.root = root;
            this.initializedRoot = root;

            this.initDayNavigation();
            this.updateStatus();
            this.startClock();

            console.log('[TJM] Jadwal Mengajar berhasil diinisialisasi.');
        },

        // ==========================================
        // BERHENTIKAN TIMER HALAMAN SEBELUMNYA
        // ==========================================
        stop() {
            if (this.interval) {
                window.clearInterval(this.interval);
                this.interval = null;
            }

            this.root = null;
            this.initializedRoot = null;
        },

        // ==========================================
        // NAVIGASI HARI
        // ==========================================
        initDayNavigation() {
            if (!this.root) return;

            const buttons = this.root.querySelectorAll(
                '.tjm-day-button'
            );

            const panels = this.root.querySelectorAll(
                '.tjm-day-panel'
            );

            const activateDay = (day) => {
                buttons.forEach(button => {
                    const active = button.dataset.day === day;

                    button.classList.toggle('active', active);

                    button.setAttribute(
                        'aria-pressed',
                        String(active)
                    );
                });

                panels.forEach(panel => {
                    panel.classList.toggle(
                        'active',
                        panel.dataset.dayPanel === day
                    );
                });
            };

            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    activateDay(button.dataset.day);
                });
            });

            // Gunakan hari berdasarkan waktu lokal browser.
            // Hari kerja yang tidak tersedia akan memilih
            // hari pertama yang memiliki jadwal.
            const namaHari = [
                'Minggu',
                'Senin',
                'Selasa',
                'Rabu',
                'Kamis',
                'Jumat',
                'Sabtu'
            ];

            const hariSekarang = namaHari[new Date().getDay()];

            const hariTersedia = Array.from(buttons).some(
                button => button.dataset.day === hariSekarang
            );

            if (hariTersedia) {
                activateDay(hariSekarang);
            } else {
                const hariDenganJadwal = Array.from(buttons).find(
                    button => {
                        const jumlah = Number(
                            button.querySelector('strong')?.textContent || 0
                        );

                        return jumlah > 0;
                    }
                );

                activateDay(
                    hariDenganJadwal?.dataset.day ||
                    buttons[0]?.dataset.day
                );
            }
        },

        // ==========================================
        // KONVERSI JAM KE MENIT
        // ==========================================
        getMinutes(value) {
            if (!value || !/^\d{1,2}:\d{2}$/.test(value)) {
                return null;
            }

            const [hour, minute] = value.split(':').map(Number);

            if (
                !Number.isInteger(hour) ||
                !Number.isInteger(minute) ||
                hour < 0 ||
                hour > 23 ||
                minute < 0 ||
                minute > 59
            ) {
                return null;
            }

            return hour * 60 + minute;
        },

        // ==========================================
        // UPDATE STATUS JADWAL
        // ==========================================
        updateStatus() {
            if (!this.root || !this.root.isConnected) {
                this.stop();
                return;
            }

            const now = new Date();

            const currentMinutes =
                now.getHours() * 60 + now.getMinutes();

            // --------------------------------------
            // KARTU JADWAL MINGGUAN
            // --------------------------------------
            this.root.querySelectorAll(
                '.tjm-class-card'
            ).forEach(card => {

                const start = this.getMinutes(
                    card.dataset.start
                );

                const end = this.getMinutes(
                    card.dataset.end
                );

                const status = card.querySelector(
                    '.tjm-class-status'
                );

                card.classList.remove(
                    'is-current',
                    'is-finished'
                );

                if (start === null || end === null) return;

                if (currentMinutes >= start && currentMinutes < end) {

                    card.classList.add('is-current');

                    if (status) {
                        status.innerHTML =
                            '<span></span> Sedang berlangsung';
                    }

                } else if (currentMinutes >= end) {

                    card.classList.add('is-finished');

                    if (status) {
                        status.innerHTML =
                            '<span></span> Selesai';
                    }

                } else if (status) {

                    status.innerHTML =
                        '<span></span> Terjadwal';

                }
            });

            // --------------------------------------
            // AGENDA HARI INI
            // --------------------------------------
            const namaHari = [
                'Minggu',
                'Senin',
                'Selasa',
                'Rabu',
                'Kamis',
                'Jumat',
                'Sabtu'
            ];

            const hariSekarang = namaHari[now.getDay()];

            this.root.querySelectorAll(
                '.tjm-today-item'
            ).forEach(item => {

                const start = this.getMinutes(
                    item.dataset.start
                );

                const end = this.getMinutes(
                    item.dataset.end
                );

                const status = item.querySelector(
                    '.tjm-today-status'
                );

                item.classList.remove(
                    'is-current',
                    'is-finished'
                );

                if (start === null || end === null || !status) {
                    return;
                }

                if (currentMinutes >= start && currentMinutes < end) {

                    item.classList.add('is-current');
                    status.textContent = 'Sedang berlangsung';

                } else if (currentMinutes >= end) {

                    item.classList.add('is-finished');
                    status.textContent = 'Selesai';

                } else {

                    status.textContent = 'Akan datang';

                }
            });
        },

        // ==========================================
        // JAM BERJALAN
        // ==========================================
        startClock() {
            if (this.interval) {
                window.clearInterval(this.interval);
            }

            this.interval = window.setInterval(() => {
                this.updateStatus();
            }, 60000);
        },

        // ==========================================
        // EVENT SEBELUM NAVIGASI SPA
        // ==========================================
        beforeUnload() {
            this.stop();
        }
    };

    // Simpan controller global supaya tidak ganda.
    window.__TJM_SPA_CONTROLLER__ = controller;

    // ==========================================
    // EVENT SPA NAVIGATION
    // ==========================================

    document.addEventListener(
        'spa:page-loaded',
        function () {
            controller.init();
        }
    );

    document.addEventListener(
        'spa:before-page-unload',
        function () {
            controller.beforeUnload();
        }
    );

    // ==========================================
    // INITIAL PAGE / RELOAD NORMAL
    // ==========================================

    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            function () {
                controller.init();
            },
            { once: true }
        );

    } else {

        controller.init();

    }

})();
