document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("registerForm");
    const full_nameEl = document.getElementById("full_name");
    const phoneEl = document.getElementById("phone");
    const emailEl = document.getElementById("email");
    const passwordEl = document.getElementById("password");
    const registerBtn = document.getElementById("registerBtn");
    const messageEl = document.getElementById("message");

    function showMessage(text, type = "info") {
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
    }

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const fullName = full_nameEl.value.trim();
        const phone = phoneEl.value.trim();
        const email = emailEl.value.trim();
        const password = passwordEl.value.trim();

        if (!fullName || !phone || !email || !password) {
            showMessage("Please enter required information!", "error");
            return;
        }

        registerBtn.disabled = true;
        registerBtn.textContent = "Registering...";

        try {
            const response = await fetch("/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    full_name: fullName,
                    phone: phone,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();
            console.log("REGISTER RESPONSE DATA:", data);

            if (response.ok && data.success) {
                showMessage(data.message || "Redirecting...", "success");

                setTimeout(() => {
                    console.log("REDIRECT URL:", data.redirect_url);
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                showMessage(data.message || "Something went wrong :(", "error");
            }
        } catch (error) {
            console.error("Register error:", error);
            showMessage("Server error. Please try again later!", "error");
        } finally {
            registerBtn.disabled = false;
            registerBtn.textContent = "Register";
        }
    });
});