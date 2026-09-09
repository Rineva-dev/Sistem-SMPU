// Inisialisasi Grafik Kehadiran
document.addEventListener('DOMContentLoaded', function () {
    const canvasEl = document.getElementById('kehadiranChart');
    if (!canvasEl) {
        return;
    }

    // Cek juga apakah Chart.js sudah tersedia
    if (typeof Chart === 'undefined') {
        return;
    }
    const ctx = document.getElementById('kehadiranChart').getContext('2d');
    const kehadiranChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'],
            datasets: [{
                label: 'Persentase Kehadiran (%)',
                data: [92, 95, 90, 97, 94, 88, 85],
                borderColor: '#005B2B',
                backgroundColor: 'rgba(0, 91, 43, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: value => value + '%' }
                }
            }
        }
    });
});