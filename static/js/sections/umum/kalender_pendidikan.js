// Tombol ganti tampilan
document.getElementById('btnTampilanDaftar').addEventListener('click', function () {
  document.getElementById('tampilanDaftar').classList.remove('d-none');
  document.getElementById('tampilanKalender').classList.add('d-none');
  this.classList.add('active');
  document.getElementById('btnTampilanKalender').classList.remove('active');
});

document.getElementById('btnTampilanKalender').addEventListener('click', function () {
  document.getElementById('tampilanDaftar').classList.add('d-none');
  document.getElementById('tampilanKalender').classList.remove('d-none');
  this.classList.add('active');
  document.getElementById('btnTampilanDaftar').classList.remove('active');

  // Hanya tampilkan pesan, TIDAK memuat kalender
  const wadah = document.getElementById('kalenderUtama');
  wadah.innerHTML = `
    <div class="alert alert-info text-center py-5">
      <i class="fas fa-calendar-times fa-2x mb-3"></i>
      <h5>Tampilan Kalender Dinonaktifkan</h5>
      <p class="mb-0">Untuk performa yang lebih ringan, fitur tampilan kalender sementara dinonaktifkan.<br>Silakan gunakan tampilan daftar untuk melihat jadwal kegiatan.</p>
    </div>
  `;
});