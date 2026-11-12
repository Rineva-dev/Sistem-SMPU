
(() => {
    'use strict';

    const GLOBAL_KEY = '__SMPU_TEACHER_DASHBOARD__';

    // Bersihkan instance sebelumnya ketika halaman dimuat ulang oleh SPA.
    if (window[GLOBAL_KEY] && typeof window[GLOBAL_KEY].destroy === 'function') {
        window[GLOBAL_KEY].destroy();
    }

    const root = document.querySelector('.edux-workspace');
    if (!root) return;

    const agendaData = Array.isArray(window.agendaData)
        ? window.agendaData
        : [];

    const btnDaftar = root.querySelector('#btnTampilanDaftar');
    const btnKalender = root.querySelector('#btnTampilanKalender');
    const tampilanDaftar = root.querySelector('#tampilanDaftar');
    const tampilanKalender = root.querySelector('#tampilanKalender');
    const kalenderElement = root.querySelector('#kalenderDashboard');

    const modal = root.querySelector('#modalDetailAgenda');
    const modalTitle = root.querySelector('#eduxModalTitle');
    const modalContent = root.querySelector('#kontenDetailAgenda');
    const closeModalButton = root.querySelector('#tutupModalAgenda');
    const closeModalFooter = root.querySelector('#tutupModalAgendaFooter');

    let calendar = null;
    let destroyed = false;
    let previousBodyOverflow = '';

    const listeners = [];

    function listen(element, eventName, callback) {
        if (!element) return;

        element.addEventListener(eventName, callback);
        listeners.push(() => {
            element.removeEventListener(eventName, callback);
        });
    }

    function normalizeDate(value) {
        if (!value) return null;

        // Menghindari parsing tanggal lokal yang bergeser karena timezone.
        const date = new Date(value);

        return Number.isNaN(date.getTime()) ? null : date;
    }

    function formatDate(value) {
        const date = normalizeDate(value);

        if (!date) return 'Belum ditentukan';

        return new Intl.DateTimeFormat('id-ID', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        }).format(date);
    }

    function formatTime(value) {
        const date = normalizeDate(value);

        if (!date) return 'Waktu belum ditentukan';

        return new Intl.DateTimeFormat('id-ID', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        }).format(date) + ' WITA';
    }

    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, char => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        })[char]);
    }

    function getAgendaById(id) {
        return agendaData.find(item => String(item.id) === String(id));
    }

    function showAgendaDetail(id) {
        const agenda = getAgendaById(id);

        if (!agenda || !modal || !modalContent) return;

        const title = agenda.judul || 'Detail agenda';
        const mulai = agenda.tanggal_mulai || agenda.tgl_mulai;
        const selesai = agenda.tanggal_selesai || agenda.tgl_selesai;
        const lokasi = agenda.lokasi || 'Lokasi belum ditentukan';
        const penanggungJawab = agenda.penanggung_jawab || 'Belum ditentukan';
        const status = agenda.status || 'Agenda sekolah';
        const deskripsi = agenda.deskripsi || agenda.isi || 'Tidak ada deskripsi tambahan.';

        modalTitle.textContent = title;

        modalContent.innerHTML = `
            <div class="edux-detail-row">
                <span class="edux-detail-icon">
                    <i class="fa-regular fa-calendar"></i>
                </span>
                <span>
                    <small>Tanggal mulai</small>
                    <strong>${escapeHTML(formatDate(mulai))}</strong>
                </span>
            </div>

            <div class="edux-detail-row">
                <span class="edux-detail-icon">
                    <i class="fa-regular fa-clock"></i>
                </span>
                <span>
                    <small>Waktu mulai</small>
                    <strong>${escapeHTML(formatTime(mulai))}</strong>
                </span>
            </div>

            <div class="edux-detail-row">
                <span class="edux-detail-icon">
                    <i class="fa-solid fa-calendar-check"></i>
                </span>
                <span>
                    <small>Tanggal selesai</small>
                    <strong>${escapeHTML(formatDate(selesai))}</strong>
                </span>
            </div>

            <div class="edux-detail-row">
                <span class="edux-detail-icon">
                    <i class="fa-solid fa-location-dot"></i>
                </span>
                <span>
                    <small>Lokasi kegiatan</small>
                    <strong>${escapeHTML(lokasi)}</strong>
                </span>
            </div>

            <div class="edux-detail-row">
                <span class="edux-detail-icon">
                    <i class="fa-solid fa-user-tie"></i>
                </span>
                <span>
                    <small>Penanggung jawab</small>
                    <strong>${escapeHTML(penanggungJawab)}</strong>
                </span>
            </div>

            <div class="edux-detail-row">
                <span class="edux-detail-icon">
                    <i class="fa-solid fa-circle-info"></i>
                </span>
                <span>
                    <small>Status agenda</small>
                    <strong>${escapeHTML(status)}</strong>
                </span>
            </div>

            <div class="edux-detail-description">
                ${escapeHTML(deskripsi).replace(/\n/g, '<br>')}
            </div>

            <div style="margin-top:20px">
                <a
                    href="/agenda/detail/${encodeURIComponent(agenda.id)}"
                    style="
                        display:inline-flex;
                        align-items:center;
                        gap:8px;
                        padding:10px 14px;
                        border-radius:9px;
                        background:#eaf7ef;
                        color:#08785b;
                        font-size:10px;
                        font-weight:800;
                        text-decoration:none;
                    "
                >
                    Buka halaman agenda
                    <i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
            </div>
        `;

        openModal();
    }

    function openModal() {
        if (!modal) return;

        previousBodyOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';

        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');

        if (closeModalButton) {
            closeModalButton.focus();
        }
    }

    function closeModal() {
        if (!modal) return;

        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = previousBodyOverflow;
    }

    function switchView(view) {
        const showCalendar = view === 'calendar';

        if (tampilanDaftar) {
            tampilanDaftar.hidden = showCalendar;
        }

        if (tampilanKalender) {
            tampilanKalender.hidden = !showCalendar;
        }

        btnDaftar?.classList.toggle('active', !showCalendar);
        btnKalender?.classList.toggle('active', showCalendar);

        if (showCalendar) {
            initializeCalendar();

            // FullCalendar perlu menghitung ulang ukuran setelah container terlihat.
            requestAnimationFrame(() => {
                if (calendar && !destroyed) {
                    calendar.updateSize();
                }
            });
        }
    }

    function buildCalendarEvents() {
        return agendaData
            .filter(item => {
                return item.tanggal_mulai || item.tgl_mulai;
            })
            .map(item => {
                const start = item.tanggal_mulai || item.tgl_mulai;
                const end = item.tanggal_selesai || item.tgl_selesai;

                return {
                    id: String(item.id),
                    title: item.judul || 'Agenda sekolah',
                    start: start,
                    end: end || undefined,
                    allDay: false,
                    backgroundColor: '#dff4e8',
                    borderColor: '#b7e4c8',
                    textColor: '#08785b',
                    extendedProps: {
                        agendaId: item.id
                    }
                };
            });
    }

    function initializeCalendar() {
        if (!kalenderElement || calendar || destroyed) return;

        if (typeof FullCalendar === 'undefined') {
            kalenderElement.innerHTML = `
                <div class="edux-agenda-empty">
                    <div class="edux-empty-illustration">
                        <i class="fa-solid fa-calendar-xmark"></i>
                    </div>
                    <h4>Kalender tidak dapat dimuat</h4>
                    <p>Pastikan library FullCalendar sudah dimuat melalui layout utama.</p>
                </div>
            `;
            return;
        }

        calendar = new FullCalendar.Calendar(kalenderElement, {
            initialView: 'dayGridMonth',
            locale: 'id',
            height: 'auto',
            firstDay: 1,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,listMonth'
            },
            buttonText: {
                today: 'Hari ini',
                month: 'Bulan',
                list: 'Daftar'
            },
            events: buildCalendarEvents(),

            eventClick(info) {
                info.jsEvent.preventDefault();

                const id = info.event.extendedProps.agendaId
                    || info.event.id;

                showAgendaDetail(id);
            },

            dayMaxEvents: 3,
            eventDisplay: 'block',
            displayEventTime: true,
            eventTimeFormat: {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            }
        });

        calendar.render();
    }

    // Ganti tampilan agenda.
    listen(btnDaftar, 'click', () => switchView('list'));
    listen(btnKalender, 'click', () => switchView('calendar'));

    // Detail agenda dari daftar.
    listen(root, 'click', event => {
        const detailButton = event.target.closest('.edux-agenda-detail-btn');

        if (!detailButton || !root.contains(detailButton)) return;

        showAgendaDetail(detailButton.dataset.agendaId);
    });

    // Modal.
    listen(closeModalButton, 'click', closeModal);
    listen(closeModalFooter, 'click', closeModal);

    listen(modal, 'click', event => {
        if (event.target === modal) {
            closeModal();
        }
    });

    listen(document, 'keydown', event => {
        if (event.key === 'Escape' && modal?.classList.contains('is-open')) {
            closeModal();
        }
    });

    // Lifecycle cleanup untuk navigasi SPA.
    window[GLOBAL_KEY] = {
        destroy() {
            if (destroyed) return;

            destroyed = true;

            listeners.forEach(removeListener => removeListener());
            listeners.length = 0;

            if (calendar) {
                calendar.destroy();
                calendar = null;
            }

            if (modal) {
                modal.classList.remove('is-open');
                modal.setAttribute('aria-hidden', 'true');
            }

            document.body.style.overflow = previousBodyOverflow;
        }
    };

    // Daftar menjadi tampilan awal.
    switchView('list');

})();
