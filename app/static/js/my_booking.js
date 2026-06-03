document.addEventListener("DOMContentLoaded", function() {
    // tabs filter solve
    const tabs = document.querySelectorAll(".appointment-tab")
    const panels = document.querySelectorAll(".appointment-tab-panel")

    tabs.forEach((tab) => {
        tab.addEventListener("click", function () {
            const targetId = tab.dataset.tabTarget;
            const targetPanel = document.getElementById(targetId);

            tabs.forEach((item) => {
                item.classList.remove("appointment-tab--active");
            });
            panels.forEach((panel)=> {
                panel.classList.remove("appointment-tab-panel--active");
            });

            tab.classList.add("appointment-tab--active");
           
            if (targetPanel) {
                targetPanel.classList.add("appointment-tab-panel--active")
            }
        })
    })
})

