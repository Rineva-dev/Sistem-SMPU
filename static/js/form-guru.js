document.addEventListener("DOMContentLoaded", function () {

    const dataMentah = document.getElementById('dataTugasKonfig').value;
    const daftarTugasBerdasarkanJabatan = JSON.parse(dataMentah);

    const inputTugasGabung = document.getElementById('inputTugasGabung');
    // ✅ Sembunyikan input ini jika hanya penyimpanan
    inputTugasGabung.tabIndex = -1;
    inputTugasGabung.style.opacity = '0';
    inputTugasGabung.style.position = 'absolute';

    let tugasTerpilih = [];
    if (inputTugasGabung.value.trim() !== "") {
        tugasTerpilih = inputTugasGabung.value.split(',').map(t => t.trim()).filter(t => t);
    }

    const selectJabatan = document.querySelector('select[name="jabatan"]');
    const dropdownTugas = document.getElementById('daftarTugasDropdown');
    const tampilanTerpilih = document.getElementById('tugasTerpilih');
    const containerMultiselect = document.querySelector('.custom-multiselect');

    // ------------------------------
    // Fungsi Tutup Semua
    // ------------------------------
    function tutupDropdownTugas() {
        dropdownTugas.style.display = 'none';
    }

    function tutupKalenderKustom() {
        if (typeof window.closeCalendar === 'function') {
            window.closeCalendar();
        }
    }

    window.tutupSemua = function() {
        tutupDropdownTugas();
        tutupKalenderKustom();
        if (typeof window.closeAllSelects === 'function') {
            window.closeAllSelects();
        }
    };

    // ------------------------------
    // VALIDASI NOMOR HP & EMAIL
    // ------------------------------
    const form = document.querySelector('form');
    const inputNoHp = document.querySelector('input[name="no_hp"]');
    const inputEmail = document.querySelector('input[name="email"]');

    form.addEventListener('submit', function(e) {
        let valid = true;
        let pesanKesalahan = [];

        // --- Validasi Nomor HP ---
        const noHp = inputNoHp.value.trim();
        if (noHp) { // Cek hanya jika diisi
            if (!/^\d+$/.test(noHp)) {
                valid = false;
                pesanKesalahan.push("Nomor HP hanya boleh berisi angka!");
            } else if (noHp.length < 8 || noHp.length > 13) {
                valid = false;
                pesanKesalahan.push("Nomor HP harus antara 8 sampai 13 digit!");
            }
        }

        // --- Validasi Email ---
        const email = inputEmail.value.trim();
        if (email) { // Cek hanya jika diisi
            // Pola email standar yang aman
            const polaEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!polaEmail.test(email)) {
                valid = false;
                pesanKesalahan.push("Format email tidak valid! Contoh: nama@domain.com");
            }
        }

        // Jika ada kesalahan, batalkan kirim dan tampilkan pesan
        if (!valid) {
            e.preventDefault();
            alert(pesanKesalahan.join("\n- "));
            // Atau jika ingin tampilkan di halaman, bisa pakai div pesan
        }
    });

    // ------------------------------
    // Fungsi Tugas Tambahan
    // ------------------------------
    function pasangEventInput() {
        const inputCari = document.getElementById('cariTugas');
        if (!inputCari) return;

        inputCari.addEventListener('focus', function() {
            tutupSemua();
            tampilkanDaftar('');
        });

        inputCari.addEventListener('input', function() {
            tampilkanDaftar(this.value);
        });
    }

    function tampilkanDaftar(kataKunci = '') {
        tutupDropdownTugas();
        dropdownTugas.innerHTML = "";

        if (typeof kataKunci !== 'string') kataKunci = '';

        const jabatan = selectJabatan.value.trim();

        if (!jabatan || !daftarTugasBerdasarkanJabatan.hasOwnProperty(jabatan)) {
            dropdownTugas.innerHTML = '<em class="text-muted">Pilih jabatan terlebih dahulu</em>';
            dropdownTugas.style.display = 'block';
            return;
        }

        const daftarFilter = daftarTugasBerdasarkanJabatan[jabatan].filter(tugas =>
            tugas.toLowerCase().includes(kataKunci.toLowerCase())
        );

        if (daftarFilter.length === 0) {
            dropdownTugas.innerHTML = '<em class="text-muted">Tidak ada tugas yang cocok</em>';
        } else {
            daftarFilter.forEach(tugas => {
                const sudah = tugasTerpilih.includes(tugas);
                const div = document.createElement('div');
                div.className = `opsi-tugas ${sudah ? 'terpilih' : ''}`;
                div.innerHTML = `<input type="checkbox" ${sudah ? 'checked' : ''}> ${tugas}`;

                div.onclick = function(e) {
                    e.stopPropagation();
                    toggleTugas(tugas);
                    tampilkanDaftar(kataKunci);
                };

                dropdownTugas.appendChild(div);
            });
        }

        dropdownTugas.style.display = 'block';
    }

    function toggleTugas(tugas) {
        const idx = tugasTerpilih.indexOf(tugas);
        idx === -1 ? tugasTerpilih.push(tugas) : tugasTerpilih.splice(idx, 1);
        perbaruiTampilan();
    }

    window.hapusTugas = function(tugas) {
        const idx = tugasTerpilih.indexOf(tugas);
        if (idx !== -1) {
            tugasTerpilih.splice(idx, 1);
            perbaruiTampilan();
            tampilkanDaftar('');
        }
    };

    function perbaruiTampilan() {
        tampilanTerpilih.innerHTML = '';

        if (tugasTerpilih.length > 0) {
            tugasTerpilih.forEach(tugas => {
                const span = document.createElement('span');
                span.className = 'badge';
                span.innerHTML = `${tugas} <button type="button" class="btn-close" onclick="hapusTugas('${tugas.replace(/'/g, "\\'")}')">&times;</button>`;
                tampilanTerpilih.appendChild(span);
            });
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'cariTugas';
            input.className = 'cari-tugas';
            input.autocomplete = 'off';
            input.tabIndex = 0;
            tampilanTerpilih.appendChild(input);
        } else {
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'cariTugas';
            input.className = 'cari-tugas';
            input.placeholder = 'Pilih atau ketik nama tugas...';
            input.autocomplete = 'off';
            input.tabIndex = 0;
            tampilanTerpilih.appendChild(input);
        }

        inputTugasGabung.value = tugasTerpilih.join(', ');
        pasangEventInput();
    }

    document.querySelectorAll('.custom-select__trigger').forEach(trigger => {
        trigger.addEventListener('click', tutupSemua);
    });

    // ✅ Tutup dropdown tugas HANYA jika klik BENAR-BENAR di luar semuanya
    document.addEventListener('click', function(e) {
        const diDalamTugas = containerMultiselect.contains(e.target);
        const diDalamKalender = 
            document.querySelector('.custom-date')?.contains(e.target) ||
            document.querySelector('.custom-date__calendar')?.contains(e.target);

        // Hanya tutup jika bukan di tugas dan bukan di kalender
        if (!diDalamTugas && !diDalamKalender) {
            tutupDropdownTugas();
        }
    });
    selectJabatan.addEventListener('change', tutupSemua);

    perbaruiTampilan();
});