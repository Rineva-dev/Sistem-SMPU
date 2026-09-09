from flask import Blueprint, render_template, session, redirect, url_for, current_app, g  # Tambahkan g
from datetime import datetime
from sqlalchemy import select
from models import db, Guru, User, AgendaKegiatan  # ✅ Tambahkan AgendaKegiatan

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
        # Hitung Guru Aktif
        total_guru = db.session.execute(
            select(db.func.count()).where(
                Guru.status == 'Aktif',
                Guru.jabatan.in_(['Guru', 'Kepala Sekolah'])
            )
        ).scalar_one()

        # Hitung Staf / TU Aktif
        total_staf = db.session.execute(
            select(db.func.count()).where(
                Guru.status == 'Aktif',
                Guru.jabatan.in_(['Staf TU', 'Tata Usaha', 'Staf Administrasi'])
            )
        ).scalar_one()

        # ✅ AMBIL DATA AGENDA DARI DATABASE
        sekarang = datetime.now()
        daftar_agenda_db = AgendaKegiatan.query\
            .filter(AgendaKegiatan.tanggal_mulai >= sekarang)\
            .order_by(AgendaKegiatan.tanggal_mulai.asc())\
            .limit(5)\
            .all()

        # ✅ Format data agar sesuai dengan tampilan di dashboard
        daftar_agenda = []
        for a in daftar_agenda_db:
            # Tentukan status otomatis sama seperti di agenda.py
            if a.status != "Dibatalkan":
                if a.tanggal_mulai > sekarang:
                    status = "Terjadwal"
                elif a.tanggal_selesai and a.tanggal_selesai < sekarang:
                    status = "Selesai"
                else:
                    status = "Berlangsung"
            else:
                status = "Dibatalkan"

            daftar_agenda.append({
                "id": a.id,
                "tanggal": a.tanggal_mulai,          # Tanggal mulai
                "waktu_mulai": a.tanggal_mulai.strftime('%H:%M'),
                "waktu_selesai": a.tanggal_selesai.strftime('%H:%M') if a.tanggal_selesai else "-",
                "nama_kegiatan": a.judul,            # Gunakan judul sebagai nama kegiatan
                "tempat": a.lokasi or "Belum ditentukan",
                "status": status
            })

    # Data sementara
    total_siswa = 456
    rata_kehadiran = 94.2

    # Data grafik
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

    user = {
        'nama': session.get('user_name', 'Kepala Sekolah'),
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