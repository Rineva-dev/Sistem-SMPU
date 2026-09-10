from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, User

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
@login_bp.route('/login')
def halaman_login():
    if (
        session.get('logged_in') is True and
        session.get('sistem_mode') == 'sekolah' and
        session.get('user_id')
    ):
        if session.get('role') == "Admin":
            return redirect(url_for('dev.index'))
        elif session.get('role') == "Guru":
            return redirect(url_for('dashboard_guru.halaman_dashboard_guru'))
        else:
            return redirect(url_for('dashboard.index'))
    return render_template('login.html')

@login_bp.route('/proses-login', methods=['POST'])
def proses_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # =========================================================
    # LOGIN ADMIN DEV
    # =========================================================
    if username == "adm1n" and password == "dev123":

        session.clear()

        session['logged_in'] = True
        session['sistem_mode'] = 'sekolah'
        session['user_id'] = 1
        session['user_name'] = "Admin Dev"
        session['role'] = "Admin"
        session['user_role'] = "Admin"
        session['jabatan'] = "Admin"
        session['tugas_tambahan'] = "Admin Sistem"
        session['daftar_tugas'] = ["Admin Sistem"]
        session['user_initials'] = "AD"
        session['halaman_aktif'] = 'utama'
        flash('Login berhasil sebagai Admin Dev', 'success')
        return redirect(url_for('dev.index'))

    # =========================================================
    # LOGIN USER BIASA
    # =========================================================
    user = User.query.filter_by(username=username).first()
    if user and user.aktif and check_password_hash(
        user.password_hash,
        password
    ):
        # ✅ SESI SUDAH TERPISAH → CUKUP CLEAR SAJA
        session.clear()

        # SIMPAN SESI SEKOLAH
        session['logged_in'] = True
        session['sistem_mode'] = 'sekolah'
        session['user_id'] = user.id
        session['guru_id'] = user.guru.id if user.guru else 0
        session['user_name'] = user.guru.nama if user.guru else "Pengguna"
        session['role'] = user.jabatan
        session['user_role'] = user.jabatan
        session['jabatan'] = user.jabatan
        session['tugas_tambahan'] = user.tugas_tambahan or ""
        session['daftar_tugas'] = (
            user.tugas_tambahan.split(',')
            if user.tugas_tambahan
            else []
        )
        session['halaman_aktif'] = 'utama'

        # INISIAL NAMA
        if user.guru:
            nama_pisah = user.guru.nama.split()
            session['user_initials'] = (
                (nama_pisah[0][0] + nama_pisah[-1][0]).upper()
                if len(nama_pisah) >= 2
                else nama_pisah[0][0].upper()
            )
        else:
            session['user_initials'] = "US"

        flash('Login berhasil! Selamat datang.', 'success')
        if user.jabatan == "Guru":
            return redirect(url_for('dashboard_guru.halaman_dashboard_guru'))
        else:
            return redirect(url_for('dashboard.index'))

    flash('Username atau kata sandi salah!', 'danger')
    return redirect(url_for('login.halaman_login'))

# =========================================================
# LOGOUT SISTEM SEKOLAH
# =========================================================
@login_bp.route('/logout')
def logout():
    # ✅ HAPUS SESI SEKOLAH SAJA — TIDAK MENGGANGGU SESI ABSENSI
    session.clear()
    return redirect(url_for('login.halaman_login'))