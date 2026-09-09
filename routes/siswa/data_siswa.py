from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime
import re
from sqlalchemy import or_
from models import db, Siswa, Kelas, User, TahunPelajaran, RiwayatKelas

# Buat Blueprint
data_siswa_bp = Blueprint('data_siswa', __name__, url_prefix='/siswa')

# ======================================
# Fungsi Bantu Cek Hak Akses
# ======================================
def ambil_daftar_tugas():
    """Ambil daftar tugas tambahan dari sesi"""
    tugas_str = session.get('tugas_tambahan', '')
    if not tugas_str:
        return []
    return [t.strip() for t in tugas_str.split(',')]

def bisa_lihat():
    """Bisa melihat data: Admin, Admin Sistem, TU, Kepala Sekolah, Waka Kesiswaan"""
    jabatan = session.get('jabatan', '').strip()
    halaman = session.get('halaman_aktif', 'utama')
    daftar_tugas = ambil_daftar_tugas()

    return (
        jabatan == "Admin"
        or jabatan in ["Tata Usaha", "TU", "Kepala Sekolah"]
        or halaman in ["admin_sistem", "admin_dev", "waka_kesiswaan"]
        or any(tugas in ["Admin Sistem", "Admin Dev", "Waka Kesiswaan"] for tugas in daftar_tugas)
    )

def bisa_kelola():
    """Bisa tambah, ubah, hapus data siswa: Admin, Admin Sistem, TU"""
    jabatan = session.get('jabatan', '').strip()
    halaman = session.get('halaman_aktif', 'utama')
    daftar_tugas = ambil_daftar_tugas()

    return (
        jabatan == "Admin"
        or jabatan in ["Tata Usaha", "TU"]
        or halaman in ["admin_sistem", "admin_dev"]
        or any(tugas in ["Admin Sistem", "Admin Dev"] for tugas in daftar_tugas)
    )

def bisa_hapus():
    """Bisa hapus data siswa: Admin, Admin Sistem, Admin Dev saja"""
    jabatan = session.get('jabatan', '').strip()
    halaman = session.get('halaman_aktif', 'utama')
    daftar_tugas = ambil_daftar_tugas()

    return (
        jabatan == "Admin"
        or halaman in ["admin_sistem", "admin_dev"]
        or any(tugas in ["Admin Sistem", "Admin Dev"] for tugas in daftar_tugas)
    )

def bisa_buat_akun():
    """✅ HANYA Admin atau saat HALAMAN AKTIF adalah admin_sistem/admin_dev yang boleh buat/ubah akun siswa"""
    jabatan = session.get('jabatan', '').strip()
    halaman = session.get('halaman_aktif', 'utama')

    return (
        jabatan == "Admin"
        or halaman in ["admin_sistem", "admin_dev"]
    )

def get_base_tahun(kode_tp):
    """Ubah format '2025/2026-1' atau '2025/2026 Ganjil' jadi '2025/2026'"""
    if not kode_tp:
        return ""
    if '-' in kode_tp:
        kode_tp = kode_tp.split('-')[0]
    if ' ' in kode_tp:
        kode_tp = kode_tp.split(' ')[0]
    return kode_tp.strip()

# ======================================
# RUTE: Halaman Daftar Siswa ✅ SUDAH DIPERBAIKI TOTAL
# ======================================
@data_siswa_bp.route('/')
def halaman_daftar_siswa():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_lihat():
        flash("Anda tidak memiliki hak akses ke halaman ini", "danger")
        return redirect(url_for('dashboard.index'))

    # ✅ Ambil tahun yang dipilih
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun = tahun_aktif.kode if tahun_aktif else None

    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    daftar_dengan_posisi = []

    # ✅ HITUNG STATISTIK BERDASARKAN TAHUN YANG DIPILIH SAJA
    total = 0
    aktif = 0
    lulus = 0
    pindah = 0

    if kode_tahun:
        # Ambil semua riwayat yang sudah tercatat di TP ini
        riwayat_tercatat = RiwayatKelas.query.filter_by(tahun_pelajaran=kode_tahun).all()
        siswa_tercatat = {r.siswa_id: r for r in riwayat_tercatat}

        # ✅ Hitung total siswa UNIK di tahun ini saja
        id_siswa_di_tahun_ini = list(siswa_tercatat.keys())
        total = len(id_siswa_di_tahun_ini)

        # Hitung status siswa yang ada di tahun ini
        if id_siswa_di_tahun_ini:
            aktif = Siswa.query.filter(Siswa.id.in_(id_siswa_di_tahun_ini), Siswa.status == 'Aktif').count()
            lulus = Siswa.query.filter(Siswa.id.in_(id_siswa_di_tahun_ini), Siswa.status == 'Lulus').count()
            pindah = Siswa.query.filter(Siswa.id.in_(id_siswa_di_tahun_ini), Siswa.status == 'Pindah').count()

        # Ambil semua siswa yang masih Aktif
        semua_siswa_aktif = Siswa.query.filter_by(status='Aktif').all()

        for siswa in semua_siswa_aktif:
            # ✅ Aturan: Siswa hanya muncul jika tahun masuknya <= TP yang dipilih
            if siswa.tahun_diterima and siswa.tahun_diterima > int(kode_tahun.split('/')[0]):
                continue

            # Jika sudah ada riwayat di TP ini → pakai data tersebut
            if siswa.id in siswa_tercatat:
                r = siswa_tercatat[siswa.id]
                daftar_dengan_posisi.append({
                    'siswa': siswa,
                    'tingkat': r.tingkat,
                    'kelas': r.kelas.nama_kelas if r.kelas else '-'
                })
            else:
                # Jika belum ada, cari riwayat TERAKHIR dari TP sebelumnya
                riwayat_terakhir = RiwayatKelas.query.filter_by(siswa_id=siswa.id)\
                    .order_by(RiwayatKelas.tahun_pelajaran.desc())\
                    .first()

                if riwayat_terakhir:
                    # Tampilkan data dari riwayat terakhir (tanpa simpan otomatis)
                    daftar_dengan_posisi.append({
                        'siswa': siswa,
                        'tingkat': riwayat_terakhir.tingkat,
                        'kelas': riwayat_terakhir.kelas.nama_kelas if riwayat_terakhir.kelas else '-'
                    })
    else:
        # Jika belum pilih tahun, tampilkan semua siswa aktif
        total = Siswa.query.filter_by(status='Aktif').count()
        aktif = Siswa.query.filter_by(status='Aktif').count()
        lulus = Siswa.query.filter_by(status='Lulus').count()
        pindah = Siswa.query.filter_by(status='Pindah').count()

    context = {
        'active_page': 'data_siswa',
        'sub_page': 'daftar',
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'user': {
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },
        'daftar_dengan_posisi': daftar_dengan_posisi,
        'semua_tahun': semua_tahun,
        'tahun_dipilih': kode_tahun,
        'total_siswa': total,
        'siswa_aktif': aktif,
        'siswa_lulus': lulus,
        'siswa_pindah': pindah,
        'bisa_kelola': bisa_kelola(),
        'bisa_hapus': bisa_hapus(),
        'bisa_buat_akun': bisa_buat_akun()
    }

    return render_template('index.html', **context)

# ======================================
# ✅ SISA KODE DI BAWAH INI TETAP SAMA PENUH DENGAN MILIK ANDA
# ======================================

@data_siswa_bp.route('/tambah-siswa', methods=['GET', 'POST'])
def tambah_siswa():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_kelola():
        flash("Anda tidak berhak menambah data siswa", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    kode_tahun = request.form.get('tahun') or request.form.get('tahun_pelajaran') or session.get('tahun_pelajaran')
    if not kode_tahun:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun = tahun_aktif.kode if tahun_aktif else None

    tahun_pilihan = TahunPelajaran.query.filter_by(kode=kode_tahun).first()
    if not tahun_pilihan or not tahun_pilihan.aktif:
        flash("❌ Tidak dapat menambah siswa: Tahun pelajaran ini tidak aktif!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

    dasar_tahun = get_base_tahun(kode_tahun)
    daftar_kelas = Kelas.query.filter_by(
        tahun_pelajaran=dasar_tahun
    ).order_by(Kelas.jenjang, Kelas.nama_kelas).all()

    if request.method == 'POST':
        nis = request.form.get('nis', '').strip()
        nisn = request.form.get('nisn', '').strip()
        nama = request.form.get('nama', '').strip()
        nik = request.form.get('nik', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        agama = request.form.get('agama', '').strip()
        tempat_lahir = request.form.get('tempat_lahir', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir')
        alamat = request.form.get('alamat', '').strip()
        no_hp = request.form.get('no_hp', '').strip()
        email = request.form.get('email', '').strip().lower()
        tahun_masuk = request.form.get('tahun_masuk') or None
        status = request.form.get('status', 'Aktif').strip()
        nama_ayah = request.form.get('nama_ayah', '').strip()
        nama_ibu = request.form.get('nama_ibu', '').strip()
        no_hp_ortu = request.form.get('no_hp_ortu', '').strip()
        pekerjaan_ayah = request.form.get('pekerjaan_ayah', '').strip()
        pekerjaan_ibu = request.form.get('pekerjaan_ibu', '').strip()

        jenis_pendaftaran = request.form.get('jenis_pendaftaran', '').strip()
        tanggal_diterima = request.form.get('tanggal_diterima')
        tahun_diterima = request.form.get('tahun_diterima') or None
        diterima_di_kelas_id = request.form.get('diterima_di_kelas') or None
        sekolah_sd = request.form.get('sekolah_sd', '').strip()
        tahun_lulus_sd = request.form.get('tahun_lulus_sd') or None
        alamat_sekolah_sd = request.form.get('alamat_sekolah_sd', '').strip()
        sekolah_asal_pindah = request.form.get('sekolah_asal_pindah', '').strip()
        tahun_pindah = request.form.get('tahun_pindah') or None
        alamat_sekolah_pindah = request.form.get('alamat_sekolah_pindah', '').strip()

        tingkat = None
        diterima_di_kelas = None
        kelas_id = None

        if jenis_pendaftaran == 'baru':
            tingkat = '7'
            if not kode_tahun:
                flash("Tahun pelajaran belum ditentukan!", "danger")
                return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

            kelas_tingkat_7 = Kelas.query.filter_by(
                jenjang='7',
                tahun_pelajaran=dasar_tahun
            ).first()

            if kelas_tingkat_7:
                diterima_di_kelas = kelas_tingkat_7.id
                kelas_id = kelas_tingkat_7.id

        elif jenis_pendaftaran == 'pindahan':
            if not diterima_di_kelas_id:
                flash("Pilih kelas tempat diterima siswa pindahan!", "danger")
                return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

            kelas_diterima = Kelas.query.get(diterima_di_kelas_id)
            if not kelas_diterima:
                flash("Kelas yang dipilih tidak valid!", "danger")
                return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))
            if kelas_diterima.tahun_pelajaran != kode_tahun:
                flash("Kelas yang dipilih tidak sesuai dengan tahun pelajaran aktif!", "danger")
                return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

            tingkat = kelas_diterima.jenjang
            diterima_di_kelas = kelas_diterima.id
            kelas_id = kelas_diterima.id

        if tingkat not in ['7', '8', '9']:
            flash("Tingkat siswa harus 7, 8, atau 9!", "danger")
            return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

        if not nis or not nama or not jenis_kelamin or not jenis_pendaftaran or not tanggal_diterima:
            flash("NIS, Nama, Jenis Kelamin, Jenis Pendaftaran, dan Tanggal Diterima wajib diisi!", "danger")
            return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

        if Siswa.query.filter_by(nis=nis).first():
            flash("NIS sudah terdaftar!", "danger")
            return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

        if nisn and Siswa.query.filter_by(nisn=nisn).first():
            flash("NISN sudah terdaftar!", "danger")
            return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

        if not email:
            email = f"siswa-{nis}@sekolah.sch.id"
        else:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash("Format email tidak valid!", "danger")
                return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))
            if Siswa.query.filter_by(email=email).first():
                flash("Email sudah digunakan!", "danger")
                return redirect(url_for('data_siswa.tambah_siswa', tahun=kode_tahun))

        siswa_baru = Siswa(
            nis=nis,
            nisn=nisn,
            nama=nama,
            nik=nik,
            jenis_kelamin=jenis_kelamin,
            tempat_lahir=tempat_lahir,
            tanggal_lahir=datetime.strptime(tanggal_lahir, '%Y-%m-%d') if tanggal_lahir else None,
            agama=agama,
            tingkat=tingkat,
            kelas_id=kelas_id,
            alamat=alamat,
            no_hp=no_hp,
            email=email,
            tahun_masuk=int(tahun_masuk) if tahun_masuk else None,
            status=status,
            nama_ayah=nama_ayah,
            nama_ibu=nama_ibu,
            no_hp_ortu=no_hp_ortu,
            pekerjaan_ayah=pekerjaan_ayah,
            pekerjaan_ibu=pekerjaan_ibu,
            jenis_pendaftaran=jenis_pendaftaran,
            tanggal_diterima=datetime.strptime(tanggal_diterima, '%Y-%m-%d') if tanggal_diterima else None,
            tahun_diterima=int(tahun_diterima) if tahun_diterima else (int(kode_tahun.split('/')[0]) if kode_tahun else None),
            diterima_di_kelas=diterima_di_kelas,
            sekolah_sd=sekolah_sd,
            tahun_lulus_sd=int(tahun_lulus_sd) if tahun_lulus_sd else None,
            alamat_sekolah_sd=alamat_sekolah_sd,
            sekolah_asal_pindah=sekolah_asal_pindah,
            tahun_pindah=int(tahun_pindah) if tahun_pindah else None,
            alamat_sekolah_pindah=alamat_sekolah_pindah
        )

        db.session.add(siswa_baru)
        db.session.flush()

        if kode_tahun:
            # Hapus dulu riwayat tahun yang lebih kecil dari tahun masuk siswa (jika ada sisa)
            if siswa_baru.tahun_diterima:
                tahun_awal = int(kode_tahun.split('/')[0])
                if siswa_baru.tahun_diterima > tahun_awal:
                    RiwayatKelas.query.filter_by(
                        siswa_id=siswa_baru.id,
                        tahun_pelajaran=kode_tahun
                    ).delete()
            
            # Tambahkan riwayat yang benar saja
            sudah_ada = RiwayatKelas.query.filter_by(
                siswa_id=siswa_baru.id,
                tahun_pelajaran=kode_tahun
            ).first()
            
            if not sudah_ada:
                riwayat_baru = RiwayatKelas(
                    siswa_id=siswa_baru.id,
                    tahun_pelajaran=kode_tahun,
                    tingkat=tingkat,
                    kelas_id=kelas_id
                )
                db.session.add(riwayat_baru)

        db.session.commit()
        flash(f"✅ Data siswa {nama} berhasil ditambahkan.", "success")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

    return render_template('index.html',
        daftar_kelas=daftar_kelas,
        active_page='data_siswa',
        sub_page='form_tambah',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        tahun_dipilih=kode_tahun,
        dasar_tahun=dasar_tahun,
        mode='tambah',
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        }
    )

@data_siswa_bp.route('/ubah/<int:id>', methods=['GET', 'POST'])
def ubah_siswa(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_kelola():
        flash("Anda tidak berhak mengubah data siswa", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')

    tahun_pilihan = TahunPelajaran.query.filter_by(kode=kode_tahun).first()
    if not tahun_pilihan:
        flash("Tahun pelajaran tidak ditemukan!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

    dasar_tahun = get_base_tahun(kode_tahun)
    daftar_kelas = Kelas.query.filter_by(
        tahun_pelajaran=dasar_tahun
    ).order_by(Kelas.jenjang, Kelas.nama_kelas).all()

    if request.method == 'POST':
        nis = request.form.get('nis', '').strip()
        nisn = request.form.get('nisn', '').strip()
        nama = request.form.get('nama', '').strip()
        nik = request.form.get('nik', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        tempat_lahir = request.form.get('tempat_lahir', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir')
        agama = request.form.get('agama', '').strip()
        alamat = request.form.get('alamat', '').strip()
        no_hp = request.form.get('no_hp', '').strip()
        email = request.form.get('email', '').strip().lower()
        tahun_masuk = request.form.get('tahun_masuk') or None
        status = request.form.get('status', 'Aktif').strip()
        nama_ayah = request.form.get('nama_ayah', '').strip()
        nama_ibu = request.form.get('nama_ibu', '').strip()
        no_hp_ortu = request.form.get('no_hp_ortu', '').strip()
        pekerjaan_ayah = request.form.get('pekerjaan_ayah', '').strip()
        pekerjaan_ibu = request.form.get('pekerjaan_ibu', '').strip()

        jenis_pendaftaran = request.form.get('jenis_pendaftaran', '').strip()
        tanggal_diterima = request.form.get('tanggal_diterima')
        tahun_diterima = request.form.get('tahun_diterima') or None
        diterima_di_kelas_id = request.form.get('diterima_di_kelas') or None
        kelas_id_baru = request.form.get('kelas_id') or None
        sekolah_sd = request.form.get('sekolah_sd', '').strip()
        tahun_lulus_sd = request.form.get('tahun_lulus_sd') or None
        alamat_sekolah_sd = request.form.get('alamat_sekolah_sd', '').strip()
        sekolah_asal_pindah = request.form.get('sekolah_asal_pindah', '').strip()
        tahun_pindah = request.form.get('tahun_pindah') or None
        alamat_sekolah_pindah = request.form.get('alamat_sekolah_pindah', '').strip()

        tingkat = siswa.tingkat
        diterima_di_kelas = siswa.diterima_di_kelas
        kelas_id = siswa.kelas_id

        if jenis_pendaftaran == 'baru':
            tingkat = '7'
            if kelas_id_baru:
                kelas_baru = Kelas.query.get(kelas_id_baru)
                if not kelas_baru or kelas_baru.jenjang != '7' or kelas_baru.tahun_pelajaran != kode_tahun:
                    flash("❌ Siswa Baru hanya boleh masuk ke Kelas Tingkat 7 di tahun pelajaran aktif!", "danger")
                    return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))
            if diterima_di_kelas_id:
                kelas_diterima = Kelas.query.get(diterima_di_kelas_id)
                if kelas_diterima and (kelas_diterima.jenjang != '7' or kelas_diterima.tahun_pelajaran != kode_tahun):
                    flash("❌ Kelas yang dipilih tidak sesuai untuk Siswa Baru!", "danger")
                    return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))
                if kelas_diterima:
                    diterima_di_kelas = kelas_diterima.id

        elif jenis_pendaftaran == 'pindahan':
            if kelas_id_baru:
                kelas_baru = Kelas.query.get(kelas_id_baru)
                if kelas_baru and kelas_baru.tahun_pelajaran == kode_tahun:
                    tingkat = kelas_baru.jenjang
                    kelas_id = kelas_baru.id
                else:
                    flash("❌ Kelas yang dipilih tidak valid atau bukan untuk tahun ini!", "danger")
                    return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))
            elif diterima_di_kelas_id:
                kelas_diterima = Kelas.query.get(diterima_di_kelas_id)
                if kelas_diterima and kelas_diterima.tahun_pelajaran == kode_tahun:
                    tingkat = kelas_diterima.jenjang
                    diterima_di_kelas = kelas_diterima.id
                else:
                    flash("❌ Kelas penerima tidak valid atau bukan untuk tahun ini!", "danger")
                    return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))

        if tingkat not in ['7', '8', '9']:
            flash("Tingkat siswa harus 7, 8, atau 9!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))

        if not nis or not nama or not jenis_kelamin or not jenis_pendaftaran or not tanggal_diterima:
            flash("NIS, Nama, Jenis Kelamin, Jenis Pendaftaran, dan Tanggal Diterima wajib diisi!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))

        if nis != siswa.nis and Siswa.query.filter_by(nis=nis).first():
            flash("NIS sudah digunakan!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))

        if nisn and nisn != siswa.nisn and Siswa.query.filter_by(nisn=nisn).first():
            flash("NISN sudah digunakan!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))

        if email and email != siswa.email:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash("Format email tidak valid!", "danger")
                return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))
            if Siswa.query.filter_by(email=email).first():
                flash("Email sudah digunakan!", "danger")
                return redirect(url_for('data_siswa.ubah_siswa', id=id, tahun=kode_tahun))

        siswa.nis = nis
        siswa.nisn = nisn
        siswa.nama = nama
        siswa.nik = nik
        siswa.jenis_kelamin = jenis_kelamin
        siswa.tempat_lahir = tempat_lahir
        siswa.tanggal_lahir = datetime.strptime(tanggal_lahir, '%Y-%m-%d') if tanggal_lahir else None
        siswa.agama = agama
        siswa.tingkat = tingkat
        siswa.kelas_id = kelas_id
        siswa.alamat = alamat
        siswa.no_hp = no_hp
        siswa.email = email
        siswa.tahun_masuk = int(tahun_masuk) if tahun_masuk else None
        siswa.status = status
        siswa.nama_ayah = nama_ayah
        siswa.nama_ibu = nama_ibu
        siswa.no_hp_ortu = no_hp_ortu
        siswa.pekerjaan_ayah = pekerjaan_ayah
        siswa.pekerjaan_ibu = pekerjaan_ibu
        siswa.jenis_pendaftaran = jenis_pendaftaran
        siswa.tanggal_diterima = datetime.strptime(tanggal_diterima, '%Y-%m-%d') if tanggal_diterima else None
        siswa.tahun_diterima = int(tahun_diterima) if tahun_diterima else siswa.tahun_diterima
        siswa.diterima_di_kelas = diterima_di_kelas
        siswa.sekolah_sd = sekolah_sd
        siswa.tahun_lulus_sd = int(tahun_lulus_sd) if tahun_lulus_sd else None
        siswa.alamat_sekolah_sd = alamat_sekolah_sd
        siswa.sekolah_asal_pindah = sekolah_asal_pindah
        siswa.tahun_pindah = int(tahun_pindah) if tahun_pindah else None
        siswa.alamat_sekolah_pindah = alamat_sekolah_pindah

        db.session.commit()
        flash(f"✅ Data siswa diperbarui.", "success")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

    return render_template('index.html',
        siswa=siswa,
        daftar_kelas=daftar_kelas,
        active_page='data_siswa',
        sub_page='form_ubah',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        tahun_dipilih=kode_tahun,
        dasar_tahun=dasar_tahun,
        mode='ubah',
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        }
    )

@data_siswa_bp.route('/kenaikan-kelas', methods=['GET', 'POST'])
def kenaikan_kelas():
    if not session.get('logged_in') or not bisa_kelola():
        flash("Tidak berhak mengakses!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    if request.method == 'POST':
        kode_tahun_lama = request.form.get('tahun_lama', '').strip()
        kode_tahun_baru = request.form.get('tahun_baru', '').strip()

        if not kode_tahun_lama or not kode_tahun_baru:
            flash("Pilih tahun pelajaran lama dan baru!", "danger")
            return redirect(url_for('data_siswa.kenaikan_kelas'))

        daftar_posisi_lama = RiwayatKelas.query.filter_by(tahun_pelajaran=kode_tahun_lama).all()
        jumlah_diproses = 0

        for posisi in daftar_posisi_lama:
            siswa = posisi.siswa
            if siswa.status != 'Aktif':
                continue

            sudah_ada = RiwayatKelas.query.filter_by(
                siswa_id=siswa.id,
                tahun_pelajaran=kode_tahun_baru
            ).first()
            if sudah_ada:
                continue

            if posisi.tingkat == '7':
                tingkat_baru = '8'
            elif posisi.tingkat == '8':
                tingkat_baru = '9'
            elif posisi.tingkat == '9':
                siswa.status = 'Lulus'
                db.session.add(siswa)
                continue
            else:
                continue

            posisi_baru = RiwayatKelas(
                siswa_id=siswa.id,
                tahun_pelajaran=kode_tahun_baru,
                tingkat=tingkat_baru,
                kelas_id=None
            )
            db.session.add(posisi_baru)

            siswa.tingkat = tingkat_baru
            siswa.kelas_id = None
            db.session.add(siswa)
            jumlah_diproses += 1

        db.session.commit()
        flash(f"✅ Kenaikan kelas selesai! Diproses {jumlah_diproses} siswa ({kode_tahun_lama} → {kode_tahun_baru})", "success")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun_baru))

    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    return render_template('index.html',
        active_page='data_siswa',
        sub_page='kenaikan_kelas',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        semua_tahun=semua_tahun,
        user={'jabatan': session.get('jabatan', '')}
    )

@data_siswa_bp.route('/atur-kelas/<int:id>', methods=['POST'])
def atur_kelas(id):
    if not session.get('logged_in') or not bisa_kelola():
        flash("Tidak berhak mengubah kelas!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)
    kode_tahun = request.form.get('tahun_pelajaran', '').strip()
    kelas_id_baru = request.form.get('kelas_id', '').strip()

    if not kode_tahun or not kelas_id_baru:
        flash("Pilih tahun pelajaran dan kelas terlebih dahulu!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

    kelas_baru = Kelas.query.get(kelas_id_baru)
    if not kelas_baru or kelas_baru.tahun_pelajaran != kode_tahun:
        flash("Kelas tidak sesuai dengan tahun pelajaran yang dipilih!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

    posisi = RiwayatKelas.query.filter_by(
        siswa_id=id,
        tahun_pelajaran=kode_tahun
    ).first()

    if posisi:
        posisi.kelas_id = kelas_baru.id
        posisi.tingkat = kelas_baru.jenjang
    else:
        posisi = RiwayatKelas(
            siswa_id=id,
            tahun_pelajaran=kode_tahun,
            tingkat=kelas_baru.jenjang,
            kelas_id=kelas_baru.id
        )
        db.session.add(posisi)

    siswa.tingkat = kelas_baru.jenjang
    siswa.kelas_id = kelas_baru.id

    db.session.commit()
    flash(f"✅ Siswa dipindahkan ke {kelas_baru.nama_kelas} TP {kode_tahun}", "success")
    return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

@data_siswa_bp.route('/hapus/<int:id>', methods=['POST'])
def hapus_siswa(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_hapus():
        flash("Anda tidak berhak menghapus data!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)
    RiwayatKelas.query.filter_by(siswa_id=id).delete()
    if siswa.akun:
        db.session.delete(siswa.akun)
    db.session.delete(siswa)
    db.session.commit()
    flash("Data siswa dan riwayatnya berhasil dihapus!", "success")
    return redirect(url_for('data_siswa.halaman_daftar_siswa'))

@data_siswa_bp.route('/detail/<int:id>')
def detail_siswa(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_lihat():
        flash("Anda tidak berhak melihat data ini!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)
    riwayat_kelas = RiwayatKelas.query.filter_by(siswa_id=id).order_by(RiwayatKelas.tahun_pelajaran.desc()).all()
    return render_template('index.html',
        siswa=siswa,
        riwayat_kelas=riwayat_kelas,
        active_page='data_siswa',
        sub_page='detail',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        bisa_buat_akun=bisa_buat_akun(),
        bisa_kelola=bisa_kelola(),
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        }
    )

@data_siswa_bp.route('/buat-akun/<int:id>', methods=['GET', 'POST'])
def buat_akun_siswa(id):
    if not session.get('logged_in') or not bisa_buat_akun():
        flash("Anda tidak memiliki hak akses untuk membuat akun siswa!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)
    if siswa.akun:
        flash("Siswa sudah memiliki akun!", "warning")
        return redirect(url_for('data_siswa.detail_siswa', id=id))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username dan Password wajib diisi!", "danger")
            return redirect(url_for('data_siswa.buat_akun_siswa', id=id))

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan!", "danger")
            return redirect(url_for('data_siswa.buat_akun_siswa', id=id))

        akun_baru = User(
            username=username,
            siswa_id=siswa.id,
            jabatan="Siswa"
        )
        akun_baru.set_password(password)

        db.session.add(akun_baru)
        db.session.commit()
        flash("Akun berhasil dibuat!", "success")
        return redirect(url_for('data_siswa.detail_siswa', id=id))

    return render_template('index.html',
        siswa=siswa,
        active_page='data_siswa',
        sub_page='buat_akun',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        }
    )

@data_siswa_bp.route('/ubah-password/<int:id>', methods=['GET', 'POST'])
def ubah_password_siswa(id):
    if not session.get('logged_in') or not bisa_buat_akun():
        flash("Anda tidak memiliki hak akses untuk mengubah password siswa!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)
    if not siswa.akun:
        flash("Siswa belum memiliki akun!", "warning")
        return redirect(url_for('data_siswa.detail_siswa', id=id))

    if request.method == 'POST':
        password_baru = request.form.get('password_baru', '').strip()
        if not password_baru:
            flash("Password baru tidak boleh kosong!", "danger")
            return redirect(url_for('data_siswa.ubah_password_siswa', id=id))

        siswa.akun.set_password(password_baru)
        db.session.commit()
        flash("Password berhasil diubah!", "success")
        return redirect(url_for('data_siswa.detail_siswa', id=id))

    return render_template('index.html',
        siswa=siswa,
        active_page='data_siswa',
        sub_page='ubah_password',
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        }
    )

@data_siswa_bp.route('/ubah-status/<int:id>', methods=['GET', 'POST'])
def ubah_status(id):
    if not session.get('logged_in') or not bisa_kelola():
        flash("Anda tidak memiliki hak akses untuk mengubah status siswa", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.get_or_404(id)

    if request.method == 'POST':
        status_baru = request.form.get('status', '').strip()

        if status_baru not in ['Aktif', 'Non Aktif']:
            flash("Status tidak valid", "danger")
            return redirect(url_for('data_siswa.halaman_daftar_siswa'))

        if status_baru == 'Non Aktif':
            if siswa.kelas_id is not None:
                flash("❌ Harap keluarkan siswa dari rombel terlebih dahulu!", "warning")
                return redirect(url_for('data_siswa.halaman_daftar_siswa'))

            jenis = request.form.get('jenis_non_aktif', '').strip()
            tanggal = request.form.get('tanggal_non_aktif', '').strip()
            alasan = request.form.get('alasan_non_aktif', '').strip()
            sekolah_tujuan = request.form.get('sekolah_tujuan', '').strip()

            if not jenis or not tanggal or not alasan:
                flash("Tanggal dan alasan wajib diisi!", "danger")
                return redirect(url_for('data_siswa.halaman_daftar_siswa'))

            if jenis == 'Pindah' and not sekolah_tujuan:
                flash("Nama sekolah tujuan wajib diisi!", "danger")
                return redirect(url_for('data_siswa.halaman_daftar_siswa'))

            siswa.status = 'Non Aktif'
            siswa.jenis_non_aktif = jenis
            siswa.tanggal_non_aktif = datetime.strptime(tanggal, '%Y-%m-%d')
            siswa.alasan_non_aktif = alasan
            siswa.sekolah_tujuan = sekolah_tujuan if jenis == 'Pindah' else None
            flash("✅ Status berhasil diubah menjadi Non Aktif", "success")

        elif status_baru == 'Aktif':
            siswa.status = 'Aktif'
            siswa.jenis_non_aktif = None
            siswa.tanggal_non_aktif = None
            siswa.alasan_non_aktif = None
            siswa.sekolah_tujuan = None
            flash("✅ Status berhasil diaktifkan kembali", "success")

        db.session.commit()
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    return render_template(
        'ubah_status.html',
        siswa=siswa,
        active_page='data_siswa',
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

@data_siswa_bp.route('/perbaiki-data-lama')
def perbaiki_data_lama():
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
    if not tahun_aktif:
        return "❌ Atur Tahun Pelajaran aktif terlebih dahulu!"

    diperbaiki = 0
    semua_siswa = Siswa.query.filter_by(status='Aktif').all()

    for siswa in semua_siswa:
        ubah = False
        if siswa.kelas_id:
            kelas = Kelas.query.get(siswa.kelas_id)
            if kelas and siswa.tingkat != kelas.jenjang:
                siswa.tingkat = kelas.jenjang
                ubah = True
        elif not siswa.tingkat:
            siswa.tingkat = '7'
            ubah = True

        if ubah:
            diperbaiki += 1

    db.session.commit()
    return f"✅ Selesai! Diperbaiki {diperbaiki} siswa. Kolom tingkat sudah terisi semua."