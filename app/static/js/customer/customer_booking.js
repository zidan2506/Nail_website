document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll(".service-tab");
    const panels = document.querySelectorAll(".service-tab-panel");
    const services = document.querySelectorAll(".service-option");
    const staffs = document.querySelectorAll(".staff-option");
    
    // Input values
    let serviceId = null
    let staffId = 0
    let timeSlot = null

    //Block: Booking Summary
    sumServiceName = document.getElementById("summary-service-name");
    sumServiceDuration = document.getElementById("summary-service-duration");
    sumServicePrice = document.getElementById("summary-service-price");
    sumStaff = document.getElementById("summary-staff");
    sumDate = document.getElementById("summary-date");
    sumTime = document.getElementById("summary-time");
    sumVAT = document.getElementById("summary-vat");
    sumTotal = document.getElementById("summary-total");

    
    // Block: Select Date & Time
    const monthLabel = document.getElementById("calendarMonthLabel")
    const calendarEl = document.getElementById("calendar")
    const timeSlotGridEl = document.getElementById("timeSlotGrid")

    const today = parseLocalDate(CALENDAR_CONFIG.today)
    const maxDate = parseLocalDate(CALENDAR_CONFIG.maxDate)

    const prevBtn = document.getElementById("prevMonth")
    const nextBtn = document.getElementById("nextMonth")

    let selectedDate = null

    let currentMonth = new Date(
        today.getFullYear(),
        today.getMonth(),
        1
    );

    prevBtn.addEventListener("click", () => {
        currentMonth = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() - 1,
            1
        );
        renderCalendar();
    });

    nextBtn.addEventListener("click", () => {
        currentMonth = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() + 1,
            1
        );
        renderCalendar();
    });

    //Block: Your information

    renderCalendar();

    tabs.forEach((tab) => {
        tab.addEventListener("click", function () {
            const targetId = tab.dataset.serviceTabTarget;
            const targetPanel = document.getElementById(targetId);

            tabs.forEach((item) => {
                item.classList.remove("service-tab--active");
            });

            panels.forEach((panel) => {
                panel.classList.remove("service-tab-panel--active");
            });

            tab.classList.add("service-tab--active");

            if (targetPanel) {
                targetPanel.classList.add("service-tab-panel--active");
            }
        });
    });

    // Service
services.forEach(label => {
    label.addEventListener("click", () => {
        const radio = label.querySelector("input[type='radio']");
        serviceId = radio.value

        //take detail datas
        const serviceName = radio.dataset.name;
        const serviceDuration = radio.dataset.duration;
        const servicePrice = parseFloat(radio.dataset.price);
        const servicePoints = parseInt(radio.dataset.points || 0);

        //Update summary
        sumServiceName.textContent = serviceName;
        sumServiceDuration.textContent = `${serviceDuration} minutes`;
        sumServicePrice.textContent = `$${servicePrice.toFixed(2)}`;

        //Update benefit points
        const earnedPoints = Math.floor(servicePoints * CALENDAR_CONFIG.pointsMultiplier);
        const benefitEl = document.getElementById("benefit-points");
        if (benefitEl) benefitEl.textContent = earnedPoints;

        //CAl VAT (25.5%) and total
        const vat = servicePrice* 0.255;
        const total = servicePrice + vat;

        sumTotal.textContent = `$${total.toFixed(2)}`;
        sumVAT.textContent = `$${vat.toFixed(2)}`;

            tryLoadSlots()

        
    })
})
    // Staff
staffs.forEach(label => {
    label.addEventListener("click", () => {
        const radio = label.querySelector("input[type='radio']")
        staffId = radio.value

        console.log("staffId: ", staffId)
        
        //take detail datas
        const staffName = radio.dataset.name

        //update summary
        sumStaff.textContent = `👤 ${staffName}`
            tryLoadSlots()
    })
})


    // Function
      
    function updateMonthLabel() {
  monthLabel.textContent = currentMonth.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}
    function getCalendarGridDates(monthDate) {
        const year = monthDate.getFullYear();
        const month = monthDate.getMonth();

        const firstDay = new Date(year, month, 1);

        const startOffSet = (firstDay.getDay() + 6) % 7;

        const gridStart = new Date(firstDay);
        gridStart.setDate(firstDay.getDate() - startOffSet);

        const dates = [];

        for (let i = 0; i < 35; i++) {

            const date = new Date(
                gridStart.getFullYear(),
                gridStart.getMonth(),
                gridStart.getDate() + i
            );
            dates.push(date);
        }
        return dates;
    }

    function renderCalendar() {
        calendarEl.innerHTML = "";
        updateMonthLabel();

        const dates = getCalendarGridDates(currentMonth);
        
        dates.forEach((dateObj) => {
            const label = document.createElement("label");
            label.className = "date-option";

            const isOtherMonth = dateObj.getMonth() !== currentMonth.getMonth() || dateObj.getFullYear() !== currentMonth.getFullYear();
            const isPast = dateObj < today;
            const isFuture = dateObj > maxDate;

            const isDisabled = isPast || isFuture || isOtherMonth;

            if (isDisabled) {
                label.classList.add("date-option--disabled")
            }
            
            const input = document.createElement("input");
            input.type = "radio";
            input.name = "booking_date";
            input.value = formatDate(dateObj);
            input.className = "option-input";
            input.disabled = isDisabled;

            const datePill = document.createElement("div");
            datePill.className = "date-pill";

            const strong = document.createElement("strong");
            strong.textContent = dateObj.getDate();

            datePill.appendChild(strong);
            label.appendChild(input);
            label.appendChild(datePill);


            label.addEventListener("click", () => {

                if (isDisabled) {
                    return
                }

                const dateStr = formatDate(dateObj);
                selectedDate = parseLocalDate(dateStr);

                //update summary
                const formattedDate = dateObj.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric"
                })

                sumDate.textContent = `📅 ${formattedDate}`

                tryLoadSlots();
            })

            calendarEl.appendChild(label);
        })
    }

    async function loadAvailableSlots(dateString, serviceId, staffId) {
        timeSlotGridEl.innerHTML = `
        <p class="empty-text">Loading available times...</p>
        `;

        try {
            const response = await fetch(
                `${CALENDAR_CONFIG.availableSlotUrl}?booking_date=${dateString}&staff_id=${staffId}&service_id=${serviceId}`
            );

            const data = await response.json();

            if (!response.ok) {
                console.error("msg:", data.message)
                throw new Error(data.message || "Failed to load available slots");
            }
            
            // render time slots run here!
            console.log("slots: ",data.available_slots)

            renderTimeSlots(data.available_slots || []);

        } catch (error) {
            console.error(error);
            timeSlotGridEl.innerHTML = `
            <p class="empty-text">Could not load available times. </p>
            `;
        }
    }

    function tryLoadSlots() {
        if (serviceId === null) {
            timeSlotGridEl.innerHTML = `<p class='empty-text'>Please select service first!</p>`
            return
        }

        if (selectedDate === null) {
            timeSlotGridEl.innerHTML = `<p class='empty-text'>Please select date first!</p>`
            return
        }

        loadAvailableSlots(formatDate(selectedDate), serviceId, staffId);
    }

    function renderTimeSlots(slots) {
        timeSlotGridEl.innerHTML = "";
        timeSlot = null;

        if (!slots || slots.length === 0) {
            timeSlotGridEl.innerHTML = "<p>No available slots for this date.</p>";
            return;
        }

        slots.forEach(slot => {
            const label = document.createElement("label");
            label.className = "time-option"

            const input = document.createElement("input");
            input.type = "radio";
            input.name = "start_time";
            input.value = slot.value;
            input.className = "option-input";

            const span = document.createElement("span");

            span.textContent = slot.label;

            label.appendChild(input);
            label.appendChild(span);

            label.addEventListener("click", () => {
                
                timeSlot = slot
                console.log("choosen time: ", slot.label)

                //update summary
                sumTime.textContent = `🕐 ${slot.label}`
            })
            timeSlotGridEl.appendChild(label)

        })
    }
    
    function parseLocalDate(dateString) {
    const [year, month, day] = dateString.split("-").map(Number);
    return new Date(year, month - 1, day);
  }
    function formatDate(dateObj) {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, "0");
    const day = String(dateObj.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
  }

});