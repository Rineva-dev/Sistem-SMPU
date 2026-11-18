from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, Kelas, Guru, TahunPelajaran, User, Siswa, RiwayatKelas, RiwayatSemester, MataPelajaran, PengaturanMapelKelas, JadwalPelajaran
from functools import wraps

kelas_bp = Blueprint('data_kelas', __name__, url_prefix='/kelas')

# --------------------------
# Cek Hak Akses
# --------------------------
def bisa_kelola_kelas(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login.halaman_login'))
        
        user = User.query.get(session.get('user_id'))
        if not user:
            flash("<i class='fas fa-exclamation-triangle'></i> Sesi tidak valid, silakan masuk kembali", "warning")
            return redirect(url_for('login.halaman_login'))

        jabatan = user.jabatan or ''
        
        daftar_tugas = []
        tugas_user = user.tugas_tambahan or ''
        if isinstance(tugas_user, str):
            daftar_tugas = [t.strip() for t in tugas_user.split(',') if t.strip()]
        elif isinstance(tugas_user, list):
            daftar_tugas = tugas_user
        
        diizinkan = ["Admin", "Tata Usaha", "TU", "Waka Kurikulum"]
        
        # === PERBAIKAN: Cek JABATAN ATAU TUGAS ===
        punya_akses = (
            jabatan in diizinkan 
            or "Waka Kurikulum" in daftar_tugas 
            or "Admin Sistem" in daftar_tugas
        )
        
        halaman_aktif = session.get('halaman_aktif', 'utama')
        
        if not punya_akses:
            flash("<i class='fas fa-ban'></i> Anda tidak memiliki hak akses untuk mengelola data kelas", "danger")
            if halaman_aktif == 'waka_kurikulum':
                return redirect(url_for('dashboard_wakakur.halaman_dashboard_wakakur'))
            return redirect(url_for('dashboard.index'))
        
        # Opsional: Pastikan di halaman yang sesuai
        
        halaman_aktif = session.get('halaman_aktif', 'utama')

        if not punya_akses:
            flash(
                "<i class='fas fa-ban'></i> Anda tidak memiliki hak akses untuk mengelola data kelas",
                "danger"
            )

            if halaman_aktif == 'waka_kurikulum':
                return redirect(url_for('dashboard_wakakur.halaman_dashboard_wakakur'))

            return redirect(url_for('dashboard.index'))

        # Pengguna yang memiliki hak akses boleh membuka Data Kelas
        
        return f(*args, **kwargs)
    return decorator

# --------------------------
# Fungsi Bantu: Ambil dasar tahun saja
# --------------------------
def get_base_tahun(kode_tp):
    """Ubah format '2025/2026-1' atau '2025/2026 Ganjil' jadi '2025/2026'"""
    if not kode_tp:
        return ""

    if '-' in kode_tp:
        kode_tp = kode_tp.split('-')[0]

    if ' ' in kode_tp:
        kode_tp = kode_tp.split(' ')[0]
    return kode_tp.strip()


def simpan_status_riwayat_semester(
    siswa,
    kelas,
    dasar_tahun,
    nomor_semester,
    status_akhir,
    tingkat
):
    """
    Memperbarui hasil akhir pada riwayat semester asal.
    Tidak membuat riwayat baru secara otomatis karena
    status_awal harus berasal dari data akademik sebenarnya.
    """

    riwayat = RiwayatSemester.query.filter_by(
        siswa_id=siswa.id,
        tahun_pelajaran=dasar_tahun,
        semester=nomor_semester
    ).first()

    if not riwayat:
        raise ValueError(
            f"Riwayat Semester {nomor_semester} tahun "
            f"{dasar_tahun} untuk siswa {siswa.nama_lengkap} "
            "belum tersedia. Proses dibatalkan agar riwayat "
            "akademik tidak dibuat dengan status awal yang keliru."
        )

    # Perbarui hanya hasil akhir semester yang diproses.
    riwayat.status_akhir = status_akhir

    # Lengkapi data historis hanya jika masih kosong.
    if not riwayat.tingkat_saat_itu:
        riwayat.tingkat_saat_itu = str(tingkat)

    if not riwayat.kelas_nama and kelas:
        riwayat.kelas_nama = kelas.nama_kelas

# --------------------------
# Fungsi Bantu: Kelola Otomatis Tugas Wali Kelas
# --------------------------
def perbarui_tugas_wali_kelas(id_wali_lama, id_wali_baru):
    """
    Saat disimpan:
    - Hapus 'Wali Kelas' dari guru lama
    - Tambahkan 'Wali Kelas' ke guru baru
    - DAN PERBARUI JUGA DI TABEL USER / AKUN
    """
    # Proses Guru Lama
    if id_wali_lama:
        guru_lama = Guru.query.get(id_wali_lama)
        if guru_lama:
            # Ubah di Tabel Guru
            daftar_tugas = [t.strip() for t in (guru_lama.tugas_tambahan or '').split(',')]
            if "Wali Kelas" in daftar_tugas:
                daftar_tugas.remove("Wali Kelas")
                guru_lama.tugas_tambahan = ", ".join(daftar_tugas) if daftar_tugas else ""
                db.session.add(guru_lama)
            # ✅ Ubah juga di Tabel User/Akun
            if guru_lama.akun:
                daftar_akun = [t.strip() for t in (guru_lama.akun.tugas_tambahan or '').split(',')]
                if "Wali Kelas" in daftar_akun:
                    daftar_akun.remove("Wali Kelas")
                    guru_lama.akun.tugas_tambahan = ", ".join(daftar_akun) if daftar_akun else ""
                    db.session.add(guru_lama.akun)

    # Proses Guru Baru
    if id_wali_baru:
        guru_baru = Guru.query.get(id_wali_baru)
        if guru_baru:
            # Ubah di Tabel Guru
            daftar_tugas = [t.strip() for t in (guru_baru.tugas_tambahan or '').split(',')]
            if "Wali Kelas" not in daftar_tugas:
                daftar_tugas.append("Wali Kelas")
                guru_baru.tugas_tambahan = ", ".join(daftar_tugas)
                db.session.add(guru_baru)
            # ✅ Ubah juga di Tabel User/Akun
            if guru_baru.akun:
                daftar_akun = [t.strip() for t in (guru_baru.akun.tugas_tambahan or '').split(',')]
                if "Wali Kelas" not in daftar_akun:
                    daftar_akun.append("Wali Kelas")
                    guru_baru.akun.tugas_tambahan = ", ".join(daftar_akun)
                    db.session.add(guru_baru.akun)

# --------------------------
# Halaman Daftar Kelas
# --------------------------
@kelas_bp.route('/')
@kelas_bp.route('/daftar')
@bisa_kelola_kelas
def halaman_daftar_kelas():
    user = User.query.get(session.get('user_id'))
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()

    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_dipilih and tahun_aktif:
        kode_tahun_dipilih = tahun_aktif.kode

    daftar_kelas = []
    if kode_tahun_dipilih:
        dasar_tahun = get_base_tahun(kode_tahun_dipilih)
        # Cari persis format dasar tahun
        daftar_kelas = Kelas.query.filter(
            Kelas.tahun_pelajaran == dasar_tahun
        ).order_by(Kelas.jenjang, Kelas.nama_kelas).all()

    # ✅ TARUH KODE INI DI SINI: Hitung jumlah siswa sesuai semester yang dipilih
    for kelas in daftar_kelas:
        kelas.jumlah_terkini = kelas.hitung_jumlah_siswa(kode_tahun_dipilih)

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='daftar',
        daftar_kelas=daftar_kelas,
        semua_tahun=semua_tahun,
        tahun_dipilih=kode_tahun_dipilih,
        tahun_aktif=tahun_aktif,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

# --------------------------
# Halaman Tambah Kelas
# --------------------------
@kelas_bp.route('/tambah', methods=['GET', 'POST'])
@bisa_kelola_kelas
def tambah_kelas():
    user = User.query.get(session.get('user_id'))
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
    if not tahun_aktif:
        flash("<i class='fas fa-exclamation-circle'></i> Tentukan Tahun Pelajaran aktif terlebih dahulu!", "warning")
        return redirect(url_for('umum.kelola_tahun_pelajaran'))

    kode_tahun_dipilih = request.args.get('tahun') or tahun_aktif.kode
    dasar_tahun = get_base_tahun(kode_tahun_dipilih)

    if "Genap" in kode_tahun_dipilih:
        flash("<i class='fas fa-info-circle'></i> Kelas hanya dibuat di Semester Ganjil. Gunakan kelas yang sudah ada untuk Genap.", "warning")
        return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

    daftar_guru = Guru.query.all()

    if request.method == 'POST':
        nama_kelas = request.form.get('nama_kelas', '').strip()
        jenjang = request.form.get('jenjang', '').strip()
        wali_kelas_id = request.form.get('wali_kelas_id') or None

        if not nama_kelas or not jenjang:
            flash("<i class='fas fa-times-circle'></i> Nama dan jenjang kelas wajib diisi!", "danger")
            return redirect(url_for('data_kelas.tambah_kelas', tahun=kode_tahun_dipilih))

        cek = Kelas.query.filter(
            Kelas.nama_kelas == nama_kelas,
            Kelas.tahun_pelajaran.like(f"{dasar_tahun}%")
        ).first()

        if cek:
            flash(f"<i class='fas fa-exclamation-triangle'></i> Kelas {nama_kelas} sudah ada di TP {dasar_tahun}!", "warning")
            return redirect(url_for('data_kelas.tambah_kelas', tahun=kode_tahun_dipilih))

        kelas_baru = Kelas(
            nama_kelas=nama_kelas,
            jenjang=jenjang,
            tahun_pelajaran=dasar_tahun,
            wali_kelas_id=wali_kelas_id
        )
        db.session.add(kelas_baru)
        perbarui_tugas_wali_kelas(None, wali_kelas_id)
        db.session.commit()
        user_saat_ini = User.query.get(session.get('user_id'))
        if user_saat_ini:
            session['jabatan'] = user_saat_ini.jabatan
            session['tugas_tambahan'] = user_saat_ini.tugas_tambahan
        user_id_saat_ini = session.get('user_id')
        if wali_kelas_id and user_id_saat_ini:
            guru_diedit = Guru.query.get(wali_kelas_id)
            if guru_diedit and guru_diedit.akun and guru_diedit.akun.id == user_id_saat_ini:
                session['tugas_tambahan'] = guru_diedit.tugas_tambahan
        flash(f"Kelas {nama_kelas} berhasil ditambahkan!", "success")
        return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='form_tambah',
        mode='tambah',
        daftar_guru=daftar_guru,
        tahun_aktif=tahun_aktif,
        tahun_dipilih=kode_tahun_dipilih,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

# --------------------------
# Halaman Ubah Kelas
# --------------------------
@kelas_bp.route('/ubah/<int:id>', methods=['GET', 'POST'])
@bisa_kelola_kelas
def ubah_kelas(id):
    user = User.query.get(session.get('user_id'))
    kelas = Kelas.query.get_or_404(id)
    daftar_guru = Guru.query.all()
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    dasar_tahun = get_base_tahun(kode_tahun_dipilih)

    id_wali_lama = kelas.wali_kelas_id

    if request.method == 'POST':
        nama_kelas = request.form.get('nama_kelas', '').strip()
        jenjang = request.form.get('jenjang', '').strip()
        wali_kelas_id = request.form.get('wali_kelas_id') or None

        if not nama_kelas or not jenjang:
            flash("<i class='fas fa-times-circle'></i> Nama dan jenjang kelas wajib diisi!", "danger")
            return redirect(url_for('data_kelas.ubah_kelas', id=id, tahun=kode_tahun_dipilih))

        cek = Kelas.query.filter(
            Kelas.nama_kelas == nama_kelas,
            Kelas.tahun_pelajaran.like(f"{dasar_tahun}%"),
            Kelas.id != id
        ).first()

        if cek:
            flash(f"<i class='fas fa-exclamation-triangle'></i> Kelas {nama_kelas} sudah ada di TP {dasar_tahun}!", "warning")
            return redirect(url_for('data_kelas.ubah_kelas', id=id, tahun=kode_tahun_dipilih))

        kelas.nama_kelas = nama_kelas
        kelas.jenjang = jenjang
        kelas.wali_kelas_id = wali_kelas_id

        perbarui_tugas_wali_kelas(id_wali_lama, wali_kelas_id)

        db.session.commit()

        user_id_saat_ini = session.get('user_id')
        if wali_kelas_id and user_id_saat_ini:
            guru_diedit = Guru.query.get(wali_kelas_id)
            if guru_diedit and guru_diedit.akun and guru_diedit.akun.id == user_id_saat_ini:
                session['tugas_tambahan'] = guru_diedit.tugas_tambahan

        flash(f"<i class='fas fa-save'></i> Data kelas diperbarui!", "success")
        return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='form_ubah',
        mode='ubah',
        kelas=kelas,
        daftar_guru=daftar_guru,
        tahun_dipilih=kode_tahun_dipilih,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

# --------------------------
# Hapus Kelas
# --------------------------
@kelas_bp.route('/hapus/<int:id>', methods=['POST'])
@bisa_kelola_kelas
def hapus_kelas(id):
    kelas = Kelas.query.get_or_404(id)
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')

    if RiwayatKelas.query.filter_by(kelas_id=kelas.id).first():
        flash("<i class='fas fa-ban'></i> Tidak bisa dihapus! Masih ada siswa tercatat di kelas ini.", "danger")
        return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

    perbarui_tugas_wali_kelas(kelas.wali_kelas_id, None)

    db.session.delete(kelas)
    db.session.commit()

    flash(f"<i class='fas fa-trash-alt'></i> Kelas {kelas.nama_kelas} berhasil dihapus!", "success")
    return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

@kelas_bp.route('/<int:id>/siswa')
@bisa_kelola_kelas
def daftar_siswa_di_kelas(id):
    user = User.query.get(session.get('user_id'))
    kelas = Kelas.query.get_or_404(id)

    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_dipilih:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_dipilih = tahun_aktif.kode if tahun_aktif else None

    dasar_tahun = get_base_tahun(kode_tahun_dipilih)

    # ========== DEBUG: CEK RIWAYAT ==========
    print("=" * 50)
    print(f"[CEK] Kelas ID: {id} | Nama: {kelas.nama_kelas}")
    print(f"[CEK] Tahun/Semester dipilih: {kode_tahun_dipilih}")
    print(f"[CEK] Dasar tahun: {dasar_tahun}")

    # Cek SEMUA riwayat di tabel RiwayatKelas untuk kelas ini
    semua_riwayat_kelas = RiwayatKelas.query.filter_by(kelas_id=id).all()
    print(f"[CEK] Jumlah riwayat di kelas ini (semua tahun): {len(semua_riwayat_kelas)}")
    for r in semua_riwayat_kelas:
        print(f"   -> Riwayat: siswa_id={r.siswa_id}, tahun_pelajaran='{r.tahun_pelajaran}', kelas_id={r.kelas_id}")

    # Cek yang SESUAI tahun yang dipilih
    daftar_siswa = []
    riwayat_list = RiwayatKelas.query.filter(
        RiwayatKelas.kelas_id == id,
        RiwayatKelas.tahun_pelajaran == kode_tahun_dipilih
    ).all()
    print(f"[CEK] Jumlah riwayat cocok dengan tahun dipilih: {len(riwayat_list)}")

    for rw in riwayat_list:
        siswa = Siswa.query.get(rw.siswa_id)
        if siswa:
            daftar_siswa.append(siswa)
    print(f"[CEK] Jumlah siswa dikembalikan ke template: {len(daftar_siswa)}")
    print("=" * 50)
    # ========== AKHIR DEBUG ==========

    # SISA KODE TETAP SAMA...
    siswa_lanjutkan = []
    if kode_tahun_dipilih.endswith('-1') or "Ganjil" in kode_tahun_dipilih:
        kode_genap_cek = f"{dasar_tahun}-2"
        tingkat_kelas = kelas.jenjang
        for siswa in daftar_siswa:
            sudah_di_genap = RiwayatKelas.query.filter_by(
                siswa_id=siswa.id, tahun_pelajaran=kode_genap_cek
            ).first()
            riwayat_tahun_ini = RiwayatKelas.query.filter(
                RiwayatKelas.siswa_id == siswa.id,
                RiwayatKelas.tahun_pelajaran.like(f"{dasar_tahun}%")
            ).all()

            sudah_naik = any(
                str(r.tingkat).isdigit()
                and int(r.tingkat) > int(tingkat_kelas)
                for r in riwayat_tahun_ini
            )
            if not sudah_di_genap and not sudah_naik:
                siswa_lanjutkan.append(siswa)

    # ==========================================
    # SISWA YANG BELUM MASUK KELAS
    # HANYA SISWA YANG SUDAH MEMILIKI RIWAYAT
    # PADA SEMESTER YANG DIPILIH
    # ==========================================

    siswa_belum_masuk = []

    if kode_tahun_dipilih:

        riwayat_belum_masuk = RiwayatKelas.query.filter(
            RiwayatKelas.tahun_pelajaran == kode_tahun_dipilih,
            RiwayatKelas.kelas_id.is_(None),
            RiwayatKelas.tingkat == str(kelas.jenjang)
        ).all()

        for rw in riwayat_belum_masuk:

            siswa = db.session.get(Siswa, rw.siswa_id)

            if not siswa:
                continue

            if siswa.status != 'Aktif':
                continue

            siswa_belum_masuk.append(siswa)

    daftar_mapel = MataPelajaran.query.order_by(MataPelajaran.kode).all()
    daftar_guru = Guru.query.join(User).filter(
        User.jabatan.in_(["Guru", "Kepala Sekolah"])
    ).order_by(Guru.nama).all()

    for m in daftar_mapel:
        aturan = PengaturanMapelKelas.query.filter_by(
            kelas_id=kelas.id, mata_pelajaran_id=m.id, tahun_pelajaran=kode_tahun_dipilih
        ).first()
        m.guru_terpilih = aturan.guru_id if aturan else None
        m.jumlah_jp = aturan.jumlah_jp if aturan else 0

    daftar_tugas = []
    if user.tugas_tambahan:
        if isinstance(user.tugas_tambahan, str):
            daftar_tugas = [t.strip() for t in user.tugas_tambahan.split(',') if t.strip()]
        else:
            daftar_tugas = list(user.tugas_tambahan) if user.tugas_tambahan else []

    # ==========================================
    # DEBUG PENGATURAN MAPEL DAN GURU
    # ==========================================
    print("\n========== DEBUG PENGATURAN MAPEL ==========")
    print("KELAS ID       :", kelas.id)
    print("TAHUN DIPILIH  :", kode_tahun_dipilih)

    for m in daftar_mapel:
        aturan = PengaturanMapelKelas.query.filter_by(
            kelas_id=kelas.id,
            mata_pelajaran_id=m.id,
            tahun_pelajaran=kode_tahun_dipilih
        ).first()

        print({
            "mapel_id": m.id,
            "mapel": m.nama_pelajaran,
            "guru_terpilih_di_template": m.guru_terpilih,
            "guru_id_database": aturan.guru_id if aturan else None,
            "nama_guru_database": aturan.guru.nama if aturan and aturan.guru else None,
            "jumlah_jp": aturan.jumlah_jp if aturan else None
        })

    print("\n========== DEBUG AKUN GURU ==========")

    for guru in Guru.query.order_by(Guru.nama).all():
        print({
            "guru_id": guru.id,
            "nama": guru.nama,
            "user_id": guru.akun.id if guru.akun else None,
            "username": guru.akun.username if guru.akun else None
        })

    print("=========================================\n")

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='detail',
        kelas=kelas,
        daftar_siswa=daftar_siswa,
        siswa_lanjutkan=siswa_lanjutkan,
        siswa_belum_masuk=siswa_belum_masuk,
        daftar_mapel=daftar_mapel,
        daftar_guru=daftar_guru,
        tahun_dipilih=kode_tahun_dipilih,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        daftar_tugas=daftar_tugas
    )

# --------------------------
# Proses Kelola Siswa di Kelas
# --------------------------
@kelas_bp.route('/<int:kelas_id>/kelola-siswa', methods=['POST'])
@bisa_kelola_kelas
def kelola_siswa_di_kelas(kelas_id):

    kelas = db.session.get(Kelas, kelas_id)

    if not kelas:
        flash("Kelas tidak ditemukan!", "danger")
        return redirect(url_for('data_kelas.halaman_daftar_kelas'))

    # =====================================
    # MENENTUKAN SEMESTER
    # Prioritas: Form -> URL -> Session -> Tahun Aktif
    # =====================================
    kode_semester = (
        request.form.get('tahun_pelajaran')
        or request.args.get('tahun')
        or session.get('tahun_pelajaran')
    )

    if not kode_semester:
        tahun_aktif = TahunPelajaran.query.filter_by(
            aktif=True
        ).first()

        kode_semester = tahun_aktif.kode if tahun_aktif else None

    if not kode_semester:
        flash("Pilih semester terlebih dahulu!", "danger")
        return redirect(url_for(
            'data_kelas.daftar_siswa_di_kelas',
            id=kelas_id
        ))

    # =====================================
    # PASTIKAN KELAS SESUAI TAHUN AJARAN
    # =====================================
    dasar_tahun = get_base_tahun(kode_semester)

    if kelas.tahun_pelajaran != dasar_tahun:
        flash(
            "Kelas tidak sesuai dengan tahun pelajaran yang dipilih!",
            "danger"
        )
        return redirect(url_for(
            'data_kelas.daftar_siswa_di_kelas',
            id=kelas_id,
            tahun=kode_semester
        ))

    # =====================================
    # AMBIL DATA ID SISWA DARI FORM
    # =====================================
    siswa_tambah_raw = request.form.getlist('tambah_id')
    siswa_keluar_raw = request.form.getlist('keluarkan_id')

    try:

        siswa_tambah = set()
        siswa_keluar = set()

        # Konversi ID menjadi integer
        for sid in siswa_tambah_raw:
            try:
                siswa_tambah.add(int(sid))
            except (TypeError, ValueError):
                raise ValueError(f"ID siswa tidak valid: {sid}")

        for sid in siswa_keluar_raw:
            try:
                siswa_keluar.add(int(sid))
            except (TypeError, ValueError):
                raise ValueError(f"ID siswa tidak valid: {sid}")

        # Jika ID yang sama ada di kedua daftar,
        # prioritaskan penambahan.
        siswa_keluar -= siswa_tambah

        jumlah_ditambahkan = 0
        jumlah_dikeluarkan = 0
        jumlah_dilewati = 0

        # =====================================
        # TAMBAHKAN SISWA KE KELAS
        #
        # SYARAT:
        # 1. Siswa harus ada.
        # 2. Status siswa harus Aktif.
        # 3. Tingkat harus sesuai jenjang kelas.
        # 4. Riwayat semester yang dipilih wajib ada.
        # 5. Tidak boleh terdaftar di kelas lain.
        #
        # TIDAK MEMBUAT RIWAYAT BARU.
        # =====================================
        for siswa_id in siswa_tambah:

            siswa = db.session.get(Siswa, siswa_id)

            if not siswa:
                jumlah_dilewati += 1
                continue

            if siswa.status != 'Aktif':
                jumlah_dilewati += 1
                continue

            if str(siswa.tingkat) != str(kelas.jenjang):
                jumlah_dilewati += 1
                continue

            # Cari riwayat pada semester yang dipilih
            riwayat = RiwayatKelas.query.filter_by(
                siswa_id=siswa.id,
                tahun_pelajaran=kode_semester
            ).first()

            # Jika belum memiliki riwayat semester ini,
            # jangan izinkan masuk kelas.
            if not riwayat:
                jumlah_dilewati += 1
                continue

            # Jika sudah berada di kelas yang sama,
            # tidak perlu diproses lagi.
            if riwayat.kelas_id == kelas.id:
                jumlah_dilewati += 1
                continue

            # Jika masih tercatat di kelas lain,
            # jangan pindahkan secara otomatis.
            if riwayat.kelas_id is not None:
                jumlah_dilewati += 1
                continue

            # Masukkan ke kelas.
            # Riwayat semester lama tidak disentuh.
            riwayat.kelas_id = kelas.id
            riwayat.tingkat = kelas.jenjang

            jumlah_ditambahkan += 1

        # =====================================
        # KELUARKAN SISWA DARI KELAS
        #
        # Hanya mengosongkan kelas pada semester
        # yang sedang dipilih.
        #
        # Riwayat tetap dipertahankan.
        # =====================================
        for siswa_id in siswa_keluar:

            riwayat = RiwayatKelas.query.filter_by(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_semester,
                kelas_id=kelas.id
            ).first()

            if not riwayat:
                continue

            riwayat.kelas_id = None
            jumlah_dikeluarkan += 1

        # =====================================
        # SIMPAN PERUBAHAN
        # =====================================
        db.session.commit()

        pesan = (
            f"Berhasil menyimpan perubahan! "
            f"{jumlah_ditambahkan} siswa ditambahkan dan "
            f"{jumlah_dikeluarkan} siswa dikeluarkan "
            f"dari kelas."
        )

        if jumlah_dilewati:
            pesan += (
                f" {jumlah_dilewati} siswa dilewati karena "
                f"tidak memenuhi persyaratan."
            )

        flash(pesan, "success")

    except ValueError as e:

        db.session.rollback()
        flash(str(e), "danger")

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "Gagal mengelola siswa kelas ID %s",
            kelas_id
        )

        flash(
            "Gagal menyimpan perubahan siswa. Periksa log server.",
            "danger"
        )

    # =====================================
    # KEMBALI KE DETAIL KELAS
    # =====================================
    return redirect(url_for(
        'data_kelas.daftar_siswa_di_kelas',
        id=kelas_id,
        tahun=kode_semester
    ))


@kelas_bp.route('/<int:kelas_id>/lanjutkan-genap', methods=['POST'])
@bisa_kelola_kelas
def lanjutkan_semester_genap(kelas_id):
    kelas = Kelas.query.get_or_404(kelas_id)

    kode_genap = (request.form.get('kode_genap') or '').strip()
    siswa_dipilih_raw = request.form.getlist('siswa_id')

    if not kode_genap or not siswa_dipilih_raw:
        flash("Pilih siswa yang akan dilanjutkan ke Semester Genap!", "warning")
        return redirect(url_for(
            'data_kelas.daftar_siswa_di_kelas',
            id=kelas_id
        ))

    try:
        # ==========================================
        # VALIDASI KODE PERIODE
        # ==========================================
        dasar_tahun = get_base_tahun(kode_genap)
        kode_ganjil = f"{dasar_tahun}-1"
        kode_genap_benar = f"{dasar_tahun}-2"

        if kode_genap != kode_genap_benar:
            raise ValueError("Kode Semester Genap tidak valid.")

        if kelas.tahun_pelajaran != dasar_tahun:
            raise ValueError("Kelas tidak sesuai dengan tahun pelajaran.")

        # Pastikan kedua periode terdaftar
        periode_ganjil = TahunPelajaran.query.filter_by(
            kode=kode_ganjil
        ).first()

        periode_genap = TahunPelajaran.query.filter_by(
            kode=kode_genap_benar
        ).first()

        if not periode_ganjil or not periode_genap:
            raise ValueError(
                "Periode Ganjil atau Genap belum terdaftar "
                "di pengaturan Tahun Pelajaran."
            )

        # ==========================================
        # VALIDASI ID SISWA
        # ==========================================
        try:
            siswa_ids = {int(sid) for sid in siswa_dipilih_raw}
        except (TypeError, ValueError):
            raise ValueError("Terdapat ID siswa yang tidak valid.")

        dibuat = 0
        dilewati = 0

        for siswa_id in siswa_ids:

            siswa = db.session.get(Siswa, siswa_id)

            if not siswa or siswa.status != 'Aktif':
                dilewati += 1
                continue

            # Siswa wajib benar-benar tercatat di kelas
            # pada Semester Ganjil yang sedang diproses.
            riwayat_ganjil = RiwayatKelas.query.filter_by(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_ganjil,
                kelas_id=kelas.id
            ).first()

            if not riwayat_ganjil:
                dilewati += 1
                continue

            # Tingkat harus konsisten dengan kelas asal.
            if str(riwayat_ganjil.tingkat) != str(kelas.jenjang):
                dilewati += 1
                continue

            # Jangan menimpa riwayat Genap yang sudah ada.
            riwayat_genap = RiwayatKelas.query.filter_by(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_genap_benar
            ).first()

            if riwayat_genap:
                dilewati += 1
                continue

            # Buat riwayat keanggotaan Semester Genap.
            db.session.add(RiwayatKelas(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_genap_benar,
                tingkat=riwayat_ganjil.tingkat,
                kelas_id=kelas.id
            ))

            # Catat bahwa siswa melanjutkan dari Semester Ganjil.
            simpan_status_riwayat_semester(
                siswa=siswa,
                kelas=kelas,
                dasar_tahun=dasar_tahun,
                nomor_semester=1,
                status_akhir="Lanjut",
                tingkat=riwayat_ganjil.tingkat
            )

            dibuat += 1

        db.session.commit()

        pesan = (
            f"{dibuat} siswa berhasil dilanjutkan ke Semester Genap."
        )

        if dilewati:
            pesan += f" {dilewati} siswa dilewati karena tidak memenuhi syarat atau sudah memiliki riwayat Genap."

        flash(pesan, "success" if dibuat else "warning")

    except ValueError as e:
        db.session.rollback()
        flash(str(e), "danger")

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Gagal melanjutkan siswa ke Semester Genap, kelas ID %s",
            kelas_id
        )
        flash(
            "Gagal melanjutkan siswa ke Semester Genap. Periksa log server.",
            "danger"
        )

    return redirect(url_for(
        'data_kelas.daftar_siswa_di_kelas',
        id=kelas.id,
        tahun=kode_genap_benar if 'kode_genap_benar' in locals() else None
    ))


@kelas_bp.route('/<int:kelas_id>/naik-kelas', methods=['POST'])
@bisa_kelola_kelas
def naik_kelas(kelas_id):
    kelas = Kelas.query.get_or_404(kelas_id)

    kode_sekarang = (
        request.form.get('kode_sekarang')
        or request.args.get('tahun')
        or session.get('tahun_pelajaran')
        or ''
    ).strip()

    siswa_dipilih_raw = request.form.getlist('siswa_id')

    if not kode_sekarang:
        flash("Tahun pelajaran tidak ditemukan!", "danger")
        return redirect(url_for(
            'data_kelas.daftar_siswa_di_kelas',
            id=kelas_id
        ))

    if not siswa_dipilih_raw:
        flash("Pilih siswa yang akan diproses!", "warning")
        return redirect(url_for(
            'data_kelas.daftar_siswa_di_kelas',
            id=kelas_id,
            tahun=kode_sekarang
        ))

    try:
        # ==========================================
        # VALIDASI PERIODE ASAL
        # ==========================================
        dasar_tahun = get_base_tahun(kode_sekarang)

        current_app.logger.warning(
            "DEBUG NAIK KELAS | kode_sekarang=%s | dasar_tahun=%s",
            kode_sekarang,
            dasar_tahun
        )

        if kode_sekarang not in (
            f"{dasar_tahun}-1",
            f"{dasar_tahun}-2"
        ):
            raise ValueError("Kode semester tidak valid.")

        if kode_sekarang != f"{dasar_tahun}-2":
            raise ValueError(
                "Proses naik kelas hanya dapat dilakukan "
                "pada Semester Genap."
            )

        if kelas.tahun_pelajaran != dasar_tahun:
            raise ValueError(
                "Kelas tidak sesuai dengan tahun pelajaran yang dipilih."
            )

        periode_asal = TahunPelajaran.query.filter_by(
            kode=kode_sekarang
        ).first()

        if not periode_asal:
            raise ValueError("Periode Semester Genap tidak ditemukan.")

        # ==========================================
        # VALIDASI JENJANG
        # ==========================================
        try:
            tingkat_sekarang = int(kelas.jenjang)
        except (TypeError, ValueError):
            raise ValueError("Jenjang kelas tidak valid.")

        if tingkat_sekarang not in (7, 8, 9):
            raise ValueError("Jenjang kelas tidak dapat diproses.")

        tingkat_baru = str(tingkat_sekarang + 1)

        # Tahun pelajaran berikutnya
        tahun_parts = dasar_tahun.split('/')

        if len(tahun_parts) != 2:
            raise ValueError("Format tahun pelajaran tidak valid.")

        tahun_berikutnya = (
            f"{tahun_parts[0]}/{int(tahun_parts[1]) + 1}"
        )

        kode_tahun_baru = f"{tahun_berikutnya}-1"

        # Untuk kelas 7 dan 8, periode tujuan wajib tersedia.
        if tingkat_sekarang < 9:
            periode_tujuan = TahunPelajaran.query.filter_by(
                kode=kode_tahun_baru
            ).first()

            if not periode_tujuan:
                raise ValueError(
                    f"Periode {kode_tahun_baru} belum dibuat. "
                    "Buat periode Tahun Pelajaran berikutnya terlebih dahulu."
                )

        # ==========================================
        # VALIDASI SISWA TERPILIH
        # ==========================================
        try:
            siswa_ids = {int(sid) for sid in siswa_dipilih_raw}
        except (TypeError, ValueError):
            raise ValueError("Terdapat ID siswa yang tidak valid.")

        jumlah_naik = 0
        jumlah_lulus = 0
        dilewati = 0

        for siswa_id in siswa_ids:

            siswa = db.session.get(Siswa, siswa_id)

            if not siswa or siswa.status != 'Aktif':
                dilewati += 1
                continue

            # Pastikan siswa memang anggota kelas ini
            # pada Semester Genap yang dipilih.
            riwayat_lama = RiwayatKelas.query.filter_by(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_sekarang,
                kelas_id=kelas.id
            ).first()

            if not riwayat_lama:
                dilewati += 1
                continue

            if str(riwayat_lama.tingkat) != str(tingkat_sekarang):
                dilewati += 1
                continue

            # ======================================
            # KELAS 9: LULUS
            # Tidak membuat riwayat Tingkat 10.
            # ======================================
            if tingkat_sekarang == 9:
                siswa.status = "Lulus"

                # Catat hasil akhir Semester Genap.
                simpan_status_riwayat_semester(
                    siswa=siswa,
                    kelas=kelas,
                    dasar_tahun=dasar_tahun,
                    nomor_semester=2,
                    status_akhir="Lulus",
                    tingkat=riwayat_lama.tingkat
                )

                jumlah_lulus += 1
                continue

            # ======================================
            # KELAS 7 / 8: NAIK KELAS
            # ======================================
            riwayat_baru = RiwayatKelas.query.filter_by(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_tahun_baru
            ).first()

            # Jangan menimpa riwayat tahun berikutnya.
            if riwayat_baru:
                dilewati += 1
                continue

            # Buat riwayat pada tahun pelajaran berikutnya.
            db.session.add(RiwayatKelas(
                siswa_id=siswa_id,
                tahun_pelajaran=kode_tahun_baru,
                tingkat=tingkat_baru,
                kelas_id=None
            ))

            # Catat hasil akhir Semester Genap tahun sebelumnya.
            simpan_status_riwayat_semester(
                siswa=siswa,
                kelas=kelas,
                dasar_tahun=dasar_tahun,
                nomor_semester=2,
                status_akhir="Naik Kelas",
                tingkat=riwayat_lama.tingkat
            )

            siswa.tingkat = tingkat_baru
            jumlah_naik += 1

        db.session.commit()

        # ==========================================
        # HASIL PROSES
        # ==========================================
        bagian_pesan = []

        if jumlah_naik:
            bagian_pesan.append(
                f"{jumlah_naik} siswa naik ke Tingkat {tingkat_baru}"
            )

        if jumlah_lulus:
            bagian_pesan.append(
                f"{jumlah_lulus} siswa dinyatakan LULUS"
            )

        if bagian_pesan:
            pesan = "Berhasil: " + " | ".join(bagian_pesan) + "."
        else:
            pesan = "Tidak ada siswa yang memenuhi syarat untuk diproses."

        if dilewati:
            pesan += f" {dilewati} siswa dilewati karena tidak memenuhi syarat atau sudah memiliki riwayat tujuan."

        flash(
            pesan,
            "success" if jumlah_naik or jumlah_lulus else "warning"
        )

    except ValueError as e:
        db.session.rollback()
        flash(str(e), "danger")

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Gagal memproses kenaikan kelas ID %s",
            kelas_id
        )
        flash(
            "Gagal memproses kenaikan kelas. Periksa log server.",
            "danger"
        )

    return redirect(url_for(
        'data_kelas.halaman_daftar_kelas',
        tahun=kode_tahun_baru if 'kode_tahun_baru' in locals() else kode_sekarang
    ))

@kelas_bp.route('/<int:kelas_id>/simpan-pengaturan-mapel', methods=['POST'])
@bisa_kelola_kelas
def simpan_pengaturan_mapel(kelas_id):
    kelas = Kelas.query.get_or_404(kelas_id)
    kode_tahun = request.form.get('tahun_pelajaran') or session.get('tahun_pelajaran')
    semua_mapel = MataPelajaran.query.all()

    for mapel in semua_mapel:
        guru_id = request.form.get(f'guru_id_{mapel.id}') or None
        jp = int(request.form.get(f'jp_{mapel.id}', 0))

        aturan = PengaturanMapelKelas.query.filter_by(
            kelas_id=kelas_id,
            mata_pelajaran_id=mapel.id,
            tahun_pelajaran=kode_tahun
        ).first()

        if aturan:
            aturan.guru_id = guru_id
            aturan.jumlah_jp = jp
        else:
            db.session.add(PengaturanMapelKelas(
                kelas_id=kelas_id,
                mata_pelajaran_id=mapel.id,
                guru_id=guru_id,
                jumlah_jp=jp,
                tahun_pelajaran=kode_tahun
            ))

    db.session.commit()
    flash("<i class='fas fa-book-open'></i> Pengaturan mata pelajaran tersimpan! Mapel dengan JP > 0 sudah aktif.", "success")
    return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas_id, tahun=kode_tahun))


# --------------------------
# Halaman Atur Jadwal Kelas
# --------------------------
@kelas_bp.route('/<int:id>/jadwal', methods=['GET', 'POST'])
@bisa_kelola_kelas
def jadwal_kelas(id):
    user = User.query.get(session.get('user_id'))
    kelas = Kelas.query.get_or_404(id)

    kode_tahun_dipilih = (
        request.args.get('tahun')
        or session.get('tahun_pelajaran')
    )

    if not kode_tahun_dipilih:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_dipilih = tahun_aktif.kode if tahun_aktif else None

    daftar_mapel = MataPelajaran.query.order_by(
        MataPelajaran.kode
    ).all()

    for m in daftar_mapel:
        aturan = PengaturanMapelKelas.query.filter_by(
            kelas_id=kelas.id,
            mata_pelajaran_id=m.id,
            tahun_pelajaran=kode_tahun_dipilih
        ).first()

        m.guru_terpilih = (
            aturan.guru if aturan and aturan.guru_id else None
        )
        m.guru_id_terpilih = aturan.guru_id if aturan else None
        m.jumlah_jp = aturan.jumlah_jp if aturan else 0

    daftar_mapel_aktif = [
        m for m in daftar_mapel
        if m.guru_id_terpilih and m.jumlah_jp > 0
    ]

    # ==========================================
    # PROSES SIMPAN JADWAL
    # ==========================================
    if request.method == 'POST':
        try:
            hari_list = request.form.getlist('hari[]')
            jam_mulai_list = request.form.getlist('jam_mulai[]')
            jam_selesai_list = request.form.getlist('jam_selesai[]')
            mapel_id_list = request.form.getlist('mapel_id[]')

            urutan_hari = [
                'Senin', 'Selasa', 'Rabu', 'Kamis',
                'Jumat', 'Sabtu', 'Minggu'
            ]

            # 1. Pastikan semua data sejajar
            jumlah_data = len(hari_list)

            if jumlah_data == 0:
                flash(
                    "Silakan tambahkan minimal satu sesi jadwal.",
                    "warning"
                )
                return redirect(request.url)

            if not (
                len(jam_mulai_list) == jumlah_data
                and len(jam_selesai_list) == jumlah_data
                and len(mapel_id_list) == jumlah_data
            ):
                flash(
                    "Data jadwal tidak lengkap atau tidak sejajar. "
                    "Silakan periksa kembali jadwal.",
                    "danger"
                )
                return redirect(request.url)

            # 2. Validasi dan normalisasi semua sesi
            from datetime import datetime

            def waktu_dtk(teks):
                waktu = datetime.strptime(teks, '%H:%M')
                return waktu.hour * 60 + waktu.minute

            daftar_sesi = []
            per_hari = {}

            for i in range(jumlah_data):
                hari = hari_list[i].strip()
                mulai = jam_mulai_list[i].strip()
                selesai = jam_selesai_list[i].strip()
                mapel_raw = mapel_id_list[i].strip()

                if hari not in urutan_hari:
                    raise ValueError(
                        f"Hari pembelajaran tidak valid: {hari}"
                    )

                if not mulai or not selesai or not mapel_raw:
                    raise ValueError(
                        f"Data jadwal hari {hari} belum lengkap."
                    )

                try:
                    menit_mulai = waktu_dtk(mulai)
                    menit_selesai = waktu_dtk(selesai)
                except ValueError:
                    raise ValueError(
                        f"Format waktu hari {hari} tidak valid."
                    )

                if menit_selesai <= menit_mulai:
                    raise ValueError(
                        f"Hari {hari}: jam selesai harus lebih "
                        "besar dari jam mulai."
                    )

                # 3. Validasi mata pelajaran dan guru
                if mapel_raw in ('imtaq', 'upacara'):
                    mapel_id = None
                    jenis_khusus = mapel_raw
                    guru_id = None

                else:
                    try:
                        mapel_id = int(mapel_raw)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Mata pelajaran hari {hari} tidak valid."
                        )

                    aturan = PengaturanMapelKelas.query.filter_by(
                        kelas_id=kelas.id,
                        mata_pelajaran_id=mapel_id,
                        tahun_pelajaran=kode_tahun_dipilih
                    ).first()

                    if not aturan or not aturan.guru_id:
                        raise ValueError(
                            f"Mata pelajaran pada hari {hari} "
                            "belum memiliki guru pengampu."
                        )

                    if not aturan.jumlah_jp or aturan.jumlah_jp <= 0:
                        raise ValueError(
                            f"Mata pelajaran pada hari {hari} "
                            "belum memiliki alokasi JP."
                        )

                    jenis_khusus = None
                    guru_id = aturan.guru_id

                sesi = {
                    'hari': hari,
                    'mulai': mulai,
                    'selesai': selesai,
                    'menit_mulai': menit_mulai,
                    'menit_selesai': menit_selesai,
                    'mapel_id': mapel_id,
                    'jenis_khusus': jenis_khusus,
                    'guru_id': guru_id
                }

                daftar_sesi.append(sesi)
                per_hari.setdefault(hari, []).append(sesi)

            # 4. Validasi jadwal bertabrakan
            for hari, sesi_hari in per_hari.items():
                sesi_hari.sort(
                    key=lambda x: x['menit_mulai']
                )

                for i in range(len(sesi_hari) - 1):
                    sekarang = sesi_hari[i]
                    berikutnya = sesi_hari[i + 1]

                    if (
                        berikutnya['menit_mulai']
                        < sekarang['menit_selesai']
                    ):
                        raise ValueError(
                            f"Jadwal bertabrakan pada hari {hari}: "
                            f"{sekarang['mulai']}–{sekarang['selesai']} "
                            f"dengan "
                            f"{berikutnya['mulai']}–{berikutnya['selesai']}."
                        )

            # ==========================================
            # 5. SEMUA VALIDASI LOLOS
            # Baru hapus jadwal lama dan simpan yang baru
            # ==========================================

            JadwalPelajaran.query.filter_by(
                kelas_id=kelas.id,
                tahun_pelajaran=kode_tahun_dipilih
            ).delete(synchronize_session=False)

            for sesi in daftar_sesi:
                jadwal_baru = JadwalPelajaran(
                    kelas_id=kelas.id,
                    tahun_pelajaran=kode_tahun_dipilih,
                    hari=sesi['hari'],
                    jam_mulai=sesi['mulai'],
                    jam_selesai=sesi['selesai'],
                    mata_pelajaran_id=sesi['mapel_id'],
                    guru_id=sesi['guru_id'],
                    jenis_khusus=sesi['jenis_khusus']
                )

                db.session.add(jadwal_baru)

            db.session.commit()

            
            print("\n========== HASIL SIMPAN ULANG JADWAL ==========")

            jadwal_debug = JadwalPelajaran.query.filter_by(
                kelas_id=kelas.id,
                tahun_pelajaran=kode_tahun_dipilih
            ).order_by(
                JadwalPelajaran.id
            ).all()

            for j in jadwal_debug:

                mapel = (
                    MataPelajaran.query.get(j.mata_pelajaran_id)
                    if j.mata_pelajaran_id else None
                )

                guru = (
                    Guru.query.get(j.guru_id)
                    if j.guru_id else None
                )

                print({
                    "jadwal_id": j.id,
                    "hari": j.hari,
                    "jam_mulai": j.jam_mulai,
                    "jam_selesai": j.jam_selesai,
                    "mapel": (
                        mapel.nama_pelajaran
                        if mapel else j.jenis_khusus
                    ),
                    "mapel_id": j.mata_pelajaran_id,
                    "guru_id": j.guru_id,
                    "nama_guru": guru.nama if guru else None
                })

            print("Total jadwal tersimpan:", len(jadwal_debug))
            print("===============================================\n")


            flash(
                f"Jadwal pelajaran {kelas.nama_kelas} berhasil disimpan! "
                f"Total {len(daftar_sesi)} sesi pembelajaran.",
                "success"
            )

        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")

        except Exception as e:
            db.session.rollback()
            print(f"[JADWAL KELAS ERROR] {str(e)}")
            flash(
                f"Gagal menyimpan jadwal: {str(e)}",
                "danger"
            )

        return redirect(
            url_for(
                'data_kelas.jadwal_kelas',
                id=id,
                tahun=kode_tahun_dipilih
            )
        )

    # ==========================================
    # AMBIL JADWAL TERSIMPAN
    # ==========================================
    urutan_hari = [
        'Senin', 'Selasa', 'Rabu', 'Kamis',
        'Jumat', 'Sabtu', 'Minggu'
    ]

    ekspresi_urutan = db.case(
        *[
            (JadwalPelajaran.hari == hari, nomor)
            for nomor, hari in enumerate(urutan_hari, start=1)
        ],
        else_=99
    )

    jadwal_tersimpan = JadwalPelajaran.query.filter_by(
        kelas_id=kelas.id,
        tahun_pelajaran=kode_tahun_dipilih
    ).order_by(
        ekspresi_urutan,
        JadwalPelajaran.jam_mulai
    ).all()

    # ==========================================
    # KELOMPOKKAN JADWAL PER HARI
    # ==========================================
    from collections import defaultdict

    jadwal_per_hari = defaultdict(list)

    for jadwal in jadwal_tersimpan:
        jadwal_per_hari[jadwal.hari].append(jadwal)

    # Senin-Jumat selalu tersedia.
    # Sabtu-Minggu tampil jika sudah memiliki jadwal.
    hari_tampil = [
        'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat'
    ]

    for hari in urutan_hari:
        if (
            hari in jadwal_per_hari
            and hari not in hari_tampil
        ):
            hari_tampil.append(hari)

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='jadwal',
        kelas=kelas,
        daftar_mapel=daftar_mapel_aktif,
        jadwal_tersimpan=jadwal_tersimpan,
        jadwal_per_hari=dict(jadwal_per_hari),
        hari_tampil=hari_tampil,
        tahun_dipilih=kode_tahun_dipilih,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )
