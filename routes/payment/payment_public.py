
from flask import Blueprint, render_template, request
from models import Siswa

payment_public_bp = Blueprint(
    "payment_public",
    __name__,
    url_prefix="/"
)


@payment_public_bp.route("/", methods=["GET", "POST"])
def index():
    siswa = None
    nisn = ""
    pesan = None
    status_pencarian = None

    if request.method == "POST":
        nisn = request.form.get("nisn", "").strip()

        if not nisn:
            pesan = "Silakan masukkan NISN siswa."
            status_pencarian = "error"

        elif not nisn.isdigit() or len(nisn) != 10:
            pesan = "NISN harus terdiri dari 10 digit angka."
            status_pencarian = "error"

        else:
            siswa = Siswa.query.filter_by(nisn=nisn).first()

            if siswa is None:
                pesan = "NISN tidak terdaftar."
                status_pencarian = "not_found"

            else:
                # Hanya siswa aktif yang dapat melanjutkan
                # ke proses pembayaran publik.
                if (siswa.status or "").strip().lower() != "aktif":
                    pesan = (
                        "Data siswa ditemukan, tetapi status "
                        "siswa perlu dikonfirmasi ke pihak sekolah."
                    )
                    status_pencarian = "inactive"
                else:
                    status_pencarian = "found"

    return render_template(
        "payment/index.html",
        siswa=siswa,
        nisn=nisn,
        pesan=pesan,
        status_pencarian=status_pencarian
    )
