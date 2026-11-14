from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app
)
from functools import wraps

from models import (
    db,
    User,
    JurnalMengajar,
    RiwayatKelas,
    Siswa,
    AbsensiJurnalMengajar,
    MataPelajaran,
    Kelas
)


absensi_siswa_bp = Blueprint(
    'absensi_siswa',
    __name__,
    template_folder='../../templates',
    url_prefix='/absensi-siswa'
)


# =========================================================
# AKSES KHUSUS GURU
# =========================================================
def guru_wajib(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login.halaman_login'))

        if (
            session.get('jabatan') != 'Guru'
            and session.get('role') != 'Guru'
        ):
            flash('Halaman ini khusus guru.', 'danger')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)

    return decorator


# =========================================================
# HELPER: VALIDASI JURNAL MILIK GURU LOGIN
# =========================================================
def ambil_jurnal_guru(jurnal_id):
    user_id = session.get('user_id')
    user_db = User.query.get(user_id) if user_id else None
    guru_data = user_db.guru if user_db else None

    if not guru_data:
        return None, None

    jurnal = JurnalMengajar.query.filter_by(
        id=jurnal_id,
        guru_id=guru_data.id
    ).first()

    return guru_data, jurnal


# =========================================================
# HELPER: DAFTAR SISWA SESUAI KELAS DAN TAHUN JURNAL
# =========================================================
def ambil_daftar_siswa(jurnal):
    riwayat_list = RiwayatKelas.query.filter_by(
        kelas_id=jurnal.kelas_id,
        tahun_pelajaran=jurnal.tahun_pelajaran
    ).join(
        Siswa,
        RiwayatKelas.siswa_id == Siswa.id
    ).order_by(
        Siswa.nama.asc()
    ).all()

    return [
        riwayat.siswa
        for riwayat in riwayat_list
        if riwayat.siswa
    ]


# =========================================================
# HALAMAN ABSENSI SISWA
# =========================================================
@absensi_siswa_bp.route('/<int:jurnal_id>')
@guru_wajib
def halaman_absensi(jurnal_id):

    guru_data, jurnal = ambil_jurnal_guru(jurnal_id)

    if not guru_data:
        flash('Data guru tidak ditemukan.', 'danger')
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    if not jurnal:
        flash('Jurnal tidak ditemukan atau bukan milik Anda.', 'danger')
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    daftar_siswa = ambil_daftar_siswa(jurnal)

    absensi_list = AbsensiJurnalMengajar.query.filter_by(
        jurnal_id=jurnal.id
    ).all()

    absensi_map = {
        item.siswa_id: item
        for item in absensi_list
    }

    data_siswa = []

    for siswa in daftar_siswa:
        absensi = absensi_map.get(siswa.id)

        data_siswa.append({
            'id': siswa.id,
            'nis': siswa.nis,
            'nama': siswa.nama,
            'jenis_kelamin': siswa.jenis_kelamin,
            'status_absensi': absensi.status if absensi else None,
            'keterangan': absensi.keterangan if absensi else ''
        })

    user = {
        'nama': session.get('user_name', 'Guru'),
        'gelar_depan': guru_data.gelar_depan,
        'gelar_belakang': guru_data.gelar_belakang,
        'jabatan': session.get('jabatan', session.get('role', '')),
        'tugas_tambahan': session.get('daftar_tugas', []),
        'inisial': session.get('user_initials', 'G')
    }

    jumlah_status = {
        'hadir': sum(1 for s in data_siswa if s['status_absensi'] == 'hadir'),
        'izin': sum(1 for s in data_siswa if s['status_absensi'] == 'izin'),
        'sakit': sum(1 for s in data_siswa if s['status_absensi'] == 'sakit'),
        'alpha': sum(1 for s in data_siswa if s['status_absensi'] == 'alpha')
    }

    return render_template(
        'sections/guru/absensi_siswa.html',
        user=user,
        halaman_aktif='utama',
        active_page='jurnal_mengajar',
        jurnal=jurnal,
        mapel=MataPelajaran.query.get(jurnal.mata_pelajaran_id),
        kelas=Kelas.query.get(jurnal.kelas_id),
        daftar_siswa=data_siswa,
        total_siswa=len(data_siswa),
        total_absen=len(absensi_list),
        jumlah_status=jumlah_status,
        tahun_ajaran=jurnal.tahun_pelajaran
    )


# =========================================================
# SIMPAN / PERBARUI ABSENSI SISWA
# =========================================================
@absensi_siswa_bp.route('/<int:jurnal_id>/simpan', methods=['POST'])
@guru_wajib
def simpan_absensi(jurnal_id):

    guru_data, jurnal = ambil_jurnal_guru(jurnal_id)

    if not guru_data:
        flash('Data guru tidak ditemukan.', 'danger')
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    if not jurnal:
        flash('Jurnal tidak ditemukan atau bukan milik Anda.', 'danger')
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    daftar_siswa = ambil_daftar_siswa(jurnal)
    siswa_valid = {siswa.id for siswa in daftar_siswa}

    status_valid = {'hadir', 'izin', 'sakit', 'alpha'}

    try:
        if not daftar_siswa:
            flash(
                'Belum ada siswa yang terdaftar pada kelas ini '
                'di tahun pelajaran jurnal tersebut.',
                'warning'
            )
            return redirect(
                url_for('absensi_siswa.halaman_absensi', jurnal_id=jurnal.id)
            )

        for siswa_id in siswa_valid:
            status = (
                request.form.get(f'status_{siswa_id}') or ''
            ).strip().lower()

            keterangan = (
                request.form.get(f'keterangan_{siswa_id}') or ''
            ).strip()

            if status not in status_valid:
                raise ValueError(
                    f'Status absensi siswa ID {siswa_id} tidak valid.'
                )

            absensi = AbsensiJurnalMengajar.query.filter_by(
                jurnal_id=jurnal.id,
                siswa_id=siswa_id
            ).first()

            if absensi:
                absensi.status = status
                absensi.keterangan = keterangan or None
            else:
                db.session.add(
                    AbsensiJurnalMengajar(
                        jurnal_id=jurnal.id,
                        siswa_id=siswa_id,
                        status=status,
                        keterangan=keterangan or None
                    )
                )

        db.session.commit()

        flash(
            f'Absensi {len(siswa_valid)} siswa berhasil disimpan.',
            'success'
        )

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            'Gagal menyimpan absensi untuk jurnal ID %s',
            jurnal.id
        )

        flash(
            'Gagal menyimpan absensi. Silakan periksa kembali.',
            'danger'
        )

    return redirect(
        url_for(
            'absensi_siswa.halaman_absensi',
            jurnal_id=jurnal.id
        )
    )