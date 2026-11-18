
(function () {
    "use strict";

    function initStudentDetail() {
        const root = document.querySelector(".student-detail");

        if (!root) return;

        // Ambil elemen tab dan panel dari root yang sedang aktif.
        const tabs = root.querySelectorAll(".sd-tab");
        const panels = root.querySelectorAll(".sd-tab-panel");

        if (!tabs.length || !panels.length) return;

        // Hindari memasang event listener berulang.
        if (root.dataset.sdInitialized === "true") return;

        root.dataset.sdInitialized = "true";

        tabs.forEach(tab => {
            tab.addEventListener("click", function (event) {
                event.preventDefault();

                const target = this.dataset.tab;

                tabs.forEach(item => {
                    item.classList.remove("active");
                });

                panels.forEach(panel => {
                    panel.classList.remove("active");
                });

                this.classList.add("active");

                const selectedPanel = root.querySelector(
                    "#sd-tab-" + target
                );

                if (selectedPanel) {
                    selectedPanel.classList.remove("active");

                    void selectedPanel.offsetWidth;

                    selectedPanel.classList.add("active");
                }
            });
        });

        console.log("[STUDENT DETAIL] Tab berhasil diinisialisasi.");
    }

    // ==========================================
    // INITIAL PAGE LOAD
    // ==========================================

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initStudentDetail,
            { once: true }
        );
    } else {
        initStudentDetail();
    }

    // ==========================================
    // SPA PAGE LOADED
    // ==========================================

    document.addEventListener(
        "spa:page-loaded",
        function () {
            requestAnimationFrame(() => {
                initStudentDetail();
            });
        }
    );

})();
