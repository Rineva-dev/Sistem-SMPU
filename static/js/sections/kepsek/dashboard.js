/* ==========================================
   DASBOR KEPALA SEKOLAH - FUNGSI & GRAFIK
========================================== */

document.addEventListener('DOMContentLoaded', function () {
    // Jalankan fungsi grafik saat halaman siap
    initPerformaChart();
});

/**
 * Inisialisasi Grafik Perkembangan Akademik & Kehadiran
 * Mengambil data dari variabel yang dikirim backend
 */
function initPerformaChart() {
    const ctx = document.getElementById('performaChart');
    if (!ctx) return; // Hentikan jika elemen grafik tidak ada

    // Ambil data dari backend (jika belum ada, pakai data kosong)
    const dataBulan = window.chartData?.bulan || [];
    const dataKehadiran = window.chartData?.kehadiran || [];
    const dataRataNilai = window.chartData?.nilai || [];

    // Buat grafik
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dataBulan,
            datasets: [
                {
                    label: 'Rata-rata Kehadiran (%)',
                    data: dataKehadiran,
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#4e73df'
                },
                {
                    label: 'Rata-rata Nilai Akademik',
                    data: dataRataNilai,
                    borderColor: '#1cc88a',
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#1cc88a'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        font: { size: 13 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true, // Ubah ke true agar data kosong terlihat rapi
                    min: 0,
                    max: 100,
                    ticks: { stepSize: 10 },
                    grid: { borderDash: [2, 4] }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}