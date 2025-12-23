document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('donationForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const loader = document.getElementById('loader');
        loader.classList.remove('hidden');
        loader.innerText = "Redirecting to payment...";

        const formData = new FormData(this);

        try {
            const response = await fetch("/payments/create/", {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error(`Server responded with ${response.status}`);
            const data = await response.json();

            if (data.payment_url) {
                const webxpayForm = document.getElementById("webxpayForm");
                webxpayForm.innerHTML = "";
                webxpayForm.action = data.payment_url;
                webxpayForm.method = "POST";

                // Append required hidden fields
                const requiredFields = ["merchant_id","order_id","total_amount","currency_code","secure_hash","return_url","cancel_url"];
                requiredFields.forEach(key => {
                    if (data[key]) {
                        const input = document.createElement("input");
                        input.type = "hidden";
                        input.name = key;
                        input.value = data[key];
                        webxpayForm.appendChild(input);
                    }
                });

                webxpayForm.submit();
            } else {
                loader.innerText = "Something went wrong. Please try again.";
                console.error("No payment_url returned:", data);
            }
        } catch (error) {
            console.error("Error connecting to server:", error);
            loader.innerText = "Error connecting to server. Please try again later.";
        }
    });
});
