from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from datetime import datetime, date, timedelta
from models import (
    db, User, TahunPelajaran, Siswa, Kelas, RiwayatKelas,
    JenisPembayaran, Ekstrakurikuler, Peminatan,
    BulanLiburEkskul, BulanLiburPeminatan, TagihanSiswa, RiwayatPembayaran
)

# === FUNGSI BANTU DIPERBAIKI ===
def daftar_bulan_semester(kode_tahun_dasar, pola_waktu, sampai_tanggal=None):
    if pola_waktu == 'semester_1':
        return [(1, "Pembayaran 1", 1)]
    elif pola_waktu == 'semester_2':
        return [(2, "Pembayaran 2", 2)]
    elif pola_waktu == 'awal_tahun':
        return [(1, "Pembayaran Awal Tahun", 1)]

    semua_semester = TahunPelajaran.query.filter(
        TahunPelajaran.kode.like(f"{kode_tahun_dasar}%")
    ).order_by(TahunPelajaran.tanggal_mulai.asc()).all()

    nama_bulan =   ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

    if semua_semester and len(semua_semester) >= 1:
        sekarang = semua_semester[0].tanggal_mulai
    else:
        try:
            tahun = int(str(kode_tahun_dasar)[:4])
            sekarang = date(tahun, 8, 1)
        except:
            return []

    akhir = sampai_tanggal if sampai_tanggal is not None else date.today()
    
    bulan_list = []
    while sekarang <= akhir:
        bulan_list.append((sekarang.month, nama_bulan[sekarang.month - 1], sekarang.year))
        if sekarang.month < 12:
            sekarang = sekarang.replace(month=sekarang.month + 1)
        else:
            sekarang = sekarang.replace(year=sekarang.year + 1, month=1)
    
    return bulan_list

def hitung_dan_dapat_total_tagihan(id_siswa, angkatan_masuk, tgl_mulai, batas_akhir):
    print(f"  -> Masuk Fungsi: id={id_siswa} angkatan={angkatan_masuk}")
    """
    Kembalikan: (daftar_tagihan, total_angka_murni)
    ✅ MEMBACA STATUS LUNAS/BELUM DARI DATABASE TagihanSiswa
    """

    daftar_tagihan_terperinci = []

    riwayat_pertama_siswa = RiwayatKelas.query.filter_by(siswa_id=id_siswa).order_by(RiwayatKelas.tahun_pelajaran.asc()).first()

    if riwayat_pertama_siswa:
        tahun_pelajaran_kode = riwayat_pertama_siswa.tahun_pelajaran
    else:
        tahun_pelajaran_kode = f"{angkatan_masuk}-1"

    semua_versi_tarif = JenisPembayaran.query.filter(
        JenisPembayaran.tahun_pelajaran.like(f"{angkatan_masuk}%"),
        # JenisPembayaran.aktif == True
    ).order_by(JenisPembayaran.pola_waktu, JenisPembayaran.nama).all()

    # === FUNGSI BANTU: Cek status lunas dari database ===
    def cek_status_tagihan(nama_tagihan, waktu_tagihan):
        jenis = JenisPembayaran.query.filter(
            JenisPembayaran.nama == nama_tagihan,
            JenisPembayaran.tahun_pelajaran.like(f"{angkatan_masuk}%")
        ).first()
        if not jenis:
            return 'Belum Lunas', 0, None

        # ✅ Cari tahun_pelajaran lengkap dari riwayat siswa
        riwayat_pertama = RiwayatKelas.query.filter_by(siswa_id=id_siswa).order_by(RiwayatKelas.tahun_pelajaran.asc()).first()
        tp_lengkap = riwayat_pertama.tahun_pelajaran.strip() if riwayat_pertama else f"{angkatan_masuk}-1"

        tagihan_db = TagihanSiswa.query.filter_by(
            siswa_id=id_siswa,
            jenis_pembayaran_id=jenis.id,
            bulan=waktu_tagihan,
            tahun_pelajaran=tp_lengkap  # ✅ Pakai format lengkap agar ketemu
        ).first()

        if tagihan_db:
            sudah = tagihan_db.sudah_dibayar or 0
            if tagihan_db.status in ['Sudah Lunas', 'Lunas']:
                return 'Lunas', sudah, tagihan_db
            if tagihan_db.status == 'Sebagian':
                return 'Sebagian', sudah, tagihan_db
        
        return 'Belum Lunas', 0, None

    # === LANJUT LOGIKA UTAMA ===
    if semua_versi_tarif:
        tarif_terpilih = {}
        for vt in semua_versi_tarif:
            if vt.kode not in tarif_terpilih:
                tarif_terpilih[vt.kode] = vt

        for tarif in tarif_terpilih.values():
            daftar_bulan_semua = daftar_bulan_semester(angkatan_masuk, tarif.pola_waktu, batas_akhir)

            # ======================================
            # BIAYA UMUM
            # ======================================
            if not (tarif.nama.startswith('Ekstrakurikuler - ') 
                    or tarif.nama.startswith('Peminatan - ') 
                    or tarif.nama.startswith('Kelas Peminatan - ')):
                if tarif.pola_waktu != 'bulanan':
                    for kode_bayar, nama_bayar, urut in daftar_bulan_semua:
                        status_sekarang, sudah_dibayar, tagihan_db = cek_status_tagihan(tarif.nama, nama_bayar)
                        daftar_tagihan_terperinci.append({
                            'id': tagihan_db.id if tagihan_db else None,
                            'nama': tarif.nama,
                            'waktu': nama_bayar,
                            'nominal': tarif.nominal,
                            'sudah_dibayar': sudah_dibayar,
                            'sisa_tagihan': max(0, tarif.nominal - sudah_dibayar),
                            'status': status_sekarang
                        })
                else:
                    for bulan_angka, nama_bulan, tahun_bulan in daftar_bulan_semua:
                        waktu_lengkap = f"{nama_bulan} {tahun_bulan}"
                        status_sekarang, sudah_dibayar, tagihan_db = cek_status_tagihan(tarif.nama, waktu_lengkap)
                        daftar_tagihan_terperinci.append({
                            'id': tagihan_db.id if tagihan_db else None,
                            'nama': tarif.nama,
                            'waktu': waktu_lengkap,
                            'nominal': tarif.nominal,
                            'sudah_dibayar': sudah_dibayar,
                            'sisa_tagihan': tarif.nominal - sudah_dibayar,
                            'status': status_sekarang
                        })
                continue

            # ======================================
            # BIAYA EKSTRAKURIKULER
            # ======================================
            if tarif.nama.startswith('Ekstrakurikuler - '):
                nama_ekskul = tarif.nama.replace('Ekstrakurikuler - ', '')
                semua_data = Ekstrakurikuler.query.filter(
                    Ekstrakurikuler.nama == nama_ekskul
                ).order_by(Ekstrakurikuler.tgl_mulai.asc()).all()
                semua_data = [
                    e for e in semua_data
                    if not (e.tgl_selesai < tgl_mulai or e.tgl_mulai > (batas_akhir or date.today()))
                ]
                for periode in semua_data:
                    daftar_id_anggota = [a.id for a in periode.anggota]
                    if id_siswa not in daftar_id_anggota:
                        continue
                    for bulan_angka, nama_bulan, tahun_bulan in daftar_bulan_semua:
                        tgl_awal = date(tahun_bulan, bulan_angka, 1)
                        tgl_akhir = date(tahun_bulan, bulan_angka + 1, 1) - timedelta(days=1) if bulan_angka != 12 else date(tahun_bulan, 12, 31)
                        batas_sampai = batas_akhir or date.today()
                        if tgl_awal > batas_sampai:
                            continue
                        beririsan = not (tgl_akhir < periode.tgl_mulai or tgl_awal > periode.tgl_selesai)
                        if not beririsan:
                            continue
                        libur = BulanLiburEkskul.query.filter_by(ekskul_id=periode.id, bulan=bulan_angka, tahun=tahun_bulan).first()
                        if libur:
                            continue
                        waktu_lengkap = f"{nama_bulan} {tahun_bulan}"
                        status_sekarang, sudah_dibayar, tagihan_db = cek_status_tagihan(tarif.nama, waktu_lengkap)
                        daftar_tagihan_terperinci.append({
                            'id': tagihan_db.id if tagihan_db else None,
                            'nama': tarif.nama,
                            'waktu': waktu_lengkap,
                            'nominal': tarif.nominal,
                            'sudah_dibayar': sudah_dibayar,
                            'sisa_tagihan': tarif.nominal - sudah_dibayar,
                            'status': status_sekarang
                        })
                continue

            # ======================================
            # BIAYA PEMINATAN
            # ======================================
            elif tarif.nama.startswith('Peminatan - ') or tarif.nama.startswith('Kelas Peminatan - '):
                nama_peminatan = tarif.nama.replace('Kelas Peminatan - ', '').replace('Peminatan - ', '').strip()
                nama_peminatan = " ".join(nama_peminatan.split())
                semua_data = Peminatan.query.filter(
                    Peminatan.nama == nama_peminatan
                ).order_by(Peminatan.tgl_mulai.asc()).all()
                semua_data = [
                    p for p in semua_data
                    if not (p.tgl_selesai < tgl_mulai or p.tgl_mulai > (batas_akhir or date.today()))
                ]
                for periode in semua_data:
                    if not periode.anggota:
                        continue
                    daftar_id_anggota = [a.id for a in periode.anggota]
                    if id_siswa not in daftar_id_anggota:
                        continue
                    for bulan_angka, nama_bulan, tahun_bulan in daftar_bulan_semua:
                        tgl_awal_bulan = date(tahun_bulan, bulan_angka, 1)
                        tgl_akhir_bulan = date(tahun_bulan, bulan_angka + 1, 1) - timedelta(days=1) if bulan_angka != 12 else date(tahun_bulan, 12, 31)
                        batas_sampai = batas_akhir or date.today()
                        if tgl_awal_bulan > batas_sampai:
                            continue
                        beririsan = not (tgl_akhir_bulan < periode.tgl_mulai or tgl_awal_bulan > periode.tgl_selesai)
                        if not beririsan:
                            continue
                        libur = BulanLiburPeminatan.query.filter_by(
                            peminatan_id=periode.id, bulan=bulan_angka, tahun=tahun_bulan
                        ).first()
                        if libur:
                            continue
                        waktu_lengkap = f"{nama_bulan} {tahun_bulan}"
                        status_sekarang, sudah_dibayar, tagihan_db = cek_status_tagihan(tarif.nama, waktu_lengkap)
                        daftar_tagihan_terperinci.append({
                            'id': tagihan_db.id if tagihan_db else None,
                            'nama': tarif.nama,
                            'waktu': waktu_lengkap,
                            'nominal': tarif.nominal,
                            'sudah_dibayar': sudah_dibayar,
                            'sisa_tagihan': tarif.nominal - sudah_dibayar,
                            'status': status_sekarang
                        })

    total_murni = sum(t['nominal'] for t in daftar_tagihan_terperinci)
    print(f"[CEK PUSAT] Siswa:{id_siswa} | Jumlah:{len(daftar_tagihan_terperinci)} | Total:{total_murni}")
    
    return daftar_tagihan_terperinci, total_murni

# === FUNGSI: PASTIKAN TAGIHAN SUDAH ADA DI TABEL TagihanSiswa ===
def pastikan_tagihan_tercatat(id_siswa, angkatan_masuk, tgl_mulai, batas_akhir):
    daftar_sementara, _ = hitung_dan_dapat_total_tagihan(
        id_siswa, angkatan_masuk, tgl_mulai, batas_akhir
    )

    daftar_tersimpan = []
    siswa = Siswa.query.get(id_siswa)
    riwayat_pertama = RiwayatKelas.query.filter_by(siswa_id=id_siswa)\
        .order_by(RiwayatKelas.tahun_pelajaran.asc()).first()
    
    if riwayat_pertama:
        tahun_pelajaran_kode = riwayat_pertama.tahun_pelajaran.strip()
    else:
        tahun_pelajaran_kode = f"{angkatan_masuk}-1"

    # === AMBIL BAGIAN DASAR TAHUN untuk pencarian ===
    dasar_tahun = tahun_pelajaran_kode.split('-')[0] if '-' in tahun_pelajaran_kode else tahun_pelajaran_kode

    for idx, item in enumerate(daftar_sementara):
        jenis = JenisPembayaran.query.filter(
            JenisPembayaran.nama == item['nama'],
            JenisPembayaran.tahun_pelajaran.like(f"{dasar_tahun}%")
        ).first()
        if not jenis:
            continue

        bulan_tagihan = None
        semester_tagihan = None
        if item.get('waktu'):
            daftar_bulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
            if any(b in item['waktu'] for b in daftar_bulan):
                bulan_tagihan = item['waktu']
            else:
                semester_tagihan = idx + 1

        tagihan = TagihanSiswa.query.filter_by(
            siswa_id=id_siswa,
            jenis_pembayaran_id=jenis.id,
            bulan=bulan_tagihan or "",
            tahun_pelajaran=tahun_pelajaran_kode
        ).first()

        if not tagihan:
            tagihan = TagihanSiswa(
                siswa_id=id_siswa,
                jenis_pembayaran_id=jenis.id,
                bulan=bulan_tagihan,
                semester=semester_tagihan,
                tahun_pelajaran=tahun_pelajaran_kode,
                nominal_tagihan=item['nominal'],
                sudah_dibayar=0,
                status='Belum Lunas'
            )
            db.session.add(tagihan)
            db.session.flush()

        daftar_tersimpan.append({
            "objek": tagihan,
            "nominal_asli": item['nominal'],
            "nama": item['nama'],
            "waktu": item.get('waktu',''),
            "sudah_dibayar": tagihan.sudah_dibayar or 0,
            "sisa_tagihan": max(0, item['nominal'] - (tagihan.sudah_dibayar or 0)),
            "status": tagihan.status
        })

    db.session.commit()
    return daftar_tersimpan

bendahara_bp = Blueprint('bendahara', __name__, url_prefix='/bendahara')

def get_base_tahun(kode_tp):
    if not kode_tp: return ""
    kode_tp = kode_tp.split('-')[0] if '-' in kode_tp else kode_tp
    return kode_tp.split(' ')[0].strip() if ' ' in kode_tp else kode_tp.strip()

def format_rupiah(angka):
    return "Rp " + "{:,.0f}".format(angka).replace(",", ".")

def get_daftar_tahun_unik():
    daftar_unik = {}
    for tp in TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all():
        kode_dasar = tp.kode.split('-')[0]
        if kode_dasar not in daftar_unik:
            daftar_unik[kode_dasar] = tp
    return list(daftar_unik.values())

def hitung_jumlah_bulan(kode_tahun_dasar, pola_waktu):
    if pola_waktu != 'bulanan':
        return 2
    semua_semester = TahunPelajaran.query.filter(
        TahunPelajaran.kode.like(f"{kode_tahun_dasar}%")
    ).order_by(TahunPelajaran.tanggal_mulai.asc()).all()
    if not semua_semester:
        return 0
    sekarang = semua_semester[0].tanggal_mulai
    akhir = date.today()
    jumlah = 0
    while sekarang <= akhir:
        jumlah += 1
        sekarang = sekarang.replace(month=sekarang.month+1) if sekarang.month < 12 else sekarang.replace(year=sekarang.year+1, month=1)
    return jumlah

# === DASHBOARD ===
@bendahara_bp.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    user = User.query.get(session.get('user_id'))
    session['halaman_aktif'] = 'bendahara'
    kode_tahun_aktif = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_aktif:
        tahun_aktif_db = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_aktif = tahun_aktif_db.kode if tahun_aktif_db else None

    nama_tahun, nama_semester = "Tidak Diketahui", "-"
    dasar_tahun = get_base_tahun(kode_tahun_aktif) if kode_tahun_aktif else ""

    if kode_tahun_aktif:
        tahun_obj = TahunPelajaran.query.filter_by(kode=kode_tahun_aktif).first()
        if tahun_obj:
            potong = tahun_obj.nama.replace('Tahun Pelajaran ', '').split(' - ')
            if len(potong) == 2:
                nama_semester = 'Ganjil' if potong[1].replace('Semester ','') == '1' else 'Genap'
                nama_tahun = potong[0]
            else:
                nama_tahun = tahun_obj.nama

    # ==============================================
    # ✅ HITUNG DATA ASLI DARI DATABASE
    # ==============================================
    total_siswa = 0
    siswa_lunas = 0
    siswa_belum_lunas = 0
    total_tagihan = 0
    total_dibayar = 0
    pemasukan_bulan_ini = 0
    pemasukan_sampai_sekarang = 0
    pengeluaran_bulan_ini = 0
    saldo_tersedia = 0

    if kode_tahun_aktif:
        riwayat_tercatat = RiwayatKelas.query.filter_by(tahun_pelajaran=kode_tahun_aktif).all()
        id_unik_siswa = list({r.siswa_id for r in riwayat_tercatat})
        total_siswa = len(id_unik_siswa)
        bulan_ini = date.today().month
        tahun_ini = date.today().year

        # ✅ AMBIL SEMUA TAGIHAN DARI SEMUA TAHUN AJARAN (bukan dibatasi satu tahun)
        tagihan_semua = TagihanSiswa.query.all()

        # ==============================================
        # DEBUG
        # ==============================================
        print("=" * 80)
        print("🔍 DEBUG TAGIHAN DASHBOARD")
        print(f"Total tagihan di DB: {len(tagihan_semua)}")
        for t in tagihan_semua[:5]:  # tampilkan 5 contoh pertama
            print(f"  TP={t.tahun_pelajaran} | Siswa={t.siswa_id} | Nominal={t.nominal_tagihan} | Status={t.status}")
        print("=" * 80)

        siswa_tagihan = {}
        total_tagihan = 0
        total_dibayar = 0
        pemasukan_bulan_ini = 0
        pemasukan_sampai_sekarang = 0

        for t in tagihan_semua:
            tagihan_nominal = t.nominal_tagihan or 0
            sudah_dibayar_dari_kolom = t.sudah_dibayar or 0
            riwayat_list = list(t.riwayat)
            bayar_dari_riwayat = sum((r.jumlah_bayar or 0) for r in riwayat_list)

            sudah_bayar = max(sudah_dibayar_dari_kolom, bayar_dari_riwayat)

            if (t.sudah_dibayar or 0) != bayar_dari_riwayat:
                t.sudah_dibayar = bayar_dari_riwayat
                if t.sudah_dibayar >= t.nominal_tagihan:
                    t.status = 'Lunas'
                elif t.sudah_dibayar > 0:
                    t.status = 'Sebagian'
                else:
                    t.status = 'Belum Lunas'

            total_tagihan += tagihan_nominal
            total_dibayar += sudah_bayar

            for bayar in riwayat_list:
                if bayar.tanggal_bayar:
                    if bayar.tanggal_bayar.month == bulan_ini and bayar.tanggal_bayar.year == tahun_ini:
                        pemasukan_bulan_ini += bayar.jumlah_bayar or 0
                    pemasukan_sampai_sekarang += bayar.jumlah_bayar or 0

            if bayar_dari_riwayat == 0 and sudah_dibayar_dari_kolom > 0:
                pemasukan_sampai_sekarang += sudah_dibayar_dari_kolom

            if t.siswa_id not in siswa_tagihan:
                siswa_tagihan[t.siswa_id] = {
                    'total_tagihan': 0,
                    'total_dibayar': 0,
                    'lunas_semua': True
                }
            siswa_tagihan[t.siswa_id]['total_tagihan'] += tagihan_nominal
            siswa_tagihan[t.siswa_id]['total_dibayar'] += sudah_bayar
            if t.status not in ['Lunas', 'Sudah Lunas']:
                siswa_tagihan[t.siswa_id]['lunas_semua'] = False

        db.session.commit()

        saldo_tersedia = pemasukan_sampai_sekarang - pengeluaran_bulan_ini

        siswa_lunas = 0
        siswa_belum_lunas = 0
        for sid in id_unik_siswa:
            if sid in siswa_tagihan:
                data = siswa_tagihan[sid]
                if data['lunas_semua'] and data['total_dibayar'] >= data['total_tagihan']:
                    siswa_lunas += 1
                else:
                    siswa_belum_lunas += 1
            else:
                siswa_belum_lunas += 1

        persen_lunas_spp = round((siswa_lunas / total_siswa * 100), 1) if total_siswa > 0 else 0
        saldo_tersedia = pemasukan_sampai_sekarang - pengeluaran_bulan_ini

        print(f"✅ HASIL: Masuk Bulan Ini={pemasukan_bulan_ini} | Total Masuk={pemasukan_sampai_sekarang} | Saldo={saldo_tersedia}")
        print(f"✅ SISWA: Total={total_siswa} | Lunas={siswa_lunas} | Belum={siswa_belum_lunas} | %={persen_lunas_spp}")

        # ==============================================
        # ✅ AMBIL RIWAYAT PEMBAYARAN SEBAGAI TRANSAKSI
        # ==============================================
        daftar_transaksi = []

        for t in tagihan_semua:
            for bayar in t.riwayat:
                if bayar.tanggal_bayar:
                    siswa = Siswa.query.get(t.siswa_id)
                    nama_siswa = siswa.nama if siswa else f"Siswa ID {t.siswa_id}"

                    nama_jenis = "Pembayaran"
                    if t.jenis_pembayaran_id:
                        from models import JenisPembayaran
                        jp = JenisPembayaran.query.get(t.jenis_pembayaran_id)
                        if jp:
                            nama_jenis = jp.nama

                    tgl_lengkap = bayar.tanggal_bayar.strftime('%d/%m/%Y')
                    jam = bayar.tanggal_bayar.strftime('%H:%M') if bayar.tanggal_bayar else "--:--"

                    daftar_transaksi.append({
                        'jenis_trx': 'masuk',
                        'jenis_pembayaran': nama_jenis,
                        'nama_siswa': nama_siswa,
                        'tanggal_lengkap': f"{tgl_lengkap} {jam}",
                        'nominal': bayar.jumlah_bayar or 0
                    })

        daftar_transaksi.sort(key=lambda x: x['tanggal_lengkap'], reverse=True)
        daftar_transaksi = daftar_transaksi[:10]

    # === AMBIL DATA 6 BULAN TERAKHIR UNTUK GRAFIK ===
    from collections import defaultdict

    bulan_nama = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nov','Des']
    dlabel_bulan = []
    data_pemasukan = []
    data_pengeluaran = []

    for i in range(5, -1, -1):
        tgl_bulan = (date.today().replace(day=1) - timedelta(days=i*32))
        bln = tgl_bulan.month
        thn = tgl_bulan.year
        dlabel_bulan.append(f"{bulan_nama[bln-1]} {str(thn)[-2:]}")

        jumlah_masuk = 0
        jumlah_keluar = 0

        for t in tagihan_semua:
            for bayar in t.riwayat:
                if bayar.tanggal_bayar and bayar.tanggal_bayar.month == bln and bayar.tanggal_bayar.year == thn:
                    jumlah_masuk += bayar.jumlah_bayar or 0

        data_pemasukan.append(jumlah_masuk)
        data_pengeluaran.append(0)  # pengeluaran belum ada datanya, isi nol dulu

    return render_template('index.html',
        active_page='dashboard', halaman_aktif='bendahara', user=user,
        user_name=session.get('user_name','Pengguna'), user_role=session.get('jabatan','Bendahara'),
        today_date=datetime.now().strftime('%d %B %Y'), today_date_long=datetime.now().strftime('%A, %d %B %Y'),
        tahun_ajaran=nama_tahun, semester=nama_semester, total_siswa=total_siswa,
        pemasukan_bulan_ini=format_rupiah(pemasukan_bulan_ini),
        pengeluaran_bulan_ini=format_rupiah(pengeluaran_bulan_ini),
        saldo_tersedia=format_rupiah(saldo_tersedia),
        persen_lunas_spp=persen_lunas_spp,
        jumlah_belum_lunas=siswa_belum_lunas,
        jumlah_lunas=siswa_lunas,
        total_tagihan=format_rupiah(total_tagihan),
        total_dibayar=format_rupiah(total_dibayar),
        daftar_transaksi=daftar_transaksi,
        dlabel_bulan=dlabel_bulan,
        data_pemasukan=data_pemasukan,
        data_pengeluaran=data_pengeluaran)

# === PENGATURAN PEMBAYARAN ===
@bendahara_bp.route('/pengaturan-pembayaran', methods=['GET','POST'])
def pengaturan_pembayaran():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    user = User.query.get(session.get('user_id'))
    session['halaman_aktif'] = 'bendahara'

    kode_angkatan = request.args.get('angkatan')
    semua_tahun_unik = get_daftar_tahun_unik()

    semua_ekskul = Ekstrakurikuler.query.order_by(Ekstrakurikuler.nama).all()
    ekskul_unik = {}
    for e in semua_ekskul:
        dasar_tahun = e.tahun_pelajaran.split('-')[0] if '-' in e.tahun_pelajaran else e.tahun_pelajaran
        kunci = f"{e.nama}||{dasar_tahun}"
        if kunci not in ekskul_unik:
            ekskul_unik[kunci] = e
    daftar_ekskul = list(ekskul_unik.values())

    semua_peminatan = Peminatan.query.order_by(Peminatan.nama).all()
    peminatan_unik = {}
    for p in semua_peminatan:
        dasar_tahun = p.tahun_pelajaran.split('-')[0] if '-' in p.tahun_pelajaran else p.tahun_pelajaran
        kunci = f"{p.nama}||{dasar_tahun}"
        if kunci not in peminatan_unik:
            peminatan_unik[kunci] = p
    daftar_peminatan = list(peminatan_unik.values())
    
    if not kode_angkatan:
        return render_template('index.html',
            active_page='pengaturan_pembayaran', halaman_aktif='bendahara', user=user,
            user_name=session.get('user_name','Pengguna'), tahun_ajaran="Silakan Pilih Tahun Ajaran",
            kode_angkatan_terpilih=None, daftar_tarif=[], semua_tp=semua_tahun_unik,
            daftar_ekskul=daftar_ekskul, daftar_peminatan=daftar_peminatan, format_rupiah=format_rupiah)

    nama_tahun = "Tidak Diketahui"
    tahun_obj = TahunPelajaran.query.filter(TahunPelajaran.kode.like(f"{kode_angkatan}%")).first()
    if tahun_obj:
        nama_tahun = tahun_obj.nama.replace('Tahun Pelajaran ','').split(' - ')[0]

    if request.form.get('salin_dari_tahun'):
        kode_sumber = request.form.get('salin_dari_tahun').strip()
        if kode_sumber != kode_angkatan:
            daftar_sumber = JenisPembayaran.query.filter(
                JenisPembayaran.tahun_pelajaran.like(f"{kode_sumber}%")
            ).all()
            sudah_ada = 0
            for s in daftar_sumber:
                if not JenisPembayaran.query.filter_by(kode=s.kode).filter(
                    JenisPembayaran.tahun_pelajaran.like(f"{kode_angkatan}%")
                ).first():
                    baru = JenisPembayaran(
                        nama=s.nama, kode=s.kode, pola_waktu=s.pola_waktu,
                        nominal=s.nominal, keterangan=s.keterangan,
                        tahun_pelajaran=s.tahun_pelajaran.replace(kode_sumber, kode_angkatan),
                        aktif=s.aktif
                    )
                    db.session.add(baru)
                    sudah_ada += 1
            db.session.commit()
            flash(f"Berhasil menyalin {sudah_ada} jenis biaya ke {nama_tahun}!", "success")
        return redirect(url_for('bendahara.pengaturan_pembayaran', angkatan=kode_angkatan))

    if request.method == 'POST' and not request.form.get('salin_dari_tahun'):
        jenis_utama = request.form.get('jenis_utama', '').strip()
        nama_kelompok = request.form.get('nama_kelompok', '').strip()

        nama_final = f"{jenis_utama} - {nama_kelompok}" if nama_kelompok else jenis_utama

        cek = JenisPembayaran.query.filter_by(kode=request.form['kode']).filter(
            JenisPembayaran.tahun_pelajaran.like(f"{kode_angkatan}%")
        ).first()
        
        if cek:
            flash(f"Kode '{request.form['kode']}' SUDAH DIPAKAI di tahun ajaran {nama_tahun}! Gunakan kode lain.", "danger")
        else:
            db.session.add(JenisPembayaran(
                nama=nama_final,
                kode=request.form['kode'],
                pola_waktu=request.form['pola_waktu'],
                nominal=int(request.form['nominal']),
                keterangan=request.form.get('keterangan',''), 
                tahun_pelajaran=f"{kode_angkatan}-1"
            ))
            db.session.commit()
            flash(f"Jenis biaya '{nama_final}' ditambahkan!", "success")
        return redirect(url_for('bendahara.pengaturan_pembayaran', angkatan=kode_angkatan))

    daftar_tarif = JenisPembayaran.query.filter(
        JenisPembayaran.tahun_pelajaran.startswith(kode_angkatan)
    ).order_by(JenisPembayaran.pola_waktu, JenisPembayaran.nama).all()

    return render_template('index.html',
        active_page='pengaturan_pembayaran', halaman_aktif='bendahara', user=user,
        user_name=session.get('user_name','Pengguna'), tahun_ajaran=nama_tahun,
        kode_angkatan_terpilih=kode_angkatan, daftar_tarif=daftar_tarif,
        semua_tp=semua_tahun_unik, daftar_ekskul=daftar_ekskul,
        daftar_peminatan=daftar_peminatan, format_rupiah=format_rupiah)

# === UBAH TARIF ===
@bendahara_bp.route('/pengaturan-pembayaran/ubah/<int:id>', methods=['POST'])
def ubah_tarif(id):
    tarif_lama = JenisPembayaran.query.get_or_404(id)
    angkatan_dasar = get_base_tahun(tarif_lama.tahun_pelajaran)
    
    tarif_lama.tgl_berlaku_sampai = date.today()
    db.session.commit()

    tarif_baru = JenisPembayaran(
        nama=request.form['nama'],
        kode=tarif_lama.kode,
        pola_waktu=request.form['pola_waktu'],
        nominal=int(request.form['nominal']),
        keterangan=request.form.get('keterangan',''),
        tahun_pelajaran=tarif_lama.tahun_pelajaran,
        aktif=True,
        tgl_berlaku_mulai=date.today()
    )
    db.session.add(tarif_baru)
    db.session.commit()

    flash("Tarif diperbarui! Data lama aman tidak berubah.", "success")
    return redirect(url_for('bendahara.pengaturan_pembayaran', angkatan=angkatan_dasar))

@bendahara_bp.route('/pengaturan-pembayaran/status/<int:id>', methods=['POST'])
def ubah_status_pembayaran(id):
    tarif = JenisPembayaran.query.get_or_404(id)
    angkatan_dasar = get_base_tahun(tarif.tahun_pelajaran)
    tarif.aktif = not tarif.aktif
    db.session.commit()
    flash(f"Status diubah menjadi {'Aktif' if tarif.aktif else 'Nonaktif'}!", "success")
    return redirect(url_for('bendahara.pengaturan_pembayaran', angkatan=angkatan_dasar))

@bendahara_bp.route('/spp-siswa')
def spp_siswa():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    user = User.query.get(session.get('user_id'))
    session['halaman_aktif'] = 'bendahara'

    kode_tahun_aktif = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_aktif:
        tahun_aktif_db = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_aktif = tahun_aktif_db.kode if tahun_aktif_db else None

    nama_tahun, nama_semester = "Tidak Diketahui", "-"
    if kode_tahun_aktif:
        tahun_obj = TahunPelajaran.query.filter_by(kode=kode_tahun_aktif).first()
        if tahun_obj:
            potong = tahun_obj.nama.replace('Tahun Pelajaran ','').split(' - ')
            if len(potong) == 2:
                nama_semester = 'Ganjil' if potong[1].replace('Semester ','') == '1' else 'Genap'
                nama_tahun = potong[0]

    total_siswa = 0
    daftar_siswa = []

    if kode_tahun_aktif:
        riwayat = RiwayatKelas.query.filter_by(tahun_pelajaran=kode_tahun_aktif).all()
        id_unik = list({r.siswa_id for r in riwayat})
        total_siswa = len(id_unik)
        data_riwayat = {r.siswa_id: r for r in riwayat}

        for sid in id_unik:
            s = Siswa.query.get(sid)
            if not s: continue
            
            r = data_riwayat[sid]

            riwayat_pertama_siswa = RiwayatKelas.query.filter_by(siswa_id=sid).order_by(RiwayatKelas.tahun_pelajaran.asc()).first()
            tahun_penuh = riwayat_pertama_siswa.tahun_pelajaran.strip()
            angkatan_masuk = tahun_penuh[:4]

            tgl_mulai_angkatan = date(int(angkatan_masuk), 8, 1)
            batas_akhir = None if s.status == 'Aktif' else s.tanggal_berhenti

            daftar_tag, total_murni = hitung_dan_dapat_total_tagihan(
                id_siswa=sid,
                angkatan_masuk=angkatan_masuk,
                tgl_mulai=tgl_mulai_angkatan,
                batas_akhir=batas_akhir
            )

            daftar_tersimpan = pastikan_tagihan_tercatat(
                id_siswa=sid,
                angkatan_masuk=angkatan_masuk,
                tgl_mulai=tgl_mulai_angkatan,
                batas_akhir=batas_akhir
            )

            tagihan_semua = TagihanSiswa.query.filter_by(
                siswa_id=sid,
                tahun_pelajaran=tahun_penuh
            ).all()
            
            total_dibayar = sum(item['sudah_dibayar'] for item in daftar_tersimpan)
            sisa_tagihan = sum(item['sisa_tagihan'] for item in daftar_tersimpan)

            # ✅ Cek status lunas dari DB, bukan dari perhitungan
            sudah_lunas = all(item['status'] in ['Lunas', 'Sudah Lunas'] for item in daftar_tersimpan)

            print(f"[CEK PERULANGAN] SID:{sid} | Tahun Asli:{angkatan_masuk} | Hitung:{total_murni} | Lunas:{sudah_lunas}")

            daftar_siswa.append({
                'id': s.id,
                'nisn': s.nisn,
                'nama': s.nama,
                'kelas': r.kelas.nama_kelas if r.kelas else '-',
                'total_tagihan': format_rupiah(total_murni),
                'total_dibayar': format_rupiah(total_dibayar),
                'sisa_tagihan': format_rupiah(sisa_tagihan),
                'status': 'Sudah Lunas' if sudah_lunas else 'Belum Lunas'
            })

    siswa_lunas = sum(1 for row in daftar_siswa if row['status'] == 'Sudah Lunas')
    siswa_belum = total_siswa - siswa_lunas
    persen_lunas = round((siswa_lunas / total_siswa * 100), 1) if total_siswa > 0 else 0

    return render_template('index.html',
        active_page='spp_siswa', halaman_aktif='bendahara', user=user,
        user_name=session.get('user_name','Pengguna'), tahun_ajaran=nama_tahun,
        semester=nama_semester, kode_tahun_aktif=kode_tahun_aktif,
        total_siswa=total_siswa, siswa_lunas=siswa_lunas, siswa_belum=siswa_belum, persen_lunas=persen_lunas,
        daftar_siswa=daftar_siswa, daftar_tahun=TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all(),
        daftar_kelas=Kelas.query.filter_by(tahun_pelajaran=get_base_tahun(kode_tahun_aktif)).order_by(Kelas.jenjang,'nama_kelas').all() if kode_tahun_aktif else [],
        format_rupiah=format_rupiah)

# === RINCIAN TAGIHAN ===
@bendahara_bp.route('/rincian-tagihan/<kode>')
def rincian_tagihan(kode):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user = User.query.get(session.get('user_id'))
    session['halaman_aktif'] = 'bendahara'

    # ✅ BISA PAKAI ID ATAU NISN — OTOMATIS DICARI
    if str(kode).isdigit():
        siswa = Siswa.query.filter(
            (Siswa.id == int(kode)) | (Siswa.nisn == kode)
        ).first()
    else:
        siswa = None

    if not siswa:
        flash("Siswa tidak ditemukan dengan kode/NISN tersebut!", "danger")
        return redirect(url_for('bendahara.spp_siswa'))

    riwayat_pertama = RiwayatKelas.query.filter_by(siswa_id=siswa.id).order_by(RiwayatKelas.tahun_pelajaran.asc()).first()
    if not riwayat_pertama:
        flash("Riwayat kelas tidak ditemukan", "danger")
        return redirect(url_for('bendahara.spp_siswa'))

    tahun_penuh = riwayat_pertama.tahun_pelajaran.strip()
    angkatan_masuk = tahun_penuh[:4]

    tp_awal = TahunPelajaran.query.filter(TahunPelajaran.kode.like(f"{angkatan_masuk}%"))\
                                  .order_by(TahunPelajaran.tanggal_mulai.asc()).first()
    tgl_mulai_angkatan = tp_awal.tanggal_mulai if tp_awal else date(int(angkatan_masuk), 8, 1)
    batas_akhir = None if siswa.status == 'Aktif' else siswa.tanggal_berhenti

    # ✅ PASTIKAN TAGIHAN MASUK KE DATABASE SEBELUM DITAMPILKAN
    daftar_tersimpan = pastikan_tagihan_tercatat(
        id_siswa=siswa.id,
        angkatan_masuk=angkatan_masuk,
        tgl_mulai=tgl_mulai_angkatan,
        batas_akhir=batas_akhir
    )
    print(f"✅ [{siswa.nama}] NISN:{siswa.nisn} | Tagihan: {len(daftar_tersimpan)} baris disimpan/ditemukan di DB")

    # Tampilkan halaman seperti biasa
    daftar_tagihan, total_semua = hitung_dan_dapat_total_tagihan(
        id_siswa=siswa.id,
        angkatan_masuk=angkatan_masuk,
        tgl_mulai=tgl_mulai_angkatan,
        batas_akhir=batas_akhir
    )

    nama_kelas = riwayat_pertama.kelas.nama_kelas if riwayat_pertama.kelas else '-'
    tahun_ajaran = tp_awal.nama.replace('Tahun Pelajaran ', '').split(' - ')[0] if tp_awal else f"{angkatan_masuk}/{int(angkatan_masuk)+1}"

    return render_template ('index.html',
                            active_page='rincian_tagihan',
                            halaman_aktif='bendahara',
                            user=user,
                            user_name=session.get('user_name','Pengguna'),
                            tahun_ajaran=tahun_ajaran,
                            siswa=siswa,
                            id_siswa=siswa.id,
                            daftar_tagihan=daftar_tagihan,
                            nama_kelas=nama_kelas,
                            total_semua=format_rupiah(total_semua),
                            format_rupiah=format_rupiah)

@bendahara_bp.route('/simpan-pembayaran', methods=['POST'])
def simpan_pembayaran():
    if not session.get('logged_in'):
        return jsonify({"sukses": False, "pesan": "Harap masuk kembali!"}), 401

    data_masuk = request.get_json()
    if not data_masuk:
        return jsonify({"sukses": False, "pesan": "Data tidak terbaca!"}), 400

    id_siswa = data_masuk.get('id_siswa')
    rincian = data_masuk.get('rincian', [])
    metode_bayar = data_masuk.get('metode_bayar', '').strip()
    catatan = data_masuk.get('catatan', '').strip()

    tanggal_lengkap_input = data_masuk.get('tanggal_lengkap', '').strip()
    tanggal_bayar = None

    if tanggal_lengkap_input:
        try:
            # Format utama dari datetime-local: YYYY-MM-DDTHH:MM
            if 'T' in tanggal_lengkap_input:
                tanggal_bayar = datetime.strptime(tanggal_lengkap_input, "%Y-%m-%dT%H:%M")
                print(f"✅ Baca tanggal lengkap: {tanggal_bayar}")
            elif ' ' in tanggal_lengkap_input and len(tanggal_lengkap_input) > 10:
                tanggal_bayar = datetime.strptime(tanggal_lengkap_input, "%Y-%m-%d %H:%M")
            else:
                # Hanya tanggal → tetap pakai jam yang dikirim terpisah jika ada
                tgl_saja = datetime.strptime(tanggal_lengkap_input[:10], "%Y-%m-%d").date()
                jam_input = data_masuk.get('jam_bayar', '00:00').strip()
                if jam_input and ':' in jam_input:
                    jam_parts = jam_input.split(':')
                    hh = int(jam_parts[0]) if jam_parts[0].isdigit() else 0
                    mm = int(jam_parts[1]) if len(jam_parts) > 1 and jam_parts[1].isdigit() else 0
                    tanggal_bayar = datetime.combine(tgl_saja, datetime.min.time().replace(hour=hh, minute=mm))
                else:
                    tanggal_bayar = datetime.combine(tgl_saja, datetime.min.time())
                print(f"✅ Pakai jam terpisah: {tanggal_bayar}")
        except Exception as e:
            print(f"⚠️ Gagal parse: {tanggal_lengkap_input} → {e}")
            tanggal_bayar = None

    # Jika tetap kosong/tidak valid → baru pakai sekarang
    if not tanggal_bayar:
        tanggal_bayar = datetime.now()
        print(f"⚠️ Fallback ke jam sekarang: {tanggal_bayar}")

    if not id_siswa or not rincian or not metode_bayar:
        return jsonify({"sukses": False, "pesan": "Data belum lengkap!"}), 400

    try:
        print(f"✅ Terima: Siswa={id_siswa} | Jumlah rincian:{len(rincian)} | Cara:{metode_bayar}")

        siswa = Siswa.query.get(id_siswa)
        if not siswa:
            return jsonify({"sukses": False, "pesan": "Siswa tidak ditemukan!"}), 404

        riwayat_pertama = RiwayatKelas.query.filter_by(siswa_id=id_siswa).order_by(RiwayatKelas.tahun_pelajaran.asc()).first()
        if not riwayat_pertama:
            return jsonify({"sukses": False, "pesan": "Riwayat kelas tidak ditemukan!"}), 400

        tahun_pelajaran_kode = riwayat_pertama.tahun_pelajaran
        angkatan_masuk = tahun_pelajaran_kode[:4]

        jumlah_diperbarui = 0

        for item in rincian:
            
            dibayar = item.get('dibayar', 0)
            if dibayar <= 0:
                continue

            nominal_asli = item.get('nominal_asli', 0)
            sisa_hutang = item.get('sisa_hutang', 0)

            tagihan = None
            tagihan_id = item.get('id')

            if tagihan_id and str(tagihan_id).isdigit():
                tagihan = TagihanSiswa.query.filter_by(
                    siswa_id=id_siswa,
                    id=int(tagihan_id)
                ).first()

            if not tagihan and nominal_asli > 0:
                tagihan = TagihanSiswa.query.filter(
                    TagihanSiswa.siswa_id == id_siswa,
                    TagihanSiswa.nominal_tagihan == nominal_asli,
                    TagihanSiswa.tahun_pelajaran.like(f"{angkatan_masuk}%"),
                    TagihanSiswa.status.notin_(['Lunas', 'Sudah Lunas'])
                ).first()

            if tagihan:
                # ✅ =====================================================
                # 🔒 PENGAMANAN UTAMA: Hitung sisa sebenarnya dari DB
                # ✅ =====================================================
                sisa_sebenarnya = max(0, tagihan.nominal_tagihan - (tagihan.sudah_dibayar or 0))
                bayar_disimpan = min(dibayar, sisa_sebenarnya)  # Batasi!

                if bayar_disimpan <= 0:
                    print(f"   ⚠️ Lewati: tagihan sudah lunas. Sisa:{sisa_sebenarnya}")
                    continue

                print(f"   ✅ Perbarui tagihan ID:{tagihan.id} | Bayar:+{bayar_disimpan} | Sisa:{sisa_sebenarnya}")

                riwayat_baru = RiwayatPembayaran(
                    tagihan_id=tagihan.id,
                    jumlah_bayar=bayar_disimpan,
                    tanggal_bayar=tanggal_bayar,
                    metode=metode_bayar,
                    keterangan=catatan
                )
                db.session.add(riwayat_baru)

                tagihan.sudah_dibayar = (tagihan.sudah_dibayar or 0) + bayar_disimpan

                if tagihan.sudah_dibayar >= tagihan.nominal_tagihan:
                    tagihan.status = 'Lunas'
                elif tagihan.sudah_dibayar > 0:
                    tagihan.status = 'Sebagian'
                else:
                    tagihan.status = 'Belum Lunas'

                jumlah_diperbarui += 1
            else:
                print(f"   ⚠️ Tagihan tidak ditemukan! Nominal:{nominal_asli}")

        db.session.commit()

        return jsonify({
            "sukses": True,
            "pesan": f"Berhasil! {jumlah_diperbarui} tagihan diperbarui."
        })

    except Exception as e:
        db.session.rollback()
        print("❌ KESALAHAN SIMPAN:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"sukses": False, "pesan": f"Kesalahan: {str(e)}"}), 500

@bendahara_bp.route('/api-rincian-tagihan/<int:id_siswa>')
def api_rincian_tagihan(id_siswa):
    if not session.get('logged_in'):
        return jsonify({"sukses": False, "pesan": "Harap masuk kembali!"}), 401

    siswa = Siswa.query.get(id_siswa)
    if not siswa:
        return jsonify({"sukses": False, "pesan": "Siswa tidak ditemukan!"}), 404

    riwayat_pertama = RiwayatKelas.query.filter_by(siswa_id=id_siswa).order_by(RiwayatKelas.tahun_pelajaran.asc()).first()
    if not riwayat_pertama:
        return jsonify({"sukses": False, "pesan": "Riwayat kelas tidak ditemukan!"}), 404

    tahun_penuh = riwayat_pertama.tahun_pelajaran.strip()
    angkatan_masuk = tahun_penuh[:4]

    tp_awal = TahunPelajaran.query.filter(TahunPelajaran.kode.like(f"{angkatan_masuk}%"))\
                                  .order_by(TahunPelajaran.tanggal_mulai.asc()).first()
    tgl_mulai_angkatan = tp_awal.tanggal_mulai if tp_awal else date(int(angkatan_masuk), 8, 1)

    batas_akhir = None if siswa.status == 'Aktif' else siswa.tanggal_berhenti

    daftar_tagihan, total_semua = hitung_dan_dapat_total_tagihan(
        id_siswa=id_siswa,
        angkatan_masuk=angkatan_masuk,
        tgl_mulai=tgl_mulai_angkatan,
        batas_akhir=batas_akhir
    )

    daftar_tagihan = [t for t in daftar_tagihan]

    return jsonify({
        "sukses": True,
        "tagihan": daftar_tagihan,
        "total": total_semua
    })

@bendahara_bp.route('/bendahara/cek-tagihan/<kode>')
def cek_tagihan(kode):
    if not session.get('logged_in'):
        return "Harap login"

    if str(kode).isdigit():
        siswa = Siswa.query.filter(
            (Siswa.id == int(kode)) | (Siswa.nisn == kode)
        ).first()
    else:
        siswa = Siswa.query.filter_by(nisn=kode).first()

    if not siswa:
        return f"Siswa dengan kode/NISN '{kode}' tidak ditemukan"

    tagihan_list = TagihanSiswa.query.filter_by(siswa_id=siswa.id).all()

    peta_bulan = {
        'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5, 'Juni': 6,
        'Juli': 7, 'Agustus': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
    }

    def kunci_urut(tagihan):
        teks = str(tagihan.bulan or "")
        bagian = teks.strip().split()
        if len(bagian) >= 2:
            nama_bulan = bagian[0]
            try:
                tahun = int(bagian[1])
                nomor_bulan = peta_bulan.get(nama_bulan, 0)
                return (tahun, nomor_bulan)
            except:
                pass
        return (9999, 99)

    tagihan_list.sort(key=kunci_urut)

    jumlah_maks_bayar = 0
    for t in tagihan_list:
        daftar_bayar = getattr(t, 'riwayat', None) or getattr(t, 'riwayat_pembayaran', [])
        jumlah_maks_bayar = max(jumlah_maks_bayar, len(daftar_bayar))

    header_kolom = """
        <th>ID Tagihan</th>
        <th>Jenis Pembayaran</th>
        <th>Periode</th>
        <th>Total Tagihan</th>
        <th>Sudah Dibayar</th>
        <th>Sisa Tagihan</th>
        <th>Status</th>
    """
    for i in range(1, jumlah_maks_bayar + 1):
        header_kolom += f"<th>Pembayaran ke-{i}</th><th>Tanggal</th><th>Metode Bayar</th>"

    hasil = f"""
    <style>
        table {{ border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 13px; }}
        th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; vertical-align: middle; }}
        th {{ background: #f0f4f8; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        h3 {{ color: #2d3748; }}
        .lunas {{ color: #2f855a; font-weight: bold; }}
        .sebagian {{ color: #d69e2e; font-weight: bold; }}
        .belum {{ color: #e53e3e; font-weight: bold; }}
        .metode {{ color: #555; font-size: 12px; font-style: italic; }}
        .tgl {{ color: #444; font-size: 12px; }}
    </style>
    <h3>📋 ISI TAGIHAN SISWA: {siswa.nama} | ID:{siswa.id} | NISN:{siswa.nisn}</h3>
    <p><strong>Keterangan:</strong> Setiap pembayaran terpisah → Nominal | Tanggal | Metode</p>
    <table>
        <tr>{header_kolom}</tr>
    """

    if not tagihan_list:
        hasil += "<tr><td colspan='10' style='text-align:center; padding:15px;'>Belum ada data tagihan</td></tr>"
    else:
        from models import JenisPembayaran
        for t in tagihan_list:
            nama_jenis = "-"
            if t.jenis_pembayaran_id:
                jp = JenisPembayaran.query.get(t.jenis_pembayaran_id)
                if jp:
                    nama_jenis = jp.nama

            periode = t.bulan or (f"Semester {t.semester}" if t.semester else "-")
            nominal = t.nominal_tagihan or 0
            sudah = t.sudah_dibayar or 0
            sisa = max(0, nominal - sudah)

            kelas_status = "belum"
            if t.status in ["Lunas", "Sudah Lunas"]:
                kelas_status = "lunas"
            elif t.status == "Sebagian":
                kelas_status = "sebagian"

            daftar_bayar = getattr(t, 'riwayat', None) or getattr(t, 'riwayat_pembayaran', [])
            daftar_bayar = sorted(daftar_bayar, key=lambda r: r.tanggal_bayar or date(1900,1,1))

            baris = f"""
                <td>{t.id}</td>
                <td>{nama_jenis}</td>
                <td>{periode}</td>
                <td><strong>Rp {nominal:,}</strong></td>
                <td>Rp {sudah:,}</td>
                <td>Rp {sisa:,}</td>
                <td class="{kelas_status}">{t.status or '-'}</td>
            """

            for bayar in daftar_bayar:
                nominal_bayar = bayar.jumlah_bayar or 0
                metode = bayar.metode or "-"

                if bayar.tanggal_bayar:
                    if hasattr(bayar.tanggal_bayar, 'hour'):
                        jam = bayar.tanggal_bayar.strftime('%H:%M')
                        tgl = f"{bayar.tanggal_bayar.strftime('%d/%m/%Y')} {jam}"
                    else:
                        tgl = bayar.tanggal_bayar.strftime('%d/%m/%Y')
                else:
                    tgl = "-"

                baris += f"""
                    <td>Rp {nominal_bayar:,}</td>
                    <td class="tgl">{tgl}</td>
                    <td class="metode">{metode}</td>
                """

            jumlah_kosong = jumlah_maks_bayar - len(daftar_bayar)
            for _ in range(jumlah_kosong):
                baris += "<td>-</td><td>-</td><td>-</td>"

            hasil += f"<tr>{baris}</tr>"

    hasil += "</table>"
    return hasil