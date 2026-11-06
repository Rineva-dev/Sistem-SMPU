
(() => {
    "use strict";

    const CHART_JS_URL =
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js";

    function loadChartJs() {
        if (window.Chart) return Promise.resolve();

        if (window.__bendaharaChartPromise) {
            return window.__bendaharaChartPromise;
        }

        window.__bendaharaChartPromise = new Promise((resolve, reject) => {
            let script = document.querySelector(
                'script[src*="chart.umd.min.js"]'
            );

            if (!script) {
                script = document.createElement("script");
                script.src = CHART_JS_URL;
                script.async = true;
                document.head.appendChild(script);
            }

            if (window.Chart) {
                resolve();
                return;
            }

            script.addEventListener("load", resolve, { once: true });
            script.addEventListener("error", () => {
                reject(new Error("Chart.js gagal dimuat."));
            }, { once: true });
        });

        return window.__bendaharaChartPromise;
    }

    function formatRupiahRingkas(value) {
        const nominal = Number(value) || 0;

        if (nominal >= 1_000_000_000) {
            return "Rp " + (nominal / 1_000_000_000).toLocaleString(
                "id-ID", { maximumFractionDigits: 1 }
            ) + " M";
        }

        if (nominal >= 1_000_000) {
            return "Rp " + (nominal / 1_000_000).toLocaleString(
                "id-ID", { maximumFractionDigits: 1 }
            ) + " jt";
        }

        if (nominal >= 1_000) {
            return "Rp " + (nominal / 1_000).toLocaleString(
                "id-ID", { maximumFractionDigits: 0 }
            ) + " rb";
        }

        return "Rp " + nominal.toLocaleString("id-ID");
    }

    function formatRupiahLengkap(value) {
        return "Rp " + (Number(value) || 0).toLocaleString("id-ID");
    }

    function buatGradient(context, warnaAtas, warnaBawah) {
        const chart = context.chart;
        const area = chart.chartArea;

        if (!area) return warnaBawah;

        const gradient = chart.ctx.createLinearGradient(
            0, area.top, 0, area.bottom
        );

        gradient.addColorStop(0, warnaAtas);
        gradient.addColorStop(1, warnaBawah);

        return gradient;
    }

    async function initDashboardBendahara() {
        const root = document.querySelector(".dashboard-bendahara-page");

        if (!root || root.dataset.chartInitialized === "true") return;

        const canvas = root.querySelector("#keuanganChart");
        const dataElement = root.querySelector("#dbKeuanganData");
        const emptyState = root.querySelector("#keuanganChartEmpty");

        if (!canvas || !dataElement) return;

        let data;

        try {
            data = JSON.parse(dataElement.textContent || "{}");
        } catch (error) {
            console.error("Data grafik keuangan tidak valid:", error);
            if (emptyState) emptyState.hidden = false;
            return;
        }

        const labels = Array.isArray(data.labels) ? data.labels : [];
        const pemasukan = Array.isArray(data.masuk) ? data.masuk : [];
        const pengeluaran = Array.isArray(data.keluar) ? data.keluar : [];

        const dataMasuk = pemasukan.map(value => Number(value) || 0);
        const dataKeluar = pengeluaran.map(value => Number(value) || 0);

        const adaData = labels.length > 0 && (
            dataMasuk.some(value => value !== 0) ||
            dataKeluar.some(value => value !== 0)
        );

        if (!adaData) {
            canvas.style.display = "none";
            if (emptyState) emptyState.hidden = false;
            root.dataset.chartInitialized = "true";
            return;
        }

        try {
            await loadChartJs();

            // Pastikan halaman belum diganti ketika library sedang dimuat
            if (!root.isConnected || !canvas.isConnected) return;

            if (canvas._keuanganChart) {
                canvas._keuanganChart.destroy();
            }

            if (emptyState) emptyState.hidden = true;
            canvas.style.display = "block";

            canvas._keuanganChart = new window.Chart(
                canvas.getContext("2d"),
                {
                    type: "line",

                    data: {
                        labels,
                        datasets: [
                            {
                                label: "Pemasukan",
                                data: dataMasuk,
                                borderColor: "#0ca678",
                                backgroundColor: context => buatGradient(
                                    context,
                                    "rgba(12,166,120,.22)",
                                    "rgba(12,166,120,.005)"
                                ),
                                borderWidth: 2.5,
                                pointRadius: 3,
                                pointHoverRadius: 6,
                                pointBackgroundColor: "#0ca678",
                                pointBorderColor: "#ffffff",
                                pointBorderWidth: 2,
                                fill: true,
                                tension: 0.38
                            },
                            {
                                label: "Pengeluaran",
                                data: dataKeluar,
                                borderColor: "#5688df",
                                backgroundColor: context => buatGradient(
                                    context,
                                    "rgba(86,136,223,.16)",
                                    "rgba(86,136,223,.005)"
                                ),
                                borderWidth: 2.5,
                                pointRadius: 3,
                                pointHoverRadius: 6,
                                pointBackgroundColor: "#5688df",
                                pointBorderColor: "#ffffff",
                                pointBorderWidth: 2,
                                fill: true,
                                tension: 0.38
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        resizeDelay: 100,

                        interaction: {
                            mode: "index",
                            intersect: false
                        },

                        animation: {
                            duration: 850,
                            easing: "easeOutQuart"
                        },

                        layout: {
                            padding: {
                                top: 8,
                                right: 10,
                                bottom: 0,
                                left: 2
                            }
                        },

                        plugins: {
                            legend: {
                                display: false
                            },

                            tooltip: {
                                backgroundColor: "#17392c",
                                titleColor: "#d9f6e7",
                                bodyColor: "#ffffff",
                                borderColor: "rgba(255,255,255,.12)",
                                borderWidth: 1,
                                padding: 13,
                                cornerRadius: 11,
                                displayColors: true,
                                usePointStyle: true,
                                boxWidth: 8,
                                boxHeight: 8,

                                titleFont: {
                                    family: "Inter, Segoe UI, sans-serif",
                                    size: 11,
                                    weight: "700"
                                },

                                bodyFont: {
                                    family: "Inter, Segoe UI, sans-serif",
                                    size: 11,
                                    weight: "500"
                                },

                                callbacks: {
                                    label(context) {
                                        return " " + context.dataset.label +
                                            ": " +
                                            formatRupiahLengkap(
                                                context.parsed.y
                                            );
                                    }
                                }
                            }
                        },

                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },
                                border: {
                                    display: false
                                },
                                ticks: {
                                    color: "#87968e",
                                    font: {
                                        family: "Inter, Segoe UI, sans-serif",
                                        size: 10,
                                        weight: "600"
                                    },
                                    maxRotation: 0,
                                    autoSkip: true
                                }
                            },

                            y: {
                                beginAtZero: true,
                                border: {
                                    display: false,
                                    dash: [3, 5]
                                },
                                grid: {
                                    color: "rgba(139,157,146,.13)",
                                    drawTicks: false
                                },
                                ticks: {
                                    color: "#93a198",
                                    padding: 10,
                                    maxTicksLimit: 6,
                                    font: {
                                        family: "Inter, Segoe UI, sans-serif",
                                        size: 9
                                    },
                                    callback: formatRupiahRingkas
                                }
                            }
                        },

                        elements: {
                            line: {
                                borderCapStyle: "round",
                                borderJoinStyle: "round"
                            }
                        }
                    }
                }
            );

            root.dataset.chartInitialized = "true";

            console.log("Dashboard keuangan berhasil diinisialisasi.");

        } catch (error) {
            console.error("Gagal menampilkan grafik keuangan:", error);
            if (emptyState) emptyState.hidden = false;
        }
    }

    // Initial page load
    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initDashboardBendahara,
            { once: true }
        );
    } else {
        initDashboardBendahara();
    }

    // SPA navigation
    document.addEventListener(
        "spa:page-loaded",
        initDashboardBendahara
    );

})();
