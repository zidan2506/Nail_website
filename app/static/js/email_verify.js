document.addEventListener("DOMContentLoaded", () => {
    const verifyForm = document.getElementById("verifyForm");
    const codeInput = document.getElementById("verification_code");
    const messageEl = document.getElementById("message");
    const verifyBtn = document.getElementById("verifyBtn");
    const resendBtn = document.getElementById("resendBtn");
    const changeBtn = document.getElementById("changeBtn")
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    function showMessage(text, type = "info") {
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
    }

    verifyForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const verificationCode = codeInput.value.trim();

        if (!verificationCode) {
            showMessage("Please enter the verification code.", "error");
            return;
        }

        verifyBtn.disabled = true;
        verifyBtn.textContent = "Verifying...";

        try {
            const response = await fetch("/verify-email", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    verification_code: verificationCode
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showMessage("Verification successful. Redirecting...", "success");

                setTimeout(() => {
                    window.location.href = data.redirect_url || "/success";
                }, 1000);
            } else {
                showMessage(data.message || "Invalid verification code. Please try again.", "error");
                if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url || "/home";
                }, 1000);
                }
            }
        } catch (error) {
            showMessage("Server error. Please try again later.", "error");
            console.error("Verification error:", error);
        } finally {
            verifyBtn.disabled = false;
            verifyBtn.textContent = "Verify Code";
        }
    });

    resendBtn.addEventListener("click", async () => {
        resendBtn.disabled = true;
        resendBtn.textContent = "Sending...";

        try {
            const response = await fetch("/resend-verification-code", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showMessage(
                    data.message || "A new verification code has been sent to your email.",
                    "info"
                );
            } else {
                showMessage(
                    data.message || "Could not resend code. Please try again.",
                    "error"
                );
            }
        } catch (error) {
            showMessage("Server error. Please try again later.", "error");
            console.error("Resend error:", error);
        } finally {
            resendBtn.disabled = false;
            resendBtn.textContent = "Resend Code";
        }
    });

    //tạm thời ẩn nút change booking tại trang verify đang solve cho nhiều case service khác
    // changeBtn.addEventListener("click", async()=>{
    //     changeBtn.textContent = "Loading...";

    //     try {
    //         const response = await fetch("/change-booking", {
    //             method: "POST"
    //         });
    //         const data = await response.json();

    //         if (!response.ok) {
    //             alert(data.message || "Something went wrong")
    //         };

    //         window.location.href = data.redirect_url;

    //     } catch (error){
    //         console.error(error);
    //         alert("Network error. Please try again!");
    //     }
    // })
});