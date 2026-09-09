document.addEventListener('DOMContentLoaded', function() {
  const daftarTTD = document.getElementById('daftar-penandatangan');
  const tombolTambah = document.getElementById('tambah-ttd');
  const barisPertama = document.querySelector('.baris-penandatangan');
  let nomorBaris = 1;

  if (!daftarTTD || !tombolTambah || !barisPertama) {
    console.warn('Halaman ini bukan halaman surat keluar, JS tidak dijalankan');
    return;
  }

  // --- INISIALISASI EDITOR GLOBAL ---
  if (window.EditorSurat) {
    window.editor = EditorSurat.init('wrapper_editor_isi', 'isi_surat');
    setTimeout(() => {
      const area = document.querySelector('[data-editor-area]');
      if (area && window.DATA_SURAT) {
        area.innerHTML = window.DATA_SURAT.isi_surat || '';
        if (window.editor) window.editor.simpan();
      }
    }, 150);
  }

  function aturTampilanTTD(selectEl) {
    const baris = selectEl.closest('.baris-penandatangan');
    if (!baris) return;

    const divPilihNama = baris.querySelector('.div-pilih-nama');
    const selectIdGuru = baris.querySelector('.select-nama');
    const inputNama = baris.querySelector('.nama-ttd');
    const inputJabatan = baris.querySelector('.jabatan-ttd');
    const idGuruTersembunyi = baris.querySelector('.id-guru-ttd');

    // Reset semua kondisi
    divPilihNama.style.display = 'none';
    selectIdGuru.value = '';
    inputNama.value = '';
    inputJabatan.value = '';
    inputNama.readOnly = false;
    inputJabatan.readOnly = false;
    inputNama.classList.remove('bg-light');
    inputJabatan.classList.remove('bg-light');
    if (idGuruTersembunyi) idGuruTersembunyi.value = '';

    const opsiTerpilih = selectEl.options[selectEl.selectedIndex];
    if (!opsiTerpilih || !selectEl.value) {
      return;
    }

    const jumlah = parseInt(opsiTerpilih.dataset.jumlah || 0);
    const jabatanAsli = opsiTerpilih.dataset.jabatanAsli || '';
    const idOtomatis = opsiTerpilih.dataset.id || '';
    const namaOtomatis = opsiTerpilih.dataset.nama || '';

    // ==============================================
    // ✅ KHUSUS JIKA PILIH "GURU"
    // Berapapun jumlahnya → Jabatan SELALU bisa diedit
    // ==============================================
    if (jabatanAsli === "Guru") {
      if (jumlah === 1 && idOtomatis) {
        selectIdGuru.value = idOtomatis;
        if (idGuruTersembunyi) idGuruTersembunyi.value = idOtomatis;
        inputNama.value = namaOtomatis;
        inputJabatan.value = jabatanAsli;
        inputNama.classList.add('bg-light');
        inputNama.readOnly = true;       // Nama terkunci
        inputJabatan.classList.remove('bg-light');
        inputJabatan.readOnly = false;    // ✅ Jabatan TERBUKA
        inputJabatan.placeholder = 'Contoh: Guru Matematika, Wali Kelas';
        return;
      }

      if (jumlah > 1) {
        divPilihNama.style.display = 'block';
        const kelasFilter = `opsi-${selectEl.value}`;
        Array.from(selectIdGuru.options).forEach(opt => {
          opt.style.display = opt.value === '' || opt.classList.contains(kelasFilter) ? '' : 'none';
        });
        inputJabatan.placeholder = 'Contoh: Guru Bahasa Indonesia, Pembina Ekskul';
        inputJabatan.readOnly = false;    // ✅ Jabatan TERBUKA
        return;
      }
    }

    // ==============================================
    // ✅ UNTUK JABATAN LAINNYA
    // Tetap terkunci semuanya, berapapun jumlahnya
    // ==============================================
    else {
      if (jumlah === 1 && idOtomatis) {
        selectIdGuru.value = idOtomatis;
        if (idGuruTersembunyi) idGuruTersembunyi.value = idOtomatis;
        inputNama.value = namaOtomatis;
        inputJabatan.value = jabatanAsli;
        inputNama.classList.add('bg-light');
        inputNama.readOnly = true;
        inputJabatan.classList.add('bg-light');
        inputJabatan.readOnly = true;     // ✅ Tetap terkunci
        return;
      }

      if (jumlah > 1) {
        divPilihNama.style.display = 'block';
        const kelasFilter = `opsi-${selectEl.value}`;
        Array.from(selectIdGuru.options).forEach(opt => {
          opt.style.display = opt.value === '' || opt.classList.contains(kelasFilter) ? '' : 'none';
        });
        inputJabatan.readOnly = true;     // ✅ Tetap terkunci meski banyak
        inputJabatan.classList.add('bg-light');
        return;
      }

      if (selectEl.value.startsWith('khusus-')) {
        inputNama.readOnly = false;
        inputJabatan.readOnly = false;
        inputJabatan.value = jabatanAsli;
        if (selectEl.value === 'khusus-lain') inputJabatan.value = '';
        inputJabatan.placeholder = 'Isi jabatan sesuai kebutuhan';
        return;
      }
    }
  }

  // --- SAAT PILIH NAMA DARI DAFTAR ---
  function pasangEventSelectNama(baris) {
    const selectIdGuru = baris.querySelector('.select-nama');
    const inputNama = baris.querySelector('.nama-ttd');
    const inputJabatan = baris.querySelector('.jabatan-ttd');
    const idGuruTersembunyi = baris.querySelector('.id-guru-ttd');

    if (!selectIdGuru) return;

    selectIdGuru.addEventListener('change', function() {
      const opsi = this.options[this.selectedIndex];
      if (!opsi.value) {
        inputNama.value = '';
        inputJabatan.value = '';
        inputNama.readOnly = false;
        inputJabatan.readOnly = false;
        if (idGuruTersembunyi) idGuruTersembunyi.value = '';
        return;
      }

      if (idGuruTersembunyi) idGuruTersembunyi.value = opsi.value;

      inputNama.value = opsi.dataset.nama;
      inputNama.classList.add('bg-light');
      inputNama.readOnly = true; // Nama selalu terkunci

      const jabatanDasar = opsi.dataset.jabatan || '';
      inputJabatan.value = jabatanDasar;

      // ✅ Khusus Guru → Jabatan tetap bisa diedit
      if (jabatanDasar === "Guru") {
        inputJabatan.readOnly = false;
        inputJabatan.classList.remove('bg-light');
        inputJabatan.placeholder = 'Contoh: Guru Mapel, Wali Kelas';
      } else {
        // Jabatan lain → tetap terkunci
        inputJabatan.readOnly = true;
        inputJabatan.classList.add('bg-light');
      }
    });
  }

  // --- Pasang semua event ke satu baris ---
  function pasangEventBaris(baris) {
    if (!baris) return;
    const selectJabatan = baris.querySelector('.jenis-ttd');
    if (selectJabatan) {
      selectJabatan.addEventListener('change', function() {
        aturTampilanTTD(this);
      });
      aturTampilanTTD(selectJabatan);
    }
    pasangEventSelectNama(baris);
    const tombolHapus = baris.querySelector('.hapus-ttd');
    if (tombolHapus) {
      tombolHapus.addEventListener('click', function() {
        baris.remove();
        nomorBaris--;
      });
    }
  }

  // --- Bersihkan baris sebelum disalin ---
  function bersihkanBarisUntukKloning(barisAsli) {
    const barisBersih = barisAsli.cloneNode(true);
    barisBersih.querySelectorAll('.custom-select__trigger, .custom-select__options').forEach(el => el.remove());
    barisBersih.querySelectorAll('.custom-select').forEach(el => { delete el.dataset.diproses; });

    const jenisTtd = barisBersih.querySelector('.jenis-ttd');
    const selectNama = barisBersih.querySelector('.select-nama');
    const namaTtd = barisBersih.querySelector('.nama-ttd');
    const jabatanTtd = barisBersih.querySelector('.jabatan-ttd');
    const divPilih = barisBersih.querySelector('.div-pilih-nama');
    const tombolHapus = barisBersih.querySelector('.hapus-ttd');
    const idGuru = barisBersih.querySelector('.id-guru-ttd');

    if (jenisTtd) jenisTtd.value = '';
    if (selectNama) selectNama.value = '';
    if (namaTtd) { namaTtd.value = ''; namaTtd.readOnly = false; namaTtd.classList.remove('bg-light'); }
    if (jabatanTtd) { jabatanTtd.value = ''; jabatanTtd.readOnly = false; jabatanTtd.classList.remove('bg-light'); }
    if (divPilih) divPilih.style.display = 'none';
    if (tombolHapus) tombolHapus.style.display = 'inline-flex';
    if (idGuru) idGuru.value = '';

    return barisBersih;
  }

  // --- MUAT DATA PENANDATANGAN SAAT EDIT ---
  window.muatPenandatangan = function(daftarTTD) {
    if (!daftarTTD || !Array.isArray(daftarTTD) || daftarTTD.length === 0) return;

    const wadah = document.getElementById('daftar-penandatangan');
    const barisPertama = document.querySelector('.baris-penandatangan');
    if (!wadah || !barisPertama) return;

    wadah.querySelectorAll('.baris-penandatangan:not(:first-child)').forEach(el => el.remove());
    let nomorBaris = 1;

    daftarTTD.forEach((data, idx) => {
      let baris;
      if (idx === 0) {
        baris = barisPertama;
      } else {
        if (nomorBaris >= 4) return;
        nomorBaris++;
        baris = bersihkanBarisUntukKloning(barisPertama);
        pasangEventBaris(baris);
        wadah.appendChild(baris);
        setTimeout(() => { if (window.initCustomSelect) window.initCustomSelect(baris.querySelectorAll('.custom-select')); }, 10);
      }

      const selectJenis = baris.querySelector('.jenis-ttd');
      const inputNama = baris.querySelector('.nama-ttd');
      const inputJabatan = baris.querySelector('.jabatan-ttd');
      const selectNama = baris.querySelector('.select-nama');
      const inputIdGuru = baris.querySelector('.id-guru-ttd');

      if (!selectJenis) return;

      let nilaiTerpilih = '';
      if (data.jenis) {
        const opsi = Array.from(selectJenis.options).find(opt => opt.value === data.jenis);
        if (opsi) nilaiTerpilih = opsi.value;
      }
      if (!nilaiTerpilih && data.jabatan) {
        const opsi = Array.from(selectJenis.options).find(opt => opt.dataset.jabatanAsli === data.jabatan.trim());
        if (opsi) nilaiTerpilih = opsi.value;
      }

      selectJenis.value = nilaiTerpilih || '';
      selectJenis.dispatchEvent(new Event('change', { bubbles: true }));

      if (inputNama) inputNama.value = data.nama || '';
      if (inputJabatan) inputJabatan.value = data.jabatan || '';
      if (inputIdGuru) inputIdGuru.value = data.id_guru || '';

      setTimeout(() => {
        if (selectNama && data.id_guru) {
          selectNama.value = data.id_guru;
          selectNama.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }, 50);
    });
  };

  // --- Jalankan untuk baris pertama ---
  pasangEventBaris(barisPertama);

  // --- Tambah baris baru ---
  tombolTambah.addEventListener('click', function() {
    if (nomorBaris >= 4) { alert('Maksimal 4 penandatangan per surat'); return; }
    nomorBaris++;
    const barisBaru = bersihkanBarisUntukKloning(barisPertama);
    pasangEventBaris(barisBaru);
    daftarTTD.appendChild(barisBaru);
    setTimeout(() => { if (window.initCustomSelect) window.initCustomSelect(barisBaru.querySelectorAll('.custom-select')); }, 10);
  });

  // --- Validasi sebelum kirim ---
  document.querySelector('form').addEventListener('submit', function(e) {
    const semuaBaris = document.querySelectorAll('.baris-penandatangan');
    let valid = true;
    semuaBaris.forEach((baris, indeks) => {
      const jenis = baris.querySelector('.jenis-ttd').value.trim();
      const nama = baris.querySelector('.nama-ttd').value.trim();
      const jabatan = baris.querySelector('.jabatan-ttd').value.trim();
      if (jenis && (!nama || !jabatan)) {
        valid = false;
        alert(`Baris ke-${indeks + 1}: Nama dan Jabatan harus diisi lengkap!`);
      }
    });
    if (!valid) e.preventDefault();
  });

  window.aturTampilanTTD = aturTampilanTTD;
  window.pasangEventBaris = pasangEventBaris;
  window.bersihkanBarisUntukKloning = bersihkanBarisUntukKloning;
});