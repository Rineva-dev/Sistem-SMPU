// ==========================================
// FUNGSI PEMBANTU UMUM (SAMA DIPAKAI DI RINCIAN)
// ==========================================
function formatRupiah(angka) {
    if (angka === null || angka === undefined || isNaN(angka)) angka = 0;
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(angka).replace(/Rp\s*/g, 'Rp ');
}

function ambilAngkaMurni(teks) {
    if (!teks) return 0;
    let bersih = String(teks).replace(/[^\d]/g, '');
    return bersih ? Number(bersih) : 0;
}

function ambilWaktuSekarang() {
    const sekarang = new Date();
    const tgl = sekarang.getFullYear() + '-' +
        String(sekarang.getMonth() + 1).padStart(2, '0') + '-' +
        String(sekarang.getDate()).padStart(2, '0');
    const jam = String(sekarang.getHours()).padStart(2, '0') + ':' +
        String(sekarang.getMinutes()).padStart(2, '0');
    return tgl + 'T' + jam;
}

function resetStatusSemua(wadah) {
    wadah.querySelectorAll('.status-info').forEach(el => {
        el.textContent = "Belum diproses";
        el.className = "badge bg-secondary status-info";
    });
}

function prosesBagiPembayaran(jumlahBayar, wadah) {
    console.log("✅ PROSES HITUNG =", jumlahBayar);
    const daftarCek = wadah.querySelectorAll('.cek-tagihan:checked');
    let sisaUang = Number(jumlahBayar) || 0;
    let rincianSimpan = [];

    daftarCek.forEach(cek => {
        const baris = cek.closest('tr');
        if (!baris) return;

        const sisaTagihanSekarang = Math.max(0, Number(baris.dataset.sisaTagihan) || 0);
        const nominalAsli = Number(baris.dataset.nominalAsli) || 0;
        const sudahDibayarSebelumnya = nominalAsli - sisaTagihanSekarang;
        const statusEl = baris.querySelector('td:last-child .status-info');

        let dibayar = 0;
        let sisaTagih = sisaTagihanSekarang;

        if (sisaUang <= 0) {
            dibayar = 0;
            sisaTagih = sisaTagihanSekarang;
            if (statusEl) { statusEl.textContent = "Belum dibayar"; statusEl.className = "badge bg-secondary status-info"; }
        } 
        else if (sisaUang >= sisaTagihanSekarang) {
            dibayar = sisaTagihanSekarang; // Tetap lunasi sisa tagihannya
            sisaTagih = 0;
            sisaUang -= sisaTagihanSekarang; // Sisa uang berkurang sesuai yang dipakai
            if (statusEl) { statusEl.textContent = "✅ Lunas"; statusEl.className = "badge bg-success status-info"; }
        }

        else {
            dibayar = sisaUang;
            sisaTagih = sisaTagihanSekarang - dibayar;
            sisaUang = 0;
            if (statusEl) { statusEl.textContent = `⚠️ Sebagian (${formatRupiah(dibayar)})`; statusEl.className = "badge bg-warning text-dark status-info"; }
        }

        dibayar = Math.min(dibayar, sisaTagihanSekarang);

        rincianSimpan.push({ 
            id: baris.dataset.id, 
            nominal_asli: nominalAsli,

            dibayar: sudahDibayarSebelumnya + dibayar,
            sisa_hutang: sisaTagih 
        });
    });
    return rincianSimpan;
}

// ==========================================
// MODAL PEMBAYARAN DARI DAFTAR UTAMA
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
    const btnBuka = document.getElementById('btnBukaPembayaran');
    const modalEl = document.getElementById('modalPembayaranDaftar');
    const pilihSiswa = document.getElementById('pilihSiswaBayar');
    const infoSiswa = document.getElementById('infoSiswaTerpilih');
    const infoNama = document.getElementById('infoNama');
    const infoNisn = document.getElementById('infoNisn');
    const infoKelas = document.getElementById('infoKelas');
    const wadahTagihan = document.getElementById('wadahDaftarTagihanUtama');
    const blokPilihSemua = document.getElementById('blokPilihSemua');
    const blokBayar = document.getElementById('blokPembayaranLengkap');
    const centangSemua = document.getElementById('pilihSemuaBelumLunasUtama');
    const metodeBayar = document.getElementById('metodeBayarUtama');
    const totalBayar = document.getElementById('totalDipilihUtama');
    const uangDiterima = document.getElementById('uangDiterimaUtama');
    const catatan = document.getElementById('catatanBayarUtama');
    const btnSimpan = document.getElementById('btnSimpanPembayaranUtama');
    let daftarTagihanMuat = [];
    let nilaiAngkaSimpan = 0;

    // Inisialisasi ikon lipat/buka
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(el => {
        el.addEventListener('shown.bs.collapse', () => el.querySelector('i').classList.toggle('fa-chevron-down', false) || el.querySelector('i').classList.toggle('fa-chevron-up', true))
        el.addEventListener('hidden.bs.collapse', () => el.querySelector('i').classList.toggle('fa-chevron-up', false) || el.querySelector('i').classList.toggle('fa-chevron-down', true))
    });

    // 🔓 BUKA MODAL + RESET KE AWAL
    if(btnBuka && modalEl){
        btnBuka.addEventListener('click', function(){
            const modal = new bootstrap.Modal(modalEl, {backdrop:'static', keyboard:false});
            modal.show();
            resetIsiModal();

            const tanggalJamEl = document.getElementById('tanggalJamBayarUtama');
            if(tanggalJamEl) {
                const sekarang = new Date();

                tanggalJamEl.value = ambilWaktuSekarang();
                tanggalJamEl.dispatchEvent(new Event('change'));
            }
            setTimeout(()=>{
                if(window.initCustomSelect) document.querySelectorAll('.modal-bayar-select').forEach(window.initCustomSelect);
            },100);
        });
    }

    if(pilihSiswa){
        pilihSiswa.addEventListener('change', async function(){
            const idSiswa = this.value.trim();
            resetTampilanMuat();
            if(!idSiswa){ resetIsiModal(); return; }

            const opsiTerpilih = this.querySelector(`option[value="${idSiswa}"]`);
            infoNama.textContent = opsiTerpilih.dataset.nama;
            infoNisn.textContent = opsiTerpilih.dataset.nisn;
            infoKelas.textContent = opsiTerpilih.dataset.kelas;
            infoSiswa.classList.remove('d-none');
            wadahTagihan.innerHTML = `<div class="text-center py-4"><i class="fas fa-spinner fa-spin fa-lg text-primary"></i><p class="mt-2">Sedang memuat daftar tagihan...</p></div>`;

            try {
                const res = await fetch(`/bendahara/api-rincian-tagihan/${idSiswa}`);
                if(!res.ok) throw new Error(`Server: ${res.status} - ${res.statusText}`);
                const data = await res.json();
                daftarTagihanMuat = (data.tagihan || []).filter(item => {
                    const sisa = Math.max(0, (item.nominal || 0) - (item.sudah_dibayar || 0));
                    return sisa > 0;
                });
                tampilkanDaftarTagihan(daftarTagihanMuat);
                blokPilihSemua.classList.remove('d-none');
                blokBayar.classList.remove('d-none');
                hitungTotalTerpilih();
                setTimeout(()=>{ if(window.initCustomSelect) document.querySelectorAll('.modal-bayar-select').forEach(window.initCustomSelect); },100);
            } catch (err) {
                wadahTagihan.innerHTML = `<div class="text-center text-danger py-4"><i class="fas fa-exclamation-triangle"></i> ${err.message}</div>`;
            }
        });
    }

    // ✅ HITUNG TOTAL SAMA RINCIAN
    metodeBayar.addEventListener('change', hitungTotalTerpilih);

    // ✅ HITUNG TOTAL & AKTIFKAN TOMBOL DIPERBAIKI
    function hitungTotalTerpilih(){
        let total = 0;
        wadahTagihan.querySelectorAll('.cek-tagihan:checked').forEach(c => total += Number(c.value) || 0);
        totalBayar.value = formatRupiah(total);

        if(total ===0){
            uangDiterima.value='';
            nilaiAngkaSimpan=0;
            resetStatusSemua(wadahTagihan);
            btnSimpan.disabled = true;
            return;
        }

        let metodeTerisi = !!metodeBayar.value.trim();
        btnSimpan.disabled = !(metodeTerisi && nilaiAngkaSimpan > 0);
    }

    // ✅ CENTANG SEMUA & KELOMPOK
    if(centangSemua){
        centangSemua.addEventListener('change', function(){
            wadahTagihan.querySelectorAll('.cek-tagihan, .pilih-semua-kelompok').forEach(c=>c.checked=this.checked);
            hitungTotalTerpilih();
            sesuaikanNominalDanStatus();
        });
    }
    wadahTagihan.addEventListener('change', e=>{
        if(e.target.classList.contains('pilih-semua-kelompok')){
            // Centang semua anak dalam kelompok
            document.querySelectorAll(`#${e.target.dataset.kel} .cek-tagihan`).forEach(c=>c.checked=e.target.checked);
            // ✅ PENTING: Setelah centang, langsung hitung total & atur status
            hitungTotalTerpilih();
            sesuaikanNominalDanStatus();
        }
        if(e.target.classList.contains('cek-tagihan')){
            hitungTotalTerpilih();
            sesuaikanNominalDanStatus();
        }
    });

    function sesuaikanNominalDanStatus(){
        const totalTagihBaru = ambilAngkaMurni(totalBayar.value);

        if(totalTagihBaru === 0){
            uangDiterima.value = '';
            nilaiAngkaSimpan = 0;
            resetStatusSemua(wadahTagihan);
        }
        else if(nilaiAngkaSimpan > totalTagihBaru){
            // ✅ OTOMATIS TURUNKAN KE TOTAL BARU
            nilaiAngkaSimpan = totalTagihBaru;
            uangDiterima.value = formatRupiah(nilaiAngkaSimpan);
            prosesBagiPembayaran(nilaiAngkaSimpan, wadahTagihan);
        }
        else if(nilaiAngkaSimpan > 0){
            prosesBagiPembayaran(nilaiAngkaSimpan, wadahTagihan);
        }

        wadahTagihan.querySelectorAll('tr').forEach(baris => {
            const cek = baris.querySelector('.cek-tagihan');
            const statusEl = baris.querySelector('.status-info');
            if(cek && !cek.checked && statusEl){
                statusEl.textContent = "Belum diproses";
                statusEl.className = "badge bg-secondary status-info";
            }
        });
    }

    uangDiterima.addEventListener('input', function () {
        const input = this;
        const cursor = input.selectionStart;
        const angka = ambilAngkaMurni(input.value);

        if (!angka) { 
            input.value = ''; 
            nilaiAngkaSimpan = 0; 
            resetStatusSemua(wadahTagihan);
            hitungTotalTerpilih();
            return; 
        }

        const jumlahDipilih = wadahTagihan.querySelectorAll('.cek-tagihan:checked').length;
        if(jumlahDipilih === 0){ 
            alert("Pilih dulu tagihan yang akan dibayar!"); 
            input.value=''; 
            nilaiAngkaSimpan=0; 
            resetStatusSemua(wadahTagihan);
            hitungTotalTerpilih();
            return; 
        }

        const totalTagih = ambilAngkaMurni(totalBayar.value);
        let angkaAkhir = angka;

        // ✅ =====================================================
        // PERBAIKAN: BATASI & SIMPAN NILAI YANG BENAR
        // ✅ =====================================================
        if(angka > totalTagih){ 
            alert(`Jumlah bayar lebih besar dari sisa tagihan!\nOtomatis disesuaikan menjadi ${formatRupiah(totalTagih)}`);
            angkaAkhir = totalTagih;
        }

        // ⭐ SANGAT PENTING: Simpan nilai yang SUDAH DIKOREKSI
        nilaiAngkaSimpan = angkaAkhir;

        // Format tampilan
        const sebelumCursor = input.value.substring(0,cursor);
        const digitSebelumCursor = (sebelumCursor.match(/\d/g)||[]).length;
        const hasilFormat = formatRupiah(angkaAkhir);
        input.value = hasilFormat;

        let digitDitemukan=0, posisiCursor=hasilFormat.length;
        for(let i=0;i<hasilFormat.length;i++){
            if(/\d/.test(hasilFormat[i])){ 
                digitDitemukan++; 
                if(digitDitemukan >= digitSebelumCursor){ posisiCursor=i+1; break; } 
            }
        }
        input.setSelectionRange(posisiCursor, posisiCursor);

        // ✅ Hitung pembagian dengan NILAI YANG SUDAH BENAR
        prosesBagiPembayaran(nilaiAngkaSimpan, wadahTagihan);
        hitungTotalTerpilih();
    });

    function tampilkanDaftarTagihan(arrTagihan){
        let kumpulKelompok={};
        arrTagihan.forEach(item => {
            let namaKelompok=item.nama||'Lainnya';
            if(!kumpulKelompok[namaKelompok]) kumpulKelompok[namaKelompok]=[];
            kumpulKelompok[namaKelompok].push(item);
        });
        if(Object.keys(kumpulKelompok).length===0){ 
            wadahTagihan.innerHTML='<div class="p-4 text-center text-muted">Semua tagihan sudah lunas!</div>'; 
            blokPilihSemua.classList.add('d-none'); 
            blokBayar.classList.add('d-none'); 
            return; 
        }
        let nomorKel=1, html='';
        for(let namaK in kumpulKelompok){
            let daftar=kumpulKelompok[namaK], idK='kel-utama-'+nomorKel++;
            html+=`
            <div class="card kelompok-modal mb-1 border">
                <div class="card-header d-flex align-items-center justify-content-between" data-bs-toggle="collapse" data-bs-target="#${idK}">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fas fa-chevron-down"></i>
                        <h6 class="mb-0 fw-semibold">${namaK}</h6>
                        <span class="badge bg-secondary">${daftar.length} tagihan</span>
                    </div>
                    <label class="form-check mb-0">
                        <input type="checkbox" class="form-check-input pilih-semua-kelompok" data-kel="${idK}"> Pilih Semua
                    </label>
                </div>
                <div id="${idK}" class="collapse">
                    <div class="p-2">
                        <table class="table table-sm mb-0">
                            <thead><tr>
                                <th width="40">Pilih</th>
                                <th>Keterangan</th>
                                <th width="140" class="text-end">Sisa Tagihan</th> <!-- ✅ UBAH JUDUL -->
                                <th width="200" class="text-center">Status</th>
                            </tr></thead>
                            <tbody>`;
            daftar.forEach(item=>{
                let disabledCek = item.status==='Lunas' ? 'disabled' : '';
                const sisaTagih = Math.max(0, (item.nominal || 0) - (item.sudah_dibayar || 0));
                const idTagihan = item.id || '';
                
                html+=`<tr data-id="${idTagihan}" 
                            data-nominal-asli="${item.nominal}" 
                            data-sisa-tagihan="${sisaTagih}">
                    <td class="text-center">
                        <input type="checkbox" class="form-check-input cek-tagihan" 
                            value="${sisaTagih}" ${disabledCek}> <!-- ✅ VALUE = SISA -->
                    </td>
                    <td class="text-start">${item.waktu||item.keterangan||''}</td>
                    <td class="text-end fw-bold text-danger">${formatRupiah(sisaTagih)}</td> <!-- ✅ TAMPILKAN SISA -->
                    <td class="text-center">
                        <span class="badge ${item.status==='Lunas'?'bg-success':'bg-secondary'} status-info">
                            ${item.status==='Lunas'?'✅ Lunas':'Belum diproses'}
                        </span>
                    </td>
                </tr>`;
            });
            html+=`</tbody></table></div></div></div>`;
        }
        wadahTagihan.innerHTML=html;
    }

    // 💾 SIMPAN KE SERVER
    if(btnSimpan){
        btnSimpan.addEventListener('click', async function(){
            const idSiswa = pilihSiswa.value;
            let jumlahBayar = nilaiAngkaSimpan;

            const totalTagihAkhir = ambilAngkaMurni(totalBayar.value);
            if (jumlahBayar > totalTagihAkhir) {
                jumlahBayar = totalTagihAkhir;
            }
            let rincianSimpan = prosesBagiPembayaran(jumlahBayar, wadahTagihan);
            let adaBayar = rincianSimpan.some(d=>d.dibayar>0);
            if(!adaBayar) return alert('Masukkan nominal uang yang diterima!');
            const metode = metodeBayar.value;
            const ket = catatan.value.trim();
            if(!metode) return alert('Pilih metode pembayaran!');

            btnSimpan.disabled = true;
            btnSimpan.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Sedang menyimpan...`;
            try {
                const tanggalJamEl = document.getElementById('tanggalJamBayarUtama');
                let tanggalBayarKirim = null;
                let tanggal_bayar = null;
                let jam_bayar = "00:00";

                if (tanggalJamEl && tanggalJamEl.value) {
                    tanggalBayarKirim = tanggalJamEl.value;

                    // ✅ Pisahkan tanggal & jam seperti di blok rincian tagihan
                    if (tanggalBayarKirim.includes('T')) {
                        const bagian = tanggalBayarKirim.split('T');
                        tanggal_bayar = bagian[0];
                        jam_bayar = bagian[1];
                    } else {
                        tanggal_bayar = tanggalBayarKirim;
                        jam_bayar = "00:00";
                    }
                }

                // ⚠️ Juga perbaiki id_siswa → harusnya idSiswa (sesuai deklarasi di atas)
                const kirim = await fetch('/bendahara/simpan-pembayaran', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    },
                    body: JSON.stringify({
                        id_siswa: idSiswa,
                        rincian: rincianSimpan,
                        metode_bayar: metode,
                        catatan: ket,
                        tanggal_bayar: tanggal_bayar,
                        jam_bayar: jam_bayar,
                        tanggal_lengkap: tanggalBayarKirim
                    })
                });

                const teksBalik = await kirim.text();
                console.log("📩 Balik Server:", teksBalik);

                if(!kirim.ok) throw new Error(`Kode: ${kirim.status}`);
                const hasil = JSON.parse(teksBalik);

                if(hasil.sukses){
                    alert(`✅ Pembayaran sebesar ${formatRupiah(jumlahBayar)} berhasil disimpan!`);
                    
                    // ✅ PERBARUI TAMPILAN TANPA HARUS TUNGGU RELOAD — SUDAH DIPERBAIKI
                    const semuaBaris = document.querySelectorAll('tbody tr');
                    let barisTabelUtama = null;

                    semuaBaris.forEach(baris => {
                        const kolomNisn = baris.cells[1]; // td ke-2 = kolom NISN
                        if(kolomNisn && kolomNisn.textContent.trim() === infoNisn.textContent.trim()){
                            barisTabelUtama = baris;
                        }
                    });

                    if(barisTabelUtama){
                        // Ambil data terbaru dari respons server
                        const dataBaru = hasil.data_terbaru || {};
                        if(dataBaru.sisa_tagihan !== undefined){
                            barisTabelUtama.cells[6].textContent = formatRupiah(dataBaru.sisa_tagihan);
                        }
                        if(dataBaru.status){
                            const badge = barisTabelUtama.querySelector('span.badge');
                            if(badge){
                                badge.textContent = dataBaru.status;
                                badge.className = `badge ${dataBaru.status==='Lunas'?'bg-success':'bg-danger'}`;
                            }
                        }
                    }
                    
                    bootstrap.Modal.getInstance(modalEl).hide();
                    location.reload(); // Tetap reload untuk kesegaran data menyeluruh
                }  
            } catch (err) {
                alert('Kesalahan jaringan/server: '+err.message); 
                console.error("❌ Rincian Kesalahan:", err);
            }
            finally { btnSimpan.innerHTML = `<i class="fas fa-save me-1"></i> Simpan Pembayaran Terpilih`; btnSimpan.disabled=false; }
        });
    }

    function resetIsiModal(){
        pilihSiswa.value = "";
        infoSiswa.classList.add('d-none');
        wadahTagihan.innerHTML = `<div class="p-4 text-center text-muted"><i class="fas fa-hand-pointer me-2"></i>Silakan pilih siswa terlebih dahulu...</div>`;
        blokPilihSemua.classList.add('d-none');
        blokBayar.classList.add('d-none');
        centangSemua.checked = false;
        metodeBayar.value = "";
        totalBayar.value = "Rp 0";
        uangDiterima.value = "";
        catatan.value = "";

        const tanggalJamEl = document.getElementById('tanggalJamBayarUtama');
        if(tanggalJamEl) {
            tanggalJamEl.value = ambilWaktuSekarang();
            // ⭐ KUNCI: Beri sinyal ke Custom Date Picker ada perubahan
            tanggalJamEl.dispatchEvent(new Event('change'));
        }

        daftarTagihanMuat = []; nilaiAngkaSimpan=0;
    }

    function resetTampilanMuat(){
        centangSemua.checked = false;
        totalBayar.value = "Rp 0"; uangDiterima.value = ""; catatan.value = ""; nilaiAngkaSimpan=0;
    }
});