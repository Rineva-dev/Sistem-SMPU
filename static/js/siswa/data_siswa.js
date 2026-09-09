document.addEventListener('DOMContentLoaded', function() {

    // ======================================
    // 1. FITUR PENCARIAN DI TABEL SISWA (TETAP DIPERTAHANKAN)
    // ======================================
    const inputCari = document.getElementById('cariSiswa');
    const tabel = document.querySelector('table tbody');

    if (inputCari && tabel) {
        inputCari.addEventListener('input', function() {
            const kataKunci = this.value.toLowerCase().trim();
            const baris = tabel.querySelectorAll('tr');
            baris.forEach(baris => {
                const teks = baris.textContent.toLowerCase();
                baris.style.display = teks.includes(kataKunci) ? '' : 'none';
            });
        });
    }


    // ======================================
    // 2. FUNGSI TAMBAH/UDAP SISWA (DISESUAIKAN DENGAN SISTEM BARU)
    // ======================================
    const jenisPendaftaran = document.getElementById('jenisPendaftaran');
    const tanggalDiterima = document.getElementById('tanggalDiterima');
    const tahunDiterima = document.getElementById('tahunDiterima');

    // Isi tahun diterima otomatis dari tanggal (tetap berjalan)
    function ambilTahunDariTanggal() {
        if (tanggalDiterima && tahunDiterima) {
            tahunDiterima.value = tanggalDiterima.value ? tanggalDiterima.value.split('-')[0] : '';
        }
    }
    if (tanggalDiterima) {
        tanggalDiterima.addEventListener('change', ambilTahunDariTanggal);
        ambilTahunDariTanggal();
    }

    // ======================================
    // 3. FUNGSI MODAL UBAH STATUS (TETAP DIPERTAHANKAN)
    // ======================================
    window.tampilkanFormNonAktif = function(id) {
        const status = document.getElementById(`status${id}`)?.value;
        const form = document.getElementById(`formNonAktif${id}`);
        if (form) form.classList.toggle('d-none', status !== 'Non Aktif');
    };

    window.tampilkanSekolahTujuan = function(id) {
        const jenis = document.getElementById(`jenis${id}`)?.value;
        const kolom = document.getElementById(`kolomSekolah${id}`);
        if (kolom) kolom.classList.toggle('d-none', jenis !== 'Pindah');
    };

    document.addEventListener('shown.bs.modal', function(e) {
        if (e.target.id.startsWith('modalStatus')) {
            const id = e.target.id.replace('modalStatus', '');
            tampilkanFormNonAktif(id);
            tampilkanSekolahTujuan(id);
        }
    });

});