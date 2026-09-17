document.addEventListener('DOMContentLoaded', function(){
    const wadah = document.getElementById('wadahDaftarHari');
    const btnTambahHari = document.getElementById('btnTambahHari');
    const elemenJson = document.getElementById('data-daftar-mapel-json');
    
    const daftarHariBenar = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];
    
    function urutkanSemuaHari() {
        const daftarKartu = Array.from(wadah.querySelectorAll('.hari-card'));
        daftarKartu.sort((a, b) => {
            const namaA = a.querySelector('.hari-nama').textContent.trim();
            const namaB = b.querySelector('.hari-nama').textContent.trim();
            return daftarHariBenar.indexOf(namaA) - daftarHariBenar.indexOf(namaB);
        });
        daftarKartu.forEach(kartu => wadah.appendChild(kartu));
    }
    
    function cekNamaHariBenar(namaHari) {
        return daftarHariBenar.includes(namaHari.trim());
    }
    
    function cekHariSudahAda(namaHari) {
        const semuaKartu = wadah.querySelectorAll('.hari-card');
        const namaBersih = namaHari.trim();
        for(let kartu of semuaKartu) {
            const namaYangAda = kartu.querySelector('.hari-nama').textContent.trim();
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
        let opsi = `<option value="">-- Pilih Mata Pelajaran --</option>`;
        opsi += `<option value="imtaq">🕌 Imtaq</option>`;
        opsi += `<option value="upacara">🇮🇩 Upacara Bendera</option>`;
        daftarMapel.forEach(item => {
            opsi += `<option value="${item.id}">${item.nama}</option>`;
        });
        return opsi;
    }
    
    function buatBaris(namaHari) {
        const baris = document.createElement('div');
        baris.className = 'baris-jadwal';
        baris.innerHTML = `
            <input type="hidden" name="hari[]" value="${namaHari}">
            <div class="jam-input-group">
                <input type="time" name="jam_mulai[]" class="form-control jam-input" required>
                <span class="jam-pemisah">s/d</span>
                <input type="time" name="jam_selesai[]" class="form-control jam-input" required>
            </div>
            <div class="mapel-select-group">
                <select name="mapel_id[]" class="form-select mapel-select" required>
                    ${buatPilihanMapel()}
                </select>
            </div>
            <button type="button" class="btn-hapus-baris hapus-baris" title="Hapus baris">
                <i class="fas fa-times"></i>
            </button>
        `;
        return baris;
    }
    
    btnTambahHari.addEventListener('click', function(){
        let namaHari = prompt("Masukkan Nama Hari:\nPilihan: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu");
        if(!namaHari) return;
        namaHari = namaHari.trim();
        
        if(!cekNamaHariBenar(namaHari)) {
            alert(`"${namaHari}" bukan nama hari yang benar!\n\nHarap tulis: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu`);
            return;
        }
        if(cekHariSudahAda(namaHari)) {
            alert(`Hari "${namaHari}" sudah ada!`);
            return;
        }
        
        const kartu = document.createElement('div');
        kartu.className = 'hari-card';
        kartu.innerHTML = `
            <div class="hari-header">
                <span class="hari-nama"><i class="fas fa-sun"></i> ${namaHari}</span>
                <button type="button" class="btn-hapus-hari hapus-hari">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
            <div class="hari-body"></div>
        `;
        kartu.querySelector('.hari-body').appendChild(buatBaris(namaHari));
        kartu.querySelector('.hari-body').insertAdjacentHTML('beforeend', `
            <button type="button" class="btn-tambah-baris tambah-baris">
                <i class="fas fa-plus-circle"></i> Tambah Jam
            </button>
        `);
        wadah.appendChild(kartu);
        urutkanSemuaHari();
    });
    
    wadah.addEventListener('click', function(e){
        if(e.target.closest('.tambah-baris')){
            e.preventDefault();
            const tombol = e.target.closest('.tambah-baris');
            const hari = tombol.closest('.hari-body').querySelector('input[name="hari[]"]').value;
            const barisBaru = buatBaris(hari);
            tombol.before(barisBaru);
        }
        if(e.target.closest('.hapus-baris')){
            const baris = e.target.closest('.baris-jadwal');
            if(baris.parentElement.querySelectorAll('.baris-jadwal').length > 1) baris.remove();
            else alert('Minimal 1 baris per hari!');
        }
        if(e.target.closest('.hapus-hari')){
            if(confirm('Yakin hapus hari ini?')) {
                e.target.closest('.hari-card').remove();
                urutkanSemuaHari();
            }
        }
    });
    
    urutkanSemuaHari();
});