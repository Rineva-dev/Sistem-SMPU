from flask import Blueprint, render_template, session, redirect, url_for, flash, g, request, jsonify, make_response
from models import Guru, AbsensiGuru, TahunPelajaran, GajiGuru, db, User, PengaturanJamKerja
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import extract
import qrcode
import io
import base64

absensi_guru_bp = Blueprint('absensi_guru', __name__)

# ✅ === FUNGSI CEK IP WIFI SEKOLAH ===
def dapatkan_ip_klien():
    """Ambil IP asli klien (bisa lewat proxy)"""
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def cek_dari_wifi_sekolah():
    """
    CEK APAKAH TERHUBUNG DARI JARINGAN SEKOLAH
    Rentang IP yang sudah terdeteksi: 10.10.12.x
    """
    ip = dapatkan_ip_klien()
    
    IP_DIPERBOLEHKAN = [
        "10.10.11."
    ]
    
    for rentang in IP_DIPERBOLEHKAN:
        if ip.startswith(rentang):
            return True, ip
    return False, ip
# ✅ === SELESAI FUNGSI CEK IP ===

def hitung_status_absensi(jam_masuk_str):
    jam = ambil_jam_pengaturan()
    JAM_MASUK_TEPAT = datetime.strptime(jam['jam_masuk_tepat'], "%H:%M").time()
    BATAS_TERLAMBAT = datetime.strptime(jam['batas_terlambat'], "%H:%M").time()  # ✅ BARU
    JAM_TUTUP_ABSEN = datetime.strptime(jam['jam_tutup_absensi'], "%H:%M").time()
    JAM_PULANG_RESMI = datetime.strptime(jam['jam_pulang_resmi'], "%H:%M").time()
    
    jam_masuk = datetime.strptime(jam_masuk_str, "%H:%M").time() if jam_masuk_str else None
    status = "hadir"
    keterangan = ""

    if jam_masuk:
        if jam_masuk > JAM_TUTUP_ABSEN:
            status = "alfa"
            keterangan = f"Lewat batas waktu absensi ({jam['jam_tutup_absensi']})"
        elif jam_masuk > BATAS_TERLAMBAT:
            # ⏰ TERLAMBAT: Setelah 07:15
            status = "terlambat"
            terlambat_menit = (
                datetime.combine(date.today(), jam_masuk) -
                datetime.combine(date.today(), BATAS_TERLAMBAT)
            ).seconds // 60
            keterangan = f"Terlambat {terlambat_menit} menit"
        elif jam_masuk > JAM_MASUK_TEPAT:
            status = "batas_waktu"
            keterangan = "Masuk pada batas waktu toleransi"
        else:
            status = "hadir"
            keterangan = "Masuk tepat waktu"

    return status, keterangan

def sudah_lewat_batas_absensi():
    jam = ambil_jam_pengaturan()  # ✅ Baca dari pengaturan
    BATAS_JAM = jam['jam_tutup_absensi']

    jam_sekarang = waktu_wita().strftime("%H:%M")

    def jam_ke_menit(jam_str):
        j, m = map(int, jam_str.split(':'))
        return j * 60 + m

    return jam_ke_menit(jam_sekarang) >= jam_ke_menit(BATAS_JAM)

def belum_jam_pulang():
    jam = ambil_jam_pengaturan()  # ✅ Baca dari pengaturan
    BATAS_PULANG = jam['jam_pulang_resmi']

    jam_sekarang = waktu_wita().strftime("%H:%M")

    def jam_ke_menit(jam_str):
        j, m = map(int, jam_str.split(':'))
        return j * 60 + m

    return jam_ke_menit(jam_sekarang) < jam_ke_menit(BATAS_PULANG)

# === ✅ FUNGSI AMBIL JAM DARI PENGATURAN DATABASE ===
def ambil_jam_pengaturan():
    defaults = {
        'jam_masuk_tepat': '07:00',
        'batas_terlambat': '07:15',   # ✅ BARU
        'jam_tutup_absensi': '11:00',
        'jam_pulang_resmi': '15:00'
    }
    hasil = defaults.copy()
    try:
        pengaturan = PengaturanJamKerja.ambil_atau_buat()
        def ke_str(t, default_str):
            return t.strftime('%H:%M') if t else default_str
        
        hasil['jam_masuk_tepat'] = ke_str(pengaturan.jam_masuk, defaults['jam_masuk_tepat'])
        hasil['batas_terlambat'] = ke_str(pengaturan.batas_terlambat, defaults['batas_terlambat'])  # ✅ BARU
        hasil['jam_tutup_absensi'] = ke_str(pengaturan.jam_tutup_absensi, defaults['jam_tutup_absensi'])
        hasil['jam_pulang_resmi'] = ke_str(pengaturan.jam_pulang, defaults['jam_pulang_resmi'])
    except Exception:
        pass
    return hasil

# ==============================================
# ✅ FUNGSI BANTU: TERBILANG (Angka ke Kalimat Bahasa Indonesia)
# ==============================================
def terbilang(angka):
    if angka == 0:
        return "Nol Rupiah"
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan"]
    belasan = ["Sepuluh", "Sebelas", "Dua Belas", "Tiga Belas", "Empat Belas", "Lima Belas",
               "Enam Belas", "Tujuh Belas", "Delapan Belas", "Sembilan Belas"]

    def ubah(n):
        if n < 10: return satuan[n]
        elif n < 20: return belasan[n - 10]
        elif n < 100: return satuan[n // 10] + " Puluh" + (" " + satuan[n % 10] if n % 10 != 0 else "")
        elif n < 1000:
            ratus = "Seratus" if n // 100 == 1 else satuan[n // 100] + " Ratus"
            return ratus + (" " + ubah(n % 100) if n % 100 != 0 else "")
        elif n < 1000000:
            return ubah(n // 1000) + " Ribu" + (" " + ubah(n % 1000) if n % 1000 != 0 else "")
        elif n < 1000000000:
            return ubah(n // 1000000) + " Juta" + (" " + ubah(n % 1000000) if n % 1000000 != 0 else "")
        else:
            return ubah(n // 1000000000) + " Miliar" + (" " + ubah(n % 1000000000) if n % 1000000000 != 0 else "")

    hasil = ubah(int(round(float(angka)))) + " Rupiah"
    return hasil.replace("  ", " ").strip()

# ==============================================
# ✅ FUNGSI BANTU: AMBIL TAHUN PELAJARAN AKTIF
# ==============================================
def ambil_tahun_pelajaran():
    """
    Mengembalikan (tgl_mulai_tp, tgl_selesai_tp, label_tp)
    berdasarkan g.tahun_pelajaran atau tahun pelajaran aktif
    """
    hari_ini = waktu_wita().date()
    tp_terpilih = None

    if g.tahun_pelajaran:
        tp_terpilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    if not tp_terpilih:
        tp_terpilih = TahunPelajaran.query.filter_by(aktif=True).first()

    if tp_terpilih:
        tgl_mulai_tp = tp_terpilih.tanggal_mulai
        tgl_selesai_tp = tp_terpilih.tanggal_selesai
        kode_parts = tp_terpilih.kode.split('-')
        if len(kode_parts) == 2:
            kode_tahun = kode_parts[0]
            semester = kode_parts[1]
            nama_semester = "Ganjil" if semester == "1" else "Genap"
            label_tp = f"{kode_tahun} / Semester {nama_semester}"
        else:
            label_tp = tp_terpilih.kode
    else:
        tgl_mulai_tp = date(hari_ini.year, 7, 1)
        tgl_selesai_tp = date(hari_ini.year + 1, 6, 30)
        label_tp = f"{hari_ini.year}/{hari_ini.year + 1}"

    return tgl_mulai_tp, tgl_selesai_tp, label_tp

def waktu_wita():
    return datetime.now(timezone.utc) + timedelta(hours=8)


@absensi_guru_bp.route('/dashboard')
def dashboard():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))

    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()

    if not guru:
        flash('Akun ini tidak memiliki akses.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))
    hari_ini = waktu_wita().date()
    absensi_hari_ini = AbsensiGuru.query.filter_by(
        guru_id=guru.id,
        tanggal=hari_ini
    ).first()
    tp_terpilih = None
    if g.tahun_pelajaran:
        tp_terpilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    if not tp_terpilih:
        tp_terpilih = TahunPelajaran.query.filter_by(aktif=True).first()
    if tp_terpilih:
        tgl_mulai_tp = tp_terpilih.tanggal_mulai
        tgl_selesai_tp = tp_terpilih.tanggal_selesai
        kode_parts = tp_terpilih.kode.split('-')
        if len(kode_parts) == 2:
            kode_tahun = kode_parts[0]
            semester = kode_parts[1]
            nama_semester = "Ganjil" if semester == "1" else "Genap"
            label_tp = f"{kode_tahun}-{nama_semester}"
        else:
            label_tp = tp_terpilih.kode
    else:
        tgl_mulai_tp = date(hari_ini.year, 7, 1)
        tgl_selesai_tp = date(hari_ini.year + 1, 6, 30)
        label_tp = f"{hari_ini.year}/{hari_ini.year + 1}"
    semua_absensi = AbsensiGuru.query.filter(
        AbsensiGuru.guru_id == guru.id,
        AbsensiGuru.tanggal >= tgl_mulai_tp,
        AbsensiGuru.tanggal <= tgl_selesai_tp
    )
    statistik = {
        'hadir': semua_absensi.filter(AbsensiGuru.status == 'hadir').count(),
        'terlambat': semua_absensi.filter(AbsensiGuru.status == 'terlambat').count(),
        'izin': semua_absensi.filter(AbsensiGuru.status.in_(['izin', 'sakit'])).count(),
        'alfa': semua_absensi.filter(AbsensiGuru.status == 'alfa').count(),
    }
    nama_bulan_lengkap = ['Jan','Peb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nop','Des']
    rentang_bulan = []
    current = tgl_mulai_tp
    while current <= tgl_selesai_tp:
        rentang_bulan.append((current.month, current.year))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    label_bulan = []
    data_hadir = []
    data_terlambat = []
    data_izin = []
    data_alfa = []
    for bln, thn in rentang_bulan:
        label_bulan.append(f"{nama_bulan_lengkap[bln - 1]}")
        filter_bulan = semua_absensi.filter(
            extract('year', AbsensiGuru.tanggal) == thn,
            extract('month', AbsensiGuru.tanggal) == bln
        )
        data_hadir.append(filter_bulan.filter(AbsensiGuru.status == 'hadir').count())
        data_terlambat.append(filter_bulan.filter(AbsensiGuru.status == 'terlambat').count())
        data_izin.append(filter_bulan.filter(AbsensiGuru.status.in_(['izin', 'sakit'])).count())
        data_alfa.append(filter_bulan.filter(AbsensiGuru.status == 'alfa').count())
    riwayat_terbaru = semua_absensi.order_by(
        AbsensiGuru.tanggal.desc()
    ).limit(5).all()

    # ✅ AMBIL JAM DARI PENGATURAN
    jam = ambil_jam_pengaturan()
    jam_masuk_tepat = jam['jam_masuk_tepat']
    batas_terlambat = jam['batas_terlambat']
    jam_tutup_absensi = jam['jam_tutup_absensi']
    jam_pulang_resmi = jam['jam_pulang_resmi']

    return render_template(
        'sections/absensi/dashboard.html',
        user=guru,
        guru=guru,
        absensi=absensi_hari_ini,
        hari_ini=hari_ini.strftime('%d %B %Y'),
        label_tp=label_tp,
        tgl_mulai_tp=tgl_mulai_tp.strftime('%d/%m/%Y'),
        tgl_selesai_tp=tgl_selesai_tp.strftime('%d/%m/%Y'),
        statistik=statistik,
        riwayat_terbaru=riwayat_terbaru,
        label_bulan=label_bulan,
        data_hadir=data_hadir,
        data_terlambat=data_terlambat,
        data_izin=data_izin,
        data_alfa=data_alfa,
        halaman_aktif='absensi',
        active_page='dashboard',
        jam_masuk_tepat=jam_masuk_tepat,
        batas_terlambat=batas_terlambat,
        jam_tutup_absensi=jam_tutup_absensi,
        jam_pulang_resmi=jam_pulang_resmi,
    )

@absensi_guru_bp.route('/absensi-harian')
def absensi_harian():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))

    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()

    if not guru:
        flash('Akun ini tidak memiliki akses.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))
    hari_ini = waktu_wita().date()
    absensi_hari_ini = AbsensiGuru.query.filter_by(
        guru_id=guru.id,
        tanggal=hari_ini
    ).first()
    tp_terpilih = None
    if g.tahun_pelajaran:
        tp_terpilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    if not tp_terpilih:
        tp_terpilih = TahunPelajaran.query.filter_by(aktif=True).first()
    if tp_terpilih:
        tgl_mulai_tp = tp_terpilih.tanggal_mulai
        tgl_selesai_tp = tp_terpilih.tanggal_selesai
    else:
        tgl_mulai_tp = date(hari_ini.year, 7, 1)
        tgl_selesai_tp = date(hari_ini.year + 1, 6, 30)
    filter_bulan = request.args.get('bulan', type=int) or hari_ini.month
    filter_tahun = request.args.get('tahun', type=int) or hari_ini.year
    absensi_query = AbsensiGuru.query.filter(
        AbsensiGuru.guru_id == guru.id,
        extract('year', AbsensiGuru.tanggal) == filter_tahun,
        extract('month', AbsensiGuru.tanggal) == filter_bulan,
        AbsensiGuru.tanggal >= tgl_mulai_tp,
        AbsensiGuru.tanggal <= tgl_selesai_tp
    ).order_by(AbsensiGuru.tanggal.desc())
    absensi_list = absensi_query.all()
    total_hadir = absensi_query.filter(AbsensiGuru.status == 'hadir').count()
    total_terlambat = absensi_query.filter(AbsensiGuru.status == 'terlambat').count()
    total_izin = absensi_query.filter(AbsensiGuru.status.in_(['izin', 'sakit'])).count()
    total_alfa = absensi_query.filter(AbsensiGuru.status == 'alfa').count()
    jam = ambil_jam_pengaturan()
    jam_masuk_tepat = jam['jam_masuk_tepat']
    batas_terlambat = jam['batas_terlambat']
    jam_tutup_absensi = jam['jam_tutup_absensi']
    jam_pulang_resmi = jam['jam_pulang_resmi']
    
    return render_template(
        'sections/absensi/absensi.html',
        user=guru,
        guru=guru,
        absensi=absensi_hari_ini,
        absensi_list=absensi_list,
        hari_ini=hari_ini.strftime('%d %B %Y'),
        total_hadir=total_hadir,
        total_terlambat=total_terlambat,
        total_izin=total_izin,
        total_alfa=total_alfa,
        filter_bulan=filter_bulan,
        filter_tahun=filter_tahun,
        halaman_aktif='absensi',
        active_page='absensi_harian',
        jam_masuk_tepat=jam_masuk_tepat,
        batas_terlambat=batas_terlambat,
        jam_tutup_absensi=jam_tutup_absensi,
        jam_pulang_resmi=jam_pulang_resmi,
    )

# === 1. Tombol Absen Masuk ===
@absensi_guru_bp.route('/absen-masuk', methods=['POST'])
def absen_masuk():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))
    halaman_asal = request.referrer
    if halaman_asal and request.host not in halaman_asal:
        halaman_asal = None

    # ✅ === CEK WIFI SEKOLAH — WAJIB ===
    dari_sekolah, ip_klien = cek_dari_wifi_sekolah()
    if not dari_sekolah:
        flash(f'⚠️ Absen Masuk hanya bisa dari Wifi Sekolah.\nIP Anda: {ip_klien}', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))

    if sudah_lewat_batas_absensi():
        flash('⚠️ Sudah lewat jam 11:00. Absensi ditutup. Terhitung ALFA.', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()
    if not guru:
        flash('Akun tidak valid.', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    hari_ini = waktu_wita().date()
    jam_sekarang = waktu_wita().strftime("%H:%M")
    alasan_telat = request.form.get('alasan_keterlambatan', '').strip()
    
    absensi = AbsensiGuru.query.filter_by(guru_id=guru.id, tanggal=hari_ini).first()
    if absensi and absensi.jam_masuk:
        flash('Anda sudah absen masuk hari ini.', 'absensi_info')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    status, keterangan = hitung_status_absensi(jam_sekarang)
    if alasan_telat and status == 'terlambat':
        if keterangan:
            keterangan = f"{keterangan} | Alasan: {alasan_telat}"
        else:
            keterangan = f"Alasan keterlambatan: {alasan_telat}"
    
    if not absensi:
        absensi = AbsensiGuru(
            guru_id=guru.id, tanggal=hari_ini,
            jam_masuk=jam_sekarang, status=status, keterangan=keterangan
        )
        db.session.add(absensi)
    else:
        absensi.jam_masuk = jam_sekarang
        absensi.status = status
        absensi.keterangan = keterangan
    
    db.session.commit()
    flash(f"Absen Masuk berhasil: {jam_sekarang} — {status.upper()}", "absensi_success")
    return redirect(halaman_asal or url_for('absensi_guru.dashboard'))

# === 2. Tombol Absen Pulang ===
@absensi_guru_bp.route('/absen-pulang', methods=['POST'])
def absen_pulang():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))
    halaman_asal = request.referrer
    if halaman_asal and request.host not in halaman_asal:
        halaman_asal = None

    # ✅ === CEK WIFI SEKOLAH — WAJIB UNTUK ABSEN PULANG JUGA ===
    dari_sekolah, ip_klien = cek_dari_wifi_sekolah()
    if not dari_sekolah:
        flash(f'⚠️ Absen Pulang hanya bisa dari Wifi Sekolah.\nIP Anda: {ip_klien}', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    # ✅ === SELESAI CEK IP ===

    if belum_jam_pulang():
        flash('⚠️ Belum jam 15:00. Absen pulang belum diperbolehkan.', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()
    if not guru:
        flash('Akun tidak valid.', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    hari_ini = waktu_wita().date()
    jam_sekarang = waktu_wita().strftime("%H:%M")
    
    absensi = AbsensiGuru.query.filter_by(guru_id=guru.id, tanggal=hari_ini).first()
    if not absensi or not absensi.jam_masuk:
        flash('⚠️ Anda belum absen masuk.', 'absensi_danger')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    if absensi.jam_pulang:
        flash('✅ Anda sudah absen pulang hari ini.', 'absensi_info')
        return redirect(halaman_asal or url_for('absensi_guru.dashboard'))
    
    absensi.jam_pulang = jam_sekarang
    db.session.commit()
    flash(f"✅ Absen Pulang berhasil: {jam_sekarang}", "absensi_success")
    return redirect(halaman_asal or url_for('absensi_guru.dashboard'))

@absensi_guru_bp.route('/qr-absensi-data')
def qr_absensi_data():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        return jsonify({"status": "error", "pesan": "Silakan login dulu"}), 401
    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()
    if not guru:
        return jsonify({"status": "error", "pesan": "Data guru tidak ditemukan"}), 404
    hari_ini = waktu_wita().date()
    hari_ini_str = hari_ini.strftime("%Y-%m-%d")
    absensi_hari_ini = AbsensiGuru.query.filter_by(
        guru_id=guru.id, tanggal=hari_ini
    ).first()
    if absensi_hari_ini and absensi_hari_ini.jam_masuk:
        if belum_jam_pulang():
            return jsonify({
                "status": "error",
                "pesan": f"Belum jam 15:00. QR Pulang belum tersedia."
            }), 403
        data_qr = f"guru:{guru.id}:tanggal:{hari_ini_str}:tipe:pulang:pembuat:guru"
    else:
        if sudah_lewat_batas_absensi():
            return jsonify({
                "status": "error",
                "pesan": "Sudah lewat jam 11:00. Absensi ditutup."
            }), 403
        data_qr = f"guru:{guru.id}:tanggal:{hari_ini_str}:tipe:masuk:pembuat:guru"
    qr_img = qrcode.make(data_qr)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    return jsonify({
        "status": "sukses",
        "qr_code": qr_base64,
        "nama": guru.nama,
        "nip": guru.nip,
        "hari_ini": hari_ini_str
    })

@absensi_guru_bp.route('/qr-absensi')
def qr_absensi():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))
    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()
    if not guru:
        flash('Akun tidak valid.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))
    hari_ini = waktu_wita().date().strftime("%Y-%m-%d")
    data_qr = f"guru:{guru.id}:tanggal:{hari_ini}:tipe:masuk:pembuat:guru"
    qr_img = qrcode.make(data_qr)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    return render_template(
        'sections/absensi/qr_absensi.html',
        qr_code=qr_base64,
        guru=guru,
        hari_ini=hari_ini
    )

@absensi_guru_bp.route('/scan-qr-proses', methods=['POST'])
def scan_qr_proses():
    hari_ini_date = waktu_wita().date()
    hari_ini_str = hari_ini_date.strftime("%Y-%m-%d")

    # === CEK BATAS WAKTU UNTUK ABSEN MASUK ===
    if sudah_lewat_batas_absensi():
        return jsonify({"status": "error", "pesan": "Sudah lewat jam 11:00. Absensi ditutup."}), 403

    data_scan = request.form.get('data_qr') or request.json.get('data_qr') or request.form.get('qr_data')
    if not data_scan:
        return jsonify({"status": "error", "pesan": "Data QR tidak terbaca"}), 400

    guru_id = None
    tipe = "masuk"
    tanggal_qr = None
    pembuat_qr = None  # 'guru' atau 'admin'

    # === ✅ PARSE QR DARI MONITORING: semua_guru:tanggal:{YYYY-MM-DD}:pembuat:admin ===
    if data_scan.startswith("semua_guru:tanggal:"):
        bagian = data_scan.split(":")
        # Format yang dibuat: "semua_guru:tanggal:2026-09-10:pembuat:admin"
        if len(bagian) >= 4:
            tanggal_qr = bagian[2].strip()
            pembuat_qr = bagian[3].strip()  # "admin"
            guru_id = "SEMUA"  # Ambil dari sesi pengguna yang men-scan

            # ✅ TENTUKAN TIPE OTOMATIS SESUAI JAM SAAT SCAN (WITA)
            jam_sekarang = waktu_wita()
            if jam_sekarang.hour < 15:
                tipe = "masuk"
            else:
                tipe = "pulang"

    # === PARSE QR DARI HALAMAN ABSENSI GURU ===
    elif data_scan.startswith("guru:"):
        bagian = data_scan.split(":")
        if len(bagian) >= 8:
            guru_id = bagian[1]
            tanggal_qr = bagian[3]
            tipe = bagian[5]
            pembuat_qr = bagian[7]
        elif len(bagian) >= 6:
            guru_id = bagian[1]
            tanggal_qr = bagian[3]
            tipe = bagian[5]
            pembuat_qr = 'guru'

    # === FALLBACK: NIP GURU LANGSUNG ===
    else:
        guru = Guru.query.filter_by(nip=data_scan).first()
        if guru:
            guru_id = guru.id
            tanggal_qr = hari_ini_str
            pembuat_qr = 'admin'
        else:
            return jsonify({"status": "error", "pesan": "QR tidak dikenali"}), 404

    if not guru_id:
        return jsonify({"status": "error", "pesan": "ID Guru tidak ditemukan"}), 404

    # ==============================================================
    # 🔒 ATURAN 1: QR HANYA BERLAKU HARI INI
    # ==============================================================
    if tanggal_qr and tanggal_qr != hari_ini_str:
        return jsonify({
            "status": "error",
            "pesan": f"❌ QR sudah kadaluarsa! Berlaku untuk {tanggal_qr}, hari ini {hari_ini_str}"
        }), 403

    # ==============================================================
    # 🔒 DETEKSI MODE SCAN
    # ==============================================================
    mode_saat_ini = 'mode_sekolah'  # Default: izinkan mesin pemindai
    if session.get('absensi_logged_in') and session.get('absensi_sistem_mode') == 'absensi':
        mode_saat_ini = 'mode_absensi'  # Dari halaman absensi guru
    elif session.get('logged_in') and session.get('sistem_mode') in ['sekolah', 'admin', 'kepala_sekolah', 'tu', 'monitoring']:
        mode_saat_ini = 'mode_sekolah'  # Dari sistem utama sekolah

    # ==============================================================
    # 🔒 ATURAN 2: SIAPA BOLEH MEN-SCAN
    # ==============================================================
    # === QR DARI MONITORING/ADMIN ===
    if pembuat_qr == 'admin':
        # ❌ DITOLAK: discan dari sistem sekolah itu sendiri
        if mode_saat_ini == 'mode_sekolah':
            return jsonify({
                "status": "error",
                "pesan": "❌ QR dari Monitoring hanya boleh discan dari Mode Absensi Guru."
            }), 403
        # ✅ DIPERBOLEHKAN: dari mode absensi guru

    # === QR DARI HALAMAN ABSENSI GURU ===
    elif pembuat_qr == 'guru':
        # ❌ DITOLAK: discan dari mode absensi
        if mode_saat_ini == 'mode_absensi':
            return jsonify({
                "status": "error",
                "pesan": "❌ QR buatan halaman absensi hanya boleh discan dari Monitoring atau Mesin Pemindai."
            }), 403

    # ==============================================================
    # ✅ AMBIL GURU ID DARI SESI JIKA QR SEMUA_GURU
    # ==============================================================
    if guru_id == "SEMUA":
        if mode_saat_ini == 'mode_absensi' and session.get('absensi_guru_id'):
            guru_id = str(session.get('absensi_guru_id'))
        else:
            return jsonify({
                "status": "error",
                "pesan": "❌ QR ini hanya bisa dipakai oleh guru yang sedang login dari Mode Absensi."
            }), 403

    guru = Guru.query.get(guru_id)
    if not guru:
        return jsonify({"status": "error", "pesan": "Data guru tidak ditemukan"}), 404

    jam_sekarang = waktu_wita().strftime("%H:%M")
    absensi = AbsensiGuru.query.filter_by(guru_id=guru.id, tanggal=hari_ini_date).first()

    # ==============================================================
    # 🔒 ATURAN 3: ABSEN PULANG WAJIB SUDAH ABSEN MASUK DULU
    # ==============================================================
    if tipe == "pulang":
        if belum_jam_pulang():
            return jsonify({"status": "error", "pesan": "Belum jam 15:00. Absen pulang belum diperbolehkan."}), 403
        if not absensi or not absensi.jam_masuk:
            return jsonify({"status": "error", "pesan": "❌ Belum absen masuk. Silakan absen masuk terlebih dahulu."}), 403
        if absensi.jam_pulang:
            return jsonify({"status": "info", "pesan": "✅ Sudah absen pulang", "jam": absensi.jam_pulang})

        absensi.jam_pulang = jam_sekarang
        db.session.commit()
        return jsonify({
            "status": "sukses",
            "pesan": f"✅ Absen Pulang berhasil atas nama {guru.nama}",
            "jam": jam_sekarang
        })

    # === ✅ PROSES ABSEN MASUK ===
    elif tipe == "masuk":
        if absensi and absensi.jam_masuk:
            return jsonify({"status": "info", "pesan": "✅ Sudah absen masuk", "jam": absensi.jam_masuk})

        status, keterangan = hitung_status_absensi(jam_sekarang)
        if not absensi:
            absensi = AbsensiGuru(
                guru_id=guru.id, tanggal=hari_ini_date,
                jam_masuk=jam_sekarang, status=status, keterangan=keterangan
            )
            db.session.add(absensi)
        else:
            absensi.jam_masuk = jam_sekarang
            absensi.status = status
            absensi.keterangan = keterangan

        db.session.commit()
        return jsonify({
            "status": "sukses",
            "pesan": f"✅ Absen Masuk berhasil atas nama {guru.nama}",
            "jam": jam_sekarang,
            "status_kehadiran": status
        })

@absensi_guru_bp.route('/api/mesin-absen', methods=['POST'])
def api_mesin_absen():
    if sudah_lewat_batas_absensi():
        return jsonify({"status": "error", "pesan": "Sudah lewat jam 11:00. Absensi ditutup."}), 403
    data = request.get_json() or request.form
    kode_kartu = data.get('kode_kartu')
    tipe = data.get('tipe', 'masuk')
    
    if not kode_kartu:
        return jsonify({"status": "error", "pesan": "Kode kartu kosong"}), 400
    
    guru = Guru.query.filter_by(nip=kode_kartu).first()
    if not guru:
        return jsonify({"status": "error", "pesan": "Kartu tidak terdaftar"}), 404
    
    hari_ini = waktu_wita().date()
    jam_sekarang = waktu_wita().strftime("%H:%M")
    absensi = AbsensiGuru.query.filter_by(guru_id=guru.id, tanggal=hari_ini).first()
    
    if tipe == "masuk":
        if absensi and absensi.jam_masuk:
            return jsonify({"status": "sudah", "jam": absensi.jam_masuk})
        
        status, keterangan = hitung_status_absensi(jam_sekarang)
        if not absensi:
            absensi = AbsensiGuru(guru_id=guru.id, tanggal=hari_ini,
                jam_masuk=jam_sekarang, status=status, keterangan=keterangan)
            db.session.add(absensi)
        else:
            absensi.jam_masuk = jam_sekarang
            absensi.status = status
            absensi.keterangan = keterangan
        
        db.session.commit()
        return jsonify({"status": "sukses", "nama": guru.nama, "jam": jam_sekarang, "status": status})
    
    elif tipe == "pulang":
        if belum_jam_pulang():
            return jsonify({"status": "error", "pesan": "Belum jam 15:00. Absen pulang belum diperbolehkan."}), 403
        if not absensi or not absensi.jam_masuk:
            return jsonify({"status": "belum_masuk"}), 400
        if absensi.jam_pulang:
            return jsonify({"status": "sudah_pulang", "jam": absensi.jam_pulang})
        
        absensi.jam_pulang = jam_sekarang
        db.session.commit()
        return jsonify({"status": "sukses", "nama": guru.nama, "jam_pulang": jam_sekarang})

# === ✅ HALAMAN REKAPITULASI ABSENSI ===
@absensi_guru_bp.route('/rekap-absensi')
def rekap_absensi():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))

    guru = Guru.query.filter_by(
        id=session.get('absensi_guru_id')
    ).first()

    if not guru:
        flash('Akun ini tidak memiliki akses.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))
    
    hari_ini = waktu_wita().date()
    
    # === Ambil Tahun Pelajaran Aktif ===
    tp_terpilih = None
    if g.tahun_pelajaran:
        tp_terpilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    if not tp_terpilih:
        tp_terpilih = TahunPelajaran.query.filter_by(aktif=True).first()
    
    if tp_terpilih:
        tgl_mulai_tp = tp_terpilih.tanggal_mulai
        tgl_selesai_tp = tp_terpilih.tanggal_selesai
        kode_parts = tp_terpilih.kode.split('-')
        if len(kode_parts) == 2:
            kode_tahun = kode_parts[0]
            semester = kode_parts[1]
            nama_semester = "Ganjil" if semester == "1" else "Genap"
            label_tp = f"{kode_tahun} / Semester {nama_semester}"
        else:
            label_tp = tp_terpilih.kode
    else:
        tgl_mulai_tp = date(hari_ini.year, 7, 1)
        tgl_selesai_tp = date(hari_ini.year + 1, 6, 30)
        label_tp = f"{hari_ini.year}/{hari_ini.year + 1}"
    
    # === Filter Bulan & Tahun ===
    filter_bulan = request.args.get('bulan', type=int) or hari_ini.month
    filter_tahun = request.args.get('tahun', type=int) or hari_ini.year
    
    # === Query Rekap Absensi ===
    rekap_query = AbsensiGuru.query.filter(
        AbsensiGuru.guru_id == guru.id,
        extract('year', AbsensiGuru.tanggal) == filter_tahun,
        extract('month', AbsensiGuru.tanggal) == filter_bulan,
        AbsensiGuru.tanggal >= tgl_mulai_tp,
        AbsensiGuru.tanggal <= tgl_selesai_tp
    )
    
    # Hitung masing-masing status
    jml_hadir = rekap_query.filter(AbsensiGuru.status == 'hadir').count()
    jml_terlambat = rekap_query.filter(AbsensiGuru.status == 'terlambat').count()
    jml_izin = rekap_query.filter(AbsensiGuru.status.in_(['izin', 'sakit'])).count()
    jml_alfa = rekap_query.filter(AbsensiGuru.status == 'alfa').count()
    
    total_hari = jml_hadir + jml_terlambat + jml_izin + jml_alfa
    
    # Hitung Persentase Kehadiran
    persen_hadir = 0
    if total_hari > 0:
        persen_hadir = round(((jml_hadir + jml_terlambat) / total_hari) * 100, 1)
    
    # Nama Bulan
    nama_bulan = [
        'Januari','Pebruari','Maret','April','Mei','Juni',
        'Juli','Agustus','September','Oktober','Nopember','Desember'
    ]
    nama_bulan_terpilih = nama_bulan[filter_bulan - 1]
    
    # Riwayat Absensi Bulan Ini
    riwayat_bulan_ini = rekap_query.order_by(AbsensiGuru.tanggal.desc()).all()
    
    return render_template(
        'sections/absensi/rekap_absensi.html',
        user=guru,
        guru=guru,
        label_tp=label_tp,
        hari_ini=hari_ini.strftime('%d %B %Y'),
        
        filter_bulan=filter_bulan,
        filter_tahun=filter_tahun,
        nama_bulan_terpilih=nama_bulan_terpilih,
        
        jml_hadir=jml_hadir,
        jml_terlambat=jml_terlambat,
        jml_izin=jml_izin,
        jml_alfa=jml_alfa,
        total_hari=total_hari,
        persen_hadir=persen_hadir,
        
        riwayat_bulan_ini=riwayat_bulan_ini,
        
        halaman_aktif='absensi',
        active_page='rekap_absensi'
    )

# === 📤 EXPORT REKAPITULASI ABSENSI — VERSI LENGKAP ===
@absensi_guru_bp.route('/export-rekap-absensi', methods=['POST'])
def export_rekap_absensi():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))

    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()
    if not guru:
        flash('Akun ini tidak memiliki akses.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))

    # === 1. Baca Parameter DARI FORM YANG BARU ===
    jenis_export = request.form.get('jenis_export', 'perbulan')

    # -- Per Bulan --
    bulan_pilih = request.form.get('bulan_pilih')
    tahun_pilih = request.form.get('tahun_pilih', type=int)

    # -- Semua Bulan --
    tahun_semua = request.form.get('tahun_semua', type=int)

    # -- Rentang Bulan & Tahun --
    bulan_awal = request.form.get('bulan_awal')
    tahun_awal = request.form.get('tahun_awal', type=int)
    bulan_akhir = request.form.get('bulan_akhir')
    tahun_akhir = request.form.get('tahun_akhir', type=int)

    # === 2. Tentukan Rentang Tanggal berdasarkan TAHUN PELAJARAN ===
    hari_ini = waktu_wita().date()
    tgl_mulai_tp, tgl_selesai_tp, label_tp = None, None, ""

    if g.tahun_pelajaran:
        tp_terpilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    else:
        tp_terpilih = TahunPelajaran.query.filter_by(aktif=True).first()

    if tp_terpilih:
        tgl_mulai_tp = tp_terpilih.tanggal_mulai
        tgl_selesai_tp = tp_terpilih.tanggal_selesai
        label_tp = tp_terpilih.kode
    else:
        tgl_mulai_tp = date(hari_ini.year, 7, 1)
        tgl_selesai_tp = date(hari_ini.year + 1, 6, 30)
        label_tp = f"{hari_ini.year}/{hari_ini.year + 1}"

    # === 3. Susun QUERY sesuai JENIS EXPORT ===
    nama_bulan = ['Januari','Pebruari','Maret','April','Mei','Juni',
                  'Juli','Agustus','September','Oktober','Nopember','Desember']
    nama_bulan_label = ""
    data_absensi = []

    # --- PILIHAN 1: PER BULAN ---
    if jenis_export == 'perbulan':
        bln_int = int(bulan_pilih)
        thn_int = tahun_pilih or hari_ini.year
        tgl_awal = date(thn_int, bln_int, 1)
        if bln_int == 12:
            tgl_akhir = date(thn_int, 12, 31)
        else:
            tgl_akhir = date(thn_int, bln_int + 1, 1) - timedelta(days=1)

        nama_bulan_label = f"{nama_bulan[bln_int - 1]}_{thn_int}"

        data_absensi = AbsensiGuru.query.filter(
            AbsensiGuru.guru_id == guru.id,
            AbsensiGuru.tanggal >= tgl_awal,
            AbsensiGuru.tanggal <= tgl_akhir,
            AbsensiGuru.tanggal >= tgl_mulai_tp,
            AbsensiGuru.tanggal <= tgl_selesai_tp
        ).order_by(AbsensiGuru.tanggal).all()

    # --- PILIHAN 2: SEMUA BULAN (1 TAHUN) ---
    elif jenis_export == 'semua':
        thn_int = tahun_semua or hari_ini.year
        tgl_awal = date(thn_int, 1, 1)
        tgl_akhir = date(thn_int, 12, 31)
        nama_bulan_label = f"SemuaBulan_{thn_int}"

        data_absensi = AbsensiGuru.query.filter(
            AbsensiGuru.guru_id == guru.id,
            extract('year', AbsensiGuru.tanggal) == thn_int,
            AbsensiGuru.tanggal >= tgl_awal,
            AbsensiGuru.tanggal <= tgl_akhir,
            AbsensiGuru.tanggal >= tgl_mulai_tp,
            AbsensiGuru.tanggal <= tgl_selesai_tp
        ).order_by(AbsensiGuru.tanggal).all()

    # --- PILIHAN 3: RENTANG BULAN & TAHUN (BISA BEDA TAHUN) ---
    elif jenis_export == 'rentang':
        bln_awal_int = int(bulan_awal)
        thn_awal_int = tahun_awal or hari_ini.year
        bln_akhir_int = int(bulan_akhir)
        thn_akhir_int = tahun_akhir or hari_ini.year

        # Buat tanggal awal & akhir
        tgl_mulai_rentang = date(thn_awal_int, bln_awal_int, 1)
        if bln_akhir_int == 12:
            tgl_selesai_rentang = date(thn_akhir_int, 12, 31)
        else:
            tgl_selesai_rentang = date(thn_akhir_int, bln_akhir_int + 1, 1) - timedelta(days=1)

        nama_bulan_label = f"{bulan_awal}-{bulan_akhir}_{thn_awal_int}-{thn_akhir_int}"

        data_absensi = AbsensiGuru.query.filter(
            AbsensiGuru.guru_id == guru.id,
            AbsensiGuru.tanggal >= tgl_mulai_rentang,
            AbsensiGuru.tanggal <= tgl_selesai_rentang,
            AbsensiGuru.tanggal >= tgl_mulai_tp,
            AbsensiGuru.tanggal <= tgl_selesai_tp
        ).order_by(AbsensiGuru.tanggal).all()

    # === 4. Cek Data Kosong ===
    if not data_absensi:
        flash('Tidak ada data absensi untuk rentang yang dipilih.', 'absensi_warning')
        return redirect(url_for('absensi_guru.rekap_absensi'))

    # === 5. Susun Data untuk Excel ===
    rows = []
    for item in data_absensi:
        hari_nama = ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'][item.tanggal.weekday()]
        rows.append({
            'Tanggal': item.tanggal.strftime('%d/%m/%Y'),
            'Hari': hari_nama,
            'Jam Masuk': item.jam_masuk or '-',
            'Jam Pulang': item.jam_pulang or '-',
            'Status': (item.status or '-').upper(),
            'Keterangan': item.keterangan or '-'
        })

    # === 6. Hitung Ringkasan ===
    jml_hadir = sum(1 for r in data_absensi if r.status == 'hadir')
    jml_terlambat = sum(1 for r in data_absensi if r.status == 'terlambat')
    jml_izin = sum(1 for r in data_absensi if r.status in ('izin','sakit'))
    jml_alfa = sum(1 for r in data_absensi if r.status == 'alfa')
    total = len(data_absensi)
    persen = round(((jml_hadir + jml_terlambat) / total) * 100, 1) if total > 0 else 0

    # === 7. Buat Excel ===
    import pandas as pd
    from io import BytesIO

    df = pd.DataFrame(rows)
    ringkasan = pd.DataFrame([
        {'Tanggal': '---', 'Hari': '---', 'Jam Masuk': '---', 'Jam Pulang': '---', 'Status': '---', 'Keterangan': '---'},
        {'Tanggal': '', 'Hari': '📊 RINGKASAN', 'Jam Masuk': '', 'Jam Pulang': '', 'Status': '', 'Keterangan': ''},
        {'Tanggal': '', 'Hari': '✅ Hadir', 'Jam Masuk': jml_hadir, 'Jam Pulang': 'hari', 'Status': '', 'Keterangan': ''},
        {'Tanggal': '', 'Hari': '⏰ Terlambat', 'Jam Masuk': jml_terlambat, 'Jam Pulang': 'hari', 'Status': '', 'Keterangan': ''},
        {'Tanggal': '', 'Hari': '📝 Izin/Sakit', 'Jam Masuk': jml_izin, 'Jam Pulang': 'hari', 'Status': '', 'Keterangan': ''},
        {'Tanggal': '', 'Hari': '❌ Alfa', 'Jam Masuk': jml_alfa, 'Jam Pulang': 'hari', 'Status': '', 'Keterangan': ''},
        {'Tanggal': '', 'Hari': '📋 Total Hari', 'Jam Masuk': total, 'Jam Pulang': 'hari', 'Status': '', 'Keterangan': ''},
        {'Tanggal': '', 'Hari': '📈 Kehadiran', 'Jam Masuk': f'{persen} %', 'Jam Pulang': '', 'Status': '', 'Keterangan': ''},
    ])

    df_final = pd.concat([df, ringkasan], ignore_index=True)

    output = BytesIO()
    nama_file = f"Rekap_Absensi_{guru.nama or 'Guru'}_{nama_bulan_label}.xlsx"

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Rekap Absensi')

    output.seek(0)

    # === 8. Kirim File ===
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={nama_file}"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

# ==============================================
# ✅ HALAMAN RINCIAN GAJI — SEJAJAR DENGAN REKAP ABSENSI
# ==============================================
@absensi_guru_bp.route('/rincian-gaji')
def rincian_gaji():
    if not (
        session.get('absensi_logged_in') is True and
        session.get('absensi_sistem_mode') == 'absensi' and
        session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))

    guru = Guru.query.filter_by(id=session.get('absensi_guru_id')).first()
    if not guru:
        flash('Akun ini tidak memiliki akses.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))

    hari_ini = waktu_wita().date()

    filter_bulan = request.args.get('bulan', type=int) or hari_ini.month
    filter_tahun = request.args.get('tahun', type=int) or hari_ini.year

    # Daftar nama bulan
    nama_bulan_list = ['','Januari','Februari','Maret','April','Mei','Juni',
                       'Juli','Agustus','September','Oktober','November','Desember']
    nama_bulan_terpilih = nama_bulan_list[filter_bulan]

    # === Cari data gaji guru tersebut di bulan yang dipilih ===
    gaji_data = GajiGuru.query.filter_by(
        guru_id=guru.id,
        bulan=filter_bulan,
        tahun=filter_tahun
    ).first()

    rincian = None
    if gaji_data:
        # Hitung ulang agar sinkron
        total_penerimaan = (gaji_data.gaji_pokok + gaji_data.tunjangan_jabatan +
                            gaji_data.tunjangan_fungsional + gaji_data.tunjangan_lain + gaji_data.bonus)
        total_potongan = (gaji_data.potongan_wajib + gaji_data.pph +
                          gaji_data.potongan_terlambat + gaji_data.pinjaman)
        gaji_bersih = total_penerimaan - total_potongan

        rincian = {
            'nama': guru.nama,
            'nip': guru.nip,
            'jabatan': guru.jabatan,
            'gaji_pokok': float(gaji_data.gaji_pokok),
            'tunjangan_jabatan': float(gaji_data.tunjangan_jabatan),
            'tunjangan_fungsional': float(gaji_data.tunjangan_fungsional),
            'tunjangan_lain': float(gaji_data.tunjangan_lain),
            'bonus': float(gaji_data.bonus),
            'potongan_wajib': float(gaji_data.potongan_wajib),
            'pph': float(gaji_data.pph),
            'potongan_terlambat': float(gaji_data.potongan_terlambat),
            'pinjaman': float(gaji_data.pinjaman),
            'total_penerimaan': float(total_penerimaan),
            'total_potongan': float(total_potongan),
            'gaji_bersih': float(gaji_bersih),
            'terbilang': terbilang(gaji_bersih),
            'kode_verifikasi': gaji_data.kode_verifikasi or '-'
        }

    # === Riwayat gaji 12 bulan terakhir untuk daftar di bawah slip ===
    daftar_gaji_db = GajiGuru.query.filter_by(
        guru_id=guru.id
    ).order_by(GajiGuru.tahun.desc(), GajiGuru.bulan.desc()).limit(12).all()

    daftar_gaji = []
    for item in daftar_gaji_db:
        daftar_gaji.append({
            'bulan': nama_bulan_list[item.bulan],
            'bulan_num': item.bulan,
            'tahun': item.tahun,
            'gaji_bersih': float(item.gaji_bersih),
            'status': item.status
        })

    return render_template(
        'sections/absensi/rincian_gaji.html',  # Taruh di folder yang sama dengan absensi
        user=guru,
        guru=guru,
        nama_bulan=nama_bulan_terpilih,
        tahun=filter_tahun,
        filter_bulan=filter_bulan,
        filter_tahun=filter_tahun,
        rincian=rincian,
        daftar_gaji=daftar_gaji,
        hari_ini=hari_ini.strftime('%d %B %Y'),
        halaman_aktif='absensi',
        active_page='rincian_gaji'
    )