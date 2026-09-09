from flask import Blueprint

# Buat Blueprint utama untuk rute-rute
routes_bp = Blueprint('routes', __name__)

# --------------------------
# ✅ Tambahkan Filter number_format
# --------------------------
def number_format(value, decimals=0):
    """Format angka menjadi format ribuan Indonesia"""
    try:
        # Ubah ke format: 12.500.000
        return f"{value:,.{decimals}f}".replace(',', '.').replace('.', ',', 1)
    except (ValueError, TypeError):
        return value

# Daftarkan filter ke Jinja
# Nanti kita akan menghubungkannya ke aplikasi utama di app.py

# --------------------------
# ✅ Impor semua Blueprint agar terdaftar
# --------------------------
from .sections.kepsek.dashboard_kepsek import dashboard_kepsek_bp

# Daftarkan semua blueprint ke Blueprint utama
routes_bp.register_blueprint(dashboard_kepsek_bp)

