document.addEventListener("DOMContentLoaded", function () {

    /* ── Tabs ─────────────────────────────────────────────
       Ngoài việc đổi panel, còn set --tab-i trên track để
       marker trượt tới đúng ô, và cập nhật aria-selected. */
    const tabList = document.querySelector(".bk-tabs");
    const tabs = Array.from(document.querySelectorAll(".bk-tab"));
    const panels = Array.from(document.querySelectorAll(".bk-panel"));

    tabs.forEach((tab, index) => {
        tab.addEventListener("click", function () {
            const targetPanel = document.getElementById(tab.dataset.tabTarget);

            tabs.forEach((item) => {
                item.classList.remove("bk-tab--active");
                item.setAttribute("aria-selected", "false");
            });
            panels.forEach((panel) => panel.classList.remove("bk-panel--active"));

            tab.classList.add("bk-tab--active");
            tab.setAttribute("aria-selected", "true");
            if (tabList) tabList.style.setProperty("--tab-i", index);

            if (targetPanel) targetPanel.classList.add("bk-panel--active");
        });
    });


    /* ── Cancel confirm modal ─────────────────────────────
       Dữ liệu lấy thẳng từ data-* trên form thay vì dò DOM
       của card. Bản cũ đọc `.detail-label`, class đã bị bỏ
       khỏi template nên querySelector trả null và cả luồng
       huỷ lịch chết ở đó. */
    const cancelModal = document.getElementById("cancel-modal");
    if (!cancelModal) return;

    const fieldService = document.getElementById("cancel-modal-service");
    const fieldDate = document.getElementById("cancel-modal-stylist");
    const fieldWhen = document.getElementById("cancel-modal-date");
    const reasonSelect = document.getElementById("cancel-modal-reason");
    let pendingForm = null;

    function openCancelModal(form) {
        fieldService.textContent = form.dataset.service || "";
        fieldWhen.textContent = form.dataset.when || "";
        fieldDate.textContent = form.dataset.staff || "";
        reasonSelect.value = "";

        pendingForm = form;
        cancelModal.classList.add("is-open");
    }

    function closeCancelModal() {
        cancelModal.classList.remove("is-open");
        pendingForm = null;
    }

    document.querySelectorAll(".bk-cancel-form").forEach((form) => {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            openCancelModal(this);
        });
    });

    document.getElementById("cancel-modal-close").addEventListener("click", closeCancelModal);
    document.getElementById("cancel-modal-keep").addEventListener("click", closeCancelModal);

    document.getElementById("cancel-modal-confirm").addEventListener("click", () => {
        const form = pendingForm;
        closeCancelModal();
        if (!form) return;

        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "cancellation_reason";
        input.value = reasonSelect.value;
        form.appendChild(input);
        form.submit();
    });

    cancelModal.addEventListener("click", function (e) {
        if (e.target === this) closeCancelModal();
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && cancelModal.classList.contains("is-open")) {
            closeCancelModal();
        }
    });
});
