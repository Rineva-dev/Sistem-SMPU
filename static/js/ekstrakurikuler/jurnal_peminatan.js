const namaBulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];

function ubahTanggal(tglStr) {
    if (!tglStr || tglStr === '-' || tglStr.trim() === '') return null;
    const [d, m, y] = tglStr.split('/');
    return new Date(`${y}-${m}-${d}`);
}

document.getElementById('modalLibur').addEventListener('show.bs.modal', async () => {
    const wadah = document.getElementById('daftarBulanPeriode');
    const elemenPeriode = document.getElementById('periode-peminatan');

    const tglMulai = ubahTanggal(elemenPeriode.dataset.mulai);
    const tglSelesai = ubahTanggal(elemenPeriode.dataset.selesai);
    const peminatanId = elemenPeriode.dataset.peminatanId;

    if (!tglMulai || !tglSelesai || isNaN(tglMulai.getTime()) || isNaN(tglSelesai.getTime())) {
        wadah.innerHTML = `<div class="text-danger">Tentukan dulu periode kegiatan pada data peminatan!</div>`;
        return;
    }

    // Ambil bulan yang SUDAH disimpan → agar tidak muncul lagi
    let sudahLibur = [];
    try {
        const res = await fetch(`/data-peminatan/libur/daftar?peminatan_id=${peminatanId}`);
        if (!res.ok) throw new Error('Error');
        sudahLibur = await res.json();
    } catch (e) {
        console.warn('⚠️ Gagal ambil data libur:', e);
    }

    // Masukkan ke daftar kunci agar mudah dicek
    const kunciSudah = new Set(sudahLibur.map(b => `${b.tahun}-${String(b.bulan).padStart(2,'0')}`));

    let sekarang = new Date(tglMulai.getFullYear(), tglMulai.getMonth(), 1);
    let html = '';
    let adaPilihan = false;

    while (sekarang <= tglSelesai) {
        const thn = sekarang.getFullYear();
        const bln = sekarang.getMonth() + 1;
        const kunci = `${thn}-${String(bln).padStart(2,'0')}`;

        // ✅ LEWATKAN bulan yang sudah terdaftar libur
        if (!kunciSudah.has(kunci)) {
            html += `
            <div class="form-check mb-2">
                <input class="form-check-input" type="checkbox" name="bulan_libur" value="${thn}-${bln}" id="bln-${thn}-${bln}">
                <label class="form-check-label" for="bln-${thn}-${bln}">
                    ${namaBulan[bln-1]} ${thn}
                </label>
            </div>`;
            adaPilihan = true;
        }

        sekarang.setMonth(sekarang.getMonth() + 1);
    }

    if (!adaPilihan) {
        wadah.innerHTML = `<div class="text-center text-muted py-3">Semua bulan pada periode ini sudah diatur libur.</div>`;
    } else {
        wadah.innerHTML = html;
    }

    // Kosongkan keterangan saat modal dibuka kembali
    document.querySelector('[name="keterangan"]').value = '';
});

document.getElementById('formLibur').addEventListener('submit', async e => {
    e.preventDefault();
    const tombol = e.target.querySelector('[type="submit"]');
    tombol.disabled = true;
    tombol.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Menyimpan...';

    const fd = new FormData(e.target);
    const bulanTerpilih = fd.getAll('bulan_libur');
    const keteranganUmum = (fd.get('keterangan') || '').trim();
    const peminatanId = fd.get('peminatan_id');

    if (bulanTerpilih.length === 0) {
        alert('Pilih dulu bulan yang akan diatur libur!');
        tombol.disabled = false;
        tombol.innerHTML = 'Simpan Pengaturan';
        return;
    }

    // Salin keterangan umum ke SEMUA bulan yang dipilih
    const dataSimpan = bulanTerpilih.map(kunci => ({
        bulan_tahun: kunci,
        keterangan: keteranganUmum
    }));

    try {
        const res = await fetch(e.target.action, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({peminatan_id: peminatanId, daftar: dataSimpan})
        });
        const hasil = await res.json();
        if (hasil.sukses) {
            bootstrap.Modal.getOrCreateInstance(document.getElementById('modalLibur')).hide();
            alert('✅ Tersimpan! Halaman diperbarui...');
            setTimeout(() => location.reload(), 500);
        } else {
            alert('❌ Gagal: ' + (hasil.pesan || 'Coba lagi'));
        }
    } catch {
        alert('❌ Gagal terhubung ke server');
    } finally {
        tombol.disabled = false;
        tombol.innerHTML = 'Simpan Pengaturan';
    }
});