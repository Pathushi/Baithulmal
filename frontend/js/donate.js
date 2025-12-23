document.getElementById('donationForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const loader = document.getElementById('loader');
    loader.classList.remove('hidden');
    loader.innerText = "Redirecting to payment...";

    const formData = new FormData(this);

    const response = await fetch("/payments/create/", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    const webxpayForm = document.getElementById("webxpayForm");
    webxpayForm.action = data.payment_url;

    Object.keys(data).forEach(key => {
        if (key !== "payment_url") {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = key;
            input.value = data[key];
            webxpayForm.appendChild(input);
        }
    });

    webxpayForm.submit();
});
