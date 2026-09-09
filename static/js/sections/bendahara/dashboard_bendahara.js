document.addEventListener('DOMContentLoaded', function () {
  const canvas = document.getElementById('keuanganChart');
  if (!canvas) {
    console.error("Canvas tidak ditemukan!");
    return;
  }
  const ctx = canvas.getContext('2d');

  console.log("📊 Label Bulan:", labelBulan);
  console.log("📊 Pemasukan:", dataMasuk);
  console.log("📊 Pengeluaran:", dataKeluar);

  if (!labelBulan.length || !dataMasuk.length) {
    console.warn("⚠️ Data grafik masih kosong!");
    return;
  }

  const nilaiMaksMasuk = Math.max(...dataMasuk);
  const nilaiMaksKeluar = Math.max(...dataKeluar);
  const nilaiMaks = Math.max(nilaiMaksMasuk, nilaiMaksKeluar, 1000000);
  const batasAtas = nilaiMaks * 1.15;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labelBulan,
      datasets: [
        {
            label: 'Pemasukan',
            data: dataMasuk,
            borderColor: '#10b981',
            backgroundColor: function(context) {
            const chart = context.chart;
            const {ctx, chartArea} = chart;
            if (!chartArea) return 'rgba(16, 185, 129, 0.15)';
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
            gradient.addColorStop(1, 'rgba(16, 185, 129, 0.03)');
            return gradient;
            },
            borderWidth: 0.5,
            pointRadius: 0, // ✅ TITIK DIHILANGKAN
            pointHoverRadius: 4,
            pointBackgroundColor: '#10b981',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 1.2,
            fill: true,
            tension: 0.38,
            cubicInterpolationMode: 'monotone'
        },
        {
            label: 'Pengeluaran',
            data: dataKeluar,
            borderColor: '#3b82f6',
            backgroundColor: function(context) {
            const chart = context.chart;
            const {ctx, chartArea} = chart;
            if (!chartArea) return 'rgba(59, 130, 246, 0.15)';
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.35)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.03)');
            return gradient;
            },
            borderWidth: 0.5,
            pointRadius: 0, // ✅ TITIK DIHILANGKAN
            pointHoverRadius: 4,
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 1.2,
            fill: true,
            tension: 0.38,
            cubicInterpolationMode: 'monotone'
        }
        ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        mode: 'index',
        intersect: false,
        axis: 'x'
      },
      layout: {
        padding: { top: 10, right: 20, bottom: 10, left: 10 }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'center', // ✅ LEGENDA DI TENGAH
          labels: {
            font: { size: 13.5, family: "'Segoe UI', 'Inter', sans-serif", weight: '600' },
            usePointStyle: true,
            pointStyle: 'circle',
            boxWidth: 8,
            boxHeight: 8,
            padding: 25,
            color: '#374151'
          }
        },
        tooltip: {
          backgroundColor: '#ffffff',
          titleColor: '#1f2937',
          bodyColor: '#374151',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          titleFont: { size: 13.5, weight: '700', family: "'Segoe UI', sans-serif" },
          bodyFont: { size: 12.5, family: "'Segoe UI', sans-serif" },
          padding: { top: 12, right: 16, bottom: 12, left: 16 },
          cornerRadius: 10,
          displayColors: true,
          boxWidth: 10,
          boxHeight: 10,
          boxPadding: 6,
          useRoundedPointStyle: true,
          callbacks: {
            label: function(tooltipItem) {
              const nilai = tooltipItem.raw || 0;
              return ' ' + tooltipItem.dataset.label + ': Rp ' + nilai.toLocaleString('id-ID');
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: batasAtas,
          grid: { 
            color: '#f1f5f9',
            drawBorder: false,
            borderDash: []
          },
          ticks: {
            font: { size: 11.5, family: "'Segoe UI', sans-serif" },
            color: '#64748b',
            maxTicksLimit: 6,
            callback: function(value) {
              return 'Rp ' + value.toLocaleString('id-ID');
            }
          }
        },
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 12, weight: '500', family: "'Segoe UI', sans-serif" },
            color: '#475569'
          }
        }
      },
      elements: {
        line: {
          borderCapStyle: 'round',
          borderJoinStyle: 'round'
        }
      }
    }
  });
});