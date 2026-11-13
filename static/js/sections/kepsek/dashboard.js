
/* ==========================================================
   KEPSEK EXECUTIVE DASHBOARD
   Chart.js + SPA Lifecycle
========================================================== */

(function () {
    'use strict';

    // Hindari listener ganda ketika halaman dimuat melalui SPA
    if (window.__kepsekDashboardRegistered) {
        if (typeof window.initKepsekDashboard === 'function') {
            window.initKepsekDashboard();
        }
        return;
    }

    window.__kepsekDashboardRegistered = true;

    let performaChartInstance = null;

    function getChartData() {
        return window.kepsekChartData || window.chartData || {};
    }

    function initPerformaChart() {
        const canvas = document.getElementById('performaChart');
        const emptyState = document.getElementById('kdChartEmpty');

        if (!canvas) return;

        // Pastikan instance lama dibersihkan
        if (performaChartInstance) {
            performaChartInstance.destroy();
            performaChartInstance = null;
        }

        if (typeof Chart === 'undefined') {
            console.warn('[Kepsek Dashboard] Chart.js belum tersedia.');
            return;
        }

        const chartData = getChartData();

        const bulan = Array.isArray(chartData.bulan)
            ? chartData.bulan
            : [];

        const kehadiran = Array.isArray(chartData.kehadiran)
            ? chartData.kehadiran
            : [];

        const nilai = Array.isArray(chartData.nilai)
            ? chartData.nilai
            : [];

        const hasData = bulan.length > 0 &&
            (kehadiran.some(v => v !== null && v !== undefined) ||
             nilai.some(v => v !== null && v !== undefined));

        if (!hasData) {
            canvas.style.display = 'none';

            if (emptyState) {
                emptyState.hidden = false;
            }

            return;
        }

        canvas.style.display = 'block';

        if (emptyState) {
            emptyState.hidden = true;
        }

        const context = canvas.getContext('2d');

        const greenGradient = context.createLinearGradient(0, 0, 0, 270);
        greenGradient.addColorStop(0, 'rgba(5, 150, 105, 0.19)');
        greenGradient.addColorStop(1, 'rgba(5, 150, 105, 0.00)');

        const blueGradient = context.createLinearGradient(0, 0, 0, 270);
        blueGradient.addColorStop(0, 'rgba(100, 116, 232, 0.13)');
        blueGradient.addColorStop(1, 'rgba(100, 116, 232, 0.00)');

        performaChartInstance = new Chart(context, {
            type: 'line',

            data: {
                labels: bulan,

                datasets: [
                    {
                        label: 'Kehadiran',
                        data: kehadiran,

                        borderColor: '#07966b',
                        backgroundColor: greenGradient,

                        borderWidth: 2.8,
                        fill: true,
                        tension: 0.4,

                        pointRadius: 3,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#07966b',
                        pointBorderWidth: 2,

                        spanGaps: true
                    },

                    {
                        label: 'Nilai Akademik',
                        data: nilai,

                        borderColor: '#7182e8',
                        backgroundColor: blueGradient,

                        borderWidth: 2.8,
                        fill: true,
                        tension: 0.4,

                        pointRadius: 3,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#7182e8',
                        pointBorderWidth: 2,

                        spanGaps: true
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                interaction: {
                    mode: 'index',
                    intersect: false
                },

                animation: {
                    duration: 850,
                    easing: 'easeOutQuart'
                },

                plugins: {
                    legend: {
                        display: false
                    },

                    tooltip: {
                        backgroundColor: '#153c2d',
                        titleColor: '#ffffff',
                        bodyColor: '#d7eee2',

                        padding: 12,
                        cornerRadius: 10,

                        displayColors: true,
                        usePointStyle: true,

                        titleFont: {
                            family: 'Inter',
                            size: 11,
                            weight: 'bold'
                        },

                        bodyFont: {
                            family: 'Inter',
                            size: 10
                        },

                        callbacks: {
                            label: function (context) {
                                const value = context.parsed.y;

                                if (value === null || value === undefined) {
                                    return context.dataset.label + ': Tidak ada data';
                                }

                                return context.dataset.label + ': ' + value +
                                    (context.datasetIndex === 0 ? '%' : '');
                            }
                        }
                    }
                },

                scales: {
                    x: {
                        border: {
                            display: false
                        },

                        grid: {
                            display: false
                        },

                        ticks: {
                            color: '#94a39a',

                            font: {
                                family: 'Inter',
                                size: 9,
                                weight: '600'
                            }
                        }
                    },

                    y: {
                        beginAtZero: true,

                        min: 0,
                        max: 100,

                        border: {
                            display: false
                        },

                        ticks: {
                            stepSize: 20,
                            color: '#94a39a',

                            font: {
                                family: 'Inter',
                                size: 9
                            },

                            callback: function (value) {
                                return value;
                            }
                        },

                        grid: {
                            color: 'rgba(29, 78, 52, 0.07)',
                            drawTicks: false
                        }
                    }
                }
            }
        });
    }

    function initKepsekDashboard() {
        const dashboard = document.getElementById('kepsekDashboard');

        if (!dashboard) {
            if (performaChartInstance) {
                performaChartInstance.destroy();
                performaChartInstance = null;
            }
            return;
        }

        initPerformaChart();
    }

    function destroyKepsekDashboard() {
        if (performaChartInstance) {
            performaChartInstance.destroy();
            performaChartInstance = null;
        }
    }

    // Expose agar bisa dipanggil ulang oleh SPA
    window.initKepsekDashboard = initKepsekDashboard;

    // Initial page load
    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            initKepsekDashboard,
            { once: true }
        );
    } else {
        initKepsekDashboard();
    }

    // SPA navigation
    document.addEventListener('spa:page-loaded', initKepsekDashboard);

    document.addEventListener(
        'spa:before-page-unload',
        destroyKepsekDashboard
    );

})();
