
import os
import io
import re
import json
import uuid
from models import User

from datetime import datetime, date, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
    send_file,
    abort
)

from openpyxl import Workbook, load_workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Border,
    Side,
    Alignment
)
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

from models import db, Siswa, TahunPelajaran, RiwayatKelas
from routes.siswa.data_siswa import bisa_kelola


# ==========================================================
# BLUEPRINT
# ==========================================================

import_siswa_bp = Blueprint(
    "import_siswa",
    __name__,
    url_prefix="/siswa/import"
)


# ==========================================================
# KONFIGURASI
# ==========================================================

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ROWS = 1000
PREVIEW_EXPIRE_MINUTES = 30

KOLOM_EXCEL = [
    "nis",
    "nisn",
    "nama",
    "nik",
    "jenis_kelamin",
    "agama",
    "tempat_lahir",
    "tanggal_lahir",
    "alamat",
    "no_hp",
    "email",
    "status",
    "nama_ayah",
    "nama_ibu",
    "no_hp_ortu",
    "pekerjaan_ayah",
    "pekerjaan_ibu",
    "jenis_pendaftaran",
    "tanggal_diterima",
    "tingkat",
    "sekolah_sd",
    "tahun_lulus_sd",
    "alamat_sekolah_sd",
    "sekolah_asal_pindah",
    "tahun_pindah",
    "alamat_sekolah_pindah"
]

KOLOM_WAJIB = [
    "nis",
    "nama",
    "jenis_kelamin",
    "jenis_pendaftaran",
    "tanggal_diterima"
]


# ==========================================================
# HELPER AKSES
# ==========================================================

def cek_akses_import():
    if not session.get("logged_in"):
        abort(403)

    if not bisa_kelola():
        abort(403)


# ==========================================================
# HELPER TAHUN PELAJARAN
# ==========================================================

def get_tahun_pelajaran_aktif():
    kode_tahun = session.get("tahun_pelajaran")

    if not kode_tahun:
        tahun_aktif = TahunPelajaran.query.filter_by(
            aktif=True
        ).first()

        if not tahun_aktif:
            return None

        kode_tahun = tahun_aktif.kode

    tahun = TahunPelajaran.query.filter_by(
        kode=kode_tahun
    ).first()

    if not tahun or not tahun.aktif:
        return None

    return tahun


# ==========================================================
# HELPER FILE PREVIEW
# ==========================================================

def folder_preview():
    folder = os.path.join(
        current_app.instance_path,
        "import_siswa"
    )

    os.makedirs(folder, exist_ok=True)

    return folder


def path_preview(token):
    if not token or not re.fullmatch(r"[a-f0-9]{32}", token):
        return None

    return os.path.join(
        folder_preview(),
        f"{token}.json"
    )


def hapus_preview(token):
    path = path_preview(token)

    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            current_app.logger.exception(
                "Gagal menghapus file preview import siswa"
            )


def bersihkan_preview_lama():
    folder = folder_preview()
    batas_waktu = datetime.now().timestamp() - (
        PREVIEW_EXPIRE_MINUTES * 60
    )

    try:
        for nama_file in os.listdir(folder):
            if not nama_file.endswith(".json"):
                continue

            path = os.path.join(folder, nama_file)

            try:
                if os.path.getmtime(path) < batas_waktu:
                    os.remove(path)
            except OSError:
                continue

    except OSError:
        current_app.logger.exception(
            "Gagal membersihkan file preview lama"
        )


def simpan_preview(data):
    token = uuid.uuid4().hex

    path = path_preview(token)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            default=str
        )

    return token


def baca_preview(token):
    path = path_preview(token)

    if not path or not os.path.isfile(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        dibuat = datetime.fromisoformat(
            data.get("dibuat", "")
        )

        if datetime.now() - dibuat > timedelta(
            minutes=PREVIEW_EXPIRE_MINUTES
        ):
            hapus_preview(token)
            return None

        return data

    except (ValueError, OSError, json.JSONDecodeError):
        return None


# ==========================================================
# HELPER NORMALISASI DATA
# ==========================================================

def teks(nilai):
    if nilai is None:
        return ""

    return str(nilai).strip()


def normalisasi_header(nilai):
    return teks(nilai).lower().replace(" ", "_")


def normalisasi_gender(nilai):
    nilai = teks(nilai).lower()

    mapping = {
        "l": "Laki-laki",
        "lk": "Laki-laki",
        "laki laki": "Laki-laki",
        "laki-laki": "Laki-laki",
        "laki_laki": "Laki-laki",
        "p": "Perempuan",
        "pr": "Perempuan",
        "perempuan": "Perempuan"
    }

    return mapping.get(nilai)


def normalisasi_pendaftaran(nilai):
    nilai = teks(nilai).lower()

    mapping = {
        "baru": "baru",
        "siswa baru": "baru",
        "pindahan": "pindahan",
        "pindah": "pindahan",
        "siswa pindahan": "pindahan"
    }

    return mapping.get(nilai)


def normalisasi_status(nilai):
    nilai = teks(nilai).lower()

    mapping = {
        "aktif": "Aktif",
        "non aktif": "Non Aktif",
        "nonaktif": "Non Aktif",
        "lulus": "Lulus",
        "pindah": "Pindah"
    }

    if not nilai:
        return "Aktif"

    return mapping.get(nilai)


def parse_tanggal(nilai):
    if isinstance(nilai, datetime):
        return nilai.date()

    if isinstance(nilai, date):
        return nilai

    nilai = teks(nilai)

    if not nilai:
        return None

    format_tanggal = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y"
    ]

    for fmt in format_tanggal:
        try:
            return datetime.strptime(
                nilai,
                fmt
            ).date()
        except ValueError:
            continue

    return None


def parse_tahun(nilai):
    if nilai is None or teks(nilai) == "":
        return None

    try:
        angka = int(float(str(nilai).strip()))

        if angka < 1900 or angka > 2200:
            return None

        return angka

    except (ValueError, TypeError):
        return None


def cek_email(email):
    if not email:
        return False

    pola = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pola, email))


# ==========================================================
# HELPER DUPLIKASI DATABASE
# ==========================================================

def cari_nis(nis):
    return Siswa.query.filter(
        Siswa.nis == nis
    ).first()


def cari_nisn(nisn):
    if not nisn:
        return None

    return Siswa.query.filter(
        Siswa.nisn == nisn
    ).first()


def cari_email(email):
    if not email:
        return None

    return Siswa.query.filter(
        Siswa.email == email
    ).first()


# ==========================================================
# HALAMAN IMPORT EXCEL
# ==========================================================

@import_siswa_bp.route("/", methods=["GET"])
def halaman_import_excel():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    if not bisa_kelola():
        flash('Anda tidak memiliki akses untuk mengimpor data siswa.', 'danger')
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    # Ambil user yang sedang login
    user = User.query.get(session.get('user_id'))

    # Pastikan user tersedia
    if not user:
        flash('Data pengguna tidak ditemukan. Silakan login kembali.', 'danger')
        return redirect(url_for('auth.login'))

    # Ambil tahun pelajaran aktif
    kode_tahun = session.get('tahun_pelajaran')

    if not kode_tahun:
        tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun = tahun_aktif.kode if tahun_aktif else None

    tahun_dipilih = TahunPelajaran.query.filter_by(
        kode=kode_tahun,
        aktif=True
    ).first() if kode_tahun else None

    if not tahun_dipilih:
        flash('Tahun pelajaran aktif tidak ditemukan.', 'danger')
        return redirect(url_for('data_siswa.halaman_daftar_siswa'))

    return render_template(
        'index.html',
        active_page='data_siswa',
        sub_page='import_excel',

        # Variabel penting untuk layout dan sidebar
        user=user,
        role=session.get('role'),

        # Konteks tahun pelajaran
        tahun_dipilih=tahun_dipilih,
        kode_tahun=kode_tahun,

        # Konteks tambahan
        halaman_aktif='utama'
    )

# ==========================================================
# DOWNLOAD TEMPLATE EXCEL
# ==========================================================

@import_siswa_bp.route("/template", methods=["GET"])
def download_template():
    cek_akses_import()

    wb = Workbook()

    ws = wb.active
    ws.title = "Data Siswa"

    instruksi = wb.create_sheet("Petunjuk")

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------

    ws.append(KOLOM_EXCEL)

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="064E3B"
    )

    header_font = Font(
        name="Arial",
        size=10,
        bold=True,
        color="FFFFFF"
    )

    thin_border = Border(
        bottom=Side(
            style="thin",
            color="D1D5DB"
        )
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )
        cell.border = thin_border

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = (
        f"A1:{get_column_letter(len(KOLOM_EXCEL))}1"
    )

    ws.row_dimensions[1].height = 30

    # Lebar kolom
    for index, kolom in enumerate(KOLOM_EXCEL, start=1):
        ws.column_dimensions[
            get_column_letter(index)
        ].width = max(17, min(len(kolom) + 5, 30))

    # Kolom identitas dan nomor telepon sebagai teks
    kolom_teks = [
        "nis",
        "nisn",
        "nik",
        "no_hp",
        "no_hp_ortu"
    ]

    for kolom in kolom_teks:
        index = KOLOM_EXCEL.index(kolom) + 1

        for row in range(2, MAX_ROWS + 2):
            ws.cell(
                row=row,
                column=index
            ).number_format = "@"

    # ------------------------------------------------------
    # DROPDOWN
    # ------------------------------------------------------

    def tambah_dropdown(kolom, pilihan):
        index = KOLOM_EXCEL.index(kolom) + 1
        huruf = get_column_letter(index)

        dv = DataValidation(
            type="list",
            formula1=f'"{pilihan}"',
            allow_blank=True
        )

        dv.error = "Silakan pilih nilai dari daftar."
        dv.errorTitle = "Pilihan tidak valid"

        ws.add_data_validation(dv)

        dv.add(
            f"{huruf}2:{huruf}{MAX_ROWS + 1}"
        )

    tambah_dropdown(
        "jenis_kelamin",
        "Laki-laki,Perempuan"
    )

    tambah_dropdown(
        "jenis_pendaftaran",
        "baru,pindahan"
    )

    tambah_dropdown(
        "tingkat",
        "7,8,9"
    )

    tambah_dropdown(
        "status",
        "Aktif,Non Aktif,Lulus,Pindah"
    )

    tambah_dropdown(
        "agama",
        "Islam,Kristen,Katolik,Hindu,Buddha,Konghucu"
    )

    # ------------------------------------------------------
    # PETUNJUK
    # ------------------------------------------------------

    petunjuk = [
        ["PETUNJUK IMPORT DATA SISWA"],
        [""],
        ["1. Isi data pada sheet Data Siswa."],
        ["2. Jangan mengubah nama kolom pada baris pertama."],
        ["3. Kolom wajib: nis, nama, jenis_kelamin, jenis_pendaftaran, tanggal_diterima."],
        ["4. jenis_kelamin: Laki-laki atau Perempuan."],
        ["5. jenis_pendaftaran: baru atau pindahan."],
        ["6. Siswa baru otomatis masuk tingkat 7."],
        ["7. Siswa pindahan wajib mengisi tingkat 7, 8, atau 9."],
        ["8. tanggal_diterima menggunakan format YYYY-MM-DD atau DD/MM/YYYY."],
        ["9. tanggal_lahir boleh dikosongkan jika belum tersedia."],
        ["10. NIS, NISN, NIK, dan nomor telepon sebaiknya diatur sebagai teks."],
        ["11. Email boleh dikosongkan. Sistem akan membuat email default."],
        ["12. Jangan mengisi kelas_id atau diterima_di_kelas. Penempatan kelas dilakukan kemudian."],
        ["13. Data hanya disimpan setelah Anda memeriksa preview dan menekan tombol konfirmasi."],
        ["14. Maksimal 1.000 baris dalam satu kali import."],
        [""],
        ["KOLOM WAJIB"],
        ["nis"],
        ["nama"],
        ["jenis_kelamin"],
        ["jenis_pendaftaran"],
        ["tanggal_diterima"]
    ]

    for baris in petunjuk:
        instruksi.append(baris)

    instruksi.column_dimensions["A"].width = 115

    instruksi["A1"].font = Font(
        bold=True,
        size=16,
        color="064E3B"
    )

    for row in range(3, instruksi.max_row + 1):
        instruksi.cell(row=row, column=1).alignment = Alignment(
            vertical="center",
            wrap_text=True
        )

    # ------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------

    output = io.BytesIO()

    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Template_Import_Data_Siswa.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# ==========================================================
# VALIDASI SATU BARIS EXCEL
# ==========================================================

def validasi_baris(row_data, nomor_baris):
    data = {}

    for kolom in KOLOM_EXCEL:
        data[kolom] = teks(
            row_data.get(kolom)
        )

    errors = []

    # ------------------------------------------------------
    # DATA WAJIB
    # ------------------------------------------------------

    if not data["nis"]:
        errors.append("NIS wajib diisi.")

    if not data["nama"]:
        errors.append("Nama siswa wajib diisi.")

    gender = normalisasi_gender(
        data["jenis_kelamin"]
    )

    if not gender:
        errors.append(
            "Jenis kelamin harus Laki-laki atau Perempuan."
        )

    pendaftaran = normalisasi_pendaftaran(
        data["jenis_pendaftaran"]
    )

    if not pendaftaran:
        errors.append(
            "Jenis pendaftaran harus baru atau pindahan."
        )

    tanggal_diterima = parse_tanggal(
        row_data.get("tanggal_diterima")
    )

    if not tanggal_diterima:
        errors.append(
            "Tanggal diterima wajib diisi dengan tanggal yang valid."
        )

    # ------------------------------------------------------
    # TINGKAT
    # ------------------------------------------------------

    if pendaftaran == "baru":
        tingkat = "7"

    elif pendaftaran == "pindahan":
        tingkat_input = data["tingkat"]

        if tingkat_input not in ["7", "8", "9"]:
            errors.append(
                "Siswa pindahan wajib mengisi tingkat 7, 8, atau 9."
            )

            tingkat = ""

        else:
            tingkat = tingkat_input

    else:
        tingkat = ""

    # ------------------------------------------------------
    # TANGGAL LAHIR
    # ------------------------------------------------------

    tanggal_lahir = None

    if data["tanggal_lahir"]:
        tanggal_lahir = parse_tanggal(
            row_data.get("tanggal_lahir")
        )

        if not tanggal_lahir:
            errors.append(
                "Format tanggal lahir tidak valid."
            )

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    status = normalisasi_status(
        data["status"]
    )

    if not status:
        errors.append(
            "Status harus Aktif, Non Aktif, Lulus, atau Pindah."
        )

    # ------------------------------------------------------
    # EMAIL
    # ------------------------------------------------------

    email = data["email"].lower()

    if not email and data["nis"]:
        email = f"siswa-{data['nis']}@sekolah.sch.id"

    if email and not cek_email(email):
        errors.append("Format email tidak valid.")

    # ------------------------------------------------------
    # TAHUN
    # ------------------------------------------------------

    tahun_lulus_sd = None

    if data["tahun_lulus_sd"]:
        tahun_lulus_sd = parse_tahun(
            data["tahun_lulus_sd"]
        )

        if tahun_lulus_sd is None:
            errors.append(
                "Tahun lulus SD harus berupa tahun yang valid."
            )

    tahun_pindah = None

    if data["tahun_pindah"]:
        tahun_pindah = parse_tahun(
            data["tahun_pindah"]
        )

        if tahun_pindah is None:
            errors.append(
                "Tahun pindah harus berupa tahun yang valid."
            )

    # ------------------------------------------------------
    # DUPLIKASI DATABASE
    # ------------------------------------------------------

    if data["nis"] and cari_nis(data["nis"]):
        errors.append(
            f"NIS {data['nis']} sudah terdaftar."
        )

    if data["nisn"] and cari_nisn(data["nisn"]):
        errors.append(
            f"NISN {data['nisn']} sudah terdaftar."
        )

    if email and cari_email(email):
        errors.append(
            f"Email {email} sudah digunakan."
        )

    # ------------------------------------------------------
    # DATA FINAL
    # ------------------------------------------------------

    hasil = {
        "nis": data["nis"],
        "nisn": data["nisn"] or None,
        "nama": data["nama"],
        "nik": data["nik"] or None,
        "jenis_kelamin": gender,
        "agama": data["agama"] or None,
        "tempat_lahir": data["tempat_lahir"] or None,
        "tanggal_lahir": (
            tanggal_lahir.isoformat()
            if tanggal_lahir else None
        ),
        "alamat": data["alamat"] or None,
        "no_hp": data["no_hp"] or None,
        "email": email or None,
        "status": status or "Aktif",
        "nama_ayah": data["nama_ayah"] or None,
        "nama_ibu": data["nama_ibu"] or None,
        "no_hp_ortu": data["no_hp_ortu"] or None,
        "pekerjaan_ayah": data["pekerjaan_ayah"] or None,
        "pekerjaan_ibu": data["pekerjaan_ibu"] or None,
        "jenis_pendaftaran": pendaftaran,
        "tanggal_diterima": (
            tanggal_diterima.isoformat()
            if tanggal_diterima else None
        ),
        "tahun_diterima": (
            tanggal_diterima.year
            if tanggal_diterima else None
        ),
        "tingkat": tingkat,
        "sekolah_sd": data["sekolah_sd"] or None,
        "tahun_lulus_sd": tahun_lulus_sd,
        "alamat_sekolah_sd": data["alamat_sekolah_sd"] or None,
        "sekolah_asal_pindah": data["sekolah_asal_pindah"] or None,
        "tahun_pindah": tahun_pindah,
        "alamat_sekolah_pindah": data["alamat_sekolah_pindah"] or None
    }

    return hasil, errors


# ==========================================================
# PREVIEW IMPORT
# ==========================================================

@import_siswa_bp.route("/preview", methods=["POST"])
def preview_import():
    cek_akses_import()

    tahun = get_tahun_pelajaran_aktif()

    if not tahun:
        flash(
            "Tahun pelajaran aktif tidak ditemukan.",
            "error"
        )

        return redirect(
            url_for("data_siswa.halaman_daftar_siswa")
        )

    file = request.files.get("file_excel")

    if not file or not file.filename:
        flash("Silakan pilih file Excel terlebih dahulu.", "error")

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    if not file.filename.lower().endswith(".xlsx"):
        flash("File harus berformat .xlsx.", "error")

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    file.seek(0, os.SEEK_END)
    ukuran = file.tell()
    file.seek(0)

    if ukuran > MAX_FILE_SIZE:
        flash("Ukuran file maksimal 10 MB.", "error")

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    try:
        wb = load_workbook(
            file,
            read_only=True,
            data_only=True
        )

        ws = wb["Data Siswa"] if "Data Siswa" in wb.sheetnames else wb.active

    except Exception:
        flash("File Excel tidak dapat dibaca atau rusak.", "error")

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    rows = ws.iter_rows(values_only=True)

    header = next(rows, None)

    if not header:
        flash("Sheet Excel tidak memiliki header.", "error")

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    header_map = {}

    for index, nama_kolom in enumerate(header):
        nama = normalisasi_header(nama_kolom)

        if nama:
            header_map[nama] = index

    kolom_hilang = [
        kolom for kolom in KOLOM_WAJIB
        if kolom not in header_map
    ]

    if kolom_hilang:
        flash(
            "Kolom wajib tidak ditemukan: "
            + ", ".join(kolom_hilang),
            "error"
        )

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    valid_rows = []
    error_rows = []

    duplikat_nis = set()
    duplikat_nisn = set()
    duplikat_email = set()

    total_baris = 0

    try:
        for nomor_baris, values in enumerate(rows, start=2):

            if not values or not any(
                value is not None and teks(value)
                for value in values
            ):
                continue

            total_baris += 1

            if total_baris > MAX_ROWS:
                error_rows.append({
                    "baris": nomor_baris,
                    "nis": "-",
                    "nama": "-",
                    "errors": [
                        f"Maksimal {MAX_ROWS} baris per import."
                    ]
                })
                break

            row_data = {}

            for kolom in KOLOM_EXCEL:
                index = header_map.get(kolom)

                row_data[kolom] = (
                    values[index]
                    if index is not None and index < len(values)
                    else None
                )

            hasil, errors = validasi_baris(
                row_data,
                nomor_baris
            )

            # Duplikasi dalam file Excel
            nis = hasil["nis"]
            nisn = hasil["nisn"]
            email = hasil["email"]

            if nis:
                if nis in duplikat_nis:
                    errors.append(
                        f"NIS {nis} muncul lebih dari sekali dalam Excel."
                    )
                else:
                    duplikat_nis.add(nis)

            if nisn:
                if nisn in duplikat_nisn:
                    errors.append(
                        f"NISN {nisn} muncul lebih dari sekali dalam Excel."
                    )
                else:
                    duplikat_nisn.add(nisn)

            if email:
                if email in duplikat_email:
                    errors.append(
                        f"Email {email} muncul lebih dari sekali dalam Excel."
                    )
                else:
                    duplikat_email.add(email)

            if errors:
                error_rows.append({
                    "baris": nomor_baris,
                    "nis": hasil["nis"] or "-",
                    "nama": hasil["nama"] or "-",
                    "errors": errors
                })
            else:
                hasil["baris_excel"] = nomor_baris
                valid_rows.append(hasil)

    finally:
        wb.close()

    # Hapus preview lama milik sesi ini
    token_lama = session.pop(
        "import_siswa_token",
        None
    )

    hapus_preview(token_lama)

    bersihkan_preview_lama()

    # Simpan hanya data valid di server
    payload = {
        "dibuat": datetime.now().isoformat(),
        "kode_tahun": tahun.kode,
        "valid_rows": valid_rows,
        "total_baris": total_baris,
        "total_valid": len(valid_rows),
        "total_error": len(error_rows)
    }

    token = simpan_preview(payload)

    session["import_siswa_token"] = token

    
    context = {
        "active_page": "data_siswa",
        "sub_page": "preview_import_excel",
        "halaman_aktif": session.get("halaman_aktif", "utama"),

        "user": {
            "jabatan": session.get("jabatan", ""),
            "tugas_tambahan": session.get("tugas_tambahan", "")
        },

        "kode_tahun": tahun.kode,
        "tahun_dipilih": tahun.kode,
        "token": token,

        "valid_rows": valid_rows,
        "error_rows": error_rows,

        "total_baris": total_baris,
        "total_valid": len(valid_rows),
        "total_error": len(error_rows),

        "bisa_kelola": bisa_kelola() if callable(bisa_kelola) else False
    }

    return render_template("index.html", **context)



# ==========================================================
# KONFIRMASI DAN SIMPAN IMPORT
# ==========================================================

@import_siswa_bp.route("/confirm", methods=["POST"])
def konfirmasi_import():
    cek_akses_import()

    token = request.form.get("token", "")

    token_sesi = session.get(
        "import_siswa_token"
    )

    if not token or token != token_sesi:
        flash(
            "Sesi preview tidak valid. Silakan upload ulang.",
            "error"
        )

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    payload = baca_preview(token)

    if not payload:
        session.pop("import_siswa_token", None)

        flash(
            "Preview sudah kedaluwarsa. Silakan upload ulang.",
            "error"
        )

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    tahun = get_tahun_pelajaran_aktif()

    if not tahun or tahun.kode != payload.get("kode_tahun"):
        flash(
            "Tahun pelajaran aktif berubah. Silakan ulangi proses import.",
            "error"
        )

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    data_valid = payload.get("valid_rows", [])

    if not data_valid:
        flash(
            "Tidak ada data valid yang dapat disimpan.",
            "warning"
        )

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    # ------------------------------------------------------
    # CEK ULANG DUPLIKASI SEBELUM TRANSAKSI
    # ------------------------------------------------------

    for data in data_valid:

        if cari_nis(data["nis"]):
            flash(
                f"NIS {data['nis']} sudah terdaftar. "
                "Tidak ada data yang disimpan.",
                "error"
            )

            return redirect(
                url_for("import_siswa.halaman_import_excel")
            )

        if data["nisn"] and cari_nisn(data["nisn"]):
            flash(
                f"NISN {data['nisn']} sudah terdaftar. "
                "Tidak ada data yang disimpan.",
                "error"
            )

            return redirect(
                url_for("import_siswa.halaman_import_excel")
            )

        if data["email"] and cari_email(data["email"]):
            flash(
                f"Email {data['email']} sudah digunakan. "
                "Tidak ada data yang disimpan.",
                "error"
            )

            return redirect(
                url_for("import_siswa.halaman_import_excel")
            )

    # ------------------------------------------------------
    # SIMPAN SEMUA DATA DALAM SATU TRANSAKSI
    # ------------------------------------------------------

    jumlah_berhasil = 0

    try:
        for data in data_valid:

            tanggal_diterima = date.fromisoformat(
                data["tanggal_diterima"]
            )

            tanggal_lahir = (
                date.fromisoformat(data["tanggal_lahir"])
                if data["tanggal_lahir"]
                else None
            )

            siswa_baru = Siswa(
                nis=data["nis"],
                nisn=data["nisn"],
                nama=data["nama"],
                nik=data["nik"],
                jenis_kelamin=data["jenis_kelamin"],
                agama=data["agama"],
                tempat_lahir=data["tempat_lahir"],
                tanggal_lahir=tanggal_lahir,
                tingkat=data["tingkat"],

                # Penempatan kelas dilakukan kemudian
                kelas_id=None,

                alamat=data["alamat"],
                no_hp=data["no_hp"],
                email=data["email"],
                status=data["status"],

                nama_ayah=data["nama_ayah"],
                nama_ibu=data["nama_ibu"],
                no_hp_ortu=data["no_hp_ortu"],
                pekerjaan_ayah=data["pekerjaan_ayah"],
                pekerjaan_ibu=data["pekerjaan_ibu"],

                jenis_pendaftaran=data["jenis_pendaftaran"],
                tanggal_diterima=tanggal_diterima,
                tahun_diterima=tanggal_diterima.year,

                # Tidak menentukan rombel saat import
                diterima_di_kelas=None,

                sekolah_sd=data["sekolah_sd"],
                tahun_lulus_sd=data["tahun_lulus_sd"],
                alamat_sekolah_sd=data["alamat_sekolah_sd"],

                sekolah_asal_pindah=data["sekolah_asal_pindah"],
                tahun_pindah=data["tahun_pindah"],
                alamat_sekolah_pindah=data["alamat_sekolah_pindah"]
            )

            db.session.add(siswa_baru)
            db.session.flush()

            riwayat = RiwayatKelas(
                siswa_id=siswa_baru.id,
                tahun_pelajaran=tahun.kode,
                tingkat=data["tingkat"],
                kelas_id=None
            )

            db.session.add(riwayat)

            jumlah_berhasil += 1

        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Gagal menyimpan import data siswa"
        )

        flash(
            "Import gagal. Tidak ada data yang disimpan. "
            "Periksa kembali data dan struktur database.",
            "error"
        )

        return redirect(
            url_for("import_siswa.halaman_import_excel")
        )

    # ------------------------------------------------------
    # SELESAI
    # ------------------------------------------------------

    hapus_preview(token)

    session.pop(
        "import_siswa_token",
        None
    )

    jumlah_error = payload.get("total_error", 0)

    pesan = (
        f"Berhasil mengimport {jumlah_berhasil} siswa."
    )

    if jumlah_error:
        pesan += (
            f" Sebanyak {jumlah_error} baris bermasalah "
            "tidak ikut disimpan."
        )

    flash(pesan, "success")

    return redirect(
        url_for(
            "data_siswa.halaman_daftar_siswa",
            tahun=tahun.kode
        )
    )


# ==========================================================
# BATALKAN PREVIEW
# ==========================================================

@import_siswa_bp.route("/batal", methods=["POST"])
def batal_import():
    cek_akses_import()

    token = session.pop(
        "import_siswa_token",
        None
    )

    hapus_preview(token)

    flash(
        "Proses import dibatalkan. Tidak ada data yang disimpan.",
        "info"
    )

    return redirect(
        url_for("import_siswa.halaman_import_excel")
    )
