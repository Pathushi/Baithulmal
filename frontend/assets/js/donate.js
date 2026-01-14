document.addEventListener("DOMContentLoaded", function () {
    const donationForm = document.getElementById("donationForm");
    const webxpayForm = document.getElementById("webxpayForm");
    const loader = document.getElementById("loader");

    // Helper to get the CSRF token from Django's cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    if (!donationForm) return; 

    donationForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        
        if (loader) loader.style.display = "block";

        const formData = new FormData(donationForm);

        try {
            // FIXED: Using a relative URL so it finds the backend on the server
            const response = await fetch("/payments/create/", {
                method: "POST",
                body: formData,
                headers: {
                    // Required for Django security
                    "X-CSRFToken": getCookie("csrftoken")
                }
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                alert("Error: " + data.error);
                if (loader) loader.style.display = "none";
                return;
            }

            // Populate and submit the hidden WebXPay form
            let finalWebxForm = webxpayForm || document.createElement("form");
            if (!webxpayForm) {
                finalWebxForm.method = "POST";
                finalWebxForm.style.display = "none";
                document.body.appendChild(finalWebxForm);
            }

            finalWebxForm.action = data.payment_url;
            finalWebxForm.innerHTML = ""; 

            for (const key in data.params) {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = key;
                input.value = data.params[key];
                finalWebxForm.appendChild(input);
            }

            finalWebxForm.submit();

        } catch (err) {
            console.error("Payment Error:", err);
            alert("Payment initiation failed: " + err.message);
            if (loader) loader.style.display = "none";
        }
    });
});
