
/* ==========================================================
   DATA KELAS — DIRECTORY INTERACTION
   SPA COMPATIBLE
========================================================== */

(() => {
    "use strict";

    function initDataKelas() {
        const page = document.getElementById("kelasManagementPage");

        if (!page || page.dataset.initialized === "true") return;

        page.dataset.initialized = "true";

        const input = page.querySelector("#cariKelas");
        const rows = Array.from(page.querySelectorAll(".kd-row"));
        const empty = page.querySelector("#kelasSearchEmpty");
        const visibleCount = page.querySelector("#kdVisibleCount");

        if (!input) return;

        function search() {
            const keyword = input.value.trim().toLocaleLowerCase("id");
            let count = 0;

            rows.forEach(row => {
                const content = [
                    row.dataset.kelas,
                    row.dataset.jenjang,
                    row.dataset.wali,
                    row.textContent
                ].join(" ").toLocaleLowerCase("id");

                const match = content.includes(keyword);

                row.hidden = !match;

                if (match) count++;
            });

            if (empty) {
                empty.hidden = count > 0 || keyword === "";
            }

            if (visibleCount) {
                visibleCount.textContent = count;
            }
        }

        input.addEventListener("input", search);

        // Shortcut pencarian dengan tombol /
        page.addEventListener("keydown", event => {
            if (
                event.key === "/" &&
                !["INPUT", "TEXTAREA", "SELECT"].includes(
                    document.activeElement.tagName
                )
            ) {
                event.preventDefault();
                input.focus();
            }

            if (event.key === "Escape" && document.activeElement === input) {
                input.value = "";
                search();
                input.blur();
            }
        });

        input.value = "";
        search();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initDataKelas, { once: true });
    } else {
        initDataKelas();
    }

    document.addEventListener("spa:page-loaded", initDataKelas);

})();
