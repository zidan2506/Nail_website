const serviceButtons = document.querySelectorAll('.service-btn');
const staffButtons = document.querySelectorAll('.staff-btn');
const dateButtons = document.querySelectorAll('.date-btn');

const serviceInput = document.getElementById('service_id');
const staffInput = document.getElementById('staff_id');
const bookingDateInput = document.getElementById('booking_date');
const slotInput = document.getElementById('slot');
const timeOptions = document.getElementById("time-options");

function clearActive(buttons) {
    buttons.forEach(btn => btn.classList.remove('active'));
}

//Function to check if user has choosen serivice,staff,date
function checkChoosen(){
    const serviceId = serviceInput.value;
    const staffId = staffInput.value;
    const bookingDate = bookingDateInput.value;

    if (!serviceId || !staffId || !bookingDate) {
        return false;
    }
    return true

}
//Function that send request to backend
async function loadAvailableSlots(serviceId, staffId, bookingDate) {
    timeOptions.innerHTML = "<p>Loading available slots...</p>"
    slotInput.value = "";

    try {
        const response = await fetch(
            `/check-available-slots?service_id=${serviceId}&staff_id=${staffId}&booking_date=${bookingDate}`
        );
        const data = await response.json();

        if (!response.ok) {
            timeOptions.innerHTML = `<p>${data.message || "Failed to load available slots."}</p>`;
            return;
        }
        renderAvailableSlots(data.available_slots);
    } catch (error) {
        timeOptions.innerHTML = "<p>Network error. Please try again. </p>"
        console.error(error);
    }
}
//Render slots
function renderAvailableSlots(slots) {
    timeOptions.innerHTML = "";

    if (!slots || slots.length === 0) {
        timeOptions.innerHTML = "<p>No available slots for this date.</p>";
        return;
    }

    slots.forEach((slot) => {
        const btn = document.createElement("button")
        btn.type = "button";
        btn.className = "option-btn time-btn";
        btn.textContent = slot;
        btn.dataset.slot = slot;

        btn.addEventListener("click", function() {
            document.querySelectorAll(".time-btn").forEach((b) =>{
                b.classList.remove("active");
            });
            btn.classList.add("active")
            slotInput.value = slot;
        });
        timeOptions.appendChild(btn)
    });
}

// Service
serviceButtons.forEach(button => {
    button.addEventListener('click', () => {
        clearActive(serviceButtons);
        button.classList.add('active');
        serviceInput.value = button.dataset.serviceId;
        console.log('service_id =', serviceInput.value);
        
        if (checkChoosen()) {
            loadAvailableSlots(serviceInput.value , staffInput.value, bookingDateInput.value)
        };
    });
});

// Staff
staffButtons.forEach(button => {
    button.addEventListener('click', () => {
        clearActive(staffButtons);
        button.classList.add('active');
        staffInput.value = button.dataset.staffId;
        console.log('staff_id =', staffInput.value);
        if (checkChoosen()) {
            loadAvailableSlots(serviceInput.value , staffInput.value, bookingDateInput.value)
        };
    });
});

// Date
dateButtons.forEach(button => {
    button.addEventListener('click', () => {
        clearActive(dateButtons);
        button.classList.add('active');
        bookingDateInput.value = button.dataset.date;
        console.log('booking_date =', bookingDateInput.value);
        if (checkChoosen()) {
            loadAvailableSlots(serviceInput.value , staffInput.value, bookingDateInput.value)
        };
    });
});

