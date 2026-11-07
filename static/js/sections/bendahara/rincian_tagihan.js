// =====================================================
// RINCIAN TAGIHAN SISWA — SPA INITIALIZATION
// =====================================================
(function () {
    'use strict';

    const PAGE_SELECTOR = '.invoice-admin-page';

    function initInvoiceAdminPage() {

        const root = document.querySelector(PAGE_SELECTOR);

        // Halaman ini tidak sedang aktif
        if (!root) return;

        // Hindari inisialisasi berulang pada halaman yang sama
        if (root.dataset.invoiceInitialized === 'true') return;

        root.dataset.invoiceInitialized = 'true';

        // =====================================================
        // INVOICE TABS
        // =====================================================

        const invoiceTabButtons = document.querySelectorAll('.invoice-tab-btn');
        const invoiceTabPanes = document.querySelectorAll('.invoice-tab-pane');

        invoiceTabButtons.forEach(button => {

            button.addEventListener('click', function () {

                const targetTab = this.dataset.tab;

                // Hapus status aktif dari seluruh tombol
                invoiceTabButtons.forEach(tab => {
                    tab.classList.remove('active');
                });

                // Hapus status aktif dari seluruh konten
                invoiceTabPanes.forEach(pane => {
                    pane.classList.remove('active');
                });

                // Aktifkan tombol yang dipilih
                this.classList.add('active');

                // Tampilkan konten tab yang dipilih
                const targetPane = document.getElementById(targetTab);

                if (targetPane) {
                    targetPane.classList.add('active');
                }

            });

        });

        // =====================================================
        // FILTER & SEARCH RIWAYAT PEMBAYARAN
        // =====================================================

        const historyBody = document.getElementById('historyPaymentBody');

        if (historyBody) {

            const historyRows = Array.from(
                historyBody.querySelectorAll('tr[data-date]')
            );

            const searchInput = document.getElementById('historySearch');
            const monthInput = document.getElementById('historyMonth');
            const methodSelect = document.getElementById('historyMethod');

            const resetButton = document.getElementById('historyResetFilter');
            const emptyResetButton = document.getElementById('historyEmptyReset');

            const visibleCount = document.getElementById('historyVisibleCount');
            const visibleTotal = document.getElementById('historyVisibleTotal');
            const filterStatus = document.getElementById('historyFilterStatus');
            const emptyState = document.getElementById('historyFilterEmpty');

            // -------------------------------------------------
            // FORMAT RUPIAH
            // -------------------------------------------------

            function formatHistoryRupiah(value) {
                return 'Rp' + new Intl.NumberFormat('id-ID', {
                    maximumFractionDigits: 0
                }).format(Number(value) || 0);
            }

            // -------------------------------------------------
            // ISI PILIHAN METODE PEMBAYARAN
            // -------------------------------------------------

            if (methodSelect) {

                const daftarMetode = [
                    ...new Set(
                        historyRows
                            .map(row => row.dataset.method)
                            .filter(method => method && method !== '-')
                    )
                ].sort();

                daftarMetode.forEach(method => {

                    const row = historyRows.find(
                        item => item.dataset.method === method
                    );

                    const namaMetode =
                        row?.querySelector('td:nth-child(4)')
                            ?.textContent.trim() || method;

                    const option = document.createElement('option');

                    option.value = method;
                    option.textContent = namaMetode;

                    methodSelect.appendChild(option);

                });

            }

            // -------------------------------------------------
            // PROSES FILTER
            // -------------------------------------------------

            function filterRiwayatPembayaran() {

                const keyword = searchInput?.value
                    .trim()
                    .toLocaleLowerCase('id-ID') || '';

                const selectedMonth = monthInput?.value || '';
                const selectedMethod = methodSelect?.value || '';

                let jumlahTampil = 0;
                let totalTampil = 0;

                historyRows.forEach(row => {

                    const tanggal = row.dataset.date || '';
                    const bulan = row.dataset.month || '';
                    const metode = row.dataset.method || '';

                    const nominal = Number(row.dataset.amount) || 0;

                    const teksBaris = row.textContent
                        .toLocaleLowerCase('id-ID');

                    const cocokKeyword =
                        !keyword || teksBaris.includes(keyword);

                    const cocokBulan =
                        !selectedMonth || bulan === selectedMonth;

                    const cocokMetode =
                        !selectedMethod || metode === selectedMethod;

                    const tampil =
                        cocokKeyword &&
                        cocokBulan &&
                        cocokMetode;

                    row.hidden = !tampil;

                    if (tampil) {
                        jumlahTampil++;
                        totalTampil += nominal;
                    }

                });

                // -------------------------------------------------
                // UPDATE SUMMARY
                // -------------------------------------------------

                if (visibleCount) {
                    visibleCount.textContent = jumlahTampil;
                }

                if (visibleTotal) {
                    visibleTotal.textContent =
                        formatHistoryRupiah(totalTampil);
                }

                // -------------------------------------------------
                // EMPTY STATE
                // -------------------------------------------------

                if (emptyState) {
                    emptyState.hidden = jumlahTampil > 0;
                }

                // -------------------------------------------------
                // STATUS FILTER
                // -------------------------------------------------

                if (filterStatus) {

                    const sedangFilter = Boolean(
                        keyword || selectedMonth || selectedMethod
                    );

                    filterStatus.textContent = sedangFilter
                        ? `Menampilkan ${jumlahTampil} dari ${historyRows.length} transaksi`
                        : 'Menampilkan semua transaksi';

                }

            }

            // -------------------------------------------------
            // EVENT INPUT
            // -------------------------------------------------

            [searchInput, monthInput, methodSelect]
                .filter(Boolean)
                .forEach(input => {

                    input.addEventListener(
                        'input',
                        filterRiwayatPembayaran
                    );

                    input.addEventListener(
                        'change',
                        filterRiwayatPembayaran
                    );

                });

            // -------------------------------------------------
            // RESET FILTER
            // -------------------------------------------------

            function resetFilterRiwayat() {

                if (searchInput) searchInput.value = '';
                if (monthInput) monthInput.value = '';
                if (methodSelect) methodSelect.value = '';

                filterRiwayatPembayaran();

            }

            resetButton?.addEventListener(
                'click',
                resetFilterRiwayat
            );

            emptyResetButton?.addEventListener(
                'click',
                resetFilterRiwayat
            );

            // -------------------------------------------------
            // INISIALISASI
            // -------------------------------------------------

            filterRiwayatPembayaran();

        }



        const modalElement = document.getElementById('modalPembayaran');
        const btnBayar = document.getElementById('btnBayarSiswa');

        if (!modalElement || !btnBayar) return;

        const modalPembayaran = bootstrap.Modal.getOrCreateInstance(modalElement);

        const wadahDaftar = document.getElementById('wadahDaftarTagihan');
        const pilihSemua = document.getElementById('pilihSemuaBelumLunas');
        const totalDipilih = document.getElementById('totalDipilih');
        const uangDiterima = document.getElementById('uangDiterima');
        const metodeBayar = document.getElementById('metodeBayar');
        const tanggalJamBayar = document.getElementById('tanggalJamBayar');
        const catatanBayar = document.getElementById('catatanBayar');
        const btnSimpan = document.getElementById('btnSimpanPembayaran');

        let daftarTagihanTerpilih = [];
        let rincianSimpan = [];

        // =====================================================
        // FORMAT RUPIAH
        // =====================================================

        function formatRupiah(angka) {
            return 'Rp' + new Intl.NumberFormat('id-ID', {
                maximumFractionDigits: 0
            }).format(Number(angka) || 0);
        }

        function ambilAngkaMurni(nilai) {
            return Number(String(nilai).replace(/[^\d]/g, '')) || 0;
        }

        function ambilWaktuSekarang() {
            const sekarang = new Date();
            const offset = sekarang.getTimezoneOffset() * 60000;
            return new Date(sekarang.getTime() - offset)
                .toISOString()
                .slice(0, 16);
        }

        function escapeText(value) {
            return String(value ?? '');
        }

        // =====================================================
        // PAGINATION
        // =====================================================

        function inisialisasiPaginasi(nav) {
            const target = document.getElementById(nav.dataset.target);
            if (!target) return;

            const rows = Array.from(target.querySelectorAll('tr'));
            const sebelumnya = nav.querySelector('.btn-sebelum');
            const sesudah = nav.querySelector('.btn-sesudah');
            const daftarNomor = nav.querySelector('.daftar-nomor');

            let perHalaman = Number(nav.dataset.perhalaman) || 5;
            let halamanAktif = 1;

            const selectUkuran = document.querySelector(
                `.ukuran-tampil[data-target="${nav.dataset.target}"]`
            );

            function render() {
                const totalHalaman = perHalaman === Infinity
                    ? 1
                    : Math.max(1, Math.ceil(rows.length / perHalaman));

                halamanAktif = Math.min(halamanAktif, totalHalaman);

                rows.forEach((row, index) => {
                    row.style.display =
                        perHalaman === Infinity ||
                        (index >= (halamanAktif - 1) * perHalaman &&
                        index < halamanAktif * perHalaman)
                        ? ''
                        : 'none';
                });

                daftarNomor.replaceChildren();

                for (let i = 1; i <= totalHalaman; i++) {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.textContent = i;

                    if (i === halamanAktif) {
                        button.classList.add('active');
                    }

                    button.addEventListener('click', function () {
                        halamanAktif = i;
                        render();
                    });

                    daftarNomor.appendChild(button);
                }

                sebelumnya.disabled = halamanAktif <= 1;
                sesudah.disabled = halamanAktif >= totalHalaman;
            }

            sebelumnya.addEventListener('click', function () {
                if (halamanAktif > 1) {
                    halamanAktif--;
                    render();
                }
            });

            sesudah.addEventListener('click', function () {
                const totalHalaman = perHalaman === Infinity
                    ? 1
                    : Math.max(1, Math.ceil(rows.length / perHalaman));

                if (halamanAktif < totalHalaman) {
                    halamanAktif++;
                    render();
                }
            });

            if (selectUkuran) {
                selectUkuran.addEventListener('change', function () {
                    perHalaman = this.value === 'all'
                        ? Infinity
                        : Number(this.value);

                    halamanAktif = 1;
                    nav.dataset.perhalaman = this.value;
                    render();
                });
            }

            render();
        }

        document.querySelectorAll('.paginasi-wrapper').forEach(inisialisasiPaginasi);

        // =====================================================
        // COLLAPSE ICON
        // =====================================================

        document.querySelectorAll(
            '.invoice-category-header[data-bs-toggle="collapse"]'
        ).forEach(header => {

            const targetSelector = header.getAttribute('data-bs-target');
            const target = document.querySelector(targetSelector);

            if (!target) return;

            target.addEventListener('show.bs.collapse', function () {
                header.setAttribute('aria-expanded', 'true');
            });

            target.addEventListener('hide.bs.collapse', function () {
                header.setAttribute('aria-expanded', 'false');
            });

        });

        // =====================================================
        // RESET MODAL
        // =====================================================

        function resetModal() {
            daftarTagihanTerpilih = [];
            rincianSimpan = [];

            wadahDaftar.replaceChildren();

            const placeholder = document.createElement('div');
            placeholder.className = 'payment-empty-placeholder';
            placeholder.textContent = 'Pilih tagihan untuk memulai pembayaran.';
            wadahDaftar.appendChild(placeholder);

            pilihSemua.checked = false;
            totalDipilih.textContent = 'Rp0';
            uangDiterima.value = '';
            metodeBayar.value = '';
            tanggalJamBayar.value = ambilWaktuSekarang();
            catatanBayar.value = '';

            btnSimpan.disabled = false;
            btnSimpan.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Simpan Pembayaran</span>
                <i class="fas fa-arrow-right submit-arrow"></i>
            `;
        }

        modalElement.addEventListener('hidden.bs.modal', resetModal);

        // =====================================================
        // MEMBANGUN DAFTAR TAGIHAN DI MODAL
        // =====================================================

        function buatElemen(tag, className, text) {
            const element = document.createElement(tag);

            if (className) element.className = className;
            if (text !== undefined) element.textContent = text;

            return element;
        }

        function buatDaftarTagihan() {

            const kelompok = new Map();

            document.querySelectorAll('.invoice-table tbody tr[data-id]')
                .forEach(row => {

                    const id = row.dataset.id;
                    const nominal = Number(row.dataset.nominal) || 0;
                    const sudahDibayar = Number(row.dataset.dibayar) || 0;
                    const sisa = Number(row.dataset.sisa) || 0;
                    const status = row.dataset.status || '';
                    const namaKelompok = row.dataset.kelompok || 'Lainnya';

                    if (!id || sisa <= 0 ||
                        status.toLowerCase() === 'lunas') {
                        return;
                    }

                    const namaTagihan =
                        row.querySelector('.invoice-name-cell span:last-child')
                            ?.textContent.trim() || 'Tagihan';

                    const periode =
                        row.querySelector('.invoice-period')
                            ?.textContent.trim() || '-';

                    if (!kelompok.has(namaKelompok)) {
                        kelompok.set(namaKelompok, []);
                    }

                    kelompok.get(namaKelompok).push({
                        id,
                        nama: namaTagihan,
                        periode,
                        nominal,
                        sudah_dibayar: sudahDibayar,
                        sisa,
                        kelompok: namaKelompok
                    });
                });

            if (kelompok.size === 0) {
                const empty = buatElemen('div', 'payment-empty-placeholder');

                const icon = buatElemen('i', 'fas fa-circle-check');
                const text = buatElemen(
                    'span',
                    '',
                    'Semua tagihan siswa sudah lunas.'
                );

                empty.append(icon, text);
                wadahDaftar.replaceChildren(empty);
                return false;
            }

            wadahDaftar.replaceChildren();

            let indexKelompok = 0;

            kelompok.forEach((tagihan, namaKelompok) => {

                indexKelompok++;

                const group = buatElemen('div', 'payment-group');
                const heading = buatElemen('div', 'payment-group-heading');
                const label = buatElemen('label');

                const checkboxKelompok = document.createElement('input');
                checkboxKelompok.type = 'checkbox';
                checkboxKelompok.className = 'pilih-semua-kelompok';
                checkboxKelompok.dataset.group = String(indexKelompok);

                const nama = buatElemen('span', '', namaKelompok);
                const jumlah = buatElemen(
                    'small',
                    '',
                    `${tagihan.length} tagihan`
                );

                label.append(checkboxKelompok, nama);
                heading.append(label, jumlah);

                group.appendChild(heading);

                tagihan.forEach(item => {

                    const row = buatElemen('div', 'payment-invoice-row');

                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.className = 'payment-invoice-check cek-tagihan';

                    checkbox.value = String(item.sisa);
                    checkbox.dataset.id = item.id;
                    checkbox.dataset.nominal = String(item.nominal);
                    checkbox.dataset.dibayar = String(item.sudah_dibayar);
                    checkbox.dataset.sisa = String(item.sisa);
                    checkbox.dataset.nama = item.nama;
                    checkbox.dataset.periode = item.periode;
                    checkbox.dataset.group = String(indexKelompok);

                    const detail = buatElemen('div', 'payment-invoice-detail');
                    const namaTagihan = buatElemen(
                        'div',
                        'payment-invoice-name',
                        item.nama
                    );

                    const meta = buatElemen(
                        'div',
                        'payment-invoice-meta',
                        `${item.periode} · ${item.kelompok}`
                    );

                    detail.append(namaTagihan, meta);

                    const amount = buatElemen('div', 'payment-invoice-amount');
                    amount.textContent = formatRupiah(item.sisa);

                    const small = buatElemen(
                        'small',
                        '',
                        `Nominal awal ${formatRupiah(item.nominal)}`
                    );

                    amount.appendChild(small);

                    row.append(checkbox, detail, amount);
                    group.appendChild(row);

                    checkbox.addEventListener('change', function () {
                        row.classList.toggle('is-selected', this.checked);
                        perbaruiStatusKelompok(indexKelompok);
                        hitungTotalTerpilih();
                    });
                });

                checkboxKelompok.addEventListener('change', function () {
                    group.querySelectorAll('.cek-tagihan').forEach(cb => {
                        cb.checked = this.checked;
                        cb.closest('.payment-invoice-row')
                            ?.classList.toggle('is-selected', this.checked);
                    });

                    hitungTotalTerpilih();
                    perbaruiStatusPilihSemua();
                });

                wadahDaftar.appendChild(group);
            });

            return true;
        }

        // =====================================================
        // CHECKBOX GROUP
        // =====================================================

        function perbaruiStatusKelompok(groupId) {

            const groupCheckbox = wadahDaftar.querySelector(
                `.pilih-semua-kelompok[data-group="${groupId}"]`
            );

            const checkboxes = wadahDaftar.querySelectorAll(
                `.cek-tagihan[data-group="${groupId}"]`
            );

            if (!groupCheckbox) return;

            const total = checkboxes.length;
            const checked = Array.from(checkboxes)
                .filter(cb => cb.checked).length;

            groupCheckbox.checked = total > 0 && checked === total;
            groupCheckbox.indeterminate = checked > 0 && checked < total;
        }

        function perbaruiStatusPilihSemua() {

            const checkboxes = wadahDaftar.querySelectorAll('.cek-tagihan');
            const checked = Array.from(checkboxes)
                .filter(cb => cb.checked).length;

            pilihSemua.checked =
                checkboxes.length > 0 && checked === checkboxes.length;

            pilihSemua.indeterminate =
                checked > 0 && checked < checkboxes.length;
        }

        pilihSemua.addEventListener('change', function () {

            const semua = wadahDaftar.querySelectorAll('.cek-tagihan');

            semua.forEach(cb => {
                cb.checked = this.checked;
                cb.closest('.payment-invoice-row')
                    ?.classList.toggle('is-selected', this.checked);
            });

            wadahDaftar.querySelectorAll('.pilih-semua-kelompok')
                .forEach(cb => {
                    cb.checked = pilihSemua.checked;
                    cb.indeterminate = false;
                });

            hitungTotalTerpilih();
        });

        // =====================================================
        // HITUNG TOTAL DAN ALOKASI
        // =====================================================

        function hitungTotalTerpilih() {

            const checkboxes = Array.from(
                wadahDaftar.querySelectorAll('.cek-tagihan:checked')
            );

            const total = checkboxes.reduce((sum, cb) => {
                return sum + Number(cb.dataset.sisa || cb.value || 0);
            }, 0);

            totalDipilih.textContent = formatRupiah(total);

            const nominalInput = ambilAngkaMurni(uangDiterima.value);

            if (checkboxes.length === 0) {
                uangDiterima.value = '';
            } else if (nominalInput > total) {
                uangDiterima.value = total.toLocaleString('id-ID');
            }

            perbaruiStatusPilihSemua();
            hitungAlokasi();
        }

        function hitungAlokasi() {

            rincianSimpan = [];

            const checkboxes = Array.from(
                wadahDaftar.querySelectorAll('.cek-tagihan:checked')
            );

            let sisaPembayaran = ambilAngkaMurni(uangDiterima.value);

            checkboxes.forEach(cb => {

                const nominalAsli = Number(cb.dataset.nominal) || 0;
                const sudahDibayar = Number(cb.dataset.dibayar) || 0;
                const sisaTagihan = Number(cb.dataset.sisa) || 0;

                const dibayar = Math.min(sisaPembayaran, sisaTagihan);
                const totalDibayar = sudahDibayar + dibayar;
                const sisaHutang = Math.max(0, sisaTagihan - dibayar);

                if (dibayar > 0) {
                    rincianSimpan.push({
                        id: cb.dataset.id,
                        nominal_asli: nominalAsli,
                        dibayar: totalDibayar,
                        sisa_hutang: sisaHutang
                    });
                }

                sisaPembayaran -= dibayar;
            });
        }

        // =====================================================
        // INPUT NOMINAL
        // =====================================================

        uangDiterima.addEventListener('input', function () {

            const nilaiSebelumnya = ambilAngkaMurni(this.value);

            const checkboxes = Array.from(
                wadahDaftar.querySelectorAll('.cek-tagihan:checked')
            );

            const total = checkboxes.reduce((sum, cb) => {
                return sum + Number(cb.dataset.sisa || 0);
            }, 0);

            let nominal = nilaiSebelumnya;

            if (nominal > total) {
                nominal = total;
            }

            this.value = nominal > 0
                ? nominal.toLocaleString('id-ID')
                : '';

            hitungAlokasi();
        });

        // =====================================================
        // BUKA MODAL
        // =====================================================

        btnBayar.addEventListener('click', function () {

            resetModal();

            const berhasil = buatDaftarTagihan();

            if (!berhasil) {
                // Modal tetap dapat dibuka agar bendahara melihat
                // informasi bahwa semua tagihan telah lunas.
                modalPembayaran.show();
                return;
            }

            modalPembayaran.show();
        });

        // =====================================================
        // SIMPAN PEMBAYARAN
        // =====================================================

        btnSimpan.addEventListener('click', async function () {

            const nominal = ambilAngkaMurni(uangDiterima.value);
            const metode = metodeBayar.value;
            const tanggaljam = tanggalJamBayar.value;

            const checkboxes = wadahDaftar.querySelectorAll('.cek-tagihan:checked');

            const totalDipilihAngka = Array.from(checkboxes).reduce(
                (sum, cb) => sum + Number(cb.dataset.sisa || 0),
                0
            );

            if (checkboxes.length === 0) {
                alert('Silakan pilih minimal satu tagihan.');
                return;
            }

            if (!nominal || nominal <= 0) {
                alert('Masukkan nominal pembayaran terlebih dahulu.');
                uangDiterima.focus();
                return;
            }

            if (nominal > totalDipilihAngka) {
                alert('Nominal pembayaran melebihi total tagihan yang dipilih.');
                return;
            }

            if (!metode) {
                alert('Silakan pilih metode pembayaran.');
                metodeBayar.focus();
                return;
            }

            if (!tanggaljam) {
                alert('Tanggal dan waktu pembayaran wajib diisi.');
                tanggalJamBayar.focus();
                return;
            }

            hitungAlokasi();

            if (rincianSimpan.length === 0) {
                alert('Tidak ada alokasi pembayaran yang dapat disimpan.');
                return;
            }

            const [tanggal_bayar, jam_bayar] = tanggaljam.split('T');

            const dataPembayaran = {
                id_siswa: document.getElementById('idSiswaTerpilih').value,
                rincian: rincianSimpan,
                metode_bayar: metode,
                catatan: catatanBayar.value.trim(),
                tanggal_bayar: tanggal_bayar,
                jam_bayar: jam_bayar,
                tanggal_lengkap: tanggaljam
            };

            const csrfToken =
                document.querySelector('meta[name="csrf-token"]')?.content ||
                document.querySelector('input[name="csrf_token"]')?.value ||
                '';

            const teksAwal = btnSimpan.innerHTML;

            btnSimpan.disabled = true;
            btnSimpan.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <span>Menyimpan Pembayaran...</span>
            `;

            try {

                const headers = {
                    'Content-Type': 'application/json'
                };

                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }

                const response = await fetch('/bendahara/simpan-pembayaran', {
                    method: 'POST',
                    headers,
                    body: JSON.stringify(dataPembayaran)
                });

                const hasil = await response.json();

                if (!response.ok) {
                    throw new Error(
                        hasil.pesan || hasil.message || 'Terjadi kesalahan saat menyimpan pembayaran.'
                    );
                }

                if (hasil.sukses) {

                    alert(hasil.pesan || 'Pembayaran berhasil disimpan!');

                    modalPembayaran.hide();

                    window.location.reload();

                } else {

                    alert(hasil.pesan || 'Pembayaran gagal disimpan.');

                    btnSimpan.disabled = false;
                    btnSimpan.innerHTML = teksAwal;
                }

            } catch (error) {

                console.error('Kesalahan pembayaran:', error);

                alert(error.message || 'Tidak dapat menghubungi server.');

                btnSimpan.disabled = false;
                btnSimpan.innerHTML = teksAwal;
            }

        });

                // =====================================================
        // INISIALISASI AWAL
        // =====================================================

        tanggalJamBayar.value = ambilWaktuSekarang();

    } // END initInvoiceAdminPage


    // =====================================================
    // INITIAL LOAD
    // =====================================================

    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initInvoiceAdminPage,
            { once: true }
        );

    } else {

        initInvoiceAdminPage();

    }


    // =====================================================
    // SPA NAVIGATION
    // =====================================================

    document.addEventListener('spa:page-loaded', function () {

        initInvoiceAdminPage();

    });

})();