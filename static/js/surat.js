let idSuratAktif = null;
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || '';
let tabAktifTerakhir = 'perlu';
const guruIdSaya = GURU_ID_SAYA || 0;

// Buka/Tutup Panel
document.getElementById('tombolSurat').addEventListener('click', function () {
    const panel = document.getElementById('panelSurat');
    const ikon = this.querySelector('.ikon-panah');
    
    if (panel.style.display === 'flex') {
        tutupPanelSurat();
    } else {
        panel.style.display = 'flex';
        ikon.classList.remove('fa-chevron-up');
        ikon.classList.add('fa-chevron-down');
        
        // 👇 Muat data sesuai tab terakhir yang dipilih
        muatDaftarSurat(tabAktifTerakhir);
    }
});

function tutupPanelSurat() {
    document.getElementById('panelSurat').style.display = 'none';
    const ikon = document.querySelector('#tombolSurat .ikon-panah');
    ikon.classList.remove('fa-chevron-down');
    ikon.classList.add('fa-chevron-up');
}

// Ganti Tab Kategori
document.querySelectorAll('.tab-surat').forEach(tab => {
    tab.addEventListener('click', function () {
        document.querySelectorAll('.tab-surat').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        tabAktifTerakhir = this.dataset.target; // Simpan tab yang dipilih
        muatDaftarSurat(tabAktifTerakhir);
    });
});

// Muat Daftar Surat Sesuai Kategori
function muatDaftarSurat(jenis = 'perlu') {
    fetch(`/surat-global/daftar-surat?jenis=${jenis}`)
        .then(res => {
            if (!res.ok) throw new Error(`Status: ${res.status}`);
            const tipe = res.headers.get('Content-Type') || '';
            if (!tipe.includes('application/json')) {
                throw new Error('Bukan data JSON, kemungkinan halaman login/404');
            }
            return res.json();
        })
        .then(data => {
            const wadah = document.getElementById('kontenPanelSurat');
            wadah.innerHTML = '';

            if (!data.surat || data.surat.length === 0) {
                wadah.innerHTML = `<div class="text-center p-4 text-muted">Tidak ada surat di kategori ini.</div>`;
                return;
            }

            data.surat.forEach(surat => {
                const kelasStatus = `status-${surat.status.toLowerCase()}`;
                const elemen = document.createElement('div');
                elemen.className = `item-surat ${kelasStatus}`;
                elemen.innerHTML = `
                    <div class="judul-surat">${surat.perihal}</div>
                    <div class="info-surat">No: ${surat.nomor_surat} | ${surat.tanggal_surat}</div>
                    <div class="info-surat">Status: ${surat.status}</div>
                `;
                elemen.onclick = () => bukaDetailSurat(surat.id);
                wadah.appendChild(elemen);
            });

            const badge = document.getElementById('jumlahNotif');
            if (data.jumlah > 0) {
                badge.textContent = data.jumlah;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(err => {
            console.error('Gagal memuat daftar surat:', err);
            document.getElementById('kontenPanelSurat').innerHTML = `<div class="text-center p-4 text-danger">${err.message}</div>`;
        });
}

function bukaDetailSurat(id) {
    idSuratAktif = id;
    tutupPanelSurat();

    fetch(`/surat-global/ambil-detail/${id}`)
        .then(res => {
            if (!res.ok) throw new Error(`Status: ${res.status}`);
            const tipe = res.headers.get('Content-Type') || '';
            if (!tipe.includes('application/json')) {
                throw new Error('Tidak bisa memuat detail, pastikan sudah login');
            }
            return res.json();
        })
        .then(surat => {
            const html = `
                <!-- KOP SURAT -->
                <div class="kop-surat">
                    <div class="kop-konten">
                        <img src="/static/img/logo-school.svg" alt="Logo SMP Unggulan Hamzanwadi" class="kop-logo">
                        
                        <div class="kop-pemisah"></div>

                        <div class="kop-teks-kanan">
                            <div class="kop-izin">IZIN OPERASIONAL: 500.16.7.2/97/PMPTSP-SMP/01/2025</div>
                            <div class="kop-kontak">
                                <i class="fa-brands fa-whatsapp-square"></i>
                                <span>081915780964</span>
                                <i class="fa-solid fa-envelope"></i>
                                <span>smpu@hamzanwadi.ac.id</span>
                            </div>
                            <div class="kop-alamat">Jl. Dr. Ciptromangun Kusumo, Sawing, Kel. Majidi, Kec. Selong, Kab. Lombok Timur - NTB</div>
                        </div>
                    </div>
                </div>

                <!-- ISI SURAT -->
                <div class="surat-kepala">
                    <span class="label">Nomor</span>
                    <span class="value">: ${surat.nomor_surat}</span>

                    <span class="label">Lampiran</span>
                    <span class="value">: ${surat.lampiran || '-'}</span>

                    <span class="label">Hal</span>
                    <span class="value">: <strong>${surat.perihal}</strong></span>
                </div>

                <div class="surat-tujuan">
                    <p>${surat.tujuan ? surat.tujuan.replace(/^(Kepada\s*\n?\s*Yth\.\s*)([\s\S]*?)(\n\s*di\s+[\s\S]*)$/s, '$1<strong>$2</strong>$3') : '-'}</p>
                </div>

                <div class="surat-isi">
                    <p><strong><em>Bismillahiwabihamdihi</em></strong></p>
                    <p class="salam"><em><strong>Assalamu'alaikum Warahmatullahi Wabarakatuh</em></strong></p>
                    <p>Semoga kami menjumpai Bapak/Ibu dalam keadaan sehat wal'afiat serta dalam limpahan Rahmat dan taufik dari Allah SWT. sehingga dapat beraktivitas seperti biasanya. Aamiin ya Rabbal Alamin.</p>
                    <p class="isi">${surat.isi_surat}</p>
                    <p class="wassalam"><strong><em>Wallohul Muwaffiq Wal Hadi ila Sabi Lirrosyad</em></strong></p>
                    <p><strong><em>Wassalamu'alaikum Warahmatullahi Wabarakatuh</em></strong></p>
                </div>

                <!-- TANDA TANGAN + QR -->
                <div class="surat-ttd" style="color: black;">
                    <p style="text-align: right; margin: 1rem 0 0;">
                        Majidi, ${new Date(surat.tanggal_surat).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })}
                    </p>
                    ${(() => {
                        const daftarTtd = surat.penandatangan || [];
                        const jumlah = daftarTtd.length;
                        // Cari posisi Kepala Sekolah
                        const posisiKepala = daftarTtd.findIndex(t => t.jabatan.trim().toLowerCase() === 'kepala sekolah');
                        const adaKepala = posisiKepala !== -1;

                        function buatBlokTtd(ttd) {
                            const qr = ttd.ttd_selesai && ttd.qr_code 
                                ? `
                                    <div class="qr-verifikasi" style="margin: 0 auto; text-align: center;">
                                        <img src="/static/${ttd.qr_code}" alt="QR Verifikasi Elektronik" style="width: 80px; height: 80px; object-fit: contain;">
                                        <p style="font-size: 8pt; margin:0; color: #333;">Ditandatangani secara elektronik</p>
                                    </div>
                                ` 
                                : `<p style="font-size: 9pt; color: #888; margin: 0 auto;">Belum ditandatangani</p>`;

                            return `
                                <div style="text-align: center;">
                                    <p style="margin: 0 0 0.75rem 0;">${ttd.jabatan || ''}</p>
                                    ${qr}
                                    <p style="margin: 0;"><strong>${ttd.nama || ''}</strong></p>
                                    <p style="margin: 0;">NIP. ${ttd.nip || '-'}</p>
                                    ${surat.status === 'Diajukan' && !ttd.ttd_selesai && ttd.id_guru === guruIdSaya
                                    ? `<button type="button" class="btn btn-sm btn-primary mt-2" onclick="prosesTindakan('setuju', ${ttd.id})">Tanda Tangan & Setujui</button>` 
                                    : ''}
                                </div>
                            `;
                        }

                        let htmlTtd = '';

                        if (jumlah === 1) {
                            // Hanya Kepala Sekolah → tidak ada "Mengetahui"
                            htmlTtd = `<div style="margin-left: 65%; text-align: left; width: max-content;">${buatBlokTtd(daftarTtd[0])}</div>`;
                        } 
                        else if (jumlah === 2) {
                            if (adaKepala) {
                                if (posisiKepala === 0) {
                                    // Kepala di KIRI
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                    `;
                                } else {
                                    // Kepala di KANAN
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                    `;
                                }
                            } else {
                                htmlTtd = `
                                    <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                    </div>
                                `;
                            }
                        } 
                        else if (jumlah === 3) {
                            if (adaKepala) {
                                if (posisiKepala === 0) {
                                    // Kepala di kiri baris atas
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                                    `;
                                } else if (posisiKepala === 1) {
                                    // Kepala di kanan baris atas
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                                    `;
                                } else if (posisiKepala === 2) {
                                    // Kepala di baris bawah tengah
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="width: 100%; text-align: center; margin-top: 1rem;">
                                            <p style="margin: 0;">Mengetahui,</p>
                                            ${buatBlokTtd(daftarTtd[2])}
                                        </div>
                                    `;
                                }
                            } else {
                                htmlTtd = `
                                    <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                    </div>
                                    <div style="width: 100%; text-align: center; margin-top: 1.5rem;">${buatBlokTtd(daftarTtd[2])}</div>
                                `;
                            }
                        } 
                        else if (jumlah === 4) {
                            if (adaKepala) {
                                if (posisiKepala === 0) {
                                    // Kepala kiri baris 1
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                        </div>
                                    `;
                                } else if (posisiKepala === 1) {
                                    // Kepala kanan baris 1
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                        </div>
                                    `;
                                } else if (posisiKepala === 2) {
                                    // Kepala kiri baris 2
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1rem;">
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                        </div>
                                    `;
                                } else if (posisiKepala === 3) {
                                    // Kepala kanan baris 2
                                    htmlTtd = `
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1rem;">
                                            <p style="width: 45%; text-align: center; margin: 0;">&nbsp;</p>
                                            <p style="width: 45%; text-align: center; margin: 0;">Mengetahui,</p>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                            <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                        </div>
                                    `;
                                }
                            } else {
                                htmlTtd = `
                                    <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%;">
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[0])}</div>
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[1])}</div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; width: 100%; padding: 0 8%; margin-top: 1.5rem;">
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[2])}</div>
                                        <div style="width: 45%; text-align: center;">${buatBlokTtd(daftarTtd[3])}</div>
                                    </div>
                                `;
                            }
                        }

                        return htmlTtd;
                    })()}
                </div>
            `;

            document.getElementById('isiDetailSurat').innerHTML = html;

            const footerAksi = document.getElementById('aksiSuratFooter');
            if (footerAksi) {
                footerAksi.style.display = surat.status === 'Diajukan' ? 'flex' : 'none';
                document.getElementById('judulModalSurat').textContent = 
                    surat.status === 'Diajukan' ? 'Pemeriksaan Surat' : `Detail Surat - Status: ${surat.status}`;
            }

            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                new bootstrap.Modal(document.getElementById('modalDetailSurat')).show();
            }
        })
        .catch(err => {
            console.error('Gagal memuat surat:', err);
            const isi = document.getElementById('isiDetailSurat');
            if (isi) isi.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
        });
}

function prosesTindakan(tindakan, idTtd = null) {
    const catatan = document.getElementById('catatanPersetujuan')?.value.trim() || '';

    // Validasi untuk perbaiki / tolak
    if ((tindakan === 'perbaiki' || tindakan === 'tolak') && !catatan) {
        alert('⚠️ Silakan tulis alasan/catatan terlebih dahulu!');
        return;
    }

    // Validasi khusus untuk tanda tangan
    if (tindakan === 'setuju' && !idTtd) {
        alert('❌ ID penandatangan tidak ditemukan, gunakan tombol di bawah nama Anda!');
        return;
    }

    fetch(`/surat-global/proses-persetujuan/${idSuratAktif}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `tindakan=${tindakan}&id_ttd=${idTtd || ''}&catatan=${encodeURIComponent(catatan)}`
    })
    .then(res => res.json())
    .then(hasil => {
        alert(hasil.pesan);
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalDetailSurat'));
        if (modal) modal.hide();
        document.getElementById('catatanPersetujuan').value = '';
        muatDaftarSurat(tabAktifTerakhir);
    })
    .catch(err => {
        alert('❌ Terjadi kesalahan saat memproses surat');
        console.error(err);
    });
}

// Tutup panel jika klik di luar area
document.addEventListener('click', function (e) {
    const panel = document.getElementById('panelSurat');
    const tombol = document.getElementById('tombolSurat');
    if (!panel.contains(e.target) && !tombol.contains(e.target)) {
        tutupPanelSurat();
    }
});

// Muat awal + set interval otomatis setiap 10 detik
window.addEventListener('load', () => {
    muatDaftarSurat(tabAktifTerakhir);
    // 👇 Real-time: perbarui data otomatis setiap 10 detik
    setInterval(() => {
        if (document.getElementById('panelSurat').style.display === 'flex') {
            muatDaftarSurat(tabAktifTerakhir);
        }
    }, 10000); // 10000 ms = 10 detik
});