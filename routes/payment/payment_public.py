from flask import Blueprint, render_template, request, jsonify
from models import Siswa

payment_public_bp = Blueprint(
    "payment_public",
    __name__,
    url_prefix="/payment-public"
)

@payment_public_bp.route("/", methods=["GET", "POST"])
def index():
    # Halaman utama — tidak perlu perubahan besar
    return render_template("payment/index.html")

@payment_public_bp.route("/cari_siswa", methods=["POST"])
def cari_siswa():
    nisn = request.form.get("nisn", "").strip()
    
    if not nisn:
        return jsonify({
            "status": "error",
            "pesan": "Silakan masukkan NISN siswa."
        })
    
    if not nisn.isdigit() or len(nisn) != 10:
        return jsonify({
            "status": "error",
            "pesan": "NISN harus terdiri dari 10 digit angka."
        })
    
    siswa = Siswa.query.filter_by(nisn=nisn).first()
    
    if not siswa:
        return jsonify({
            "status": "not_found",
            "pesan": "NISN tidak terdaftar."
        })
    
    if (siswa.status or "").strip().lower() != "aktif":
        return jsonify({
            "status": "inactive",
            "pesan": "Data siswa ditemukan, tetapi status siswa perlu dikonfirmasi ke pihak sekolah."
        })
    
    nama_kelas = (
        siswa.kelas_sekarang.nama_kelas
        if hasattr(siswa, 'kelas_sekarang') and siswa.kelas_sekarang
        else (siswa.tingkat or "Belum ditentukan")
    )
    
    return jsonify({
        "status": "found",
        "pesan": "Data siswa berhasil ditemukan.",
        "siswa": {
            "nama": siswa.nama or "Nama tidak tersedia",
            "nisn": siswa.nisn,
            "kelas": nama_kelas,
            "tahun_masuk": siswa.tahun_masuk or "-"
        }
    })