
(function () {
    function initStudentDetail() {
        const root = document.querySelector('.student-detail');
        if (!root || root.dataset.sdInitialized === 'true') return;

        root.dataset.sdInitialized = 'true';

        const tabs = root.querySelectorAll('.sd-tab');
        const panels = root.querySelectorAll('.sd-tab-panel');

        tabs.forEach(tab => {
            tab.addEventListener('click', function () {
                const target = this.dataset.tab;

                tabs.forEach(item => item.classList.remove('active'));
                panels.forEach(panel => panel.classList.remove('active'));

                this.classList.add('active');

                const selectedPanel = root.querySelector('#sd-tab-' + target);
                if (selectedPanel) {
                    selectedPanel.classList.remove('active');
                    void selectedPanel.offsetWidth;
                    selectedPanel.classList.add('active');
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initStudentDetail);
    } else {
        initStudentDetail();
    }
})();
