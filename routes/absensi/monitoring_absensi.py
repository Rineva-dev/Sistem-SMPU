# ==================================================
# ✅ MONITORING ABSENSI — KHUSUS SISTEM SEKOLAH
# Hanya dapat diakses oleh Admin / Kepala Sekolah / TU
# TIDAK BOLEH diakses dari Sesi Absensi Guru
# ==================================================
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, make_response, g, jsonify
from models import Guru, AbsensiGuru, TahunPelajaran, db, User
from datetime import date, datetime, timedelta
from sqlalchemy import extract
import pandas as pd
from io import BytesIO
import qrcode
import io
import base64

# ✅ Blueprint Terpisah
monitoring_bp = Blueprint('monitoring_absensi', __name__)

# ==============================================
# ✅ FUNGSI BANTU: AMBIL TAHUN PELAJARAN AKTIF
# ==============================================
def ambil_tahun_pelajaran():
    """
    Mengembalikan (tgl_mulai_tp, tgl_selesai_tp, label_tp)
    berdasarkan g.tahun_pelajaran atau tahun pelajaran aktif
    """
    hari_ini = date.today()
    tp_terpilih = None
    if hasattr(g, 'tahun_pelajaran') and g.tahun_pelajaran:
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

# ==============================================
# ✅ FUNGSI BANTU: CEK HAK AKSES SISTEM SEKOLAH
# ==============================================
def cek_akses_monitoring():
    """
    Aturan Tegas:
    1. ❌ Ditolak jika dari Sesi Absensi Guru
    2. ✅ Wajib login dari Sistem Sekolah (sesi user_id)
    3. ✅ Harus memiliki jabatan/tugas yang diizinkan
    """
    # 🔴 TOLAK SISTEM ABSENSI SECARA TEGAS
    if not (session.get('logged_in') is True and session.get('sistem_mode') == 'sekolah' and session.get('user_id')):
        flash('Halaman ini hanya dapat diakses dari Sistem Sekolah.', 'warning')
        return False, 'tolak_absensi'

    # 🔴 WAJIB LOGIN SISTEM SEKOLAH
    if not session.get('user_id'):
        flash('⚠️ Silakan login dari Sistem Sekolah terlebih dahulu.', 'absensi_warning')
        return False, 'tolak_login'

    # 🟢 CEK JABATAN DAN TUGAS
    jabatan = session.get('jabatan', '')
    daftar_boleh = ["Kepala Sekolah", "Admin", "Tata Usaha", "TU", "Bendahara"]
    daftar_tugas = session.get('daftar_tugas', [])
    if not isinstance(daftar_tugas, list):
        daftar_tugas = []

    if jabatan in daftar_boleh or "Admin Sistem" in daftar_tugas or session.get('halaman_aktif') == 'admin_sistem':
        return True, None
    else:
        flash('⛔ Anda tidak memiliki izin untuk melihat halaman ini.', 'absensi_danger')
        return False, 'tolak_izin'

def belum_jam_pulang():
    """
    Mengembalikan True jika BELUM jam 15:00 hari ini
    Digunakan agar QR Pulang baru bisa dibuat setelah jam 15:00
    """
    jam_sekarang = datetime.now()
    batas_jam = jam_sekarang.replace(hour=15, minute=0, second=0, microsecond=0)
    return jam_sekarang < batas_jam

# ==================================================
# ✅ HALAMAN MONITORING ABSENSI
# ==================================================
@monitoring_bp.route('/monitoring-absensi')
def monitoring_absensi():
    """
    Halaman Monitoring Absensi SELURUH GURU
    Bisa difilter per Bulan & Tahun, dengan ringkasan per guru
    """
    # ✅ CEK HAK AKSES
    boleh, alasan = cek_akses_monitoring()
    if not boleh:
        if alasan == 'tolak_absensi':
            return redirect(url_for('login.halaman_login'))
        elif alasan == 'tolak_login':
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('dashboard'))

    # ✅ AMBIL DATA DARI SESI SISTEM SEKOLAH
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    user_name = session.get('user_name', 'Pengguna')
    jabatan = session.get('jabatan', '')
    halaman_aktif = session.get('halaman_aktif', 'utama')
    hari_ini = date.today()

    # === Ambil Tahun Pelajaran ===
    tgl_mulai_tp, tgl_selesai_tp, label_tp = ambil_tahun_pelajaran()
    # Pastikan nilai tahun pelajaran valid
    if not tgl_mulai_tp or not tgl_selesai_tp:
        tgl_mulai_tp = date(hari_ini.year, 7, 1)
        tgl_selesai_tp = date(hari_ini.year + 1, 6, 30)
        label_tp = f"{hari_ini.year}/{hari_ini.year + 1}"

    # === Filter Bulan & Tahun ===
    filter_bulan = request.args.get('bulan', type=int) or hari_ini.month
    filter_tahun = request.args.get('tahun', type=int) or hari_ini.year

    # === Daftar Bulan & Tahun untuk Dropdown ===
    nama_bulan_list = ['Januari','Pebruari','Maret','April','Mei','Juni',
                       'Juli','Agustus','September','Oktober','Nopember','Desember']
    daftar_bulan = [(i+1, nama_bulan_list[i]) for i in range(12)]
    daftar_tahun = []
    for thn in range(tgl_mulai_tp.year, tgl_selesai_tp.year + 2):
        daftar_tahun.append((thn, f"{thn}/{thn+1}"))
    nama_bulan_terpilih = nama_bulan_list[filter_bulan - 1]

    # === Rentang Tanggal Filter ===
    tgl_awal_filter = date(filter_tahun, filter_bulan, 1)
    if filter_bulan == 12:
        tgl_akhir_filter = date(filter_tahun, 12, 31)
    else:
        tgl_akhir_filter = date(filter_tahun, filter_bulan + 1, 1) - timedelta(days=1)

    # === Ambil SEMUA GURU AKTIF ===
    semua_guru = Guru.query.order_by(Guru.nama).all()

    # === Hitung Statistik untuk SETIAP GURU ===
    daftar_monitoring = []
    total_semua_hadir = total_semua_terlambat = total_semua_izin = total_semua_alfa = 0

    for guru in semua_guru:
        absensi_guru = AbsensiGuru.query.filter(
            AbsensiGuru.guru_id == guru.id,
            AbsensiGuru.tanggal.between(tgl_awal_filter, tgl_akhir_filter),
            AbsensiGuru.tanggal.between(tgl_mulai_tp, tgl_selesai_tp)
        )
        jml_hadir = absensi_guru.filter(AbsensiGuru.status == 'hadir').count()
        jml_terlambat = absensi_guru.filter(AbsensiGuru.status == 'terlambat').count()
        jml_izin = absensi_guru.filter(AbsensiGuru.status.in_(['izin','sakit'])).count()
        jml_alfa = absensi_guru.filter(AbsensiGuru.status == 'alfa').count()

        total_hari = jml_hadir + jml_terlambat + jml_izin + jml_alfa
        persen = round(((jml_hadir + jml_terlambat) / total_hari) * 100, 1) if total_hari > 0 else 0

        total_semua_hadir += jml_hadir
        total_semua_terlambat += jml_terlambat
        total_semua_izin += jml_izin
        total_semua_alfa += jml_alfa

        daftar_monitoring.append({
            'id': guru.id,
            'nama': guru.nama,
            'nip': guru.nip,
            'jabatan': guru.jabatan,
            'hadir': jml_hadir,
            'terlambat': jml_terlambat,
            'izin': jml_izin,
            'alfa': jml_alfa,
            'total_hari': total_hari,
            'persen_kehadiran': persen
        })

    # === TOTAL RINGKASAN SELURUH GURU ===
    total_keseluruhan = total_semua_hadir + total_semua_terlambat + total_semua_izin + total_semua_alfa
    persen_total = round(((total_semua_hadir + total_semua_terlambat) / total_keseluruhan) * 100, 1) if total_keseluruhan > 0 else 0
    ringkasan_seluruh = {
        'jumlah_guru': len(semua_guru),
        'hadir': total_semua_hadir,
        'terlambat': total_semua_terlambat,
        'izin': total_semua_izin,
        'alfa': total_semua_alfa,
        'total': total_keseluruhan,
        'persen': persen_total
    }

    return render_template(
        'sections/absensi/monitoring_absensi.html',
        user=user,
        user_name=user_name,
        jabatan=jabatan,
        label_tp=label_tp,
        hari_ini=hari_ini.strftime('%d %B %Y'),
        filter_bulan=filter_bulan,
        filter_tahun=filter_tahun,
        nama_bulan_terpilih=nama_bulan_terpilih,
        daftar_bulan=daftar_bulan,
        daftar_tahun=daftar_tahun,
        daftar_guru=daftar_monitoring,
        ringkasan=ringkasan_seluruh,
        halaman_aktif=halaman_aktif,
        active_page='monitoring_absensi'
    )

# ==================================================
# ✅ EXPORT MONITORING KE EXCEL
# ==================================================
@monitoring_bp.route('/export-monitoring', methods=['POST'])
def export_monitoring():
    """Export seluruh monitoring absensi ke Excel"""

    # ✅ CEK HAK AKSES — SAMA DENGAN HALAMAN UTAMA
    boleh, alasan = cek_akses_monitoring()
    if not boleh:
        if alasan == 'tolak_absensi':
            return redirect(url_for('login.halaman_login'))
        elif alasan == 'tolak_login':
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('dashboard'))

    # Ambil parameter filter
    filter_bulan = request.form.get('bulan', type=int) or date.today().month
    filter_tahun = request.form.get('tahun', type=int) or date.today().year

    # Rentang tanggal
    tgl_awal = date(filter_tahun, filter_bulan, 1)
    if filter_bulan == 12:
        tgl_akhir = date(filter_tahun, 12, 31)
    else:
        tgl_akhir = date(filter_tahun, filter_bulan + 1, 1) - timedelta(days=1)

    tgl_mulai_tp, tgl_selesai_tp, _ = ambil_tahun_pelajaran()

    # Ambil data & hitung
    semua_guru = Guru.query.order_by(Guru.nama).all()
    nama_bulan_list = ['Januari','Pebruari','Maret','April','Mei','Juni',
                       'Juli','Agustus','September','Oktober','Nopember','Desember']
    nama_bulan_terpilih = nama_bulan_list[filter_bulan - 1]

    rows = []
    for guru in semua_guru:
        absensi_guru = AbsensiGuru.query.filter(
            AbsensiGuru.guru_id == guru.id,
            AbsensiGuru.tanggal >= tgl_awal,
            AbsensiGuru.tanggal <= tgl_akhir,
            AbsensiGuru.tanggal >= tgl_mulai_tp,
            AbsensiGuru.tanggal <= tgl_selesai_tp
        )
        jml_hadir = absensi_guru.filter(AbsensiGuru.status == 'hadir').count()
        jml_terlambat = absensi_guru.filter(AbsensiGuru.status == 'terlambat').count()
        jml_izin = absensi_guru.filter(AbsensiGuru.status.in_(['izin','sakit'])).count()
        jml_alfa = absensi_guru.filter(AbsensiGuru.status == 'alfa').count()
        total = jml_hadir + jml_terlambat + jml_izin + jml_alfa
        persen = round(((jml_hadir + jml_terlambat) / total) * 100, 1) if total > 0 else 0

        rows.append({
            'Nama Guru': guru.nama,
            'NIP': guru.nip or '-',
            'Jabatan': guru.jabatan or '-',
            'Hadir': jml_hadir,
            'Terlambat': jml_terlambat,
            'Izin/Sakit': jml_izin,
            'Alfa': jml_alfa,
            'Total Hari': total,
            'Kehadiran %': f"{persen} %"
        })

    if not rows:
        flash('Tidak ada data untuk diekspor.', 'absensi_warning')
        return redirect(url_for('monitoring_absensi.monitoring_absensi'))

    # Buat Excel
    df = pd.DataFrame(rows)
    output = BytesIO()
    nama_file = f"Monitoring_Absensi_{nama_bulan_terpilih}_{filter_tahun}.xlsx"
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Monitoring Absensi')
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={nama_file}"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

# ==================================================
# ✅ BUAT QR ABSENSI — BERLAKU UNTUK SEMUA GURU
# Format: semua_guru:tanggal:{TGL}:tipe:{jenis}:pembuat:admin
# ==================================================
# ==============================================
# ✅ BUAT QR ABSENSI — 1 QR UNTUK MASUK & PULANG
# Format: semua_guru:tanggal:{YYYY-MM-DD}:pembuat:admin
# Tipe ditentukan OTOMATIS dari jam saat scan:
#   < 15:00 → MASUK  /  ≥ 15:00 → PULANG
# ==============================================
@monitoring_bp.route('/buat-qr-semua-guru', methods=['POST'])
def buat_qr_semua_guru():
    """Buat 1 QR berlaku untuk SEMUA guru — otomatis Masuk/Pulang berdasarkan jam scan"""
    # ✅ CEK HAK AKSES
    boleh, alasan = cek_akses_monitoring()
    if not boleh:
        return jsonify({"status": "error", "pesan": "⚠️ Tidak memiliki izin"}), 403

    hari_ini = date.today()
    hari_ini_str = hari_ini.strftime("%Y-%m-%d")

    # ✅ FORMAT QR — TANPA TIPE, SISTEM YANG MENENTUKAN
    data_qr = f"semua_guru:tanggal:{hari_ini_str}:pembuat:admin"

    qr_img = qrcode.make(data_qr)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        "status": "sukses",
        "qr_code": qr_base64,
        "hari_ini": hari_ini_str,
        "keterangan": "QR berlaku untuk Masuk & Pulang"
    })