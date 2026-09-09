/* ==========================================
   FUNGSI CUSTOM DROPDOWN / SELECT
========================================== */

// Jadikan fungsi bisa dipanggil kapan saja
window.initCustomSelect = function(wrappers) {
  // Ubah jadi array kalau cuma satu elemen
  if (!Array.isArray(wrappers) && !(wrappers instanceof NodeList)) {
    wrappers = [wrappers];
  }

  wrappers.forEach(selectWrapper => {
    // Lewati kalau sudah diproses
    if (selectWrapper.dataset.diproses === 'true') return;
    selectWrapper.dataset.diproses = 'true';

    const originalSelect = selectWrapper.querySelector('select');
    if (!originalSelect) return;

    // Sembunyikan select asli
    originalSelect.style.cssText = `
      opacity: 0;
      position: absolute;
      pointer-events: none;
      width: 1px;
      height: 1px;
      border: none;
      margin: 0;
      padding: 0;
    `;
    originalSelect.tabIndex = -1;

    // Hapus elemen lama jika ada
    selectWrapper.querySelectorAll('.custom-select__trigger, .custom-select__options').forEach(el => el.remove());

    const trigger = document.createElement('div');
    const selectedText = document.createElement('span');
    const arrow = document.createElement('span');
    const optionsList = document.createElement('div');

    trigger.className = 'custom-select__trigger';
    trigger.tabIndex = 0;
    selectedText.className = 'custom-select__selected';
    arrow.className = 'custom-select__arrow';
    optionsList.className = 'custom-select__options';

    trigger.appendChild(selectedText);
    trigger.appendChild(arrow);
    selectWrapper.appendChild(trigger);
    selectWrapper.appendChild(optionsList);

    const populateOptions = () => {
      optionsList.innerHTML = '';
      Array.from(originalSelect.options).forEach((option) => {
        const optionEl = document.createElement('div');
        optionEl.className = 'custom-select__option';
        optionEl.dataset.value = option.value;
        // Simpan juga data tambahan jika ada
        if (option.dataset.id) optionEl.dataset.id = option.dataset.id;
        if (option.dataset.nama) optionEl.dataset.nama = option.dataset.nama;
        if (option.dataset.jabatanAsli) optionEl.dataset.jabatanAsli = option.dataset.jabatanAsli;
        
        optionEl.textContent = option.textContent.trim();

        if (option.selected) {
          optionEl.classList.add('selected');
          selectedText.textContent = option.textContent.trim();
        } else {
          optionEl.classList.remove('selected');
        }

        optionEl.addEventListener('click', (e) => {
          e.stopPropagation();
          originalSelect.value = option.value;
          // Salin semua data atribut
          for (let attr in optionEl.dataset) {
            originalSelect.dataset[attr] = optionEl.dataset[attr];
          }
          originalSelect.dispatchEvent(new Event('change', { bubbles: true }));
          window.closeAllSelects();
          trigger.focus();
        });

        optionsList.appendChild(optionEl);
      });
    };

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      window.closeAllSelects(selectWrapper);
      selectWrapper.classList.toggle('open');
      selectWrapper.classList.add('focused');
    });

    trigger.addEventListener('focus', () => selectWrapper.classList.add('focused'));
    trigger.addEventListener('blur', () => {
      setTimeout(() => {
        if (!selectWrapper.classList.contains('open')) selectWrapper.classList.remove('focused');
      }, 150);
    });

    trigger.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectWrapper.classList.toggle('open'); }
      if (e.key === 'Escape') { window.closeAllSelects(); trigger.focus(); }
    });

    // ✅ PERBAIKAN UTAMA: Saat nilai select berubah, perbarui tampilan customnya
    originalSelect.addEventListener('change', () => {
      const currentValue = originalSelect.value;
      let ditemukan = false;
      optionsList.querySelectorAll('.custom-select__option').forEach(opt => {
        const cocok = opt.dataset.value === currentValue;
        opt.classList.toggle('selected', cocok);
        if (cocok) {
          selectedText.textContent = opt.textContent.trim();
          ditemukan = true;
        }
      });
      // Jika tidak ada yang cocok, kosongkan tulisan
      if (!ditemukan) {
        selectedText.textContent = '';
      }
    });

    populateOptions();
  });
};

// Fungsi tutup semua dropdown
window.closeAllSelects = (except = null) => {
  document.querySelectorAll('.custom-select').forEach(sel => {
    if (sel !== except) sel.classList.remove('open', 'focused');
  });
};

// Jalankan otomatis saat halaman pertama kali dimuat
document.addEventListener('DOMContentLoaded', function() {
  window.initCustomSelect(document.querySelectorAll('.custom-select'));
  document.addEventListener('click', window.closeAllSelects);
});