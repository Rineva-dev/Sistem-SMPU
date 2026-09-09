document.addEventListener('DOMContentLoaded', function () {
    const modalTambah = document.getElementById('modalTambah');
    const formTambah = modalTambah ? modalTambah.querySelector('form') : null;
    const btnTambahBaru = document.querySelector('[data-bs-target="#modalTambah"]');
    const semuaBtnEdit = document.querySelectorAll('.btn-warning[title="Ubah"]');
    const semuaBtnStatus = document.querySelectorAll('.btn-secondary[title="Nonaktifkan"], .btn-success[title="Aktifkan"]');
    const nominalInput = document.getElementById('nominalInput');
    const nominalAsli = document.getElementById('nominalAsli');

    let modeEdit = false;
    let idDataEdit = null;

    function formatRupiah(angka) {
        let angkaBersih = angka.replace(/[^0-9]/g, '');
        if (!angkaBersih) return '';
        return 'Rp ' + angkaBersih.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function isiNominalEdit(nilaiAngka) {
        if (!nilaiAngka) {
            nominalInput.value = '';
            nominalAsli.value = '';
            return;
        }
        nominalAsli.value = nilaiAngka;
        nominalInput.value = formatRupiah(nilaiAngka);
    }
    window.isiNominalEdit = isiNominalEdit;

    if (nominalInput && nominalAsli) {
        nominalInput.addEventListener('input', function () {
            let posKursor = this.selectionStart;
            let nilaiAsli = this.value.replace(/[^0-9]/g, '');
            let panjangSebelum = this.value.length;

            this.value = formatRupiah(this.value);
            nominalAsli.value = nilaiAsli;

            let panjangSesudah = this.value.length;
            let selisih = panjangSesudah - panjangSebelum;
            this.selectionStart = this.selectionEnd = posKursor + selisih;
        });
    }

    if (btnTambahBaru && modalTambah) {
        btnTambahBaru.addEventListener('click', function () {
            modeEdit = false;
            idDataEdit = null;
            if (formTambah) formTambah.reset();
            const judulModal = modalTambah.querySelector('.modal-title');
            if (judulModal) judulModal.textContent = 'Tambah Tarif Baru';

            if (nominalInput) nominalInput.value = '';
            if (nominalAsli) nominalAsli.value = '';

            const oldEditId = formTambah.querySelector('[name="edit_id"]');
            if (oldEditId) oldEditId.remove();

            setTimeout(() => {
                window.initCustomSelect(modalTambah.querySelectorAll('.custom-select'));
            }, 100);
        });
    }

    semuaBtnEdit.forEach(btn => {
        btn.addEventListener('click', function () {
            modeEdit = true;
            const baris = this.closest('tr');

            idDataEdit = baris.dataset.id;
            const namaPenuh = baris.querySelector('td:nth-child(2)').textContent.trim();
            const kode = baris.dataset.kode;
            const pola = baris.dataset.pola;
            const nominal = baris.querySelector('td:nth-child(4)').textContent.replace(/\D/g, '');
            const keterangan = baris.dataset.keterangan;

            // Pisahkan nama jadi jenis utama + kelompok
            let jenisUtama = namaPenuh;
            let namaKelompok = '';
            if(namaPenuh.includes(' - ')){
                let bagian = namaPenuh.split(' - ', 1);
                jenisUtama = bagian[0];
                namaKelompok = namaPenuh.replace(bagian[0] + ' - ', '');
            }

            formTambah.querySelector('[name="jenis_utama"]').value = jenisUtama;
            // Trigger event agar pilihan kelompok muncul
            formTambah.querySelector('[name="jenis_utama"]').dispatchEvent(new Event('change'));
            
            // Isi pilihan kelompok setelah muncul
            setTimeout(() => {
                if(namaKelompok){
                    formTambah.querySelector('[name="nama_kelompok"]').value = namaKelompok;
                }
            }, 50);

            formTambah.querySelector('[name="kode"]').value = kode;
            formTambah.querySelector('[name="pola_waktu"]').value = pola;
            window.isiNominalEdit(nominal);
            formTambah.querySelector('[name="keterangan"]').value = keterangan;

            modalTambah.querySelector('.modal-title').textContent = 'Ubah Tarif';
            bootstrap.Modal.getOrCreateInstance(modalTambah).show();
        });
    });

    // === TOMBOL UBAH STATUS ===
    semuaBtnStatus.forEach(btn => {
        btn.addEventListener('click', function () {
            const baris = this.closest('tr');
            const id = baris.dataset.id;
            const statusSekarang = this.getAttribute('title');

            if (!confirm(`Yakin ingin ${statusSekarang} jenis pembayaran ini?`)) return;

            // Kirim data ke server
            fetch(`/bendahara/pengaturan-pembayaran/status/${id}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.sukses) {
                    // Muat ulang halaman agar tabel terbaru
                    window.location.reload();
                } else {
                    alert(data.pesan || 'Gagal mengubah status!');
                }
            })
            .catch(err => {
                alert('Terjadi kesalahan koneksi!');
            });
        });
    });

    if (formTambah) {
        formTambah.addEventListener('submit', function (e) {

            const nilaiNominal = nominalAsli.value;
            const nominal = parseInt(nilaiNominal);
            const kode = this.kode.value.trim();

            if (!kode) {
                alert('Kode unik tidak boleh kosong!');
                e.preventDefault();
                return;
            }
            if (isNaN(nominal) || nominal <= 0) {
                alert('Nominal harus berupa angka positif!');
                e.preventDefault();
                return;
            }

            if (modeEdit && idDataEdit) {
                let inputId = formTambah.querySelector('[name="edit_id"]');
                if (!inputId) {
                    inputId = document.createElement('input');
                    inputId.type = 'hidden';
                    inputId.name = 'edit_id';
                    formTambah.appendChild(inputId);
                }
                inputId.value = idDataEdit;
            }
        });
    }
});