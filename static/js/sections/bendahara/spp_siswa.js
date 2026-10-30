
// ============================================================
// MANAJEMEN PEMBAYARAN SPP - HALAMAN STATUS SISWA
// Premium SaaS Interaction
// ============================================================


// ============================================================
// 1. FUNGSI PEMBANTU
// ============================================================

function formatRupiah(angka) {
    angka = Number(angka) || 0;

    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(angka).replace(/Rp\s*/g, 'Rp ');
}


function ambilAngkaMurni(teks) {
    if (teks === null || teks === undefined) return 0;

    const bersih = String(teks).replace(/[^\d]/g, '');

    return bersih ? Number(bersih) : 0;
}


function ambilWaktuSekarang() {
    const sekarang = new Date();

    const tanggal =
        sekarang.getFullYear() + '-' +
        String(sekarang.getMonth() + 1).padStart(2, '0') + '-' +
        String(sekarang.getDate()).padStart(2, '0');

    const jam =
        String(sekarang.getHours()).padStart(2, '0') + ':' +
        String(sekarang.getMinutes()).padStart(2, '0');

    return `${tanggal}T${jam}`;
}


function resetStatusSemua(wadah) {
    if (!wadah) return;

    wadah.querySelectorAll('.status-info').forEach(el => {
        el.textContent = 'Belum diproses';
        el.className = 'badge bg-secondary status-info';
    });
}


// ============================================================
// 2. PEMBAGIAN NOMINAL PEMBAYARAN
// ============================================================

function prosesBagiPembayaran(jumlahBayar, wadah) {
    const daftarCek = wadah.querySelectorAll('.cek-tagihan:checked');

    let sisaUang = Number(jumlahBayar) || 0;
    const rincianSimpan = [];

    daftarCek.forEach(cek => {
        const baris = cek.closest('tr');

        if (!baris) return;

        const sisaTagihanSekarang = Math.max(
            0,
            Number(baris.dataset.sisaTagihan) || 0
        );

        const nominalAsli = Number(baris.dataset.nominalAsli) || 0;

        const statusEl = baris.querySelector('.status-info');

        let dibayar = 0;
        let sisaTagih = sisaTagihanSekarang;

        if (sisaUang <= 0) {
            dibayar = 0;

            if (statusEl) {
                statusEl.textContent = 'Belum dibayar';
                statusEl.className = 'badge bg-secondary status-info';
            }

        } else if (sisaUang >= sisaTagihanSekarang) {
            dibayar = sisaTagihanSekarang;
            sisaTagih = 0;

            sisaUang -= sisaTagihanSekarang;

            if (statusEl) {
                statusEl.textContent = 'Lunas';
                statusEl.className = 'badge bg-success status-info';
            }

        } else {
            dibayar = sisaUang;
            sisaTagih = sisaTagihanSekarang - dibayar;

            sisaUang = 0;

            if (statusEl) {
                statusEl.textContent = `Sebagian (${formatRupiah(dibayar)})`;
                statusEl.className = 'badge bg-warning text-dark status-info';
            }
        }

        dibayar = Math.min(dibayar, sisaTagihanSekarang);

        rincianSimpan.push({
            id: baris.dataset.id,
            nominal_asli: nominalAsli,
            dibayar: dibayar,
            sisa_hutang: sisaTagih
        });
    });

    return rincianSimpan;
}


// ============================================================
// 3. INISIALISASI HALAMAN
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    const $ = id => document.getElementById(id);

    // --------------------------------------------------------
    // Elemen modal pembayaran
    // --------------------------------------------------------

    const btnBuka = $('btnBukaPembayaran');
    const modalEl = $('modalPembayaranDaftar');

    const pilihSiswa = $('pilihSiswaBayar');

    const infoSiswa = $('infoSiswaTerpilih');
    const infoNama = $('infoNama');
    const infoNisn = $('infoNisn');
    const infoKelas = $('infoKelas');

    const wadahTagihan = $('wadahDaftarTagihanUtama');

    const blokPilihSemua = $('blokPilihSemua');
    const blokBayar = $('blokPembayaranLengkap');

    const centangSemua = $('pilihSemuaBelumLunasUtama');

    const metodeBayar = $('metodeBayarUtama');
    const totalBayar = $('totalDipilihUtama');
    const uangDiterima = $('uangDiterimaUtama');

    const catatan = $('catatanBayarUtama');
    const tanggalJam = $('tanggalJamBayarUtama');

    const btnSimpan = $('btnSimpanPembayaranUtama');

    let nilaiAngkaSimpan = 0;
    let daftarTagihanMuat = [];


    // --------------------------------------------------------
    // Animasi angka statistik
    // --------------------------------------------------------

    function animasikanAngka() {
        const angka = document.querySelectorAll('.spp-page .stat-card-content h3');

        angka.forEach(elemen => {
            const teks = elemen.textContent.trim();
            const target = parseFloat(teks.replace(/[^\d.]/g, ''));

            if (!Number.isFinite(target)) return;

            const akhiran = teks.includes('%') ? '%' : '';
            const durasi = 850;
            const awal = performance.now();

            function animasi(waktu) {
                const progres = Math.min((waktu - awal) / durasi, 1);
                const easing = 1 - Math.pow(1 - progres, 4);

                const nilai = Math.round(target * easing);

                elemen.textContent = nilai.toLocaleString('id-ID') + akhiran;

                if (progres < 1) {
                    requestAnimationFrame(animasi);
                }
            }

            elemen.textContent = '0' + akhiran;

            requestAnimationFrame(animasi);
        });
    }

    animasikanAngka();


    // --------------------------------------------------------
    // Inisialisasi collapse
    // --------------------------------------------------------

    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(el => {

        el.addEventListener('shown.bs.collapse', () => {
            const ikon = el.querySelector('i');

            if (ikon) {
                ikon.classList.remove('fa-chevron-down');
                ikon.classList.add('fa-chevron-up');
            }
        });

        el.addEventListener('hidden.bs.collapse', () => {
            const ikon = el.querySelector('i');

            if (ikon) {
                ikon.classList.remove('fa-chevron-up');
                ikon.classList.add('fa-chevron-down');
            }
        });
    });


    // ========================================================
    // 4. MODAL PEMBAYARAN MANUAL
    // ========================================================

    function resetIsiModal() {
        if (!pilihSiswa) return;

        pilihSiswa.value = '';

        infoSiswa?.classList.add('d-none');

        if (wadahTagihan) {
            wadahTagihan.innerHTML = `
                <div class="spp-empty-bill">
                    <div class="spp-empty-illustration">
                        <div class="spp-empty-circle">
                            <i class="fas fa-hand-pointer"></i>
                        </div>
                        <span class="spp-empty-spark spp-empty-spark-one">✦</span>
                        <span class="spp-empty-spark spp-empty-spark-two">✧</span>
                    </div>
                    <strong>Belum ada siswa dipilih</strong>
                    <p>Silakan pilih siswa terlebih dahulu. Daftar tagihan akan muncul di area ini.</p>
                </div>
            `;
        }

        blokPilihSemua?.classList.add('d-none');
        blokBayar?.classList.add('d-none');

        if (centangSemua) centangSemua.checked = false;

        if (metodeBayar) metodeBayar.value = '';

        if (totalBayar) totalBayar.value = 'Rp 0';

        if (uangDiterima) uangDiterima.value = '';

        if (catatan) catatan.value = '';

        if (tanggalJam) {
            tanggalJam.value = ambilWaktuSekarang();
            tanggalJam.dispatchEvent(new Event('change'));
        }

        nilaiAngkaSimpan = 0;
        daftarTagihanMuat = [];

        if (btnSimpan) btnSimpan.disabled = true;
    }


    function resetTampilanMuat() {
        if (centangSemua) centangSemua.checked = false;

        if (totalBayar) totalBayar.value = 'Rp 0';

        if (uangDiterima) uangDiterima.value = '';

        if (catatan) catatan.value = '';

        nilaiAngkaSimpan = 0;

        if (btnSimpan) btnSimpan.disabled = true;
    }


    // Buka modal
    if (btnBuka && modalEl) {
        btnBuka.addEventListener('click', function () {

            resetIsiModal();

            if (tanggalJam) {
                tanggalJam.value = ambilWaktuSekarang();
                tanggalJam.dispatchEvent(new Event('change'));
            }

            const modal = bootstrap.Modal.getOrCreateInstance(modalEl, {
                backdrop: 'static',
                keyboard: false
            });

            modal.show();

            setTimeout(() => {
                if (window.initCustomSelect) {
                    document.querySelectorAll('.modal-bayar-select')
                        .forEach(window.initCustomSelect);
                }
            }, 150);
        });
    }


    // ========================================================
    // 5. MEMUAT TAGIHAN SISWA
    // ========================================================

    if (pilihSiswa) {

        pilihSiswa.addEventListener('change', async function () {

            const idSiswa = this.value.trim();

            resetTampilanMuat();

            daftarTagihanMuat = [];

            if (!idSiswa) {
                resetIsiModal();
                return;
            }

            const opsiTerpilih = this.options[this.selectedIndex];

            if (!opsiTerpilih) return;

            if (infoNama) infoNama.textContent = opsiTerpilih.dataset.nama || '-';
            if (infoNisn) infoNisn.textContent = opsiTerpilih.dataset.nisn || '-';
            if (infoKelas) infoKelas.textContent = opsiTerpilih.dataset.kelas || '-';

            infoSiswa?.classList.remove('d-none');

            if (wadahTagihan) {
                wadahTagihan.innerHTML = `
                    <div class="loading-state">
                        <div class="loading-spinner"></div>
                        <strong>Memuat tagihan siswa</strong>
                        <span>Mohon tunggu sebentar...</span>
                    </div>
                `;
            }

            try {
                const response = await fetch(
                    `/bendahara/api-rincian-tagihan/${encodeURIComponent(idSiswa)}`
                );

                if (!response.ok) {
                    throw new Error(`Gagal memuat tagihan (${response.status})`);
                }

                const data = await response.json();

                daftarTagihanMuat = (data.tagihan || []).filter(item => {

                    const nominal = Number(item.nominal) || 0;
                    const sudahDibayar = Number(item.sudah_dibayar) || 0;

                    return Math.max(0, nominal - sudahDibayar) > 0;
                });

                tampilkanDaftarTagihan(daftarTagihanMuat);

                blokPilihSemua?.classList.remove('d-none');
                blokBayar?.classList.remove('d-none');

                hitungTotalTerpilih();

                setTimeout(() => {
                    if (window.initCustomSelect) {
                        document.querySelectorAll('.modal-bayar-select')
                            .forEach(window.initCustomSelect);
                    }
                }, 100);

            } catch (error) {
                console.error('Memuat tagihan:', error);

                if (wadahTagihan) {
                    wadahTagihan.innerHTML = `
                        <div class="error-state">
                            <i class="fas fa-triangle-exclamation"></i>
                            <strong>Tagihan gagal dimuat</strong>
                            <span>${error.message}</span>
                        </div>
                    `;
                }
            }
        });
    }


    // ========================================================
    // 6. MENAMPILKAN DAFTAR TAGIHAN
    // ========================================================

    function tampilkanDaftarTagihan(arrTagihan) {

        if (!wadahTagihan) return;

        const kumpulKelompok = {};

        arrTagihan.forEach(item => {
            const namaKelompok = item.nama || 'Lainnya';

            if (!kumpulKelompok[namaKelompok]) {
                kumpulKelompok[namaKelompok] = [];
            }

            kumpulKelompok[namaKelompok].push(item);
        });

        if (Object.keys(kumpulKelompok).length === 0) {

            wadahTagihan.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-circle-check"></i>
                    <strong>Semua tagihan sudah lunas!</strong>
                    <span>Tidak ada tagihan yang perlu dibayarkan.</span>
                </div>
            `;

            blokPilihSemua?.classList.add('d-none');
            blokBayar?.classList.add('d-none');

            return;
        }

        let nomorKelompok = 1;
        let html = '';

        for (const namaKelompok in kumpulKelompok) {

            const daftar = kumpulKelompok[namaKelompok];
            const idKelompok = `kel-utama-${nomorKelompok++}`;

            html += `
                <div class="card kelompok-modal mb-2">
                    <div class="card-header"
                         data-bs-toggle="collapse"
                         data-bs-target="#${idKelompok}"
                         role="button">

                        <div class="d-flex align-items-center gap-2">
                            <i class="fas fa-chevron-down"></i>
                            <strong>${namaKelompok}</strong>
                            <span class="badge bg-secondary">
                                ${daftar.length} tagihan
                            </span>
                        </div>

                        <label class="form-check mb-0">
                            <input type="checkbox"
                                   class="form-check-input pilih-semua-kelompok"
                                   data-kel="${idKelompok}">
                            <span>Pilih Semua</span>
                        </label>
                    </div>

                    <div id="${idKelompok}" class="collapse">
                        <div class="table-responsive p-2">
                            <table class="table table-sm align-middle mb-0">
                                <thead>
                                    <tr>
                                        <th class="text-center">Pilih</th>
                                        <th>Keterangan</th>
                                        <th class="text-end">Sisa Tagihan</th>
                                        <th class="text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;

            daftar.forEach(item => {

                const nominal = Number(item.nominal) || 0;
                const sudahDibayar = Number(item.sudah_dibayar) || 0;

                const sisaTagihan = Math.max(0, nominal - sudahDibayar);

                const idTagihan = item.id || '';

                html += `
                    <tr
                        data-id="${idTagihan}"
                        data-nominal-asli="${nominal}"
                        data-sisa-tagihan="${sisaTagihan}">

                        <td class="text-center">
                            <input type="checkbox"
                                   class="form-check-input cek-tagihan"
                                   value="${sisaTagihan}">
                        </td>

                        <td>
                            <span class="fw-semibold">
                                ${item.waktu || item.keterangan || '-'}
                            </span>
                        </td>

                        <td class="text-end fw-bold">
                            ${formatRupiah(sisaTagihan)}
                        </td>

                        <td class="text-center">
                            <span class="badge bg-secondary status-info">
                                Belum diproses
                            </span>
                        </td>
                    </tr>
                `;
            });

            html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        }

        wadahTagihan.innerHTML = html;
    }


    // ========================================================
    // 7. HITUNG TOTAL PEMBAYARAN
    // ========================================================

    function hitungTotalTerpilih() {

        if (!wadahTagihan || !totalBayar) return;

        let total = 0;

        wadahTagihan.querySelectorAll('.cek-tagihan:checked')
            .forEach(checkbox => {
                total += Number(checkbox.value) || 0;
            });

        totalBayar.value = formatRupiah(total);

        if (total === 0) {
            if (uangDiterima) uangDiterima.value = '';

            nilaiAngkaSimpan = 0;

            resetStatusSemua(wadahTagihan);

            if (btnSimpan) btnSimpan.disabled = true;

            return;
        }

        const metodeTerisi = !!metodeBayar?.value.trim();

        if (btnSimpan) {
            btnSimpan.disabled = !(metodeTerisi && nilaiAngkaSimpan > 0);
        }
    }


    function sesuaikanNominalDanStatus() {

        const totalTagihanBaru = ambilAngkaMurni(totalBayar?.value);

        if (totalTagihanBaru === 0) {

            if (uangDiterima) uangDiterima.value = '';

            nilaiAngkaSimpan = 0;

            resetStatusSemua(wadahTagihan);

        } else if (nilaiAngkaSimpan > totalTagihanBaru) {

            nilaiAngkaSimpan = totalTagihanBaru;

            if (uangDiterima) {
                uangDiterima.value = formatRupiah(nilaiAngkaSimpan);
            }

            prosesBagiPembayaran(nilaiAngkaSimpan, wadahTagihan);

        } else if (nilaiAngkaSimpan > 0) {

            prosesBagiPembayaran(nilaiAngkaSimpan, wadahTagihan);
        }

        wadahTagihan.querySelectorAll('tr').forEach(baris => {

            const checkbox = baris.querySelector('.cek-tagihan');
            const status = baris.querySelector('.status-info');

            if (checkbox && !checkbox.checked && status) {
                status.textContent = 'Belum diproses';
                status.className = 'badge bg-secondary status-info';
            }
        });

        hitungTotalTerpilih();
    }


    // ========================================================
    // 8. PILIH SEMUA TAGIHAN
    // ========================================================

    centangSemua?.addEventListener('change', function () {

        wadahTagihan.querySelectorAll('.cek-tagihan, .pilih-semua-kelompok')
            .forEach(checkbox => {
                checkbox.checked = this.checked;
            });

        hitungTotalTerpilih();
        sesuaikanNominalDanStatus();
    });


    wadahTagihan?.addEventListener('change', function (event) {

        if (event.target.classList.contains('pilih-semua-kelompok')) {

            const idKelompok = event.target.dataset.kel;

            const kelompok = document.getElementById(idKelompok);

            kelompok?.querySelectorAll('.cek-tagihan')
                .forEach(checkbox => {
                    checkbox.checked = event.target.checked;
                });

            hitungTotalTerpilih();
            sesuaikanNominalDanStatus();
        }

        if (event.target.classList.contains('cek-tagihan')) {

            hitungTotalTerpilih();
            sesuaikanNominalDanStatus();

            const semuaCheckbox = [
                ...wadahTagihan.querySelectorAll('.cek-tagihan')
            ];

            const semuaTerpilih = semuaCheckbox.length > 0 &&
                semuaCheckbox.every(checkbox => checkbox.checked);

            if (centangSemua) {
                centangSemua.checked = semuaTerpilih;
            }
        }
    });


    // ========================================================
    // 9. INPUT NOMINAL PEMBAYARAN
    // ========================================================

    metodeBayar?.addEventListener('change', hitungTotalTerpilih);


    uangDiterima?.addEventListener('input', function () {

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

        if (jumlahDipilih === 0) {

            alert('Pilih terlebih dahulu tagihan yang akan dibayar.');

            input.value = '';

            nilaiAngkaSimpan = 0;

            resetStatusSemua(wadahTagihan);

            hitungTotalTerpilih();

            return;
        }

        const totalTagihan = ambilAngkaMurni(totalBayar.value);

        let angkaAkhir = angka;

        if (angka > totalTagihan) {

            angkaAkhir = totalTagihan;

            input.value = formatRupiah(angkaAkhir);

            alert(
                'Nominal pembayaran melebihi total tagihan yang dipilih.\n' +
                'Nominal otomatis disesuaikan menjadi ' +
                formatRupiah(totalTagihan)
            );
        }

        nilaiAngkaSimpan = angkaAkhir;

        const hasilFormat = formatRupiah(angkaAkhir);

        input.value = hasilFormat;

        // Menjaga posisi kursor
        const sebelumCursor = String(input.value).substring(0, cursor);
        const digitSebelumCursor = (sebelumCursor.match(/\d/g) || []).length;

        let digitDitemukan = 0;
        let posisiCursor = hasilFormat.length;

        for (let i = 0; i < hasilFormat.length; i++) {

            if (/\d/.test(hasilFormat[i])) {
                digitDitemukan++;

                if (digitDitemukan >= digitSebelumCursor) {
                    posisiCursor = i + 1;
                    break;
                }
            }
        }

        input.setSelectionRange(posisiCursor, posisiCursor);

        prosesBagiPembayaran(nilaiAngkaSimpan, wadahTagihan);

        hitungTotalTerpilih();
    });


    // ========================================================
    // 10. SIMPAN PEMBAYARAN KE SERVER
    // ========================================================

    if (btnSimpan) {

        btnSimpan.addEventListener('click', async function () {

            const idSiswa = pilihSiswa?.value;

            if (!idSiswa) {
                alert('Pilih siswa terlebih dahulu.');
                return;
            }

            let jumlahBayar = nilaiAngkaSimpan;

            const totalTagihanAkhir = ambilAngkaMurni(totalBayar.value);

            jumlahBayar = Math.min(jumlahBayar, totalTagihanAkhir);

            if (jumlahBayar <= 0) {
                alert('Masukkan nominal pembayaran terlebih dahulu.');
                return;
            }

            const rincianSimpan = prosesBagiPembayaran(
                jumlahBayar,
                wadahTagihan
            );

            const adaBayar = rincianSimpan.some(item => item.dibayar > 0);

            if (!adaBayar) {
                alert('Tidak ada tagihan yang dapat dibayarkan.');
                return;
            }

            const metode = metodeBayar.value;
            const keterangan = catatan.value.trim();

            if (!metode) {
                alert('Pilih metode pembayaran terlebih dahulu.');
                return;
            }

            if (!tanggalJam?.value) {
                alert('Tanggal dan jam pembayaran wajib diisi.');
                return;
            }

            const teksTombolAwal = btnSimpan.innerHTML;

            btnSimpan.disabled = true;

            btnSimpan.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                Menyimpan pembayaran...
            `;

            try {

                const [tanggalBayar, jamBayar] = tanggalJam.value.split('T');

                const csrf = document.querySelector(
                    'meta[name="csrf-token"]'
                )?.content || '';

                const response = await fetch('/bendahara/simpan-pembayaran', {

                    method: 'POST',

                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf
                    },

                    body: JSON.stringify({

                        id_siswa: idSiswa,

                        rincian: rincianSimpan,

                        metode_bayar: metode,

                        catatan: keterangan,

                        tanggal_bayar: tanggalBayar,

                        jam_bayar: jamBayar || '00:00',

                        tanggal_lengkap: tanggalJam.value
                    })
                });


                const hasil = await response.json();

                if (!response.ok || !hasil.sukses) {
                    throw new Error(
                        hasil.pesan || hasil.message ||
                        'Pembayaran gagal disimpan.'
                    );
                }


                // Notifikasi berhasil
                alert(
                    'Pembayaran berhasil disimpan!\n\n' +
                    'Nominal: ' + formatRupiah(jumlahBayar)
                );


                // Tutup modal
                const modal = bootstrap.Modal.getInstance(modalEl);

                modal?.hide();


                // Refresh data agar seluruh statistik dan tabel sinkron
                window.location.reload();

            } catch (error) {

                console.error('Simpan pembayaran:', error);

                alert(
                    error.message ||
                    'Terjadi kesalahan saat menyimpan pembayaran.'
                );

            } finally {

                btnSimpan.innerHTML = teksTombolAwal;

                btnSimpan.disabled = false;
            }
        });
    }


    // ========================================================
    // 11. FILTER TABEL SISWA
    // ========================================================

    const inputCari = $('cariSiswaSPP');

    const filterBulan = $('filterBulan');
    const filterKelas = $('filterKelas');
    const filterStatus = $('filterStatus');

    const btnReset = $('btnResetFilter');

    const tabel = $('tabelSiswaSPP');

    const jumlahBaris = $('jumlahBarisSPP');


    function terapkanFilterSPP() {

        if (!tabel) return;

        const cari = (inputCari?.value || '').toLowerCase().trim();

        const bulan = (filterBulan?.value || '').toLowerCase();

        const kelas = filterKelas?.value || '';

        const status = filterStatus?.value || '';

        let jumlah = 0;

        tabel.querySelectorAll('tbody tr.baris-siswa').forEach(baris => {

            const nisn = (baris.dataset.nisn || '').toLowerCase();

            const nama = (baris.dataset.nama || '').toLowerCase();

            const kelasBaris = baris.dataset.kelas || '';

            const statusBaris = baris.dataset.status || '';

            // Filter nama dan NISN
            const cocokCari =
                !cari ||
                nisn.includes(cari) ||
                nama.includes(cari);

            // Filter kelas
            const cocokKelas =
                !kelas ||
                kelasBaris === kelas;

            // Filter status
            const cocokStatus =
                !status ||
                statusBaris === status;

            // Filter bulan:
            // Hanya diterapkan apabila baris memiliki informasi bulan.
            const bulanBaris = (baris.dataset.bulan || '').toLowerCase();

            const cocokBulan =
                !bulan ||
                !bulanBaris ||
                bulanBaris.includes(bulan);

            const tampil =
                cocokCari &&
                cocokKelas &&
                cocokStatus &&
                cocokBulan;

            baris.style.display = tampil ? '' : 'none';

            if (tampil) jumlah++;
        });

        if (jumlahBaris) {
            jumlahBaris.textContent = `Menampilkan ${jumlah} siswa`;
        }
    }


    [inputCari, filterBulan, filterKelas, filterStatus].forEach(elemen => {

        if (!elemen) return;

        elemen.addEventListener(
            elemen.tagName === 'INPUT' ? 'input' : 'change',
            terapkanFilterSPP
        );
    });


    btnReset?.addEventListener('click', function () {

        if (inputCari) inputCari.value = '';

        if (filterBulan) filterBulan.value = '';

        if (filterKelas) filterKelas.value = '';

        if (filterStatus) filterStatus.value = '';

        terapkanFilterSPP();
    });


    // ========================================================
    // 12. EXPORT CSV
    // ========================================================

    function exportTabelSPP() {

        if (!tabel) return;

        const baris = [
            ...tabel.querySelectorAll('thead tr, tbody tr')
        ].filter(tr => {

            if (tr.closest('thead')) return true;

            return tr.classList.contains('baris-siswa') &&
                tr.style.display !== 'none';
        });


        if (baris.length <= 1) {
            alert('Tidak ada data siswa untuk diekspor.');
            return;
        }


        const csv = baris.map(tr => {

            return [...tr.querySelectorAll('th, td')]
                .slice(0, 8)
                .map(td => {

                    const teks = td.innerText
                        .trim()
                        .replace(/\s+/g, ' ');

                    return `"${teks.replace(/"/g, '""')}"`;
                })
                .join(';');

        }).join('\r\n');


        const blob = new Blob(
            ['\uFEFF' + csv],
            { type: 'text/csv;charset=utf-8;' }
        );

        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');

        link.href = url;

        link.download = 'laporan-pembayaran-spp.csv';

        document.body.appendChild(link);

        link.click();

        link.remove();

        URL.revokeObjectURL(url);
    }


    // Dapat dipanggil dari tombol HTML inline onclick
    window.exportTabelSPP = exportTabelSPP;


    // ========================================================
    // 13. CETAK LAPORAN
    // ========================================================

    document.querySelectorAll('.spp-page [onclick="window.print()"]')
        .forEach(tombol => {

            tombol.addEventListener('click', function (event) {
                event.preventDefault();
                window.print();
            });
        });


    // ========================================================
    // 14. EFEK INTERAKSI TABEL
    // ========================================================

    document.querySelectorAll('#tabelSiswaSPP tbody tr.baris-siswa')
        .forEach((baris, index) => {

            baris.style.setProperty('--row-index', index);

        });


    // Jalankan filter awal
    terapkanFilterSPP();

});
