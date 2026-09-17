from flask import Blueprint, render_template, session, redirect, url_for, current_app, g  # Tambahkan g
from datetime import datetime
from sqlalchemy import select
from models import db, Guru, User, AgendaKegiatan, Siswa, RataKehadiranGuru

# Buat Blueprint
dashboard_kepsek_bp = Blueprint(
    'dashboard_kepsek',
    __name__,
    template_folder='../../templates',
    url_prefix='/dashboard-kepsek'
)

@dashboard_kepsek_bp.route('/')
def index():
    # Cek login
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # Pastikan hanya Kepala Sekolah yang bisa akses
    if session.get('role') != 'Kepala Sekolah':
        return redirect(url_for('dashboard.index'))

    # --------------------------
    # Data Khusus Kepala Sekolah
    # --------------------------
    with current_app.app_context():
        total_guru = db.session.execute(
            select(db.func.count()).where(
                Guru.status == 'Aktif',
                Guru.jabatan.in_(['Guru', 'Kepala Sekolah'])
            )
        ).scalar_one()

        total_staf = db.session.execute(
            select(db.func.count()).where(
                Guru.status == 'Aktif',
                Guru.jabatan.in_(['Staf TU', 'Tata Usaha', 'Staf Administrasi'])
            )
        ).scalar_one()

        sekarang = datetime.now()
        hari_ini = sekarang.date()

        daftar_agenda_db = AgendaKegiatan.query\
            .order_by(AgendaKegiatan.tanggal_mulai.asc())\
            .all()
        
        daftar_agenda = []
        for a in daftar_agenda_db:
            tgl_mulai = a.tanggal_mulai.date()
            tgl_selesai = a.tanggal_selesai.date() if a.tanggal_selesai else tgl_mulai

            if tgl_selesai < hari_ini:
                continue

            if tgl_mulai < hari_ini and tgl_selesai >= hari_ini:

                pass
            elif tgl_mulai > hari_ini:

                pass
            elif tgl_mulai == hari_ini:

                pass
            else:

                continue

            if a.status == "Dibatalkan":
                status = "Dibatalkan"
            else:
                if a.tanggal_mulai > sekarang:
                    status = "Terjadwal"
                elif a.tanggal_selesai and a.tanggal_selesai < sekarang:

                    status = "Selesai"
                else:
                    status = "Berlangsung"
            
            daftar_agenda.append({
                "id": a.id,
                "tanggal": a.tanggal_mulai,
                "waktu_mulai": a.tanggal_mulai.strftime('%H:%M'),
                "waktu_selesai": a.tanggal_selesai.strftime('%H:%M') if a.tanggal_selesai else "-",
                "nama_kegiatan": a.judul,
                "tempat": a.lokasi or "Belum ditentukan",
                "status": status
            })

        total_siswa = db.session.execute(
            select(db.func.count()).where(
                Siswa.status == 'Aktif'
            )
        ).scalar_one()

        tahun_pelajaran_aktif = g.tahun_pelajaran if hasattr(g, 'tahun_pelajaran') else '2025/2026'

        sekarang = datetime.now()
        thn = sekarang.year
        bln = sekarang.month

        daftar_rata = RataKehadiranGuru.hitung_semua_periode(tahun_pelajaran_aktif, bln, thn)

        if daftar_rata:
            total_persen = sum(float(r.persen_kehadiran) for r in daftar_rata)
            rata_kehadiran = round(total_persen / len(daftar_rata), 1)
        else:
            rata_kehadiran = 0.0

    chart_data = {
        'bulan': ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'],
        'kehadiran': [92.1, 93.5, 94.2, 93.8, 95.0, 94.8],
        'nilai': [75.2, 76.4, 77.0, 77.8, 78.2, 78.7]
    }

    # --------------------------
    # Data Pendukung Lainnya
    # --------------------------
    user_role = session.get('role', '')
    daftar_tugas = session.get('daftar_tugas', [])

    user_id = session.get('user_id')
    user_db = User.query.get(user_id) if user_id else None
    guru_data = user_db.guru if user_db else None

    user = {
        'nama': session.get('user_name', 'Kepala Sekolah'),
        'gelar_depan': guru_data.gelar_depan if guru_data else None,
        'gelar_belakang': guru_data.gelar_belakang if guru_data else None,
        'jabatan': user_role,
        'tugas_tambahan': ", ".join(daftar_tugas) if isinstance(daftar_tugas, list) else daftar_tugas,
        'inisial': session.get('user_initials', 'KS')
    }

    user_name = session.get('user_name', 'Kepala Sekolah')
    today_date = datetime.now().strftime('%d %B %Y')
    today_date_long = datetime.now().strftime('%A, %d %B %Y')
    tahun_ajaran = g.tahun_pelajaran if hasattr(g, 'tahun_pelajaran') else '2025/2026'
    semester = 'Genap'

    # --------------------------
    # Kumpulkan Semua Variabel
    # --------------------------
    context = {
        'active_page': 'dashboard',
        'halaman_aktif': 'utama',
        'role': 'Kepala Sekolah',
        'user': user,
        'user_name': user_name,
        'user_role': user_role,
        'daftar_tugas': daftar_tugas,
        'user_initials': session.get('user_initials', 'KS'),
        'today_date': today_date,
        'today_date_long': today_date_long,
        'tahun_ajaran': tahun_ajaran,
        'semester': semester,
        'sub_page': None,

        # Data kartu & grafik & agenda
        'total_siswa': total_siswa,
        'total_guru': total_guru,
        'total_staf': total_staf,
        'rata_kehadiran': rata_kehadiran,
        'daftar_agenda': daftar_agenda,
        'chart_data': chart_data
    }

    return render_template('index.html', **context)