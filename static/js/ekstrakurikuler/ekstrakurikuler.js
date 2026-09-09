document.addEventListener('DOMContentLoaded', function () {
    // ==============================================
    // MODAL EDIT EKSKUL
    // ==============================================
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = this.dataset.id;
            document.getElementById('formEdit').action = `/data-ekskul/ubah/${id}`;
            
            document.getElementById('editNama').value = this.dataset.nama;
            document.getElementById('editPembina').value = this.dataset.pembina || '';
            document.getElementById('editKeterangan').value = this.dataset.keterangan || '';

            const tglMulai = this.dataset.tgl_mulai || '';
            const tglSelesai = this.dataset.tgl_selesai || '';
            document.getElementById('editTglMulai').value = tglMulai;
            document.getElementById('editTglSelesai').value = tglSelesai;

            const modal = new bootstrap.Modal(document.getElementById('modalEdit'), {
                backdrop: 'static',
                keyboard: false
            });
            modal.show();

            setTimeout(() => {
                const wrapMulai = document.getElementById('editTglMulai').closest('.custom-date');
                const wrapSelesai = document.getElementById('editTglSelesai').closest('.custom-date');

                if (tglMulai && wrapMulai) {
                    const inputManual = wrapMulai.querySelector('.custom-date__input-manual');
                    if (inputManual) {
                        const d = String(new Date(tglMulai).getDate()).padStart(2,'0');
                        const m = String(new Date(tglMulai).getMonth()+1).padStart(2,'0');
                        const y = new Date(tglMulai).getFullYear();
                        inputManual.value = `${d}/${m}/${y}`;
                    }
                }

                if (tglSelesai && wrapSelesai) {
                    const inputManual = wrapSelesai.querySelector('.custom-date__input-manual');
                    if (inputManual) {
                        const d = String(new Date(tglSelesai).getDate()).padStart(2,'0');
                        const m = String(new Date(tglSelesai).getMonth()+1).padStart(2,'0');
                        const y = new Date(tglSelesai).getFullYear();
                        inputManual.value = `${d}/${m}/${y}`;
                    }
                }
            }, 150);
        });
    });

    // ==============================================
    // MODAL HAPUS
    // ==============================================
    document.querySelectorAll('.btn-hapus').forEach(btn => {
        btn.addEventListener('click', function(){
            const id = this.dataset.id;
            document.getElementById('formHapus').action = `/data-ekskul/hapus/${id}`;
            new bootstrap.Modal(document.getElementById('modalHapus'), {
                backdrop: 'static',
                keyboard: false
            }).show();
        });
    });

    // ==============================================
    // MODAL ANGGOTA - DIPERBAIKI & DIPERCEPAT
    // ==============================================
    function hitungJumlah() {
        const jmlBelum = document.querySelectorAll('#daftarBelum tr').length;
        const jmlSudah = document.querySelectorAll('#daftarSudah tr').length;
        document.getElementById('jmlBelum').textContent = `${jmlBelum} siswa`;
        document.getElementById('jmlSudah').textContent = `${jmlSudah} siswa`;
    }

    // Pilih/Batal pilih siswa
    document.addEventListener('click', e => {
        const baris = e.target.closest('.pilih-siswa');
        if (baris) baris.classList.toggle('table-active');
    });

    // Masukkan ke anggota
    document.getElementById('btnTambahSiswa').addEventListener('click', () => {
        document.querySelectorAll('#daftarBelum tr.table-active').forEach(tr => {
            tr.classList.remove('table-active');
            document.getElementById('daftarSudah').appendChild(tr);
        });
        hitungJumlah();
    });

    // Keluarkan dari anggota
    document.getElementById('btnKeluarkanSiswa').addEventListener('click', () => {
        document.querySelectorAll('#daftarSudah tr.table-active').forEach(tr => {
            tr.classList.remove('table-active');
            document.getElementById('daftarBelum').appendChild(tr);
        });
        hitungJumlah();
    });

    // ✅ BAGIAN PENTING: BUKA MODAL & PILIH ANGGOTA DENGAN BENAR
    document.querySelectorAll('.btn-anggota').forEach(btn => {
        btn.addEventListener('click', async () => {
            const idEkskul = btn.dataset.id;
            document.getElementById('namaEkskul').textContent = btn.dataset.nama;
            document.getElementById('formAnggota').action = `/data-ekskul/anggota/${idEkskul}`;

            try {
                const res = await fetch(`/data-ekskul/${idEkskul}/anggota`);
                if (!res.ok) throw new Error('Gagal ambil data');
                const anggotaTerdaftar = await res.json();

                // ==============================================
                // ✅ PERBAIKAN UTAMA: KEMBALIKAN SEMUA KE KIRI DULU
                // ==============================================
                // Pindahkan semua baris dari kolom kanan kembali ke kolom kiri
                document.querySelectorAll('#daftarSudah tr').forEach(tr => {
                    document.getElementById('daftarBelum').appendChild(tr);
                    tr.classList.remove('table-active'); // Hapus tanda pilih juga
                });

                // ✅ Baru pindahkan siswa yang BENAR-BENAR sudah terdaftar ke kanan
                anggotaTerdaftar.forEach(item => {
                    const barisSiswa = document.querySelector(`#daftarBelum tr[data-id="${item.id}"]`);
                    if (barisSiswa) {
                        document.getElementById('daftarSudah').appendChild(barisSiswa);
                    }
                });

                hitungJumlah();
            } catch (err) {
                console.error('Gagal memuat anggota:', err);
                alert('Gagal memuat data anggota!');
            }

            new bootstrap.Modal(document.getElementById('modalAnggota'), {
                backdrop: 'static',
                keyboard: false
            }).show();
        });
    });

    // ✅ KIRIM DATA SAAT DISIMPAN
    document.getElementById('formAnggota').addEventListener('submit', () => {
        document.querySelectorAll('#formAnggota input[name="anggota_id[]"]').forEach(i => i.remove());
        
        document.querySelectorAll('#daftarSudah tr').forEach(tr => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'anggota_id[]';
            input.value = tr.dataset.id;
            document.getElementById('formAnggota').appendChild(input);
        });
    });

    document.addEventListener('DOMContentLoaded', hitungJumlah);

    // ==============================================
    // TOMBOL JURNAL
    // ==============================================
    document.querySelectorAll('.btn-jurnal').forEach(btn => {
        btn.addEventListener('click', function(){
            const id = this.dataset.id;
            window.location.href = `/data-ekskul/${id}/jurnal`;
        });
    });

    document.getElementById('modalAnggota').addEventListener('hidden.bs.modal', function () {
        document.querySelectorAll('.pilih-siswa.table-active').forEach(tr => {
            tr.classList.remove('table-active');
        });
    });
});