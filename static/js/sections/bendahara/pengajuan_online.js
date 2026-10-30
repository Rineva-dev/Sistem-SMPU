
document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // =========================================
    // KONFIGURASI
    // =========================================

    const BASE_URL = '/bendahara';
    const URL_DETAIL = (id) => `${BASE_URL}/api-pengajuan-online/${id}`;
    const URL_VERIFIKASI = (id) =>
        `${BASE_URL}/pengajuan-online/${id}/verifikasi`;

    const csrfToken =
        document.querySelector('meta[name="csrf-token"]')?.content || '';

    let pengajuanAktif = null;
    let tindakanAktif = null;
    let sedangMemproses = false;

    // =========================================
    // ELEMENT
    // =========================================

    const cariInput = document.getElementById('cariPengajuan');
    const filterStatus = document.getElementById('filterStatusPengajuan');
    const btnResetFilter = document.getElementById('resetFilterPengajuan');

    const tabel = document.getElementById('tabelPengajuan');
    const jumlahTampil = document.getElementById('jumlahPengajuanTampil');
    const noResult = document.getElementById('pengajuanNoResult');

    const modalDetail = document.getElementById('modalDetailPengajuan');
    const modalKonfirmasi = document.getElementById('modalKonfirmasiPengajuan');

    const loadingDetail = document.getElementById('detailPengajuanLoading');
    const contentDetail = document.getElementById('detailPengajuanContent');
    const errorDetail = document.getElementById('detailPengajuanError');

    const btnBukaSetujui = document.getElementById('btnBukaSetujui');
    const btnBukaTolak = document.getElementById('btnBukaTolak');
    const btnKonfirmasi = document.getElementById('btnKonfirmasiPengajuan');

    const blokAlasan = document.getElementById('blokAlasanPenolakan');
    const inputAlasan = document.getElementById('catatanPenolakan');

    // =========================================
    // HELPER
    // =========================================

    function formatRupiah(nilai) {
        const angka = Number(nilai || 0);

        return 'Rp ' + angka.toLocaleString('id-ID', {
            maximumFractionDigits: 0
        });
    }

    function formatTanggal(value) {
        if (!value) return '-';

        const tanggal = new Date(value);

        if (Number.isNaN(tanggal.getTime())) {
            return value;
        }

        return tanggal.toLocaleString('id-ID', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Asia/Makassar'
        }) + ' WITA';
    }

    function tampilkanNotifikasi(pesan, tipe = 'info') {
        // Gunakan SweetAlert jika tersedia
        if (typeof Swal !== 'undefined') {
            const icon = ['success', 'error', 'warning', 'info']
                .includes(tipe) ? tipe : 'info';

            Swal.fire({
                icon,
                title: tipe === 'success'
                    ? 'Berhasil'
                    : tipe === 'error'
                        ? 'Terjadi Kesalahan'
                        : 'Informasi',
                text: pesan,
                confirmButtonColor: '#014737'
            });

            return;
        }

        alert(pesan);
    }

    function setText(id, value) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent =
                value === null || value === undefined || value === ''
                    ? '-'
                    : String(value);
        }
    }

    function buatElemen(tag, className, text) {
        const element = document.createElement(tag);

        if (className) {
            element.className = className;
        }

        if (text !== undefined) {
            element.textContent = text;
        }

        return element;
    }

    async function ambilJSON(url, options = {}) {
        const response = await fetch(url, {
            credentials: 'same-origin',
            ...options,
            headers: {
                'Accept': 'application/json',
                ...(options.headers || {})
            }
        });

        let hasil;

        try {
            hasil = await response.json();
        } catch {
            throw new Error('Respons server bukan JSON yang valid.');
        }

        if (!response.ok || hasil.sukses === false) {
            throw new Error(
                hasil.pesan ||
                hasil.message ||
                hasil.error ||
                `Permintaan gagal (${response.status}).`
            );
        }

        return hasil;
    }

    function bukaModal(modal) {
        if (!modal) return;

        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function tutupModal(modal) {
        if (!modal) return;

        modal.classList.remove('show');

        if (
            !document.querySelector('.pengajuan-modal-overlay.show')
        ) {
            document.body.style.overflow = '';
        }
    }

    // =========================================
    // FILTER DAN PENCARIAN
    // =========================================

    function filterPengajuan() {
        if (!tabel) return;

        const keyword = (cariInput?.value || '')
            .toLowerCase()
            .trim();

        const statusDipilih = filterStatus?.value || 'semua';

        const baris = tabel.querySelectorAll('tbody tr.baris-pengajuan');

        let jumlah = 0;

        baris.forEach((row) => {
            const kode = row.dataset.kode || '';
            const nama = row.dataset.nama || '';
            const status = row.dataset.status || '';

            const cocokKeyword =
                !keyword ||
                kode.includes(keyword) ||
                nama.includes(keyword);

            const cocokStatus =
                statusDipilih === 'semua' ||
                status === statusDipilih;

            const tampil = cocokKeyword && cocokStatus;

            row.style.display = tampil ? '' : 'none';

            if (tampil) jumlah++;
        });

        if (jumlahTampil) {
            jumlahTampil.textContent = jumlah;
        }

        if (noResult) {
            noResult.hidden = jumlah > 0;
        }
    }

    cariInput?.addEventListener('input', filterPengajuan);
    filterStatus?.addEventListener('change', filterPengajuan);

    btnResetFilter?.addEventListener('click', function () {
        if (cariInput) cariInput.value = '';
        if (filterStatus) filterStatus.value = 'semua';

        filterPengajuan();
    });

    // =========================================
    // STATUS PENGAJUAN
    // =========================================

    function tampilkanStatus(status) {
        const label = {
            menunggu_verifikasi: 'Menunggu Verifikasi',
            disetujui: 'Disetujui',
            ditolak: 'Ditolak',
            dibatalkan: 'Dibatalkan'
        };

        const className = {
            menunggu_verifikasi: 'status-menunggu',
            disetujui: 'status-disetujui',
            ditolak: 'status-ditolak',
            dibatalkan: 'status-dibatalkan'
        };

        const icon = {
            menunggu_verifikasi: 'fa-clock',
            disetujui: 'fa-check-circle',
            ditolak: 'fa-times-circle',
            dibatalkan: 'fa-ban'
        };

        const element = document.getElementById('detailStatus');

        if (!element) return;

        element.className =
            'status-pengajuan ' +
            (className[status] || 'status-dibatalkan');

        element.replaceChildren();

        const iconElement = buatElemen(
            'i',
            'fas ' + (icon[status] || 'fa-info-circle')
        );

        element.append(
            iconElement,
            document.createTextNode(
                ' ' + (label[status] || status || '-')
            )
        );
    }

    // =========================================
    // RINCIAN TAGIHAN
    // =========================================

    function tampilkanRincianTagihan(daftar) {
        const container = document.getElementById(
            'detailDaftarTagihan'
        );

        if (!container) return;

        container.replaceChildren();

        if (!Array.isArray(daftar) || daftar.length === 0) {
            container.append(
                buatElemen('p', 'detail-catatan', 'Tidak ada rincian tagihan.')
            );
            return;
        }

        const wrapper = buatElemen('div', 'rincian-tagihan-list');

        daftar.forEach((item, index) => {
            const nama =
                item.nama_tagihan ||
                item.nama ||
                item.jenis_pembayaran ||
                item.tagihan?.nama_tagihan ||
                item.tagihan?.jenis_pembayaran ||
                `Tagihan ${index + 1}`;

            const nominal = Number(
                item.nominal_dibayar ??
                item.nominal ??
                0
            );

            const baris = buatElemen('div', 'rincian-tagihan-item');

            const informasi = buatElemen('div', 'rincian-tagihan-info');
            informasi.append(
                buatElemen('strong', '', nama)
            );

            if (item.keterangan) {
                informasi.append(
                    buatElemen('small', '', item.keterangan)
                );
            }

            baris.append(
                informasi,
                buatElemen(
                    'strong',
                    'rincian-tagihan-nominal',
                    formatRupiah(nominal)
                )
            );

            wrapper.append(baris);
        });

        container.append(wrapper);
    }

    // =========================================
    // BUKTI PEMBAYARAN
    // =========================================

    function tampilkanBukti(url) {
        const container = document.getElementById(
            'detailBuktiPembayaran'
        );

        if (!container) return;

        container.replaceChildren();

        if (!url) {
            container.textContent = 'Bukti pembayaran tidak tersedia.';
            return;
        }

        const alamat = String(url);

        // Hanya izinkan URL relatif atau HTTP(S)
        let urlValid;

        try {
            urlValid = new URL(alamat, window.location.origin);

            if (
                !['http:', 'https:'].includes(urlValid.protocol)
            ) {
                throw new Error('URL bukti tidak valid.');
            }
        } catch {
            container.textContent = 'Alamat bukti pembayaran tidak valid.';
            return;
        }

        const ekstensi = urlValid.pathname
            .split('.')
            .pop()
            .toLowerCase();

        const formatGambar = [
            'jpg', 'jpeg', 'png', 'webp', 'gif'
        ].includes(ekstensi);

        if (formatGambar) {
            const gambar = document.createElement('img');

            gambar.src = urlValid.href;
            gambar.alt = 'Bukti pembayaran';
            gambar.loading = 'lazy';

            gambar.onerror = function () {
                container.textContent =
                    'Bukti pembayaran tidak dapat ditampilkan.';
            };

            container.append(gambar);
        } else if (ekstensi === 'pdf') {
            container.append(
                buatElemen(
                    'p',
                    '',
                    'Dokumen bukti pembayaran tersedia dalam format PDF.'
                )
            );
        } else {
            container.textContent =
                'Format bukti pembayaran tidak didukung untuk pratinjau.';
        }

        const link = buatElemen(
            'a',
            '',
            'Buka bukti pembayaran'
        );

        link.href = urlValid.href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';

        container.append(link);
    }

    // =========================================
    // TAMPILKAN DETAIL
    // =========================================

    function tampilkanDetail(data) {
        const pengajuan = data.pengajuan || data;

        pengajuanAktif = pengajuan;

        const siswa = pengajuan.siswa || {};

        setText('detailNamaSiswa', siswa.nama || '-');
        setText('detailNisn', 'NISN: ' + (siswa.nisn || '-'));

        setText('detailKode', pengajuan.kode_transaksi);
        setText('detailMetode', pengajuan.metode?.toUpperCase());
        setText('detailTanggal', formatTanggal(pengajuan.diajukan_pada));
        setText('detailTotal', formatRupiah(pengajuan.total_diajukan));

        const avatar = document.getElementById('detailAvatar');

        if (avatar) {
            avatar.textContent = siswa.nama
                ? siswa.nama.charAt(0).toUpperCase()
                : '?';
        }

        tampilkanStatus(pengajuan.status);

        tampilkanRincianTagihan(
            pengajuan.detail_tagihan || data.detail_tagihan || []
        );

        tampilkanBukti(
            pengajuan.bukti_url ||
            data.bukti_url ||
            null
        );

        setText(
            'detailCatatanOrangtua',
            pengajuan.catatan_orangtua || 'Tidak ada catatan.'
        );

        const blokCatatanAdmin = document.getElementById(
            'blokCatatanAdmin'
        );

        const catatanAdmin = pengajuan.catatan_admin || '';

        if (blokCatatanAdmin) {
            blokCatatanAdmin.hidden = !catatanAdmin;
        }

        setText('detailCatatanAdmin', catatanAdmin);

        // Tombol verifikasi hanya muncul untuk pengajuan yang menunggu
        const bolehVerifikasi =
            pengajuan.status === 'menunggu_verifikasi';

        const actions = document.getElementById('detailActions');

        if (actions) {
            actions.hidden = !bolehVerifikasi;
        }
    }

    async function bukaDetail(id) {
        pengajuanAktif = null;

        loadingDetail.hidden = false;
        contentDetail.hidden = true;
        errorDetail.hidden = true;

        bukaModal(modalDetail);

        try {
            const hasil = await ambilJSON(URL_DETAIL(id));

            if (!hasil.sukses) {
                throw new Error(
                    hasil.pesan || 'Gagal mengambil detail pengajuan.'
                );
            }

            tampilkanDetail(hasil);

            loadingDetail.hidden = true;
            contentDetail.hidden = false;

        } catch (error) {
            console.error('Gagal memuat detail:', error);

            loadingDetail.hidden = true;
            errorDetail.hidden = false;
            errorDetail.textContent =
                error.message || 'Gagal memuat detail pengajuan.';
        }
    }

    // Klik tombol detail
    tabel?.addEventListener('click', function (event) {
        const tombol = event.target.closest(
            '.btn-detail-pengajuan'
        );

        if (!tombol) return;

        const id = tombol.dataset.pengajuanId;

        if (id) {
            bukaDetail(id);
        }
    });

    // =========================================
    // MODAL KONFIRMASI
    // =========================================

    function bukaKonfirmasi(tindakan) {
        if (!pengajuanAktif) return;

        tindakanAktif = tindakan;

        const menolak = tindakan === 'tolak';

        setText(
            'judulKonfirmasi',
            menolak ? 'Tolak Pengajuan?' : 'Setujui Pembayaran?'
        );

        setText(
            'pesanKonfirmasi',
            menolak
                ? 'Pengajuan ini akan ditolak. Tuliskan alasan penolakan agar orang tua mengetahui penyebabnya.'
                : 'Pastikan bukti pembayaran dan seluruh rincian tagihan sudah sesuai sebelum menyetujui transaksi.'
        );

        blokAlasan.hidden = !menolak;

        if (inputAlasan) {
            inputAlasan.value = '';
        }

        btnKonfirmasi.textContent = menolak
            ? 'Ya, Tolak Pengajuan'
            : 'Ya, Setujui Pembayaran';

        btnKonfirmasi.style.background = menolak
            ? '#c84e4e'
            : '#014737';

        bukaModal(modalKonfirmasi);
    }

    btnBukaSetujui?.addEventListener('click', function () {
        bukaKonfirmasi('setujui');
    });

    btnBukaTolak?.addEventListener('click', function () {
        bukaKonfirmasi('tolak');
    });

    // =========================================
    // KIRIM VERIFIKASI
    // =========================================

    async function prosesVerifikasi() {
        if (!pengajuanAktif || !tindakanAktif || sedangMemproses) {
            return;
        }

        const id = pengajuanAktif.id;
        const tindakan = tindakanAktif;

        const catatan = inputAlasan?.value.trim() || '';

        if (tindakan === 'tolak' && !catatan) {
            tampilkanNotifikasi(
                'Mohon tuliskan alasan penolakan terlebih dahulu.',
                'warning'
            );

            inputAlasan?.focus();
            return;
        }

        sedangMemproses = true;
        btnKonfirmasi.disabled = true;
        btnKonfirmasi.textContent = 'Memproses...';

        try {
            const hasil = await ambilJSON(URL_VERIFIKASI(id), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    tindakan: tindakan,
                    catatan_admin: catatan
                })
            });

            if (!hasil.sukses) {
                throw new Error(
                    hasil.pesan || 'Verifikasi gagal diproses.'
                );
            }

            tutupModal(modalKonfirmasi);
            tutupModal(modalDetail);

            tampilkanNotifikasi(
                hasil.pesan ||
                (
                    tindakan === 'setujui'
                        ? 'Pembayaran berhasil disetujui.'
                        : 'Pengajuan berhasil ditolak.'
                ),
                'success'
            );

            // Perbarui statistik dan status dari database
            setTimeout(function () {
                window.location.reload();
            }, 1000);

        } catch (error) {
            console.error('Verifikasi gagal:', error);

            tampilkanNotifikasi(
                error.message || 'Terjadi kesalahan saat verifikasi.',
                'error'
            );

        } finally {
            sedangMemproses = false;
            btnKonfirmasi.disabled = false;

            btnKonfirmasi.textContent =
                tindakan === 'tolak'
                    ? 'Ya, Tolak Pengajuan'
                    : 'Ya, Setujui Pembayaran';
        }
    }

    btnKonfirmasi?.addEventListener('click', prosesVerifikasi);

    // =========================================
    // TUTUP MODAL
    // =========================================

    document.querySelectorAll('[data-close-modal]').forEach((button) => {
        button.addEventListener('click', function () {
            tutupModal(modalDetail);
        });
    });

    document.querySelectorAll('[data-close-konfirmasi]').forEach((button) => {
        button.addEventListener('click', function () {
            if (!sedangMemproses) {
                tutupModal(modalKonfirmasi);
            }
        });
    });

    [modalDetail, modalKonfirmasi].forEach((modal) => {
        modal?.addEventListener('click', function (event) {
            if (
                event.target === modal &&
                !sedangMemproses
            ) {
                tutupModal(modal);
            }
        });
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape' || sedangMemproses) return;

        if (modalKonfirmasi?.classList.contains('show')) {
            tutupModal(modalKonfirmasi);
        } else if (modalDetail?.classList.contains('show')) {
            tutupModal(modalDetail);
        }
    });

    // =========================================
    // INISIALISASI
    // =========================================

    filterPengajuan();

});

