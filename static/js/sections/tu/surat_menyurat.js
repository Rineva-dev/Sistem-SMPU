document.addEventListener('DOMContentLoaded', function() {


    // ==========================================
    // BAGIAN 1: KALENDER KUSTOM
    // ==========================================
    const customDateWrappers = document.querySelectorAll('.custom-date');
    let activeCalendar = null;
    let currentView = 'days';
    let yearRangeStart = new Date().getFullYear() - 10;

    // Sudah ada ini di JS kamu
    const bulanNama = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ];

    // ✅ Fungsi yang DIPERBAIKI & DILENGKAPI
    function ubahTanggalKeBahasaIndonesia(tanggalStr) {
        if (!tanggalStr || tanggalStr === '-') return tanggalStr;

        const petaBulan = {
            'January': 'Januari',
            'February': 'Februari',
            'March': 'Maret',
            'April': 'April',
            'May': 'Mei',
            'June': 'Juni',
            'July': 'Juli',
            'August': 'Agustus',
            'September': 'September',
            'October': 'Oktober',
            'November': 'November',
            'December': 'Desember'
        };

        // 1. Format: "03 July 2026" → bahasa Indonesia
        const bagian = tanggalStr.trim().split(' ');
        if (bagian.length === 3 && petaBulan[bagian[1]]) {
            return `${bagian[0]} ${petaBulan[bagian[1]]} ${bagian[2]}`;
        }

        // 2. Format: "03/07/2026" → bahasa Indonesia
        if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(tanggalStr)) {
            const [hari, bln, thn] = tanggalStr.split('/');
            const indeksBulan = parseInt(bln) - 1;
            if (indeksBulan >= 0 && indeksBulan < 12) {
                return `${hari.padStart(2, '0')} ${bulanNama[indeksBulan]} ${thn}`;
            }
        }

        // 3. Format: "2026-07-03" (dari database) → bahasa Indonesia ✅ DITAMBAHKAN
        if (/^\d{4}-\d{2}-\d{2}$/.test(tanggalStr)) {
            const tglObj = new Date(tanggalStr + 'T00:00:00');
            if (!isNaN(tglObj.getTime())) {
                const hari = String(tglObj.getDate()).padStart(2, '0');
                const bulan = bulanNama[tglObj.getMonth()];
                const tahun = tglObj.getFullYear();
                return `${hari} ${bulan} ${tahun}`;
            }
        }

        return tanggalStr;
    }

    customDateWrappers.forEach(wrapper => {
        const existingTrigger = wrapper.querySelector('.custom-date__trigger');
        if (existingTrigger) existingTrigger.remove();

        const originalInput = wrapper.querySelector('input[type="date"]');
        originalInput.style.opacity = '0';
        originalInput.style.position = 'absolute';
        originalInput.style.pointerEvents = 'none';
        originalInput.tabIndex = -1;

        let currentDate = new Date();
        let selectedDate = originalInput.value ? new Date(originalInput.value + 'T00:00:00') : null;

        const trigger = document.createElement('div');
        const inputManual = document.createElement('input');
        const icon = document.createElement('i');

        trigger.className = 'custom-date__trigger';
        inputManual.className = 'custom-date__input-manual';
        inputManual.type = 'text';
        inputManual.placeholder = 'dd/mm/yyyy';
        inputManual.tabIndex = 0;
        icon.className = 'fa fa-calendar custom-date__icon';
        icon.tabIndex = -1;

        trigger.append(inputManual, icon);
        wrapper.append(trigger);

        function formatToDisplay(date) {
            if (!date || isNaN(date.getTime())) return '';
            const d = String(date.getDate()).padStart(2, '0');
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const y = date.getFullYear();
            return `${d}/${m}/${y}`;
        }

        function formatToSave(str) {
            if (!str) return '';
            const parts = str.split('/');
            if (parts.length !== 3) return '';
            const d = parseInt(parts[0]);
            const m = parseInt(parts[1]);
            const y = parseInt(parts[2]);
            if (!d || !m || !y || m < 1 || m > 12 || d < 1 || d > 31) return '';
            const date = new Date(y, m - 1, d);
            if (date.getDate() !== d || date.getMonth() + 1 !== m || date.getFullYear() !== y) return '';
            return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        }

        function updateDisplay() {
            inputManual.value = formatToDisplay(selectedDate);
        }

        function renderDays() {
            currentView = 'days';
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();

            const firstDay = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const daysInPrevMonth = new Date(year, month, 0).getDate();

            let html = `
                <div class="calendar-header">
                    <button type="button" class="calendar-nav prev">&larr;</button>
                    <div class="calendar-title">${bulanNama[month]} ${year}</div>
                    <button type="button" class="calendar-nav next">&rarr;</button>
                </div>
                <div class="calendar-weekdays">
                    <span>Min</span><span>Sen</span><span>Sel</span><span>Rab</span><span>Kam</span><span>Jum</span><span>Sab</span>
                </div>
                <div class="calendar-days">
            `;

            for (let i = firstDay - 1; i >= 0; i--) {
                html += `<div class="calendar-day other-month">${daysInPrevMonth - i}</div>`;
            }

            const today = new Date();
            for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(year, month, day);
                const isToday = date.toDateString() === today.toDateString();
                const isSelected = selectedDate && date.toDateString() === selectedDate.toDateString();
                const kelas = `calendar-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}`;
                html += `<div class="${kelas}" data-day="${day}">${day}</div>`;
            }

            const totalCells = 42;
            const used = firstDay + daysInMonth;
            for (let i = 1; i <= totalCells - used; i++) {
                html += `<div class="calendar-day other-month">${i}</div>`;
            }

            html += `</div>`;
            activeCalendar.innerHTML = html;

            activeCalendar.querySelector('.prev').addEventListener('click', (e) => {
                e.stopPropagation();
                currentDate.setMonth(currentDate.getMonth() - 1);
                renderDays();
            });

            activeCalendar.querySelector('.next').addEventListener('click', (e) => {
                e.stopPropagation();
                currentDate.setMonth(currentDate.getMonth() + 1);
                renderDays();
            });

            activeCalendar.querySelector('.calendar-title').addEventListener('click', (e) => {
                e.stopPropagation();
                renderMonths();
            });

            activeCalendar.querySelectorAll('.calendar-day:not(.other-month)').forEach(dayEl => {
                dayEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const day = parseInt(dayEl.dataset.day);
                    selectedDate = new Date(year, month, day);
                    originalInput.value = formatToSave(formatToDisplay(selectedDate));
                    originalInput.dispatchEvent(new Event('change'));
                    updateDisplay();
                    closeCalendar();
                });
            });
        }

        function renderMonths() {
            currentView = 'months';
            const year = currentDate.getFullYear();

            let html = `
                <div class="calendar-header">
                    <button type="button" class="calendar-nav prev">&larr;</button>
                    <div class="calendar-title">${year}</div>
                    <button type="button" class="calendar-nav next">&rarr;</button>
                </div>
                <div class="calendar-months">
            `;

            bulanNama.forEach((namaBulan, indeks) => {
                const isActive = indeks === currentDate.getMonth();
                html += `<div class="month-item ${isActive ? 'active' : ''}" data-month="${indeks}">${namaBulan}</div>`;
            });

            html += `</div>`;
            activeCalendar.innerHTML = html;

            activeCalendar.querySelector('.prev').addEventListener('click', (e) => {
                e.stopPropagation();
                currentDate.setFullYear(currentDate.getFullYear() - 1);
                renderMonths();
            });

            activeCalendar.querySelector('.next').addEventListener('click', (e) => {
                e.stopPropagation();
                currentDate.setFullYear(currentDate.getFullYear() + 1);
                renderMonths();
            });

            activeCalendar.querySelector('.calendar-title').addEventListener('click', (e) => {
                e.stopPropagation();
                renderYears();
            });

            activeCalendar.querySelectorAll('.month-item').forEach(monthEl => {
                monthEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const bulanPilih = parseInt(monthEl.dataset.month);
                    currentDate.setMonth(bulanPilih);
                    renderDays();
                });
            });
        }

        function renderYears() {
            currentView = 'years';
            const rentangMulai = yearRangeStart;
            const rentangAkhir = rentangMulai + 9;

            let html = `
                <div class="calendar-header">
                    <button type="button" class="calendar-nav prev">&larr;</button>
                    <div class="calendar-title">${rentangMulai} - ${rentangAkhir}</div>
                    <button type="button" class="calendar-nav next">&rarr;</button>
                </div>
                <div class="calendar-years">
            `;

            for (let y = rentangMulai; y <= rentangAkhir; y++) {
                const isActive = y === currentDate.getFullYear();
                html += `<div class="year-item ${isActive ? 'active' : ''}" data-year="${y}">${y}</div>`;
            }

            html += `</div>`;
            activeCalendar.innerHTML = html;

            activeCalendar.querySelector('.prev').addEventListener('click', (e) => {
                e.stopPropagation();
                yearRangeStart -= 10;
                renderYears();
            });

            activeCalendar.querySelector('.next').addEventListener('click', (e) => {
                e.stopPropagation();
                yearRangeStart += 10;
                renderYears();
            });

            activeCalendar.querySelectorAll('.year-item').forEach(yearEl => {
                yearEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const tahunPilih = parseInt(yearEl.dataset.year);
                    currentDate.setFullYear(tahunPilih);
                    renderMonths();
                });
            });
        }

        function openCalendar() {
            if (!activeCalendar) {
                activeCalendar = document.createElement('div');
                activeCalendar.className = 'custom-date__calendar';
                document.body.appendChild(activeCalendar);
            }

            const rect = trigger.getBoundingClientRect();
            activeCalendar.style.left = `${rect.left + window.scrollX}px`;
            activeCalendar.style.top = `${rect.bottom + window.scrollY + 8}px`;

            activeCalendar.classList.add('open');
            wrapper.classList.add('open', 'focused');

            if (typeof window.closeAllSelects === 'function') window.closeAllSelects();
            if (typeof tutupDropdownTugas === 'function') tutupDropdownTugas();

            currentDate = selectedDate ? new Date(selectedDate) : new Date();
            yearRangeStart = Math.floor(currentDate.getFullYear() / 10) * 10;
            renderDays();
        }

        window.closeCalendar = function() {
            if (activeCalendar) activeCalendar.classList.remove('open');
            document.querySelectorAll('.custom-date').forEach(el => el.classList.remove('open', 'focused'));
            currentView = 'days';
        };

        inputManual.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) value = value.slice(0, 8);
            if (value.length >= 2) value = value.slice(0, 2) + '/' + value.slice(2);
            if (value.length >= 5) value = value.slice(0, 5) + '/' + value.slice(5);
            e.target.value = value;
        });

        inputManual.addEventListener('blur', function() {
            const str = this.value.trim();
            const valid = formatToSave(str);
            if (valid) {
                originalInput.value = valid;
                selectedDate = new Date(valid + 'T00:00:00');
                updateDisplay();
            } else {
                this.value = formatToDisplay(selectedDate);
            }
            wrapper.classList.remove('focused');
        });

        inputManual.addEventListener('focus', () => {
            wrapper.classList.add('focused');
            if (typeof tutupSemua === 'function') tutupSemua();
        });

        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            activeCalendar?.classList.contains('open') ? closeCalendar() : openCalendar();
        });

        document.addEventListener('click', (e) => {
            const diDalamWrapper = wrapper.contains(e.target);
            const diDalamKalender = activeCalendar?.contains(e.target);
            if (!diDalamWrapper && !diDalamKalender) closeCalendar();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeCalendar();
        });

        updateDisplay();
    });

    // --- Buka Modal & Tampilkan Surat Lengkap ---
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.btn-lihat-surat');
        if (!btn) return;

        const modalEl = document.getElementById('modalLihatSurat');
        const modal = new bootstrap.Modal(modalEl);

        // Ambil data dari atribut
        const nomor = btn.dataset.nomor || '';
        const tanggal = ubahTanggalKeBahasaIndonesia(btn.dataset.tanggal || '');
        const tujuan = btn.dataset.tujuan || '';
        const lampiran = btn.dataset.lampiran || '-';
        const perihal = btn.dataset.perihal || '';
        const isi = JSON.parse(btn.dataset.isi || '""');
        const daftarTtd = JSON.parse(btn.dataset.ttd || '[]');

        // Susun format surat lengkap dengan kop
        const htmlSurat = `
        <!-- KOP SURAT -->
        <div class="kop-surat">
            <div class="kop-konten">
            <img src="/static/img/logo-school.svg" alt="Logo SMP Unggulan Hamzanwadi" class="kop-logo">
            
            <div class="kop-pemisah"></div>

            <div class="kop-teks-kanan">
                <div class="kop-izin">IZIN OPERASIONAL: 500.16.7.2/97/PMPTSP-SMP/01/2025</div>
                <div class="kop-kontak">
                <i class="fa-brands fa-whatsapp-square"></i>
                <span>081915780964</span>
                <i class="fa-solid fa-envelope"></i>
                <span>smpu@hamzanwadi.ac.id</span>
                </div>
                <div class="kop-alamat">Jl. Dr. Ciptromangun Kusumo, Sawing, Kel. Majidi, Kec. Selong, Kab. Lombok Timur - NTB</div>
            </div>
            </div>
        </div>

        <!-- ISI SURAT -->
        <div class="surat-kepala">
            <span class="label">Nomor</span>
            <span class="value">: ${nomor}</span>

            <span class="label">Lampiran</span>
            <span class="value">: ${lampiran}</span>

            <span class="label">Hal</span>
            <span class="value">: <strong>${perihal}</strong></span>
        </div>

        <div class="surat-tujuan">
            <p>${tujuan.replace(/^(Kepada\s*\n?\s*Yth\.\s*)([\s\S]*?)(\n\s*di\s+[\s\S]*)$/s, '$1<strong>$2</strong>$3')}</p>
        </div>

        <div class="surat-isi">
            <p><strong><em>Bismillahiwabihamdihi</em></strong></p>
            <p class="salam"><em><strong>Assalamu'alaikum Warahmatullahi Wabarakatuh</em></strong></p>
            <p>Semoga kami menjumpai Bapak/Ibu dalam keadaan sehat wal'afiat serta dalam limpahan Rahmat dan taufik dari Allah SWT. sehingga dapat beraktivitas seperti biasanya. Aamiin ya Rabbal Alamin.</p>
            <p class="isi">${isi}</p>
            <p class="wassalam"><strong><em>Wallohul Muwaffiq Wal Hadi ila Sabi Lirrosyad</em></strong></p>
            <p><strong><em>Wassalamu'alaikum Warahmatullahi Wabarakatuh</em></strong></p>
        </div>

        <!-- TANDA TANGAN + QR SESUAI FORMAT -->
        <div class="surat-ttd" style="color: black;">
            <p style="text-align: right; margin: 1rem 0 0;">
                Majidi, ${tanggal}
            </p>
            ${(() => {
                // ✅ Gunakan data yang sudah diambil dari tombol
                const daftarTtd = JSON.parse(btn.dataset.ttd || '[]');
                const jumlah = daftarTtd.length;
                // Cari posisi Kepala Sekolah
                const posisiKepala = daftarTtd.findIndex(t => t.jabatan?.trim().toLowerCase() === 'kepala sekolah');
                const adaKepala = posisiKepala !== -1;

                function buatBlokTtd(ttd) {
                    const sudahTtd = ttd.ttd_selesai === true;
                    const qr = sudahTtd && ttd.qr_code 
                        ? `
                            <div class="qr-verifikasi" style="margin: 0 auto; text-align: center;">
                                <img src="/static/${ttd.qr_code}" alt="QR Verifikasi Elektronik" style="width: 80px; height: 80px; object-fit: contain;">
                                <p style="font-size: 8pt; margin:0; color: #333;">Ditandatangani secara elektronik</p>
                            </div>
                        ` 
                        : `<p style="font-size: 9pt; color: #888; margin: 0 auto;">Belum ditandatangani</p>`;

                    return `
                        <div style="text-align: center;">
                            <p style="margin: 0 0 0.75rem 0;">${ttd.jabatan || ''}</p>
                            ${qr}
                            <p style="margin: 0;"><strong>${ttd.nama || ''}</strong></p>
                            <p style="margin: 0;">NIP. ${ttd.nip || '-'}</p>
                        </div>
                    `;
                }

                let htmlTtd = '';

                if (jumlah === 1) {
                    htmlTtd = `<div style="margin-left: 65%; text-align: left; width: max-content;">${buatBlokTtd(daftarTtd[0])}</div>`;
                } 
                else if (jumlah === 2) {
                    if (adaKepala) {
                        if (posisiKepala === 0) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                            `;
                        } else {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                            `;
                        }
                    } else {
                        htmlTtd = `
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                            </div>
                        `;
                    }
                } 
                else if (jumlah === 3) {
                    if (adaKepala) {
                        if (posisiKepala === 0) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                            `;
                        } else if (posisiKepala === 1) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                            `;
                        } else if (posisiKepala === 2) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="width: 100%; text-align: center; margin-top: 1rem;">
                                    <p style="margin: 0;">Mengetahui,</p>
                                    ${buatBlokTtd(daftarTtd[2])}
                                </div>
                            `;
                        }
                    } else {
                        htmlTtd = `
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                            </div>
                            <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                        `;
                    }
                } 
                else if (jumlah === 4) {
                    if (adaKepala) {
                        if (posisiKepala === 0) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        } else if (posisiKepala === 1) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        } else if (posisiKepala === 2) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1rem;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        } else if (posisiKepala === 3) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1rem;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        }
                    } else {
                        htmlTtd = `
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                            </div>
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1.5rem;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                            </div>
                        `;
                    }
                }

                return htmlTtd;
            })()}
        </div>
        `;

        // Masukkan konten ke modal
        document.getElementById('kontenSuratLengkap').innerHTML = htmlSurat;
        modal.show();
    });

    // --- Fungsi Cetak ---
    document.getElementById('btnCetakDariModal').addEventListener('click', function() {
        const konten = document.getElementById('kontenSuratLengkap').innerHTML;
        if (!konten.trim()) {
            alert('Konten surat belum siap, silakan tunggu sebentar!');
            return;
        }

        const jendelaCetak = window.open('', '_blank', 'width=900,height=1100,scrollbars=yes');
        jendelaCetak.document.write(`
            <!DOCTYPE html>
            <html lang="id-ID">
            <head>

                <meta charset="UTF-8">
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Cetak Surat</title>
                <!-- Ambil gaya dari file CSS utama -->
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                <link rel="stylesheet" href="/static/css/jabatan/tu/surat_menyurat.css" onload="setelahSiap()">
                <style>
                    /* === Aturan cetak khusus agar stabil di PDF === */
                    @page {
                        size: A4;
                        margin: 0;
                        /* Hindari pemotongan halaman yang tidak rapi */
                        orphans: 4;
                        widows: 4;
                        /* Paksa kualitas maksimal */
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }

                    * {
                        margin: 0;
                        padding: 0;
                        border: 0;
                        box-sizing: border-box;
                        /* Jaga karakter & gambar tetap tajam */
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                        color-adjust: exact !important;
                        image-rendering: -webkit-optimize-contrast !important;
                        image-rendering: crisp-edges !important;
                        -webkit-font-smoothing: antialiased !important;
                        -moz-osx-font-smoothing: grayscale !important;
                        /* Mencegah perubahan bentuk saat dikonversi ke PDF */
                        transform: none !important;
                        backface-visibility: visible !important;
                    }

                    body {
                        font-family: 'Times New Roman', Times, serif !important;
                        font-size: 12pt !important;
                        line-height: 1.7 !important;
                        background: #ffffff !important;
                        color: #000000 !important;
                        width: 210mm !important;
                        min-height: 297mm !important;
                        margin: 0 auto !important;
                        /* Jangan ubah skala aslinya */
                        zoom: 1 !important;
                    }

                    /* === Kop & Logo tetap asli === */
                    .kop-surat {
                        width: 100% !important;
                        position: relative !important;
                        overflow: visible !important;
                    }

                    .kop-logo {
                        object-fit: contain !important;
                        display: block !important;
                        image-rendering: crisp-edges !important;
                    }

                    .kop-pemisah {
                        background-size: 100% auto !important;
                        background-repeat: repeat-x !important;
                        background-position: top center !important;
                    }

                    /* === Konten surat tetap rapi === */
                    #kontenSuratLengkap {
                        width: 210mm !important;
                        min-height: 297mm !important;
                        margin: 0 auto !important;
                        padding: 0.5cm 1.27cm 1.27cm !important;
                        background: #ffffff !important;
                        box-shadow: none !important;
                        visibility: visible !important;
                        display: block !important;
                        white-space: normal !important;
                    }

                    /* Sembunyikan hanya elemen yang mengganggu */
                    .modal, .modal-backdrop, button, .btn, .nav, .card-header, .card-footer, .custom-date, .calendar {
                        display: none !important;
                        visibility: hidden !important;
                        position: absolute !important;
                        width: 0 !important;
                        height: 0 !important;
                    }

                    /* Tunggu sampai benar-benar siap */
                    function setelahSiap() {
                        setTimeout(() => {
                            window.print();
                            window.close();
                        }, 1200);
                    }
                </style>
            </head>
            <body>
                <div id="kontenSuratLengkap">
                    ${konten}
                </div>
            </body>
            </html>
        `);

        jendelaCetak.document.close();
        jendelaCetak.focus();

        setTimeout(() => {
            jendelaCetak.print();
            jendelaCetak.close();
        }, 600);
    });

    // ==========================================
    // BAGIAN 2: FILTER & PENCARIAN SURAT
    // ==========================================
    const cariInput = document.getElementById('cariSurat');
    const filterTanggal = document.getElementById('filterTanggal');
    const filterSelect = document.getElementById('filterKeterangan');

    const opsiFilter = {
        masuk: [
            { nilai: '', teks: 'Semua Status' },
            { nilai: 'Diproses', teks: 'Diproses' },
            { nilai: 'Selesai', teks: 'Selesai' }
        ],
        keluar: [
            { nilai: '', teks: 'Semua Sifat' },
            { nilai: 'Penting', teks: 'Penting' },
            { nilai: 'Biasa', teks: 'Biasa' }
        ]
    };

    // Fungsi ganti opsi dan perbarui tampilan custom select
    function gantiOpsiFilter(tabAktif) {
        // Kosongkan dan isi ulang opsi asli
        filterSelect.innerHTML = '';
        opsiFilter[tabAktif].forEach(item => {
            const opsi = document.createElement('option');
            opsi.value = item.nilai;
            opsi.textContent = item.teks;
            filterSelect.appendChild(opsi);
        });

        // 👇 INI BARU: Perbarui tampilan custom select setelah opsi berubah
        const wrapperSelect = filterSelect.closest('.custom-select');
        if (wrapperSelect && typeof wrapperSelect.populateOptions === 'function') {
            wrapperSelect.populateOptions();
        } else {
            // Jika fungsi belum tersedia, panggil ulang inisialisasi secara manual
            const customSelects = document.querySelectorAll('.custom-select');
            customSelects.forEach(sel => {
                if (sel === wrapperSelect) {
                    const event = new Event('change');
                    filterSelect.dispatchEvent(event);
                }
            });
        }
    }

    // Jalankan pertama kali
    gantiOpsiFilter('masuk');

    // Event saat pindah tab
    const tabElList = document.querySelectorAll('#tabSurat button[data-bs-toggle="tab"]');
    tabElList.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            cariInput.value = '';
            filterTanggal.value = '';
            gantiOpsiFilter(target === '#masuk' ? 'masuk' : 'keluar');
            filterTabel();
        });
    });

    // ==========================================
    // ATUR TOMBOL TAMBAH SESUAI TAB
    // ==========================================
    const btnTambah = document.getElementById('btnTambahSurat');

    function setUrlTambah(tab) {
        if (tab === 'masuk') {
            btnTambah.href = '/surat-menyurat/tambah-masuk';
            btnTambah.innerHTML = '<i class="fas fa-plus me-1"></i> Surat Masuk';
        } else {
            btnTambah.href = '/surat-menyurat/tambah-keluar';
            btnTambah.innerHTML = '<i class="fas fa-plus me-1"></i> Surat Keluar';
        }
    }

    // Atur awal
    setUrlTambah('masuk');

    // Ubah saat pindah tab
    tabElList.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            cariInput.value = '';
            filterTanggal.value = '';
            gantiOpsiFilter(target === '#masuk' ? 'masuk' : 'keluar');
            setUrlTambah(target === '#masuk' ? 'masuk' : 'keluar');
            filterTabel();
        });
    });

    // Fungsi utama filter
    function filterTabel() {
        const kataKunci = cariInput.value.toLowerCase().trim();
        const tanggal = filterTanggal.value;
        const nilaiFilter = filterSelect.value;

        const tabAktif = document.querySelector('.tab-pane.active');
        if (!tabAktif) return;

        const baris = tabAktif.querySelectorAll('tbody tr');
        baris.forEach(baris => {
            const teksBaris = baris.textContent.toLowerCase();
            const tglBaris = baris.querySelector('td:nth-child(3)')?.textContent.trim() || '';
            const keteranganBaris = baris.querySelector('.badge')?.textContent.trim() || '';

            const cocokKata = kataKunci === '' || teksBaris.includes(kataKunci);
            const cocokTanggal = tanggal === '' || tglBaris === tanggal;
            const cocokFilter = nilaiFilter === '' || keteranganBaris === nilaiFilter;

            baris.style.display = (cocokKata && cocokTanggal && cocokFilter) ? '' : 'none';
        });
    }

    // Jalankan filter saat ada perubahan
    cariInput.addEventListener('input', filterTabel);
    filterTanggal.addEventListener('change', filterTabel);
    filterSelect.addEventListener('change', filterTabel);

    // --- CETAK LANGSUNG DARI TABEL MELALUI MODAL YANG SUDAH ADA ---
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.btn-cetak-langsung');
        if (!btn) return;

        e.preventDefault();
        e.stopPropagation();

        // Ambil data persis seperti tombol "Lihat"
        const nomor = btn.dataset.nomor || '';
        const tanggal = ubahTanggalKeBahasaIndonesia(btn.dataset.tanggal || '');
        const tujuan = btn.dataset.tujuan || '';
        const lampiran = btn.dataset.lampiran || '-';
        const perihal = btn.dataset.perihal || '';
        const isi = JSON.parse(btn.dataset.isi || '""');
        const daftarTtd = JSON.parse(btn.dataset.ttd || '[]');

        // Susun konten surat SAMA PERSIS seperti di modal
        const htmlSurat = `
        <!-- KOP SURAT -->
        <div class="kop-surat">
            <div class="kop-konten">
            <img src="/static/img/logo-school.svg" alt="Logo SMP Unggulan Hamzanwadi" class="kop-logo">
            
            <div class="kop-pemisah"></div>

            <div class="kop-teks-kanan">
                <div class="kop-izin">IZIN OPERASIONAL: 500.16.7.2/97/PMPTSP-SMP/01/2025</div>
                <div class="kop-kontak">
                <i class="fa-brands fa-whatsapp-square"></i>
                <span>081915780964</span>
                <i class="fa-solid fa-envelope"></i>
                <span>smpu@hamzanwadi.ac.id</span>
                </div>
                <div class="kop-alamat">Jl. Dr. Ciptromangun Kusumo, Sawing, Kel. Majidi, Kec. Selong, Kab. Lombok Timur - NTB</div>
            </div>
            </div>
        </div>

        <!-- ISI SURAT -->
        <div class="surat-kepala">
            <span class="label">Nomor</span>
            <span class="value">: ${nomor}</span>

            <span class="label">Lampiran</span>
            <span class="value">: ${lampiran}</span>

            <span class="label">Hal</span>
            <span class="value">: <strong>${perihal}</strong></span>
        </div>

        <div class="surat-tujuan">
            <p>${tujuan.replace(/^(Kepada\s*\n?\s*Yth\.\s*)([\s\S]*?)(\n\s*di\s+[\s\S]*)$/s, '$1<strong>$2</strong>$3')}</p>
        </div>

        <div class="surat-isi">
            <p><strong><em>Bismillahiwabihamdihi</em></strong></p>
            <p class="salam"><em><strong>Assalamu'alaikum Warahmatullahi Wabarakatuh</em></strong></p>
            <p>Semoga kami menjumpai Bapak/Ibu dalam keadaan sehat wal'afiat serta dalam limpahan Rahmat dan taufik dari Allah SWT. sehingga dapat beraktivitas seperti biasanya. Aamiin ya Rabbal Alamin.</p>
            <p class="isi">${isi}</p>
            <p class="wassalam"><strong><em>Wallohul Muwaffiq Wal Hadi ila Sabi Lirrosyad</em></strong></p>
            <p><strong><em>Wassalamu'alaikum Warahmatullahi Wabarakatuh</em></strong></p>
        </div>

        <!-- TANDA TANGAN + QR SESUAI FORMAT -->
        <div class="surat-ttd" style="color: black;">
            <p style="text-align: right; margin: 1rem 0 0;">
                Majidi, ${tanggal}
            </p>
            ${(() => {
                // ✅ Gunakan data yang sudah diambil dari tombol
                const daftarTtd = JSON.parse(btn.dataset.ttd || '[]');
                const jumlah = daftarTtd.length;
                // Cari posisi Kepala Sekolah
                const posisiKepala = daftarTtd.findIndex(t => t.jabatan?.trim().toLowerCase() === 'kepala sekolah');
                const adaKepala = posisiKepala !== -1;

                function buatBlokTtd(ttd) {
                    const sudahTtd = ttd.ttd_selesai === true;
                    const qr = sudahTtd && ttd.qr_code 
                        ? `
                            <div class="qr-verifikasi" style="margin: 0 auto; text-align: center;">
                                <img src="/static/${ttd.qr_code}" alt="QR Verifikasi Elektronik" style="width: 80px; height: 80px; object-fit: contain;">
                                <p style="font-size: 8pt; margin:0; color: #333;">Ditandatangani secara elektronik</p>
                            </div>
                        ` 
                        : `<p style="font-size: 9pt; color: #888; margin: 0 auto;">Belum ditandatangani</p>`;

                    return `
                        <div style="text-align: center;">
                            <p style="margin: 0 0 0.75rem 0;">${ttd.jabatan || ''}</p>
                            ${qr}
                            <p style="margin: 0;"><strong>${ttd.nama || ''}</strong></p>
                            <p style="margin: 0;">NIP. ${ttd.nip || '-'}</p>
                        </div>
                    `;
                }

                let htmlTtd = '';

                if (jumlah === 1) {
                    htmlTtd = `<div style="margin-left: 65%; text-align: left; width: max-content;">${buatBlokTtd(daftarTtd[0])}</div>`;
                } 
                else if (jumlah === 2) {
                    if (adaKepala) {
                        if (posisiKepala === 0) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                            `;
                        } else {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                            `;
                        }
                    } else {
                        htmlTtd = `
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                            </div>
                        `;
                    }
                } 
                else if (jumlah === 3) {
                    if (adaKepala) {
                        if (posisiKepala === 0) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                            `;
                        } else if (posisiKepala === 1) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                            `;
                        } else if (posisiKepala === 2) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="width: 100%; text-align: center; margin-top: 1rem;">
                                    <p style="margin: 0;">Mengetahui,</p>
                                    ${buatBlokTtd(daftarTtd[2])}
                                </div>
                            `;
                        }
                    } else {
                        htmlTtd = `
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                            </div>
                            <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                        `;
                    }
                } 
                else if (jumlah === 4) {
                    if (adaKepala) {
                        if (posisiKepala === 0) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        } else if (posisiKepala === 1) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        } else if (posisiKepala === 2) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1rem;">
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        } else if (posisiKepala === 3) {
                            htmlTtd = `
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1rem;">
                                    <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                    <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                </div>
                                <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                    <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                </div>
                            `;
                        }
                    } else {
                        htmlTtd = `
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                            </div>
                            <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1.5rem;">
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                            </div>
                        `;
                    }
                }

                return htmlTtd;
            })()}
        </div>
        `;

        // Isi konten ke elemen modal (tanpa menampilkannya ke pengguna)
        document.getElementById('kontenSuratLengkap').innerHTML = htmlSurat;

        // --- BAGIAN INI YANG DIMATIKAN: JANGAN BUKA MODAL ---
        // const modal = new bootstrap.Modal(document.getElementById('modalLihatSurat'));
        // modal.show();

        // Jalankan fungsi cetak yang SAMA PERSIS seperti tombol di modal
        setTimeout(() => {
            document.getElementById('btnCetakDariModal').click();
        }, 300);
    });
});