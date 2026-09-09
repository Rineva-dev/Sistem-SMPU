from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, User, Guru

absensi_bp = Blueprint('absensi', __name__)


@absensi_bp.route('/login-absensi', methods=['GET', 'POST'])
def login_absensi():

    # ==========================================================
    # CEK APAKAH SUDAH LOGIN KE SISTEM ABSENSI
    # ==========================================================
    if (
        session.get('absensi_logged_in') and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):

        user = User.query.get(session.get('absensi_user_id'))

        if user and user.guru:
            return redirect(url_for('absensi_guru.dashboard'))

        else:
            # Hapus hanya sesi absensi
            for key in list(session.keys()):
                if key.startswith('absensi_'):
                    session.pop(key, None)

            flash(
                'Akun ini tidak terdaftar sebagai Guru.',
                'absensi_danger'
            )

    # ==========================================================
    # PROSES LOGIN
    # ==========================================================
    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if not user:

            flash(
                'Username tidak terdaftar.',
                'absensi_danger'
            )

        elif not user.aktif:

            flash(
                'Akun ini sudah dinonaktifkan.',
                'absensi_danger'
            )

        elif not check_password_hash(user.password_hash, password):

            flash(
                'Kata sandi salah.',
                'absensi_danger'
            )

        elif not user.guru:

            flash(
                'Akun ini belum terhubung ke data Guru.',
                'absensi_danger'
            )

        else:

            # ==================================================
            # HAPUS SESSION ABSENSI LAMA SAJA
            # ==================================================
            for key in list(session.keys()):
                if key.startswith('absensi_'):
                    session.pop(key, None)

            # ==================================================
            # BUAT SESSION ABSENSI BARU
            # ==================================================
            session['absensi_logged_in'] = True
            session['absensi_sistem_mode'] = 'absensi'
            session['absensi_user_id'] = user.id
            session['absensi_guru_id'] = user.guru.id
            session['absensi_user_name'] = user.guru.nama
            session['absensi_halaman'] = 'absensi'

            # ==================================================
            # PESAN LOGIN
            # ==================================================
            flash(
                f'Selamat datang, {user.guru.nama}',
                'absensi_success'
            )

            return redirect(
                url_for('absensi_guru.dashboard')
            )

    # ==========================================================
    # TAMPILKAN HALAMAN LOGIN
    # ==========================================================
    return render_template('login_absensi.html')


# ==============================================================
# LOGOUT SISTEM ABSENSI
# ==============================================================
@absensi_bp.route('/logout-absensi')
def logout_absensi():

    for key in list(session.keys()):
        if key.startswith('absensi_'):
            session.pop(key, None)

    return redirect(
        url_for('absensi.login_absensi')
    )