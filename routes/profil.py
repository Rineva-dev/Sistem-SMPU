from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db, Guru, User
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime
from sqlalchemy.exc import IntegrityError

profil_bp = Blueprint('profil', __name__, url_prefix='/profil')

# HALAMAN BIODATA GURU
@profil_bp.route('/biodata')
def biodata():
    user_id = session.get('user_id') or session.get('absensi_user_id')

    referer = request.referrer
    if referer and not referer.endswith('/profil/biodata') and not 'login' in referer:
        session['kembali_ke'] = referer
        print("✅ Disimpan kembali_ke:", referer)

    halaman_aktif = session.get('halaman_aktif', 'utama')
    session.setdefault('halaman_aktif', halaman_aktif)

    referer = request.referrer or ''
    active_page = session.get('active_page', 'dashboard')
    
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
        active_page = 'dashboard'
    
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

# =========================================================
# EDIT BIODATA GURU — COMPLETE
# =========================================================
@profil_bp.route('/edit-biodata', methods=['POST'])
def edit_biodata():

    # -----------------------------------------------------
    # IDENTIFIKASI USER
    # -----------------------------------------------------
    user_id = session.get('user_id') or session.get('absensi_user_id')

    if not user_id:
        flash('Silakan login terlebih dahulu.', 'warning')

        if session.get('absensi_logged_in'):
            return redirect(url_for('absensi.login_absensi'))

        return redirect(url_for('login.halaman_login'))

    user = User.query.get(user_id)
    guru = user.guru if user else None

    if not guru:
        flash('Data guru tidak ditemukan.', 'danger')

        if g.sistem_mode == 'absensi':
            return redirect(url_for('absensi_profil.biodata'))

        return redirect(url_for('profil.biodata'))

    # -----------------------------------------------------
    # AMBIL DATA FORM
    # -----------------------------------------------------
    def ambil(nama):
        return request.form.get(nama, '').strip()

    try:

        # =================================================
        # 1. VALIDASI IDENTITAS WAJIB
        # =================================================
        nama = ambil('nama')
        jenis_kelamin = ambil('jenis_kelamin')

        if not nama:
            flash('Nama lengkap wajib diisi.', 'danger')
            return redirect(url_for('profil.biodata'))

        if len(nama) > 100:
            flash('Nama maksimal 100 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if not jenis_kelamin or len(jenis_kelamin) > 20:
            flash('Jenis kelamin wajib diisi dengan benar.', 'danger')
            return redirect(url_for('profil.biodata'))

        # =================================================
        # 2. AMBIL DAN VALIDASI NIK
        # =================================================
        nik = ambil('nik') or None

        if nik and (not nik.isdigit() or len(nik) != 16):
            flash('NIK harus terdiri dari tepat 16 digit angka.', 'danger')
            return redirect(url_for('profil.biodata'))

        # =================================================
        # 3. VALIDASI TANGGAL LAHIR
        # =================================================
        tanggal_lahir_input = ambil('tanggal_lahir')

        if tanggal_lahir_input:
            try:
                tanggal_lahir = datetime.strptime(
                    tanggal_lahir_input, '%Y-%m-%d'
                ).date()
            except ValueError:
                flash('Tanggal lahir tidak valid.', 'danger')
                return redirect(url_for('profil.biodata'))
        else:
            tanggal_lahir = None

        # =================================================
        # 4. VALIDASI EMAIL UNIK
        # =================================================
        email = ambil('email') or None

        if email:
            if len(email) > 100:
                flash('Email maksimal 100 karakter.', 'danger')
                return redirect(url_for('profil.biodata'))

            email_duplikat = Guru.query.filter(
                Guru.email == email,
                Guru.id != guru.id
            ).first()

            if email_duplikat:
                flash('Email tersebut sudah digunakan guru lain.', 'danger')
                return redirect(url_for('profil.biodata'))

        # =================================================
        # 5. VALIDASI PANJANG FIELD
        # =================================================
        nip = ambil('nip') or None
        gelar_depan = ambil('gelar_depan') or None
        gelar_belakang = ambil('gelar_belakang') or None
        tempat_lahir = ambil('tempat_lahir') or None
        pendidikan = ambil('pendidikan_terakhir') or None
        status_pernikahan = ambil('status_pernikahan') or None
        no_hp = ambil('no_hp') or None

        if nip and len(nip) > 50:
            flash('NIP maksimal 50 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if gelar_depan and len(gelar_depan) > 30:
            flash('Gelar depan maksimal 30 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if gelar_belakang and len(gelar_belakang) > 50:
            flash('Gelar belakang maksimal 50 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if tempat_lahir and len(tempat_lahir) > 100:
            flash('Tempat lahir maksimal 100 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if pendidikan and len(pendidikan) > 10:
            flash('Pendidikan terakhir maksimal 10 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if status_pernikahan and len(status_pernikahan) > 20:
            flash('Status pernikahan maksimal 20 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        if no_hp and len(no_hp) > 20:
            flash('Nomor handphone maksimal 20 karakter.', 'danger')
            return redirect(url_for('profil.biodata'))

        # =================================================
        # 6. UPDATE IDENTITAS PRIBADI
        # =================================================
        guru.nama = nama
        guru.nip = nip
        guru.nik = nik

        guru.gelar_depan = gelar_depan
        guru.gelar_belakang = gelar_belakang

        guru.jenis_kelamin = jenis_kelamin
        guru.tempat_lahir = tempat_lahir
        guru.tanggal_lahir = tanggal_lahir

        guru.pendidikan_terakhir = pendidikan
        guru.status_pernikahan = status_pernikahan

        # =================================================
        # 7. UPDATE DATA KEPEGAWAIAN
        # =================================================

        # =================================================
        # 8. UPDATE DATA KONTAK
        # =================================================
        guru.no_hp = no_hp
        guru.email = email
        guru.alamat = ambil('alamat') or None

        # =================================================
        # 9. SINKRONISASI DATA USER
        # =================================================

        # =================================================
        # 10. SIMPAN DATABASE
        # =================================================
        db.session.commit()

        # =================================================
        # 11. UPDATE SESSION
        # =================================================
        session['user_name'] = guru.nama
        session['jabatan'] = guru.jabatan
        session['email'] = guru.email
        session['no_hp'] = guru.no_hp

        nama_parts = guru.nama.split()

        session['user_initials'] = ''.join(
            bagian[0].upper()
            for bagian in nama_parts[:2]
        )

        flash('Biodata berhasil diperbarui!', 'success')

    except IntegrityError as e:
        db.session.rollback()

        print('[BIODATA] IntegrityError:', str(e))

        flash(
            'Data gagal disimpan karena ada data unik yang sudah digunakan, '
            'misalnya alamat email.',
            'danger'
        )

    except Exception as e:
        db.session.rollback()

        print('[BIODATA] ERROR:', str(e))

        flash(
            'Terjadi kesalahan saat menyimpan biodata. '
            'Silakan coba kembali.',
            'danger'
        )

    # -----------------------------------------------------
    # KEMBALI KE HALAMAN BIODATA
    # -----------------------------------------------------
    if g.sistem_mode == 'absensi':
        return redirect(url_for('absensi_profil.biodata'))

    return redirect(url_for('profil.biodata'))
