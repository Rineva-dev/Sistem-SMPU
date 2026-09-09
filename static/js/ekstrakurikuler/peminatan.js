document.addEventListener('DOMContentLoaded', function () {
    // Inisialisasi Bootstrap Modal
    const modalEdit = new bootstrap.Modal(document.getElementById('modalEdit'));
    const modalHapus = new bootstrap.Modal(document.getElementById('modalHapus'));
    const modalAnggota = new bootstrap.Modal(document.getElementById('modalAnggota'));

    // ==============================================
    // FUNGSI: MODAL EDIT PEMINATAN
    // ==============================================
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = this.dataset.id;
            document.getElementById('formEdit').action = `/data-peminatan/ubah/${id}`;
            
            // Isi semua kolom dari data atribut tombol
            document.getElementById('editNama').value = this.dataset.nama;
            document.getElementById('editPembina').value = this.dataset.pembina || '';
            document.getElementById('editKeterangan').value = this.dataset.keterangan || '';
            document.getElementById('editTglMulai').value = this.dataset.tgl_mulai || '';
            document.getElementById('editTglSelesai').value = this.dataset.tgl_selesai || '';
            
            modalEdit.show();
        });
    });

    // ==============================================
    // FUNGSI: MODAL HAPUS PEMINATAN
    // ==============================================
    document.querySelectorAll('.btn-hapus').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = this.dataset.id;
            document.getElementById('formHapus').action = `/data-peminatan/hapus/${id}`;
            modalHapus.show();
        });
    });

    // ==============================================
    // FUNGSI: KELOLA ANGGOTA PEMINATAN
    // ==============================================
    const formAnggota = document.getElementById('formAnggota');
    const daftarBelumEl = document.getElementById('daftarBelum');
    const daftarSudahEl = document.getElementById('daftarSudah');
    const jmlBelumEl = document.getElementById('jmlBelum');
    const jmlSudahEl = document.getElementById('jmlSudah');
    const namaPeminatanEl = document.getElementById('namaPeminatan');

    let semuaSiswaAwal = [];
    let anggotaTerpilih = [];
    let peminatanIdAktif = null;

    // Buka modal dan ambil data dari server
    document.querySelectorAll('.btn-anggota').forEach(btn => {
        btn.addEventListener('click', function () {
            peminatanIdAktif = this.dataset.id;
            namaPeminatanEl.textContent = this.dataset.nama;
            formAnggota.action = `/data-peminatan/anggota/${peminatanIdAktif}`;

            // Ambil daftar siswa yang sudah terdaftar
            fetch(`/data-peminatan/${peminatanIdAktif}/anggota`)
                .then(res => res.json())
                .then(data => {
                    anggotaTerpilih = data.anggota || [];
                    
                    // Salin data semua siswa dari tabel awal
                    semuaSiswaAwal = Array.from(daftarBelumEl.querySelectorAll('tr')).map(tr => ({
                        id: tr.dataset.id,
                        nisn: tr.cells[0].textContent.trim(),
                        nama: tr.cells[1].textContent.trim(),
                        kelas: tr.cells[2].textContent.trim(),
                        rombel: tr.cells[3].textContent.trim()
                    }));

                    tampilkanDaftar();
                    modalAnggota.show();
                })
                .catch(err => {
                    console.error('Gagal mengambil data anggota:', err);
                    alert('Gagal memuat data anggota!');
                });
        });
    });

    // Susun ulang tampilan siswa: yang masuk & yang belum
    function tampilkanDaftar() {
        daftarBelumEl.innerHTML = '';
        daftarSudahEl.innerHTML = '';

        semuaSiswaAwal.forEach(siswa => {
            const sudahAda = anggotaTerpilih.some(a => String(a.id) === String(siswa.id));
            const baris = buatBarisSiswa(siswa);
            
            if (!sudahAda) {
                daftarBelumEl.appendChild(baris);
            } else {
                daftarSudahEl.appendChild(baris.cloneNode(true));
            }
        });

        // Update jumlah
        jmlBelumEl.textContent = `${daftarBelumEl.children.length} siswa`;
        jmlSudahEl.textContent = `${daftarSudahEl.children.length} siswa`;

        // Aktifkan fungsi pilih baris
        aturPilihanBaris();
    }

    // Buat elemen baris tabel siswa
    function buatBarisSiswa(s) {
        const tr = document.createElement('tr');
        tr.setAttribute('role', 'button');
        tr.dataset.id = s.id;
        tr.innerHTML = `
            <td class="font-monospace text-muted">${s.nisn}</td>
            <td class="fw-medium">${s.nama}</td>
            <td>${s.kelas}</td>
            <td>${s.rombel}</td>
        `;
        return tr;
    }

    // Beri efek sorot saat baris diklik
    function aturPilihanBaris() {
        [daftarBelumEl, daftarSudahEl].forEach(tabel => {
            tabel.querySelectorAll('tr').forEach(tr => {
                tr.addEventListener('click', () => {
                    tr.classList.toggle('table-primary');
                });
            });
        });
    }

    // Pindahkan siswa terpilih ke daftar anggota
    document.getElementById('btnTambahSiswa').addEventListener('click', () => {
        daftarBelumEl.querySelectorAll('tr.table-primary').forEach(tr => {
            const idDipilih = tr.dataset.id;
            const dataSiswa = semuaSiswaAwal.find(s => String(s.id) === String(idDipilih));
            
            if (dataSiswa && !anggotaTerpilih.some(a => String(a.id) === String(idDipilih))) {
                anggotaTerpilih.push(dataSiswa);
            }
        });
        tampilkanDaftar();
    });

    // Keluarkan siswa dari daftar anggota
    document.getElementById('btnKeluarkanSiswa').addEventListener('click', () => {
        daftarSudahEl.querySelectorAll('tr.table-primary').forEach(tr => {
            const idDipilih = tr.dataset.id;
            anggotaTerpilih = anggotaTerpilih.filter(a => String(a.id) !== String(idDipilih));
        });
        tampilkanDaftar();
    });

    // Kirim data ID siswa yang terpilih ke backend
    formAnggota.addEventListener('submit', function (e) {
        e.preventDefault();
        
        // Hapus input lama jika ada
        this.querySelectorAll('input[name^="anggota_id"]').forEach(el => el.remove());

        // Buat input SESUAI nama yang dibaca backend: anggota_id[]
        anggotaTerpilih.forEach(item => {
            const inputId = document.createElement('input');
            inputId.type = 'hidden';
            inputId.name = 'anggota_id[]'; // <-- SESUAIKAN PERSIS!
            inputId.value = item.id;
            this.appendChild(inputId);
        });

        this.submit();
    });

    document.querySelectorAll('.btn-jurnal').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = this.dataset.id;
            const nama = this.dataset.nama;
            // ✅ SESUAIKAN URUTAN DENGAN RUTE: /data-peminatan/[ID]/jurnal
            window.location.href = `/data-peminatan/${id}/jurnal`;
        });
    });
});