/**
 * Komponen Global: Editor Surat
 * Semua elemen toolbar dibuat otomatis oleh JS
 */
window.EditorSurat = (function () {

  /**
   * Inisialisasi editor
   * @param {string} wrapperId - ID tempat menaruh toolbar + editor
   * @param {string} inputId - ID input tersembunyi untuk kirim data
   * @returns {object} Fungsi publik
   */
  function init(wrapperId, inputId) {
    const wrapper = document.getElementById(wrapperId);
    const inputTersembunyi = document.getElementById(inputId);

    if (!wrapper || !inputTersembunyi) {
      console.warn(`[EditorSurat] Elemen tidak ditemukan: ${wrapperId} / ${inputId}`);
      return null;
    }

    // Buat struktur HTML
    wrapper.innerHTML = `
      <!-- Toolbar -->
      <div class="border rounded-top bg-light p-2 d-flex flex-wrap align-items-center gap-2 mb-0" data-editor-toolbar></div>
      <!-- Input File Gambar (tersembunyi) -->
      <input type="file" id="editor-gambar-input" accept="image/*" style="display:none" />
      <!-- Input Warna Tersembunyi -->
      <input type="color" id="pilih-warna-teks" class="input-warna-tersembunyi" value="#000000" />
      <input type="color" id="pilih-warna-latar" class="input-warna-tersembunyi" value="#ffff00" />

      <!-- ✅ MODAL PENGATURAN JARAK - Seperti Word -->
      <div class="modal fade" id="modalJarakParagraf" tabindex="-1" aria-labelledby="labelModalJarak" aria-hidden="true">
        <div class="modal-dialog modal-sm">
          <div class="modal-content">
            <div class="modal-header p-2">
              <h6 class="modal-title m-0" id="labelModalJarak">Pengaturan Paragraf</h6>
              <button type="button" class="btn-close btn-sm" data-bs-dismiss="modal" aria-label="Tutup"></button>
            </div>
            <div class="modal-body p-3">
              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label small">Jarak Sebelum</label>
                  <div class="input-group input-group-sm">
                    <input type="number" id="jarak-sebelum-input" class="form-control" min="0" max="100" step="1" value="0">
                    <span class="input-group-text">pt</span>
                  </div>
                </div>
                <div class="col-6">
                  <label class="form-label small">Jarak Sesudah</label>
                  <div class="input-group input-group-sm">
                    <input type="number" id="jarak-sesudah-input" class="form-control" min="0" max="100" step="1" value="8">
                    <span class="input-group-text">pt</span>
                  </div>
                </div>
              </div>
              <div class="mb-2">
                <label class="form-label small">Jarak Baris</label>
                <select id="jarak-baris-input" class="form-select form-select-sm">
                  <option value="1.0">Tunggal (1.0)</option>
                  <option value="1.15" selected>1,15</option>
                  <option value="1.5">1,5</option>
                  <option value="2.0">Ganda (2.0)</option>
                  <option value="2.5">2,5</option>
                  <option value="3.0">3,0</option>
                </select>
              </div>
            </div>
            <div class="modal-footer p-2">
              <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Batal</button>
              <button type="button" class="btn btn-sm btn-primary" id="terapkan-pengaturan-jarak">Terapkan</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Area Editor - ✅ Hapus line-height dari inline style -->
      <div 
        class="form-control border-top-0 rounded-bottom" 
        style="min-height: 320px; padding: 16px 16px 16px 24px; font-family: 'Times New Roman', serif; font-size: 12pt; text-align: justify; overflow-y: auto;"
        contenteditable="true"
        placeholder="Tuliskan isi surat di sini..."
        data-editor-area
      ></div>
    `;

    const toolbar = wrapper.querySelector('[data-editor-toolbar]');
    toolbar.style.display = "flex";
    toolbar.style.alignItems = "center";
    toolbar.style.gap = "6px";
    const editor = wrapper.querySelector('[data-editor-area]');
    const inputGambar = document.getElementById('editor-gambar-input');
    const inputWarnaTeks = document.getElementById('pilih-warna-teks');
    const inputWarnaLatar = document.getElementById('pilih-warna-latar');

    // --- Fungsi Simpan ---
    function simpan() {
      // Pastikan semua teks dibungkus <p> agar format berfungsi
      if (!editor.innerHTML.trim()) {
        editor.innerHTML = '<p style="line-height:1.15; margin:0pt 0 8pt 0;"><br></p>';
      }
      // Bungkus teks langsung menjadi <p> jika belum ada
      if (!editor.querySelector('p, div, li')) {
        editor.innerHTML = `<p style="line-height:1.15; margin:0pt 0 8pt 0;">${editor.innerHTML}</p>`;
      }
      inputTersembunyi.value = editor.innerHTML;
    }

    // --- Fungsi Format Teks ---
    function format(perintah, nilai = null) {
      document.execCommand(perintah, false, nilai);
      
      // Atur gaya daftar agar tidak ketutup batas kiri
      if (perintah === 'insertOrderedList' || perintah === 'insertUnorderedList') {
        setTimeout(() => {
          const daftar = editor.querySelector('ol, ul');
          if (daftar) {
            daftar.style.paddingLeft = '32px';
            daftar.style.margin = '8px 0';
            daftar.style.listStylePosition = 'outside';
            daftar.style.lineHeight = 'inherit';
          }
        }, 10);
      }

      editor.focus();
      simpan();
    }

    // --- ✅ Perbarui Tanda Centang Aktif di Menu ---
    function perbaruiTandaCentang(nilaiTerpilih) {
      document.querySelectorAll('#menu-jarak .dropdown-item[data-line]').forEach(item => {
        const tanda = item.querySelector('.cek-tanda');
        const aktif = item.dataset.line === nilaiTerpilih;
        item.classList.toggle('aktif', aktif);
        if (tanda) tanda.style.visibility = aktif ? 'visible' : 'hidden';
      });
    }

    // ✅ Ambil semua paragraf dalam seleksi - DIPERBAIKI
    function dapatkanSemuaParagrafTerpilih() {
      const seleksi = window.getSelection();
      if (!seleksi.rangeCount) return [];

      const rentang = seleksi.getRangeAt(0);
      const semuaBlok = editor.querySelectorAll('p, div, li');
      const hasil = [];

      semuaBlok.forEach(blok => {
        const rentangBlok = document.createRange();
        rentangBlok.selectNodeContents(blok);
        if (
          rentang.compareBoundaryPoints(Range.END_TO_START, rentangBlok) < 0 &&
          rentang.compareBoundaryPoints(Range.START_TO_END, rentangBlok) > 0
        ) {
          hasil.push(blok);
        }
      });

      // Jika tidak ditemukan, bungkus teks ke dalam <p>
      if (hasil.length === 0) {
        let elemen = seleksi.anchorNode;
        while (elemen && elemen !== editor) {
          if (elemen.nodeType === Node.ELEMENT_NODE && elemen.matches('p, div, li')) {
            hasil.push(elemen);
            break;
          }
          elemen = elemen.parentElement;
        }
        // Jika masih tidak ada, buat <p> baru
        if (hasil.length === 0) {
          document.execCommand('formatBlock', false, 'p');
          elemen = seleksi.anchorNode.parentElement;
          while (elemen && elemen.nodeType !== Node.ELEMENT_NODE) elemen = elemen.parentElement;
          if (elemen && elemen.matches('p, div, li')) {
            elemen.style.lineHeight = '1.15';
            elemen.style.margin = '0pt 0 8pt 0';
            hasil.push(elemen);
          }
        }
      }

      return hasil;
    }

    // --- ✅ Cek Status Jarak Paragraf Saat Ini ---
    function cekStatusJarakParagraf() {
      const daftarBlok = dapatkanSemuaParagrafTerpilih();
      if (daftarBlok.length === 0) return;

      // Ambil nilai jarak dari blok pertama
      const gaya = window.getComputedStyle(daftarBlok[0]);
      const jarakSebelum = parseFloat(gaya.marginTop) || 0;
      const jarakSesudah = parseFloat(gaya.marginBottom) || 0;
      const jarakBaris = parseFloat(gaya.lineHeight).toFixed(2).replace(/\.00$/, '.0');

      // Perbarui teks tombol saklar
      const btnSebelum = document.querySelector('[data-action="toggle-before"]');
      const btnSesudah = document.querySelector('[data-action="toggle-after"]');

      if (btnSebelum) {
        btnSebelum.textContent = jarakSebelum >= 7 ? '✓ Hapus Jarak Sebelum' : 'Tambah Jarak Sebelum';
      }
      if (btnSesudah) {
        btnSesudah.textContent = jarakSesudah >= 7 ? '✓ Hapus Jarak Sesudah' : 'Tambah Jarak Sesudah';
      }

      // Isi nilai ke modal jika terbuka
      const inputSebelum = document.getElementById('jarak-sebelum-input');
      const inputSesudah = document.getElementById('jarak-sesudah-input');
      const inputBaris = document.getElementById('jarak-baris-input');
      if (inputSebelum) inputSebelum.value = Math.round(jarakSebelum);
      if (inputSesudah) inputSesudah.value = Math.round(jarakSesudah);
      if (inputBaris) inputBaris.value = jarakBaris;
    }

    // --- ✅ Cek Jarak Baris Saat Ini ---
    function cekJarakSaatIni() {
      const seleksi = window.getSelection();
      if (!seleksi.rangeCount) return;

      let elemen = seleksi.anchorNode;
      while (elemen && elemen !== editor) {
        if (elemen.nodeType === Node.ELEMENT_NODE && (elemen.matches('p, div') || elemen.tagName === 'LI')) {
          const nilai = getComputedStyle(elemen).lineHeight;
          const nilaiAngka = parseFloat(nilai).toFixed(2);
          const daftarPilihan = ['1.00', '1.15', '1.50', '2.00', '2.50', '3.00'];
          const nilaiBulat = nilaiAngka.replace(/\.00$/, '.0');
          if (daftarPilihan.includes(nilaiAngka) || daftarPilihan.includes(nilaiBulat)) {
            perbaruiTandaCentang(nilaiBulat);
          }
          break;
        }
        elemen = elemen.parentElement;
      }
      cekStatusJarakParagraf();
    }

    // --- ✅ Atur Jarak Baris - DIPERKUAT ---
    function aturJarakBaris(nilai) {
      const daftarParagraf = dapatkanSemuaParagrafTerpilih();
      if (daftarParagraf.length === 0) return;
      
      daftarParagraf.forEach(blok => {
        // ✅ Gunakan !important agar pasti berubah
        blok.style.setProperty('line-height', nilai, 'important');
      });
      perbaruiTandaCentang(nilai);
      editor.focus();
      simpan();
    }

    // --- ✅ Buka Modal Pengaturan Lengkap ---
    function bukaPengaturanJarakLengkap() {
      cekStatusJarakParagraf(); // Isi nilai sesuai posisi kursor
      const modal = new bootstrap.Modal(document.getElementById('modalJarakParagraf'));
      modal.show();
    }

    // --- ✅ Terapkan Semua Pengaturan dari Modal - DIPERKUAT ---
    function terapkanPengaturanDariModal() {
      const jarakSebelum = document.getElementById('jarak-sebelum-input').value || 0;
      const jarakSesudah = document.getElementById('jarak-sesudah-input').value || 0;
      const jarakBaris = document.getElementById('jarak-baris-input').value || '1.15';

      const daftarBlok = dapatkanSemuaParagrafTerpilih();
      if (daftarBlok.length === 0) return;
      
      daftarBlok.forEach(blok => {
        blok.style.setProperty('margin-top', `${jarakSebelum}pt`, 'important');
        blok.style.setProperty('margin-bottom', `${jarakSesudah}pt`, 'important');
        blok.style.setProperty('line-height', jarakBaris, 'important');
      });

      cekStatusJarakParagraf();
      perbaruiTandaCentang(jarakBaris);
      editor.focus();
      simpan();

      // Tutup modal
      bootstrap.Modal.getInstance(document.getElementById('modalJarakParagraf')).hide();
    }

    // ✅ Tombol Saklar Jarak Sebelum - DIPERKUAT
    function toggleJarakSebelum() {
      const daftarBlok = dapatkanSemuaParagrafTerpilih();
      if (daftarBlok.length === 0) return;

      const gaya = window.getComputedStyle(daftarBlok[0]);
      const jarakSekarang = parseFloat(gaya.marginTop) || 0;
      const nilaiBaru = jarakSekarang >= 7 ? '0pt' : '12pt'; // Standar Word: 12pt sebelum

      daftarBlok.forEach(blok => {
        blok.style.setProperty('margin-top', nilaiBaru, 'important');
      });

      cekStatusJarakParagraf();
      editor.focus();
      simpan();
    }

    // ✅ Tombol Saklar Jarak Sesudah - DIPERKUAT
    function toggleJarakSesudah() {
      const daftarBlok = dapatkanSemuaParagrafTerpilih();
      if (daftarBlok.length === 0) return;

      const gaya = window.getComputedStyle(daftarBlok[0]);
      const jarakSekarang = parseFloat(gaya.marginBottom) || 0;
      const nilaiBaru = jarakSekarang >= 7 ? '0pt' : '8pt'; // Standar Word: 8pt sesudah

      daftarBlok.forEach(blok => {
        blok.style.setProperty('margin-bottom', nilaiBaru, 'important');
      });

      cekStatusJarakParagraf();
      editor.focus();
      simpan();
    }

    // --- Fungsi Masukkan Tab / Jarak ---
    function masukkanTab() {
      const seleksi = window.getSelection();
      if (!seleksi.rangeCount) return;
      const rentang = seleksi.getRangeAt(0);
      rentang.insertNode(document.createTextNode('\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0'));
      rentang.collapse(false);
      seleksi.removeAllRanges();
      seleksi.addRange(rentang);
      editor.focus();
      simpan();
    }

    // --- Fungsi Kurangi Jarak ---
    function kurangiTab() {
      document.execCommand('outdent', false, null);
      editor.focus();
      simpan();
    }

    // --- Fungsi Masukkan Tautan ---
    function masukkanTautan() {
      const url = prompt('Masukkan alamat tautan:', 'https://');
      if (url) format('createLink', url);
    }

    // --- Fungsi Unggah & Sisip Gambar ---
    function unggahGambar(e) {
      const file = e.target.files[0];
      if (!file) return;
      if (!file.type.startsWith('image/')) {
        alert('Hanya boleh mengunggah file gambar!');
        return;
      }
      const pembaca = new FileReader();
      pembaca.onload = function (peristiwa) {
        const urlGambar = peristiwa.target.result;
        format('insertImage', urlGambar);
        inputGambar.value = '';
      };
      pembaca.readAsDataURL(file);
    }

    // --- Bangun Isi Toolbar ---
    toolbar.innerHTML = `
      <!-- Gaya Huruf -->
      <button type="button" class="btn btn-sm btn-light" data-act="bold" title="Tebal (Ctrl+B)">
        <b>B</b>
      </button>
      <button type="button" class="btn btn-sm btn-light" data-act="italic" title="Miring (Ctrl+I)">
        <i>I</i>
      </button>
      <button type="button" class="btn btn-sm btn-light" data-act="underline" title="Garis Bawah (Ctrl+U)">
        <u>U</u>
      </button>
      <button type="button" class="btn btn-sm btn-light" data-act="strikeThrough" title="Coret">
        <s>S</s>
      </button>

      <div class="vr"></div>

      <!-- Jenis Huruf -->
      <select class="form-select form-select-sm" id="font-family" title="Jenis Huruf">
        <option value="Times New Roman" selected>Times New Roman</option>
        <option value="Segoe UI">Segoe UI</option>
        <option value="Arial">Arial</option>
        <option value="Calibri">Calibri</option>
        <option value="Georgia">Georgia</option>
      </select>

      <!-- Ukuran Huruf -->
      <select class="form-select form-select-sm" id="font-size" title="Ukuran Huruf">
        <option value="2">10 pt</option>
        <option value="3" selected>12 pt</option>
        <option value="4">14 pt</option>
        <option value="5">18 pt</option>
        <option value="6">24 pt</option>
        <option value="7">36 pt</option>
      </select>

      <div class="vr"></div>

      <!-- ✅ JARAK BARIS & PARAGRAF - Tampilan Sama Word -->
      <div class="dropdown" id="dropdown-jarak">
        <button type="button" class="btn btn-sm btn-light" id="tombol-jarak" title="Jarak Baris & Paragraf">
          <i class="fas fa-text-height"></i>
        </button>
        <ul class="dropdown-menu dropdown-menu-sm" id="menu-jarak">
          <li><button type="button" class="dropdown-item" data-line="1.0"><span class="cek-tanda">✓</span> Tunggal</button></li>
          <li><button type="button" class="dropdown-item aktif" data-line="1.15"><span class="cek-tanda">✓</span> 1,15</button></li>
          <li><button type="button" class="dropdown-item" data-line="1.5"><span class="cek-tanda">✓</span> 1,5</button></li>
          <li><button type="button" class="dropdown-item" data-line="2.0"><span class="cek-tanda">✓</span> Ganda</button></li>
          <li><button type="button" class="dropdown-item" data-line="2.5"><span class="cek-tanda">✓</span> 2,5</button></li>
          <li><button type="button" class="dropdown-item" data-line="3.0"><span class="cek-tanda">✓</span> 3,0</button></li>
          <li><hr class="dropdown-divider"></li>
          <!-- ✅ TOMBOL PENGATURAN LENGKAP -->
          <li><button type="button" class="dropdown-item" id="jarak-kustom"><span class="cek-tanda"></span> Pengaturan Jarak...</button></li>
          <li><hr class="dropdown-divider"></li>
          <li><button type="button" class="dropdown-item" data-action="toggle-before">Tambah Jarak Sebelum</button></li>
          <li><button type="button" class="dropdown-item" data-action="toggle-after">Tambah Jarak Sesudah</button></li>
        </ul>
      </div>

      <div class="vr"></div>

      <!-- Warna Teks & Latar -->
      <div class="color-group">
        <button type="button" class="btn btn-sm btn-light btn-color" id="btn-warna-teks" title="Pilih Warna Teks">
          <span>A</span>
        </button>
        <button type="button" class="btn btn-sm btn-light" id="reset-warna-teks" title="Hapus Warna Teks">
          <span>×</span>
        </button>
      </div>
      <div class="color-group">
        <button type="button" class="btn btn-sm btn-light btn-color" id="btn-warna-latar" title="Pilih Warna Latar">
          <span>A</span>
        </button>
        <button type="button" class="btn btn-sm btn-light" id="reset-warna-latar" title="Hapus Warna Latar">
          <span>×</span>
        </button>
      </div>

      <div class="vr"></div>

      <!-- Gaya Paragraf -->
      <select class="form-select form-select-sm" id="style-block" title="Gaya Paragraf">
        <option value="">Paragraph</option>
        <option value="h1">Heading 1</option>
        <option value="h2">Heading 2</option>
        <option value="h3">Heading 3</option>
        <option value="h4">Heading 4</option>
      </select>

      <div class="vr"></div>

      <!-- Daftar & Indentasi -->
      <button type="button" class="btn btn-sm btn-light" data-act="insertOrderedList" title="Daftar Bernomor">
        <i class="fas fa-list-ol"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" data-act="insertUnorderedList" title="Daftar Berpoin">
        <i class="fas fa-list-ul"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" id="btn-indent" title="Tambah Indentasi">
        <i class="fas fa-indent"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" id="btn-outdent" title="Kurangi Indentasi">
        <i class="fas fa-outdent"></i>
      </button>

      <div class="vr"></div>

      <!-- Tautan & Gambar -->
      <button type="button" class="btn btn-sm btn-light" id="btn-link" title="Sisipkan Tautan">
        <i class="fas fa-link"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" id="btn-image" title="Unggah & Sisipkan Gambar">
        <i class="fas fa-image"></i>
      </button>

      <div class="vr"></div>

      <!-- Kode & Riwayat -->
      <button type="button" class="btn btn-sm btn-light" id="btn-code" title="Lihat Kode HTML">
        <i class="fas fa-code"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" data-act="undo" title="Batalkan Tindakan">
        <i class="fas fa-undo"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" data-act="redo" title="Ulangi Tindakan">
        <i class="fas fa-redo"></i>
      </button>
      <button type="button" class="btn btn-sm btn-light" id="btn-print" title="Cetak Isi Surat">
        <i class="fas fa-print"></i>
      </button>
    `;

    // --- Atur warna awal garis bawah ---
    const btnWarnaTeks = document.getElementById('btn-warna-teks');
    const btnWarnaLatar = document.getElementById('btn-warna-latar');
    btnWarnaTeks.style.backgroundImage = `linear-gradient(to top, #000000 3px, transparent 3px)`;
    btnWarnaLatar.style.backgroundImage = `linear-gradient(to top, #ffff00 3px, transparent 3px)`;

    // --- Pasang Event Klik ---
    // Gaya Huruf
    toolbar.querySelector('[data-act="bold"]').addEventListener('click', () => format('bold'));
    toolbar.querySelector('[data-act="italic"]').addEventListener('click', () => format('italic'));
    toolbar.querySelector('[data-act="underline"]').addEventListener('click', () => format('underline'));
    toolbar.querySelector('[data-act="strikeThrough"]').addEventListener('click', () => format('strikeThrough'));

    // ✅ Kontrol Buka-Tutup Dropdown Jarak
    const tombolJarak = document.getElementById('tombol-jarak');
    const menuJarak = document.getElementById('menu-jarak');

    tombolJarak.addEventListener('click', function(e) {
      e.stopPropagation();
      cekJarakSaatIni();
      const tombolPosisi = tombolJarak.getBoundingClientRect();
      const ruangKanan = window.innerWidth - tombolPosisi.right;
      menuJarak.classList.toggle('dropdown-menu-end', ruangKanan < 220);
      menuJarak.classList.toggle('show');
    });

    document.addEventListener('click', function(e) {
      if (!menuJarak.contains(e.target) && !tombolJarak.contains(e.target)) {
        menuJarak.classList.remove('show');
      }
    });

    // ✅ Event Pilihan Jarak Baris
    menuJarak.querySelectorAll('.dropdown-item[data-line]').forEach(item => {
      item.addEventListener('click', function(e) {
        e.preventDefault();
        aturJarakBaris(this.dataset.line);
        menuJarak.classList.remove('show');
      });
    });

    // ✅ Event Buka Pengaturan Lengkap
    document.getElementById('jarak-kustom').addEventListener('click', function(e) {
      e.preventDefault();
      menuJarak.classList.remove('show');
      bukaPengaturanJarakLengkap();
    });

    // ✅ Event Terapkan Pengaturan Modal
    document.getElementById('terapkan-pengaturan-jarak').addEventListener('click', terapkanPengaturanDariModal);

    // ✅ Event Jarak Paragraf
    menuJarak.querySelector('[data-action="toggle-before"]').addEventListener('click', function(e) {
      e.preventDefault();
      toggleJarakSebelum();
      menuJarak.classList.remove('show');
    });
    menuJarak.querySelector('[data-action="toggle-after"]').addEventListener('click', function(e) {
      e.preventDefault();
      toggleJarakSesudah();
      menuJarak.classList.remove('show');
    });

    // ✅ Perbarui status jarak saat kursor bergerak
    editor.addEventListener('mouseup', cekJarakSaatIni);
    editor.addEventListener('keyup', cekJarakSaatIni);
    editor.addEventListener('click', cekJarakSaatIni);

    // Jenis & Ukuran Huruf
    document.getElementById('font-family').addEventListener('change', function() {
      format('fontName', this.value);
    });
    document.getElementById('font-size').addEventListener('change', function() {
      format('fontSize', this.value);
    });

    // Warna Teks
    btnWarnaTeks.addEventListener('click', () => inputWarnaTeks.click());
    inputWarnaTeks.addEventListener('input', function() {
      const warna = this.value;
      format('foreColor', warna);
      btnWarnaTeks.style.backgroundImage = `linear-gradient(to top, ${warna} 3px, transparent 3px)`;
    });
    document.getElementById('reset-warna-teks').addEventListener('click', function() {
      format('removeFormat');
      format('foreColor', '#000000');
      inputWarnaTeks.value = '#000000';
      btnWarnaTeks.style.backgroundImage = `linear-gradient(to top, #000000 3px, transparent 3px)`;
    });

    // Warna Latar
    btnWarnaLatar.addEventListener('click', () => inputWarnaLatar.click());
    inputWarnaLatar.addEventListener('input', function() {
      const warna = this.value;
      format('hiliteColor', warna);
      btnWarnaLatar.style.backgroundImage = `linear-gradient(to top, ${warna} 3px, transparent 3px)`;
    });
    document.getElementById('reset-warna-latar').addEventListener('click', function() {
      format('hiliteColor', 'transparent');
      inputWarnaLatar.value = '#ffff00';
      btnWarnaLatar.style.backgroundImage = `linear-gradient(to top, #ffff00 3px, transparent 3px)`;
    });

    // Gaya Paragraf
    document.getElementById('style-block').addEventListener('change', function() {
      if (this.value) format('formatBlock', this.value);
      this.value = '';
    });

    // Daftar & Indentasi
    toolbar.querySelector('[data-act="insertOrderedList"]').addEventListener('click', () => format('insertOrderedList'));
    toolbar.querySelector('[data-act="insertUnorderedList"]').addEventListener('click', () => format('insertUnorderedList'));
    document.getElementById('btn-indent').addEventListener('click', masukkanTab);
    document.getElementById('btn-outdent').addEventListener('click', kurangiTab);

    // Tautan & Gambar
    document.getElementById('btn-link').addEventListener('click', masukkanTautan);
    document.getElementById('btn-image').addEventListener('click', () => inputGambar.click());
    inputGambar.addEventListener('change', unggahGambar);

    // Riwayat & Kode
    document.getElementById('btn-code').addEventListener('click', () => {
      const kode = editor.innerHTML;
      const hasil = prompt('Kode HTML Isi Surat:', kode);
      if (hasil !== null) {
        editor.innerHTML = hasil;
        simpan();
      }
    });
    toolbar.querySelector('[data-act="undo"]').addEventListener('click', () => format('undo'));
    toolbar.querySelector('[data-act="redo"]').addEventListener('click', () => format('redo'));
    document.getElementById('btn-print').addEventListener('click', () => window.print());

    // --- Event Tambahan ---
    editor.addEventListener('input', simpan);
    editor.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        masukkanTab();
      }
    });

    // Simpan nilai awal
    simpan();
    cekStatusJarakParagraf();

    // Fungsi publik
    return { simpan, format, masukkanTab, kurangiTab, aturJarakBaris };
  }

  return { init };
})();