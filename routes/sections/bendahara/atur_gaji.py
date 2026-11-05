from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, abort, jsonify
)
from decimal import Decimal, InvalidOperation
from datetime import datetime
from types import SimpleNamespace
from models import (
    db,
    Guru,
    GajiGuru,
    DetailGajiGuru,
    User
)

import json
import secrets
import string

# Blueprint terpisah untuk pengaturan gaji
atur_gaji_bp = Blueprint(
    'atur_gaji',
    __name__,
    url_prefix='/bendahara/atur-gaji'
)


# ==========================================================
# PEMERIKSAAN AKSES
# ==========================================================

def bendahara_required():
    """
    Pemeriksaan akses modul Bendahara.
    Mengikuti format session dari login aplikasi.
    """

    # Pastikan pengguna sudah login
    if session.get('logged_in') is not True:
        return redirect(url_for('login.halaman_login'))

    # Pastikan menggunakan sistem sekolah
    if session.get('sistem_mode') != 'sekolah':
        abort(403)

    # Admin memiliki akses
    role = (session.get('role') or '').strip().lower()

    if role == 'admin':
        return

    # Periksa tugas tambahan
    daftar_tugas = session.get('daftar_tugas', [])

    if isinstance(daftar_tugas, str):
        daftar_tugas = daftar_tugas.split(',')

    daftar_tugas = [
        tugas.strip().lower()
        for tugas in daftar_tugas
        if tugas.strip()
    ]

    # Izinkan Bendahara
    if 'bendahara' in daftar_tugas:
        return

    abort(403)

def buat_kode_verifikasi(bulan, tahun):
    karakter = string.ascii_uppercase + string.digits
    kode_unik = ''.join(secrets.choice(karakter) for _ in range(6))

    return f"SLP-{tahun}{bulan:02d}-{kode_unik}"

# ==========================================================
# UTILITAS
# ==========================================================

def angka_uang(nilai):
    """Mengubah input nominal menjadi Decimal yang aman."""
    if nilai is None or str(nilai).strip() == '':
        return Decimal('0')

    nilai = str(nilai).strip().replace('.', '').replace(',', '.')

    try:
        hasil = Decimal(nilai)
        if hasil < 0:
            raise ValueError('Nominal tidak boleh negatif.')

        return hasil.quantize(Decimal('0.01'))

    except (InvalidOperation, ValueError):
        raise ValueError('Nominal gaji tidak valid.')


def format_bulan(bulan):
    nama_bulan = [
        '',
        'Januari', 'Februari', 'Maret', 'April',
        'Mei', 'Juni', 'Juli', 'Agustus',
        'September', 'Oktober', 'November', 'Desember'
    ]

    return nama_bulan[bulan] if 1 <= bulan <= 12 else '-'


# ==========================================================
# UTILITAS KOMPONEN GAJI DINAMIS
# ==========================================================

def baca_komponen_gaji():
    """
    Membaca komponen penerimaan dan potongan
    dari JSON yang dikirim oleh form.
    """

    raw = request.form.get('komponen_json', '[]')

    try:
        komponen = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise ValueError(
            'Format komponen gaji tidak valid.'
        )

    if not isinstance(komponen, list):
        raise ValueError(
            'Daftar komponen gaji tidak valid.'
        )

    hasil = []
    total_penerimaan = Decimal('0')
    total_potongan = Decimal('0')

    for index, item in enumerate(komponen):

        if not isinstance(item, dict):
            raise ValueError(
                'Format item komponen tidak valid.'
            )

        jenis = str(item.get('jenis', '')).strip().lower()

        nama_item = str(
            item.get('nama_item', '')
        ).strip()

        if jenis not in ('penerimaan', 'potongan'):
            raise ValueError(
                'Jenis komponen tidak valid.'
            )

        if not nama_item:
            raise ValueError(
                'Nama komponen tidak boleh kosong.'
            )

        if len(nama_item) > 120:
            raise ValueError(
                'Nama komponen maksimal 120 karakter.'
            )

        try:
            nominal = Decimal(
                str(item.get('nominal') or '0').strip()
            ).quantize(Decimal('0.01'))

            if not nominal.is_finite() or nominal < 0:
                raise ValueError

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError('Nominal komponen tidak valid.')

        hasil.append({
            'jenis': jenis,
            'nama_item': nama_item,
            'nominal': nominal,
            'urutan': index
        })

        if jenis == 'penerimaan':
            total_penerimaan += nominal
        else:
            total_potongan += nominal

    gaji_bersih = total_penerimaan - total_potongan

    if gaji_bersih < 0:
        raise ValueError(
            'Total potongan tidak boleh melebihi total penerimaan.'
        )

    return {
        'komponen': hasil,
        'total_penerimaan': total_penerimaan,
        'total_potongan': total_potongan,
        'gaji_bersih': gaji_bersih
    }

# ==========================================================
# HALAMAN PENGATURAN GAJI
# ==========================================================

@atur_gaji_bp.route('/', methods=['GET', 'POST'])
def index():
    akses = bendahara_required()

    if akses:
        return akses

    sekarang = datetime.now()

    # ------------------------------------------------------
    # PERIODE DEFAULT GAJI
    # Default: bulan sebelumnya
    # ------------------------------------------------------

    if sekarang.month == 1:
        bulan_default = 12
        tahun_default = sekarang.year - 1
    else:
        bulan_default = sekarang.month - 1
        tahun_default = sekarang.year

    # ------------------------------------------------------
    # BULAN DAN TAHUN YANG DIPILIH BENDAHARA
    # ------------------------------------------------------

    # Indeks bulan sekarang sebagai batas paling baru
    indeks_sekarang = sekarang.year * 12 + sekarang.month - 1

    # Default periode penggajian: bulan sebelumnya
    indeks_default = indeks_sekarang - 1

    try:
        bulan = int(request.values.get('bulan', (indeks_default % 12) + 1))
        tahun = int(request.values.get('tahun', indeks_default // 12))

        if not 1 <= bulan <= 12:
            raise ValueError

        if not 2000 <= tahun <= 2100:
            raise ValueError

        indeks_dipilih = tahun * 12 + bulan - 1

        # Tidak boleh memilih periode setelah bulan sekarang
        if indeks_dipilih > indeks_sekarang:
            indeks_dipilih = indeks_sekarang
            tahun = indeks_dipilih // 12
            bulan = (indeks_dipilih % 12) + 1

    except (ValueError, TypeError):

        flash('Bulan atau tahun tidak valid.', 'danger')

        return redirect(url_for('atur_gaji.index'))

    # ------------------------------------------------------
    # SIMPAN / PERBARUI GAJI DINAMIS
    # ------------------------------------------------------

    if request.method == 'POST':

        try:
            guru_id = request.form.get(
                'guru_id', ''
            ).strip()

            if not guru_id:
                raise ValueError(
                    'Silakan pilih guru terlebih dahulu.'
                )

            guru = Guru.query.filter_by(
                id=guru_id
            ).first()

            if not guru:
                raise ValueError(
                    'Data guru tidak ditemukan.'
                )

            # Baca seluruh komponen dinamis
            hasil = baca_komponen_gaji()

            komponen = hasil['komponen']

            total_penerimaan = hasil[
                'total_penerimaan'
            ]

            total_potongan = hasil[
                'total_potongan'
            ]

            gaji_bersih = hasil[
                'gaji_bersih'
            ]

            # Cari data gaji periode ini
            data_gaji = GajiGuru.query.filter_by(
                guru_id=guru_id,
                bulan=bulan,
                tahun=tahun
            ).first()

            # Jangan izinkan perubahan jika slip sudah diterbitkan
            if (
                data_gaji
                and data_gaji.status_penerbitan == 'terbit'
            ):
                raise ValueError(
                    'Slip gaji sudah diterbitkan dan tidak dapat diedit.'
                )

            # Buat data gaji baru jika belum ada
            if not data_gaji:

                data_gaji = GajiGuru(
                    guru_id=guru_id,
                    bulan=bulan,
                    tahun=tahun,
                    status_penerbitan='draft'
                )

                db.session.add(data_gaji)

                # Pastikan ID gaji sudah tersedia
                db.session.flush()

            # --------------------------------------------------
            # KOMPATIBILITAS KOLOM LAMA
            # --------------------------------------------------
            # Komponen dinamis sekarang menjadi sumber utama.
            # Kolom lama tetap dipertahankan agar struktur
            # database lama tidak perlu dihapus.
            # --------------------------------------------------

            data_gaji.gaji_pokok = Decimal('0')
            data_gaji.tunjangan_jabatan = Decimal('0')
            data_gaji.tunjangan_fungsional = Decimal('0')
            data_gaji.tunjangan_lain = Decimal('0')
            data_gaji.bonus = Decimal('0')

            data_gaji.potongan_wajib = Decimal('0')
            data_gaji.pph = Decimal('0')
            data_gaji.potongan_terlambat = Decimal('0')
            data_gaji.pinjaman = Decimal('0')

            # Simpan total hasil perhitungan server
            data_gaji.total_penerimaan = total_penerimaan
            data_gaji.total_potongan = total_potongan
            data_gaji.gaji_bersih = gaji_bersih

            # --------------------------------------------------
            # HAPUS DETAIL KOMPONEN LAMA PER GAJI
            # --------------------------------------------------

            DetailGajiGuru.query.filter_by(
                gaji_id=data_gaji.id
            ).delete(
                synchronize_session=False
            )

            # --------------------------------------------------
            # SIMPAN DETAIL KOMPONEN BARU
            # --------------------------------------------------

            for item in komponen:

                detail = DetailGajiGuru(
                    gaji_id=data_gaji.id,
                    jenis=item['jenis'],
                    nama_item=item['nama_item'],
                    nominal=item['nominal'],
                    urutan=item['urutan']
                )

                db.session.add(detail)

            # --------------------------------------------------
            # COMMIT
            # --------------------------------------------------

            db.session.commit()

            flash(
                f'Pengaturan gaji {guru.nama} berhasil disimpan.',
                'success'
            )

        except ValueError as e:

            db.session.rollback()

            flash(str(e), 'danger')

        except Exception as e:

            db.session.rollback()

            print(
                'ERROR SIMPAN GAJI:',
                repr(e)
            )

            flash(
                'Terjadi kesalahan saat menyimpan data gaji.',
                'danger'
            )

        return redirect(
            url_for(
                'atur_gaji.index',
                bulan=bulan,
                tahun=tahun,
                akhir_bulan=request.values.get(
                    'akhir_bulan', sekarang.month
                ),
                akhir_tahun=request.values.get(
                    'akhir_tahun', sekarang.year
                )
            )
        )


    # ------------------------------------------------------
    # AMBIL SELURUH DATA GURU
    # ------------------------------------------------------

    daftar_guru = Guru.query.order_by(
        Guru.nama.asc()
    ).all()

    # ------------------------------------------------------
    # AMBIL DATA GAJI PADA PERIODE TERPILIH
    # ------------------------------------------------------

    data_gaji_periode = GajiGuru.query.filter_by(
        bulan=bulan,
        tahun=tahun
    ).all()

    print("\n========== DEBUG PENGGAJIAN ==========")
    print("PERIODE:", bulan, tahun)
    print("JUMLAH DATA GAJI:", len(data_gaji_periode))

    for data in data_gaji_periode:

        detail = DetailGajiGuru.query.filter_by(
            gaji_id=data.id
        ).all()

        print("\nGURU ID:", data.guru_id)
        print("GAJI ID:", data.id)
        print("TOTAL PENERIMAAN:", data.total_penerimaan)
        print("TOTAL POTONGAN:", data.total_potongan)
        print("GAJI BERSIH:", data.gaji_bersih)
        print("JUMLAH DETAIL:", len(detail))

        for item in detail:
            print(
                "DETAIL:",
                item.id,
                "| JENIS:", repr(item.jenis),
                "| NAMA:", item.nama_item,
                "| NOMINAL:", item.nominal
            )

    print("======================================\n")

    # Pemetaan data gaji berdasarkan ID guru
    gaji_per_guru = {
        str(data.guru_id).strip(): data
        for data in data_gaji_periode
    }

    # ------------------------------------------------------
    # GABUNGKAN SELURUH GURU DENGAN DATA GAJINYA
    # ------------------------------------------------------

    daftar_gaji = []

    for guru in daftar_guru:

        data = gaji_per_guru.get(
            str(guru.id).strip()
        )

        total_penerimaan = Decimal('0')
        total_potongan = Decimal('0')
        gaji_bersih = Decimal('0')

        if data:

            # Ambil detail komponen dari database
            detail = DetailGajiGuru.query.filter_by(
                gaji_id=data.id
            ).all()

            if detail:

                for item in detail:

                    nominal = Decimal(
                        str(item.nominal or 0)
                    )

                    jenis = str(item.jenis or '').strip().lower()

                    if jenis == 'penerimaan':
                        total_penerimaan += nominal

                    elif jenis == 'potongan':
                        total_potongan += nominal

                gaji_bersih = total_penerimaan - total_potongan

            else:

                # Fallback untuk data gaji lama
                total_penerimaan = Decimal(
                    str(data.total_penerimaan or 0)
                )

                total_potongan = Decimal(
                    str(data.total_potongan or 0)
                )

                gaji_bersih = Decimal(
                    str(data.gaji_bersih or 0)
                )

            # Jika data lama belum memiliki total,
            # hitung dari kolom-kolom gaji lama.
            if (
                not detail
                and total_penerimaan == 0
                and total_potongan == 0
            ):

                kolom_penerimaan = [
                    data.gaji_pokok,
                    data.tunjangan_jabatan,
                    data.tunjangan_fungsional,
                    data.tunjangan_lain,
                    data.bonus
                ]

                kolom_potongan = [
                    data.potongan_wajib,
                    data.pph,
                    data.potongan_terlambat,
                    data.pinjaman
                ]

                total_penerimaan = sum(
                    (
                        Decimal(str(nilai or 0))
                        for nilai in kolom_penerimaan
                    ),
                    Decimal('0')
                )

                total_potongan = sum(
                    (
                        Decimal(str(nilai or 0))
                        for nilai in kolom_potongan
                    ),
                    Decimal('0')
                )

                gaji_bersih = (
                    total_penerimaan - total_potongan
                )

        daftar_gaji.append(
            SimpleNamespace(
                guru=guru,
                data=data,

                # Status penerbitan slip
                status=(
                    data.status_penerbitan
                    if data else 'belum_ada'
                ),

                # Status pembayaran tetap terpisah
                status_pembayaran=(
                    data.status
                    if data else 'belum'
                ),

                # Penanda apakah record gaji sudah tersimpan
                has_salary=data is not None,

                gaji_id=data.id if data else None,

                total_penerimaan=total_penerimaan,
                total_potongan=total_potongan,
                gaji_bersih=gaji_bersih
            )
        )

    # ------------------------------------------------------
    # STATISTIK PENGGAJIAN
    # ------------------------------------------------------

    total_guru = len(daftar_guru)

    # Hanya menghitung guru yang sudah memiliki record gaji
    total_draft = sum(
        1 for item in daftar_gaji
        if item.has_salary and item.status == 'draft'
    )

    total_terbit = sum(
        1 for item in daftar_gaji
        if item.has_salary and item.status == 'terbit'
    )

    total_penggajian = sum(
        (
            Decimal(str(item.gaji_bersih or 0))
            for item in daftar_gaji
        ),
        Decimal('0')
    )

    # ======================================================
    # NAVIGASI ARSIP PENGGAJIAN (5 BULAN)
    # ======================================================

    JUMLAH_PERIODE = 5

    indeks_sekarang = sekarang.year * 12 + sekarang.month - 1

    # Kelompok awal selalu berakhir pada bulan sekarang
    try:
        akhir_bulan = int(request.args.get('akhir_bulan', sekarang.month))
        akhir_tahun = int(request.args.get('akhir_tahun', sekarang.year))

        indeks_akhir = akhir_tahun * 12 + akhir_bulan - 1

        if not 1 <= akhir_bulan <= 12:
            raise ValueError

        if indeks_akhir > indeks_sekarang:
            indeks_akhir = indeks_sekarang

    except (ValueError, TypeError):
        indeks_akhir = indeks_sekarang

    # Periode yang sedang dipilih harus menjadi ujung kelompok
    # ketika pengguna memilih salah satu bulan.
    if request.args.get('bulan') and request.args.get('tahun'):
        indeks_akhir = min(
            tahun * 12 + bulan - 1,
            indeks_sekarang
        )

    # Awal kelompok 5 bulan
    indeks_awal = indeks_akhir - (JUMLAH_PERIODE - 1)

    daftar_periode = []

    for indeks in range(indeks_awal, indeks_akhir + 1):

        nomor_tahun = indeks // 12
        nomor_bulan = (indeks % 12) + 1

        daftar_periode.append(
            SimpleNamespace(
                bulan=nomor_bulan,
                tahun=nomor_tahun,
                value=f'{nomor_tahun}-{nomor_bulan:02d}',
                label=f'{format_bulan(nomor_bulan)} {nomor_tahun}',
                active=(
                    nomor_bulan == bulan
                    and nomor_tahun == tahun
                ),
                url=url_for(
                    'atur_gaji.index',
                    bulan=nomor_bulan,
                    tahun=nomor_tahun,
                    akhir_bulan=nomor_bulan,
                    akhir_tahun=nomor_tahun
                )
            )
        )

    # Navigasi kelompok 5 bulan sebelumnya dan berikutnya
    indeks_akhir_lama = indeks_akhir - JUMLAH_PERIODE
    indeks_akhir_baru = min(
        indeks_akhir + JUMLAH_PERIODE,
        indeks_sekarang
    )

    url_lebih_lama = url_for(
        'atur_gaji.index',
        bulan=(indeks_akhir_lama % 12) + 1,
        tahun=indeks_akhir_lama // 12,
        akhir_bulan=(indeks_akhir_lama % 12) + 1,
        akhir_tahun=indeks_akhir_lama // 12
    )

    url_lebih_baru = url_for(
        'atur_gaji.index',
        bulan=(indeks_akhir_baru % 12) + 1,
        tahun=indeks_akhir_baru // 12,
        akhir_bulan=(indeks_akhir_baru % 12) + 1,
        akhir_tahun=indeks_akhir_baru // 12
    )

    ada_periode_lebih_lama = True
    ada_periode_lebih_baru = indeks_akhir < indeks_sekarang

    # ------------------------------------------------------
    # INFORMASI PERIODE
    # ------------------------------------------------------

    periode_label = f'{format_bulan(bulan)} {tahun}'
    status_periode = 'Periode Penggajian'

    # ------------------------------------------------------
    # AKUN PENGGUNA LOGIN
    # ------------------------------------------------------

    akun = db.session.get(
        User,
        session.get('user_id')
    )

    return render_template(
        'index.html',

        active_page='atur_gaji',
        halaman_aktif='bendahara',

        user=akun,

        daftar_guru=daftar_guru,
        daftar_gaji=daftar_gaji,
        gaji_per_guru=gaji_per_guru,

        total_guru=total_guru,
        total_penggajian=total_penggajian,
        total_draft=total_draft,
        total_terbit=total_terbit,

        daftar_periode=daftar_periode,
        periode_label=periode_label,
        status_periode=status_periode,

        bulan=bulan,
        tahun=tahun,
        nama_bulan=format_bulan(bulan),
        url_lebih_lama=url_lebih_lama,
        url_lebih_baru=url_lebih_baru,
        ada_periode_lebih_lama=ada_periode_lebih_lama,
        ada_periode_lebih_baru=ada_periode_lebih_baru,

        sekarang=sekarang

    )

# ==========================================================
# API DATA RINCIAN GAJI GURU
# ==========================================================

@atur_gaji_bp.route('/data/<string:guru_id>')
def data_gaji_guru(guru_id):

    akses = bendahara_required()

    if akses:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak.'
        }), 403

    try:
        bulan = int(request.args.get('bulan'))
        tahun = int(request.args.get('tahun'))

        if not 1 <= bulan <= 12:
            raise ValueError

        if not 2000 <= tahun <= 2100:
            raise ValueError

    except (ValueError, TypeError):

        return jsonify({
            'success': False,
            'message': 'Periode tidak valid.'
        }), 400

    guru = Guru.query.filter_by(
        id=guru_id
    ).first()

    if not guru:

        return jsonify({
            'success': False,
            'message': 'Data guru tidak ditemukan.'
        }), 404

    data = GajiGuru.query.filter_by(
        guru_id=guru_id,
        bulan=bulan,
        tahun=tahun
    ).first()

    # ------------------------------------------------------
    # FORMAT NOMINAL
    # ------------------------------------------------------

    def nominal(kolom):

        nilai = getattr(
            data,
            kolom,
            0
        ) if data else 0

        return str(nilai or 0)

    # ------------------------------------------------------
    # KOMPONEN DINAMIS
    # ------------------------------------------------------

    komponen = []

    if data:

        detail = DetailGajiGuru.query.filter_by(
            gaji_id=data.id
        ).order_by(
            DetailGajiGuru.urutan.asc(),
            DetailGajiGuru.id.asc()
        ).all()

        # Jika detail sudah ada, gunakan detail dinamis
        if detail:

            komponen = [
                {
                    'jenis': item.jenis,
                    'nama_item': item.nama_item,
                    'nominal': str(item.nominal or 0),
                    'urutan': item.urutan
                }
                for item in detail
            ]

        else:

            # --------------------------------------------------
            # FALLBACK DATA GAJI LAMA
            # --------------------------------------------------

            komponen_lama = [
                (
                    'penerimaan',
                    'Gaji Pokok',
                    'gaji_pokok'
                ),
                (
                    'penerimaan',
                    'Tunjangan Jabatan',
                    'tunjangan_jabatan'
                ),
                (
                    'penerimaan',
                    'Tunjangan Fungsional',
                    'tunjangan_fungsional'
                ),
                (
                    'penerimaan',
                    'Tunjangan Lainnya',
                    'tunjangan_lain'
                ),
                (
                    'penerimaan',
                    'Bonus / Insentif',
                    'bonus'
                ),
                (
                    'potongan',
                    'Potongan Wajib',
                    'potongan_wajib'
                ),
                (
                    'potongan',
                    'PPh / Pajak',
                    'pph'
                ),
                (
                    'potongan',
                    'Potongan Keterlambatan',
                    'potongan_terlambat'
                ),
                (
                    'potongan',
                    'Pinjaman / Kasbon',
                    'pinjaman'
                )
            ]

            for jenis, nama, kolom in komponen_lama:

                nilai = getattr(
                    data,
                    kolom,
                    0
                ) or 0

                if Decimal(str(nilai)) > 0:

                    komponen.append({
                        'jenis': jenis,
                        'nama_item': nama,
                        'nominal': str(nilai),
                        'urutan': len(komponen)
                    })

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return jsonify({

        'success': True,

        'guru': {
            'id': guru.id,
            'nama': guru.nama,
            'nip': guru.nip or ''
        },

        'gaji': {

            # Data lama tetap disediakan untuk kompatibilitas
            'gaji_pokok': nominal('gaji_pokok'),
            'tunjangan_jabatan': nominal(
                'tunjangan_jabatan'
            ),
            'tunjangan_fungsional': nominal(
                'tunjangan_fungsional'
            ),
            'tunjangan_lain': nominal(
                'tunjangan_lain'
            ),
            'bonus': nominal('bonus'),

            'potongan_wajib': nominal(
                'potongan_wajib'
            ),
            'pph': nominal('pph'),
            'potongan_terlambat': nominal(
                'potongan_terlambat'
            ),
            'pinjaman': nominal('pinjaman'),

            'total_penerimaan': nominal(
                'total_penerimaan'
            ),
            'total_potongan': nominal(
                'total_potongan'
            ),
            'gaji_bersih': nominal(
                'gaji_bersih'
            ),

            # Status penerbitan slip
            'status': (
                data.status_penerbitan
                if data else 'draft'
            ),

            'status_penerbitan': (
                data.status_penerbitan
                if data else 'draft'
            ),

            # Status pembayaran
            'status_pembayaran': (
                data.status
                if data else 'belum'
            ),

            # Penanda apakah gaji sudah tersimpan
            'has_salary': data is not None,

            # Data baru untuk komponen dinamis
            'komponen': komponen
        }
    })


# ==========================================================
# AJAX — MEMUAT ULANG TABEL PENGGAJIAN SAJA
# ==========================================================

@atur_gaji_bp.route('/tabel')
def tabel_penggajian():

    akses = bendahara_required()

    if akses:
        return akses

    sekarang = datetime.now()

    try:
        bulan = int(request.args.get('bulan'))
        tahun = int(request.args.get('tahun'))

        if not 1 <= bulan <= 12:
            raise ValueError

        if not 2000 <= tahun <= 2100:
            raise ValueError

        # Batasi periode agar tidak melewati bulan sekarang
        indeks_sekarang = sekarang.year * 12 + sekarang.month - 1
        indeks_dipilih = tahun * 12 + bulan - 1

        if indeks_dipilih > indeks_sekarang:
            bulan = sekarang.month
            tahun = sekarang.year

    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Periode tidak valid.'
        }), 400

    # ==========================================
    # AMBIL DATA GURU
    # ==========================================

    daftar_guru = Guru.query.order_by(
        Guru.nama.asc()
    ).all()

    # ==========================================
    # AMBIL DATA GAJI SESUAI PERIODE
    # ==========================================

    data_gaji_periode = GajiGuru.query.filter_by(
        bulan=bulan,
        tahun=tahun
    ).all()

    # Petakan data gaji berdasarkan ID guru
    gaji_per_guru = {
        str(data.guru_id).strip(): data
        for data in data_gaji_periode
    }

    daftar_gaji = []

    # ==========================================
    # HITUNG RINCIAN GAJI SETIAP GURU
    # ==========================================

    for guru in daftar_guru:

        data = gaji_per_guru.get(
            str(guru.id).strip()
        )

        total_penerimaan = Decimal('0')
        total_potongan = Decimal('0')
        gaji_bersih = Decimal('0')

        if data:

            detail = DetailGajiGuru.query.filter_by(
                gaji_id=data.id
            ).all()

            if detail:

                for item in detail:

                    nominal = Decimal(
                        str(item.nominal or 0)
                    )

                    jenis = str(
                        item.jenis or ''
                    ).strip().lower()

                    if jenis == 'penerimaan':
                        total_penerimaan += nominal

                    elif jenis == 'potongan':
                        total_potongan += nominal

                gaji_bersih = (
                    total_penerimaan - total_potongan
                )

            else:

                # Fallback data gaji lama
                total_penerimaan = Decimal(
                    str(data.total_penerimaan or 0)
                )

                total_potongan = Decimal(
                    str(data.total_potongan or 0)
                )

                gaji_bersih = Decimal(
                    str(data.gaji_bersih or 0)
                )

                # Jika total lama masih kosong,
                # hitung dari kolom gaji lama.
                if (
                    total_penerimaan == 0
                    and total_potongan == 0
                ):

                    kolom_penerimaan = [
                        data.gaji_pokok,
                        data.tunjangan_jabatan,
                        data.tunjangan_fungsional,
                        data.tunjangan_lain,
                        data.bonus
                    ]

                    kolom_potongan = [
                        data.potongan_wajib,
                        data.pph,
                        data.potongan_terlambat,
                        data.pinjaman
                    ]

                    total_penerimaan = sum(
                        (
                            Decimal(str(nilai or 0))
                            for nilai in kolom_penerimaan
                        ),
                        Decimal('0')
                    )

                    total_potongan = sum(
                        (
                            Decimal(str(nilai or 0))
                            for nilai in kolom_potongan
                        ),
                        Decimal('0')
                    )

                    gaji_bersih = (
                        total_penerimaan - total_potongan
                    )

        daftar_gaji.append(
            SimpleNamespace(
                guru=guru,
                data=data,

                status=(
                    data.status_penerbitan
                    if data else 'belum_ada'
                ),

                status_pembayaran=(
                    data.status
                    if data else 'belum'
                ),

                has_salary=data is not None,

                gaji_id=data.id if data else None,

                total_penerimaan=total_penerimaan,
                total_potongan=total_potongan,
                gaji_bersih=gaji_bersih
            )
        )

    # ==========================================
    # HITUNG STATISTIK PENGGAJIAN
    # ==========================================

    total_guru = len(daftar_guru)

    total_penggajian = sum(
        (
            item.gaji_bersih
            for item in daftar_gaji
        ),
        Decimal('0')
    )

    total_draft = sum(
        1 for item in daftar_gaji
        if item.has_salary and item.status == 'draft'
    )

    total_terbit = sum(
        1 for item in daftar_gaji
        if item.has_salary and item.status == 'terbit'
    )

    # ==========================================
    # KIRIM HTML TABEL + STATISTIK KE JAVASCRIPT
    # ==========================================

    html_tabel = render_template(
        'sections/bendahara/tabel_gaji_rows.html',
        daftar_gaji=daftar_gaji
    )

    return jsonify({
        'success': True,
        'html': html_tabel,
        'statistik': {
            'total_guru': total_guru,
            'total_penggajian': float(total_penggajian),
            'total_draft': total_draft,
            'total_terbit': total_terbit
        }
    })


# ==========================================================
# API PENERBITAN SLIP GAJI
# ==========================================================

def periode_valid(bulan, tahun):
    """Memvalidasi periode penggajian."""

    try:
        bulan = int(bulan)
        tahun = int(tahun)

        if not 1 <= bulan <= 12:
            return None

        if not 2000 <= tahun <= 2100:
            return None

        sekarang = datetime.now()

        indeks_sekarang = (
            sekarang.year * 12 + sekarang.month - 1
        )

        indeks_dipilih = tahun * 12 + bulan - 1

        if indeks_dipilih > indeks_sekarang:
            return None

        return bulan, tahun

    except (ValueError, TypeError):
        return None


def terbitkan_data_gaji(data_gaji):
    """Mengubah status penerbitan satu record gaji."""

    if data_gaji.status_penerbitan == 'terbit':
        return False

    if data_gaji.status_penerbitan != 'draft':
        raise ValueError(
            'Status penerbitan gaji tidak valid.'
        )

    data_gaji.status_penerbitan = 'terbit'

    if not data_gaji.kode_verifikasi:
        data_gaji.kode_verifikasi = buat_kode_verifikasi(
            data_gaji.bulan,
            data_gaji.tahun
        )

    return True


# ----------------------------------------------------------
# TERBITKAN SATU SLIP
# ----------------------------------------------------------

@atur_gaji_bp.route(
    '/terbitkan/<int:gaji_id>',
    methods=['POST']
)
def terbitkan_satu(gaji_id):

    akses = bendahara_required()

    if akses:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak.'
        }), 403

    payload = request.get_json(silent=True) or {}

    periode = periode_valid(
        payload.get('bulan'),
        payload.get('tahun')
    )

    if not periode:
        return jsonify({
            'success': False,
            'message': 'Periode penggajian tidak valid.'
        }), 400

    bulan, tahun = periode

    try:
        data_gaji = GajiGuru.query.filter_by(
            id=gaji_id,
            bulan=bulan,
            tahun=tahun
        ).with_for_update().first()

        if not data_gaji:
            return jsonify({
                'success': False,
                'message': 'Data gaji tidak ditemukan.'
            }), 404

        if data_gaji.status_penerbitan == 'terbit':
            return jsonify({
                'success': False,
                'message': 'Slip gaji ini sudah diterbitkan.'
            }), 409

        terbitkan_data_gaji(data_gaji)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Slip gaji berhasil diterbitkan.',
            'gaji_id': data_gaji.id
        })

    except ValueError as e:
        db.session.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

    except Exception as e:
        db.session.rollback()

        print('ERROR TERBITKAN GAJI:', repr(e))

        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat menerbitkan slip gaji.'
        }), 500


# ----------------------------------------------------------
# TERBITKAN BEBERAPA SLIP TERPILIH
# ----------------------------------------------------------

@atur_gaji_bp.route(
    '/terbitkan-terpilih',
    methods=['POST']
)
def terbitkan_terpilih():

    akses = bendahara_required()

    if akses:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak.'
        }), 403

    payload = request.get_json(silent=True) or {}

    daftar_id = payload.get('gaji_ids')

    periode = periode_valid(
        payload.get('bulan'),
        payload.get('tahun')
    )

    if not periode:
        return jsonify({
            'success': False,
            'message': 'Periode penggajian tidak valid.'
        }), 400

    bulan, tahun = periode

    if not isinstance(daftar_id, list) or not daftar_id:
        return jsonify({
            'success': False,
            'message': 'Pilih minimal satu slip gaji.'
        }), 400

    try:
        # Validasi ID yang dikirim
        try:
            daftar_id = list(dict.fromkeys(
                int(item) for item in daftar_id
            ))
        except (ValueError, TypeError):
            raise ValueError('Daftar ID gaji tidak valid.')

        if any(item <= 0 for item in daftar_id):
            raise ValueError('ID gaji tidak valid.')

        if len(daftar_id) > 500:
            raise ValueError(
                'Maksimal 500 slip dalam satu penerbitan.'
            )

        data_gaji = GajiGuru.query.filter(
            GajiGuru.id.in_(daftar_id),
            GajiGuru.bulan == bulan,
            GajiGuru.tahun == tahun
        ).with_for_update().all()

        if len(data_gaji) != len(daftar_id):
            raise ValueError(
                'Sebagian data gaji tidak ditemukan.'
            )

        # Pastikan semuanya masih draft
        if any(
            item.status_penerbitan != 'draft'
            for item in data_gaji
        ):
            raise ValueError(
                'Sebagian slip sudah diterbitkan atau statusnya tidak valid.'
            )

        # Terbitkan seluruh data dalam satu transaksi
        for item in data_gaji:
            terbitkan_data_gaji(item)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': (
                f'{len(data_gaji)} slip gaji berhasil diterbitkan.'
            ),
            'jumlah_terbit': len(data_gaji)
        })

    except ValueError as e:
        db.session.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

    except Exception as e:
        db.session.rollback()

        print('ERROR TERBITKAN GAJI TERPILIH:', repr(e))

        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat menerbitkan slip gaji.'
        }), 500


# ----------------------------------------------------------
# TERBITKAN SEMUA DRAFT DALAM SATU PERIODE
# ----------------------------------------------------------

@atur_gaji_bp.route(
    '/terbitkan-semua',
    methods=['POST']
)
def terbitkan_semua():

    akses = bendahara_required()

    if akses:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak.'
        }), 403

    payload = request.get_json(silent=True) or {}

    periode = periode_valid(
        payload.get('bulan'),
        payload.get('tahun')
    )

    if not periode:
        return jsonify({
            'success': False,
            'message': 'Periode penggajian tidak valid.'
        }), 400

    bulan, tahun = periode

    try:
        daftar_gaji = GajiGuru.query.filter_by(
            bulan=bulan,
            tahun=tahun,
            status_penerbitan='draft'
        ).with_for_update().all()

        if not daftar_gaji:
            return jsonify({
                'success': False,
                'message': 'Tidak ada slip Draft pada periode ini.'
            }), 400

        for item in daftar_gaji:
            terbitkan_data_gaji(item)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': (
                f'{len(daftar_gaji)} slip gaji '
                f'periode {format_bulan(bulan)} {tahun} '
                'berhasil diterbitkan.'
            ),
            'jumlah_terbit': len(daftar_gaji)
        })

    except Exception as e:
        db.session.rollback()

        print('ERROR TERBITKAN SEMUA GAJI:', repr(e))

        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat menerbitkan seluruh slip.'
        }), 500



# ==========================================================
# API VERIFIKASI KEASLIAN SLIP GAJI
# ==========================================================
@atur_gaji_bp.route('/verifikasi', methods=['GET'])
def verifikasi_slip_gaji():

    akses = bendahara_required()

    if akses:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak.'
        }), 403

    kode = request.args.get('kode', '').strip().upper()

    print("KODE VERIFIKASI DITERIMA:", repr(kode))

    if not kode:
        return jsonify({
            'success': False,
            'message': 'Masukkan kode verifikasi.'
        }), 400

    if len(kode) > 40:
        return jsonify({
            'success': False,
            'message': 'Format kode verifikasi tidak valid.'
        }), 400

    try:
        # Cari slip berdasarkan kode verifikasi.
        # Hanya slip yang sudah diterbitkan yang dianggap valid.
        data_gaji = GajiGuru.query.filter_by(
            kode_verifikasi=kode,
            status_penerbitan='terbit'
        ).first()

        if not data_gaji:
            return jsonify({
                'success': False,
                'valid': False,
                'message': (
                    'Kode verifikasi tidak ditemukan. '
                    'Slip gaji tidak dapat dinyatakan valid.'
                )
            }), 404

        # Ambil data guru
        guru = Guru.query.filter_by(
            id=data_gaji.guru_id
        ).first()

        if not guru:
            return jsonify({
                'success': False,
                'valid': False,
                'message': (
                    'Data guru pemilik slip tidak ditemukan.'
                )
            }), 404

        # Ambil seluruh detail komponen gaji
        detail_gaji = DetailGajiGuru.query.filter_by(
            gaji_id=data_gaji.id
        ).order_by(
            DetailGajiGuru.urutan.asc(),
            DetailGajiGuru.id.asc()
        ).all()

        komponen = []

        total_penerimaan = Decimal('0')
        total_potongan = Decimal('0')

        for item in detail_gaji:

            nominal = Decimal(
                str(item.nominal or 0)
            )

            komponen.append({
                'jenis': item.jenis,
                'nama_item': item.nama_item,
                'nominal': str(nominal)
            })

            if item.jenis == 'penerimaan':
                total_penerimaan += nominal

            elif item.jenis == 'potongan':
                total_potongan += nominal

        # Gunakan total tersimpan sebagai sumber utama.
        # Jika total belum tersedia, hitung dari detail.
        total_penerimaan = Decimal(
            str(
                data_gaji.total_penerimaan
                if data_gaji.total_penerimaan is not None
                else total_penerimaan
            )
        )

        total_potongan = Decimal(
            str(
                data_gaji.total_potongan
                if data_gaji.total_potongan is not None
                else total_potongan
            )
        )

        gaji_bersih = Decimal(
            str(
                data_gaji.gaji_bersih
                if data_gaji.gaji_bersih is not None
                else total_penerimaan - total_potongan
            )
        )

        return jsonify({
            'success': True,
            'valid': True,
            'message': 'Slip gaji berhasil diverifikasi.',

            'data': {
                'kode_verifikasi': data_gaji.kode_verifikasi,

                'guru': {
                    'id': guru.id,
                    'nama': guru.nama,
                    'nip': guru.nip or '',
                    'jabatan': guru.jabatan or 'Guru'
                },

                'periode': {
                    'bulan': data_gaji.bulan,
                    'tahun': data_gaji.tahun,
                    'label': (
                        f'{format_bulan(data_gaji.bulan)} '
                        f'{data_gaji.tahun}'
                    )
                },

                'keuangan': {
                    'total_penerimaan': str(total_penerimaan),
                    'total_potongan': str(total_potongan),
                    'gaji_bersih': str(gaji_bersih)
                },

                'status_penerbitan': data_gaji.status_penerbitan,
                'status_pembayaran': data_gaji.status or 'belum',

                'komponen': komponen
            }
        })

    except Exception as e:

        print(
            'ERROR VERIFIKASI SLIP GAJI:',
            repr(e)
        )

        return jsonify({
            'success': False,
            'message': (
                'Terjadi kesalahan saat memverifikasi slip gaji.'
            )
        }), 500
