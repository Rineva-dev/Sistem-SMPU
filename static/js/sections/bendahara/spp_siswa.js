(() => {
    'use strict';

    const GLOBAL_KEY = 'SPPPremiumV3';

    if (window[GLOBAL_KEY]) {
        window[GLOBAL_KEY].init();
        return;
    }

    const instances = new Map();

    const rupiahFormatter = new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });

    const rupiah = value =>
        rupiahFormatter.format(value).replace(/\s+/g, ' ');

    const escapeHTML = value =>
        String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[character]));

    function parseMoney(value) {
        if (typeof value === 'number') {
            return Number.isFinite(value) ? value : 0;
        }

        let text = String(value ?? '').trim();

        const lokal =
            /rp|,|\s/i.test(text) ||
            /^-?\d{1,3}(\.\d{3})+$/.test(text);

        text = text.replace(/rp|\s/gi, '');

        if (lokal) {
            text = text.replace(/\./g, '').replace(',', '.');
        }

        const number = Number(text);

        return Number.isFinite(number) ? number : 0;
    }

    function localDateTime() {
        const now = new Date();
        const pad = value => String(value).padStart(2, '0');

        return (
            `${now.getFullYear()}-` +
            `${pad(now.getMonth() + 1)}-` +
            `${pad(now.getDate())}T` +
            `${pad(now.getHours())}:` +
            `${pad(now.getMinutes())}`
        );
    }

    function allocate(bills, selected, amount) {
        let available = amount;

        return bills
            .filter(bill => selected.has(bill.id))
            .map(bill => {
                const paid = Math.min(
                    available,
                    bill.remaining
                );

                available -= paid;

                return {
                    id: bill.id,
                    nominal_asli: bill.nominal,
                    dibayar: paid,
                    sisa_hutang: bill.remaining - paid
                };
            });
    }

    function mount(root) {
        if (instances.has(root)) return;

        const $ = role =>
            root.querySelector(`[data-role="${role}"]`);

        const events = new AbortController();

        const on = (element, event, handler) => {
            element.addEventListener(event, handler, {
                signal: events.signal
            });
        };

        const reducedMotion = window.matchMedia(
            '(prefers-reduced-motion: reduce)'
        ).matches;

        const frames = new Set();

        let toastTimer;
        let requestController;
        let requestSequence = 0;
        let focusBefore;

        let statusFilter = '';
        let page = 1;
        let filteredRows = [];

        let bills = [];
        let selected = new Set();
        let amount = 0;

        let loading = false;
        let saving = false;
        let uncertain = false;

        const dialog = $('dialog');

        const rows = [
            ...root.querySelectorAll('[data-student-row]')
        ];

        const studentOptions = [
            ...$('student').options
        ].slice(1).map(option => ({
            value: option.value,
            name: option.dataset.name || '',
            nisn: option.dataset.nisn || '',
            className: option.dataset.class || '-',
            label: option.textContent.trim()
        }));

        instances.set(root, {
            destroy() {
                requestSequence++;
                requestController?.abort();
                events.abort();

                clearTimeout(toastTimer);

                frames.forEach(id => {
                    cancelAnimationFrame(id);
                });

                frames.clear();

                if (dialog.open) {
                    dialog.close();
                }

                instances.delete(root);
            }
        });

        function frame(callback) {
            const id = requestAnimationFrame(time => {
                frames.delete(id);
                callback(time);
            });

            frames.add(id);
        }

        function animateValue(element, target, format) {
            if (reducedMotion || !Number.isFinite(target)) {
                element.textContent = format(target);
                return;
            }

            const start = performance.now();
            const duration = 1050;

            function tick(time) {
                if (!root.isConnected) return;

                const progress = Math.min(
                    (time - start) / duration,
                    1
                );

                const eased = 1 - Math.pow(1 - progress, 4);

                element.textContent = format(target * eased);

                if (progress < 1) {
                    frame(tick);
                } else {
                    element.textContent = format(target);
                }
            }

            frame(tick);
        }

        function toast(text) {
            clearTimeout(toastTimer);

            $('toast').textContent = text;
            $('toast').hidden = false;

            toastTimer = setTimeout(() => {
                $('toast').hidden = true;
            }, 4500);
        }

        function message(text = '', type = '') {
            $('message').hidden = !text;
            $('message').textContent = text;

            $('message').className =
                `s3-form-message ${type ? `is-${type}` : ''}`;
        }

        /* ================================================
           INITIAL DATA AND OVERVIEW
        ================================================ */

        let sumTotal = 0;
        let sumPaid = 0;
        let sumRemaining = 0;
        let countPaid = 0;

        rows.forEach(row => {
            const total = parseMoney(row.dataset.total);
            const paid = parseMoney(row.dataset.paid);
            const remaining = parseMoney(row.dataset.remaining);

            sumTotal += total;
            sumPaid += paid;
            sumRemaining += remaining;

            const isPaid = remaining <= 0;

            if (isPaid) countPaid++;

            row.dataset.status = isPaid
                ? 'paid'
                : 'unpaid';

            const badge = row.querySelector(
                '[data-row-status]'
            );

            badge.className =
                `s3-badge is-${row.dataset.status}`;

            badge.textContent = isPaid
                ? 'Lunas'
                : 'Belum lunas';

            row.querySelectorAll('[data-money]')
                .forEach(cell => {
                    cell.textContent = rupiah(
                        parseMoney(
                            row.dataset[cell.dataset.money]
                        )
                    );
                });
        });

        const countTotal = rows.length;
        const countUnpaid = countTotal - countPaid;

        const percentage = countTotal
            ? countPaid / countTotal * 100
            : 0;

        const wholeNumber = value =>
            Math.round(value).toLocaleString('id-ID');

        const percentNumber = value =>
            value.toLocaleString('id-ID', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 1
            });

        animateValue(
            $('count-total'),
            countTotal,
            wholeNumber
        );

        animateValue(
            $('count-paid'),
            countPaid,
            wholeNumber
        );

        animateValue(
            $('count-unpaid'),
            countUnpaid,
            wholeNumber
        );

        animateValue(
            $('percentage'),
            percentage,
            percentNumber
        );

        animateValue(
            $('money-paid'),
            sumPaid,
            value => rupiah(Math.round(value))
        );

        $('money-total').textContent = rupiah(sumTotal);
        $('money-remaining').textContent = rupiah(sumRemaining);

        $('tab-total').textContent = wholeNumber(countTotal);
        $('tab-paid').textContent = wholeNumber(countPaid);
        $('tab-unpaid').textContent = wholeNumber(countUnpaid);

        $('progress-caption').textContent =
            `${wholeNumber(countPaid)} dari ` +
            `${wholeNumber(countTotal)} siswa telah lunas`;

        frame(() => {
            frame(() => {
                $('donut').style.strokeDashoffset =
                    String(100 - percentage);
            });
        });

        [...new Set(
            rows.map(row => row.dataset.class)
        )]
            .sort((a, b) =>
                a.localeCompare(b, 'id', {
                    numeric: true
                })
            )
            .forEach(name => {
                $('class').add(
                    new Option(name, name)
                );
            });

        /* ================================================
           FILTERS AND PAGINATION
        ================================================ */

        function filter(resetPage = true) {
            if (resetPage) page = 1;

            const query = $('search')
                .value
                .trim()
                .toLocaleLowerCase('id');

            const className = $('class').value;

            filteredRows = rows.filter(row => {
                const identity =
                    `${row.dataset.name} ${row.dataset.nisn}`
                        .toLocaleLowerCase('id');

                return (
                    (!query || identity.includes(query)) &&
                    (!className || row.dataset.class === className) &&
                    (!statusFilter || row.dataset.status === statusFilter)
                );
            });

            const size = Number($('page-size').value);

            const pageCount = Math.max(
                1,
                Math.ceil(filteredRows.length / size)
            );

            page = Math.min(
                Math.max(1, page),
                pageCount
            );

            rows.forEach(row => {
                row.hidden = true;
            });

            filteredRows
                .slice((page - 1) * size, page * size)
                .forEach(row => {
                    row.hidden = false;
                });

            $('empty').hidden = filteredRows.length > 0;

            $('count').textContent = filteredRows.length
                ? (
                    `${(page - 1) * size + 1}–` +
                    `${Math.min(page * size, filteredRows.length)} ` +
                    `dari ${filteredRows.length} siswa`
                )
                : '0 siswa ditemukan';

            $('page').textContent = `${page} / ${pageCount}`;

            root.querySelector(
                '[data-action="prev"]'
            ).disabled = page <= 1;

            root.querySelector(
                '[data-action="next"]'
            ).disabled = page >= pageCount;

            root.querySelectorAll('[data-status-filter]')
                .forEach(button => {
                    const active =
                        button.dataset.statusFilter === statusFilter;

                    button.classList.toggle(
                        'is-active',
                        active
                    );

                    button.setAttribute(
                        'aria-pressed',
                        String(active)
                    );
                });

            const descriptions = [];

            if (statusFilter) {
                descriptions.push(
                    statusFilter === 'paid'
                        ? 'Status: lunas'
                        : 'Status: belum lunas'
                );
            }

            if (className) {
                descriptions.push(`Kelas: ${className}`);
            }

            if (query) {
                descriptions.push(
                    `Pencarian: ${$('search').value.trim()}`
                );
            }

            $('filter-note').textContent = descriptions.length
                ? descriptions.join(' · ')
                : 'Menampilkan seluruh siswa';
        }

        on($('search'), 'input', () => filter());
        on($('class'), 'change', () => filter());
        on($('page-size'), 'change', () => filter());

        function showUnpaid() {
            statusFilter = 'unpaid';
            filter();

            $('directory').scrollIntoView({
                behavior: reducedMotion ? 'auto' : 'smooth',
                block: 'start'
            });
        }

        on(document, 'keydown', event => {
            const target = event.target;

            const editing =
                target instanceof Element &&
                (
                    target.matches('input, textarea, select') ||
                    target.isContentEditable
                );

            if (
                event.key === '/' &&
                !event.ctrlKey &&
                !event.metaKey &&
                !event.altKey &&
                !editing &&
                !dialog.open &&
                root.isConnected
            ) {
                event.preventDefault();
                $('search').focus();
            }
        });

        /* ================================================
           STUDENT SEARCH
        ================================================ */

        function searchStudents() {
            const query = $('student-search')
                .value
                .trim()
                .toLocaleLowerCase('id');

            const currentValue = $('student').value;

            const found = studentOptions.filter(option => {
                return `${option.name} ${option.nisn}`
                    .toLocaleLowerCase('id')
                    .includes(query);
            });

            const current = studentOptions.find(
                option => option.value === currentValue
            );

            const visible =
                current && !found.includes(current)
                    ? [current, ...found]
                    : found;

            $('student').replaceChildren(
                new Option('Pilih siswa', '')
            );

            visible.forEach(item => {
                $('student').add(
                    new Option(item.label, item.value)
                );
            });

            $('student').value = currentValue;

            $('student-count').textContent =
                `${found.length} siswa sesuai pencarian`;
        }

        on(
            $('student-search'),
            'input',
            searchStudents
        );

        /* ================================================
           PAYMENT STATE
        ================================================ */

        function showEmpty(
            title = 'Mulai dengan memilih siswa',
            description = 'Daftar tagihan akan ditampilkan di sini.'
        ) {
            $('bills').innerHTML = `
                <div class="s3-empty s3-bill-empty">
                    <span class="s3-empty-symbol" aria-hidden="true">▤</span>
                    <strong>${escapeHTML(title)}</strong>
                    <p>${escapeHTML(description)}</p>
                </div>
            `;
        }

        function selectedTotal() {
            return bills.reduce((sum, bill) => {
                return sum + (
                    selected.has(bill.id)
                        ? bill.remaining
                        : 0
                );
            }, 0);
        }

        function recalculate() {
            const total = selectedTotal();

            if (amount > total) {
                amount = total;

                $('amount').value = amount
                    ? rupiah(amount)
                    : '';

                message(
                    'Nominal disesuaikan dengan total tagihan terpilih.'
                );
            }

            if (total === 0) {
                amount = 0;
                $('amount').value = '';
            }

            $('selected-total').textContent = rupiah(total);
            $('selected-count').textContent =
                `${selected.size} tagihan dipilih`;

            $('allocated').textContent = rupiah(amount);
            $('remaining').textContent = rupiah(total - amount);

            $('payment-fields').disabled =
                !total || saving || uncertain;

            $('save').disabled =
                !total ||
                amount <= 0 ||
                loading ||
                saving ||
                uncertain ||
                !$('method').value ||
                !$('date').value ||
                !$('date').validity.valid;

            const allocations = new Map(
                allocate(bills, selected, amount)
                    .map(item => [
                        String(item.id),
                        item
                    ])
            );

            root.querySelectorAll('[data-bill-status]')
                .forEach(element => {
                    const item = allocations.get(
                        element.dataset.billStatus
                    );

                    let text = 'Belum dialokasikan';
                    let kind = '';

                    if (item?.dibayar > 0) {
                        const full = item.sisa_hutang === 0;

                        text = full
                            ? 'Akan lunas'
                            : 'Dibayar sebagian';

                        kind = full
                            ? 'paid'
                            : 'unpaid';
                    }

                    element.textContent = text;
                    element.className =
                        `s3-badge s3-bill-status ${kind ? `is-${kind}` : ''}`;

                    const detail = element.parentElement
                        .querySelector('[data-allocation]');

                    detail.textContent = item?.dibayar > 0
                        ? (
                            `${rupiah(item.dibayar)} dialokasikan · ` +
                            `Sisa ${rupiah(item.sisa_hutang)}`
                        )
                        : '';
                });

            root.querySelectorAll('[data-bill-check]')
                .forEach(input => {
                    input.checked = selected.has(
                        input.dataset.billCheck
                    );
                });

            root.querySelectorAll('[data-group-check]')
                .forEach(input => {
                    const group = bills.filter(
                        bill => bill.group === Number(
                            input.dataset.groupCheck
                        )
                    );

                    const checkedCount = group.filter(
                        bill => selected.has(bill.id)
                    ).length;

                    input.checked =
                        checkedCount > 0 &&
                        checkedCount === group.length;

                    input.indeterminate =
                        checkedCount > 0 &&
                        checkedCount < group.length;
                });

            $('all').checked =
                bills.length > 0 &&
                selected.size === bills.length;

            $('all').indeterminate =
                selected.size > 0 &&
                selected.size < bills.length;

            const step = selected.size
                ? 3
                : $('student').value
                    ? 2
                    : 1;

            root.querySelectorAll('[data-step]')
                .forEach(element => {
                    const active =
                        Number(element.dataset.step) === step;

                    element.classList.toggle(
                        'is-active',
                        active
                    );

                    if (active) {
                        element.setAttribute(
                            'aria-current',
                            'step'
                        );
                    } else {
                        element.removeAttribute('aria-current');
                    }
                });
        }

        /* ================================================
           BILL RENDER
        ================================================ */

        function renderBills() {
            if (!bills.length) {
                showEmpty(
                    'Semua tagihan sudah lunas',
                    'Tidak ada tagihan yang perlu dibayarkan.'
                );

                return;
            }

            const groups = new Map();

            bills.forEach(bill => {
                if (!groups.has(bill.group)) {
                    groups.set(bill.group, []);
                }

                groups.get(bill.group).push(bill);
            });

            $('bills').innerHTML = [...groups]
                .map(([groupId, group]) => {
                    const items = group.map((bill, index) => {
                        const inputId =
                            `s3-bill-${groupId}-${index}`;

                        return `
                            <div class="s3-bill-row">
                                <input
                                    type="checkbox"
                                    id="${inputId}"
                                    data-bill-check="${escapeHTML(bill.id)}"
                                    aria-label="Pilih ${escapeHTML(bill.name)} ${escapeHTML(bill.description)}"
                                >

                                <div>
                                    <label
                                        for="${inputId}"
                                        class="s3-bill-title"
                                    >
                                        ${escapeHTML(bill.description)}
                                    </label>

                                    <small>
                                        Tagihan ${rupiah(bill.nominal)}
                                        · Dibayar ${rupiah(bill.paid)}
                                    </small>

                                    <span
                                        class="s3-badge s3-bill-status"
                                        data-bill-status="${escapeHTML(bill.id)}"
                                    >
                                        Belum dialokasikan
                                    </span>

                                    <small data-allocation></small>
                                </div>

                                <div class="s3-bill-price">
                                    ${rupiah(bill.remaining)}
                                    <small>Sisa tagihan</small>
                                </div>
                            </div>
                        `;
                    }).join('');

                    return `
                        <details class="s3-bill-group" open>
                            <summary>
                                ${escapeHTML(group[0].name)}
                                <small>${group.length} tagihan</small>
                            </summary>

                            <label class="s3-group-select">
                                <input
                                    type="checkbox"
                                    data-group-check="${groupId}"
                                >
                                Pilih semua dalam kelompok
                            </label>

                            ${items}
                        </details>
                    `;
                }).join('');
        }

        /* ================================================
           LOAD BILLS
        ================================================ */

        async function loadBills() {
            if (saving || uncertain) return;

            requestController?.abort();

            const sequence = ++requestSequence;
            const studentId = $('student').value;

            bills = [];
            selected.clear();
            amount = 0;

            $('amount').value = '';
            $('method').value = '';
            $('note').value = '';

            $('all-wrap').hidden = true;
            $('bill-count').textContent = '0 tagihan';
            $('profile').hidden = !studentId;

            loading = !!studentId;

            message();
            recalculate();

            if (!studentId) {
                $('bills').removeAttribute('aria-busy');
                showEmpty();
                return;
            }

            const student = studentOptions.find(
                option => option.value === studentId
            );

            if (!student) {
                loading = false;
                showEmpty(
                    'Siswa tidak ditemukan',
                    'Pilih kembali siswa yang tersedia.'
                );
                recalculate();
                return;
            }

            $('profile-name').textContent = student.name;
            $('profile-nisn').textContent = student.nisn;
            $('profile-class').textContent = student.className;
            $('profile-avatar').textContent =
                student.name.slice(0, 1).toUpperCase();

            showEmpty(
                'Sedang memuat tagihan…',
                'Menyiapkan rincian pembayaran siswa.'
            );

            $('bills').setAttribute('aria-busy', 'true');

            requestController = new AbortController();

            try {
                const response = await fetch(
                    root.dataset.billsUrl +
                    encodeURIComponent(studentId),
                    {
                        signal: requestController.signal,
                        credentials: 'same-origin',
                        headers: {
                            Accept: 'application/json'
                        }
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `Tagihan gagal dimuat (HTTP ${response.status}).`
                    );
                }

                const data = await response.json();

                if (
                    sequence !== requestSequence ||
                    !root.isConnected
                ) {
                    return;
                }

                if (!Array.isArray(data.tagihan)) {
                    throw new Error(
                        'Format respons tagihan tidak sesuai.'
                    );
                }

                const seenIds = new Set();
                const groupNames = new Map();

                bills = data.tagihan.map(item => {
                    const id = String(item.id ?? '');

                    if (!id || seenIds.has(id)) {
                        throw new Error(
                            'ID tagihan kosong atau duplikat.'
                        );
                    }

                    seenIds.add(id);

                    if (
                        item.nominal == null ||
                        item.sudah_dibayar == null ||
                        item.nominal === '' ||
                        item.sudah_dibayar === ''
                    ) {
                        throw new Error(
                            'Nominal tagihan tidak lengkap.'
                        );
                    }

                    const nominal = Number(item.nominal);
                    const paid = Number(item.sudah_dibayar);

                    if (
                        ![nominal, paid].every(number =>
                            Number.isSafeInteger(number) &&
                            number >= 0
                        )
                    ) {
                        throw new Error(
                            'Nominal API harus berupa angka rupiah bulat.'
                        );
                    }

                    const name = String(
                        item.nama || 'Lainnya'
                    );

                    if (!groupNames.has(name)) {
                        groupNames.set(
                            name,
                            groupNames.size
                        );
                    }

                    return {
                        id,
                        nominal,
                        paid,
                        remaining: Math.max(0, nominal - paid),
                        name,
                        group: groupNames.get(name),
                        description: String(
                            item.waktu ||
                            item.keterangan ||
                            '-'
                        )
                    };
                })
                    .filter(bill => bill.remaining > 0)
                    .sort((a, b) => a.group - b.group);

                const allRemaining = bills.reduce(
                    (sum, bill) => sum + bill.remaining,
                    0
                );

                if (!Number.isSafeInteger(allRemaining)) {
                    throw new Error(
                        'Total tagihan melebihi batas nominal yang didukung.'
                    );
                }

                renderBills();

                $('all-wrap').hidden = bills.length === 0;

                $('bill-count').textContent =
                    `${bills.length} tagihan`;

            } catch (error) {
                if (
                    error.name === 'AbortError' ||
                    sequence !== requestSequence ||
                    !root.isConnected
                ) {
                    return;
                }

                bills = [];
                selected.clear();

                showEmpty(
                    'Tagihan gagal dimuat',
                    error.message ||
                    'Periksa koneksi, lalu coba kembali.'
                );

                const retry = document.createElement('button');

                retry.type = 'button';
                retry.className = 's3-btn s3-btn-ghost';
                retry.dataset.action = 'retry';
                retry.textContent = 'Coba lagi ↗';

                $('bills').firstElementChild.append(retry);

            } finally {
                if (sequence === requestSequence) {
                    loading = false;

                    $('bills').removeAttribute('aria-busy');

                    recalculate();
                }
            }
        }

        on($('student'), 'change', loadBills);

        /* ================================================
           SELECTION AND AMOUNT
        ================================================ */

        on($('all'), 'change', () => {
            if (saving || uncertain) return;

            selected = $('all').checked
                ? new Set(bills.map(bill => bill.id))
                : new Set();

            recalculate();
        });

        on($('bills'), 'change', event => {
            if (saving || uncertain) return;

            const input = event.target;

            if (input.matches('[data-bill-check]')) {
                const id = input.dataset.billCheck;

                if (input.checked) {
                    selected.add(id);
                } else {
                    selected.delete(id);
                }

            } else if (input.matches('[data-group-check]')) {
                const groupId = Number(
                    input.dataset.groupCheck
                );

                bills
                    .filter(bill => bill.group === groupId)
                    .forEach(bill => {
                        if (input.checked) {
                            selected.add(bill.id);
                        } else {
                            selected.delete(bill.id);
                        }
                    });

            } else {
                return;
            }

            recalculate();
        });

        on($('amount'), 'input', () => {
            const input = $('amount');
            const raw = input.value;

            const cursor =
                input.selectionStart ?? raw.length;

            const digitCount = raw
                .slice(0, cursor)
                .replace(/\D/g, '')
                .length;

            const number = Number(
                raw.replace(/\D/g, '')
            ) || 0;

            const total = selectedTotal();

            amount = Number.isSafeInteger(number)
                ? Math.min(number, total)
                : total;

            if (
                number > total ||
                !Number.isSafeInteger(number)
            ) {
                message(
                    `Nominal disesuaikan menjadi ${rupiah(total)} ` +
                    'sesuai total tagihan terpilih.'
                );
            } else {
                message();
            }

            input.value = amount
                ? rupiah(amount)
                : '';

            let position = input.value.length;
            let found = 0;

            for (let index = 0; index < input.value.length; index++) {
                if (
                    /\d/.test(input.value[index]) &&
                    ++found >= digitCount
                ) {
                    position = digitCount
                        ? index + 1
                        : index;

                    break;
                }
            }

            input.setSelectionRange(
                position,
                position
            );

            recalculate();
        });

        ['method', 'date'].forEach(role => {
            on($(role), 'input', recalculate);
            on($(role), 'change', recalculate);
        });

        /* ================================================
           OPEN / CLOSE
        ================================================ */

        function openPayment() {
            if (dialog.open) return;

            focusBefore = document.activeElement;

            if (!uncertain) {
                $('form').reset();

                $('student-search').value = '';
                $('student').value = '';

                searchStudents();

                $('date').value = localDateTime();

                bills = [];
                selected.clear();

                amount = 0;
                loading = false;

                $('profile').hidden = true;
                $('all-wrap').hidden = true;
                $('bill-count').textContent = '0 tagihan';

                $('bills').removeAttribute('aria-busy');

                showEmpty();
                message();
                recalculate();
            }

            dialog.showModal();

            if (!uncertain) {
                $('student-search').focus();
            }
        }

        function closePayment() {
            if (!saving) {
                dialog.close();
            }
        }

        on(dialog, 'cancel', event => {
            if (saving) {
                event.preventDefault();
            }
        });

        on(dialog, 'close', () => {
            requestController?.abort();
            requestSequence++;
            loading = false;

            if (focusBefore?.isConnected) {
                focusBefore.focus();
            }
        });

        function lockForm(locked) {
            $('student').disabled = locked;
            $('student-search').disabled = locked;
            $('all').disabled = locked;

            $('bills').querySelectorAll('input')
                .forEach(input => {
                    input.disabled = locked;
                });

            dialog.querySelectorAll('[data-action="close"]')
                .forEach(button => {
                    button.disabled = saving;
                });

            recalculate();
        }

        /* ================================================
           SAVE PAYMENT
        ================================================ */

        on($('form'), 'submit', async event => {
            event.preventDefault();

            if (
                saving ||
                uncertain ||
                loading ||
                !$('form').reportValidity()
            ) {
                return;
            }

            const total = selectedTotal();

            if (
                !selected.size ||
                amount <= 0 ||
                amount > total ||
                !Number.isSafeInteger(amount)
            ) {
                message(
                    'Periksa kembali pilihan tagihan dan nominal pembayaran.',
                    'error'
                );
                return;
            }

            const details = allocate(
                bills,
                selected,
                amount
            );

            const allocatedAmount = details.reduce(
                (sum, item) => sum + item.dibayar,
                0
            );

            if (allocatedAmount !== amount) {
                message(
                    'Alokasi pembayaran tidak sesuai nominal.',
                    'error'
                );
                return;
            }

            const [date, time] = $('date').value.split('T');

            const payload = {
                id_siswa: $('student').value,
                rincian: details,
                metode_bayar: $('method').value,
                catatan: $('note').value.trim(),
                tanggal_bayar: date,
                jam_bayar: time || '00:00',
                tanggal_lengkap: $('date').value
            };

            saving = true;

            message();
            lockForm(true);

            $('save').textContent = 'Menyimpan pembayaran…';

            let definitiveFailure = false;

            try {
                const csrf =
                    document.querySelector(
                        'meta[name="csrf-token"]'
                    )?.content ||
                    document.querySelector(
                        'input[name="csrf_token"]'
                    )?.value ||
                    '';

                const response = await fetch(
                    root.dataset.saveUrl,
                    {
                        method: 'POST',
                        credentials: 'same-origin',

                        headers: {
                            'Content-Type': 'application/json',
                            Accept: 'application/json',
                            'X-CSRFToken': csrf
                        },

                        body: JSON.stringify(payload)
                    }
                );

                let result;

                try {
                    result = await response.json();
                } catch {
                    throw new Error(
                        'Balasan server tidak dapat dibaca.'
                    );
                }

                if (
                    !response.ok ||
                    result.sukses !== true
                ) {
                    definitiveFailure =
                        result.sukses === false &&
                        response.status < 500;

                    throw new Error(
                        result.pesan ||
                        result.message ||
                        'Pembayaran belum dapat dikonfirmasi.'
                    );
                }

                message(
                    'Pembayaran berhasil disimpan. Memperbarui data…',
                    'success'
                );

                $('save').textContent = 'Tersimpan ✓';

                window.location.reload();

            } catch (error) {
                saving = false;

                if (!definitiveFailure) {
                    uncertain = true;

                    message(
                        `${error.message} ` +
                        'Status penyimpanan belum pasti. ' +
                        'Tutup panel, muat ulang halaman, lalu periksa ' +
                        'riwayat pembayaran sebelum mencatat ulang.',
                        'error'
                    );

                    $('save').textContent =
                        'Periksa riwayat pembayaran';

                } else {
                    message(
                        error.message,
                        'error'
                    );

                    $('save').textContent =
                        'Simpan pembayaran ↗';
                }

                lockForm(uncertain);
            }
        });

        /* ================================================
           EXPORT / PRINT
        ================================================ */

        const reportHeaders = [
            'No.',
            'NISN',
            'Nama siswa',
            'Kelas',
            'Total tagihan',
            'Dibayarkan',
            'Sisa tagihan',
            'Status'
        ];

        function reportData() {
            return filteredRows.map((row, index) => [
                index + 1,
                row.dataset.nisn,
                row.dataset.name,
                row.dataset.class,
                parseMoney(row.dataset.total),
                parseMoney(row.dataset.paid),
                parseMoney(row.dataset.remaining),
                row.dataset.status === 'paid'
                    ? 'Lunas'
                    : 'Belum lunas'
            ]);
        }

        function exportCSV() {
            if (!filteredRows.length) {
                toast('Tidak ada data untuk diekspor.');
                return;
            }

            const csvCell = value => {
                let text = String(value);

                if (/^\s*[=+\-@\t\r\n]/.test(text)) {
                    text = "'" + text;
                }

                return `"${text.replace(/"/g, '""')}"`;
            };

            const data = reportData().map(row =>
                row.map((value, index) =>
                    index === 1 ? `'${value}` : value
                )
            );

            const csv =
                '\uFEFF' +
                [reportHeaders, ...data]
                    .map(row => row.map(csvCell).join(';'))
                    .join('\r\n');

            const url = URL.createObjectURL(
                new Blob([csv], {
                    type: 'text/csv;charset=utf-8;'
                })
            );

            const anchor = document.createElement('a');

            anchor.href = url;
            anchor.download = 'laporan-pembayaran-spp.csv';

            document.body.append(anchor);

            anchor.click();
            anchor.remove();

            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 1000);

            toast(
                `${filteredRows.length} siswa diekspor sesuai filter.`
            );
        }

        function printReport() {
            if (!filteredRows.length) {
                toast('Tidak ada data untuk dicetak.');
                return;
            }

            const popup = window.open('', '_blank');

            if (!popup) {
                toast(
                    'Izinkan pop-up untuk membuka laporan cetak.'
                );
                return;
            }

            popup.opener = null;

            const tableHead = reportHeaders.map(
                header => `<th>${escapeHTML(header)}</th>`
            ).join('');

            const tableBody = reportData().map(row => {
                const cells = row.map((value, index) => {
                    const content =
                        index >= 4 && index <= 6
                            ? rupiah(value)
                            : value;

                    return `<td>${escapeHTML(content)}</td>`;
                }).join('');

                return `<tr>${cells}</tr>`;
            }).join('');

            const filterLabel = $('filter-note').textContent;

            popup.document.write(`
                <!doctype html>
                <html lang="id">
                <head>
                    <meta charset="UTF-8">
                    <title>Laporan pembayaran SPP</title>

                    <style>
                        @page {
                            size: A4 landscape;
                            margin: 14mm;
                        }

                        body {
                            color: #263c2d;
                            font: 11px system-ui, sans-serif;
                        }

                        h1 {
                            margin-bottom: 8px;
                            font-size: 23px;
                        }

                        p {
                            margin: 5px 0;
                            color: #788671;
                            font-size: 10px;
                        }

                        table {
                            width: 100%;
                            margin-top: 22px;
                            border-collapse: collapse;
                        }

                        th, td {
                            padding: 9px 7px;
                            border-bottom: 1px solid #dfe5d8;
                            text-align: left;
                        }

                        th {
                            background: #eef4e7;
                            font-size: 9px;
                        }

                        td:nth-child(n+5):nth-child(-n+7) {
                            text-align: right;
                            white-space: nowrap;
                        }

                        thead {
                            display: table-header-group;
                        }

                        tr {
                            break-inside: avoid;
                        }
                    </style>
                </head>

                <body>
                    <h1>Laporan pembayaran SPP</h1>

                    <p>${escapeHTML(filterLabel)}</p>

                    <p>
                        ${filteredRows.length} siswa ·
                        Dicetak ${escapeHTML(
                            new Date().toLocaleString('id-ID')
                        )}
                    </p>

                    <table>
                        <thead>
                            <tr>${tableHead}</tr>
                        </thead>

                        <tbody>${tableBody}</tbody>
                    </table>
                </body>
                </html>
            `);

            popup.document.close();
            popup.focus();
            popup.print();
        }

        /* ================================================
           CENTRAL CLICK HANDLER
        ================================================ */

        on(root, 'click', event => {
            if (!(event.target instanceof Element)) return;

            const statusButton = event.target.closest(
                '[data-status-filter]'
            );

            if (statusButton) {
                statusFilter =
                    statusButton.dataset.statusFilter;

                filter();
                return;
            }

            const button = event.target.closest(
                '[data-action]'
            );

            if (!button || button.disabled) return;

            switch (button.dataset.action) {
                case 'open':
                    openPayment();
                    break;

                case 'close':
                    closePayment();
                    break;

                case 'show-unpaid':
                    showUnpaid();
                    break;

                case 'retry':
                    loadBills();
                    break;

                case 'reset':
                    statusFilter = '';

                    $('search').value = '';
                    $('class').value = '';

                    filter();
                    break;

                case 'prev':
                    page--;
                    filter(false);
                    break;

                case 'next':
                    page++;
                    filter(false);
                    break;

                case 'export':
                    exportCSV();
                    break;

                case 'print':
                    printReport();
                    break;

                case 'full':
                    if (!saving && !uncertain) {
                        amount = selectedTotal();

                        $('amount').value = amount
                            ? rupiah(amount)
                            : '';

                        message();
                        recalculate();
                    }
                    break;
            }
        });

        filter();
        searchStudents();
        recalculate();
    }

    /* =====================================================
       SPA LIFECYCLE
    ===================================================== */

    function init(container = document) {
        if (container.matches?.('[data-spp-premium]')) {
            mount(container);
        }

        container
            .querySelectorAll('[data-spp-premium]')
            .forEach(mount);
    }

    function destroy(container) {
        [...instances].forEach(([root, instance]) => {
            if (
                !container ||
                root === container ||
                container.contains(root)
            ) {
                instance.destroy();
            }
        });
    }

    window[GLOBAL_KEY] = {
        init,
        destroy
    };

    function boot() {
        init();

        new MutationObserver(records => {
            [...instances].forEach(([root, instance]) => {
                if (!root.isConnected) {
                    instance.destroy();
                }
            });

            records.forEach(record => {
                record.addedNodes.forEach(node => {
                    if (
                        node.nodeType === 1 &&
                        node.isConnected
                    ) {
                        init(node);
                    }
                });
            });
        }).observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            boot,
            { once: true }
        );
    } else {
        boot();
    }
})();