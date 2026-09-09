from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime
from werkzeug.security import generate_password_hash
import re
from models import db, Guru, User

# Buat Blueprint
data_guru_bp = Blueprint('data_guru', __name__, url_prefix='/guru')

# ==========================================
# KONFIGURASI UTAMA
# ==========================================
# Daftar tugas tambahan (TANPA "Mengajar", karena otomatis untuk Guru)
DAFTAR_TUGAS = {
    "Guru": [
        "Waka Kurikulum", "Waka Kesiswaan", "Waka Sarana dan Prasarana",
        "Pembina Ekstrakurikuler", "Bendahara", "Admin Sistem"
    ],
    "Kepala Sekolah": [
        "Pembina Ekstrakurikuler", "Waka Kurikulum", "Waka Kesiswaan",
        "Bendahara", "Admin Sistem"
    ],
    "Tata Usaha": [
        "Waka Kurikulum", "Waka Kesiswaan",
        "Waka Sarana dan Prasarana",  "Bendahara", "Pengelola Kepegawaian",
        "Admin Sistem"
    ]
}

# Daftar jabatan yang diizinkan dibuat lewat menu
JABATAN_IZIN = ["Guru", "Kepala Sekolah", "Tata Usaha"]

# ==========================================
# FUNGSI BANTUAN & HAK AKSES (SESUAI HALAMAN AKTIF)
# ==========================================
def dapatkan_daftar_tugas():
    """Ambil daftar tugas dari sesi"""
    tugas = session.get('tugas_tambahan', '').strip()
    return [t.strip() for t in tugas.split(',')] if tugas else []

def bisa_lihat():
    """Bisa melihat data"""
    jabatan = session.get('jabatan', '').strip()
    halaman_aktif = session.get('halaman_aktif', 'utama')
    return (
        jabatan == "Admin"
        or jabatan in ["Kepala Sekolah", "Tata Usaha", "TU"]
        or halaman_aktif == "admin_sistem"
    )

def bisa_kelola():
    """Bisa tambah & ubah data"""
    jabatan = session.get('jabatan', '').strip()
    halaman_aktif = session.get('halaman_aktif', 'utama')
    return (
        jabatan == "Admin"
        or jabatan in ["Tata Usaha", "TU"]
        or halaman_aktif == "admin_sistem"
    )

def bisa_hapus():
    """✅ Hanya jika halaman aktif = Admin Sistem atau jabatan utama Admin"""
    jabatan = session.get('jabatan', '').strip()
    halaman_aktif = session.get('halaman_aktif', 'utama')
    return jabatan == "Admin" or halaman_aktif == "admin_sistem"

def bisa_atur_akun():
    """✅ Hanya jika halaman aktif = Admin Sistem atau jabatan utama Admin"""
    jabatan = session.get('jabatan', '').strip()
    halaman_aktif = session.get('halaman_aktif', 'utama')
    return jabatan == "Admin" or halaman_aktif == "admin_sistem"

def dapatkan_semua_tugas(jabatan, tugas_tambahan):
    """Gabungkan tugas otomatis + tugas tambahan"""
    daftar = []
    if jabatan in ["Guru", "Kepala Sekolah"]:
        daftar.append("Mengajar")
    if tugas_tambahan:
        daftar.extend([t.strip() for t in tugas_tambahan.split(',')])
    return daftar

def bersihkan_tugas(jabatan, tugas_input, tugas_sudah_ada=""):
    """
    Filter tugas agar sesuai jabatan,
    TAPI TIDAK menghapus 'Wali Kelas' yang sudah ada.
    """
    if not tugas_input:
        tugas_input = ""

    tugas_lama = [t.strip() for t in tugas_sudah_ada.split(',')] if tugas_sudah_ada else []
    simpan_wali = "Wali Kelas" in tugas_lama

    daftar_input = [t.strip() for t in tugas_input.split(',')]
    daftar_valid = DAFTAR_TUGAS.get(jabatan, [])
    tugas_terpilih = [t for t in daftar_input if t in daftar_valid]

    if simpan_wali and "Wali Kelas" not in tugas_terpilih:
        tugas_terpilih.insert(0, "Wali Kelas")

    return ", ".join(tugas_terpilih)

# ==========================================
# RUTE UTAMA - TAMPILKAN DAFTAR & STATISTIK
# ==========================================
@data_guru_bp.route('/')
def halaman_data_guru():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ Ganti pengecekan lama dengan yang baru
    if not bisa_lihat():
        flash("Anda tidak memiliki hak akses ke halaman ini", "danger")
        return redirect(url_for('dashboard.index'))

    # Ambil SEMUA data guru dari database
    semua_guru = Guru.query.all()

    # Hitung statistik secara otomatis
    total_guru = len(semua_guru)
    guru_laki = Guru.query.filter_by(jenis_kelamin='Laki-laki').count()
    guru_perempuan = Guru.query.filter_by(jenis_kelamin='Perempuan').count()
    guru_sertifikasi = Guru.query.filter_by(sertifikasi=True).count()

    # Hitung persentase (hindari pembagian nol)
    persen_guru_laki = round((guru_laki / total_guru) * 100) if total_guru > 0 else 0
    persen_guru_perempuan = round((guru_perempuan / total_guru) * 100) if total_guru > 0 else 0
    persen_sertifikasi = round((guru_sertifikasi / total_guru) * 100) if total_guru > 0 else 0

    # Ubah format data agar sesuai tampilan
    daftar_guru = []
    for g in semua_guru:
        daftar_guru.append({
            'id': g.id,
            'nama': g.nama,
            'email': g.email,
            'jenis_kelamin': g.jenis_kelamin,
            'jabatan': g.jabatan or 'Guru',
            'tugas_tambahan': g.tugas_tambahan.split(',') if g.tugas_tambahan else [],
            'semua_tugas': dapatkan_semua_tugas(g.jabatan, g.tugas_tambahan),
            'status': g.status or 'Aktif',
            'akun': g.akun
        })

    context = {
        'active_page': 'data_guru',
        'sub_page': 'daftar',
        'user_name': session.get('user_name', 'Pengguna'),
        'jabatan': session.get('jabatan', ''),
        'role': session.get('jabatan', ''),
        'daftar_tugas_user': session.get('tugas_tambahan', '').split(',') if session.get('tugas_tambahan') else [],
        'tugas_tambahan': session.get('tugas_tambahan', ''),
        'user': {
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },
        'today_date': datetime.now().strftime('%d %B %Y'),
        'today_date_long': datetime.now().strftime('%A, %d %B %Y'),
        'total_guru': total_guru,
        'guru_laki': guru_laki,
        'guru_perempuan': guru_perempuan,
        'persen_guru_laki': persen_guru_laki,
        'persen_guru_perempuan': persen_guru_perempuan,
        'guru_sertifikasi': guru_sertifikasi,
        'persen_sertifikasi': persen_sertifikasi,
        'daftar_guru': daftar_guru,
        'bisa_kelola': bisa_kelola(),
        'bisa_hapus': bisa_hapus(),
        'bisa_atur_akun': bisa_atur_akun()
    }

    return render_template('index.html', halaman_aktif=session.get('halaman_aktif', 'utama'), **context)

# ==========================================
# RUTE TAMBAH DATA GURU
# ==========================================
@data_guru_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_guru():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ Ganti pengecekan
    if not bisa_kelola():
        flash("Anda tidak berhak menambah data guru", "danger")
        return redirect(url_for('data_guru.halaman_data_guru'))

    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form.get('nama', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        jabatan = request.form.get('jabatan', '').strip()
        tugas_tambahan = request.form.get('tugas_tambahan', '').strip()
        sertifikasi = True if request.form.get('sertifikasi') == 'ya' else False
        status = request.form.get('status', 'Aktif').strip()
        tempat_lahir = request.form.get('tempat_lahir', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir')
        no_hp = request.form.get('no_hp', '').strip()
        email = request.form.get('email', '').strip().lower()
        alamat = request.form.get('alamat', '').strip()

        # --------------------------
        # VALIDASI ATURAN SISTEM
        # --------------------------
        if jabatan not in JABATAN_IZIN:
            flash(f"Jabatan '{jabatan}' tidak valid atau tidak dapat dibuat lewat menu", "danger")
            return redirect(url_for('data_guru.tambah_guru'))

        # ✅ VALIDASI NOMOR HP
        if no_hp:  # Cek hanya jika diisi
            if not no_hp.isdigit():
                flash("Nomor HP hanya boleh berisi angka saja!", "danger")
                return redirect(url_for('data_guru.tambah_guru'))
            if len(no_hp) < 8 or len(no_hp) > 13:
                flash("Nomor HP harus memiliki panjang antara 8 sampai 13 angka!", "danger")
                return redirect(url_for('data_guru.tambah_guru'))

        # ✅ VALIDASI EMAIL
        if email:  # Cek hanya jika diisi
            pola_email = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(pola_email, email):
                flash("Format email tidak valid! Contoh yang benar: nama@domain.com", "danger")
                return redirect(url_for('data_guru.tambah_guru'))
            # Cek apakah email sudah terdaftar
            if Guru.query.filter_by(email=email).first():
                flash('Email sudah terdaftar! Gunakan email lain.', 'danger')
                return redirect(url_for('data_guru.tambah_guru'))

        tugas_tambahan = bersihkan_tugas(jabatan, tugas_tambahan, "")

        # Buat data baru
        guru_baru = Guru(
            nama=nama,
            jenis_kelamin=jenis_kelamin,
            jabatan=jabatan,
            tugas_tambahan=tugas_tambahan,
            sertifikasi=sertifikasi,
            status=status,
            tempat_lahir=tempat_lahir,
            tanggal_lahir=datetime.strptime(tanggal_lahir, '%Y-%m-%d') if tanggal_lahir else None,
            no_hp=no_hp,
            email=email if email else None,
            alamat=alamat
        )

        # Simpan ke database
        db.session.add(guru_baru)
        db.session.commit()
        flash('Data guru berhasil ditambahkan!', 'success')
        return redirect(url_for('data_guru.halaman_data_guru'))

    # Ganti bagian return render_template jadi begini:
    return render_template('index.html',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        active_page='data_guru',
        sub_page='form_tambah',
        mode='tambah',
        daftar_tugas_konfig=DAFTAR_TUGAS,
        role=session.get('jabatan', ''),
        daftar_tugas_user=session.get('tugas_tambahan', '').split(',') if session.get('tugas_tambahan') else [],
        jabatan=session.get('jabatan', ''),
        tugas_tambahan=session.get('tugas_tambahan', ''),
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },
        bisa_kelola=bisa_kelola(),
        bisa_hapus=bisa_hapus(),
        bisa_atur_akun=bisa_atur_akun()
    )

# ==========================================
# RUTE UBAH DATA GURU
# ==========================================
@data_guru_bp.route('/ubah/<int:id>', methods=['GET', 'POST'])
def ubah_guru(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ Ganti pengecekan
    if not bisa_kelola():
        flash("Anda tidak berhak mengubah data guru", "danger")
        return redirect(url_for('dashboard.index'))

    guru = Guru.query.get_or_404(id)

    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form.get('nama', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        jabatan_baru = request.form.get('jabatan', '').strip()
        tugas_tambahan = request.form.get('tugas_tambahan', '').strip()
        sertifikasi = True if request.form.get('sertifikasi') == 'ya' else False
        status = request.form.get('status', 'Aktif').strip()
        tempat_lahir = request.form.get('tempat_lahir', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir')
        no_hp = request.form.get('no_hp', '').strip()
        email = request.form.get('email', '').strip().lower()
        alamat = request.form.get('alamat', '').strip()

        # --------------------------
        # VALIDASI ATURAN SISTEM
        # --------------------------
        if jabatan_baru not in JABATAN_IZIN:
            flash(f"Tidak dapat mengubah ke jabatan '{jabatan_baru}'", "danger")
            return redirect(url_for('data_guru.ubah_guru', id=id))

        if no_hp:
            if not no_hp.isdigit():
                flash("Nomor HP hanya boleh berisi angka saja!", "danger")
                return redirect(url_for('data_guru.ubah_guru', id=id))
            if len(no_hp) < 8 or len(no_hp) > 13:
                flash("Nomor HP harus memiliki panjang antara 8 sampai 13 angka!", "danger")
                return redirect(url_for('data_guru.ubah_guru', id=id))

        if email:
            pola_email = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(pola_email, email):
                flash("Format email tidak valid! Contoh yang benar: nama@domain.com", "danger")
                return redirect(url_for('data_guru.ubah_guru', id=id))

            if email != guru.email and Guru.query.filter_by(email=email).first():
                flash('Email sudah digunakan oleh data lain!', 'danger')
                return redirect(url_for('data_guru.ubah_guru', id=id))

        tugas_tambahan = bersihkan_tugas(jabatan_baru, tugas_tambahan, guru.tugas_tambahan)

        guru.nama = nama
        guru.jenis_kelamin = jenis_kelamin
        guru.jabatan = jabatan_baru
        guru.tugas_tambahan = tugas_tambahan
        guru.sertifikasi = sertifikasi
        guru.status = status
        guru.tempat_lahir = tempat_lahir
        guru.tanggal_lahir = datetime.strptime(tanggal_lahir, '%Y-%m-%d') if tanggal_lahir else None
        guru.no_hp = no_hp
        guru.email = email if email else None
        guru.alamat = alamat

        db.session.commit()
        flash('Data guru berhasil diperbarui!', 'success')
        return redirect(url_for('data_guru.halaman_data_guru'))

    return render_template('index.html',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        active_page='data_guru',
        sub_page='form_ubah',
        mode='ubah',
        guru=guru,
        daftar_tugas_konfig=DAFTAR_TUGAS,
        role=session.get('jabatan', ''),
        daftar_tugas_user=session.get('tugas_tambahan', '').split(',') if session.get('tugas_tambahan') else [],
        jabatan=session.get('jabatan', ''),
        tugas_tambahan=session.get('tugas_tambahan', ''),
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },

        bisa_kelola=bisa_kelola(),
        bisa_hapus=bisa_hapus(),
        bisa_atur_akun=bisa_atur_akun()
    )

# ==========================================
# RUTE HAPUS DATA GURU
# ==========================================
@data_guru_bp.route('/hapus/<int:id>', methods=['POST'])
def hapus_guru(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ Gunakan hak khusus untuk hapus
    if not bisa_hapus():
        flash("Anda tidak berhak menghapus data guru", "danger")
        return redirect(url_for('data_guru.halaman_data_guru'))

    guru = Guru.query.get_or_404(id)
    db.session.delete(guru)
    db.session.commit()
    flash('Data guru berhasil dihapus!', 'success')
    return redirect(url_for('data_guru.halaman_data_guru'))

# ==========================================
# RUTE LIHAT DETAIL
# ==========================================
@data_guru_bp.route('/detail/<int:id>')
def detail_guru(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_lihat():
        flash("Anda tidak memiliki hak akses untuk melihat data ini", "danger")
        return redirect(url_for('dashboard.index'))

    guru = Guru.query.get_or_404(id)

    return render_template('index.html',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        active_page='data_guru',
        sub_page='detail',
        guru=guru,
        role=session.get('jabatan', ''),
        daftar_tugas_user=session.get('tugas_tambahan', '').split(',') if session.get('tugas_tambahan') else [],
        jabatan=session.get('jabatan', ''),
        tugas_tambahan=session.get('tugas_tambahan', ''),
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },

        bisa_kelola=bisa_kelola(),
        bisa_hapus=bisa_hapus(),
        bisa_atur_akun=bisa_atur_akun()
    )

@data_guru_bp.route('/atur-ulang-password/<int:id>', methods=['GET', 'POST'])
def atur_ulang_password(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_atur_akun():
        flash("Hanya Admin yang berhak mengatur password", "danger")
        return redirect(url_for('data_guru.halaman_data_guru'))

    guru = Guru.query.get_or_404(id)

    if not guru.akun:
        flash("Guru ini belum memiliki akun login", "warning")
        return redirect(url_for('data_guru.halaman_data_guru'))

    if request.method == 'POST':
        password_baru = request.form.get('password_baru', '').strip()
        konfirmasi_password = request.form.get('konfirmasi_password', '').strip()

        if not password_baru or len(password_baru) < 6:
            flash("Password minimal 6 karakter", "danger")
            return render_template('form_atur_password.html', guru=guru)

        if password_baru != konfirmasi_password:
            flash("Konfirmasi password tidak cocok", "danger")
            return render_template('form_atur_password.html', guru=guru)

        guru.akun.set_password(password_baru)
        db.session.commit()
        flash(f"Password untuk {guru.nama} berhasil diubah!", "success")
        return redirect(url_for('data_guru.halaman_data_guru'))

    return render_template('form_atur_password.html',
        guru=guru,
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        active_page='data_guru',
        # ✅ TAMBAHKAN INI
        bisa_kelola=bisa_kelola(),
        bisa_hapus=bisa_hapus(),
        bisa_atur_akun=bisa_atur_akun()
    )

@data_guru_bp.route('/buat-akun/<int:id>', methods=['GET', 'POST'])
def buat_akun(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_atur_akun():
        flash("Hanya Admin yang berhak membuat akun", "danger")
        return redirect(url_for('data_guru.halaman_data_guru'))

    guru = Guru.query.get_or_404(id)

    if guru.akun:
        flash("Guru ini sudah memiliki akun login", "warning")
        return redirect(url_for('data_guru.halaman_data_guru'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username dan Password wajib diisi!", "danger")
            return render_template('password/form_buat_akun.html', guru=guru)

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan, pilih yang lain!", "danger")
            return render_template('password/form_buat_akun.html', guru=guru)

        try:
            akun_baru = User(
                username=username,
                password_hash=generate_password_hash(password),
                guru_id=guru.id,
                jabatan=guru.jabatan,
                tugas_tambahan=guru.tugas_tambahan,
                aktif=True
            )
            db.session.add(akun_baru)
            db.session.commit()
            flash(f"Akun untuk {guru.nama} berhasil dibuat!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal membuat akun: {str(e)}", "danger")

        return redirect(url_for('data_guru.halaman_data_guru'))

    return render_template('password/form_buat_akun.html',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        guru=guru,
        active_page='data_guru',
        sub_page='buat_akun',
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },
        # ✅ TAMBAHKAN INI
        bisa_kelola=bisa_kelola(),
        bisa_hapus=bisa_hapus(),
        bisa_atur_akun=bisa_atur_akun()
    )

# ==========================================
# RUTE ATUR ULANG / UBAH PASSWORD
# ==========================================
@data_guru_bp.route('/ubah-password/<int:id>', methods=['GET', 'POST'])
def ubah_password(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ Ganti pengecekan
    if not bisa_atur_akun():
        flash("Hanya Admin yang berhak mengubah password", "danger")
        return redirect(url_for('data_guru.halaman_data_guru'))

    guru = Guru.query.get_or_404(id)

    if not hasattr(guru, 'akun') or not guru.akun:
        flash("Guru ini belum memiliki akun login", "warning")
        return redirect(url_for('data_guru.halaman_data_guru'))

    if request.method == 'POST':
        pass_baru = request.form.get('password_baru', '').strip()
        konfirmasi = request.form.get('konfirmasi_password', '').strip()

        if len(pass_baru) < 6:
            flash("Password minimal 6 karakter!", "danger")
            return render_template('form_ubah_password.html', guru=guru)

        if pass_baru != konfirmasi:
            flash("Konfirmasi password tidak cocok!", "danger")
            return render_template('form_ubah_password.html', guru=guru)

        guru.akun.password_hash = generate_password_hash(pass_baru)
        db.session.commit()
        flash("Password berhasil diperbarui!", "success")
        return redirect(url_for('data_guru.halaman_data_guru'))

    return render_template('form_ubah_password.html',
        guru=guru,
        active_page='data_guru',
        sub_page='ubah_password',
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        }
    )