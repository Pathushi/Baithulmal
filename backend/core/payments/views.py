import hashlib
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from .models import Payment, FailedPayment


# -------------------------------
# WebXPay Hash Generator
# -------------------------------
def generate_webxpay_hash(merchant_id, transaction_id, amount, secret):
    raw = f"{merchant_id}{transaction_id}{amount}{secret}"
    return hashlib.md5(raw.encode()).hexdigest().upper()


# -------------------------------
# Create Payment (Before Redirect)
# -------------------------------
@csrf_exempt
def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    payment = Payment.objects.create(
        name=request.POST.get("name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        country=request.POST.get("country"),
        amount=request.POST.get("amount"),
        message=request.POST.get("message"),
        status="Pending",
    )

    secure_hash = generate_webxpay_hash(
        settings.WEBXPAY_MERCHANT_ID,
        payment.transaction_id,
        payment.amount,
        settings.WEBXPAY_SECRET,
    )

    return JsonResponse({
        "payment_url": settings.WEBXPAY_URL,
        "merchant_id": settings.WEBXPAY_MERCHANT_ID,
        "transaction_id": str(payment.transaction_id),
        "amount": str(payment.amount),
        "currency": "USD",
        "hash": secure_hash,
        "return_url": "http://127.0.0.1:8000/payments/callback/",
        "cancel_url": "http://127.0.0.1:8000/payments/callback/",
    })


# -------------------------------
# Send Thank You Email (HTML)
# -------------------------------
def send_thank_you_email(payment):
    subject = "Thank you for your donation"
    from_email = settings.EMAIL_HOST_USER
    to_email = [payment.email]

    text_content = f"""
Dear {payment.name},

Thank you for your generous donation of USD {payment.amount}.

Your support truly makes a difference.

May Allah reward you abundantly.

Best regards,
Baithulmal Team
"""

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
        <div style="background-color: #ffffff; max-width: 600px; margin: auto;
                    padding: 30px; border-radius: 8px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
          <h2 style="color:#0f3d2e;">Thank you for your donation 🤍</h2>

          <p>Dear <strong>{payment.name}</strong>,</p>

          <p>
            We sincerely thank you for your generous donation of
            <strong style="color:#145c44;">USD {payment.amount}</strong>.
          </p>

          <p>Your support helps us continue our mission and bring hope to those in need.</p>

          <p>May Allah reward you abundantly for your kindness and generosity.</p>

          <p>
            Warm regards,<br>
            <strong>Ceylon Baithulmal Fund</strong>
          </p>

          <hr>
          <small>
            📍 Colombo, Sri Lanka<br>
            📧 info@baithulmal.lk
          </small>
        </div>
      </body>
    </html>
    """

    email = EmailMultiAlternatives(
        subject,
        text_content,
        from_email,
        to_email
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


# -------------------------------
# WebXPay Callback Handler
# -------------------------------
@csrf_exempt
def payment_callback(request):
    transaction_id = request.POST.get("transaction_id")
    status = request.POST.get("status")  # SUCCESS / FAILED

    if not transaction_id:
        return HttpResponse("Invalid callback data", status=400)

    try:
        payment = Payment.objects.get(transaction_id=transaction_id)

        if status == "SUCCESS":
            payment.status = "Success"
            payment.save()

            # ✅ Send email ONLY on success
            send_thank_you_email(payment)

            return HttpResponse("Payment Successful")

        else:
            payment.status = "Failed"
            payment.save()

            FailedPayment.objects.create(
                transaction_id=payment.transaction_id,
                name=payment.name,
                email=payment.email,
                phone=payment.phone,
                amount=payment.amount,
            )

            return HttpResponse("Payment Failed")

    except Payment.DoesNotExist:
        return HttpResponse("Payment not found", status=404)
