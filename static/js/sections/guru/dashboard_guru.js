
/* =========================================================
   SMPU TEACHER DASHBOARD
   PREMIUM WORKSPACE
========================================================= */

(() => {
    'use strict';

    const GLOBAL_KEY = '__SMPU_TEACHER_DASHBOARD__';

    /*
     * Hindari listener dan kalender terduplikasi
     * ketika dashboard dimuat melalui SPA.
     */
    if (window[GLOBAL_KEY]) {
        window[GLOBAL_KEY].destroy();
    }

    const dashboard = document.querySelector('.teacher-dashboard');

    if (!dashboard) {
        return;
    }

    const state = {
        root: dashboard,
        kalender: null,
        modal: null,
        initialized: false,
        destroyed: false
    };


    /* =====================================================
       ELEMENTS
    ====================================================== */

    const btnDaftar = dashboard.querySelector(
        '#btnTampilanDaftar'
    );

    const btnKalender = dashboard.querySelector(
        '#btnTampilanKalender'
    );

    const tampilanDaftar = dashboard.querySelector(
        '#tampilanDaftar'
    );

    const tampilanKalender = dashboard.querySelector(
        '#tampilanKalender'
    );

    const kalenderElement = dashboard.querySelector(
        '#kalenderDashboard'
    );


    /* =====================================================
       HELPERS
    ====================================================== */

    function escapeHTML(value) {

        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');

    }


    function getAgendaData() {

        const data = window.agendaData;

        if (!Array.isArray(data)) {
            return [];
        }

        return data;

    }


    function normalizeStatus(status) {

        return String(status || 'terjadwal')
            .toLowerCase()
            .trim()
            .replace(/\s+/g, '-');

    }


    function getStatusInfo(status) {

        const normalized = normalizeStatus(status);

        const statusMap = {
            terjadwal: {
                label: 'Terjadwal',
                color: 'blue'
            },

            berlangsung: {
                label: 'Berlangsung',
                color: 'green'
            },

            selesai: {
                label: 'Selesai',
                color: 'gray'
            },

            dibatalkan: {
                label: 'Dibatalkan',
                color: 'red'
            }
        };

        return statusMap[normalized] || {
            label: status || 'Tidak diketahui',
            color: 'gray'
        };

    }


    function formatTanggal(value) {

        if (!value) {
            return '-';
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return '-';
        }

        return new Intl.DateTimeFormat('id-ID', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        }).format(date);

    }


    function getAgendaById(id) {

        return getAgendaData().find(
            item => String(item.id) === String(id)
        );

    }


    /* =====================================================
       SWITCH DAFTAR / KALENDER
    ====================================================== */

    function setTampilan(mode) {

        const isKalender = mode === 'kalender';

        if (
            !btnDaftar ||
            !btnKalender ||
            !tampilanDaftar ||
            !tampilanKalender
        ) {
            return;
        }

        btnDaftar.classList.toggle(
            'active',
            !isKalender
        );

        btnKalender.classList.toggle(
            'active',
            isKalender
        );

        btnDaftar.setAttribute(
            'aria-pressed',
            String(!isKalender)
        );

        btnKalender.setAttribute(
            'aria-pressed',
            String(isKalender)
        );


        tampilanDaftar.classList.toggle(
            'd-none',
            isKalender
        );

        tampilanKalender.classList.toggle(
            'd-none',
            !isKalender
        );


        if (isKalender) {

            initKalenderDashboard();

            /*
             * FullCalendar perlu update ukuran
             * ketika container baru terlihat.
             */
            requestAnimationFrame(() => {

                if (state.kalender) {
                    state.kalender.updateSize();
                }

            });

        }

    }


    /* =====================================================
       DETAIL AGENDA
    ====================================================== */

    function bukaModalDetail(agenda) {

        if (!agenda || state.destroyed) {
            return;
        }

        tutupModal();

        const status = getStatusInfo(
            agenda.status
        );

        const modal = document.createElement('div');

        modal.className = 'td-modal-overlay';

        modal.setAttribute(
            'role',
            'presentation'
        );

        modal.innerHTML = `
            <div
                class="td-modal-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="tdModalTitle"
            >

                <div class="td-modal-header">

                    <div class="td-modal-header-icon">
                        <i class="fas fa-calendar-check"></i>
                    </div>

                    <div class="td-modal-header-content">

                        <span class="td-modal-eyebrow">
                            SCHOOL ACTIVITIES
                        </span>

                        <h3 id="tdModalTitle">
                            Detail Agenda
                        </h3>

                    </div>

                    <button
                        type="button"
                        class="td-modal-close"
                        aria-label="Tutup detail agenda"
                    >
                        <i class="fas fa-times"></i>
                    </button>

                </div>


                <div class="td-modal-body">

                    <div class="td-modal-agenda-title">
                        ${escapeHTML(agenda.judul || 'Agenda Sekolah')}
                    </div>

                    <div class="td-modal-status">
                        <span class="td-modal-status-dot td-status-${escapeHTML(status.color)}"></span>

                        <span>
                            ${escapeHTML(status.label)}
                        </span>
                    </div>


                    <div class="td-modal-details">

                        <div class="td-modal-detail-row">

                            <div class="td-modal-detail-icon">
                                <i class="far fa-calendar"></i>
                            </div>

                            <div class="td-modal-detail-content">

                                <span class="td-modal-detail-label">
                                    Waktu Mulai
                                </span>

                                <strong>
                                    ${escapeHTML(formatTanggal(agenda.tanggal_mulai))}
                                </strong>

                            </div>

                        </div>


                        <div class="td-modal-detail-row">

                            <div class="td-modal-detail-icon">
                                <i class="far fa-clock"></i>
                            </div>

                            <div class="td-modal-detail-content">

                                <span class="td-modal-detail-label">
                                    Waktu Selesai
                                </span>

                                <strong>
                                    ${escapeHTML(formatTanggal(agenda.tanggal_selesai))}
                                </strong>

                            </div>

                        </div>


                        <div class="td-modal-detail-row">

                            <div class="td-modal-detail-icon">
                                <i class="fas fa-map-marker-alt"></i>
                            </div>

                            <div class="td-modal-detail-content">

                                <span class="td-modal-detail-label">
                                    Lokasi
                                </span>

                                <strong>
                                    ${escapeHTML(agenda.lokasi || 'Belum ditentukan')}
                                </strong>

                            </div>

                        </div>


                        <div class="td-modal-detail-row">

                            <div class="td-modal-detail-icon">
                                <i class="fas fa-user"></i>
                            </div>

                            <div class="td-modal-detail-content">

                                <span class="td-modal-detail-label">
                                    Penanggung Jawab
                                </span>

                                <strong>
                                    ${escapeHTML(agenda.penanggung_jawab || 'Belum ditentukan')}
                                </strong>

                            </div>

                        </div>

                    </div>


                    <div class="td-modal-description">

                        <div class="td-modal-description-heading">
                            <i class="fas fa-align-left"></i>
                            Deskripsi Kegiatan
                        </div>

                        <p>
                            ${escapeHTML(agenda.deskripsi || 'Tidak ada keterangan tambahan untuk agenda ini.')}
                        </p>

                    </div>

                </div>


                <div class="td-modal-footer">

                    <button
                        type="button"
                        class="td-modal-dismiss"
                    >
                        Tutup
                    </button>

                    <a
                        class="td-modal-open-detail"
                        href="/agenda/detail/${encodeURIComponent(String(agenda.id))}"
                    >
                        Buka Agenda
                        <i class="fas fa-arrow-right"></i>
                    </a>

                </div>

            </div>
        `;


        /*
         * Modal styling.
         */
        modal.style.cssText = `
            position: fixed;
            inset: 0;
            z-index: 99999;

            display: flex;
            align-items: center;
            justify-content: center;

            padding: 1rem;

            background: rgba(5, 25, 17, .58);

            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
        `;


        document.body.appendChild(modal);

        state.modal = modal;


        /*
         * Tutup tombol.
         */
        const closeButton = modal.querySelector(
            '.td-modal-close'
        );

        const dismissButton = modal.querySelector(
            '.td-modal-dismiss'
        );

        closeButton.addEventListener(
            'click',
            tutupModal
        );

        dismissButton.addEventListener(
            'click',
            tutupModal
        );


        /*
         * Klik backdrop.
         */
        modal.addEventListener('click', function(event) {

            if (event.target === modal) {
                tutupModal();
            }

        });


        /*
         * Escape.
         */
        state.escapeHandler = function(event) {

            if (event.key === 'Escape') {
                tutupModal();
            }

        };

        document.addEventListener(
            'keydown',
            state.escapeHandler
        );


        /*
         * Fokus tombol close.
         */
        closeButton.focus();

    }


    function tutupModal() {

        if (!state.modal) {
            return;
        }

        state.modal.remove();

        state.modal = null;

        if (state.escapeHandler) {

            document.removeEventListener(
                'keydown',
                state.escapeHandler
            );

            state.escapeHandler = null;

        }

    }


    /* =====================================================
       FULLCALENDAR
    ====================================================== */

    function initKalenderDashboard() {

        if (
            state.kalender ||
            !kalenderElement ||
            state.destroyed
        ) {
            return;
        }


        /*
         * Cek FullCalendar.
         */
        if (
            typeof FullCalendar === 'undefined' ||
            typeof FullCalendar.Calendar !== 'function'
        ) {

            kalenderElement.innerHTML = `
                <div class="td-empty-state">

                    <div class="td-empty-icon">
                        <i class="fas fa-calendar-exclamation"></i>
                    </div>

                    <h4>Kalender belum tersedia</h4>

                    <p>
                        Library FullCalendar belum dimuat.
                        Silakan periksa konfigurasi library kalender.
                    </p>

                </div>
            `;

            return;

        }


        const agenda = getAgendaData();


        /*
         * Mapping agenda.
         */
        const events = agenda.map(item => {

            const status = normalizeStatus(
                item.status
            );

            return {

                id: String(item.id),

                title: item.judul || 'Agenda Sekolah',

                start: item.tanggal_mulai,

                end: item.tanggal_selesai || null,

                classNames: [
                    status
                ],

                extendedProps: {

                    lokasi: item.lokasi || '-',

                    penanggung_jawab:
                        item.penanggung_jawab || '-',

                    deskripsi:
                        item.deskripsi || '',

                    status:
                        item.status || 'Terjadwal'

                }

            };

        }).filter(item => item.start);


        /*
         * Buat kalender.
         */
        state.kalender = new FullCalendar.Calendar(
            kalenderElement,
            {

                initialView: 'dayGridMonth',

                locale: 'id',

                height: 'auto',

                firstDay: 1,

                dayMaxEvents: 3,

                headerToolbar: {

                    left: 'prev,next today',

                    center: 'title',

                    right: 'dayGridMonth,timeGridWeek'

                },

                buttonText: {

                    today: 'Hari ini',

                    month: 'Bulan',

                    week: 'Minggu'

                },

                events: events,


                eventContent: function(arg) {

                    const title = document.createElement(
                        'div'
                    );

                    title.className = 'fc-event-title';

                    title.textContent =
                        arg.event.title || 'Agenda';


                    const wrapper = document.createElement(
                        'div'
                    );

                    wrapper.appendChild(title);


                    if (arg.event.start) {

                        const waktu = document.createElement(
                            'div'
                        );

                        waktu.className = 'fc-event-time';

                        waktu.textContent =
                            arg.event.start.toLocaleTimeString(
                                'id-ID',
                                {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    hour12: false
                                }
                            );

                        wrapper.prepend(waktu);

                    }


                    return {
                        domNodes: [wrapper]
                    };

                },


                eventClick: function(info) {

                    info.jsEvent.preventDefault();

                    const agenda = getAgendaById(
                        info.event.id
                    );

                    if (agenda) {
                        bukaModalDetail(agenda);
                    }

                },


                dateClick: function() {

                    /*
                     * Tidak membuka modal saat
                     * klik tanggal kosong.
                     */

                }

            }
        );


        state.kalender.render();

    }


    /* =====================================================
       EVENT DELEGATION
    ====================================================== */

    function handleDashboardClick(event) {

        const target = event.target;

        if (!(target instanceof Element)) {
            return;
        }


        /*
         * Switch daftar.
         */
        const daftarButton = target.closest(
            '#btnTampilanDaftar'
        );

        if (daftarButton) {

            event.preventDefault();

            setTampilan('daftar');

            return;

        }


        /*
         * Switch kalender.
         */
        const kalenderButton = target.closest(
            '#btnTampilanKalender'
        );

        if (kalenderButton) {

            event.preventDefault();

            setTampilan('kalender');

            return;

        }


        /*
         * Detail agenda.
         */
        const detailButton = target.closest(
            '.td-agenda-detail'
        );

        if (detailButton) {

            event.preventDefault();

            const href = detailButton.getAttribute(
                'href'
            );

            if (!href) {
                return;
            }

            const id = href.split('/').pop();

            const agenda = getAgendaById(id);

            if (agenda) {
                bukaModalDetail(agenda);
            }

        }

    }


    /* =====================================================
       INIT
    ====================================================== */

    function init() {

        if (state.initialized || state.destroyed) {
            return;
        }

        state.initialized = true;


        /*
         * Default daftar.
         */
        setTampilan('daftar');


        /*
         * Delegation pada root dashboard.
         */
        dashboard.addEventListener(
            'click',
            handleDashboardClick
        );

    }


    /* =====================================================
       DESTROY
    ====================================================== */

    function destroy() {

        if (state.destroyed) {
            return;
        }

        state.destroyed = true;


        dashboard.removeEventListener(
            'click',
            handleDashboardClick
        );


        tutupModal();


        if (state.kalender) {

            state.kalender.destroy();

            state.kalender = null;

        }

    }


    /*
     * Public instance.
     */
    window[GLOBAL_KEY] = {
        init,
        destroy,
        setTampilan,
        bukaModalDetail
    };


    /*
     * Inisialisasi.
     *
     * Cocok untuk halaman biasa maupun
     * halaman yang sudah berada dalam DOM.
     */
    init();


})();
