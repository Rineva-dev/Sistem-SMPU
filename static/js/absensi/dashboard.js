
document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("grafikAbsensi");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    // Hindari membuat grafik ganda apabila script dipanggil kembali.
    const existingChart = Chart.getChart(canvas);

    if (existingChart) {
        existingChart.destroy();
    }

    // Ambil data asli dari template Flask/Jinja.
    function readJSON(id, fallback = []) {
        const element = document.getElementById(id);

        if (!element) return fallback;

        try {
            const parsed = JSON.parse(element.textContent);
            return Array.isArray(parsed) ? parsed : fallback;
        } catch (error) {
            console.error("Data grafik tidak valid:", id, error);
            return fallback;
        }
    }

    const labels = readJSON("data-label-bulan");
    const hadir = readJSON("data-hadir");
    const terlambat = readJSON("data-terlambat");
    const izin = readJSON("data-izin");

    const ctx = canvas.getContext("2d");

    // Gradasi transparan supaya grafik terlihat elegan,
    // tanpa memenuhi area grafik dengan warna pekat.
    const gradientHadir = ctx.createLinearGradient(0, 0, 0, 340);
    gradientHadir.addColorStop(0, "rgba(22, 163, 104, 0.22)");
    gradientHadir.addColorStop(1, "rgba(22, 163, 104, 0.00)");

    const gradientTerlambat = ctx.createLinearGradient(0, 0, 0, 340);
    gradientTerlambat.addColorStop(0, "rgba(233, 162, 59, 0.13)");
    gradientTerlambat.addColorStop(1, "rgba(233, 162, 59, 0.00)");

    const gradientIzin = ctx.createLinearGradient(0, 0, 0, 340);
    gradientIzin.addColorStop(0, "rgba(101, 88, 217, 0.13)");
    gradientIzin.addColorStop(1, "rgba(101, 88, 217, 0.00)");

    const commonLine = {
        type: "line",
        borderWidth: 2.5,
        tension: 0.35,
        cubicInterpolationMode: "monotone",
        fill: true,

        // Titik muncul saat grafik disentuh atau diarahkan kursor
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHitRadius: 14,
        pointHoverBorderWidth: 3,

        spanGaps: true
    };

    new Chart(ctx, {
        type: "line",

        data: {
            labels: labels,

            datasets: [
                {
                    ...commonLine,
                    label: "Hadir",
                    data: hadir,
                    borderColor: "#16865b",
                    backgroundColor: gradientHadir,
                    pointBackgroundColor: "#16865b",
                    pointBorderColor: "#ffffff",
                    pointHoverBackgroundColor: "#16865b",
                    pointHoverBorderColor: "#ffffff"
                },
                {
                    ...commonLine,
                    label: "Terlambat",
                    data: terlambat,
                    borderColor: "#e9a23b",
                    backgroundColor: gradientTerlambat,
                    pointBackgroundColor: "#e9a23b",
                    pointBorderColor: "#ffffff",
                    pointHoverBackgroundColor: "#e9a23b",
                    pointHoverBorderColor: "#ffffff"
                },
                {
                    ...commonLine,
                    label: "Izin / Sakit",
                    data: izin,
                    borderColor: "#6558d9",
                    backgroundColor: gradientIzin,
                    pointBackgroundColor: "#6558d9",
                    pointBorderColor: "#ffffff",
                    pointHoverBackgroundColor: "#6558d9",
                    pointHoverBorderColor: "#ffffff"
                }
            ]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            interaction: {
                mode: "index",
                intersect: false
            },

            layout: {
                padding: {
                    top: 12,
                    right: 8,
                    bottom: 2,
                    left: 2
                }
            },

            animation: {
                duration: 850,
                easing: "easeOutQuart"
            },

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    enabled: true,
                    backgroundColor: "#17243a",
                    titleColor: "#ffffff",
                    bodyColor: "#e3e9f3",
                    footerColor: "#aebbd0",
                    padding: 14,
                    cornerRadius: 12,
                    boxPadding: 5,
                    usePointStyle: true,
                    displayColors: true,

                    titleFont: {
                        family: "Inter, sans-serif",
                        size: 13,
                        weight: "700"
                    },

                    bodyFont: {
                        family: "Inter, sans-serif",
                        size: 12,
                        weight: "500"
                    },

                    callbacks: {
                        label: function (context) {
                            const value = context.parsed.y;
                            const formatted = Number.isFinite(value)
                                ? value.toLocaleString("id-ID")
                                : "—";

                            return " " + context.dataset.label + ": " + formatted;
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
                        display: false,
                        drawTicks: false
                    },

                    ticks: {
                        color: "#8994a7",
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 12,
                        padding: 12,

                        font: {
                            family: "Inter, sans-serif",
                            size: 11,
                            weight: "500"
                        }
                    }
                },

                y: {
                    beginAtZero: true,

                    border: {
                        display: false,
                        dash: [4, 4]
                    },

                    grid: {
                        color: "rgba(148, 163, 184, 0.16)",
                        drawTicks: false,
                        lineWidth: 1
                    },

                    ticks: {
                        color: "#8994a7",
                        padding: 12,
                        precision: 0,

                        font: {
                            family: "Inter, sans-serif",
                            size: 11
                        },

                        callback: function (value) {
                            return Number(value).toLocaleString("id-ID");
                        }
                    }
                }
            }
        }
    });
});
