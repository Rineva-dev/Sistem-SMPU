document.addEventListener('DOMContentLoaded', function () {
    const ctxEl = document.getElementById('grafikAbsensi');
    if (!ctxEl) return;

    // Ambil data dari elemen tersembunyi yang disiapkan di HTML
    const labelBulan = JSON.parse(document.getElementById('data-label-bulan').textContent);
    const dataHadir = JSON.parse(document.getElementById('data-hadir').textContent);
    const dataTerlambat = JSON.parse(document.getElementById('data-terlambat').textContent);
    const dataIzin = JSON.parse(document.getElementById('data-izin').textContent);
    const dataAlfa = JSON.parse(document.getElementById('data-alfa').textContent);

    const ctx = ctxEl.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labelBulan,
            datasets: [
                {
                    label: 'Hadir',
                    data: dataHadir,
                    backgroundColor: '#22c55e',
                    borderRadius: 6
                },
                {
                    label: 'Terlambat',
                    data: dataTerlambat,
                    backgroundColor: '#f97316',
                    borderRadius: 6
                },
                {
                    label: 'Izin/Sakit',
                    data: dataIzin,
                    backgroundColor: '#3b82f6',
                    borderRadius: 6
                },
                {
                    label: 'Alfa',
                    data: dataAlfa,
                    backgroundColor: '#ef4444',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { usePointStyle: true, padding: 16 }
                }
            },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
});