
/* ==========================================================
   NOVA ACADEMIC WORKSPACE
   Timetable Controller
========================================================== */

(function () {
    const DAYS = [
        'Senin', 'Selasa', 'Rabu', 'Kamis',
        'Jumat', 'Sabtu', 'Minggu'
    ];

    function initNovaTimetable() {
        const page = document.querySelector('.nova-timetable');

        if (!page || page.dataset.novaReady === 'true') return;

        const form = page.querySelector('#novaJadwalForm');
        const list = page.querySelector('#wadahDaftarHari');
        const dataElement = page.querySelector('#data-daftar-mapel-json');

        const modal = document.getElementById('novaDayModal');
        const daySelect = document.getElementById('novaDaySelect');
        const dayError = document.getElementById('novaDayError');

        if (!form || !list || !dataElement || !modal || !daySelect) return;

        page.dataset.novaReady = 'true';

        let subjects = [];

        try {
            subjects = JSON.parse(dataElement.textContent.trim());
        } catch (error) {
            console.error('NOVA: Gagal membaca mata pelajaran.', error);
            alert('Data mata pelajaran tidak dapat dibaca.');
            return;
        }

        /* ------------------------------------------
           HELPERS
        ------------------------------------------ */

        const getDayName = card =>
            card.querySelector('.nova-day-value')?.value || '';

        const getCards = () =>
            Array.from(list.querySelectorAll('.nova-day'));

        const getExistingDays = () =>
            getCards().map(getDayName);

        function updateNumbers() {
            const cards = getCards();

            cards.forEach(card => {
                const index = DAYS.indexOf(getDayName(card));
                const number = card.querySelector('.nova-day-index');

                if (number) {
                    number.textContent = String(index + 1).padStart(2, '0');
                }
            });
        }

        function sortDays() {
            const cards = getCards();

            cards.sort((a, b) =>
                DAYS.indexOf(getDayName(a)) -
                DAYS.indexOf(getDayName(b))
            );

            cards.forEach(card => list.appendChild(card));
            updateNumbers();
            updateSummary();
        }

        function updateSummary() {
            const count = getCards().length;
            const empty = document.getElementById('novaEmpty');
            const total = document.getElementById('novaDayTotal');

            if (empty) empty.hidden = count !== 0;

            if (total) {
                total.textContent = `${count} hari terjadwal`;
            }
        }

        function makeOption(value, label) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            return option;
        }

        function makeSubjectSelect() {
            const select = document.createElement('select');
            select.name = 'mapel_id[]';
            select.required = true;

            select.appendChild(
                makeOption('', 'Pilih mata pelajaran')
            );

            select.appendChild(makeOption('imtaq', 'Imtaq'));
            select.appendChild(makeOption('upacara', 'Upacara Bendera'));

            subjects.forEach(subject => {
                select.appendChild(
                    makeOption(String(subject.id), subject.nama)
                );
            });

            return select;
        }

        /* ------------------------------------------
           CREATE SESSION
        ------------------------------------------ */

        function createSession(day) {
            const row = document.createElement('div');
            row.className = 'nova-session';

            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'hari[]';
            hidden.value = day;

            const timeControl = document.createElement('div');
            timeControl.className = 'nova-time-control';

            const startLabel = document.createElement('label');
            startLabel.className = 'nova-time-box';

            const startCaption = document.createElement('span');
            startCaption.textContent = 'MULAI';

            const startInput = document.createElement('input');
            startInput.type = 'time';
            startInput.name = 'jam_mulai[]';
            startInput.required = true;

            startLabel.append(startCaption, startInput);

            const arrow = document.createElement('span');
            arrow.className = 'nova-time-arrow';
            arrow.innerHTML = '<i class="fas fa-arrow-right"></i>';

            const endLabel = document.createElement('label');
            endLabel.className = 'nova-time-box';

            const endCaption = document.createElement('span');
            endCaption.textContent = 'SELESAI';

            const endInput = document.createElement('input');
            endInput.type = 'time';
            endInput.name = 'jam_selesai[]';
            endInput.required = true;

            endLabel.append(endCaption, endInput);

            timeControl.append(startLabel, arrow, endLabel);

            const subjectControl = document.createElement('div');
            subjectControl.className = 'nova-subject-control';

            const mobileLabel = document.createElement('span');
            mobileLabel.className = 'nova-mobile-label';
            mobileLabel.textContent = 'MATA PELAJARAN';

            const selectWrap = document.createElement('div');
            selectWrap.className = 'nova-select-wrap';

            const bookIcon = document.createElement('i');
            bookIcon.className = 'fas fa-book-open';

            const select = makeSubjectSelect();

            const arrowIcon = document.createElement('i');
            arrowIcon.className = 'fas fa-chevron-down nova-select-arrow';

            selectWrap.append(bookIcon, select, arrowIcon);
            subjectControl.append(mobileLabel, selectWrap);

            const remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'nova-remove-session hapus-baris';
            remove.title = 'Hapus sesi';
            remove.innerHTML = '<i class="fas fa-xmark"></i>';

            row.append(hidden, timeControl, subjectControl, remove);

            return row;
        }

        /* ------------------------------------------
           CREATE DAY
        ------------------------------------------ */

        function createDay(day) {
            const card = document.createElement('section');
            card.className = 'nova-day';
            card.dataset.day = day;

            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.className = 'nova-day-value';
            hidden.value = day;

            const identity = document.createElement('div');
            identity.className = 'nova-day-identity';

            const index = document.createElement('span');
            index.className = 'nova-day-index';

            const nameWrap = document.createElement('div');
            nameWrap.className = 'nova-day-name-wrap';

            const name = document.createElement('strong');
            name.className = 'nova-day-name';
            name.textContent = day;

            const caption = document.createElement('span');
            caption.className = 'nova-day-caption';
            caption.textContent = 'Hari pembelajaran';

            nameWrap.append(name, caption);

            const indicator = document.createElement('span');
            indicator.className = 'nova-day-indicator';

            identity.append(index, nameWrap, indicator);

            const sessions = document.createElement('div');
            sessions.className = 'nova-day-sessions';
            sessions.appendChild(createSession(day));

            const addSession = document.createElement('button');
            addSession.type = 'button';
            addSession.className = 'nova-add-session tambah-baris';
            addSession.innerHTML =
                '<i class="fas fa-plus"></i> Tambah sesi pembelajaran';

            sessions.appendChild(addSession);

            const actions = document.createElement('div');
            actions.className = 'nova-day-actions';

            const removeDay = document.createElement('button');
            removeDay.type = 'button';
            removeDay.className = 'nova-remove-day hapus-hari';
            removeDay.title = 'Hapus hari';
            removeDay.innerHTML = '<i class="fas fa-trash-can"></i>';

            actions.appendChild(removeDay);

            card.append(hidden, identity, sessions, actions);

            return card;
        }

        /* ------------------------------------------
           MODAL
        ------------------------------------------ */

        function openModal() {
            daySelect.value = '';
            dayError.textContent = '';

            const existing = getExistingDays();

            Array.from(daySelect.options).forEach(option => {
                if (option.value) {
                    option.disabled = existing.includes(option.value);
                }
            });

            modal.classList.add('is-open');
            modal.setAttribute('aria-hidden', 'false');
            daySelect.focus();
        }

        function closeModal() {
            modal.classList.remove('is-open');
            modal.setAttribute('aria-hidden', 'true');
        }

        function addDay() {
            const day = daySelect.value;

            if (!day) {
                dayError.textContent = 'Pilih hari terlebih dahulu.';
                daySelect.focus();
                return;
            }

            if (!DAYS.includes(day) || getExistingDays().includes(day)) {
                dayError.textContent = 'Hari tidak valid atau sudah tersedia.';
                return;
            }

            const card = createDay(day);

            list.appendChild(card);

            sortDays();
            updateSummary();
            closeModal();

            card.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }

        page.querySelector('#btnTambahHari')
            ?.addEventListener('click', openModal);

        document.getElementById('btnTambahHariEmpty')
            ?.addEventListener('click', openModal);

        document.getElementById('novaConfirmDay')
            ?.addEventListener('click', addDay);

        modal.querySelectorAll('[data-nova-close]').forEach(button => {
            button.addEventListener('click', closeModal);
        });

        daySelect.addEventListener('change', () => {
            dayError.textContent = '';
        });

        modal.addEventListener('keydown', event => {
            if (event.key === 'Escape') closeModal();
        });

        /* ------------------------------------------
           DELEGATED ACTIONS
        ------------------------------------------ */

        list.addEventListener('click', event => {
            const addSession = event.target.closest('.tambah-baris');

            if (addSession) {
                const card = addSession.closest('.nova-day');
                const day = getDayName(card);
                const sessions = card.querySelector('.nova-day-sessions');

                sessions.insertBefore(
                    createSession(day),
                    addSession
                );

                return;
            }

            const removeSession = event.target.closest('.hapus-baris');

            if (removeSession) {
                const session = removeSession.closest('.nova-session');
                const card = session.closest('.nova-day');

                const count = card.querySelectorAll('.nova-session').length;

                if (count <= 1) {
                    alert('Minimal harus ada satu sesi pada setiap hari.');
                    return;
                }

                session.remove();
                return;
            }

            const removeDay = event.target.closest('.hapus-hari');

            if (removeDay) {
                const card = removeDay.closest('.nova-day');
                const day = getDayName(card);

                if (confirm(`Hapus seluruh jadwal hari ${day}?`)) {
                    card.remove();
                    sortDays();
                    updateSummary();
                }
            }
        });

        /* ------------------------------------------
           VALIDATION
        ------------------------------------------ */

        form.addEventListener('submit', event => {
            const sessions = Array.from(
                form.querySelectorAll('.nova-session')
            );

            if (!sessions.length) {
                event.preventDefault();
                alert('Tambahkan setidaknya satu hari dan sesi pembelajaran.');
                return;
            }

            for (const session of sessions) {
                const start = session.querySelector('[name="jam_mulai[]"]');
                const end = session.querySelector('[name="jam_selesai[]"]');
                const subject = session.querySelector('[name="mapel_id[]"]');

                if (!start.value || !end.value || !subject.value) {
                    event.preventDefault();
                    alert('Lengkapi seluruh waktu dan mata pelajaran.');
                    return;
                }

                if (start.value >= end.value) {
                    event.preventDefault();
                    alert('Jam selesai harus lebih besar dari jam mulai.');
                    end.focus();
                    return;
                }
            }

            // Cek tabrakan waktu pada hari yang sama
            const grouped = {};

            sessions.forEach(session => {
                const day = session.querySelector('[name="hari[]"]').value;
                const start = session.querySelector('[name="jam_mulai[]"]').value;
                const end = session.querySelector('[name="jam_selesai[]"]').value;

                if (!grouped[day]) grouped[day] = [];

                grouped[day].push({
                    start,
                    end,
                    element: session
                });
            });

            for (const [day, items] of Object.entries(grouped)) {
                items.sort((a, b) => a.start.localeCompare(b.start));

                for (let i = 1; i < items.length; i++) {
                    if (items[i].start < items[i - 1].end) {
                        event.preventDefault();

                        alert(
                            `Jadwal hari ${day} bertabrakan antara ` +
                            `${items[i - 1].start}–${items[i - 1].end} dan ` +
                            `${items[i].start}–${items[i].end}.`
                        );

                        items[i].element.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });

                        return;
                    }
                }
            }
        });

        /* ------------------------------------------
           INITIALIZATION
        ------------------------------------------ */

        sortDays();
        updateSummary();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNovaTimetable);
    } else {
        initNovaTimetable();
    }

    document.addEventListener('spa:page-loaded', initNovaTimetable);

})();
