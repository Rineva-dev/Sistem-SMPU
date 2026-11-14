
/* =========================================================
   PREMIUM CLASSROOM WORKSPACE
   Detail Kelas • Student Management
========================================================= */

(() => {
    'use strict';

    function initClassroomPage() {
        const app = document.getElementById('classroomApp');
        if (!app || app.dataset.crInitialized === '1') return;
        app.dataset.crInitialized = '1';

        /* -----------------------------------------
           DIRECTORY SEARCH
        ----------------------------------------- */
        const searchInput = document.getElementById('crSearchStudent');
        const studentRows = [...document.querySelectorAll('.cr-student-row')];
        const visibleCount = document.getElementById('crVisibleCount');
        const noResult = document.getElementById('crNoSearchResult');

        function filterDirectory() {
            const keyword = (searchInput?.value || '').trim().toLowerCase();
            let visible = 0;

            studentRows.forEach(row => {
                const match = row.textContent.toLowerCase().includes(keyword);
                row.hidden = !match;
                if (match) visible++;
            });

            if (visibleCount) visibleCount.textContent = visible;
            if (noResult) noResult.hidden = visible !== 0 || studentRows.length === 0;
        }

        searchInput?.addEventListener('input', filterDirectory);

        /* -----------------------------------------
           HELPERS
        ----------------------------------------- */
        const $ = (id) => document.getElementById(id);

        const modalElement = $('modalKelolaSiswa');
        const form = $('formKelolaSiswa');

        if (!modalElement || !form) return;

        let adaPerubahan = false;
        let allowModalClose = false;
        let availableStudents = [];
        let memberStudents = [];

        const makeStudent = (id, nis, nama, origin) => ({
            id: String(id),
            nis: String(nis || '-'),
            nama: String(nama || 'Tanpa Nama'),
            origin
        });

        function readSource(containerId, origin) {
            const container = $(containerId);
            if (!container) return [];

            return [...container.querySelectorAll('.item-asli')].map(el =>
                makeStudent(
                    el.dataset.id,
                    el.dataset.nis,
                    el.dataset.nama,
                    origin
                )
            );
        }

        function escapeText(value) {
            return String(value ?? '');
        }

        function createTransferItem(student, side) {
            const label = document.createElement('label');
            label.className = 'cr-transfer-item';
            label.dataset.id = student.id;

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = side === 'available' ? 'belum-check' : 'sudah-check';
            checkbox.value = student.id;

            const customCheck = document.createElement('span');
            customCheck.className = 'cr-custom-check';

            const avatar = document.createElement('span');
            avatar.className = 'cr-transfer-avatar';
            avatar.textContent = escapeText(student.nama).trim().charAt(0).toUpperCase() || '?';

            const textWrap = document.createElement('span');
            textWrap.className = 'cr-transfer-text';

            const name = document.createElement('strong');
            name.textContent = student.nama;

            const nis = document.createElement('small');
            nis.textContent = `NIS: ${student.nis}`;

            textWrap.append(name, nis);
            label.append(checkbox, customCheck, avatar, textWrap);

            checkbox.addEventListener('change', updateTransferSummary);
            return label;
        }

        function renderTransferList(side) {
            const isAvailable = side === 'available';
            const container = $(isAvailable ? 'daftarBelum' : 'daftarSudah');
            const students = isAvailable ? availableStudents : memberStudents;

            if (!container) return;

            container.replaceChildren();

            if (!students.length) {
                const empty = document.createElement('div');
                empty.className = 'cr-list-empty';

                const icon = document.createElement('i');
                icon.className = isAvailable ? 'fas fa-user-check' : 'fas fa-users';

                const message = document.createElement('span');
                message.textContent = isAvailable
                    ? 'Semua siswa yang tersedia sudah ditambahkan'
                    : 'Belum ada anggota kelas';

                empty.append(icon, message);
                container.appendChild(empty);
            } else {
                const fragment = document.createDocumentFragment();
                students.forEach(student => fragment.appendChild(createTransferItem(student, side)));
                container.appendChild(fragment);
            }

            updateTransferSummary();
            applyTransferSearch(side);
        }

        function updateTransferSummary() {
            const availableCount = $('crAvailableCount');
            const memberCount = $('crMemberCount');
            const availableSelected = $('crAvailableSelected');
            const memberSelected = $('crMemberSelected');

            const selectedAvailable = document.querySelectorAll('#daftarBelum .belum-check:checked').length;
            const selectedMember = document.querySelectorAll('#daftarSudah .sudah-check:checked').length;

            if (availableCount) availableCount.textContent = availableStudents.length;
            if (memberCount) memberCount.textContent = memberStudents.length;
            if (availableSelected) availableSelected.textContent = `${selectedAvailable} dipilih`;
            if (memberSelected) memberSelected.textContent = `${selectedMember} dipilih`;

            const additions = memberStudents.filter(s => s.origin === 'available').length;
            const removals = availableStudents.filter(s => s.origin === 'member').length;

            adaPerubahan = additions > 0 || removals > 0;

            const indicator = $('crChangeIndicator');
            if (indicator) {
                indicator.classList.toggle('has-changes', adaPerubahan);
                indicator.innerHTML = adaPerubahan
                    ? `<i class="fas fa-arrows-left-right"></i> ${additions} ditambahkan • ${removals} dikeluarkan`
                    : `<i class="fas fa-check-circle"></i> Belum ada perubahan`;
            }

            const saveButton = $('tombolSimpan');
            if (saveButton) saveButton.disabled = !adaPerubahan;
        }

        function applyTransferSearch(side) {
            const isAvailable = side === 'available';
            const input = $(isAvailable ? 'cariBelum' : 'cariSudah');
            const container = $(isAvailable ? 'daftarBelum' : 'daftarSudah');
            if (!input || !container) return;

            const query = input.value.trim().toLowerCase();
            container.querySelectorAll('.cr-transfer-item').forEach(item => {
                item.hidden = !item.textContent.toLowerCase().includes(query);
            });

            const selectAll = $(isAvailable ? 'pilihSemuaBelum' : 'pilihSemuaSudah');
            if (selectAll) selectAll.checked = false;
        }

        function setSelectAll(side, checked) {
            const selector = side === 'available'
                ? '#daftarBelum .belum-check'
                : '#daftarSudah .sudah-check';

            const search = $(side === 'available' ? 'cariBelum' : 'cariSudah');
            const query = (search?.value || '').trim().toLowerCase();

            document.querySelectorAll(selector).forEach(checkbox => {
                const item = checkbox.closest('.cr-transfer-item');
                if (!item || item.hidden) return;
                if (query && !item.textContent.toLowerCase().includes(query)) return;
                checkbox.checked = checked;
            });

            updateTransferSummary();
        }

        function resetTransferWorkspace() {
            availableStudents = readSource('dataAsliBelum', 'available');
            memberStudents = readSource('dataAsliSudah', 'member');

            $('cariBelum').value = '';
            $('cariSudah').value = '';
            $('pilihSemuaBelum').checked = false;
            $('pilihSemuaSudah').checked = false;

            renderTransferList('available');
            renderTransferList('member');
            updateTransferSummary();
        }

        /* -----------------------------------------
           MODAL OPEN
        ----------------------------------------- */
        modalElement.addEventListener('show.bs.modal', resetTransferWorkspace);

        /* -----------------------------------------
           SEARCH TRANSFER PANELS
        ----------------------------------------- */
        $('cariBelum')?.addEventListener('input', () => applyTransferSearch('available'));
        $('cariSudah')?.addEventListener('input', () => applyTransferSearch('member'));

        /* -----------------------------------------
           SELECT ALL
        ----------------------------------------- */
        $('pilihSemuaBelum')?.addEventListener('change', function () {
            setSelectAll('available', this.checked);
        });

        $('pilihSemuaSudah')?.addEventListener('change', function () {
            setSelectAll('member', this.checked);
        });

        /* -----------------------------------------
           MOVE STUDENTS
        ----------------------------------------- */
        $('btnMasukkan')?.addEventListener('click', () => {
            const selectedIds = new Set(
                [...document.querySelectorAll('#daftarBelum .belum-check:checked')]
                    .map(input => String(input.value))
            );

            if (!selectedIds.size) {
                alert('Pilih minimal satu siswa yang akan dimasukkan.');
                return;
            }

            const moved = availableStudents.filter(student => selectedIds.has(student.id));
            availableStudents = availableStudents.filter(student => !selectedIds.has(student.id));
            memberStudents.push(...moved);

            $('pilihSemuaBelum').checked = false;
            $('pilihSemuaSudah').checked = false;

            renderTransferList('available');
            renderTransferList('member');
        });

        $('btnKeluarkan')?.addEventListener('click', () => {
            const selectedIds = new Set(
                [...document.querySelectorAll('#daftarSudah .sudah-check:checked')]
                    .map(input => String(input.value))
            );

            if (!selectedIds.size) {
                alert('Pilih minimal satu siswa yang akan dikeluarkan.');
                return;
            }

            const moved = memberStudents.filter(student => selectedIds.has(student.id));
            memberStudents = memberStudents.filter(student => !selectedIds.has(student.id));
            availableStudents.push(...moved);

            $('pilihSemuaBelum').checked = false;
            $('pilihSemuaSudah').checked = false;

            renderTransferList('available');
            renderTransferList('member');
        });

        /* -----------------------------------------
           BUILD POST PAYLOAD
           Compare final position with original position.
           This prevents false add/remove when moved back.
        ----------------------------------------- */
        form.addEventListener('submit', event => {
            const additions = memberStudents.filter(student => student.origin === 'available');
            const removals = availableStudents.filter(student => student.origin === 'member');

            if (!additions.length && !removals.length) {
                event.preventDefault();
                alert('Tidak ada perubahan yang perlu disimpan.');
                return;
            }

            const confirmation = confirm(
                `Simpan perubahan anggota kelas?\n\n` +
                `• Masukkan: ${additions.length} siswa\n` +
                `• Keluarkan: ${removals.length} siswa\n\n` +
                `Pastikan data sudah benar.`
            );

            if (!confirmation) {
                event.preventDefault();
                return;
            }

            // Remove old generated fields if any.
            form.querySelectorAll('.cr-generated-field').forEach(el => el.remove());

            additions.forEach(student => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'tambah_id';
                input.value = student.id;
                input.className = 'cr-generated-field';
                form.appendChild(input);
            });

            removals.forEach(student => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'keluarkan_id';
                input.value = student.id;
                input.className = 'cr-generated-field';
                form.appendChild(input);
            });

            adaPerubahan = false;
        });

        /* -----------------------------------------
           CLOSE / CANCEL WITH UNSAVED WARNING
        ----------------------------------------- */
        function closeTransferModal() {
            if (adaPerubahan && !confirm('Perubahan belum disimpan. Yakin ingin menutup modal?')) {
                return;
            }

            allowModalClose = true;
            bootstrap.Modal.getOrCreateInstance(modalElement).hide();
        }

        modalElement.addEventListener('hide.bs.modal', event => {
            if (adaPerubahan && !allowModalClose) {
                event.preventDefault();

                if (confirm('Perubahan belum disimpan. Yakin ingin menutup modal?')) {
                    allowModalClose = true;
                    bootstrap.Modal.getOrCreateInstance(modalElement).hide();
                }
            }
        });

        modalElement.addEventListener('hidden.bs.modal', () => {
            allowModalClose = false;
            adaPerubahan = false;
        });

        $('tombolTutupModal')?.addEventListener('click', closeTransferModal);
        $('tombolBatal')?.addEventListener('click', closeTransferModal);

        /* -----------------------------------------
           SELECT ALL: SEMESTER / PROMOTION
        ----------------------------------------- */
        function bindSelectAll(masterId, itemSelector) {
            const master = $(masterId);
            if (!master) return;

            const items = () => [...document.querySelectorAll(itemSelector)];

            master.addEventListener('change', function () {
                items().forEach(item => {
                    item.checked = this.checked;
                });
            });

            items().forEach(item => {
                item.addEventListener('change', () => {
                    const all = items();
                    master.checked = all.length > 0 && all.every(cb => cb.checked);
                    master.indeterminate = all.some(cb => cb.checked) && !master.checked;
                });
            });
        }

        bindSelectAll('pilihSemuaLanjut', '.lanjut-check');
        bindSelectAll('pilihSemuaNaik', '.naik-check');

        /* -----------------------------------------
           PROCESS FORM CONFIRMATION
        ----------------------------------------- */
        $('modalLanjutkan')?.querySelector('form')?.addEventListener('submit', event => {
            const count = document.querySelectorAll('.lanjut-check:checked').length;
            if (!count) {
                event.preventDefault();
                alert('Pilih minimal satu siswa untuk dilanjutkan.');
                return;
            }
            if (!confirm(`Lanjutkan ${count} siswa ke semester Genap?`)) {
                event.preventDefault();
            }
        });

        $('modalNaikKelas')?.querySelector('form')?.addEventListener('submit', event => {
            const count = document.querySelectorAll('.naik-check:checked').length;
            if (!count) {
                event.preventDefault();
                alert('Pilih minimal satu siswa untuk diproses naik kelas.');
                return;
            }
            if (!confirm(`Proses kenaikan kelas untuk ${count} siswa?`)) {
                event.preventDefault();
            }
        });

        /* -----------------------------------------
           SUBJECT TABLE: LIVE JP STATUS
        ----------------------------------------- */
        document.querySelectorAll('.cr-jp-input').forEach(input => {
            const update = () => {
                const row = input.closest('.cr-subject-row');
                if (!row) return;
                row.classList.toggle('cr-subject-disabled', Number(input.value) <= 0);
            };

            input.addEventListener('input', update);
            update();
        });
    }

    // Normal page load.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initClassroomPage, { once: true });
    } else {
        initClassroomPage();
    }

    // SPA navigation support.
    document.addEventListener('spa:page-loaded', initClassroomPage);
})();
