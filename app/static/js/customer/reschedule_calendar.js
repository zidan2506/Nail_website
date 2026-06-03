document.addEventListener("DOMContentLoaded", () => {
  const calendarEl = document.getElementById("miniCalendar");
  const prevBtn = document.getElementById("prevCalendarBtn");
  const nextBtn = document.getElementById("nextCalendarBtn");
  const newDateInput = document.getElementById("newDateInput");
  const monthLabel = document.getElementById("calendarMonthLabel");
  const timeSlotGrid = document.getElementById("timeSlotGrid");
  const rescheduleForm = document.getElementById("rescheduleForm");
  const newTimeInput = document.getElementById("newTimeInput");
  const newDatePreview = document.getElementById("newDatePreview");
  const newTimePreview = document.getElementById("newTimePreview");


  const today = parseLocalDate(RESCHEDULE_CONFIG.today);
  const maxDate = parseLocalDate(RESCHEDULE_CONFIG.maxDate);

  let selectedDate = parseLocalDate(RESCHEDULE_CONFIG.selectedDate);
  let currentMonth = new Date(
    today.getFullYear(),
    today.getMonth(),
    1
  );

  console.log(currentMonth)

  newDateInput.value = formatDate(selectedDate);

  updateNewDatePreview(selectedDate);
  updateNewTimePreview(null);
  renderCalendar();
  loadAvailableSlots(formatDate(selectedDate));

  if (rescheduleForm) {
    rescheduleForm.addEventListener("submit", (event) => {
        if (!newDateInput.value || !newTimeInput.value) {
            event.preventDefault();
            alert("Please select a new date and time");
        }
    })
}

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
 
  function updateNewDatePreview(dateObj) {
    if (!newDatePreview) return;

    newDatePreview.textContent = dateObj.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
      
    });
  }
  function updateNewTimePreview(timeLabel) {
    if (!newTimePreview) return;

    newTimePreview.textContent = timeLabel || "Please select a time";

  }
  async function loadAvailableSlots(dateString) {
    timeSlotGrid.innerHTML = `
    <p class="empty-text">Loading available times...</p>
    `;
    try {
        const response = await fetch(
            `${RESCHEDULE_CONFIG.availableSlotUrl}?date=${dateString}`
        );

        if (!response.ok) {
            throw new Error("Failed to load available slots");
        }
        const data = await response.json();
        
        renderTimeSlots(data.slots || []);
    } catch (error) {
        console.error(error);
        timeSlotGrid.innerHTML = `
        <p class="empty-text">Could not load available times.</p>
        `;
    }
  }

  function renderTimeSlots(slots) {
    timeSlotGrid.innerHTML = "";

    if (slots.length === 0) {
        timeSlotGrid.innerHTML = `
        <p class="empty-text">No available time slots for this date.</p>
        `;
        return;
    }

    slots.forEach((slot) => {
        const btn = document.createElement("button");

        btn.type = "button";
        btn.className = "time-slot-btn";
        btn.textContent = slot.label;
        btn.dataset.time = slot.value;

        btn.addEventListener("click", () => {
            document.querySelectorAll(".time-slot-btn").forEach((item) => {
                item.classList.remove("is-selected");
            });

            btn.classList.add("is-selected")

            if (newTimeInput) {
                newTimeInput.value = slot.value;
            }

            updateNewTimePreview(slot.label)
            
            console.log("Selected time:", slot.value);
        });

        timeSlotGrid.appendChild(btn);

    });
  }

  function renderCalendar() {
    calendarEl.innerHTML = "";
    updateMonthLabel();

    const dates = getCalendarGridDates(currentMonth);

    dates.forEach((dateObj) => {
      const btn = document.createElement("button");

      btn.type = "button";
      btn.className = "calendar-day";
      btn.textContent = dateObj.getDate();

      const isOutsideMonth = dateObj.getMonth() !== currentMonth.getMonth();
      const isDisabled = dateObj < today || dateObj > maxDate;
      const isSelected = isSameDate(dateObj, selectedDate);

      if (isOutsideMonth) {
        btn.classList.add("is-muted");
      }

      if (isDisabled) {
        btn.classList.add("is-disabled");
        btn.disabled = true;
      }

      if (isSelected) {
        btn.classList.add("is-selected");
      }

      btn.addEventListener("click", () => {
        selectedDate = new Date(dateObj);
        newDateInput.value = formatDate(selectedDate);

        const newTimeInput = document.getElementById("newTimeInput");
        if (newTimeInput) {
            newTimeInput.value = "";

        }

        updateNewDatePreview(selectedDate);
        updateNewTimePreview(null);

        console.log("Selected date:", newDateInput.value);
        
        renderCalendar();
        loadAvailableSlots(formatDate(selectedDate));
      });


      calendarEl.appendChild(btn);
    });

    updateNavButtons();
  }

  function getCalendarGridDates(monthDate) {
    const year = monthDate.getFullYear();
    const month = monthDate.getMonth();

    const firstDay = new Date(year, month, 1);

    // Convert Sunday-first của JS sang Monday-first.
    const startOffset = (firstDay.getDay() + 6) % 7;

    const gridStart = new Date(firstDay);
    gridStart.setDate(firstDay.getDate() - startOffset);

    const dates = [];

    for (let i = 0; i < 35; i++) {
      const date = new Date(gridStart);
      date.setDate(gridStart.getDate() + i);
      dates.push(date);
    }

    return dates;
  }

  function updateNavButtons() {
    const prevMonth = new Date(
      currentMonth.getFullYear(),
      currentMonth.getMonth() - 1,
      1
    );

    const prevMonthEnd = new Date(
      prevMonth.getFullYear(),
      prevMonth.getMonth() + 1,
      0
    );

    const nextMonth = new Date(
      currentMonth.getFullYear(),
      currentMonth.getMonth() + 1,
      1
    );

    prevBtn.disabled = prevMonthEnd < today;
    nextBtn.disabled = nextMonth > maxDate;
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

  function isSameDate(a, b) {
    return (
      a.getFullYear() === b.getFullYear() &&
      a.getMonth() === b.getMonth() &&
      a.getDate() === b.getDate()
    );
  }
  function updateMonthLabel() {
  monthLabel.textContent = currentMonth.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}
});