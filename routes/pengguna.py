from flask import Blueprint, render_template, request, redirect, url_for, session, flash
# Nanti gunakan model database, contoh:
# from models import Pengguna
# from werkzeug.security import generate_password_hash, check_password_hash

pengguna_bp = Blueprint('pengguna', __name__)

# Cek hak akses sebelum masuk
def cek_hak_akses():
    jabatan = session.get('jabatan', '')
    tugas = session.get('tugas_tambahan', '')
    daftar_tugas = [t.strip() for t in tugas.split(',')] if tugas else []

    if jabatan != "Admin" and "Admin Sistem" not in daftar_tugas:
        flash("Anda tidak memiliki hak akses untuk halaman ini", "danger")
        return False
    return True

# Halaman daftar pengguna
@pengguna_bp.route('/pengguna')
def daftar_pengguna():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    
    if not cek_hak_akses():
        return redirect(url_for('dashboard.index'))

    # --- Nanti ganti dengan ambil dari database ---
    # daftar = Pengguna.query.all()
    daftar = []  # Sementara kosong

    return render_template(
        'pengguna/daftar.html',
        daftar_pengguna=daftar,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        tugas_tambahan=session.get('tugas_tambahan')
    )

# Halaman tambah pengguna
@pengguna_bp.route('/pengguna/tambah', methods=['GET', 'POST'])
def tambah_pengguna():
    if not session.get('logged_in') or not cek_hak_akses():
        return redirect(url_for('login.halaman_login'))

    if request.method == 'POST':
        nip = request.form.get('nip', '').strip()
        nama = request.form.get('nama', '').strip()
        jabatan = request.form.get('jabatan', '').strip()
        tugas_tambahan = request.form.get('tugas_tambahan', '').strip()
        sandi = request.form.get('sandi', '').strip()

        # Aturan: Tidak boleh membuat jabatan Admin lewat menu
        if jabatan == "Admin":
            flash("Jabatan Admin hanya dapat dibuat secara khusus oleh pengembang sistem", "danger")
            return redirect(url_for('pengguna.tambah_pengguna'))

        # Simpan ke database nanti
        # pengguna_baru = Pengguna(
        #     nip=nip,
        #     nama=nama,
        #     jabatan=jabatan,
        #     tugas_tambahan=tugas_tambahan,
        #     sandi=generate_password_hash(sandi)
        # )
        # db.session.add(pengguna_baru)
        # db.session.commit()

        flash("Pengguna berhasil ditambahkan", "success")
        return redirect(url_for('pengguna.daftar_pengguna'))

    return render_template(
        'layout.html',
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        tugas_tambahan=session.get('tugas_tambahan')
    )