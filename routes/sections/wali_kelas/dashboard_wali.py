
from flask import Blueprint, render_template, session, redirect, url_for
from sqlalchemy import func

from models import db, User, Guru, Kelas, TahunPelajaran, RiwayatKelas


bp = Blueprint('dashboard_wali', __name__)


def get_base_tahun(kode_tp):
    """Mengambil tahun pelajaran tanpa kode semester."""
    if not kode_tp:
        return None

    return kode_tp.split('-')[0].strip()


@bp.route('/')
def index():
    # =========================================
    # 1. VALIDASI LOGIN
    # =========================================
    if (
        not session.get('logged_in')
        or session.get('sistem_mode') != 'sekolah'
        or not session.get('user_id')
    ):
        return redirect(url_for('login.halaman_login'))

    # =========================================
    # 2. AMBIL DATA USER DAN GURU
    # =========================================
    user = db.session.get(User, session.get('user_id'))

    if not user:
        return redirect(url_for('login.halaman_login'))

    if not user.guru_id:
        return render_template(
            'sections/wali_kelas/dashboard.html',
            user=user,
            guru=None,
            tahun_pelajaran=None,
            daftar_kelas=[],
            total_kelas=0,
            total_siswa=0,
            pesan="Akun ini belum terhubung dengan data guru."
        )

    guru = db.session.get(Guru, user.guru_id)

    if not guru:
        return render_template(
            'sections/wali_kelas/dashboard.html',
            user=user,
            guru=None,
            tahun_pelajaran=None,
            daftar_kelas=[],
            total_kelas=0,
            total_siswa=0,
            pesan="Data guru untuk akun ini tidak ditemukan."
        )

    # =========================================
    # 3. AMBIL TAHUN PELAJARAN AKTIF
    # =========================================
    tahun_pelajaran = (
        TahunPelajaran.query
        .filter_by(aktif=True)
        .order_by(TahunPelajaran.id.desc())
        .first()
    )

    kode_tp = tahun_pelajaran.kode if tahun_pelajaran else None
    tahun_dasar = get_base_tahun(kode_tp)

    # =========================================
    # 4. AMBIL SEMUA KELAS WALI KELAS
    # =========================================
    query_kelas = Kelas.query.filter(
        Kelas.wali_kelas_id == guru.id
    )

    if tahun_dasar:
        query_kelas = query_kelas.filter(
            Kelas.tahun_pelajaran == tahun_dasar
        )

    daftar_kelas = (
        query_kelas
        .order_by(Kelas.jenjang.asc(), Kelas.nama_kelas.asc())
        .all()
    )

    # =========================================
    # 5. HITUNG SISWA BERDASARKAN RIWAYAT KELAS
    # =========================================
    total_siswa = 0

    for kelas in daftar_kelas:
        jumlah_siswa = 0

        if kode_tp:
            jumlah_siswa = (
                db.session.query(func.count(func.distinct(RiwayatKelas.siswa_id)))
                .filter(
                    RiwayatKelas.kelas_id == kelas.id,
                    RiwayatKelas.tahun_pelajaran == kode_tp
                )
                .scalar()
                or 0
            )

        kelas.jumlah_siswa_periode = jumlah_siswa
        total_siswa += jumlah_siswa

    # =========================================
    # 6. TAMPILKAN DASHBOARD
    # =========================================
    return render_template(
        'sections/wali_kelas/dashboard.html',
        active_page='dashboard_wali',
        halaman_aktif='wali_kelas',
        user=user,
        guru=guru,
        tahun_pelajaran=tahun_pelajaran,
        daftar_kelas=daftar_kelas,
        total_kelas=len(daftar_kelas),
        total_siswa=total_siswa,
        pesan=None
    )
