import hashlib
import base64
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from .models import Payment, FailedPayment

# -------------------------------
# WebXPay Hash Generator
# -------------------------------
def generate_webxpay_hash(merchant_id, transaction_id, amount, secret):
    raw = f"{merchant_id}{transaction_id}{amount}{secret}"
    return hashlib.md5(raw.encode()).hexdigest().upper()

# -------------------------------
# Send Thank You Email
# -------------------------------
def send_thank_you_email(payment):
    subject = "Thank you for your donation"
    from_email = settings.EMAIL_HOST_USER
    to_email = [payment.email]

    text_content = f"Dear {payment.first_name},\n\nThank you for your generous donation of USD {payment.amount}.\n\nBest regards,\nBaithulmal Team"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
        <div style="background-color: #ffffff; max-width: 600px; margin: auto; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
          <h2 style="color:#0f3d2e;">Thank you for your donation!</h2>
          <p>Dear <strong>{payment.first_name} {payment.last_name}</strong>,</p>
          <p>We sincerely thank you for your generous donation of <strong style="color:#145c44;">USD {payment.amount:.2f}</strong>.</p>
          <p>May Allah reward you abundantly for your kindness and generosity.</p>
          <p>Warm regards,<br><strong>Ceylon Baithulmal Fund</strong></p>
        </div>
      </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    email.send()

# -------------------------------
# Create Payment
# -------------------------------
@csrf_exempt
def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    # Split full name
    full_name = request.POST.get("name", "")
    first_name = full_name.split(" ")[0] if full_name else ""
    last_name = " ".join(full_name.split(" ")[1:]) if len(full_name.split(" ")) > 1 else ""

    # Convert amount to Decimal
    try:
        amount = Decimal(request.POST.get("amount", "0"))
    except:
        return JsonResponse({"error": "Invalid amount"}, status=400)

    try:
        payment = Payment.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            country=request.POST.get("country"),
            address_line_one=request.POST.get("address_line_one", ""),
            amount=amount,
            message=request.POST.get("message", ""),
            status="Pending",
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # -------------------------------
    # Format amount and generate secure hash
    # -------------------------------
    formatted_amount = f"{payment.amount:.2f}"
    secure_hash = generate_webxpay_hash(
        settings.WEBXPAY_MERCHANT_ID,
        str(payment.transaction_id),
        formatted_amount,
        settings.WEBXPAY_SECRET,
    )

    # Dynamic URLs
    return_url = request.build_absolute_uri(reverse('payment_callback'))
    cancel_url = return_url  # optional: you can create a separate cancel view

    return JsonResponse({
        "payment_url": settings.WEBXPAY_URL,
        "merchant_id": settings.WEBXPAY_MERCHANT_ID,
        "order_id": str(payment.transaction_id),
        "total_amount": formatted_amount,
        "currency_code": "USD",  # change to "LKR" if needed
        "secure_hash": secure_hash,
        "return_url": return_url,
        "cancel_url": cancel_url,
    })

# -------------------------------
# Payment Callback
# -------------------------------
@csrf_exempt
def payment_callback(request):
    transaction_id = request.POST.get("transaction_id")
    status = request.POST.get("status")

    if not transaction_id:
        return HttpResponse("Invalid callback data", status=400)

    try:
        payment = Payment.objects.get(transaction_id=transaction_id)

        if status == "SUCCESS":
            payment.status = "Success"
            payment.save()
            send_thank_you_email(payment)
            return HttpResponse("Payment Successful")
        else:
            payment.status = "Failed"
            payment.save()
            FailedPayment.objects.create(
                transaction_id=payment.transaction_id,
                first_name=payment.first_name,
                last_name=payment.last_name,
                email=payment.email,
                phone=payment.phone,
                amount=payment.amount,
            )
            return HttpResponse("Payment Failed")

    except Payment.DoesNotExist:
        return HttpResponse("Payment not found", status=404)
