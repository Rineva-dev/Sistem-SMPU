document.addEventListener('DOMContentLoaded', function() {
    let popupAktif = null;

    // FUNGSI BUKA PEMILIH WAKTU
    function bukaPemilih(bungkusInduk, inputSumber, tampilanTeks) {
        if (popupAktif) popupAktif.remove();

        let jamPilih = '07';
        let menitPilih = '00';
        if (inputSumber.value) {
            [jamPilih, menitPilih] = inputSumber.value.split(':');
        }

        popupAktif = document.createElement('div');
        popupAktif.className = 'custom-time__popup';
        popupAktif.innerHTML = `
            <div class="time-popup-judul">Waktu</div>
            <div class="time-bungkus-isi">
                <div class="time-popup-pilihan">
                    <div class="time-kolom">
                        <button type="button" class="time-btn-naik" data-arah="jam">&uarr;</button>
                        <input type="text" class="time-angka" data-tipe="jam" value="${jamPilih}" maxlength="2" inputmode="numeric">
                        <div class="time-label">Jam</div>
                        <button type="button" class="time-btn-turun" data-arah="jam">&darr;</button>
                    </div>
                    <span class="time-pemisah">:</span>
                    <div class="time-kolom">
                        <button type="button" class="time-btn-naik" data-arah="menit">&uarr;</button>
                        <input type="text" class="time-angka" data-tipe="menit" value="${menitPilih}" maxlength="2" inputmode="numeric">
                        <div class="time-label">Menit</div>
                        <button type="button" class="time-btn-turun" data-arah="menit">&darr;</button>
                    </div>
                </div>
                <div class="time-popup-aksi">
                    <button type="button" class="time-btn-batal">Batal</button>
                    <button type="button" class="time-btn-ok">OK</button>
                </div>
            </div>
        `;
        document.body.appendChild(popupAktif);

        // Tombol panah
        popupAktif.querySelectorAll('.time-btn-naik, .time-btn-turun').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const arah = btn.dataset.arah;
                const kotakAngka = popupAktif.querySelector(`.time-angka[data-tipe="${arah}"]`);
                let nilai = parseInt(kotakAngka.value) || 0;
                if (btn.classList.contains('time-btn-naik')) {
                    nilai = arah === 'jam' ? (nilai + 1) % 24 : (nilai + 1) % 60;
                } else {
                    nilai = arah === 'jam' ? (nilai - 1 + 24) % 24 : (nilai - 1 + 60) % 60;
                }
                kotakAngka.value = String(nilai).padStart(2, '0');
            });
        });

        // Validasi ketik
        popupAktif.querySelectorAll('.time-angka').forEach(input => {
            input.addEventListener('input', () => {
                input.value = input.value.replace(/[^0-9]/g, '');
                let nilai = parseInt(input.value) || 0;
                if (input.dataset.tipe === 'jam' && nilai > 23) input.value = '23';
                if (input.dataset.tipe === 'menit' && nilai > 59) input.value = '59';
            });
            input.addEventListener('blur', () => {
                input.value = String(parseInt(input.value) || 0).padStart(2, '0');
            });
        });

        // Tombol OK
        popupAktif.querySelector('.time-btn-ok').addEventListener('click', () => {
            const jam = popupAktif.querySelector('.time-angka[data-tipe="jam"]').value || '00';
            const menit = popupAktif.querySelector('.time-angka[data-tipe="menit"]').value || '00';
            const nilaiAkhir = `${jam}:${menit}`;
            inputSumber.value = nilaiAkhir;
            tampilanTeks.textContent = nilaiAkhir;
            inputSumber.dispatchEvent(new Event('change'));
            popupAktif.remove();
            popupAktif = null;
        });

        // Tombol Batal
        popupAktif.querySelector('.time-btn-batal').addEventListener('click', () => {
            popupAktif.remove();
            popupAktif = null;
        });
    }

    // INISIALISASI YANG BISA DIPANGGIL BERKALI-KALI TAPI TIDAK GANDA
    window.initCustomTime = function(elemenTarget) {
        const target = elemenTarget || document.querySelectorAll('.custom-time');
        target.forEach(bungkus => {
            // ❗ PENTING: Lewati yang sudah jadi
            if (bungkus.querySelector('.custom-time__tombol')) return;

            const inputAsli = bungkus.querySelector('input[type="time"]');
            if (!inputAsli) return;

            inputAsli.style.opacity = '0';
            inputAsli.style.position = 'absolute';
            inputAsli.style.pointerEvents = 'none';
            inputAsli.tabIndex = -1;

            const tampilan = document.createElement('div');
            const teks = document.createElement('span');
            const ikon = document.createElement('i');
            tampilan.className = 'custom-time__tombol';
            teks.className = 'custom-time__nilai';
            teks.textContent = inputAsli.value || '-- : --';
            ikon.className = 'fa fa-clock custom-time__ikon';
            tampilan.append(teks, ikon);
            bungkus.append(tampilan);

            tampilan.addEventListener('click', (e) => {
                e.stopPropagation();
                bukaPemilih(bungkus, inputAsli, teks);
            });
        });
    };

    // Jalankan pertama kali
    window.initCustomTime();
});