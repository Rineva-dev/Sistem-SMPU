document.addEventListener('DOMContentLoaded', function() {

    window.bukaModalEdit = function(id, tahunMulai, tahunSelesai, tglMulai, tglSelesai, semester) {
        const elId = document.getElementById('edit_id');
        const elTahunMulai = document.getElementById('edit_tahun_mulai');
        const elTahunSelesai = document.getElementById('edit_tahun_selesai');
        const elSemester = document.getElementById('edit_semester');
        const elTglMulai = document.getElementById('edit_tanggal_mulai');
        const elTglSelesai = document.getElementById('edit_tanggal_selesai');

        if (!elId || !elTahunMulai || !elTglMulai) return;

        // Isi nilai dalam format YYYY-MM-DD (tanpa jam)
        elId.value = id;
        elTahunMulai.value = tahunMulai;
        elTahunSelesai.value = tahunSelesai;
        elSemester.value = semester;
        elTglMulai.value = tglMulai;
        elTglSelesai.value = tglSelesai;

        setTimeout(() => {
            const pembungkus1 = elTglMulai.closest('.custom-date');
            const pembungkus2 = elTglSelesai.closest('.custom-date');
            const tampilan1 = pembungkus1?.querySelector('.custom-date__input-manual');
            const tampilan2 = pembungkus2?.querySelector('.custom-date__input-manual');

            if (tglMulai && tampilan1) {
                const [thn, bln, tgl] = tglMulai.split('-');
                tampilan1.value = `${tgl}/${bln}/${thn}`;
                pembungkus1.classList.add('filled');
                
                // Set tanggal tanpa bagian jam
                const dateObj1 = new Date(tglMulai);
                if (!isNaN(dateObj1.getTime())) {
                    pembungkus1.selectedDate = dateObj1;
                    elTglMulai.value = tglMulai;
                }
            }

            if (tglSelesai && tampilan2) {
                const [thn, bln, tgl] = tglSelesai.split('-');
                tampilan2.value = `${tgl}/${bln}/${thn}`;
                pembungkus2.classList.add('filled');
                
                const dateObj2 = new Date(tglSelesai);
                if (!isNaN(dateObj2.getTime())) {
                    pembungkus2.selectedDate = dateObj2;
                    elTglSelesai.value = tglSelesai;
                }
            }

            elTglMulai.dispatchEvent(new Event('input', { bubbles: true }));
            elTglMulai.dispatchEvent(new Event('change', { bubbles: true }));
            elTglSelesai.dispatchEvent(new Event('input', { bubbles: true }));
            elTglSelesai.dispatchEvent(new Event('change', { bubbles: true }));

        }, 150);

        new bootstrap.Modal(document.getElementById('modalEdit')).show();
    };

    // Sisa kode tetap sama seperti sebelumnya ...
    const tahunMulaiInput = document.getElementById('tahun_mulai');
    if (tahunMulaiInput) {
        tahunMulaiInput.addEventListener('input', function() {
            const selesai = document.getElementById('tahun_selesai');
            if (this.value && !selesai.value) selesai.value = parseInt(this.value) + 1;
        });
    }

    const editTahunMulai = document.getElementById('edit_tahun_mulai');
    if (editTahunMulai) {
        editTahunMulai.addEventListener('input', function() {
            const selesai = document.getElementById('edit_tahun_selesai');
            if (this.value && !selesai.value) selesai.value = parseInt(this.value) + 1;
        });
    }

    const formEdit = document.getElementById('formEdit');
    if (formEdit) {
        formEdit.addEventListener('submit', function(e) {
            const tglMulai = document.getElementById('edit_tanggal_mulai').value.trim();
            const tglSelesai = document.getElementById('edit_tanggal_selesai').value.trim();

            if (!tglMulai || !tglSelesai) {
                e.preventDefault();
                alert('⚠️ Tanggal mulai dan selesai wajib diisi!');
                return false;
            }
        });
    }

});