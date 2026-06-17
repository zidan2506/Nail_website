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

    // Cancel confirm modal
    const cancelModal = document.getElementById("cancel-modal");
    let pendingForm = null;

    function openCancelModal(form) {
        const card = form.closest(".appointment-card");

        document.getElementById("cancel-modal-service").textContent =
            card.querySelector(".appointment-card__title").textContent.trim();

        let dateTime = "", stylist = "";
        card.querySelectorAll(".appointment-card__detail").forEach(row => {
            const label = row.querySelector(".detail-label").textContent.trim();
            const value = row.querySelector(".detail-value").textContent.trim();
            if (label === "Date:") dateTime = value;
            if (label === "Stylist:") stylist = value;
        });

        document.getElementById("cancel-modal-date").textContent = dateTime;
        document.getElementById("cancel-modal-stylist").textContent = stylist;
        document.getElementById("cancel-modal-reason").value = "";

        pendingForm = form;
        cancelModal.classList.add("is-open");
    }

    function closeCancelModal() {
        cancelModal.classList.remove("is-open");
        pendingForm = null;
    }

    document.querySelectorAll(".inline-form").forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            openCancelModal(this);
        });
    });

    document.getElementById("cancel-modal-close").addEventListener("click", closeCancelModal);
    document.getElementById("cancel-modal-keep").addEventListener("click", closeCancelModal);

    document.getElementById("cancel-modal-confirm").addEventListener("click", () => {
        const form = pendingForm;
        closeCancelModal();
        if (form) {
            const reason = document.getElementById("cancel-modal-reason").value;
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "cancellation_reason";
            input.value = reason;
            form.appendChild(input);
            form.submit();
        }
    });

    cancelModal.addEventListener("click", function(e) {
        if (e.target === this) closeCancelModal();
    });
})

