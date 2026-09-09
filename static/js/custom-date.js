/* ==========================================
   CUSTOM DATE & DATETIME PICKER
   ✅ BISA DIKETIK LANGSUNG + PANAH TETAP ADA
   ✅ INPUT TETAP KOSONG SAAT PERTAMA
   ✅ KALENDER LANGSUNG KE TANGGAL MULAI SAAT DIBUKA
========================================== */

document.addEventListener('DOMContentLoaded', function() {
    const customDateWrappers = document.querySelectorAll('.custom-date');
    let activeCalendar = null;
    let currentView = 'days';
    let yearRangeStart = new Date().getFullYear() - 10;

    const bulanNama = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ];

    customDateWrappers.forEach(wrapper => {
        const existingTrigger = wrapper.querySelector('.custom-date__trigger');
        if (existingTrigger) existingTrigger.remove();

        const originalInput = wrapper.querySelector('input');
        const isDateTime = originalInput.type === 'datetime-local';

        originalInput.style.opacity = '0';
        originalInput.style.position = 'absolute';
        originalInput.style.pointerEvents = 'none';
        originalInput.tabIndex = -1;

        let currentDate = new Date();
        let selectedDate = null;

        // Baca nilai lama jika ada
        if (originalInput.value) {
            selectedDate = new Date(originalInput.value);
            if (isNaN(selectedDate.getTime())) selectedDate = null;
        }

        // Buat elemen
        const trigger = document.createElement('div');
        const inputManual = document.createElement('input');
        const icon = document.createElement('i');

        trigger.className = 'custom-date__trigger';
        inputManual.className = 'custom-date__input-manual';
        inputManual.type = 'text';
        inputManual.placeholder = isDateTime ? 'dd/mm/yyyy HH:MM' : 'dd/mm/yyyy';
        inputManual.tabIndex = 0;
        icon.className = 'fa fa-calendar custom-date__icon';
        icon.tabIndex = -1;

        trigger.append(inputManual, icon);
        wrapper.append(trigger);

        // --- Format tampilan ---
        function formatToDisplay(date) {
            if (!date || isNaN(date.getTime())) return '';
            const d = String(date.getDate()).padStart(2, '0');
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const y = date.getFullYear();
            if (isDateTime) {
                const h = String(date.getHours()).padStart(2, '0');
                const min = String(date.getMinutes()).padStart(2, '0');
                return `${d}/${m}/${y} ${h}:${min}`;
            }
            return `${d}/${m}/${y}`;
        }

        // --- Format simpan ---
        function formatToSave(str) {
            if (!str) return '';
            let datePart, timePart = '00:00';
            if (isDateTime) {
                const parts = str.trim().split(' ');
                if (parts.length === 2) {
                    datePart = parts[0];
                    timePart = parts[1];
                } else {
                    datePart = str.trim();
                }
            } else {
                datePart = str.trim();
            }

            const tgl = datePart.split('/');
            if (tgl.length !== 3) return '';
            const d = parseInt(tgl[0]), m = parseInt(tgl[1]), y = parseInt(tgl[2]);
            if (!d || !m || !y || m < 1 || m > 12 || d < 1 || d > 31) return '';

            const jam = timePart.split(':');
            const h = jam[0] ? parseInt(jam[0]) : 0;
            const min = jam[1] ? parseInt(jam[1]) : 0;
            if (h < 0 || h > 23 || min < 0 || min > 59) return '';

            if (!isDateTime) {
                return `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            }
            return `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}T${String(h).padStart(2,'0')}:${String(min).padStart(2,'0')}`;
        }

        function updateDisplay() {
            inputManual.value = formatToDisplay(selectedDate);
            if (selectedDate) {
                const y = selectedDate.getFullYear();
                const m = String(selectedDate.getMonth() + 1).padStart(2, '0');
                const d = String(selectedDate.getDate()).padStart(2, '0');
                if (!isDateTime) {
                    originalInput.value = `${y}-${m}-${d}`;
                } else {
                    const h = String(selectedDate.getHours()).padStart(2, '0');
                    const min = String(selectedDate.getMinutes()).padStart(2, '0');
                    originalInput.value = `${y}-${m}-${d}T${h}:${min}`;
                }
            } else {
                originalInput.value = '';
            }
        }

        // --- Render Kalender ---
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

            if (isDateTime) {
                const sekarang = new Date();
                const currentHour = selectedDate ? selectedDate.getHours() : sekarang.getHours();
                const currentMinute = selectedDate ? selectedDate.getMinutes() : sekarang.getMinutes();
                html += `
                    <div class="calendar-time mt-2 pt-2 border-top">
                        <label class="form-label small">Pukul</label>
                        <div class="d-flex gap-2 align-items-center">
                            <div class="time-input-wrapper" style="position:relative; flex:1;">
                                <input type="text" inputmode="numeric" maxlength="2" value="${String(currentHour).padStart(2,'0')}" 
                                    class="form-control form-control-sm time-hour" placeholder="Jam"
                                    style="padding-right:18px;">
                                <div class="time-arrows" style="position:absolute;right:4px;top:0;height:100%;display:flex;flex-direction:column;justify-content:center;pointer-events:auto;">
                                    <button type="button" class="time-up" style="border:none;background:transparent;padding:0 2px 0 0;font-size:10px;line-height:1em;color:#666;margin-top:-2px;">▲</button>
                                    <button type="button" class="time-down" style="border:none;background:transparent;padding:0 2px 0 0;font-size:10px;line-height:1em;color:#666;margin-top:-2px;">▼</button>
                                </div>
                            </div>
                            <span>:</span>
                            <div class="time-input-wrapper" style="position:relative; flex:1;">
                                <input type="text" inputmode="numeric" maxlength="2" value="${String(currentMinute).padStart(2,'0')}" 
                                    class="form-control form-control-sm time-minute" placeholder="Menit"
                                    style="padding-right:18px;">
                                <div class="time-arrows" style="position:absolute;right:4px;top:0;height:100%;display:flex;flex-direction:column;justify-content:center;pointer-events:auto;">
                                    <button type="button" class="time-up" style="border:none;background:transparent;padding:0 2px 0 0;font-size:10px;line-height:1em;color:#666;margin-top:-2px;">▲</button>
                                    <button type="button" class="time-down" style="border:none;background:transparent;padding:0 2px 0 0;font-size:10px;line-height:1em;color:#666;margin-top:-2px;">▼</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

            activeCalendar.innerHTML = html;

            activeCalendar.querySelector('.prev').addEventListener('click', e => {
                e.stopPropagation();
                currentDate.setMonth(currentDate.getMonth() - 1);
                renderDays();
            });

            activeCalendar.querySelector('.next').addEventListener('click', e => {
                e.stopPropagation();
                currentDate.setMonth(currentDate.getMonth() + 1);
                renderDays();
            });

            activeCalendar.querySelector('.calendar-title').addEventListener('click', e => {
                e.stopPropagation();
                renderMonths();
            });

            if (isDateTime) {
                const hourInput = activeCalendar.querySelector('.time-hour');
                const minuteInput = activeCalendar.querySelector('.time-minute');
                const hourUp = activeCalendar.querySelectorAll('.time-up')[0];
                const hourDown = activeCalendar.querySelectorAll('.time-down')[0];
                const minUp = activeCalendar.querySelectorAll('.time-up')[1];
                const minDown = activeCalendar.querySelectorAll('.time-down')[1];

                // Fungsi normalisasi & simpan
                const normalisasiJam = () => {
                    let val = hourInput.value.replace(/\D/g, '');
                    if (val === '') val = '0';
                    let num = parseInt(val);
                    if (num > 23) num = 23;
                    if (num < 0) num = 0;
                    hourInput.value = String(num).padStart(2, '0');
                    if (selectedDate) {
                        selectedDate.setHours(num);
                        updateDisplay();
                    }
                    return num;
                };

                const normalisasiMenit = () => {
                    let val = minuteInput.value.replace(/\D/g, '');
                    if (val === '') val = '0';
                    let num = parseInt(val);
                    if (num > 59) num = 59;
                    if (num < 0) num = 0;
                    minuteInput.value = String(num).padStart(2, '0');
                    if (selectedDate) {
                        selectedDate.setMinutes(num);
                        updateDisplay();
                    }
                    return num;
                };

                // Panah naik turun Jam
                hourUp.addEventListener('click', e => {
                    e.stopPropagation();
                    let h = parseInt(hourInput.value) || 0;
                    h = h >= 23 ? 0 : h + 1;
                    hourInput.value = String(h).padStart(2, '0');
                    if (selectedDate) { selectedDate.setHours(h); updateDisplay(); }
                });
                hourDown.addEventListener('click', e => {
                    e.stopPropagation();
                    let h = parseInt(hourInput.value) || 0;
                    h = h <= 0 ? 23 : h - 1;
                    hourInput.value = String(h).padStart(2, '0');
                    if (selectedDate) { selectedDate.setHours(h); updateDisplay(); }
                });

                // Panah naik turun Menit
                minUp.addEventListener('click', e => {
                    e.stopPropagation();
                    let m = parseInt(minuteInput.value) || 0;
                    m = m >= 59 ? 0 : m + 1;
                    minuteInput.value = String(m).padStart(2, '0');
                    if (selectedDate) { selectedDate.setMinutes(m); updateDisplay(); }
                });
                minDown.addEventListener('click', e => {
                    e.stopPropagation();
                    let m = parseInt(minuteInput.value) || 0;
                    m = m <= 0 ? 59 : m - 1;
                    minuteInput.value = String(m).padStart(2, '0');
                    if (selectedDate) { selectedDate.setMinutes(m); updateDisplay(); }
                });

                // Bisa diketik langsung — simpan saat selesai
                hourInput.addEventListener('blur', normalisasiJam);
                minuteInput.addEventListener('blur', normalisasiMenit);

                // Pindah tekan Enter
                hourInput.addEventListener('keydown', e => {
                    if (e.key === 'Enter') { e.preventDefault(); minuteInput.focus(); }
                });
                minuteInput.addEventListener('keydown', e => {
                    if (e.key === 'Enter') { e.preventDefault(); minuteInput.blur(); }
                });
            }

            // Batas tanggal
            const batasMinKal = originalInput.min ? new Date(originalInput.min) : null;
            const batasMaxKal = originalInput.max ? new Date(originalInput.max) : null;

            activeCalendar.querySelectorAll('.calendar-day:not(.other-month)').forEach(dayEl => {
                const day = parseInt(dayEl.dataset.day);
                const tanggalPilih = new Date(year, month, day);
                const diLuarRentang = (batasMinKal && tanggalPilih < batasMinKal) || (batasMaxKal && tanggalPilih > batasMaxKal);

                if (diLuarRentang) {
                    dayEl.classList.add('other-month');
                    dayEl.style.cursor = 'not-allowed';
                } else {
                    dayEl.addEventListener('click', e => {
                        e.stopPropagation();
                        let h = 0, m = 0;
                        if (isDateTime) {
                            h = parseInt(activeCalendar.querySelector('.time-hour').value) || new Date().getHours();
                            m = parseInt(activeCalendar.querySelector('.time-minute').value) || new Date().getMinutes();
                        }
                        selectedDate = new Date(year, month, day, h, m);
                        originalInput.value = formatToSave(formatToDisplay(selectedDate));
                        originalInput.dispatchEvent(new Event('change'));
                        updateDisplay();
                        closeCalendar();
                    });
                }
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

            activeCalendar.querySelector('.prev').addEventListener('click', e => {
                e.stopPropagation();
                currentDate.setFullYear(currentDate.getFullYear() - 1);
                renderMonths();
            });
            activeCalendar.querySelector('.next').addEventListener('click', e => {
                e.stopPropagation();
                currentDate.setFullYear(currentDate.getFullYear() + 1);
                renderMonths();
            });
            activeCalendar.querySelector('.calendar-title').addEventListener('click', e => {
                e.stopPropagation();
                renderYears();
            });
            activeCalendar.querySelectorAll('.month-item').forEach(monthEl => {
                monthEl.addEventListener('click', e => {
                    e.stopPropagation();
                    currentDate.setMonth(parseInt(monthEl.dataset.month));
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

            activeCalendar.querySelector('.prev').addEventListener('click', e => {
                e.stopPropagation();
                yearRangeStart -= 10;
                renderYears();
            });
            activeCalendar.querySelector('.next').addEventListener('click', e => {
                e.stopPropagation();
                yearRangeStart += 10;
                renderYears();
            });
            activeCalendar.querySelectorAll('.year-item').forEach(yearEl => {
                yearEl.addEventListener('click', e => {
                    e.stopPropagation();
                    currentDate.setFullYear(parseInt(yearEl.dataset.year));
                    renderMonths();
                });
            });
        }

        function openCalendar() {
            if (!activeCalendar) {
                activeCalendar = document.createElement('div');
                activeCalendar.className = 'custom-date__calendar';
                // ✅ TARUH DI DALAM .custom-date BUKAN DI <body>
                wrapper.appendChild(activeCalendar);
            }

            // ❌ HAPUS window.scrollY / scrollX — biarkan posisi terhadap induk
            const rect = trigger.getBoundingClientRect();
            const wrapperRect = wrapper.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            const calendarHeight = isDateTime ? 320 : 280;
            const calendarWidth = 260;
            const margin = 4;

            const spaceBelow = windowHeight - rect.bottom;
            let topPos;

            // ✅ Hitung posisi RELATIF ke wrapper, BUKAN ke halaman
            if (spaceBelow >= calendarHeight + margin) {
                // Buka DI BAWAH
                topPos = rect.bottom - wrapperRect.top + margin;
                activeCalendar.style.removeProperty('bottom');
            } else {
                // Buka DI ATAS
                topPos = 'auto';
                activeCalendar.style.bottom = (wrapperRect.bottom - rect.top + margin) + 'px';
            }

            activeCalendar.style.left = '0'; // ✅ Rata kiri dengan input
            activeCalendar.style.top = typeof topPos === 'number' ? `${topPos}px` : topPos;
            activeCalendar.classList.add('open');
            wrapper.classList.add('open');

            const batasMinOpen = originalInput.min ? new Date(originalInput.min) : null;
            if (!selectedDate && batasMinOpen) {
                currentDate = new Date(batasMinOpen);
            } else {
                currentDate = selectedDate ? new Date(selectedDate) : new Date();
            }
            yearRangeStart = Math.floor(currentDate.getFullYear() / 10) * 10;
            renderDays();
        }

        window.closeCalendar = function() {
            if (activeCalendar) activeCalendar.classList.remove('open');
            document.querySelectorAll('.custom-date').forEach(el => el.classList.remove('open', 'focused'));
            currentView = 'days';
        };

        inputManual.addEventListener('input', e => {
            let value = e.target.value.replace(/\D/g, '');
            if (isDateTime) {
                if (value.length > 12) value = value.slice(0,12);
                if (value.length >= 2) value = value.slice(0,2) + '/' + value.slice(2);
                if (value.length >= 5) value = value.slice(0,5) + '/' + value.slice(5);
                if (value.length >= 8) value = value.slice(0,8) + ' ' + value.slice(8);
                if (value.length >= 11) value = value.slice(0,11) + ':' + value.slice(11);
            } else {
                if (value.length > 8) value = value.slice(0,8);
                if (value.length >= 2) value = value.slice(0,2) + '/' + value.slice(2);
                if (value.length >= 5) value = value.slice(0,5) + '/' + value.slice(5);
            }
            e.target.value = value;
        });

        inputManual.addEventListener('blur', () => {
            const str = inputManual.value.trim();
            const valid = formatToSave(str);
            if (valid) {
                originalInput.value = valid;
                selectedDate = new Date(valid);
            } else {
                originalInput.value = '';
                selectedDate = null;
            }
            updateDisplay();
            wrapper.classList.remove('focused');
        });

        originalInput.addEventListener('change', () => {
            if (originalInput.value) {
                selectedDate = new Date(originalInput.value);
                if (isNaN(selectedDate.getTime())) selectedDate = new Date();
            } else {
                selectedDate = null;
            }
            updateDisplay();
        });

        inputManual.addEventListener('focus', () => wrapper.classList.add('focused'));

        icon.addEventListener('click', e => {
            e.stopPropagation();
            activeCalendar?.classList.contains('open') ? closeCalendar() : openCalendar();
        });

        document.addEventListener('click', e => {
            if (!wrapper.contains(e.target) && !activeCalendar?.contains(e.target)) closeCalendar();
        });

        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') closeCalendar();
        });

        updateDisplay();
    });
});