from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, User, Guru

absensi_bp = Blueprint('absensi', __name__)


@absensi_bp.route('/')
def absensi_root():
    return redirect(url_for('absensi.login_absensi'))

@absensi_bp.route('/login')
def absensi_login_alias():
    return redirect(url_for('absensi.login_absensi'))

@absensi_bp.route('/login-absensi', methods=['GET', 'POST'])
def login_absensi():
    # ✅ BERSIHKAN SEMUA PESAN FLASH LAMA DULU
    session.pop('_flashes', None)

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
            # Hapus sesi absensi yang tidak valid
            session.clear()
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

        # Simpan isi form agar TIDAK HILANG
        session['last_username'] = username

        if not user:
            flash('Username tidak terdaftar.', 'absensi_danger')
            session['error_username'] = True       # ✅ Tandai username salah
            session['error_password'] = False
        elif not user.aktif:
            flash('Akun ini sudah dinonaktifkan.', 'absensi_danger')
            session['error_username'] = True       # ✅ Tandai username salah
            session['error_password'] = False
        elif not check_password_hash(user.password_hash, password):
            flash('Kata sandi salah.', 'absensi_danger')
            session['error_username'] = False      # ✅ Username benar
            session['error_password'] = True       # ✅ Tandai sandi salah
        elif not user.guru:
            flash('Akun ini belum terhubung ke data Guru.', 'absensi_danger')
            session['error_username'] = True
            session['error_password'] = False
        else:
            # ✅ HAPUS SESI ABSENSI LAMA → CUKUP CLEAR SAJA
            session.clear()
            # BUAT SESI ABSENSI BARU
            session['absensi_logged_in'] = True
            session['absensi_sistem_mode'] = 'absensi'
            session['absensi_user_id'] = user.id
            session['absensi_guru_id'] = user.guru.id
            session['absensi_user_name'] = user.guru.nama
            session['absensi_halaman'] = 'absensi'

            session['user_id'] = user.id
            session['user_name'] = user.guru.nama
            session['jabatan'] = user.guru.jabatan or 'Guru'
            session['user_initials'] = ''.join(
                [nama[0].upper() for nama in user.guru.nama.split()[:2]]
            )
            # Ambil kontak dari Guru, BUKAN dari User
            session['email'] = getattr(user.guru, 'email', None)
            session['no_hp'] = getattr(user.guru, 'no_hp', None) or getattr(user.guru, 'telepon', None)
            session['halaman_aktif'] = 'absensi'

            flash(
                f'Selamat datang, {user.guru.nama}',
                'absensi_success'
            )
            return redirect(url_for('absensi_guru.dashboard'))
    else:
        # ✅ Saat BUKA HALAMAN / RELOAD → HAPUS ISI & TANDA SALAH
        session.pop('last_username', None)
        session.pop('error_username', None)
        session.pop('error_password', None)

    # ==========================================================
    # TAMPILKAN HALAMAN LOGIN
    # ==========================================================
    return render_template('login_absensi.html')

# ==============================================================
# LOGOUT SISTEM ABSENSI
# ==============================================================
@absensi_bp.route('/logout-absensi')
def logout_absensi():

    hapus_kunci = [
        'absensi_logged_in', 'absensi_sistem_mode', 'absensi_user_id',
        'absensi_guru_id', 'absensi_user_name', 'absensi_halaman',
        'halaman_aktif', 'user_id', 'user_name', 'jabatan', 'user_initials',
        'email', 'no_hp'
    ]
    for kunci in hapus_kunci:
        session.pop(kunci, None)
    return redirect(url_for('absensi.login_absensi'))