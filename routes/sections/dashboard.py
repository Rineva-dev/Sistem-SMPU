from flask import Blueprint, render_template, session, redirect, url_for, request
from datetime import datetime
from sqlalchemy import func
from models import User, Siswa, Guru, Kelas, TahunPelajaran, RiwayatKelas

dashboard_bp = Blueprint('dashboard', __name__)

# ==============================================
# FUNGSI SAMA PERSIS DENGAN SEMUA HALAMAN LAIN
# ==============================================
def get_base_tahun(kode_tp):
    """Ubah format '2025/2026-1' jadi '2025/2026'"""
    if not kode_tp:
        return ""
    if '-' in kode_tp:
        kode_tp = kode_tp.split('-')[0]
    if ' ' in kode_tp:
        kode_tp = kode_tp.split(' ')[0]
    return kode_tp.strip()


@dashboard_bp.route('/')
@dashboard_bp.route('/<page>')
def index(page='dashboard'):
    # ✅ RESET SESI ABSENSI → KEMBALI KE MODE SEKOLAH
    session['absensi_logged_in'] = None
    session['absensi_sistem_mode'] = None
    session['absensi_user_id'] = None
    session['absensi_guru_id'] = None

    if not (session.get('logged_in') and 
            session.get('sistem_mode') == 'sekolah' and 
            session.get('user_id')):
        return redirect(url_for('login.halaman_login'))

    halaman_aktif = session.get('halaman_aktif', 'utama')
    jabatan = session.get('role', '')

    # ==============================================
    # ⚠️ TIDAK ADA PENGECEKAN BENDAHARA DI SINI → INI YANG BIKIN LOOP!
    # ==============================================
    
    if halaman_aktif == 'waka_kurikulum':
        return redirect(url_for('dashboard_wakakur.halaman_dashboard_wakakur'))

    if halaman_aktif == 'utama':
        if jabatan == 'Guru':
            return redirect('/dashboard-guru')
        elif jabatan == 'Kepala Sekolah':
            return redirect(url_for('dashboard_kepsek.index'))

    if jabatan == 'Kepala Sekolah':
        return redirect(url_for('dashboard_kepsek.index'))

    active_page = page
    user_role = session.get('user_role', '')
    daftar_tugas = session.get('daftar_tugas', [])
    user = User.query.get(session.get('user_id'))

    # ==============================================
    # ✅ AMBIL TAHUN PILIHAN PENGGUNA
    # ==============================================
    kode_tahun_aktif = request.args.get('tahun') or session.get('tahun_pelajaran')
    
    if not kode_tahun_aktif:
        tahun_aktif_db = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_aktif = tahun_aktif_db.kode if tahun_aktif_db else None

    nama_tahun = "Tidak Diketahui"
    nama_semester = "-"
    dasar_tahun = get_base_tahun(kode_tahun_aktif)

    if kode_tahun_aktif:
        tahun_obj = TahunPelajaran.query.filter_by(kode=kode_tahun_aktif).first()
        if tahun_obj:
            potong = tahun_obj.nama.replace('Tahun Pelajaran ', '').split(' - ')
            if len(potong) == 2:
                nomor_semester = potong[1].replace('Semester ', '')
                nama_semester = 'Ganjil' if nomor_semester == '1' else 'Genap'
                nama_tahun = potong[0]
            else:
                nama_tahun = tahun_obj.nama

        total_kelas_query = Kelas.query
        if dasar_tahun:
            total_kelas_query = total_kelas_query.filter_by(tahun_pelajaran=dasar_tahun)

        if kode_tahun_aktif:
            riwayat_sesuai = RiwayatKelas.query.filter_by(tahun_pelajaran=kode_tahun_aktif).all()
            id_siswa_unik = list({r.siswa_id for r in riwayat_sesuai})
            total_siswa = len(id_siswa_unik)

            if id_siswa_unik:
                siswa_laki = Siswa.query.filter(
                    Siswa.id.in_(id_siswa_unik),
                    Siswa.jenis_kelamin == 'Laki-laki'
                ).count()

                siswa_perempuan = Siswa.query.filter(
                    Siswa.id.in_(id_siswa_unik),
                    Siswa.jenis_kelamin == 'Perempuan'
                ).count()
            else:
                siswa_laki = 0
                siswa_perempuan = 0

        else:
            total_siswa = Siswa.query.filter_by(status='Aktif').count()
            siswa_laki = Siswa.query.filter_by(status='Aktif', jenis_kelamin='Laki-laki').count()
            siswa_perempuan = Siswa.query.filter_by(status='Aktif', jenis_kelamin='Perempuan').count()

        siswa_lulus = Siswa.query.filter_by(status='Lulus').count()
        total_guru = Guru.query.count()
        guru_sertifikasi = Guru.query.filter_by(sertifikasi=True).count()
        total_kelas = total_kelas_query.count()

    persen_siswa = 2.5
    persen_guru = 0
    persen_hadir = 94
    persen_naik = 1.2
    jumlah_surat_masuk = 12
    jumlah_surat_keluar = 8
    jumlah_pegawai = total_guru + 5
    total_pemasukan_tahun = 450000000
    total_pengeluaran_tahun = 320000000
    jumlah_mapel_diampu = 4
    jumlah_siswa_diajar = 120
    persen_kehadiran_mengajar = 96
    jumlah_jam_minggu = 24
    jadwal_hari_ini = [
        {'jam': '07.00 - 08.30', 'mapel': 'Matematika', 'kelas': 'VIII A'},
        {'jam': '09.00 - 10.30', 'mapel': 'Matematika', 'kelas': 'VIII B'}
    ]
    nama_kelas = 'VIII A'
    jumlah_siswa_kelas = 32
    persen_hadir_kelas = 97
    jumlah_tidak_hadir = 1
    jumlah_belum_lunas_spp = 3
    rata_rata_nilai = 78.5
    jumlah_naik_kelas = 31
    jumlah_mapel = 16
    jumlah_jam_efektif = 36
    rata_rata_nilai_sekolah = 76.2
    jumlah_jadwal_teratur = 18
    total_siswa_sekolah = total_siswa
    rata_kehadiran_sekolah = 94
    jumlah_pelanggaran = 5
    jumlah_prestasi = 8
    jumlah_ruangan = 22
    jumlah_ruangan_layak = 20
    jumlah_perbaikan = 2
    jumlah_inventaris = 420

    # ✅ DI SET 0 UNTUK AMAN (tidak akan terpakai saat masuk Bendahara)
    pemasukan_bulan_ini = 1
    pengeluaran_bulan_ini = 0
    saldo_tersedia = pemasukan_bulan_ini - pengeluaran_bulan_ini
    persen_lunas_spp = 0

    nama_ekskul = 'Pramuka'
    jumlah_anggota = 45
    frekuensi_pertemuan = 4
    rata_kehadiran_anggota = 88
    jumlah_prestasi_ekskul = 3
    total_siswa_binaan = 120
    kasus_ditangani_bulan = 12
    kasus_selesai = 9
    kasus_berlangsung = 3
    kegiatan_bimbingan = 8
    daftar_kasus = [
        {'nama_siswa': 'Andi Pratama', 'kelas': 'VIII B', 'jenis_kasus': 'Keterlambatan masuk kelas berulang', 'status': 'Proses'},
        {'nama_siswa': 'Siti Aminah', 'kelas': 'VII C', 'jenis_kasus': 'Kesulitan memahami pelajaran', 'status': 'Selesai'}
    ]
    pengumuman = [
        {'judul': 'Libur Hari Raya', 'isi': 'Sekolah libur selama 3 hari mulai tanggal 10 Juni 2026.', 'tanggal': '05 Juni 2026'},
        {'judul': 'Pembagian Rapor Semester Genap', 'isi': 'Pembagian rapor dilaksanakan pada hari Sabtu, 20 Juni 2026.', 'tanggal': '02 Juni 2026'}
    ]

    daftar_bulan = ["Januari", "Pebruari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "Nopember", "Desember"]

    context = {
        'active_page': active_page,
        'halaman_aktif': halaman_aktif,
        'user': user,
        'user_name': session.get('user_name', 'Pengguna'),
        'user_role': user_role,
        'role': session.get('role', user_role),
        'daftar_tugas': daftar_tugas,
        'user_initials': session.get('user_initials', 'US'),
        'today_date': datetime.now().strftime('%d %B %Y'),
        'today_date_long': datetime.now().strftime('%A, %d %B %Y'),
        'tahun_ajaran': nama_tahun,
        'semester': nama_semester,
        'total_siswa': total_siswa,
        'persen_siswa': persen_siswa,
        'total_guru': total_guru,
        'persen_guru': persen_guru,
        'total_kelas': total_kelas,
        'persen_hadir': persen_hadir,
        'persen_naik': persen_naik,
        'jumlah_surat_masuk': jumlah_surat_masuk,
        'jumlah_surat_keluar': jumlah_surat_keluar,
        'jumlah_pegawai': jumlah_pegawai,
        'total_pemasukan_tahun': total_pemasukan_tahun,
        'total_pengeluaran_tahun': total_pengeluaran_tahun,
        'jumlah_mapel_diampu': jumlah_mapel_diampu,
        'jumlah_siswa_diajar': jumlah_siswa_diajar,
        'persen_kehadiran_mengajar': persen_kehadiran_mengajar,
        'jumlah_jam_minggu': jumlah_jam_minggu,
        'jadwal_hari_ini': jadwal_hari_ini,
        'nama_kelas': nama_kelas,
        'jumlah_siswa_kelas': jumlah_siswa_kelas,
        'persen_hadir_kelas': persen_hadir_kelas,
        'jumlah_tidak_hadir': jumlah_tidak_hadir,
        'jumlah_belum_lunas_spp': jumlah_belum_lunas_spp,
        'jumlah_laki': siswa_laki,
        'jumlah_perempuan': siswa_perempuan,
        'rata_rata_nilai': rata_rata_nilai,
        'jumlah_naik_kelas': jumlah_naik_kelas,
        'jumlah_mapel': jumlah_mapel,
        'jumlah_jam_efektif': jumlah_jam_efektif,
        'rata_rata_nilai_sekolah': rata_rata_nilai_sekolah,
        'jumlah_jadwal_teratur': jumlah_jadwal_teratur,
        'total_siswa_sekolah': total_siswa_sekolah,
        'rata_kehadiran_sekolah': rata_kehadiran_sekolah,
        'jumlah_pelanggaran': jumlah_pelanggaran,
        'jumlah_prestasi': jumlah_prestasi,
        'jumlah_ruangan': jumlah_ruangan,
        'jumlah_ruangan_layak': jumlah_ruangan_layak,
        'jumlah_perbaikan': jumlah_perbaikan,
        'jumlah_inventaris': jumlah_inventaris,
        'pemasukan_bulan_ini': pemasukan_bulan_ini,
        'pengeluaran_bulan_ini': pengeluaran_bulan_ini,
        'saldo_tersedia': saldo_tersedia,
        'persen_lunas_spp': persen_lunas_spp,
        'nama_ekskul': nama_ekskul,
        'jumlah_anggota': jumlah_anggota,
        'frekuensi_pertemuan': frekuensi_pertemuan,
        'rata_kehadiran_anggota': rata_kehadiran_anggota,
        'jumlah_prestasi_ekskul': jumlah_prestasi_ekskul,
        'total_siswa_binaan': total_siswa_binaan,
        'kasus_ditangani_bulan': kasus_ditangani_bulan,
        'kasus_selesai': kasus_selesai,
        'kasus_berlangsung': kasus_berlangsung,
        'kegiatan_bimbingan': kegiatan_bimbingan,
        'daftar_kasus': daftar_kasus,
        'pengumuman': pengumuman,
        'dlabel_bulan': daftar_bulan,
    }

    return render_template('index.html', **context)


@dashboard_bp.route('/pindah/<nama_halaman>')
def pindah_halaman(nama_halaman):
    # ✅ Tambahkan reset di sini juga
    session['absensi_logged_in'] = None
    session['absensi_sistem_mode'] = None
    session['absensi_user_id'] = None
    session['absensi_guru_id'] = None

    if not (session.get('logged_in') and 
            session.get('sistem_mode') == 'sekolah' and 
            session.get('user_id')):
        return redirect(url_for('login.halaman_login'))

    daftar_halaman = ['utama', 'bendahara', 'admin_sistem', 'wali_kelas', 
                      'waka_kurikulum', 'waka_kesiswaan', 'pembina_ekskul']
    
    if nama_halaman in daftar_halaman:
        session['halaman_aktif'] = nama_halaman
    
    if nama_halaman == 'bendahara':
        return redirect(url_for('bendahara.index'))
    elif nama_halaman == 'waka_kurikulum':
        return redirect(url_for('dashboard_wakakur.halaman_dashboard_wakakur'))
    elif nama_halaman == 'admin_sistem':
        return redirect(url_for('dashboard_admin.index'))
    else:
        return redirect(url_for('dashboard.index'))