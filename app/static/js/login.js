document.addEventListener("DOMContentLoaded", () =>{
    const loginForm = document.getElementById("login-form")
    const emailInput = document.getElementById("email")
    const passwordInput = document.getElementById("password")
    const loginBtn = document.getElementById("login-btn")
    const messageEl = document.getElementById("message")

    function showMessage(text, type="info") {
        messageEl.textContent = text
        messageEl.className = `message ${type}`
    }

    loginForm.addEventListener("submit", async(e) => {
        e.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if  (!email || !password) {
            showMessage("Please enter email & password", "error");
            return;
        }

        loginBtn.disabled = true;
        loginBtn.textContent = "Login...";

        try {
            const response = await fetch ("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            })
            const data = await response.json()

            if (response.ok && data.success) {
                showMessage(data.message || "Redicrecting...", "success");

                setTimeout(() => {
                    console.log("Redirect URL: ", data.redirect_url);
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                showMessage(data.message || "Something went wrong :(", "error");

            }
        }catch (error) {
                console.error("Login error", error);
                showMessage("Server error. Please try again later", "error")
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = "Login";
        }

    })
})