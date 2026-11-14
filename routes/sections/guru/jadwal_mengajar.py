from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import datetime
from models import (
    db,
    User,
    Guru,
    JadwalPelajaran,
    MataPelajaran,
    Kelas,
    TahunPelajaran
)

jadwal_mengajar_bp = Blueprint(
    'jadwal_mengajar',
    __name__,
    url_prefix='/jadwal-mengajar'
)

HARI_URUT = {
    'Senin': 1,
    'Selasa': 2,
    'Rabu': 3,
    'Kamis': 4,
    'Jumat': 5,
    'Sabtu': 6,
    'Minggu': 7
}


def format_jam(nilai):
    """Mengubah objek time atau string menjadi format HH:MM."""
    if not nilai:
        return ''

    if hasattr(nilai, 'strftime'):
        return nilai.strftime('%H:%M')

    return str(nilai)[:5]


@jadwal_mengajar_bp.route('/')
def halaman_jadwal_mengajar():

    # ==========================================
    # VALIDASI LOGIN GURU
    # ==========================================
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if session.get('role') != 'Guru' and session.get('jabatan') != 'Guru':
        flash('Halaman ini khusus untuk guru.', 'danger')
        return redirect(url_for('dashboard.index'))

    user_db = User.query.get(session.get('user_id'))
    guru_data = user_db.guru if user_db else None

    if not guru_data:
        flash('Data guru tidak ditemukan.', 'warning')
        return redirect(url_for('dashboard_guru.halaman_dashboard_guru'))

    # ==========================================
    # TAHUN PELAJARAN AKTIF
    # ==========================================
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()

    kode_tahun = (
        session.get('tahun_pelajaran')
        or (tahun_aktif.kode if tahun_aktif else None)
    )

    nama_tahun = (
        tahun_aktif.nama
        if tahun_aktif and tahun_aktif.kode == kode_tahun
        else kode_tahun or 'Belum tersedia'
    )

    semester = (
        tahun_aktif.semester
        if tahun_aktif and tahun_aktif.kode == kode_tahun
        else '-'
    )

    # ==========================================
    # AMBIL JADWAL KHUSUS MILIK GURU
    # ==========================================
    jadwal_query = JadwalPelajaran.query.filter_by(
        guru_id=guru_data.id,
        tahun_pelajaran=kode_tahun
    ) if kode_tahun else JadwalPelajaran.query.filter(
        JadwalPelajaran.guru_id == guru_data.id,
        JadwalPelajaran.tahun_pelajaran == None
    )

    jadwal_database = jadwal_query.order_by(
        JadwalPelajaran.jam_mulai.asc()
    ).all()

    daftar_hari = [
        'Senin',
        'Selasa',
        'Rabu',
        'Kamis',
        'Jumat'
    ]

    jadwal_per_hari = {hari: [] for hari in daftar_hari}
    semua_jadwal = []

    for item in jadwal_database:

        hari = (item.hari or '').strip().title()

        # Halaman ini menampilkan jadwal sekolah Senin-Jumat.
        # Hari lain tetap dimasukkan ke daftar jika ada.
        if hari not in jadwal_per_hari:
            jadwal_per_hari[hari] = []

        mapel = (
            MataPelajaran.query.get(item.mata_pelajaran_id)
            if item.mata_pelajaran_id
            else None
        )

        kelas = (
            Kelas.query.get(item.kelas_id)
            if item.kelas_id
            else None
        )

        jam_mulai = format_jam(item.jam_mulai)
        jam_selesai = format_jam(item.jam_selesai)

        jenis_khusus = (
            str(item.jenis_khusus).strip()
            if item.jenis_khusus
            else ''
        )

        nama_mapel = (
            mapel.nama_pelajaran
            if mapel
            else jenis_khusus or 'Kegiatan Khusus'
        )

        data_jadwal = {
            'id': item.id,
            'hari': hari,
            'jam_mulai': jam_mulai,
            'jam_selesai': jam_selesai,
            'nama_mapel': nama_mapel,
            'nama_kelas': kelas.nama_kelas if kelas else '-',
            'jenis_khusus': jenis_khusus,
            'khusus': bool(jenis_khusus),
            'kode_mapel': mapel.kode if mapel else '',
            'kelas_id': item.kelas_id
        }

        jadwal_per_hari[hari].append(data_jadwal)
        semua_jadwal.append(data_jadwal)

    # Urutkan jadwal di setiap hari berdasarkan jam mulai.
    for hari in jadwal_per_hari:
        jadwal_per_hari[hari].sort(
            key=lambda x: x['jam_mulai'] or '99:99'
        )

    semua_jadwal.sort(
        key=lambda x: (
            HARI_URUT.get(x['hari'], 99),
            x['jam_mulai'] or '99:99'
        )
    )

    # ==========================================
    # HARI DAN WAKTU SEKARANG
    # ==========================================
    sekarang = datetime.now()

    nama_hari_sekarang = [
        'Senin', 'Selasa', 'Rabu',
        'Kamis', 'Jumat', 'Sabtu', 'Minggu'
    ][sekarang.weekday()]

    jadwal_hari_ini = jadwal_per_hari.get(
        nama_hari_sekarang, []
    )

    # ==========================================
    # RINGKASAN JADWAL
    # ==========================================
    jumlah_jam = 0

    for jadwal in semua_jadwal:
        try:
            mulai = datetime.strptime(
                jadwal['jam_mulai'], '%H:%M'
            )
            selesai = datetime.strptime(
                jadwal['jam_selesai'], '%H:%M'
            )

            durasi = (
                selesai.hour * 60 + selesai.minute
                - mulai.hour * 60 - mulai.minute
            )

            if durasi > 0:
                jumlah_jam += durasi / 60

        except (ValueError, TypeError):
            pass

    jumlah_kelas = len({
        j['kelas_id']
        for j in semua_jadwal
        if j['kelas_id'] is not None
    })

    user = {
        'nama': session.get('user_name', 'Guru'),
        'jabatan': session.get('jabatan', 'Guru'),
        'inisial': session.get('user_initials', 'G'),
        'tugas_tambahan': session.get('daftar_tugas', []),
        'gelar_depan': guru_data.gelar_depan,
        'gelar_belakang': guru_data.gelar_belakang
    }

    context = {
        'active_page': 'jadwal_mengajar',
        'halaman_aktif': 'utama',
        'role': session.get('role'),
        'user': user,

        'tahun_ajaran': kode_tahun,
        'nama_tahun': nama_tahun,
        'semester': semester,

        'daftar_hari': daftar_hari,
        'jadwal_per_hari': jadwal_per_hari,
        'semua_jadwal': semua_jadwal,
        'jadwal_hari_ini': jadwal_hari_ini,

        'nama_hari_sekarang': nama_hari_sekarang,
        'tanggal_sekarang': sekarang.strftime('%d %B %Y'),
        'jumlah_jadwal': len(semua_jadwal),
        'jumlah_kelas': jumlah_kelas,
        'jumlah_jam': round(jumlah_jam, 1)
    }

    return render_template(
        'sections/guru/jadwal_mengajar.html',
        **context
    )