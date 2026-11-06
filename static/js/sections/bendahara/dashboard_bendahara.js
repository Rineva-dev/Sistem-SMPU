(() => {
    "use strict";

    const MODULE_KEY = "__hamzanwadiFinanceEmeraldV3";

    // Jika script dijalankan lagi oleh SPA, gunakan modul yang sama.
    if (window[MODULE_KEY]) {
        window[MODULE_KEY].init();
        return;
    }

    const CHART_URL =
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js";

    const motionPreference = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    );

    const currency = new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0
    });

    let active = null;
    let chartLibraryPromise = null;
    let paused = false;

    try {
        paused =
            sessionStorage.getItem("bdx-motion-paused") === "true";
    } catch (_) {}

    // ==========================================
    // CHART LIBRARY
    // ==========================================

    function loadChartLibrary() {
        if (typeof window.Chart === "function") {
            return Promise.resolve(window.Chart);
        }

        if (chartLibraryPromise) {
            return chartLibraryPromise;
        }

        chartLibraryPromise = new Promise((resolve, reject) => {
            const script = document.createElement("script");

            script.src = CHART_URL;
            script.async = true;
            script.dataset.bdxChartLoader = "true";

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
                finish(
                    typeof window.Chart === "function"
                        ? null
                        : new Error("Chart.js tidak tersedia.")
                );
            };

            script.onerror = () => {
                finish(
                    new Error(
                        "Chart.js gagal dimuat. Periksa koneksi atau CSP."
                    )
                );
            };

            document.head.appendChild(script);
        }).catch(error => {
            chartLibraryPromise = null;
            throw error;
        });

        return chartLibraryPromise;
    }

    // ==========================================
    // HELPERS
    // ==========================================

    function isActive(state) {
        return (
            active === state &&
            state.root.isConnected
        );
    }

    function motionDisabled() {
        return paused || motionPreference.matches;
    }

    function chartAnimation(duration = 550) {
        return motionDisabled()
            ? false
            : {
                duration,
                easing: "easeOutQuart"
            };
    }

    function compactCurrency(value) {
        const number = Number(value);
        const absolute = Math.abs(number);

        if (absolute >= 1e9) {
            return "Rp " +
                (number / 1e9).toLocaleString(
                    "id-ID",
                    { maximumFractionDigits: 1 }
                ) +
                " M";
        }

        if (absolute >= 1e6) {
            return "Rp " +
                (number / 1e6).toLocaleString(
                    "id-ID",
                    { maximumFractionDigits: 1 }
                ) +
                " jt";
        }

        if (absolute >= 1e3) {
            return "Rp " +
                (number / 1e3).toLocaleString(
                    "id-ID",
                    { maximumFractionDigits: 0 }
                ) +
                " rb";
        }

        return currency.format(number);
    }

    // ==========================================
    // DATA VALIDATION
    // ==========================================

    function readData(root) {
        const element = root.querySelector("#bdxKeuanganData");

        if (!element) {
            throw new Error("Elemen data grafik tidak ditemukan.");
        }

        const source = JSON.parse(element.textContent);

        if (!Array.isArray(source.labels)) {
            throw new Error("Label bulan harus berupa array.");
        }

        const expenseReady =
            root.dataset.expenseReady === "true";

        function numericArray(values) {
            if (
                !Array.isArray(values) ||
                values.length !== source.labels.length
            ) {
                throw new Error(
                    "Jumlah label dan nominal grafik tidak sama."
                );
            }

            return values.map(value => {
                if (
                    !["number", "string"].includes(typeof value) ||
                    String(value).trim() === ""
                ) {
                    throw new Error(
                        "Nominal grafik harus angka mentah."
                    );
                }

                const number = Number(value);

                if (!Number.isFinite(number)) {
                    throw new Error(
                        "Nominal grafik tidak valid."
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

    function selectedData(state) {
        // Baca ulang agar tombol Coba lagi juga
        // dapat memproses data yang sudah diperbaiki.
        const data = readData(state.root);

        return {
            labels: data.labels.slice(-state.range),
            masuk: data.masuk.slice(-state.range),
            keluar: data.keluar.slice(-state.range),
            expenseReady: data.expenseReady
        };
    }

    // ==========================================
    // SUMMARY / TABLE
    // ==========================================

    function updateSummary(state, data) {
        const total = data.masuk.reduce(
            (sum, value) => sum + value,
            0
        );

        state.total.textContent = currency.format(total);

        const fragment = document.createDocumentFragment();

        data.labels.forEach((label, index) => {
            const row = document.createElement("tr");

            const values = [
                label,
                currency.format(data.masuk[index])
            ];

            if (data.expenseReady) {
                values.push(
                    currency.format(data.keluar[index])
                );
            }

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            fragment.appendChild(row);
        });

        state.dataTable.replaceChildren(fragment);
    }

    // ==========================================
    // CHART STATES
    // ==========================================

    function showChartState(state, title, detail, retry = false) {
        state.canvas.hidden = true;
        state.stateBox.hidden = false;

        state.stateTitle.textContent = title;
        state.stateDetail.textContent = detail;
        state.retry.hidden = !retry;
    }

    function destroyChart(state) {
        const instance = state.chart;
        state.chart = null;

        if (instance) {
            instance.destroy();
        }

        // Bersihkan instance parsial jika constructor gagal.
        const partial =
            window.Chart?.getChart?.(state.canvas);

        if (partial) {
            partial.destroy();
        }

        delete state.canvas._keuanganChart;
    }

    // ==========================================
    // DATASET
    // ==========================================

    function createDataset(label, values, topColor, bottomColor) {
        return {
            label,
            data: values,

            borderRadius: 6,
            borderSkipped: false,
            maxBarThickness: 42,
            categoryPercentage: 0.65,
            barPercentage: 0.8,

            backgroundColor(context) {
                const chart = context.chart;
                const area = chart.chartArea;

                if (!area) return bottomColor;

                const gradient = chart.ctx.createLinearGradient(
                    0,
                    area.top,
                    0,
                    area.bottom
                );

                gradient.addColorStop(0, topColor);
                gradient.addColorStop(1, bottomColor);

                return gradient;
            },

            hoverBackgroundColor: bottomColor
        };
    }

    function buildDatasets(data) {
        const result = [
            createDataset(
                "Pemasukan",
                data.masuk,
                "#47a17b",
                "#1d7453"
            )
        ];

        if (data.expenseReady) {
            result.push(
                createDataset(
                    "Pengeluaran",
                    data.keluar,
                    "#ddc795",
                    "#b49a64"
                )
            );
        }

        return result;
    }

    // ==========================================
    // RENDER CHART
    // ==========================================

    async function renderChart(state) {
        if (!isActive(state)) return;

        const token = ++state.renderToken;

        try {
            const data = selectedData(state);

            updateSummary(state, data);

            const hasData =
                data.labels.length > 0 &&
                [...data.masuk, ...data.keluar].some(
                    value => value !== 0
                );

            if (!hasData) {
                destroyChart(state);

                showChartState(
                    state,
                    "Belum ada transaksi pada periode ini",
                    "Pilih periode lain atau periksa riwayat pembayaran."
                );

                return;
            }

            // Perbarui instance yang sudah ada agar transisi
            // 3/6 bulan lebih halus tanpa membangun ulang canvas.
            if (state.chart) {
                state.chart.stop();

                state.chart.data.labels = data.labels;

                state.chart.data.datasets.forEach(
                    (dataset, index) => {
                        dataset.data = index === 0
                            ? data.masuk
                            : data.keluar;
                    }
                );

                state.chart.options.animation = chartAnimation(450);

                state.canvas.hidden = false;
                state.stateBox.hidden = true;

                state.chart.update();
                return;
            }

            showChartState(
                state,
                "Menyiapkan grafik",
                "Memuat ringkasan transaksi…"
            );

            const Chart = await loadChartLibrary();

            // Abaikan hasil lama jika periode berubah
            // atau halaman sudah ditinggalkan.
            if (
                !isActive(state) ||
                token !== state.renderToken
            ) {
                return;
            }

            state.canvas.hidden = false;
            state.stateBox.hidden = true;

            state.chart = new Chart(
                state.canvas.getContext("2d"),
                {
                    type: "bar",

                    data: {
                        labels: data.labels,
                        datasets: buildDatasets(data)
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        resizeDelay: 100,
                        animation: chartAnimation(700),

                        interaction: {
                            mode: "index",
                            intersect: false
                        },

                        layout: {
                            padding: {
                                top: 10,
                                right: 8
                            }
                        },

                        plugins: {
                            legend: {
                                display: false
                            },

                            tooltip: {
                                backgroundColor: "#173e30",
                                titleColor: "#dce9dc",
                                bodyColor: "#ffffff",
                                borderColor: "#ffffff15",
                                borderWidth: 1,
                                padding: 13,
                                cornerRadius: 10,
                                displayColors: true,

                                callbacks: {
                                    label(context) {
                                        return context.dataset.label +
                                            ": " +
                                            currency.format(
                                                context.parsed.y
                                            );
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
                                    color: "#7b8c79",
                                    maxRotation: 0,
                                    autoSkip: true,
                                    font: {
                                        size: 11
                                    }
                                }
                            },

                            y: {
                                beginAtZero: true,

                                border: {
                                    display: false
                                },

                                grid: {
                                    color: "#edf2e9"
                                },

                                ticks: {
                                    color: "#7b8c79",
                                    maxTicksLimit: 5,
                                    font: {
                                        size: 10
                                    },
                                    callback: compactCurrency
                                }
                            }
                        }
                    }
                }
            );

            state.canvas._keuanganChart = state.chart;

        } catch (error) {
            if (
                !isActive(state) ||
                token !== state.renderToken
            ) {
                return;
            }

            destroyChart(state);

            showChartState(
                state,
                "Grafik belum bisa ditampilkan",
                "Periksa koneksi atau data grafik, lalu coba lagi.",
                true
            );

            console.error(
                "[Hamzanwadi Finance]",
                error
            );
        }
    }

    // ==========================================
    // SEARCH TRANSACTIONS
    // ==========================================

    function filterTransactions(state) {
        const query = state.search.value
            .trim()
            .toLocaleLowerCase("id-ID");

        let count = 0;

        state.rows.forEach(item => {
            const matches =
                query === "" ||
                item.searchText.includes(query);

            item.element.hidden = !matches;

            if (matches) count++;
        });

        state.noResults.hidden = !(
            state.rows.length > 0 &&
            count === 0
        );

        state.count.textContent = query
            ? `${count} dari ${state.rows.length} transaksi ditampilkan`
            : `${state.rows.length} transaksi ditampilkan`;
    }

    // ==========================================
    // MOTION
    // ==========================================

    function applyMotion() {
        if (!active) return;

        active.root.classList.toggle(
            "bdx-paused",
            motionDisabled()
        );

        const label = paused
            ? "Aktifkan animasi"
            : "Jeda animasi";

        active.motionButton.setAttribute(
            "aria-pressed",
            String(paused)
        );

        active.motionButton.setAttribute(
            "aria-label",
            label
        );

        active.motionButton.title = label;

        const icon = active.motionButton.querySelector("i");

        icon.classList.toggle("fa-play", paused);
        icon.classList.toggle("fa-pause", !paused);

        if (active.chart) {
            active.chart.stop();
            active.chart.options.animation = chartAnimation(450);
            active.chart.update("none");
        }
    }

    function applyVisibility() {
        if (!active) return;

        active.root.classList.toggle(
            "bdx-background",
            document.hidden
        );
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    function cleanup() {
        if (!active) return;

        const previous = active;
        active = null;

        previous.renderToken++;
        previous.events.abort();

        cancelAnimationFrame(previous.searchFrame);

        destroyChart(previous);
    }

    // ==========================================
    // INITIALIZE
    // ==========================================

    function init() {
        const root = document.querySelector(".bdx");

        if (
            active?.root === root &&
            root?.isConnected
        ) {
            return;
        }

        cleanup();

        if (!root) return;

        const selectors = {
            canvas: "#bdxKeuanganChart",
            stateBox: "[data-bdx-chart-state]",
            stateTitle: "[data-bdx-state-title]",
            stateDetail: "[data-bdx-state-detail]",
            retry: "[data-bdx-retry]",
            total: "[data-bdx-total]",
            dataTable: "[data-bdx-data-table]",
            search: "[data-bdx-search]",
            noResults: "[data-bdx-no-results]",
            count: "[data-bdx-count]",
            motionButton: "[data-bdx-motion]"
        };

        const elements = {};

        for (const [key, selector] of Object.entries(selectors)) {
            elements[key] = root.querySelector(selector);

            if (!elements[key]) {
                console.error(
                    "[Hamzanwadi Finance] Elemen tidak ditemukan:",
                    selector
                );
                return;
            }
        }

        const state = {
            root,
            ...elements,

            range: 6,
            chart: null,
            renderToken: 0,
            searchFrame: 0,
            events: new AbortController(),

            rows: Array.from(
                root.querySelectorAll("[data-bdx-transaction]")
            ).map(element => ({
                element,
                searchText: element.textContent.toLocaleLowerCase("id-ID")
            }))
        };

        active = state;

        const options = {
            signal: state.events.signal
        };

        const rangeButtons = Array.from(
            root.querySelectorAll("[data-bdx-range]")
        );

        rangeButtons.forEach(button => {
            button.addEventListener("click", () => {
                const range = Number(button.dataset.bdxRange);

                if (
                    ![3, 6].includes(range) ||
                    range === state.range
                ) {
                    return;
                }

                state.range = range;

                rangeButtons.forEach(item => {
                    item.setAttribute(
                        "aria-pressed",
                        String(
                            Number(item.dataset.bdxRange) === range
                        )
                    );
                });

                renderChart(state);
            }, options);
        });

        state.retry.addEventListener("click", () => {
            renderChart(state);
        }, options);

        state.search.addEventListener("input", () => {
            cancelAnimationFrame(state.searchFrame);

            state.searchFrame = requestAnimationFrame(() => {
                if (isActive(state)) {
                    filterTransactions(state);
                }
            });
        }, options);

        state.motionButton.addEventListener("click", () => {
            paused = !paused;

            try {
                sessionStorage.setItem(
                    "bdx-motion-paused",
                    String(paused)
                );
            } catch (_) {}

            applyMotion();
        }, options);

        applyMotion();
        applyVisibility();
        filterTransactions(state);
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

    document.addEventListener(
        "visibilitychange",
        applyVisibility
    );

    motionPreference.addEventListener(
        "change",
        applyMotion
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