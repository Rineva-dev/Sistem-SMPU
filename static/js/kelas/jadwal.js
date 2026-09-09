document.addEventListener('DOMContentLoaded', function(){
    const wadah = document.getElementById('wadahDaftarHari');
    const btnTambahHari = document.getElementById('btnTambahHari');
    const elemenJson = document.getElementById('data-daftar-mapel-json');

    // ✅ DAFTAR NAMA HARI YANG DIPERBOLEHKAN SAJA
    const daftarHariBenar = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];

    // ✅ FUNGSI URUTKAN HARI SELALU SESUAI URUTAN BAKU
    function urutkanSemuaHari() {
        const daftarKartu = Array.from(wadah.querySelectorAll('.card.mb-3'));
        daftarKartu.sort((a, b) => {
            const namaA = a.querySelector('.card-header').textContent.trim();
            const namaB = b.querySelector('.card-header').textContent.trim();
            return daftarHariBenar.indexOf(namaA) - daftarHariBenar.indexOf(namaB);
        });
        daftarKartu.forEach(kartu => wadah.appendChild(kartu));
    }

    // ✅ CEK APAKAH NAMA HARI DITULIS DENGAN BENAR
    function cekNamaHariBenar(namaHari) {
        return daftarHariBenar.includes(namaHari.trim());
    }

    // ✅ CEK APAKAH HARI SUDAH ADA (TIDAK BOLEH GANDA)
    function cekHariSudahAda(namaHari) {
        const semuaKartu = wadah.querySelectorAll('.card.mb-3');
        const namaBersih = namaHari.trim();
        for(let kartu of semuaKartu) {
            const namaYangAda = kartu.querySelector('.card-header').textContent.trim();
            if(namaYangAda === namaBersih) return true;
        }
        return false;
    }

    let daftarMapel = [];
    try {
        const teksBersih = elemenJson.textContent.trim();
        daftarMapel = JSON.parse(teksBersih);
    } catch (err) {
        console.error("JSON Error:", err);
        alert("Data mapel bermasalah!");
        return;
    }

    function buatPilihanMapel() {
        let opsi = `<option value="">-- Pilih Mapel --</option>`;
        opsi += `<option value="imtaq">Imtaq</option>`;
        opsi += `<option value="upacara">Upacara Bendera</option>`;
        daftarMapel.forEach(item => {
            opsi += `<option value="${item.id}">${item.nama}</option>`;
        });
        return opsi;
    }

    function buatBaris(namaHari) {
        const baris = document.createElement('div');
        baris.className = 'baris-jadwal d-flex gap-2 align-items-center mb-2';
        baris.innerHTML = `
            <input type="hidden" name="hari[]" value="${namaHari}">
            <div class="custom-time">
                <input type="time" name="jam_mulai[]" class="form-control" required>
            </div>
            <span class="text-muted">-</span>
            <div class="custom-time">
                <input type="time" name="jam_selesai[]" class="form-control" required>
            </div>
            <div class="custom-select">
                <select name="mapel_id[]" class="form-select" required>
                    ${buatPilihanMapel()}
                </select>
            </div>
            <button type="button" class="btn btn-outline-danger btn-sm hapus-baris">
                <i class="fas fa-times"></i>
            </button>
        `;
        return baris;
    }

    // Tambah Hari Baru
    btnTambahHari.addEventListener('click', function(){
        let namaHari = prompt("Masukkan Nama Hari:\nPilihan: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu");
        if(!namaHari) return;

        namaHari = namaHari.trim();

        // ✅ 1. CEK APAKAH TULISANNYA BENAR
        if(!cekNamaHariBenar(namaHari)) {
            alert(`"${namaHari}" bukan nama hari yang benar!\n\nHarap tulis persis:\nSenin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu`);
            return;
        }

        // ✅ 2. CEK APAKAH SUDAH ADA
        if(cekHariSudahAda(namaHari)) {
            alert(`Hari "${namaHari}" sudah ada!`);
            return;
        }

        const kartu = document.createElement('div');
        kartu.className = 'card mb-3 shadow-sm';
        kartu.innerHTML = `
            <div class="card-header bg-light d-flex justify-content-between align-items-center fw-bold">
                <i class="fas fa-calendar-day me-2"></i> ${namaHari}
                <button type="button" class="btn btn-sm btn-outline-danger hapus-hari"><i class="fas fa-trash"></i></button>
            </div>
            <div class="card-body"></div>
        `;
        kartu.querySelector('.card-body').appendChild(buatBaris(namaHari));
        kartu.querySelector('.card-body').insertAdjacentHTML('beforeend', `
            <button type="button" class="btn btn-sm btn-outline-primary tambah-baris"><i class="fas fa-plus me-1"></i> Tambah Jam</button>
        `);
        wadah.appendChild(kartu);
        
        if(window.initCustomSelect) window.initCustomSelect(kartu.querySelectorAll('.custom-select'));
        if(window.initCustomTime) window.initCustomTime(kartu.querySelectorAll('.custom-time'));

        urutkanSemuaHari();
    });

    // Aksi Tombol
    wadah.addEventListener('click', function(e){
        // Tambah Jam
        if(e.target.closest('.tambah-baris')){
            e.preventDefault();
            e.stopPropagation();
            const tombol = e.target.closest('.tambah-baris');
            const hari = tombol.closest('.card-body').querySelector('input[name="hari[]"]').value;
            const barisBaru = buatBaris(hari);
            tombol.before(barisBaru);
            
            if(window.initCustomSelect) window.initCustomSelect(barisBaru.querySelectorAll('.custom-select'));
            if(window.initCustomTime) window.initCustomTime(barisBaru.querySelectorAll('.custom-time'));
        }
        // Hapus Baris
        if(e.target.closest('.hapus-baris')){
            const baris = e.target.closest('.baris-jadwal');
            if(baris.parentElement.querySelectorAll('.baris-jadwal').length > 1) baris.remove();
            else alert('Minimal 1 baris per hari!');
        }
        // Hapus Hari
        if(e.target.closest('.hapus-hari')){
            if(confirm('Yakin hapus hari ini?')) {
                e.target.closest('.card.mb-3').remove();
                urutkanSemuaHari();
            }
        }
    });

    urutkanSemuaHari();

});