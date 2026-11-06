(() => {
    "use strict";

    // Mencegah listener global terpasang berulang saat SPA.
    const MODULE_KEY = "__emeraldFinanceDashboardV2";

    if (window[MODULE_KEY]) {
        window[MODULE_KEY].init();
        return;
    }

    const CHART_URL =
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js";

    const ROOT_SELECTOR = ".dashboard-bendahara-page";

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    );

    const rupiah = new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0
    });

    let current = null;
    let chartPromise = null;
    let motionPaused = false;

    try {
        motionPaused =
            sessionStorage.getItem("fin-motion-paused") === "true";
    } catch (_) {
        // Dashboard tetap berjalan jika sessionStorage tidak tersedia.
    }

    // ==========================================
    // LOAD CHART.JS
    // ==========================================

    function loadChartJs() {
        if (typeof window.Chart === "function") {
            return Promise.resolve(window.Chart);
        }

        if (chartPromise) {
            return chartPromise;
        }

        chartPromise = new Promise((resolve, reject) => {
            const script = document.createElement("script");

            script.src = CHART_URL;
            script.async = true;
            script.dataset.finChartLoader = "true";

            let settled = false;

            function finish(error) {
                if (settled) return;
                settled = true;

                clearTimeout(timeout);

                script.onload = null;
                script.onerror = null;

                if (error) {
                    script.remove();
                    reject(error);
                    return;
                }

                resolve(window.Chart);
            }

            const timeout = setTimeout(() => {
                finish(
                    new Error("Waktu memuat Chart.js habis.")
                );
            }, 15000);

            script.onload = () => {
                if (typeof window.Chart !== "function") {
                    finish(
                        new Error("Chart.js tidak tersedia.")
                    );
                    return;
                }

                finish();
            };

            script.onerror = () => {
                finish(
                    new Error(
                        "Chart.js gagal dimuat. Periksa jaringan atau CSP."
                    )
                );
            };

            document.head.appendChild(script);
        }).catch(error => {
            // Izinkan percobaan ulang.
            chartPromise = null;
            throw error;
        });

        return chartPromise;
    }

    // ==========================================
    // UTILITAS
    // ==========================================

    function isCurrent(state) {
        return (
            current === state &&
            state.root.isConnected
        );
    }

    function formatRupiahRingkas(value) {
        const nominal = Number(value);
        const absolute = Math.abs(nominal);

        if (absolute >= 1_000_000_000) {
            return "Rp " +
                (nominal / 1_000_000_000).toLocaleString(
                    "id-ID",
                    { maximumFractionDigits: 1 }
                ) +
                " M";
        }

        if (absolute >= 1_000_000) {
            return "Rp " +
                (nominal / 1_000_000).toLocaleString(
                    "id-ID",
                    { maximumFractionDigits: 1 }
                ) +
                " jt";
        }

        if (absolute >= 1_000) {
            return "Rp " +
                (nominal / 1_000).toLocaleString(
                    "id-ID",
                    { maximumFractionDigits: 0 }
                ) +
                " rb";
        }

        return rupiah.format(nominal);
    }

    function showState(state, title, detail, allowRetry = false) {
        state.canvas.hidden = true;
        state.stateBox.hidden = false;

        state.stateBox.querySelector(
            "[data-state-title]"
        ).textContent = title;

        state.stateBox.querySelector(
            "[data-state-detail]"
        ).textContent = detail;

        state.retryButton.hidden = !allowRetry;
    }

    // ==========================================
    // VALIDASI DATA BACKEND
    // ==========================================

    function readData(root) {
        const element = root.querySelector("#dbKeuanganData");

        if (!element) {
            throw new Error("Elemen data grafik tidak ditemukan.");
        }

        const source = JSON.parse(element.textContent);

        if (
            !Array.isArray(source.labels) ||
            !Array.isArray(source.masuk)
        ) {
            throw new Error("Format data grafik tidak valid.");
        }

        const expenseReady =
            root.dataset.expenseReady === "true";

        function numericArray(values) {
            if (
                !Array.isArray(values) ||
                values.length !== source.labels.length
            ) {
                throw new Error(
                    "Jumlah bulan dan nilai grafik tidak sama."
                );
            }

            return values.map(value => {
                if (
                    (
                        typeof value !== "number" &&
                        typeof value !== "string"
                    ) ||
                    String(value).trim() === ""
                ) {
                    throw new Error(
                        "Nominal grafik harus berupa angka mentah."
                    );
                }

                const number = Number(value);

                if (!Number.isFinite(number)) {
                    throw new Error(
                        "Nominal grafik tidak valid: " + value
                    );
                }

                return number;
            });
        }

        return {
            labels: source.labels.map(String),
            masuk: numericArray(source.masuk),
            keluar: expenseReady
                ? numericArray(source.keluar)
                : [],
            expenseReady
        };
    }

    // ==========================================
    // RINGKASAN DAN TABEL
    // ==========================================

    function updateSummaryAndTable(state, data) {
        const totalElement = state.root.querySelector(
            "[data-fin-total]"
        );

        const tableBody = state.root.querySelector(
            "[data-fin-table]"
        );

        const totalMasuk = data.masuk.reduce(
            (total, nominal) => total + nominal,
            0
        );

        totalElement.textContent = rupiah.format(totalMasuk);
        tableBody.replaceChildren();

        data.labels.forEach((label, index) => {
            const row = document.createElement("tr");

            const values = [
                label,
                rupiah.format(data.masuk[index])
            ];

            if (data.expenseReady) {
                values.push(
                    rupiah.format(data.keluar[index])
                );
            }

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            tableBody.appendChild(row);
        });
    }

    // ==========================================
    // DATASET GRAFIK
    // ==========================================

    function createDataset(label, values, color, fillColor) {
        return {
            label,
            data: values,

            borderColor: color,
            borderWidth: 2.5,

            pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: color,
            pointBorderColor: "#ffffff",
            pointBorderWidth: 2,

            fill: true,

            // Garis lurus tidak menghasilkan lekukan
            // yang seolah turun di bawah nol antarbulan.
            tension: 0,

            backgroundColor(context) {
                const chart = context.chart;
                const area = chart.chartArea;

                if (!area) {
                    return fillColor;
                }

                const gradient = chart.ctx.createLinearGradient(
                    0,
                    area.top,
                    0,
                    area.bottom
                );

                gradient.addColorStop(0, fillColor);
                gradient.addColorStop(
                    1,
                    "rgba(255,255,255,0)"
                );

                return gradient;
            }
        };
    }

    // ==========================================
    // RENDER GRAFIK
    // ==========================================

    async function renderChart(state) {
        if (
            state.loading ||
            state.chart ||
            !isCurrent(state)
        ) {
            return;
        }

        state.loading = true;

        try {
            const data = readData(state.root);

            updateSummaryAndTable(state, data);

            const hasData =
                data.labels.length > 0 &&
                [...data.masuk, ...data.keluar].some(
                    value => value !== 0
                );

            if (!hasData) {
                showState(
                    state,
                    "Belum ada data keuangan",
                    "Tidak ada nominal transaksi pada periode enam bulan ini."
                );

                return;
            }

            showState(
                state,
                "Menyiapkan grafik",
                "Memuat tampilan arus keuangan…"
            );

            const Chart = await loadChartJs();

            // Pengguna mungkin sudah pindah halaman
            // ketika CDN selesai dimuat.
            if (!isCurrent(state)) return;

            state.canvas.hidden = false;
            state.stateBox.hidden = true;

            const datasets = [
                createDataset(
                    "Pemasukan",
                    data.masuk,
                    "#079669",
                    "rgba(7,150,105,.22)"
                )
            ];

            if (data.expenseReady) {
                datasets.push(
                    createDataset(
                        "Pengeluaran",
                        data.keluar,
                        "#5688df",
                        "rgba(86,136,223,.16)"
                    )
                );
            }

            state.chart = new Chart(
                state.canvas.getContext("2d"),
                {
                    type: "line",

                    data: {
                        labels: data.labels,
                        datasets
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        animation:
                            reducedMotion.matches || motionPaused
                                ? false
                                : {
                                    duration: 700,
                                    easing: "easeOutQuart"
                                },

                        interaction: {
                            mode: "index",
                            intersect: false
                        },

                        layout: {
                            padding: {
                                top: 10,
                                right: 10
                            }
                        },

                        plugins: {
                            legend: {
                                display: false
                            },

                            tooltip: {
                                backgroundColor: "#123f30",
                                titleColor: "#d9f3e3",
                                bodyColor: "#ffffff",
                                padding: 13,
                                cornerRadius: 10,
                                displayColors: true,

                                callbacks: {
                                    label(context) {
                                        return context.dataset.label +
                                            ": " +
                                            rupiah.format(
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
                                    color: "#62796b",
                                    font: {
                                        size: 11
                                    },
                                    maxRotation: 0,
                                    autoSkip: true
                                }
                            },

                            y: {
                                beginAtZero: true,

                                border: {
                                    display: false
                                },

                                grid: {
                                    color: "#edf2ee"
                                },

                                ticks: {
                                    color: "#62796b",
                                    maxTicksLimit: 5,
                                    font: {
                                        size: 10
                                    },
                                    callback: formatRupiahRingkas
                                }
                            }
                        }
                    }
                }
            );

            // Tetap tersedia untuk pemeriksaan lewat Console.
            state.canvas._keuanganChart = state.chart;

        } catch (error) {
            if (!isCurrent(state)) return;

            if (state.chart) {
                state.chart.destroy();
                state.chart = null;
            }

            // Bersihkan jika constructor sempat
            // mendaftarkan instance sebelum gagal.
            const partialChart =
                window.Chart?.getChart?.(state.canvas);

            if (partialChart) {
                partialChart.destroy();
            }

            delete state.canvas._keuanganChart;

            showState(
                state,
                "Grafik belum bisa ditampilkan",
                "Coba lagi. Jika tetap gagal, periksa data grafik dan koneksi.",
                true
            );

            console.error(
                "[Dashboard Bendahara]",
                error
            );

        } finally {
            state.loading = false;
        }
    }

    // ==========================================
    // PENGATURAN ANIMASI
    // ==========================================

    function applyMotionPreference() {
        if (!current) return;

        const shouldPause =
            motionPaused || reducedMotion.matches;

        current.root.classList.toggle(
            "fin-motion-paused",
            shouldPause
        );

        const button = current.root.querySelector(
            "[data-fin-motion]"
        );

        button.textContent = motionPaused
            ? "Aktifkan animasi"
            : "Jeda animasi";

        button.setAttribute(
            "aria-pressed",
            String(motionPaused)
        );

        if (current.chart) {
            current.chart.stop();

            current.chart.options.animation = shouldPause
                ? false
                : {
                    duration: 700,
                    easing: "easeOutQuart"
                };

            current.chart.update("none");
        }
    }

    // ==========================================
    // CLEANUP SEBELUM PINDAH HALAMAN
    // ==========================================

    function cleanup() {
        if (!current) return;

        const previous = current;
        current = null;

        // Lepaskan listener tombol pada halaman lama.
        previous.events.abort();

        if (previous.chart) {
            previous.chart.destroy();
        }

        delete previous.canvas._keuanganChart;
    }

    // ==========================================
    // INITIALIZE
    // ==========================================

    function init() {
        const root = document.querySelector(ROOT_SELECTOR);

        if (
            current?.root === root &&
            root?.isConnected
        ) {
            return;
        }

        cleanup();

        if (!root) return;

        const canvas = root.querySelector("#keuanganChart");
        const stateBox = root.querySelector("#keuanganChartEmpty");
        const retryButton = root.querySelector("[data-fin-retry]");
        const motionButton = root.querySelector("[data-fin-motion]");

        if (
            !canvas ||
            !stateBox ||
            !retryButton ||
            !motionButton
        ) {
            return;
        }

        const state = {
            root,
            canvas,
            stateBox,
            retryButton,
            chart: null,
            loading: false,
            events: new AbortController()
        };

        current = state;

        retryButton.addEventListener(
            "click",
            () => renderChart(state),
            {
                signal: state.events.signal
            }
        );

        motionButton.addEventListener(
            "click",
            () => {
                motionPaused = !motionPaused;

                try {
                    sessionStorage.setItem(
                        "fin-motion-paused",
                        String(motionPaused)
                    );
                } catch (_) {
                    // Preferensi tetap berlaku untuk halaman aktif.
                }

                applyMotionPreference();
            },
            {
                signal: state.events.signal
            }
        );

        applyMotionPreference();
        renderChart(state);
    }

    window[MODULE_KEY] = {
        init,
        cleanup
    };

    document.addEventListener(
        "spa:before-page-unload",
        cleanup
    );

    document.addEventListener(
        "spa:page-loaded",
        init
    );

    reducedMotion.addEventListener(
        "change",
        applyMotionPreference
    );

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            init,
            { once: true }
        );
    } else {
        init();
    }
})();