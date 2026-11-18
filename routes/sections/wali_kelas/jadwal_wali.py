
from flask import (
    Blueprint, render_template, session,
    redirect, url_for, request
)

from models import (
    db, User, Guru, Kelas, TahunPelajaran,
    JadwalPelajaran
)


jadwal_wali_bp = Blueprint(
    'jadwal_wali',
    __name__,
    url_prefix='/wali-kelas'
)


def get_base_tahun(kode_tp):
    if not kode_tp:
        return None
    return kode_tp.split('-')[0].strip()


@jadwal_wali_bp.route('/jadwal-pelajaran')
def index():

    # ==============================
    # CEK LOGIN DAN WORKSPACE
    # ==============================
    if (
        not session.get('logged_in')
        or session.get('sistem_mode') != 'sekolah'
        or not session.get('user_id')
    ):
        return redirect(url_for('login.halaman_login'))

    if session.get('halaman_aktif') != 'wali_kelas':
        return redirect(url_for('dashboard.index'))

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

    hari_list = [
        'Senin',
        'Selasa',
        'Rabu',
        'Kamis',
        'Jumat',
        'Sabtu'
    ]

    if not tahun_pelajaran:
        return render_template(
            'sections/wali_kelas/jadwal_pelajaran.html',
            active_page='jadwal_wali',
            halaman_aktif='wali_kelas',
            user=user,
            guru=guru,
            tahun_pelajaran=None,
            daftar_kelas=[],
            kelas_terpilih=None,
            jadwal_per_hari={hari: [] for hari in hari_list},
            jumlah_jadwal=0,
            pesan="Belum ada tahun pelajaran aktif."
        )

    kode_tp = tahun_pelajaran.kode
    tahun_dasar = get_base_tahun(kode_tp)

    # ==============================
    # KELAS YANG DIAMPU
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
            'sections/wali_kelas/jadwal_pelajaran.html',
            active_page='jadwal_wali',
            halaman_aktif='wali_kelas',
            user=user,
            guru=guru,
            tahun_pelajaran=tahun_pelajaran,
            daftar_kelas=[],
            kelas_terpilih=None,
            jadwal_per_hari={hari: [] for hari in hari_list},
            jumlah_jadwal=0,
            pesan="Anda belum ditugaskan sebagai Wali Kelas pada tahun pelajaran aktif."
        )

    # ==============================
    # VALIDASI KELAS
    # ==============================
    kelas_ids = [kelas.id for kelas in daftar_kelas]

    kelas_id = request.args.get('kelas_id', type=int)

    if kelas_id and kelas_id not in kelas_ids:
        return "Anda tidak memiliki akses ke kelas tersebut.", 403

    kelas_filter = [kelas_id] if kelas_id else kelas_ids

    kelas_terpilih = next(
        (kelas for kelas in daftar_kelas if kelas.id == kelas_id),
        None
    )

    # ==============================
    # AMBIL JADWAL PELAJARAN
    # ==============================
    daftar_jadwal = (
        JadwalPelajaran.query
        .filter(
            JadwalPelajaran.kelas_id.in_(kelas_filter),
            JadwalPelajaran.tahun_pelajaran == kode_tp
        )
        .all()
    )
    # ==============================
    # KELOMPOKKAN BERDASARKAN HARI
    # ==============================
    urutan_hari = {
        hari: index
        for index, hari in enumerate(hari_list)
    }

    jadwal_per_hari = {
        hari: []
        for hari in hari_list
    }

    for jadwal in daftar_jadwal:
        hari = (jadwal.hari or '').strip().capitalize()

        if hari not in jadwal_per_hari:
            continue

        jadwal_per_hari[hari].append(jadwal)

    # Urutkan berdasarkan jam mulai
    for hari in hari_list:
        jadwal_per_hari[hari].sort(
            key=lambda item: str(item.jam_mulai or '')
        )

    return render_template(
        'sections/wali_kelas/jadwal_pelajaran.html',
        active_page='jadwal_wali',
        halaman_aktif='wali_kelas',
        user=user,
        guru=guru,
        tahun_pelajaran=tahun_pelajaran,
        daftar_kelas=daftar_kelas,
        kelas_terpilih=kelas_terpilih,
        jadwal_per_hari=jadwal_per_hari,
        jumlah_jadwal=len(daftar_jadwal),
        pesan=None
    )
