// =========================================================
// SMPU - GRAFIK ABSENSI
// SPA COMPATIBLE
// =========================================================

(() => {
    "use strict";

    // -----------------------------------------------------
    // FUNGSI MEMBACA DATA JSON DARI TEMPLATE
    // -----------------------------------------------------

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

    // -----------------------------------------------------
    // HANCURKAN GRAFIK LAMA
    // -----------------------------------------------------

    function destroyGrafikAbsensi() {
        const canvas = document.getElementById("grafikAbsensi");

        if (!canvas || typeof Chart === "undefined") return;

        const existingChart = Chart.getChart(canvas);

        if (existingChart) {
            existingChart.destroy();
        }
    }

    // -----------------------------------------------------
    // INISIALISASI GRAFIK
    // -----------------------------------------------------

    function initGrafikAbsensi() {
        const canvas = document.getElementById("grafikAbsensi");

        if (!canvas || typeof Chart === "undefined") {
            return;
        }

        // Hindari inisialisasi ganda.
        if (Chart.getChart(canvas)) {
            return;
        }

        const labels = readJSON("data-label-bulan");
        const hadir = readJSON("data-hadir");
        const terlambat = readJSON("data-terlambat");
        const izin = readJSON("data-izin");

        const ctx = canvas.getContext("2d");

        if (!ctx) return;

        // -------------------------------------------------
        // GRADASI WARNA
        // -------------------------------------------------

        const gradientHadir = ctx.createLinearGradient(0, 0, 0, 340);
        gradientHadir.addColorStop(0, "rgba(22, 163, 104, 0.22)");
        gradientHadir.addColorStop(1, "rgba(22, 163, 104, 0.00)");

        const gradientTerlambat = ctx.createLinearGradient(0, 0, 0, 340);
        gradientTerlambat.addColorStop(0, "rgba(233, 162, 59, 0.13)");
        gradientTerlambat.addColorStop(1, "rgba(233, 162, 59, 0.00)");

        const gradientIzin = ctx.createLinearGradient(0, 0, 0, 340);
        gradientIzin.addColorStop(0, "rgba(101, 88, 217, 0.13)");
        gradientIzin.addColorStop(1, "rgba(101, 88, 217, 0.00)");

        // -------------------------------------------------
        // KONFIGURASI GARIS
        // -------------------------------------------------

        const commonLine = {
            type: "line",
            borderWidth: 2.5,
            tension: 0.35,
            cubicInterpolationMode: "monotone",
            fill: true,

            pointRadius: 0,
            pointHoverRadius: 5,
            pointHitRadius: 14,
            pointHoverBorderWidth: 3,

            spanGaps: true
        };

        // -------------------------------------------------
        // BUAT CHART
        // -------------------------------------------------

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

        console.log("[SMPU SPA] Grafik absensi berhasil diinisialisasi.");
    }

    // -----------------------------------------------------
    // SIMPAN FUNGSI AGAR BISA DIPANGGIL ULANG OLEH SPA
    // -----------------------------------------------------

    window.__smpuInitGrafikAbsensi = initGrafikAbsensi;
    window.__smpuDestroyGrafikAbsensi = destroyGrafikAbsensi;

    // -----------------------------------------------------
    // EVENT SPA
    // -----------------------------------------------------

    if (!window.__smpuGrafikAbsensiEventsRegistered) {

        // Halaman baru selesai dimuat melalui SPA.
        document.addEventListener("spa:page-loaded", function () {
            window.__smpuInitGrafikAbsensi?.();
        });

        // Bersihkan grafik sebelum konten halaman diganti.
        document.addEventListener("spa:before-page-unload", function () {
            window.__smpuDestroyGrafikAbsensi?.();
        });

        window.__smpuGrafikAbsensiEventsRegistered = true;
    }

    // -----------------------------------------------------
    // HALAMAN PERTAMA KALI DIBUKA (NON-SPA)
    // -----------------------------------------------------

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initGrafikAbsensi,
            { once: true }
        );
    } else {
        initGrafikAbsensi();
    }

})();