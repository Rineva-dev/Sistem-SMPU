
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, abort
)
from decimal import Decimal, InvalidOperation
from datetime import datetime
from models import db, Guru, GajiGuru, User


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
    # SIMPAN / PERBARUI GAJI
    # ------------------------------------------------------

    if request.method == 'POST':
        try:
            guru_id = request.form.get('guru_id', '').strip()

            if not guru_id:
                raise ValueError('Silakan pilih guru terlebih dahulu.')

            guru = Guru.query.filter_by(id=guru_id).first()

            if not guru:
                raise ValueError('Data guru tidak ditemukan.')

            # Ambil komponen gaji
            gaji_pokok = angka_uang(
                request.form.get('gaji_pokok')
            )

            tunjangan_jabatan = angka_uang(
                request.form.get('tunjangan_jabatan')
            )

            tunjangan_fungsional = angka_uang(
                request.form.get('tunjangan_fungsional')
            )

            tunjangan_lain = angka_uang(
                request.form.get('tunjangan_lain')
            )

            bonus = angka_uang(
                request.form.get('bonus')
            )

            # Ambil komponen potongan
            potongan_wajib = angka_uang(
                request.form.get('potongan_wajib')
            )

            pph = angka_uang(
                request.form.get('pph')
            )

            potongan_terlambat = angka_uang(
                request.form.get('potongan_terlambat')
            )

            pinjaman = angka_uang(
                request.form.get('pinjaman')
            )

            # Hitung total
            total_penerimaan = (
                gaji_pokok
                + tunjangan_jabatan
                + tunjangan_fungsional
                + tunjangan_lain
                + bonus
            )

            total_potongan = (
                potongan_wajib
                + pph
                + potongan_terlambat
                + pinjaman
            )

            gaji_bersih = total_penerimaan - total_potongan

            if gaji_bersih < 0:
                raise ValueError(
                    'Total potongan tidak boleh melebihi total penerimaan.'
                )

            # Cari data gaji berdasarkan guru, bulan, dan tahun
            data_gaji = GajiGuru.query.filter_by(
                guru_id=guru_id,
                bulan=bulan,
                tahun=tahun
            ).first()

            # Jika belum ada, buat data baru
            if not data_gaji:
                data_gaji = GajiGuru(
                    guru_id=guru_id,
                    bulan=bulan,
                    tahun=tahun
                )
                db.session.add(data_gaji)

            # Isi komponen gaji
            data_gaji.gaji_pokok = gaji_pokok
            data_gaji.tunjangan_jabatan = tunjangan_jabatan
            data_gaji.tunjangan_fungsional = tunjangan_fungsional
            data_gaji.tunjangan_lain = tunjangan_lain
            data_gaji.bonus = bonus

            data_gaji.potongan_wajib = potongan_wajib
            data_gaji.pph = pph
            data_gaji.potongan_terlambat = potongan_terlambat
            data_gaji.pinjaman = pinjaman

            data_gaji.total_penerimaan = total_penerimaan
            data_gaji.total_potongan = total_potongan
            data_gaji.gaji_bersih = gaji_bersih

            db.session.commit()

            flash(
                f'Pengaturan gaji {guru.nama} berhasil disimpan.',
                'success'
            )

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')

        except Exception:
            db.session.rollback()
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
    # AMBIL DATA GURU
    # ------------------------------------------------------

    daftar_guru = Guru.query.order_by(
        Guru.nama.asc()
    ).all()

    # ------------------------------------------------------
    # AMBIL DATA GAJI PADA PERIODE TERPILIH
    # ------------------------------------------------------

    daftar_gaji = GajiGuru.query.filter_by(
        bulan=bulan,
        tahun=tahun
    ).all()

    # Pemetaan data gaji berdasarkan guru
    gaji_per_guru = {
        data.guru_id: data
        for data in daftar_gaji
    }

    # Ambil akun pengguna yang sedang login
    akun = db.session.get(User, session.get('user_id'))

    return render_template(
        'index.html',
        active_page='atur_gaji',
        halaman_aktif='bendahara',

        user=akun,

        daftar_guru=daftar_guru,
        daftar_gaji=daftar_gaji,
        gaji_per_guru=gaji_per_guru,

        bulan=bulan,
        tahun=tahun,
        nama_bulan=format_bulan(bulan),

        sekarang=sekarang
    )
