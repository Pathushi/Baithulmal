document.addEventListener("DOMContentLoaded", function () {
    const donationForm = document.getElementById("donationForm");
    const webxpayForm = document.getElementById("webxpayForm");
    const loader = document.getElementById("loader");

    donationForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        loader.classList.remove("hidden");

        const formData = new FormData(donationForm);

        try {
            const response = await fetch("/payments/create/", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (data.error) {
                alert("Error: " + data.error);
                loader.classList.add("hidden");
                return;
            }

            // Populate hidden WebXPay form
            webxpayForm.action = data.payment_url;
            webxpayForm.innerHTML = ""; // clear previous inputs

            for (const key in data.params) {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = key;
                input.value = data.params[key];
                webxpayForm.appendChild(input);
            }

            // Submit to WebXPay
            webxpayForm.submit();

        } catch (err) {
            console.error(err);
            alert("Payment initiation failed.");
            loader.classList.add("hidden");
        }
    });
});
