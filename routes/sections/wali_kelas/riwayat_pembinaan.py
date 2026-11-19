
from datetime import date, datetime

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, abort
)

from sqlalchemy import or_

from models import (
    db, User, Guru, Kelas, TahunPelajaran,
    RiwayatKelas, Siswa, RiwayatPembinaanSiswa
)


riwayat_pembinaan_bp = Blueprint(
    'riwayat_pembinaan',
    __name__,
    url_prefix='/wali-kelas'
)


# ==========================================================
# HELPER: KONTEKS WALI KELAS
# ==========================================================

def get_wali_context():

    if not session.get('logged_in'):
        return None, redirect(url_for('login.halaman_login'))

    if session.get('sistem_mode') != 'sekolah':
        return None, redirect(url_for('login.halaman_login'))

    user = User.query.get(session.get('user_id'))

    if not user or not user.guru_id:
        return None, redirect(url_for('dashboard_wali.index'))

    guru = Guru.query.get(user.guru_id)

    if not guru:
        return None, redirect(url_for('dashboard_wali.index'))

    tahun_aktif = (
        TahunPelajaran.query
        .filter_by(aktif=True)
        .order_by(TahunPelajaran.id.desc())
        .first()
    )

    if not tahun_aktif:
        flash('Tahun pelajaran aktif belum tersedia.', 'warning')
        return None, redirect(url_for('dashboard_wali.index'))

    kode_tp = tahun_aktif.kode
    tahun_dasar = kode_tp.split('-')[0].strip()

    daftar_kelas = (
        Kelas.query
        .filter(
            Kelas.wali_kelas_id == guru.id,
            Kelas.tahun_pelajaran == tahun_dasar
        )
        .order_by(Kelas.nama_kelas.asc())
        .all()
    )

    kelas_ids = [kelas.id for kelas in daftar_kelas]

    context = {
        'user': user,
        'guru': guru,
        'tahun_aktif': tahun_aktif,
        'kode_tp': kode_tp,
        'tahun_dasar': tahun_dasar,
        'daftar_kelas': daftar_kelas,
        'kelas_ids': kelas_ids
    }

    return context, None


# ==========================================================
# HELPER: VALIDASI KEPEMILIKAN KELAS
# ==========================================================

def validasi_kelas_milik_wali(kelas_id, context):

    try:
        kelas_id = int(kelas_id)
    except (TypeError, ValueError):
        abort(400, description='Kelas tidak valid.')

    if kelas_id not in context['kelas_ids']:
        abort(403, description='Anda tidak memiliki akses ke kelas tersebut.')

    return kelas_id


# ==========================================================
# HELPER: VALIDASI SISWA DALAM KELAS
# ==========================================================

def siswa_terdaftar_di_kelas(siswa_id, kelas_id, kode_tp):

    return RiwayatKelas.query.filter_by(
        siswa_id=siswa_id,
        kelas_id=kelas_id,
        tahun_pelajaran=kode_tp
    ).first() is not None


# ==========================================================
# HELPER: AMBIL CATATAN MILIK WALI KELAS
# ==========================================================

def ambil_pembinaan_milik_guru(pembinaan_id, context):

    pembinaan = RiwayatPembinaanSiswa.query.filter(
        RiwayatPembinaanSiswa.id == pembinaan_id,
        RiwayatPembinaanSiswa.guru_id == context['guru'].id,
        RiwayatPembinaanSiswa.tahun_pelajaran == context['kode_tp'],
        RiwayatPembinaanSiswa.kelas_id.in_(context['kelas_ids'])
    ).first()

    if not pembinaan:
        abort(404, description='Riwayat pembinaan tidak ditemukan.')

    return pembinaan


# ==========================================================
# HALAMAN UTAMA RIWAYAT PEMBINAAN
# ==========================================================

@riwayat_pembinaan_bp.route('/riwayat-pembinaan', methods=['GET'])
def index():

    context, error = get_wali_context()

    if error:
        return error

    kelas_ids = context['kelas_ids']

    filter_kelas = request.args.get('kelas', '').strip()
    filter_kategori = request.args.get('kategori', '').strip()
    filter_status = request.args.get('status', '').strip()
    pencarian = request.args.get('q', '').strip()

    # ------------------------------------------------------
    # DAFTAR SISWA
    # ------------------------------------------------------

    daftar_siswa = []

    if kelas_ids:
        daftar_siswa = (
            db.session.query(Siswa, RiwayatKelas.kelas_id)
            .join(
                RiwayatKelas,
                RiwayatKelas.siswa_id == Siswa.id
            )
            .filter(
                RiwayatKelas.tahun_pelajaran == context['kode_tp'],
                RiwayatKelas.kelas_id.in_(kelas_ids)
            )
            .order_by(Siswa.nama.asc())
            .all()
        )

    # ------------------------------------------------------
    # QUERY RIWAYAT PEMBINAAN
    # ------------------------------------------------------

    query = RiwayatPembinaanSiswa.query.filter(
        RiwayatPembinaanSiswa.tahun_pelajaran == context['kode_tp'],
        RiwayatPembinaanSiswa.guru_id == context['guru'].id
    )

    if kelas_ids:
        query = query.filter(
            RiwayatPembinaanSiswa.kelas_id.in_(kelas_ids)
        )
    else:
        query = query.filter(
            RiwayatPembinaanSiswa.id == -1
        )

    if filter_kelas:
        try:
            kelas_filter_id = int(filter_kelas)

            if kelas_filter_id not in kelas_ids:
                abort(403)

            query = query.filter(
                RiwayatPembinaanSiswa.kelas_id == kelas_filter_id
            )

        except ValueError:
            filter_kelas = ''

    if filter_kategori:
        query = query.filter(
            RiwayatPembinaanSiswa.kategori == filter_kategori
        )

    if filter_status:
        query = query.filter(
            RiwayatPembinaanSiswa.status == filter_status
        )

    if pencarian:
        kata = f'%{pencarian}%'

        query = (
            query.join(
                Siswa,
                RiwayatPembinaanSiswa.siswa_id == Siswa.id
            )
            .filter(
                or_(
                    Siswa.nama.ilike(kata),
                    RiwayatPembinaanSiswa.judul.ilike(kata),
                    RiwayatPembinaanSiswa.kronologi.ilike(kata)
                )
            )
        )

    daftar_pembinaan = (
        query
        .order_by(
            RiwayatPembinaanSiswa.tanggal_kejadian.desc(),
            RiwayatPembinaanSiswa.id.desc()
        )
        .all()
    )

    # ------------------------------------------------------
    # STATISTIK
    # ------------------------------------------------------

    statistik_query = RiwayatPembinaanSiswa.query.filter(
        RiwayatPembinaanSiswa.tahun_pelajaran == context['kode_tp'],
        RiwayatPembinaanSiswa.guru_id == context['guru'].id
    )

    if kelas_ids:
        statistik_query = statistik_query.filter(
            RiwayatPembinaanSiswa.kelas_id.in_(kelas_ids)
        )
    else:
        statistik_query = statistik_query.filter(
            RiwayatPembinaanSiswa.id == -1
        )

    semua_pembinaan = statistik_query.all()

    statistik = {
        'total': len(semua_pembinaan),
        'pemantauan': sum(
            1 for item in semua_pembinaan
            if item.status == 'dalam_pemantauan'
        ),
        'membaik': sum(
            1 for item in semua_pembinaan
            if item.status == 'membaik'
        ),
        'selesai': sum(
            1 for item in semua_pembinaan
            if item.status == 'selesai'
        ),
        'rujukan_bk': sum(
            1 for item in semua_pembinaan
            if item.status == 'dirujuk_bk'
        )
    }

    return render_template(
        'sections/wali_kelas/riwayat_pembinaan.html',
        active_page='riwayat_pembinaan_wali',
        halaman_aktif='wali_kelas',
        user='user',

        guru=context['guru'],
        tahun_aktif=context['tahun_aktif'],
        tahun_pelajaran=context['kode_tp'],

        daftar_kelas=context['daftar_kelas'],
        daftar_siswa=daftar_siswa,
        daftar_pembinaan=daftar_pembinaan,

        statistik=statistik,

        filter_kelas=filter_kelas,
        filter_kategori=filter_kategori,
        filter_status=filter_status,
        pencarian=pencarian
    )


# ==========================================================
# TAMBAH RIWAYAT PEMBINAAN
# ==========================================================

@riwayat_pembinaan_bp.route(
    '/riwayat-pembinaan/tambah',
    methods=['POST']
)
def tambah():

    context, error = get_wali_context()

    if error:
        return error

    try:
        siswa_id = int(request.form.get('siswa_id', ''))
        kelas_id = int(request.form.get('kelas_id', ''))
    except (TypeError, ValueError):
        flash('Siswa atau kelas tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    kelas_id = validasi_kelas_milik_wali(
        kelas_id,
        context
    )

    if not siswa_terdaftar_di_kelas(
        siswa_id,
        kelas_id,
        context['kode_tp']
    ):
        flash('Siswa tidak terdaftar di kelas tersebut.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    tanggal_input = request.form.get('tanggal_kejadian', '').strip()

    try:
        tanggal_kejadian = date.fromisoformat(tanggal_input)
    except (TypeError, ValueError):
        flash('Tanggal kejadian tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    kategori = request.form.get('kategori', '').strip()
    tingkat = request.form.get('tingkat_pembinaan', '').strip()
    judul = request.form.get('judul', '').strip()
    kronologi = request.form.get('kronologi', '').strip()
    tindakan = request.form.get('tindakan_pembinaan', '').strip()

    hasil = request.form.get('hasil_pembinaan', '').strip()

    perlu_pemantauan = (
        request.form.get('perlu_pemantauan') == '1'
    )

    tanggal_pemantauan_input = (
        request.form.get('tanggal_pemantauan', '').strip()
    )

    status = request.form.get('status', '').strip()

    komunikasi_orang_tua = (
        request.form.get('komunikasi_orang_tua') == '1'
    )

    catatan_orang_tua = (
        request.form.get('catatan_orang_tua', '').strip()
    )

    kategori_valid = [
        'kedisiplinan',
        'akademik',
        'perilaku',
        'sosial',
        'kehadiran',
        'lainnya'
    ]

    tingkat_valid = [
        'pembinaan_awal',
        'pembinaan_lanjutan',
        'pembinaan_khusus'
    ]

    status_valid = [
        'dalam_pemantauan',
        'membaik',
        'selesai',
        'dirujuk_bk'
    ]

    if kategori not in kategori_valid:
        flash('Kategori pembinaan tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    if tingkat not in tingkat_valid:
        flash('Tingkat pembinaan tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    if status not in status_valid:
        flash('Status pembinaan tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    if not judul or not kronologi or not tindakan:
        flash('Judul, kronologi, dan tindakan pembinaan wajib diisi.', 'warning')
        return redirect(url_for('riwayat_pembinaan.index'))

    tanggal_pemantauan = None

    if tanggal_pemantauan_input:
        try:
            tanggal_pemantauan = date.fromisoformat(
                tanggal_pemantauan_input
            )
        except ValueError:
            flash('Tanggal pemantauan tidak valid.', 'danger')
            return redirect(url_for('riwayat_pembinaan.index'))

    if perlu_pemantauan and not tanggal_pemantauan:
        flash(
            'Tanggal pemantauan wajib diisi jika pemantauan diaktifkan.',
            'warning'
        )
        return redirect(url_for('riwayat_pembinaan.index'))

    pembinaan = RiwayatPembinaanSiswa(
        siswa_id=siswa_id,
        kelas_id=kelas_id,
        guru_id=context['guru'].id,
        tahun_pelajaran=context['kode_tp'],

        tanggal_kejadian=tanggal_kejadian,
        kategori=kategori,
        tingkat_pembinaan=tingkat,

        judul=judul,
        kronologi=kronologi,
        tindakan_pembinaan=tindakan,
        hasil_pembinaan=hasil or None,

        perlu_pemantauan=perlu_pemantauan,
        tanggal_pemantauan=(
            tanggal_pemantauan if perlu_pemantauan else None
        ),

        status=status,
        komunikasi_orang_tua=komunikasi_orang_tua,
        catatan_orang_tua=catatan_orang_tua or None
    )

    try:
        db.session.add(pembinaan)
        db.session.commit()

        flash('Riwayat pembinaan siswa berhasil ditambahkan.', 'success')

    except Exception:
        db.session.rollback()
        flash('Terjadi kesalahan saat menyimpan pembinaan.', 'danger')

    return redirect(url_for('riwayat_pembinaan.index'))


# ==========================================================
# EDIT RIWAYAT PEMBINAAN
# ==========================================================

@riwayat_pembinaan_bp.route(
    '/riwayat-pembinaan/<int:pembinaan_id>/edit',
    methods=['POST']
)
def edit(pembinaan_id):

    context, error = get_wali_context()

    if error:
        return error

    pembinaan = ambil_pembinaan_milik_guru(
        pembinaan_id,
        context
    )

    try:
        siswa_id = int(request.form.get('siswa_id', ''))
        kelas_id = int(request.form.get('kelas_id', ''))
    except (TypeError, ValueError):
        flash('Siswa atau kelas tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    kelas_id = validasi_kelas_milik_wali(
        kelas_id,
        context
    )

    if not siswa_terdaftar_di_kelas(
        siswa_id,
        kelas_id,
        context['kode_tp']
    ):
        flash('Siswa tidak terdaftar di kelas tersebut.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    try:
        tanggal_kejadian = date.fromisoformat(
            request.form.get('tanggal_kejadian', '').strip()
        )
    except (TypeError, ValueError):
        flash('Tanggal kejadian tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    kategori = request.form.get('kategori', '').strip()
    tingkat = request.form.get('tingkat_pembinaan', '').strip()
    judul = request.form.get('judul', '').strip()
    kronologi = request.form.get('kronologi', '').strip()
    tindakan = request.form.get('tindakan_pembinaan', '').strip()
    hasil = request.form.get('hasil_pembinaan', '').strip()

    perlu_pemantauan = (
        request.form.get('perlu_pemantauan') == '1'
    )

    tanggal_pemantauan_input = (
        request.form.get('tanggal_pemantauan', '').strip()
    )

    status = request.form.get('status', '').strip()

    komunikasi_orang_tua = (
        request.form.get('komunikasi_orang_tua') == '1'
    )

    catatan_orang_tua = (
        request.form.get('catatan_orang_tua', '').strip()
    )

    if kategori not in [
        'kedisiplinan', 'akademik', 'perilaku',
        'sosial', 'kehadiran', 'lainnya'
    ]:
        flash('Kategori pembinaan tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    if tingkat not in [
        'pembinaan_awal',
        'pembinaan_lanjutan',
        'pembinaan_khusus'
    ]:
        flash('Tingkat pembinaan tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    if status not in [
        'dalam_pemantauan',
        'membaik',
        'selesai',
        'dirujuk_bk'
    ]:
        flash('Status pembinaan tidak valid.', 'danger')
        return redirect(url_for('riwayat_pembinaan.index'))

    if not judul or not kronologi or not tindakan:
        flash('Judul, kronologi, dan tindakan wajib diisi.', 'warning')
        return redirect(url_for('riwayat_pembinaan.index'))

    tanggal_pemantauan = None

    if tanggal_pemantauan_input:
        try:
            tanggal_pemantauan = date.fromisoformat(
                tanggal_pemantauan_input
            )
        except ValueError:
            flash('Tanggal pemantauan tidak valid.', 'danger')
            return redirect(url_for('riwayat_pembinaan.index'))

    if perlu_pemantauan and not tanggal_pemantauan:
        flash('Tanggal pemantauan wajib diisi.', 'warning')
        return redirect(url_for('riwayat_pembinaan.index'))

    pembinaan.siswa_id = siswa_id
    pembinaan.kelas_id = kelas_id

    pembinaan.tanggal_kejadian = tanggal_kejadian
    pembinaan.kategori = kategori
    pembinaan.tingkat_pembinaan = tingkat

    pembinaan.judul = judul
    pembinaan.kronologi = kronologi
    pembinaan.tindakan_pembinaan = tindakan
    pembinaan.hasil_pembinaan = hasil or None

    pembinaan.perlu_pemantauan = perlu_pemantauan
    pembinaan.tanggal_pemantauan = (
        tanggal_pemantauan if perlu_pemantauan else None
    )

    pembinaan.status = status
    pembinaan.komunikasi_orang_tua = komunikasi_orang_tua
    pembinaan.catatan_orang_tua = catatan_orang_tua or None

    try:
        db.session.commit()
        flash('Riwayat pembinaan berhasil diperbarui.', 'success')

    except Exception:
        db.session.rollback()
        flash('Terjadi kesalahan saat memperbarui pembinaan.', 'danger')

    return redirect(url_for('riwayat_pembinaan.index'))


# ==========================================================
# HAPUS RIWAYAT PEMBINAAN
# ==========================================================

@riwayat_pembinaan_bp.route(
    '/riwayat-pembinaan/<int:pembinaan_id>/hapus',
    methods=['POST']
)
def hapus(pembinaan_id):

    context, error = get_wali_context()

    if error:
        return error

    pembinaan = ambil_pembinaan_milik_guru(
        pembinaan_id,
        context
    )

    try:
        db.session.delete(pembinaan)
        db.session.commit()

        flash('Riwayat pembinaan berhasil dihapus.', 'success')

    except Exception:
        db.session.rollback()
        flash('Terjadi kesalahan saat menghapus pembinaan.', 'danger')

    return redirect(url_for('riwayat_pembinaan.index'))
