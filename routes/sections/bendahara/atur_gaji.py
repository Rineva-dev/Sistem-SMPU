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

    # Bulan dan tahun yang dipilih
    try:
        bulan = int(
            request.values.get('bulan', sekarang.month)
        )
        tahun = int(
            request.values.get('tahun', sekarang.year)
        )

        if not 1 <= bulan <= 12:
            raise ValueError

        if not 2000 <= tahun <= 2100:
            raise ValueError

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

            # Buat data gaji baru jika belum ada
            if not data_gaji:

                data_gaji = GajiGuru(
                    guru_id=guru_id,
                    bulan=bulan,
                    tahun=tahun
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
                tahun=tahun
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

                status=data.status if data else 'draft',

                total_penerimaan=total_penerimaan,
                total_potongan=total_potongan,
                gaji_bersih=gaji_bersih
            )
        )

    # ------------------------------------------------------
    # STATISTIK PENGGAJIAN
    # ------------------------------------------------------

    total_guru = len(daftar_guru)

    total_terbit = sum(
        1 for item in daftar_gaji
        if item.status == 'terbit'
    )

    total_draft = total_guru - total_terbit

    total_penggajian = sum(
        (
            Decimal(str(item.gaji_bersih or 0))
            for item in daftar_gaji
        ),
        Decimal('0')
    )

    # ------------------------------------------------------
    # DAFTAR PERIODE FILTER
    # ------------------------------------------------------

    daftar_periode = []

    for i in range(12):
        nomor_bulan = bulan - i
        nomor_tahun = tahun

        while nomor_bulan <= 0:
            nomor_bulan += 12
            nomor_tahun -= 1

        daftar_periode.append(
            SimpleNamespace(
                value=f'{nomor_tahun}-{nomor_bulan:02d}',
                label=f'{format_bulan(nomor_bulan)} {nomor_tahun}',
                active=(
                    nomor_bulan == bulan
                    and nomor_tahun == tahun
                )
            )
        )

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

            'status': data.status if data else 'draft',

            # Data baru untuk komponen dinamis
            'komponen': komponen
        }
    })
