
document.addEventListener('DOMContentLoaded', () => {

    const config = window.PAYROLL_CONFIG || {};

    const tableBody = document.getElementById('payrollTableBody');
    const searchInput = document.getElementById('payrollSearch');
    const filterStatus = document.getElementById('filterStatus');
    const filterPeriode = document.getElementById('filterPeriode');

    const modal = document.getElementById('salaryModal');
    const form = document.getElementById('salaryForm');

    const saveButton = document.getElementById('salarySaveBtn');
    const komponenJson = document.getElementById('komponenJson');

    const penerimaanList = document.getElementById('penerimaanList');
    const potonganList = document.getElementById('potonganList');

    const addPenerimaanBtn = document.getElementById('addPenerimaanBtn');
    const addPotonganBtn = document.getElementById('addPotonganBtn');

    const summaryPenerimaan = document.getElementById('summaryPenerimaan');
    const summaryPotongan = document.getElementById('summaryPotongan');
    const summaryBersih = document.getElementById('summaryBersih');
    const salaryWarning = document.getElementById('salaryWarning');

    let activeTrigger = null;
    let toastTimer = null;
    let readOnlyMode = false;
    let originalSaveButtonHTML = saveButton.innerHTML;

    // =====================================================
    // FORMAT RUPIAH
    // =====================================================

    function formatRupiah(value) {
        return new Intl.NumberFormat('id-ID', {
            maximumFractionDigits: 0
        }).format(value || 0);
    }

    // Membaca nominal dari input yang menggunakan format Indonesia.
    // Contoh: 500.000 menjadi 500000.
    function parseNominal(value) {
        const cleaned = String(value || '').replace(/[^\d]/g, '');
        return Number(cleaned) || 0;
    }


    // Membaca nominal dari database/API.
    // Contoh: "500000.00" tetap menjadi 500000,
    // bukan 50000000.
    function parseDatabaseNominal(value) {
        if (value === null || value === undefined || value === '') {
            return 0;
        }

        const nominal = Number(String(value).replace(',', '.'));

        return Number.isFinite(nominal)
            ? Math.round(nominal)
            : 0;
    }

    function formatInput(input) {
        const value = parseNominal(input.value);

        input.value = value ? formatRupiah(value) : '';

        return value;
    }

    // =====================================================
    // TOAST
    // =====================================================

    function showToast(title, message, type = 'success') {

        const toast = document.getElementById('payrollToast');
        const titleEl = document.getElementById('toastTitle');
        const messageEl = document.getElementById('toastMessage');
        const icon = toast.querySelector('.toast-icon i');

        titleEl.textContent = title;
        messageEl.textContent = message;

        toast.classList.remove('show', 'toast-error');

        if (type === 'error') {
            toast.classList.add('toast-error');
            icon.className = 'fas fa-circle-exclamation';
        } else {
            icon.className = 'fas fa-circle-check';
        }

        requestAnimationFrame(() => toast.classList.add('show'));

        clearTimeout(toastTimer);

        toastTimer = setTimeout(() => {
            toast.classList.remove('show');
        }, 3500);
    }

    // =====================================================
    // FILTER TABEL
    // =====================================================

    function filterTable() {

        if (!tableBody) return;

        const keyword = (searchInput?.value || '').toLowerCase().trim();
        const status = (filterStatus?.value || '').toLowerCase();

        const rows = tableBody.querySelectorAll('.payroll-row');

        let visible = 0;

        rows.forEach(row => {

            const nama = (row.dataset.nama || '').toLowerCase();
            const nip = (row.dataset.nip || '').toLowerCase();
            const rowStatus = (row.dataset.status || '').toLowerCase();

            const matchKeyword =
                nama.includes(keyword) || nip.includes(keyword);

            const matchStatus =
                !status || rowStatus === status;

            const show = matchKeyword && matchStatus;

            row.hidden = !show;

            if (show) visible++;
        });

        let empty = document.getElementById('payrollNoResult');

        if (!empty && rows.length) {

            empty = document.createElement('tr');
            empty.id = 'payrollNoResult';

            empty.innerHTML = `
                <td colspan="8">
                    <div class="table-empty">
                        <div class="empty-illustration">
                            <i class="fas fa-magnifying-glass"></i>
                        </div>
                        <h3>Data Tidak Ditemukan</h3>
                        <p>Coba gunakan kata kunci atau filter yang berbeda.</p>
                    </div>
                </td>
            `;

            tableBody.appendChild(empty);
        }

        if (empty) {
            empty.hidden = visible !== 0 || rows.length === 0;
        }

        const count = document.getElementById('payrollVisibleCount');

        if (count) {
            count.textContent = visible;
        }
    }

    searchInput?.addEventListener('input', filterTable);
    filterStatus?.addEventListener('change', filterTable);

    // =====================================================
    // FILTER PERIODE
    // =====================================================

    filterPeriode?.addEventListener('change', function () {

        const value = this.value;

        if (!value) return;

        const parts = value.split('-');

        if (parts.length !== 2) return;

        const year = Number(parts[0]);
        const month = Number(parts[1]);

        if (!year || month < 1 || month > 12) return;

        const url = new URL(window.location.href);

        url.searchParams.set('tahun', year);
        url.searchParams.set('bulan', month);

        window.location.href = url.toString();
    });

    // =====================================================
    // MODAL
    // =====================================================

    function openModal() {

        modal.classList.add('show');

        modal.setAttribute('aria-hidden', 'false');

        document.body.classList.add('payroll-modal-open');
    }

    function closeModal() {

        modal.classList.remove('show');

        modal.setAttribute('aria-hidden', 'true');

        document.body.classList.remove('payroll-modal-open');

        modal.querySelector('.salary-modal-dialog')
            .classList.remove('salary-readonly');

        if (activeTrigger) {
            activeTrigger.focus();
            activeTrigger = null;
        }
    }

    modal?.querySelectorAll('[data-close-modal]').forEach(button => {

        button.addEventListener('click', closeModal);

    });

    document.addEventListener('keydown', event => {

        if (
            event.key === 'Escape' &&
            modal.classList.contains('show')
        ) {
            closeModal();
        }

    });

    // =====================================================
    // BUAT ITEM KOMPONEN
    // =====================================================

    function createComponentItem(jenis, data = {}) {

        const row = document.createElement('div');

        row.className = 'salary-dynamic-item';

        row.dataset.jenis = jenis;

        const nameField = document.createElement('label');

        nameField.className =
            'salary-dynamic-field salary-dynamic-field-name';

        const nameLabel = document.createElement('span');

        nameLabel.textContent = 'Nama Komponen';

        const nameInput = document.createElement('input');

        nameInput.type = 'text';

        nameInput.className = 'salary-component-name';

        nameInput.maxLength = 120;

        nameInput.placeholder = jenis === 'penerimaan'
            ? 'Contoh: Gaji Pokok'
            : 'Contoh: Potongan Kasbon';

        nameInput.value = data.nama_item || '';

        nameInput.autocomplete = 'off';

        nameInput.required = true;

        nameField.append(nameLabel, nameInput);

        const moneyField = document.createElement('label');

        moneyField.className =
            'salary-dynamic-field salary-dynamic-field-money';

        const moneyLabel = document.createElement('span');

        moneyLabel.textContent = 'Nominal';

        const moneyWrap = document.createElement('div');

        moneyWrap.className = 'salary-dynamic-money';

        const currency = document.createElement('span');

        currency.textContent = 'Rp';

        const moneyInput = document.createElement('input');

        moneyInput.type = 'text';

        moneyInput.className = 'salary-component-nominal';

        moneyInput.inputMode = 'numeric';

        moneyInput.placeholder = '0';

        const nominalDatabase = parseDatabaseNominal(data.nominal);

        moneyInput.value = nominalDatabase > 0
            ? formatRupiah(nominalDatabase)
            : '';

        moneyInput.autocomplete = 'off';

        moneyInput.required = true;

        moneyWrap.append(currency, moneyInput);

        moneyField.append(moneyLabel, moneyWrap);

        const removeButton = document.createElement('button');

        removeButton.type = 'button';

        removeButton.className = 'salary-remove-item-btn';

        removeButton.title = 'Hapus komponen';

        removeButton.setAttribute(
            'aria-label',
            'Hapus komponen ' + (data.nama_item || '')
        );

        removeButton.innerHTML = '<i class="fas fa-trash-can"></i>';

        removeButton.addEventListener('click', () => {

            row.remove();

            updateSummary();

        });

        moneyInput.addEventListener('input', () => {

            formatInput(moneyInput);

            updateSummary();

        });

        moneyInput.addEventListener('focus', () => {
            moneyInput.select();
        });

        row.append(nameField, moneyField, removeButton);

        if (readOnlyMode) {

            nameInput.readOnly = true;
            moneyInput.readOnly = true;

            removeButton.hidden = true;
        }

        return row;
    }

    // =====================================================
    // TAMBAH ITEM
    // =====================================================

    function addComponent(jenis, data = {}) {

        if (readOnlyMode) return;

        const list = jenis === 'penerimaan'
            ? penerimaanList
            : potonganList;

        const row = createComponentItem(jenis, data);

        list.appendChild(row);

        updateSummary();

        row.querySelector('.salary-component-name')?.focus();
    }

    addPenerimaanBtn.addEventListener('click', () => {

        addComponent('penerimaan');

    });

    addPotonganBtn.addEventListener('click', () => {

        addComponent('potongan');

    });

    // =====================================================
    // KUMPULKAN KOMPONEN
    // =====================================================

    function collectComponents() {

        const komponen = [];

        const rows = form.querySelectorAll(
            '.salary-dynamic-item'
        );

        rows.forEach((row, index) => {

            const namaInput = row.querySelector(
                '.salary-component-name'
            );

            const nominalInput = row.querySelector(
                '.salary-component-nominal'
            );

            const namaItem = namaInput.value.trim();

            const nominal = parseNominal(
                nominalInput.value
            );

            komponen.push({

                jenis: row.dataset.jenis,

                nama_item: namaItem,

                nominal: String(nominal),

                urutan: index

            });

        });

        return komponen;
    }

    // =====================================================
    // RINGKASAN
    // =====================================================

    function updateSummary() {

        const komponen = collectComponents();

        let penerimaan = 0;
        let potongan = 0;

        komponen.forEach(item => {

            const nominal = parseNominal(item.nominal);

            if (item.jenis === 'penerimaan') {

                penerimaan += nominal;

            } else if (item.jenis === 'potongan') {

                potongan += nominal;

            }

        });

        const bersih = penerimaan - potongan;

        summaryPenerimaan.textContent =
            'Rp ' + formatRupiah(penerimaan);

        summaryPotongan.textContent =
            'Rp ' + formatRupiah(potongan);

        summaryBersih.textContent =
            'Rp ' + formatRupiah(Math.max(0, bersih));

        salaryWarning.hidden = bersih >= 0;

        saveButton.disabled =
            readOnlyMode || bersih < 0;

        return {
            penerimaan,
            potongan,
            bersih
        };
    }

    // =====================================================
    // RESET FORM
    // =====================================================

    function resetSalaryForm() {

        form.reset();

        penerimaanList.innerHTML = '';
        potonganList.innerHTML = '';

        komponenJson.value = '';

        readOnlyMode = false;

        modal.querySelector('.salary-modal-dialog')
            .classList.remove('salary-readonly');

        addPenerimaanBtn.disabled = false;
        addPotonganBtn.disabled = false;

        addPenerimaanBtn.hidden = false;
        addPotonganBtn.hidden = false;

        saveButton.hidden = false;

        saveButton.disabled = false;

        saveButton.innerHTML = originalSaveButtonHTML;

        salaryWarning.hidden = true;

        updateSummary();
    }

    // =====================================================
    // LOAD KOMPONEN DARI API
    // =====================================================

    function loadComponents(salary) {

        penerimaanList.innerHTML = '';
        potonganList.innerHTML = '';

        const komponen = Array.isArray(salary.komponen)
            ? salary.komponen
            : [];

        komponen.forEach(item => {

            const jenis = item.jenis;

            if (
                jenis !== 'penerimaan' &&
                jenis !== 'potongan'
            ) {
                return;
            }

            const list = jenis === 'penerimaan'
                ? penerimaanList
                : potonganList;

            list.appendChild(
                createComponentItem(jenis, item)
            );

        });

        updateSummary();
    }

    // =====================================================
    // LOAD DATA GURU
    // =====================================================

    async function loadTeacherSalary(guruId, readOnly = false) {

        resetSalaryForm();

        document.getElementById('salaryGuruId').value = guruId;

        const nameEl = document.getElementById('modalTeacherName');
        const nipEl = document.getElementById('modalTeacherNip');
        const avatarEl = document.getElementById('modalTeacherAvatar');

        nameEl.textContent = 'Memuat data guru...';
        nipEl.textContent = 'Mohon tunggu';
        avatarEl.textContent = '...';

        openModal();

        try {

            const endpoint = config.dataUrl.replace(
                '__GURU_ID__',
                encodeURIComponent(guruId)
            );

            const url = new URL(
                endpoint,
                window.location.origin
            );

            url.searchParams.set('bulan', config.bulan);
            url.searchParams.set('tahun', config.tahun);

            const response = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (!response.ok || !result.success) {

                throw new Error(
                    result.message || 'Gagal mengambil data guru.'
                );

            }

            nameEl.textContent = result.guru.nama;

            nipEl.textContent =
                result.guru.nip || 'NIP belum tersedia';

            avatarEl.textContent =
                result.guru.nama.charAt(0).toUpperCase();

            const salary = result.gaji || {};

            // Muat komponen dinamis
            loadComponents(salary);

            readOnlyMode = Boolean(readOnly);

            const title = document.getElementById(
                'salaryModalTitle'
            );

            const dialog = modal.querySelector(
                '.salary-modal-dialog'
            );

            if (readOnlyMode) {

                title.textContent = 'Lihat Rincian Gaji';

                dialog.classList.add('salary-readonly');

                addPenerimaanBtn.hidden = true;
                addPotonganBtn.hidden = true;

                saveButton.hidden = true;

                form.querySelectorAll(
                    '.salary-component-name, .salary-component-nominal'
                ).forEach(input => {

                    input.readOnly = true;

                });

                form.querySelectorAll(
                    '.salary-remove-item-btn'
                ).forEach(button => {

                    button.hidden = true;

                });

            } else {

                title.textContent = 'Atur Rincian Gaji';

                dialog.classList.remove('salary-readonly');

                addPenerimaanBtn.hidden = false;
                addPotonganBtn.hidden = false;

                saveButton.hidden = false;

            }

            updateSummary();

        } catch (error) {

            console.error(error);

            closeModal();

            showToast(
                'Gagal memuat data',
                error.message,
                'error'
            );

        }
    }

    // =====================================================
    // TOMBOL AKSI TABEL
    // =====================================================

    tableBody?.addEventListener('click', event => {

        const editButton = event.target.closest(
            '.btn-edit-salary'
        );

        const viewButton = event.target.closest(
            '.btn-view-salary'
        );

        const button = editButton || viewButton;

        if (!button) return;

        const guruId = button.dataset.guruId;

        if (!guruId) return;

        activeTrigger = button;

        loadTeacherSalary(
            guruId,
            Boolean(viewButton)
        );

    });

    // =====================================================
    // VALIDASI FORM
    // =====================================================

    form.addEventListener('submit', event => {

        if (readOnlyMode) {

            event.preventDefault();

            return;
        }

        const komponen = collectComponents();

        const totals = updateSummary();

        if (!document.getElementById('salaryGuruId').value) {

            event.preventDefault();

            showToast(
                'Data belum lengkap',
                'Guru belum dipilih.',
                'error'
            );

            return;
        }

        if (totals.potongan > totals.penerimaan) {

            event.preventDefault();

            showToast(
                'Periksa nominal',
                'Total potongan tidak boleh melebihi total penerimaan.',
                'error'
            );

            return;
        }

        // Nama item wajib diisi
        const namaKosong = komponen.some(item => {
            return !item.nama_item.trim();
        });

        if (namaKosong) {

            event.preventDefault();

            showToast(
                'Nama komponen belum diisi',
                'Silakan isi nama setiap komponen.',
                'error'
            );

            return;
        }

        // Pastikan nominal valid dan tidak negatif
        const nominalInvalid = komponen.some(item => {

            const nominal = Number(item.nominal);

            return !Number.isFinite(nominal) || nominal < 0;

        });

        if (nominalInvalid) {

            event.preventDefault();

            showToast(
                'Nominal tidak valid',
                'Periksa kembali nominal komponen.',
                'error'
            );

            return;
        }

        // Kirim daftar komponen ke backend
        komponenJson.value = JSON.stringify(komponen);

        saveButton.disabled = true;

        saveButton.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';

    });

    // =====================================================
    // INIT
    // =====================================================

    filterTable();

});
