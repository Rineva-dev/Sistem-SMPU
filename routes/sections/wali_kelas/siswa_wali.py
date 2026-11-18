
from flask import (
    Blueprint, render_template, session,
    redirect, url_for, request
)

from models import (
    db, User, Guru, Kelas, TahunPelajaran,
    RiwayatKelas, Siswa
)


siswa_wali_bp = Blueprint(
    'siswa_wali',
    __name__,
    url_prefix='/wali-kelas'
)


def get_base_tahun(kode_tp):
    if not kode_tp:
        return None
    return kode_tp.split('-')[0].strip()


@siswa_wali_bp.route('/data-siswa')
def data_siswa():

    # ==============================
    # CEK LOGIN
    # ==============================
    if (
        not session.get('logged_in')
        or session.get('sistem_mode') != 'sekolah'
        or not session.get('user_id')
    ):
        return redirect(url_for('login.halaman_login'))

    user = db.session.get(User, session.get('user_id'))

    if not user or not user.guru_id:
        return redirect(url_for('dashboard_wali.index'))

    guru = db.session.get(Guru, user.guru_id)

    if not guru:
        return redirect(url_for('dashboard_wali.index'))

    # ==============================
    # TAHUN PELAJARAN AKTIF
    # ==============================
    tahun_pelajaran = (
        TahunPelajaran.query
        .filter_by(aktif=True)
        .order_by(TahunPelajaran.id.desc())
        .first()
    )

    if not tahun_pelajaran:
        return render_template(
            'sections/wali_kelas/data_siswa.html',
            active_page='data_siswa_wali',
            halaman_aktif='wali_kelas',
            user=user,
            guru=guru,
            tahun_pelajaran=None,
            daftar_kelas=[],
            daftar_siswa=[],
            kelas_terpilih=None,
            pesan="Belum ada tahun pelajaran aktif."
        )

    kode_tp = tahun_pelajaran.kode
    tahun_dasar = get_base_tahun(kode_tp)

    # ==============================
    # KELAS YANG DIAMPU GURU
    # ==============================
    daftar_kelas = (
        Kelas.query
        .filter(
            Kelas.wali_kelas_id == guru.id,
            Kelas.tahun_pelajaran == tahun_dasar
        )
        .order_by(Kelas.jenjang, Kelas.nama_kelas)
        .all()
    )

    if not daftar_kelas:
        return render_template(
            'sections/wali_kelas/data_siswa.html',
            active_page='data_siswa_wali',
            halaman_aktif='wali_kelas',
            user=user,
            guru=guru,
            tahun_pelajaran=tahun_pelajaran,
            daftar_kelas=[],
            daftar_siswa=[],
            kelas_terpilih=None,
            pesan="Anda belum ditugaskan sebagai Wali Kelas pada tahun pelajaran aktif."
        )

    # ==============================
    # VALIDASI AKSES KELAS
    # ==============================
    kelas_ids = [kelas.id for kelas in daftar_kelas]

    kelas_id = request.args.get('kelas_id', type=int)

    if kelas_id and kelas_id not in kelas_ids:
        return "Anda tidak memiliki akses ke kelas tersebut.", 403

    kelas_filter = [kelas_id] if kelas_id else kelas_ids

    # ==============================
    # AMBIL SISWA BERDASARKAN
    # RIWAYAT KELAS PERIODE AKTIF
    # ==============================
    daftar_siswa = (
        db.session.query(Siswa)
        .join(
            RiwayatKelas,
            RiwayatKelas.siswa_id == Siswa.id
        )
        .filter(
            RiwayatKelas.tahun_pelajaran == kode_tp,
            RiwayatKelas.kelas_id.in_(kelas_filter)
        )
        .order_by(Siswa.nama.asc())
        .all()
    )

    kelas_terpilih = next(
        (k for k in daftar_kelas if k.id == kelas_id),
        None
    )

    return render_template(
        'sections/wali_kelas/data_siswa.html',
        active_page='data_siswa_wali',
        halaman_aktif='wali_kelas',
        user=user,
        guru=guru,
        tahun_pelajaran=tahun_pelajaran,
        daftar_kelas=daftar_kelas,
        daftar_siswa=daftar_siswa,
        kelas_terpilih=kelas_terpilih,
        pesan=None
    )

