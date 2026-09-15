from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db, Guru, User
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

profil_bp = Blueprint('profil', __name__, url_prefix='/profil')

# ✅ HALAMAN BIODATA GURU — DILENGKAPI VARIABEL SIDEBAR
@profil_bp.route('/biodata')
def biodata():
    # Baca dari kedua sumber
    print("===== DEBUG SESI =====")
    print("user_id dari sesi:", session.get('user_id'))
    print("absensi_user_id:", session.get('absensi_user_id'))
    print("absensi_logged_in:", session.get('absensi_logged_in'))
    user_id = session.get('user_id') or session.get('absensi_user_id')
    print("user_id yang dipakai:", user_id)
    
    # ✅ BACA halaman_aktif
    halaman_aktif = session.get('halaman_aktif', 'utama')
    session.setdefault('halaman_aktif', halaman_aktif)
    
    # ✅ DETEKSI OTOMATIS DARI URL ASAL — LENGKAP ABSENSI
    referer = request.referrer or ''
    active_page = session.get('active_page', 'dashboard')  # nilai bawaan
    
    # ========== SISTEM ABSENSI ==========
    if '/absensi-guru/dashboard' in referer or 'dashboard' in referer and 'absensi' in referer:
        active_page = 'dashboard'
    elif '/absensi-guru/absensi-harian' in referer or 'absensi_harian' in referer:
        active_page = 'absensi_harian'
    elif '/absensi-guru/rekap-absensi' in referer or 'rekap_absensi' in referer:
        active_page = 'rekap_absensi'
    elif '/absensi-guru/rincian-gaji' in referer or 'rincian_gaji' in referer:
        active_page = 'rincian_gaji'
    
    # ========== SISTEM UTAMA — ADMIN SISTEM ==========
    elif 'tahun-pelajaran' in referer or 'tahun_pelajaran' in referer:
        active_page = 'tahun_pelajaran'
    elif 'kalender' in referer:
        active_page = 'kalender'
    elif 'data-guru' in referer or '/guru' in referer:
        active_page = 'data_guru'
    elif 'data-siswa' in referer or '/siswa' in referer:
        active_page = 'data_siswa'
    elif 'data-kelas' in referer or '/kelas' in referer:
        active_page = 'data_kelas'
    elif 'data-mapel' in referer or 'data_mapel' in referer:
        active_page = 'data_mapel'
    elif 'data-ekskul' in referer or 'data_ekskul' in referer:
        active_page = 'data_ekskul'
    elif 'data-peminatan' in referer or 'data_peminatan' in referer:
        active_page = 'data_peminatan'
    elif 'dashboard-admin' in referer or 'dashboard_admin' in referer or '/admin-sistem' in referer:
        active_page = 'dashboard'  # Admin Sistem pakai 'dashboard'
    elif 'monitoring-absensi' in referer:
        active_page = 'monitoring_absensi'
    
    # ========== SISTEM UTAMA — BENDAHARA ==========
    elif 'spp-siswa' in referer or 'spp_siswa' in referer or 'pembayaran' in referer:
        active_page = 'spp_siswa'
    elif 'pemasukan' in referer:
        active_page = 'pemasukan'
    elif 'pengeluaran' in referer:
        active_page = 'pengeluaran'
    elif 'laporan-keuangan' in referer or 'lap_keuangan' in referer:
        active_page = 'lap_keuangan'
    elif 'pengaturan-biaya' in referer or 'pengaturan_pembayaran' in referer:
        active_page = 'pengaturan_pembayaran'
    
    # ========== SISTEM UTAMA — KEPALA SEKOLAH / TU / GURU ==========
    elif 'jadwal' in referer:
        active_page = 'jadwal'
    elif '/nilai/guru' in referer or 'nilai_guru' in referer:
        active_page = 'nilai_guru'
    elif '/absensi/guru' in referer or 'absensi_guru' in referer:
        active_page = 'absensi_guru'
    elif 'agenda' in referer:
        active_page = 'agenda'
    elif 'persetujuan' in referer:
        active_page = 'persetujuan'
    elif 'laporan/sekolah' in referer or 'laporan_sekolah' in referer:
        active_page = 'laporan'
    elif 'profil-sekolah' in referer:
        active_page = 'profil_sekolah'
    elif 'surat-menyurat' in referer:
        active_page = 'surat_menyurat'
    elif 'arsip-dokumen' in referer or 'arsip' in referer:
        active_page = 'arsip'
    elif 'laporan-administrasi' in referer or 'laporan_administrasi' in referer:
        active_page = 'laporan_sekolah'
    elif 'pengaturan-umum' in referer or 'pengaturan_umum' in referer:
        active_page = 'pengaturan_umum'
    elif 'atur-hak-akses' in referer or 'atur_hak' in referer:
        active_page = 'atur_hak'
    elif 'log-aktivitas' in referer or 'log_aktivitas' in referer:
        active_page = 'log_aktivitas'
    elif 'backup-data' in referer or 'backup_data' in referer:
        active_page = 'backup_data'
    elif 'info-sistem' in referer or 'info_sistem' in referer:
        active_page = 'info_sistem'
    elif 'dashboard-guru' in referer:
        active_page = 'dashboard_guru'
    elif 'dashboard' in referer:
        active_page = 'dashboard'  # Halaman utama / Kepala Sekolah / TU
    
    # ✅ Simpan ke sesi agar konsisten antar halaman profil
    session['active_page'] = active_page
    
    # =============================================
    # SISA KODE TETAP SAMA SEPERTI ASLINYA
    # =============================================
    if not user_id:
        flash('Silakan login dulu', 'warning')
        if session.get('absensi_logged_in'):
            return redirect(url_for('absensi.login_absensi'))
        return redirect(url_for('login.halaman_login'))
    
    user = User.query.get(str(user_id))
    print("Apakah User ditemukan?", user)
    if user:
        print("User punya guru?", user.guru)
    
    if not session.get('user_id'):
        user = User.query.get(str(user_id))
        if user and user.guru:
            session['user_id'] = user.id
            session['user_name'] = user.guru.nama
            session['jabatan'] = user.guru.jabatan or 'Guru'
            session['user_initials'] = ''.join(
                [nama[0].upper() for nama in user.guru.nama.split()[:2]]
            )
            session['email'] = getattr(user.guru, 'email', None)
            session['no_hp'] = getattr(user.guru, 'no_hp', None) or getattr(user.guru, 'telepon', None)
            
            if g.sistem_mode == 'absensi':
                return redirect(url_for('absensi_profil.biodata'))
            else:
                return redirect(url_for('profil.biodata'))
    
    user = User.query.get(str(user_id))
    guru = user.guru if user else None
    
    daftar_tugas = []
    if user and user.tugas_tambahan:
        if isinstance(user.tugas_tambahan, str):
            daftar_tugas = [t.strip() for t in user.tugas_tambahan.split(',')]
        else:
            daftar_tugas = user.tugas_tambahan
    
    if halaman_aktif == 'utama':
        nama_halaman_aktif = guru.jabatan
    elif halaman_aktif == 'bendahara':
        nama_halaman_aktif = 'Bendahara'
    elif halaman_aktif == 'admin_sistem':
        nama_halaman_aktif = 'Admin Sistem'
    elif halaman_aktif == 'wali_kelas':
        nama_halaman_aktif = 'Wali Kelas'
    elif halaman_aktif == 'waka_kurikulum':
        nama_halaman_aktif = 'Waka Kurikulum'
    elif halaman_aktif == 'waka_kesiswaan':
        nama_halaman_aktif = 'Waka Kesiswaan'
    elif halaman_aktif == 'pembina_ekskul':
        nama_halaman_aktif = 'Pembina Ekstrakurikuler'
    else:
        nama_halaman_aktif = guru.jabatan
    
    return render_template(
        'profil/biodata.html',
        guru=guru,
        user=user,
        halaman_aktif=halaman_aktif,
        active_page=active_page,
        nama_halaman_aktif=nama_halaman_aktif,
        daftar_tugas=daftar_tugas
    )

# ✅ HALAMAN UBAH AKUN — DILENGKAPI VARIABEL SIDEBAR
@profil_bp.route('/ubah-akun', methods=['GET', 'POST'])
def ubah_akun():
    user_id = session.get('user_id') or session.get('absensi_user_id')
    if not user_id:
        flash('Silakan login dulu', 'warning')
        if session.get('absensi_logged_in'):
            return redirect(url_for('absensi.login_absensi'))
        return redirect(url_for('login.halaman_login'))

    if not session.get('user_id'):
        user = User.query.get(str(user_id))
        if user and user.guru:
            session['user_id'] = user.id
            session['user_name'] = user.guru.nama
            session['jabatan'] = user.guru.jabatan or 'Guru'
            session['user_initials'] = ''.join(
                [nama[0].upper() for nama in user.guru.nama.split()[:2]]
            )

    user = User.query.get(str(user_id))
    if not user:
        flash('Pengguna tidak ditemukan', 'danger')
        if g.sistem_mode == 'absensi':
            return redirect(url_for('absensi_profil.biodata'))
        else:
            return redirect(url_for('profil.biodata'))

    if request.method == 'POST':
        username_baru = request.form.get('username', '').strip()
        password_lama = request.form.get('password_lama', '')
        password_baru = request.form.get('password_baru', '')
        konfirmasi_password = request.form.get('konfirmasi_password', '')
        
        if User.query.filter(User.username == username_baru, User.id != user.id).first():
            flash('Username sudah digunakan!', 'danger')
            return redirect(url_for('profil.ubah_akun'))
        
        user.username = username_baru
        
        if password_lama:
            if not user.check_password(password_lama):
                flash('Password lama salah!', 'danger')
                return redirect(url_for('profil.ubah_akun'))
            if password_baru != konfirmasi_password:
                flash('Password baru tidak cocok!', 'danger')
                return redirect(url_for('profil.ubah_akun'))
            if len(password_baru) < 6:
                flash('Password minimal 6 karakter!', 'danger')
                return redirect(url_for('profil.ubah_akun'))
            user.set_password(password_baru)
        
        db.session.commit()
        flash('Akun berhasil diperbarui!', 'success')
        if g.sistem_mode == 'absensi':
            return redirect(url_for('absensi_profil.biodata'))
        else:
            return redirect(url_for('profil.biodata'))
    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not session.get('halaman_aktif'):
        session['halaman_aktif'] = halaman_aktif

    return render_template(
        'profil/ubah_akun.html',
        user=user,
        halaman_aktif=halaman_aktif,
        active_page=halaman_aktif
    )

# ✅ HALAMAN UBAH FOTO PROFIL — DIPERBAIKI
@profil_bp.route('/ubah-foto', methods=['GET', 'POST'])
def ubah_foto():
    user_id = session.get('user_id') or session.get('absensi_user_id')
    if not user_id:
        flash('Silakan login dulu', 'warning')
        if session.get('absensi_logged_in'):
            return redirect(url_for('absensi.login_absensi'))
        return redirect(url_for('login.halaman_login'))

    if not session.get('user_id'):
        user = User.query.get(str(user_id))
        if user and user.guru:
            session['user_id'] = user.id
            session['user_name'] = user.guru.nama
            session['jabatan'] = user.guru.jabatan or 'Guru'
            session['user_initials'] = ''.join(
                [nama[0].upper() for nama in user.guru.nama.split()[:2]]
            )
    
    user = User.query.get(str(user_id))
    guru = user.guru if user else None
    if not guru:
        flash('Data guru tidak ditemukan', 'danger')
        if g.sistem_mode == 'absensi':
            return redirect(url_for('absensi_profil.biodata'))
        else:
            return redirect(url_for('profil.biodata'))
    
    if request.method == 'POST':
        foto_data = request.form.get('foto_data', '')
        if foto_data and foto_data.startswith('data:image'):
            from config import Config
            import os, uuid, base64
            _, b64_str = foto_data.split(',')
            ekstensi = '.jpg'
            nama_file_baru = f"{uuid.uuid4().hex}{ekstensi}"
            folder_simpan = os.path.join(Config.UPLOAD_FOLDER, 'foto_profil')
            os.makedirs(folder_simpan, exist_ok=True)
            path_simpan = os.path.join(folder_simpan, nama_file_baru)
            with open(path_simpan, 'wb') as f:
                f.write(base64.b64decode(b64_str))
            
            if guru.foto_profil:
                path_lama = os.path.join(folder_simpan, guru.foto_profil)
                if os.path.exists(path_lama):
                    try: os.remove(path_lama)
                    except: pass
            
            guru.foto_profil = nama_file_baru
            session['foto_profil'] = guru.foto_profil
            db.session.commit()
            flash('✅ Foto profil berhasil diperbarui!', 'success')
        else:
            flash('Silakan pilih foto dan potong terlebih dahulu', 'warning')

    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not session.get('halaman_aktif'):
        session['halaman_aktif'] = halaman_aktif
    
    if g.sistem_mode == 'absensi':
        return redirect(url_for('absensi_profil.biodata'))
    else:
        return redirect(url_for('profil.biodata'))

# ✅ HALAMAN EDIT BIODATA — DIPERBAIKI
@profil_bp.route('/edit-biodata', methods=['GET', 'POST'])
def edit_biodata():
    user_id = session.get('user_id') or session.get('absensi_user_id')
    if not user_id:
        flash('Silakan login dulu', 'warning')
        if session.get('absensi_logged_in'):
            return redirect(url_for('absensi.login_absensi'))
        return redirect(url_for('login.halaman_login'))

    if not session.get('user_id'):
        user = User.query.get(str(user_id))
        if user and user.guru:
            session['user_id'] = user.id
            session['user_name'] = user.guru.nama
            session['jabatan'] = user.guru.jabatan or 'Guru'
            session['user_initials'] = ''.join(
                [nama[0].upper() for nama in user.guru.nama.split()[:2]]
            )
    
    user = User.query.get(str(user_id))
    guru = user.guru if user else None
    if not guru:
        flash('Data guru tidak ditemukan', 'danger')
        if g.sistem_mode == 'absensi':
            return redirect(url_for('absensi_profil.biodata'))
        else:
            return redirect(url_for('profil.biodata'))
    
    if request.method == 'POST':
        guru.nik = request.form.get('nik', '').strip() or None
        guru.gelar_depan = request.form.get('gelar_depan', '').strip() or None
        guru.gelar_belakang = request.form.get('gelar_belakang', '').strip() or None
        guru.pendidikan_terakhir = request.form.get('pendidikan_terakhir', '').strip() or None
        guru.status_pernikahan = request.form.get('status_pernikahan', '').strip() or None
        guru.no_hp = request.form.get('no_hp', '').strip() or None
        guru.email = request.form.get('email', '').strip() or None
        guru.alamat = request.form.get('alamat', '').strip() or None
        
        db.session.commit()
        flash('✅ Biodata berhasil diperbarui!', 'success')

    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not session.get('halaman_aktif'):
        session['halaman_aktif'] = halaman_aktif
    
    if g.sistem_mode == 'absensi':
        return redirect(url_for('absensi_profil.biodata'))
    else:
        return redirect(url_for('profil.biodata'))