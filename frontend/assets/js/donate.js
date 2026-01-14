document.addEventListener("DOMContentLoaded", function () {
    const donationForm = document.getElementById("donationForm");
    const webxpayForm = document.getElementById("webxpayForm");
    const loader = document.getElementById("loader");

    if (!donationForm) return; // Prevent errors if on a different page

    donationForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        
        // Show loader (using style because your HTML loader doesn't use 'hidden' class)
        if (loader) loader.style.display = "block";

        const formData = new FormData(donationForm);

        try {
            // 1. Correct the URL to point to your Django server (Port 8000)
            const response = await fetch("http://127.0.0.1:8000/payments/create/", {
                method: "POST",
                body: formData,
                // If you aren't using @csrf_exempt in Django, you need the CSRF header here
            });

            // 2. Check if the response is actually JSON before parsing
            if (!response.ok) {
                const text = await response.text();
                console.error("Server Error Response:", text);
                throw new Error(`Server returned ${response.status}: Not Found or Internal Error`);
            }

            const data = await response.json();

            if (data.error) {
                alert("Error: " + data.error);
                if (loader) loader.style.display = "none";
                return;
            }

            // 3. Handle WebXPay Form population
            // Create the form if it doesn't exist in HTML
            let finalWebxForm = webxpayForm;
            if (!finalWebxForm) {
                finalWebxForm = document.createElement("form");
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
            // Hide loader so user can try again
            if (loader) loader.style.display = "none";
        }
    });
});