
document.addEventListener('DOMContentLoaded', () => {

    const config = window.PAYROLL_CONFIG || {};

    const tableBody = document.getElementById('payrollTableBody');
    const searchInput = document.getElementById('payrollSearch');
    const filterStatus = document.getElementById('filterStatus');

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

        toast.classList.remove('show', 'toast-error', 'toast-warning');

        if (type === 'error') {
            toast.classList.add('toast-error');
            icon.className = 'fas fa-circle-exclamation';

        } else if (type === 'warning') {
            toast.classList.add('toast-warning');
            icon.className = 'fas fa-triangle-exclamation';

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
                <td colspan="9">
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

        updatePublishSelection();
    }

    searchInput?.addEventListener('input', filterTable);
    filterStatus?.addEventListener('change', filterTable);

    
    // =====================================================
    // AJAX — RELOAD TABEL TANPA RELOAD HALAMAN
    // =====================================================

    let tableLoading = false;

    const archiveList = document.querySelector(
        '.archive-period-list'
    );

    const archiveNavigation = document.querySelector(
        '.payroll-archive-navigation'
    );

    const monthNames = [
        'Januari', 'Februari', 'Maret', 'April',
        'Mei', 'Juni', 'Juli', 'Agustus',
        'September', 'Oktober', 'November', 'Desember'
    ];

    function createPeriodUrl(bulan, tahun) {

        const url = new URL(window.location.href);

        url.searchParams.set('bulan', bulan);
        url.searchParams.set('tahun', tahun);

        url.searchParams.set('akhir_bulan', bulan);
        url.searchParams.set('akhir_tahun', tahun);

        return url;
    }

    function updateArchiveNavigation(bulan, tahun) {

        if (!archiveList || !archiveNavigation) return;

        const indeksAkhir = tahun * 12 + bulan - 1;

        const indeksSekarang =
            config.tahunSekarang * 12 +
            config.bulanSekarang - 1;

        const indeksAwal = indeksAkhir - 4;

        // Perbarui lima tombol periode
        archiveList.innerHTML = '';

        for (
            let indeks = indeksAwal;
            indeks <= indeksAkhir;
            indeks++
        ) {

            const tahunItem = Math.floor(indeks / 12);

            const bulanItem = (indeks % 12) + 1;

            const link = document.createElement('a');

            link.href = createPeriodUrl(
                bulanItem,
                tahunItem
            ).toString();

            link.className = 'archive-period-item';

            const monthLabel = document.createElement('span');

            monthLabel.className = 'archive-period-month';

            monthLabel.textContent =
                monthNames[bulanItem - 1] + ' ' + tahunItem;

            link.appendChild(monthLabel);

            // Periode yang sedang dipilih menjadi aktif
            if (indeks === indeksAkhir) {

                link.classList.add('active');

                const icon = document.createElement('i');

                icon.className = 'fas fa-circle-check';

                link.appendChild(icon);
            }

            archiveList.appendChild(link);
        }

        // Perbarui tombol Lebih Lama dan Lebih Baru
        const navButtons = archiveNavigation.querySelectorAll(
            '.archive-nav-btn'
        );

        const tombolLama = navButtons[0];
        const tombolBaru = navButtons[navButtons.length - 1];

        const indeksLama = indeksAkhir - 5;

        const indeksBaru = Math.min(
            indeksAkhir + 5,
            indeksSekarang
        );

        if (tombolLama) {

            const bulanLama = (indeksLama % 12) + 1;

            const tahunLama = Math.floor(indeksLama / 12);

            tombolLama.href = createPeriodUrl(
                bulanLama,
                tahunLama
            ).toString();

        }

        if (tombolBaru) {

            const bulanBaru = (indeksBaru % 12) + 1;

            const tahunBaru = Math.floor(indeksBaru / 12);

            tombolBaru.href = createPeriodUrl(
                bulanBaru,
                tahunBaru
            ).toString();

            const disabled = indeksAkhir >= indeksSekarang;

            tombolBaru.classList.toggle(
                'disabled',
                disabled
            );

            if (disabled) {

                tombolBaru.setAttribute(
                    'aria-disabled',
                    'true'
                );

                tombolBaru.setAttribute(
                    'tabindex',
                    '-1'
                );

            } else {

                tombolBaru.removeAttribute('aria-disabled');

                tombolBaru.removeAttribute('tabindex');

            }
        }
    }

    async function loadPeriod(bulan, tahun, updateUrl = true) {

        if (tableLoading) return;

        tableLoading = true;

        const tableContainer = document.querySelector(
            '.payroll-table-container'
        );

        tableContainer?.classList.add('table-loading');

        try {

            const url = new URL(
                config.tableUrl,
                window.location.origin
            );

            url.searchParams.set('bulan', bulan);
            url.searchParams.set('tahun', tahun);

            
            const response = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Gagal memuat data penggajian.');
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || 'Gagal memuat data.');
            }

            // Perbarui tabel
            tableBody.innerHTML = result.html;

            // Reset pilihan checkbox periode sebelumnya
            if (selectAllPayroll) {
                selectAllPayroll.checked = false;
                selectAllPayroll.indeterminate = false;
            }

            // Perbarui statistik
            const statistik = result.statistik;

            const formatRupiah = new Intl.NumberFormat('id-ID', {
                maximumFractionDigits: 0
            });

            document.getElementById('statTotalGuru').textContent =
                statistik.total_guru;

            document.getElementById('statTotalPenggajian').textContent =
                formatRupiah.format(statistik.total_penggajian);

            document.getElementById('statTotalDraft').textContent =
                statistik.total_draft;

            document.getElementById('statTotalTerbit').textContent =
                statistik.total_terbit;

            // Perbarui progress bar
            const totalGuru = statistik.total_guru;

            document.getElementById('statProgressDraft').style.width =
                `${totalGuru ? (statistik.total_draft / totalGuru) * 100 : 0}%`;

            document.getElementById('statProgressTerbit').style.width =
                `${totalGuru ? (statistik.total_terbit / totalGuru) * 100 : 0}%`;


            // Perbarui periode aktif
            config.bulan = bulan;
            config.tahun = tahun;

            // Perbarui label periode pada workspace
            const periodLabel = document.getElementById(
                'workspacePeriodLabel'
            );

            if (periodLabel) {
                periodLabel.textContent =
                    monthNames[bulan - 1] + ' ' + tahun;
            }

            // Perbarui tampilan arsip lima bulan
            updateArchiveNavigation(bulan, tahun);

            // Terapkan kembali pencarian dan filter
            filterTable();

            // Perbarui URL tanpa reload halaman
            if (updateUrl) {

                const pageUrl = createPeriodUrl(
                    bulan,
                    tahun
                );

                window.history.pushState(
                    {
                        bulan,
                        tahun
                    },
                    '',
                    pageUrl.toString()
                );
            }

        } catch (error) {

            console.error(error);

            showToast(
                'Gagal memuat tabel',
                error.message,
                'error'
            );

        } finally {

            tableLoading = false;

            tableContainer?.classList.remove('table-loading');

        }
    }

    // =====================================================
    // KLIK NAVIGASI ARSIP
    // =====================================================

    archiveNavigation?.addEventListener('click', event => {

        const link = event.target.closest(
            '.archive-period-item, .archive-nav-btn'
        );

        if (!link) return;

        if (
            link.classList.contains('disabled') ||
            link.getAttribute('aria-disabled') === 'true'
        ) {
            event.preventDefault();
            return;
        }

        event.preventDefault();

        const url = new URL(
            link.href,
            window.location.origin
        );

        const bulan = Number(
            url.searchParams.get('bulan')
        );

        const tahun = Number(
            url.searchParams.get('tahun')
        );

        if (!bulan || !tahun) return;

        loadPeriod(bulan, tahun);
    });

    // =====================================================
    // TOMBOL BULAN BERJALAN
    // =====================================================

    const btnBulanBerjalan = document.getElementById(
        'btnBulanBerjalan'
    );

    btnBulanBerjalan?.addEventListener('click', function () {

        loadPeriod(
            config.bulanSekarang,
            config.tahunSekarang
        );

    });

    // =====================================================
    // BROWSER BACK / FORWARD
    // =====================================================

    window.addEventListener('popstate', () => {

        const url = new URL(window.location.href);

        const bulan = Number(
            url.searchParams.get('bulan')
        );

        const tahun = Number(
            url.searchParams.get('tahun')
        );

        if (bulan && tahun) {

            loadPeriod(bulan, tahun, false);

        }

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

    async function loadTeacherSalary(
        guruId,
        bulan,
        tahun,
        readOnly = false
    ) {

        resetSalaryForm();

        // Simpan identitas guru
        document.getElementById('salaryGuruId').value = guruId;

        // Simpan periode sesuai baris tabel yang diklik
        document.getElementById('salaryBulan').value = bulan;
        document.getElementById('salaryTahun').value = tahun;

        // Perbarui label periode pada modal
        const periodLabel = document.getElementById('modalPeriodLabel');

        if (periodLabel) {
            periodLabel.textContent =
                monthNames[bulan - 1] + ' ' + tahun;
        }

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

            url.searchParams.set('bulan', bulan);
            url.searchParams.set('tahun', tahun);

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

        // Ambil periode dari baris tabel yang diklik
        const row = button.closest('.payroll-row');

        const bulan = Number(
            row?.dataset.bulan || config.bulan
        );

        const tahun = Number(
            row?.dataset.tahun || config.tahun
        );

        if (!bulan || !tahun) {
            showToast(
                'Periode tidak valid',
                'Bulan dan tahun penggajian tidak ditemukan.',
                'error'
            );
            return;
        }

        activeTrigger = button;

        loadTeacherSalary(
            guruId,
            bulan,
            tahun,
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
    // PAYROLL PUBLISHING
    // =====================================================

    const selectAllPayroll = document.getElementById('selectAllPayroll');
    const selectedPayrollCount = document.getElementById('selectedPayrollCount');
    const btnPublishSelected = document.getElementById('btnPublishSelected');
    const btnPublishAll = document.getElementById('btnPublishAll');

    function getSelectedPayrollIds() {
        return Array.from(
            tableBody.querySelectorAll('.row-payroll-checkbox:checked')
        ).map(checkbox => Number(checkbox.value));
    }

    function updatePublishSelection() {

        const checkboxes = Array.from(
            tableBody.querySelectorAll('.row-payroll-checkbox')
        );

        const selected = getSelectedPayrollIds();

        if (selectedPayrollCount) {
            selectedPayrollCount.textContent =
                `${selected.length} slip dipilih`;
        }

        if (btnPublishSelected) {
            btnPublishSelected.disabled = selected.length === 0;
        }

        if (selectAllPayroll) {

            const visibleCheckboxes = checkboxes.filter(checkbox => {
                const row = checkbox.closest('.payroll-row');

                return row && !row.hidden;
            });

            const visibleSelected = visibleCheckboxes.filter(
                checkbox => checkbox.checked
            );

            selectAllPayroll.checked =
                visibleCheckboxes.length > 0 &&
                visibleSelected.length === visibleCheckboxes.length;

            selectAllPayroll.indeterminate =
                visibleSelected.length > 0 &&
                visibleSelected.length < visibleCheckboxes.length;
        }
    }

    // -----------------------------------------------------
    // CSRF TOKEN
    // -----------------------------------------------------

    function getPayrollCsrfToken() {
        return (
            document.querySelector('meta[name="csrf-token"]')?.content ||
            document.querySelector('input[name="csrf_token"]')?.value ||
            ''
        );
    }

    async function payrollPost(url, payload = {}) {
        const headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };

        const csrfToken = getPayrollCsrfToken();

        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch(url, {
            method: 'POST',
            headers,
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.message || 'Permintaan gagal diproses.'
            );
        }

        return result;
    }

    // -----------------------------------------------------
    // PILIH SEMUA DRAFT YANG TERLIHAT
    // -----------------------------------------------------

    if (selectAllPayroll) {
        selectAllPayroll.addEventListener('change', function () {
            const checkboxes = tableBody.querySelectorAll(
                '.row-payroll-checkbox'
            );

            checkboxes.forEach(checkbox => {
                const row = checkbox.closest('.payroll-row');

                if (row && row.style.display !== 'none') {
                    checkbox.checked = this.checked;
                }
            });

            updatePublishSelection();
        });
    }

    // Pilihan checkbox individual
    if (tableBody) {
        tableBody.addEventListener('change', function (event) {
            if (
                event.target.classList.contains(
                    'row-payroll-checkbox'
                )
            ) {
                updatePublishSelection();
            }
        });
    }

    // -----------------------------------------------------
    // TERBITKAN SLIP TERPILIH
    // -----------------------------------------------------

    if (btnPublishSelected) {
        btnPublishSelected.addEventListener('click', async function () {
            const ids = getSelectedPayrollIds();

            if (!ids.length) {
                showToast(
                    'Belum Ada Pilihan',
                    'Pilih minimal satu slip gaji terlebih dahulu.',
                    'warning'
                );
                return;
            }

            const konfirmasi = window.confirm(
                `Terbitkan ${ids.length} slip gaji yang dipilih ` +
                `untuk periode ${config.bulan}/${config.tahun}? ` +
                `Slip yang sudah diterbitkan tidak dapat diedit.`
            );

            if (!konfirmasi) return;

            const tombolAwal = this.innerHTML;

            try {
                this.disabled = true;
                this.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Memproses...';

                const result = await payrollPost(
                    '/bendahara/atur-gaji/terbitkan-terpilih',
                    {
                        gaji_ids: ids,
                        bulan: config.bulan,
                        tahun: config.tahun
                    }
                );

                showToast(
                    'Berhasil',
                    result.message || 'Slip gaji berhasil diterbitkan.',
                    'success'
                );

                await loadPeriod(
                    config.bulan,
                    config.tahun,
                    false
                );

            } catch (error) {
                showToast(
                    'Gagal Menerbitkan',
                    error.message,
                    'error'
                );

            } finally {
                this.innerHTML = tombolAwal;
                updatePublishSelection();
            }
        });
    }

    // -----------------------------------------------------
    // TERBITKAN SEMUA DRAFT
    // -----------------------------------------------------

    if (btnPublishAll) {
        btnPublishAll.addEventListener('click', async function () {
            const konfirmasi = window.confirm(
                `Apakah Anda yakin ingin menerbitkan SEMUA slip ` +
                `Draft pada periode ${config.bulan}/${config.tahun}? ` +
                `Slip yang diterbitkan tidak dapat diedit kembali.`
            );

            if (!konfirmasi) return;

            const tombolAwal = this.innerHTML;

            try {
                this.disabled = true;
                this.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Memproses...';

                const result = await payrollPost(
                    '/bendahara/atur-gaji/terbitkan-semua',
                    {
                        bulan: config.bulan,
                        tahun: config.tahun
                    }
                );

                showToast(
                    'Berhasil',
                    result.message || 'Slip gaji berhasil diterbitkan.',
                    'success'
                );

                await loadPeriod(
                    config.bulan,
                    config.tahun,
                    false
                );

            } catch (error) {
                showToast(
                    'Gagal Menerbitkan',
                    error.message,
                    'error'
                );

            } finally {
                this.disabled = false;
                this.innerHTML = tombolAwal;
            }
        });
    }

    // -----------------------------------------------------
    // TERBITKAN SATU SLIP DARI TABEL
    // -----------------------------------------------------

    if (tableBody) {
        tableBody.addEventListener('click', async function (event) {
            const tombol = event.target.closest(
                '.btn-publish-single'
            );

            if (!tombol) return;

            const gajiId = Number(tombol.dataset.gajiId);

            if (!gajiId) return;

            const konfirmasi = window.confirm(
                'Terbitkan slip gaji guru ini? ' +
                'Slip yang sudah diterbitkan tidak dapat diedit kembali.'
            );

            if (!konfirmasi) return;

            const tombolAwal = tombol.innerHTML;

            try {
                tombol.disabled = true;
                tombol.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i>';

                const result = await payrollPost(
                    `/bendahara/atur-gaji/terbitkan/${gajiId}`,
                    {
                        bulan: config.bulan,
                        tahun: config.tahun
                    }
                );

                showToast(
                    'Berhasil',
                    result.message || 'Slip gaji berhasil diterbitkan.',
                    'success'
                );

                await loadPeriod(
                    config.bulan,
                    config.tahun,
                    false
                );

            } catch (error) {
                tombol.disabled = false;
                tombol.innerHTML = tombolAwal;

                showToast(
                    'Gagal Menerbitkan',
                    error.message,
                    'error'
                );
            }
        });
    }

    // Inisialisasi checkbox
    updatePublishSelection();


    // =====================================================
    // INIT
    // =====================================================

    filterTable();

});
