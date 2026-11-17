from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime
import re
from sqlalchemy import or_
from models import (
    db, Siswa, Kelas, User, TahunPelajaran,
    RiwayatKelas, RiwayatSemester,
    RiwayatPembayaran, TagihanSiswa,
    PengajuanPembayaran, DetailPengajuanPembayaran
)
from flask import current_app

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

def format_tahun_pelajaran(kode_tp):
    """Ubah '2026/2027-1' → '2026/2027-Ganjil', '2026/2027-2' → '2026/2027-Genap'"""
    if not kode_tp:
        return ""
    bagian = kode_tp.split('-')
    if len(bagian) == 2:
        tahun = bagian[0]
        angka = bagian[1]
        if angka == '1':
            return f"{tahun}-Ganjil"
        elif angka == '2':
            return f"{tahun}-Genap"
    return kode_tp  # fallback jika format lain

def simpan_keaktifan_riwayat(siswa, tanggal_non_aktif, jenis):
    """
    Mencatat status Pindah/Berhenti pada semester sesuai tanggal.
    Tidak mengubah status_akhir dan tidak menimpa riwayat semester sebelumnya.
    """

    # Cari periode akademik berdasarkan tanggal kejadian
    periode = TahunPelajaran.query.filter(
        TahunPelajaran.tanggal_mulai <= tanggal_non_aktif,
        TahunPelajaran.tanggal_selesai >= tanggal_non_aktif
    ).all()

    if len(periode) != 1:
        raise ValueError(
            "Tanggal nonaktif tidak berada dalam tepat satu periode "
            "tahun pelajaran. Periksa kalender tahun pelajaran."
        )

    tp = periode[0]
    dasar_tahun = tp.kode.rsplit("-", 1)[0]
    semester = tp.semester

    # Pastikan siswa memang memiliki riwayat kelas pada periode tersebut
    kode_periode = tp.kode

    riwayat_kelas = RiwayatKelas.query.filter_by(
        siswa_id=siswa.id,
        tahun_pelajaran=kode_periode
    ).first()

    if not riwayat_kelas:
        raise ValueError(
            "Riwayat kelas siswa pada periode tersebut tidak ditemukan."
        )

    riwayat = RiwayatSemester.query.filter_by(
        siswa_id=siswa.id,
        tahun_pelajaran=dasar_tahun,
        semester=semester
    ).first()

    if riwayat:
        # Hanya ubah keaktifan semester tempat kejadian berlangsung
        riwayat.keaktifan = jenis

    else:
        kelas = db.session.get(Kelas, riwayat_kelas.kelas_id) \
            if riwayat_kelas.kelas_id else None

        riwayat = RiwayatSemester(
            siswa_id=siswa.id,
            tahun_pelajaran=dasar_tahun,
            semester=semester,
            status_awal="Lanjutan",
            status_akhir=None,
            keaktifan=jenis,
            tingkat_saat_itu=riwayat_kelas.tingkat,
            kelas_nama=kelas.nama_kelas if kelas else None
        )

        db.session.add(riwayat)

    # Jika kejadian terjadi di semester 2, pastikan semester 1
    # tercatat Aktif apabila siswa memang memiliki riwayat kelas di sana.
    if semester == 2:
        riwayat_ganjil = RiwayatSemester.query.filter_by(
            siswa_id=siswa.id,
            tahun_pelajaran=dasar_tahun,
            semester=1
        ).first()

        kelas_ganjil = RiwayatKelas.query.filter_by(
            siswa_id=siswa.id,
            tahun_pelajaran=f"{dasar_tahun}-1"
        ).first()

        if not riwayat_ganjil and kelas_ganjil:
            kelas = db.session.get(Kelas, kelas_ganjil.kelas_id) \
                if kelas_ganjil.kelas_id else None

            db.session.add(RiwayatSemester(
                siswa_id=siswa.id,
                tahun_pelajaran=dasar_tahun,
                semester=1,
                status_awal="Lanjutan",
                status_akhir=None,
                keaktifan="Aktif",
                tingkat_saat_itu=kelas_ganjil.tingkat,
                kelas_nama=kelas.nama_kelas if kelas else None
            ))

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

    today_date = datetime.now().strftime('%d %B %Y')

    # ✅ Ambil tahun yang dipilih
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    print(f"[DEBUG] kode_tahun yang dicari: '{kode_tahun}'")
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
        # Ambil hanya riwayat yang benar-benar tercatat
        # pada tahun pelajaran yang sedang dipilih.
        riwayat_tercatat = (
            RiwayatKelas.query
            .filter_by(tahun_pelajaran=kode_tahun)
            .all()
        )

        siswa_tercatat = {
            r.siswa_id: r
            for r in riwayat_tercatat
        }

        id_siswa_di_tahun_ini = list(siswa_tercatat.keys())

        # Statistik hanya berdasarkan siswa yang memiliki riwayat
        # pada tahun pelajaran terpilih.
        total = len(id_siswa_di_tahun_ini)

        if id_siswa_di_tahun_ini:
            aktif = Siswa.query.filter(
                Siswa.id.in_(id_siswa_di_tahun_ini),
                Siswa.status == 'Aktif'
            ).count()

            lulus = Siswa.query.filter(
                Siswa.id.in_(id_siswa_di_tahun_ini),
                Siswa.status == 'Lulus'
            ).count()

            pindah = Siswa.query.filter(
                Siswa.id.in_(id_siswa_di_tahun_ini),
                Siswa.status == 'Pindah'
            ).count()

        # Tampilkan hanya siswa yang memiliki riwayat
        # pada tahun pelajaran yang dipilih.
        daftar_dengan_posisi = []

        for riwayat in riwayat_tercatat:
            siswa = riwayat.siswa

            if not siswa or siswa.status != 'Aktif':
                continue

            daftar_dengan_posisi.append({
                'siswa': siswa,
                'tingkat': riwayat.tingkat,
                'kelas': (
                    riwayat.kelas.nama_kelas
                    if riwayat.kelas else '-'
                )
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
        'today_date': today_date,
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

    # Ambil tahun pelajaran — dari form atau dari sesi
    kode_tahun = request.form.get('tahun_pelajaran') or session.get('tahun_pelajaran')
    print(f"[DEBUG] kode_tahun diterima dari form: '{kode_tahun}'")

    if not kode_tahun:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        if not tahun_aktif:
            flash("Tidak ada Tahun Pelajaran yang aktif!", "danger")
            return redirect(url_for('data_siswa.halaman_daftar_siswa'))
        kode_tahun = tahun_aktif.kode

    dasar_tahun = get_base_tahun(kode_tahun)
    print(f"[DEBUG] dasar_tahun dipakai untuk kelas: '{dasar_tahun}'")

    tahun_pilihan = TahunPelajaran.query.filter_by(kode=kode_tahun).first()
    if not tahun_pilihan:
        flash("Tahun pelajaran tidak ditemukan!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    if not tahun_pilihan.aktif:
        flash("Tahun pelajaran ini TIDAK AKTIF — tidak boleh menambah siswa!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    daftar_kelas = Kelas.query.filter_by(
        tahun_pelajaran=dasar_tahun
    ).order_by(Kelas.jenjang, Kelas.nama_kelas).all()
    print(f"[DEBUG] Jumlah kelas ditemukan: {len(daftar_kelas)}")

    if request.method == 'POST':
        # Baca SEMUA field dari form
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
        status = request.form.get('status', 'Aktif').strip()
        nama_ayah = request.form.get('nama_ayah', '').strip()
        nama_ibu = request.form.get('nama_ibu', '').strip()
        no_hp_ortu = request.form.get('no_hp_ortu', '').strip()
        pekerjaan_ayah = request.form.get('pekerjaan_ayah', '').strip()
        pekerjaan_ibu = request.form.get('pekerjaan_ibu', '').strip()
        jenis_pendaftaran = request.form.get('jenis_pendaftaran', '').strip()
        tanggal_diterima = request.form.get('tanggal_diterima')
        tahun_diterima = request.form.get('tahun_diterima') or None

        # Tahun diterima selalu mengikuti tanggal diterima
        tanggal_obj = datetime.strptime(tanggal_diterima, '%Y-%m-%d') if tanggal_diterima else None
        tahun_diterima = tanggal_obj.year if tanggal_obj else None
        sekolah_sd = request.form.get('sekolah_sd', '').strip()
        tahun_lulus_sd = request.form.get('tahun_lulus_sd') or None
        alamat_sekolah_sd = request.form.get('alamat_sekolah_sd', '').strip()
        sekolah_asal_pindah = request.form.get('sekolah_asal_pindah', '').strip()
        tahun_pindah = request.form.get('tahun_pindah') or None
        alamat_sekolah_pindah = request.form.get('alamat_sekolah_pindah', '').strip()

        print(f"[DEBUG] Jenis: {jenis_pendaftaran} | NIS: {nis} | Nama: {nama}")

        # ==========================================
        # PENENTUAN TINGKAT PENERIMAAN
        # ROMBEL TIDAK DITENTUKAN SAAT PENDAFTARAN
        # ==========================================

        tingkat_form = request.form.get('tingkat', '').strip()

        if jenis_pendaftaran == 'baru':
            # Siswa baru otomatis diterima di tingkat 7
            tingkat = '7'

        elif jenis_pendaftaran == 'pindahan':
            # Siswa pindahan harus menentukan tingkat penerimaan
            if tingkat_form not in ['7', '8', '9']:
                flash("Pilih tingkat penerimaan siswa pindahan!", "danger")
                return redirect(url_for(
                    'data_siswa.tambah_siswa'
                ))

            tingkat = tingkat_form

        else:
            flash("Jenis pendaftaran tidak valid!", "danger")
            return redirect(url_for(
                'data_siswa.tambah_siswa'
            ))

        # Tidak ada penempatan rombel saat pendaftaran
        kelas_id = None

        # Kolom lama dipertahankan sementara untuk kompatibilitas
        # tetapi tidak lagi digunakan untuk menyimpan ID rombel
        diterima_di_kelas = None

        # Validasi wajib
        if not nis or not nama or not jenis_kelamin or not jenis_pendaftaran or not tanggal_diterima:
            flash("NIS, Nama, Jenis Kelamin, Jenis Pendaftaran, dan Tanggal Diterima wajib diisi!", "danger")
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

        if Siswa.query.filter_by(nis=nis).first():
            flash(f"NIS '{nis}' sudah terdaftar!", "danger")
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

        if nisn and Siswa.query.filter_by(nisn=nisn).first():
            flash(f"NISN '{nisn}' sudah terdaftar!", "danger")
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

        if not email:
            email = f"siswa-{nis}@sekolah.sch.id"
        else:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash("Format email tidak valid!", "danger")
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
            if Siswa.query.filter_by(email=email).first():
                flash("Email sudah digunakan!", "danger")
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

        # Buat objek siswa baru
        try:
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
                status=status,
                nama_ayah=nama_ayah,
                nama_ibu=nama_ibu,
                no_hp_ortu=no_hp_ortu,
                pekerjaan_ayah=pekerjaan_ayah,
                pekerjaan_ibu=pekerjaan_ibu,
                jenis_pendaftaran=jenis_pendaftaran,
                tanggal_diterima=tanggal_obj,
                tahun_diterima=tahun_diterima,
                diterima_di_kelas=diterima_di_kelas,
                sekolah_sd=sekolah_sd,
                tahun_lulus_sd=int(tahun_lulus_sd) if tahun_lulus_sd else None,
                alamat_sekolah_sd=alamat_sekolah_sd,
                sekolah_asal_pindah=sekolah_asal_pindah,
                tahun_pindah=int(tahun_pindah) if tahun_pindah else None,
                alamat_sekolah_pindah=alamat_sekolah_pindah
            )

            db.session.add(siswa_baru)
            db.session.flush()  # Dapatkan ID siswa

            # Tambahkan riwayat kelas
            sudah_ada = RiwayatKelas.query.filter_by(
                siswa_id=siswa_baru.id,
                tahun_pelajaran=kode_tahun
            ).first()

            if not sudah_ada:
                riwayat_baru = RiwayatKelas(
                    siswa_id=siswa_baru.id,
                    tahun_pelajaran=kode_tahun,
                    tingkat=tingkat,
                    kelas_id=None
                )
                db.session.add(riwayat_baru)
                print(f"[DEBUG] Riwayat dibuat: TP={kode_tahun}, Tingkat={tingkat}")

            db.session.commit()
            print(f"[DEBUG] ✅ Siswa tersimpan! ID={siswa_baru.id}")
            flash(f"✅ Data siswa {nama} berhasil ditambahkan.", "success")
            return redirect(url_for('data_siswa.halaman_daftar_siswa', tahun=kode_tahun))

        except Exception as e:
            db.session.rollback()
            print(f"[DEBUG] ❌ ERROR saat simpan: {str(e)}")
            flash(f"Gagal menyimpan: {str(e)}", "danger")
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

    # GET request — tampilkan form
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

@data_siswa_bp.route('/ubah/<string:public_id>', methods=['GET', 'POST'])
def ubah_siswa(public_id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_kelola():
        flash("Anda tidak berhak mengubah data siswa", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()
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
        tanggal_obj = datetime.strptime(tanggal_diterima, '%Y-%m-%d') if tanggal_diterima else None
        tahun_diterima = tanggal_obj.year if tanggal_obj else None
        sekolah_sd = request.form.get('sekolah_sd', '').strip()
        tahun_lulus_sd = request.form.get('tahun_lulus_sd') or None
        alamat_sekolah_sd = request.form.get('alamat_sekolah_sd', '').strip()
        sekolah_asal_pindah = request.form.get('sekolah_asal_pindah', '').strip()
        tahun_pindah = request.form.get('tahun_pindah') or None
        alamat_sekolah_pindah = request.form.get('alamat_sekolah_pindah', '').strip()

        # ==========================================
        # TINGKAT PENERIMAAN
        # TANPA PENENTUAN ROMBEL
        # ==========================================

        tingkat_form = request.form.get('tingkat', '').strip()

        if jenis_pendaftaran == 'baru':
            tingkat = '7'

        elif jenis_pendaftaran == 'pindahan':
            if tingkat_form not in ['7', '8', '9']:
                flash("Pilih tingkat penerimaan siswa pindahan!", "danger")
                return redirect(url_for(
                    'data_siswa.ubah_siswa',
                    public_id=public_id,
                    tahun=kode_tahun
                ))

            tingkat = tingkat_form

        else:
            flash("Jenis pendaftaran tidak valid!", "danger")
            return redirect(url_for(
                'data_siswa.ubah_siswa',
                public_id=public_id,
                tahun=kode_tahun
            ))

        # Pertahankan penempatan rombel yang sudah ada,
        # selama masih sesuai dengan tingkat siswa.
        kelas_id = siswa.kelas_id

        if kelas_id:
            kelas_terpasang = Kelas.query.get(kelas_id)

            if (
                not kelas_terpasang
                or str(kelas_terpasang.jenjang) != str(tingkat)
            ):
                kelas_id = None

        # Kolom lama tidak lagi digunakan
        diterima_di_kelas = None

        if tingkat not in ['7', '8', '9']:
            flash("Tingkat siswa harus 7, 8, atau 9!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', public_id=public_id, tahun=kode_tahun))

        if not nis or not nama or not jenis_kelamin or not jenis_pendaftaran or not tanggal_diterima:
            flash("NIS, Nama, Jenis Kelamin, Jenis Pendaftaran, dan Tanggal Diterima wajib diisi!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', public_id=public_id, tahun=kode_tahun))

        if nis != siswa.nis and Siswa.query.filter_by(nis=nis).first():
            flash("NIS sudah digunakan!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', public_id=public_id, tahun=kode_tahun))

        if nisn and nisn != siswa.nisn and Siswa.query.filter_by(nisn=nisn).first():
            flash("NISN sudah digunakan!", "danger")
            return redirect(url_for('data_siswa.ubah_siswa', public_id=public_id, tahun=kode_tahun))

        if email and email != siswa.email:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash("Format email tidak valid!", "danger")
                return redirect(url_for('data_siswa.ubah_siswa', public_id=public_id, tahun=kode_tahun))
            if Siswa.query.filter_by(email=email).first():
                flash("Email sudah digunakan!", "danger")
                return redirect(url_for('data_siswa.ubah_siswa', public_id=public_id, tahun=kode_tahun))

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
        siswa.tanggal_diterima = tanggal_obj
        siswa.tahun_diterima = tahun_diterima
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


@data_siswa_bp.route('/atur-kelas/<string:public_id>', methods=['POST'])
def atur_kelas(public_id):
    if not session.get('logged_in') or not bisa_kelola():
        flash("Tidak berhak mengubah kelas!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    # Cari siswa menggunakan public_id untuk URL
    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()

    kode_tahun = request.form.get('tahun_pelajaran', '').strip()
    kelas_id_baru = request.form.get('kelas_id', '').strip()

    if not kode_tahun or not kelas_id_baru:
        flash("Pilih tahun pelajaran dan kelas terlebih dahulu!", "danger")
        return redirect(url_for(
            'data_siswa.halaman_daftar_siswa',
            tahun=kode_tahun
        ))

    # Validasi ID kelas
    try:
        kelas_id_baru = int(kelas_id_baru)
    except (TypeError, ValueError):
        flash("ID kelas tidak valid!", "danger")
        return redirect(url_for(
            'data_siswa.halaman_daftar_siswa',
            tahun=kode_tahun
        ))

    kelas_baru = db.session.get(Kelas, kelas_id_baru)

    if not kelas_baru or kelas_baru.tahun_pelajaran != kode_tahun:
        flash("Kelas tidak sesuai dengan tahun pelajaran yang dipilih!", "danger")
        return redirect(url_for(
            'data_siswa.halaman_daftar_siswa',
            tahun=kode_tahun
        ))

    # Cari riwayat menggunakan ID INTEGER siswa
    posisi = RiwayatKelas.query.filter_by(
        siswa_id=siswa.id,
        tahun_pelajaran=kode_tahun
    ).first()

    if posisi:
        posisi.kelas_id = kelas_baru.id
        posisi.tingkat = kelas_baru.jenjang
    else:
        posisi = RiwayatKelas(
            siswa_id=siswa.id,  # ✅ ID INTEGER SISWA
            tahun_pelajaran=kode_tahun,
            tingkat=kelas_baru.jenjang,
            kelas_id=kelas_baru.id
        )
        db.session.add(posisi)

    # Perbarui posisi siswa saat ini
    siswa.tingkat = kelas_baru.jenjang
    siswa.kelas_id = kelas_baru.id

    try:
        db.session.commit()
        flash(
            f"✅ Siswa berhasil ditempatkan di {kelas_baru.nama_kelas} TP {kode_tahun}",
            "success"
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Gagal mengatur kelas siswa ID %s", siswa.id
        )
        flash("Gagal menyimpan penempatan kelas. Periksa log server.", "danger")

    return redirect(url_for(
        'data_siswa.halaman_daftar_siswa',
        tahun=kode_tahun
    ))


@data_siswa_bp.route('/hapus/<string:public_id>', methods=['POST'])
def hapus_siswa(public_id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if not bisa_hapus():
        flash("Anda tidak berhak menghapus data!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()

    try:
        # ==========================================
        # 1. PERIKSA RIWAYAT PEMBAYARAN
        # ==========================================
        ada_riwayat_bayar = (
            RiwayatPembayaran.query
            .join(TagihanSiswa, RiwayatPembayaran.tagihan_id == TagihanSiswa.id)
            .filter(TagihanSiswa.siswa_id == siswa.id)
            .first()
        )

        if ada_riwayat_bayar:
            flash(
                "Siswa tidak dapat dihapus karena sudah memiliki "
                "riwayat pembayaran. Pertahankan data keuangan "
                "dan ubah status siswa menjadi nonaktif jika diperlukan.",
                "warning"
            )
            return redirect(url_for('data_siswa.halaman_daftar_siswa'))

        # ==========================================
        # 2. PERIKSA DETAIL PENGAJUAN PEMBAYARAN
        # ==========================================
        ada_detail_pengajuan = (
            DetailPengajuanPembayaran.query
            .join(TagihanSiswa, DetailPengajuanPembayaran.tagihan_id == TagihanSiswa.id)
            .filter(TagihanSiswa.siswa_id == siswa.id)
            .first()
        )

        if ada_detail_pengajuan:
            flash(
                "Siswa tidak dapat dihapus karena tagihannya "
                "masih terhubung dengan pengajuan pembayaran.",
                "warning"
            )
            return redirect(url_for('data_siswa.halaman_daftar_siswa'))

        # ==========================================
        # 3. PERIKSA PENGAJUAN PEMBAYARAN SISWA
        # ==========================================
        ada_pengajuan = (
            PengajuanPembayaran.query
            .filter_by(siswa_id=siswa.id)
            .first()
        )

        if ada_pengajuan:
            flash(
                "Siswa tidak dapat dihapus karena masih memiliki "
                "riwayat pengajuan pembayaran.",
                "warning"
            )
            return redirect(url_for('data_siswa.halaman_daftar_siswa'))

        # ==========================================
        # 4. HAPUS RIWAYAT KELAS
        # ==========================================
        RiwayatKelas.query.filter_by(siswa_id=siswa.id).delete(
            synchronize_session=False
        )

        # ==========================================
        # 5. HAPUS AKUN JIKA ADA
        # ==========================================
        if siswa.akun:
            db.session.delete(siswa.akun)

        # ==========================================
        # 6. HAPUS SISWA
        # Tagihan tanpa relasi keuangan akan ikut
        # terhapus melalui cascade delete-orphan.
        # ==========================================
        db.session.delete(siswa)

        db.session.commit()

        flash(
            "Data siswa, riwayat kelas, dan tagihan yang aman "
            "dihapus berhasil dihapus!",
            "success"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(
            "Gagal menghapus siswa ID %s", siswa.id
        )
        flash(
            "Terjadi kesalahan saat menghapus data siswa. "
            "Silakan periksa log server.",
            "danger"
        )

    return redirect(url_for('data_siswa.halaman_daftar_siswa'))

@data_siswa_bp.route('/detail/<string:public_id>')
def detail_siswa(public_id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    if not bisa_lihat():
        flash("Anda tidak berhak melihat data ini!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))
    
    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()

    # ========== DEBUG: CEK RIWAYAT SISWA ==========
    print("=" * 50)
    print(f"[DETAIL SISWA] ID: {siswa.id} | Public ID: {siswa.public_id} | Nama: {siswa.nama}")
    # ==============================================

    # === AMBIL & NORMALISASI KODE TAHUN ===
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    
    def normalisasi_tahun(kode):
        if not kode:
            return None
        kode = kode.strip()
        if ' Ganjil' in kode:
            return kode.replace(' Ganjil', '-1')
        if ' Genap' in kode:
            return kode.replace(' Genap', '-2')
        return kode
    
    kode_cari = normalisasi_tahun(kode_tahun)

    # ========== DEBUG ==========
    print(f"[DETAIL SISWA] kode_tahun mentah: {kode_tahun}")
    print(f"[DETAIL SISWA] kode_cari dinormalisasi: {kode_cari}")
    # ===========================

    if not kode_cari:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_cari = tahun_aktif.kode if tahun_aktif else None
    
    tahun_dipilih_formatted = format_tahun_pelajaran(kode_cari) if kode_cari else None

    riwayat_tahun_ini = None
    if kode_cari:
        riwayat_tahun_ini = RiwayatKelas.query.filter_by(
            siswa_id=siswa.id,
            tahun_pelajaran=kode_cari
        ).first()

    # ========== DEBUG ==========
    print(f"[DETAIL SISWA] riwayat_tahun_ini ditemukan: {riwayat_tahun_ini is not None}")
    # ===========================

    kelas_sekarang = None
    kelas_tahun_formatted = None
    if riwayat_tahun_ini and riwayat_tahun_ini.kelas:
        kelas_sekarang = riwayat_tahun_ini.kelas
        kelas_sekarang.jenjang = riwayat_tahun_ini.tingkat
        kelas_tahun_formatted = tahun_dipilih_formatted
    else:
        riwayat_terakhir = RiwayatKelas.query.filter_by(siswa_id=siswa.id)\
            .order_by(RiwayatKelas.tahun_pelajaran.desc())\
            .first()
        if riwayat_terakhir and riwayat_terakhir.kelas:
            kelas_sekarang = riwayat_terakhir.kelas
            kelas_sekarang.jenjang = riwayat_terakhir.tingkat
            kelas_tahun_formatted = format_tahun_pelajaran(riwayat_terakhir.tahun_pelajaran)
    
    # Ambil SEMUA riwayat kelas siswa
    riwayat_kelas = RiwayatKelas.query.filter_by(siswa_id=siswa.id)\
        .order_by(RiwayatKelas.tahun_pelajaran.asc()).all()

    # ========== DEBUG ==========
    print(f"[DETAIL SISWA] Jumlah riwayat_kelas dari DB: {len(riwayat_kelas)}")
    for r in riwayat_kelas:
        print(f"   -> TP: {r.tahun_pelajaran} | Kelas: {r.kelas.nama_kelas if r.kelas else 'TIDAK ADA/NULL'} | Tingkat: {r.tingkat}")
    # ===========================

    
    
    riwayat_semester = []

    for rw in riwayat_kelas:
        # Normalisasi kode tahun dan semester.
        bagian = rw.tahun_pelajaran.rsplit('-', 1)

        if len(bagian) == 2 and bagian[1] in ['1', '2']:
            dasar_tahun = bagian[0]
            nomor_semester = int(bagian[1])
        else:
            dasar_tahun = rw.tahun_pelajaran
            nomor_semester = None

        # Jika RiwayatKelas belum menyimpan kode semester,
        # gunakan semester aktif yang sesuai dengan konteks data.
        if nomor_semester is None and kode_cari:
            bagian_pilihan = kode_cari.rsplit('-', 1)

            if len(bagian_pilihan) == 2 and bagian_pilihan[1] in ['1', '2']:
                if bagian_pilihan[0] == dasar_tahun:
                    nomor_semester = int(bagian_pilihan[1])

        riwayat_db = None

        if nomor_semester:
            riwayat_db = RiwayatSemester.query.filter_by(
                siswa_id=siswa.id,
                tahun_pelajaran=dasar_tahun,
                semester=nomor_semester
            ).first()

        print(
            f"[CEK RIWAYAT] Siswa={siswa.id} | "
            f"TP={rw.tahun_pelajaran} | "
            f"Dasar={dasar_tahun} | "
            f"Semester={nomor_semester} | "
            f"Ditemukan={riwayat_db is not None}"
        )

        # Status awal semester
        status_awal = (
            riwayat_db.status_awal
            if riwayat_db and riwayat_db.status_awal
            else "Lanjutan"
        )

        # Status akhir semester
        status_akhir = (
            riwayat_db.status_akhir
            if riwayat_db and riwayat_db.status_akhir
            else ""
        )

        # Keaktifan:
        # Jika ada catatan database, gunakan nilai tersebut.
        # Jika belum ada catatan, siswa dianggap Aktif karena
        # memiliki RiwayatKelas pada semester ini.
        if riwayat_db and riwayat_db.keaktifan:
            keaktifan = riwayat_db.keaktifan
        else:
            keaktifan = "Aktif"

        tingkat_saat_itu = (
            riwayat_db.tingkat_saat_itu
            if riwayat_db and riwayat_db.tingkat_saat_itu
            else rw.tingkat
        )

        kelas_nama = (
            riwayat_db.kelas_nama
            if riwayat_db and riwayat_db.kelas_nama
            else (rw.kelas.nama_kelas if rw.kelas else None)
        )

        riwayat_semester.append({
            "tahun_pelajaran": rw.tahun_pelajaran,
            "status_awal": status_awal,
            "status_akhir": status_akhir,
            "tingkat_saat_itu": tingkat_saat_itu,
            "kelas_nama": kelas_nama,
            "keaktifan": keaktifan
        })

    # ========== DEBUG ==========
    print(f"[DETAIL SISWA] Jumlah riwayat_semester dikirim ke template: {len(riwayat_semester)}")
    print("=" * 50)
    # ===========================

    return render_template('index.html',
        siswa=siswa,
        riwayat_semester=riwayat_semester,
        kelas_sekarang=kelas_sekarang,
        tahun_dipilih_formatted=tahun_dipilih_formatted,
        kelas_sekarang_tahun_formatted=kelas_tahun_formatted,
        tahun_dipilih=kode_cari,
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

@data_siswa_bp.route('/buat-akun/<string:public_id>', methods=['GET', 'POST'])
def buat_akun_siswa(public_id):
    if not session.get('logged_in') or not bisa_buat_akun():
        flash("Anda tidak memiliki hak akses untuk membuat akun siswa!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()
    if siswa.akun:
        flash("Siswa sudah memiliki akun!", "warning")
        return redirect(url_for('data_siswa.detail_siswa', public_id=public_id))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username dan Password wajib diisi!", "danger")
            return redirect(url_for('data_siswa.buat_akun_siswa', public_id=public_id))

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan!", "danger")
            return redirect(url_for('data_siswa.buat_akun_siswa', public_id=public_id))

        akun_baru = User(
            username=username,
            siswa_id=siswa.id,
            jabatan="Siswa"
        )
        akun_baru.set_password(password)

        db.session.add(akun_baru)
        db.session.commit()
        flash("Akun berhasil dibuat!", "success")
        return redirect(url_for('data_siswa.detail_siswa', public_id=public_id))

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

@data_siswa_bp.route('/ubah-password/<string:public_id>', methods=['GET', 'POST'])
def ubah_password_siswa(public_id):
    if not session.get('logged_in') or not bisa_buat_akun():
        flash("Anda tidak memiliki hak akses untuk mengubah password siswa!", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()
    if not siswa.akun:
        flash("Siswa belum memiliki akun!", "warning")
        return redirect(url_for('data_siswa.detail_siswa', public_id=public_id))

    if request.method == 'POST':
        password_baru = request.form.get('password_baru', '').strip()
        if not password_baru:
            flash("Password baru tidak boleh kosong!", "danger")
            return redirect(url_for('data_siswa.ubah_password_siswa', public_id=public_id))

        siswa.akun.set_password(password_baru)
        db.session.commit()
        flash("Password berhasil diubah!", "success")
        return redirect(url_for('data_siswa.detail_siswa', public_id=public_id))

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

@data_siswa_bp.route('/ubah-status/<string:public_id>', methods=['GET', 'POST'])
def ubah_status(public_id):
    if not session.get('logged_in') or not bisa_kelola():
        flash("Anda tidak memiliki hak akses untuk mengubah status siswa", "danger")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    siswa = Siswa.query.filter_by(
        public_id=public_id
    ).first_or_404()

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

            tanggal_obj = datetime.strptime(tanggal, '%Y-%m-%d').date()

            simpan_keaktifan_riwayat(
                siswa=siswa,
                tanggal_non_aktif=tanggal_obj,
                jenis=jenis
            )

            siswa.status = 'Non Aktif'
            siswa.jenis_non_aktif = jenis
            siswa.tanggal_non_aktif = tanggal_obj
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

@data_siswa_bp.route('/isi-riwayat-lama')
def isi_riwayat_lama():
    return (
        "Fitur pengisian riwayat otomatis telah dinonaktifkan. "
        "Riwayat siswa hanya dibuat melalui proses pendaftaran, "
        "lanjut semester, dan kenaikan kelas."
    ), 410