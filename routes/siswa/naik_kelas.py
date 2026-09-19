from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Siswa, RiwayatSemester, TahunPelajaran

naik_kelas_bp = Blueprint('naik_kelas', __name__, url_prefix='/naik-kelas')

def proses_naik_kelas(semester_aktif, semester_berikutnya):
    """
    semester_aktif = "2025/2026-Genap" atau "2025/2026-2"
    semester_berikutnya = "2026/2027-Ganjil" atau "2026/2027-1"
    """
    # 1. Ambil semua siswa Aktif di semester ini
    siswa_list = Siswa.query.filter_by(status='Aktif').all()
    jumlah_diproses = 0
    
    for siswa in siswa_list:
        tingkat = int(siswa.tingkat)
        
        # === TEMPAT LOGIKA KAMU ===
        # Tentukan semester: 1 = Ganjil, 2 = Genap
        semester = 1 if ("-1" in semester_aktif or "Ganjil" in semester_aktif) else 2
        
        # Terapkan aturan
        if tingkat == 9 and semester == 2:
            status_akhir = "Lulus"
        else:
            status_akhir = "Naik"
        # ==========================
        
        # 2. Simpan riwayat semester berjalan
        RiwayatSemester(
            siswa_id=siswa.id,
            tahun_pelajaran=semester_aktif,
            semester=semester,
            status_awal='Lanjut Semester',
            status_akhir=status_akhir,  # ✅ Pakai variabel di atas
            keaktifan='Aktif',
            tingkat_saat_itu=str(tingkat),
            kelas_nama=siswa.kelas_sekarang.nama_kelas if siswa.kelas_sekarang else None
        ).simpan()
        
        # 3. Perbarui data siswa
        if status_akhir == "Naik":
            siswa.tingkat = str(tingkat + 1)
            siswa.kelas_id = None
        else:  # Lulus
            siswa.status = 'Lulus'
            siswa.kelas_id = None
        
        # 4. Buat riwayat untuk semester berikutnya
        tingkat_baru = tingkat + 1 if status_akhir == "Naik" else None
        RiwayatSemester(
            siswa_id=siswa.id,
            tahun_pelajaran=semester_berikutnya,
            semester=1,
            status_awal='Naik Kelas' if status_akhir == "Naik" else '-',
            status_akhir=None,
            keaktifan='Aktif' if status_akhir == "Naik" else 'Non Aktif',
            tingkat_saat_itu=str(tingkat_baru) if status_akhir == "Naik" else '-',
            kelas_nama=None
        ).simpan()
        
        jumlah_diproses += 1
    
    db.session.commit()
    return jumlah_diproses

@naik_kelas_bp.route('/', methods=['GET', 'POST'])
def halaman_naik_kelas():
    from flask import session, redirect, url_for, flash
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    
    # Cek hak akses — pakai fungsi yang sama seperti di data_siswa
    jabatan = session.get('jabatan', '').strip()
    if not (jabatan == "Admin" or jabatan in ["Tata Usaha", "TU"]):
        flash("Anda tidak berhak mengakses proses ini!", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        semester_aktif = request.form.get('semester_aktif', '').strip()
        semester_berikutnya = request.form.get('semester_berikutnya', '').strip()
        
        if not semester_aktif or not semester_berikutnya:
            flash("Pilih semester aktif dan semester berikutnya!", "danger")
            return redirect(url_for('naik_kelas.halaman_naik_kelas'))
        
        jumlah = proses_naik_kelas(semester_aktif, semester_berikutnya)
        flash(f"✅ Proses naik kelas selesai! Diproses {jumlah} siswa.", "success")
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    # Ambil daftar tahun pelajaran untuk dipilih
    semua_tp = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    return render_template('index.html',
        active_page='naik_kelas',
        semua_tp=semua_tp,
        halaman_aktif=session.get('halaman_aktif', 'utama'),
        user={'jabatan': session.get('jabatan', '')}
    )

