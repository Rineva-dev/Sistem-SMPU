from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime

dev_bp = Blueprint('dev', __name__)

@dev_bp.route('/dashboard')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ Cek akses, tapi TIDAK tampilkan pesan jika salah
    if session.get('role') != "Admin":
        # Hanya alihkan, TANPA flash
        return redirect(url_for('dashboard.index'))

    # Data untuk Admin saja
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }

    sekarang = datetime.now()
    today_date_long = sekarang.strftime('%A, %d %B %Y')  # Contoh: Thursday, 02 July 2026
    today_date = sekarang.strftime('%d %B %Y')  # Contoh: 02 Jul 2026

    context = {
        'active_page': 'dashboard_dev',
        'halaman_aktif': 'utama',
        'role': session.get('role', ''),
        'daftar_tugas': session.get('daftar_tugas', []),
        'user': user,
        'user_name': session.get('user_name', 'Admin Dev'),
        'today_date_long': today_date_long,
        'today_date': today_date,
        'total_pengguna': 38,
        'versi_sistem': '1.0.0',
        'ruang_penyimpanan': 28,
        'error_sistem': 0
    }

    return render_template('index.html', **context)

# Lakukan hal yang sama untuk SEMUA rute di dev_bp
@dev_bp.route('/pengaturan-umum')
def pengaturan_umum():
    if session.get('role') != "Admin":
        return redirect(url_for('dashboard.index'))
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }
    return render_template('dev/pengaturan_umum.html', active_page='pengaturan_umum', user=user)


@dev_bp.route('/atur-hak-akses')
def atur_hak_akses():
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }
    return render_template('dev/atur_hak_akses.html', active_page='atur_hak', user=user)

@dev_bp.route('/log-aktivitas')
def log_aktivitas():
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }
    return render_template('dev/log_aktivitas.html', active_page='log_aktivitas', user=user)

@dev_bp.route('/backup-data')
def backup_data():
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }
    return render_template('dev/backup_data.html', active_page='backup_data', user=user)

@dev_bp.route('/pengaturan-keamanan')
def pengaturan_keamanan():
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }
    return render_template('dev/pengaturan_keamanan.html', active_page='pengaturan_keamanan', user=user)

@dev_bp.route('/info-sistem')
def info_sistem():
    user = {
        'nama': session.get('user_name', 'Admin Dev'),
        'jabatan': session.get('role', 'Admin'),
        'tugas_tambahan': ", ".join(session.get('daftar_tugas', [])),
        'inisial': session.get('user_initials', 'AD')
    }
    return render_template('dev/info_sistem.html', active_page='info_sistem', user=user)