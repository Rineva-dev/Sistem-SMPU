from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Kelas, Guru, TahunPelajaran, User, Siswa, RiwayatKelas, MataPelajaran, PengaturanMapelKelas, JadwalPelajaran
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
        jabatan = session.get('jabatan', '')
        tugas = session.get('tugas_tambahan', '')
        daftar_tugas = [t.strip() for t in tugas.split(',')] if tugas else []
        if jabatan not in ["Admin", "Tata Usaha", "TU", "Waka Kurikulum"] and "Admin Sistem" not in daftar_tugas:
            flash("Anda tidak memiliki hak akses untuk mengelola data kelas", "danger")
            return redirect(url_for('dashboard.index'))
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
        flash("Tentukan Tahun Pelajaran aktif terlebih dahulu!", "warning")
        return redirect(url_for('umum.kelola_tahun_pelajaran'))

    kode_tahun_dipilih = request.args.get('tahun') or tahun_aktif.kode
    dasar_tahun = get_base_tahun(kode_tahun_dipilih)

    if "Genap" in kode_tahun_dipilih:
        flash("Kelas hanya dibuat di Semester Ganjil. Gunakan kelas yang sudah ada untuk Genap.", "warning")
        return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

    daftar_guru = Guru.query.all()

    if request.method == 'POST':
        nama_kelas = request.form.get('nama_kelas', '').strip()
        jenjang = request.form.get('jenjang', '').strip()
        wali_kelas_id = request.form.get('wali_kelas_id') or None

        if not nama_kelas or not jenjang:
            flash("Nama dan jenjang kelas wajib diisi!", "danger")
            return redirect(url_for('data_kelas.tambah_kelas', tahun=kode_tahun_dipilih))

        cek = Kelas.query.filter(
            Kelas.nama_kelas == nama_kelas,
            Kelas.tahun_pelajaran.like(f"{dasar_tahun}%")
        ).first()

        if cek:
            flash(f"Kelas {nama_kelas} sudah ada di TP {dasar_tahun}!", "warning")
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
            flash("Nama dan jenjang kelas wajib diisi!", "danger")
            return redirect(url_for('data_kelas.ubah_kelas', id=id, tahun=kode_tahun_dipilih))

        cek = Kelas.query.filter(
            Kelas.nama_kelas == nama_kelas,
            Kelas.tahun_pelajaran.like(f"{dasar_tahun}%"),
            Kelas.id != id
        ).first()

        if cek:
            flash(f"Kelas {nama_kelas} sudah ada di TP {dasar_tahun}!", "warning")
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

        flash(f"Data kelas diperbarui!", "success")
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
        flash("Tidak bisa dihapus! Masih ada siswa tercatat di kelas ini.", "danger")
        return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

    perbarui_tugas_wali_kelas(kelas.wali_kelas_id, None)

    db.session.delete(kelas)
    db.session.commit()

    flash(f"Kelas {kelas.nama_kelas} berhasil dihapus!", "success")
    return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_tahun_dipilih))

# --------------------------
# Halaman Daftar Siswa di Kelas
# --------------------------
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
    daftar_siswa = []

    if kode_tahun_dipilih:
        daftar_siswa = Siswa.query.join(RiwayatKelas).filter(
            RiwayatKelas.tahun_pelajaran == kode_tahun_dipilih,
            RiwayatKelas.kelas_id == kelas.id
        ).order_by(Siswa.nama).all()

    siswa_lanjutkan = []
    if kode_tahun_dipilih.endswith('-1') or "Ganjil" in kode_tahun_dipilih:
        kode_genap_cek = f"{dasar_tahun}-2"
        tingkat_kelas = kelas.jenjang
        
        for siswa in daftar_siswa:
            sudah_di_genap = RiwayatKelas.query.filter_by(
                siswa_id=siswa.id,
                tahun_pelajaran=kode_genap_cek
            ).first()

            sudah_naik = RiwayatKelas.query.filter(
                RiwayatKelas.siswa_id == siswa.id,
                RiwayatKelas.tahun_pelajaran.like(f"{dasar_tahun}%"),
                RiwayatKelas.tingkat > tingkat_kelas
            ).first()

            if not sudah_di_genap and not sudah_naik:
                siswa_lanjutkan.append(siswa)

    siswa_belum_masuk = []
    if kode_tahun_dipilih:
        siswa_belum_masuk = Siswa.query.filter(
            Siswa.status == 'Aktif',
            Siswa.tingkat == kelas.jenjang
        ).outerjoin(RiwayatKelas, db.and_(
            RiwayatKelas.siswa_id == Siswa.id,
            RiwayatKelas.tahun_pelajaran == kode_tahun_dipilih
        )).filter(
            (RiwayatKelas.id.is_(None)) | (RiwayatKelas.kelas_id.is_(None))
        ).order_by(Siswa.nama).all()

    daftar_mapel = MataPelajaran.query.order_by(MataPelajaran.kode).all()
    daftar_guru = Guru.query.join(User).filter(
        User.jabatan.in_(["Guru", "Kepala Sekolah"])
    ).order_by(Guru.nama).all()

    # Sisipkan pengaturan yang sudah ada
    for m in daftar_mapel:
        aturan = PengaturanMapelKelas.query.filter_by(
            kelas_id=kelas.id,
            mata_pelajaran_id=m.id,
            tahun_pelajaran=kode_tahun_dipilih
        ).first()
        m.guru_terpilih = aturan.guru_id if aturan else None
        m.jumlah_jp = aturan.jumlah_jp if aturan else 0

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='detail',
        kelas=kelas,
        daftar_siswa=daftar_siswa,
        daftar_mapel=daftar_mapel,
        daftar_guru=daftar_guru,
        siswa_lanjutkan=siswa_lanjutkan,
        siswa_belum_masuk=siswa_belum_masuk,
        tahun_dipilih=kode_tahun_dipilih,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

# --------------------------
# Proses Kelola Siswa di Kelas
# --------------------------
@kelas_bp.route('/<int:kelas_id>/kelola-siswa', methods=['POST'])
@bisa_kelola_kelas
def kelola_siswa_di_kelas(kelas_id):
    kelas = Kelas.query.with_entities(Kelas.id, Kelas.jenjang, Kelas.tahun_pelajaran).filter_by(id=kelas_id).first()
    if not kelas:
        flash("Kelas tidak ditemukan!", "danger")
        return redirect(url_for('data_kelas.halaman_daftar_kelas'))

    # ✅ Urutan prioritas: form → url → sesi → tahun aktif
    kode_semester = request.form.get('tahun_pelajaran') or request.args.get('tahun') or session.get('tahun_pelajaran')
    
    if not kode_semester:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_semester = tahun_aktif.kode if tahun_aktif else None

    if not kode_semester:
        flash("Pilih semester terlebih dahulu!", "danger")
        return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas_id))

    siswa_tambah = request.form.getlist('tambah_id')
    siswa_keluar = request.form.getlist('keluarkan_id')

    try:
        # ✅ TAMBAH: HANYA di semester ini
        for sid in siswa_tambah:
            siswa = Siswa.query.get(sid)
            if siswa and siswa.tingkat == kelas.jenjang:
                riwayat = RiwayatKelas.query.filter_by(
                    siswa_id=sid,
                    tahun_pelajaran=kode_semester
                ).first()
                if riwayat:
                    riwayat.kelas_id = kelas.id
                else:
                    db.session.add(RiwayatKelas(
                        siswa_id=sid,
                        tahun_pelajaran=kode_semester,
                        tingkat=kelas.jenjang,
                        kelas_id=kelas.id
                    ))

        # ✅ KELUARKAN: HANYA di semester ini — TIDAK hapus riwayat semester lain!
        for sid in siswa_keluar:
            riwayat = RiwayatKelas.query.filter_by(
                siswa_id=sid,
                tahun_pelajaran=kode_semester
            ).first()
            if riwayat:
                riwayat.kelas_id = None  # Kosongkan saja di semester ini
                # JANGAN hapus riwayat, JANGAN ubah kelas_id di tabel Siswa untuk semester lain

        db.session.commit()
        flash(f"Perubahan tersimpan untuk Semester {kode_semester}!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Gagal: {e}", "danger")

    return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas_id, tahun=kode_semester))

@kelas_bp.route('/<int:kelas_id>/lanjutkan-genap', methods=['POST'])
@bisa_kelola_kelas
def lanjutkan_semester_genap(kelas_id):
    kelas = Kelas.query.get_or_404(kelas_id)
    kode_genap = request.form.get('kode_genap')
    siswa_dipilih = request.form.getlist('siswa_id')

    if not kode_genap or not siswa_dipilih:
        flash("Pilih siswa yang akan dilanjutkan ke Genap!", "warning")
        return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas_id, tahun=kode_genap))

    # Pastikan format kode Genap sesuai database
    dasar_tahun = get_base_tahun(kode_genap)
    kode_genap_benar = f"{dasar_tahun}-2"
    kode_ganjil_sama = f"{dasar_tahun}-1"

    dibuat = 0
    diperbarui = 0

    for sid in siswa_dipilih:
        # Cek apakah SUDAH ADA riwayat Genap untuk siswa ini
        riwayat_genap = RiwayatKelas.query.filter_by(
            siswa_id=sid,
            tahun_pelajaran=kode_genap_benar
        ).first()

        if riwayat_genap:
            # ✅ Sudah ada: langsung perbarui kelas_id saja
            if riwayat_genap.kelas_id != kelas.id:
                riwayat_genap.kelas_id = kelas.id
                diperbarui += 1
        else:
            # ✅ Belum ada: buat baru dari data Ganjil
            riwayat_ganjil = RiwayatKelas.query.filter_by(
                siswa_id=sid,
                tahun_pelajaran=kode_ganjil_sama,
                kelas_id=kelas.id
            ).first()
            
            if riwayat_ganjil:
                db.session.add(RiwayatKelas(
                    siswa_id=sid,
                    tahun_pelajaran=kode_genap_benar,
                    tingkat=riwayat_ganjil.tingkat,
                    kelas_id=kelas.id
                ))
                dibuat += 1

    db.session.commit()
    pesan = f"Selesai! {dibuat} siswa baru ditambahkan ke Genap"
    if diperbarui > 0:
        pesan += f", {diperbarui} siswa sudah ada dan diperbarui kelasnya"
    flash(pesan + ". Riwayat Ganjil tetap aman!", "success")

    return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas.id, tahun=kode_genap_benar))

@kelas_bp.route('/<int:kelas_id>/naik-kelas', methods=['POST'])
@bisa_kelola_kelas
def naik_kelas(kelas_id):
    kelas = Kelas.query.get_or_404(kelas_id)
    kode_sekarang = request.form.get('kode_sekarang') or request.args.get('tahun') or session.get('tahun_pelajaran')
    siswa_dipilih = request.form.getlist('siswa_id')

    if not siswa_dipilih:
        flash("Pilih siswa yang akan naik kelas!", "warning")
        return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas_id, tahun=kode_sekarang))

    tingkat_baru = str(int(kelas.jenjang) + 1)
    jumlah_berhasil = 0

    for sid in siswa_dipilih:
        siswa = Siswa.query.get(sid)
        if siswa and siswa.tingkat == kelas.jenjang:
            siswa.tingkat = tingkat_baru
            jumlah_berhasil += 1

    db.session.commit()
    flash(f"Berhasil memproses naik kelas untuk {jumlah_berhasil} siswa ke Tingkat {tingkat_baru}! Siapkan kelas baru tahun depan.", "success")
    return redirect(url_for('data_kelas.halaman_daftar_kelas', tahun=kode_sekarang))

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
    flash("Pengaturan mata pelajaran tersimpan! Mapel dengan JP > 0 sudah aktif.", "success")
    return redirect(url_for('data_kelas.daftar_siswa_di_kelas', id=kelas_id, tahun=kode_tahun))

# --------------------------
# Halaman Atur Jadwal Kelas
# --------------------------
@kelas_bp.route('/<int:id>/jadwal', methods=['GET', 'POST'])
@bisa_kelola_kelas
def jadwal_kelas(id):
    user = User.query.get(session.get('user_id'))
    kelas = Kelas.query.get_or_404(id)

    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_dipilih:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_dipilih = tahun_aktif.kode if tahun_aktif else None

    daftar_mapel = MataPelajaran.query.order_by(MataPelajaran.kode).all()
    for m in daftar_mapel:
        aturan = PengaturanMapelKelas.query.filter_by(
            kelas_id=kelas.id,
            mata_pelajaran_id=m.id,
            tahun_pelajaran=kode_tahun_dipilih
        ).first()

        m.guru_terpilih = aturan.guru if aturan and aturan.guru_id else None
        m.guru_id_terpilih = aturan.guru_id if aturan else None
        m.jumlah_jp = aturan.jumlah_jp if aturan else 0

    daftar_mapel_aktif = [m for m in daftar_mapel if m.guru_id_terpilih and m.jumlah_jp > 0]

    if request.method == 'POST':
        try:
            hari_list = request.form.getlist('hari[]')
            jam_mulai_list = request.form.getlist('jam_mulai[]')
            jam_selesai_list = request.form.getlist('jam_selesai[]')
            mapel_id_list = request.form.getlist('mapel_id[]')

            if not hari_list:
                flash("Silakan atur jadwal terlebih dahulu!", "warning")
                return redirect(request.url)

            JadwalPelajaran.query.filter_by(
                kelas_id=kelas.id,
                tahun_pelajaran=kode_tahun_dipilih
            ).delete()
            db.session.commit()

            for i in range(len(hari_list)):
                mapel_id = int(mapel_id_list[i])

                aturan = PengaturanMapelKelas.query.filter_by(
                    kelas_id=kelas.id,
                    mata_pelajaran_id=mapel_id,
                    tahun_pelajaran=kode_tahun_dipilih
                ).first()

                if not aturan or not aturan.guru_id:
                    continue

                jadwal_baru = JadwalPelajaran(
                    kelas_id=kelas.id,
                    tahun_pelajaran=kode_tahun_dipilih,
                    hari=hari_list[i],
                    jam_mulai=jam_mulai_list[i],
                    jam_selesai=jam_selesai_list[i],
                    mata_pelajaran_id=mapel_id,
                    guru_id=aturan.guru_id
                )
                db.session.add(jadwal_baru)

            db.session.commit()
            flash(f"Jadwal Pelajaran {kelas.nama_kelas} berhasil disimpan!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Gagal menyimpan jadwal: {str(e)}", "danger")

        return redirect(url_for('data_kelas.jadwal_kelas', id=id, tahun=kode_tahun_dipilih))

    jadwal_tersimpan = JadwalPelajaran.query.filter_by(
        kelas_id=kelas.id,
        tahun_pelajaran=kode_tahun_dipilih
    ).order_by(JadwalPelajaran.hari, JadwalPelajaran.jam_mulai).all()

    return render_template(
        'index.html',
        active_page='data_kelas',
        sub_page='jadwal',
        kelas=kelas,
        daftar_mapel=daftar_mapel_aktif,
        jadwal_tersimpan=jadwal_tersimpan,
        tahun_dipilih=kode_tahun_dipilih,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )