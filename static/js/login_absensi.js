
(() => {
    'use strict';

    const $ = (selector, parent = document) =>
        parent.querySelector(selector);

    const form = $('#formLogin');
    const username = $('#username');
    const password = $('#password');
    const togglePassword = $('#togglePassword');
    const iconMata = $('#iconMata');
    const btnLogin = $('#btnLogin');
    const notifContainer = $('#notifContainer');

    /* =========================================
       PASSWORD VISIBILITY
    ========================================= */

    if (togglePassword && password && iconMata) {
        togglePassword.addEventListener('click', () => {
            const visible = password.type === 'password';

            password.type = visible ? 'text' : 'password';

            iconMata.classList.toggle('fa-eye', !visible);
            iconMata.classList.toggle('fa-eye-slash', visible);

            togglePassword.setAttribute(
                'aria-label',
                visible
                    ? 'Sembunyikan kata sandi'
                    : 'Tampilkan kata sandi'
            );

            togglePassword.setAttribute(
                'aria-pressed',
                String(visible)
            );

            password.focus({ preventScroll: true });
        });
    }

    /* =========================================
       INPUT ERROR HANDLING
    ========================================= */

    [username, password].forEach(input => {
        if (!input) return;

        input.addEventListener('input', () => {
            const wrapper = input.closest('.input-box');

            if (wrapper) {
                wrapper.classList.remove('has-error');
            }
        });
    });

    /* =========================================
       LOGIN LOADING
    ========================================= */

    if (form && btnLogin) {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                form.reportValidity();
                return;
            }

            if (btnLogin.disabled) {
                event.preventDefault();
                return;
            }

            btnLogin.disabled = true;
            btnLogin.classList.add('is-loading');

            const text = $('.button-text', btnLogin);
            const icon = $('.button-icon i', btnLogin);

            if (text) {
                text.textContent = 'Memverifikasi akun...';
            }

            if (icon) {
                icon.className = 'fa fa-spinner';
            }
        });
    }

    /* =========================================
       NOTIFICATION
    ========================================= */

    class Notifikasi {
        constructor(container) {
            this.container = container;
            this.defaultDuration = 4200;
        }

        tampil(teks, tipe = 'info', durasi = null) {
            if (!this.container) return;

            const item = document.createElement('div');
            item.className = `notif ${tipe}`;

            const message = document.createElement('span');
            message.textContent = String(teks);

            const close = document.createElement('button');
            close.type = 'button';
            close.className = 'notif-tutup';
            close.setAttribute('aria-label', 'Tutup notifikasi');
            close.textContent = '×';

            item.append(message, close);
            this.container.appendChild(item);

            let timer;

            const remove = () => {
                if (!item.isConnected) return;

                clearTimeout(timer);
                item.classList.add('hilang');

                setTimeout(() => item.remove(), 350);
            };

            close.addEventListener('click', remove);

            requestAnimationFrame(() => {
                item.classList.add('muncul');
            });

            timer = setTimeout(
                remove,
                Number(durasi) || this.defaultDuration
            );
        }

        bacaFlash() {
            const messages = Array.isArray(window.pesanFlash)
                ? window.pesanFlash
                : [];

            messages.forEach(message => {
                if (!Array.isArray(message) || message.length < 2) {
                    return;
                }

                const category = String(message[0]).toLowerCase();
                const text = message[1];

                let type = 'info';

                if (
                    category.includes('success') ||
                    category.includes('sukses')
                ) {
                    type = 'sukses';
                } else if (
                    category.includes('danger') ||
                    category.includes('error')
                ) {
                    type = 'error';
                } else if (category.includes('warning')) {
                    type = 'peringatan';
                }

                this.tampil(text, type);
            });
        }
    }

    const notification = new Notifikasi(notifContainer);
    notification.bacaFlash();

    /* =========================================
       DESKTOP INITIAL FOCUS
    ========================================= */

    if (
        username &&
        !username.value.trim() &&
        window.matchMedia('(min-width: 721px)').matches
    ) {
        setTimeout(() => {
            username.focus({ preventScroll: true });
        }, 550);
    }

})();
