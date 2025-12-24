import logging
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from .models import Payment, FailedPayment
from .crypto_utils import encrypt_payment

logger = logging.getLogger(__name__)


def send_thank_you_email(payment):
    subject = "Thank you for your donation"
    from_email = settings.EMAIL_HOST_USER
    to_email = [payment.email]

    text_content = f"Dear {payment.first_name},\n\nThank you for your donation of USD {payment.amount}.\n\nBest regards,\nCeylon Baithulmal Fund"

    html_content = f"""
    <html>
      <body style="font-family: Arial; background:#f4f6f8; padding:20px;">
        <div style="background:#fff; padding:30px; max-width:600px; margin:auto;">
          <h2>Thank you for your donation!</h2>
          <p>Dear <strong>{payment.first_name} {payment.last_name}</strong>,</p>
          <p>You donated <strong>USD {payment.amount:.2f}</strong>.</p>
          <p>May Allah reward you.</p>
          <p><strong>Ceylon Baithulmal Fund</strong></p>
        </div>
      </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    email.send()


@csrf_exempt
def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        # Get and validate amount
        amount_str = request.POST.get("amount", "").strip()
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                return JsonResponse({"error": "Invalid amount"}, status=400)
        except:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        # Create Payment record
        payment = Payment.objects.create(
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            email=request.POST.get("email", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            address_line_one=request.POST.get("address_line_one", "").strip(),
            address_line_two=request.POST.get("address_line_two", "").strip(),
            city=request.POST.get("city", "").strip(),
            state=request.POST.get("state", "").strip(),
            postal_code=request.POST.get("postal_code", "").strip(),
            country=request.POST.get("country", "").strip(),
            amount=amount,
            message=request.POST.get("message", "").strip(),
            status="Pending",
        )

        # Encrypt payment parameter using RSA public key
        encrypted_payment = encrypt_payment(str(payment.transaction_id), str(amount))

        # Build params according to WebXPay documentation
        params = {
            "first_name": payment.first_name,           # Mandatory
            "last_name": payment.last_name,             # Mandatory
            "email": payment.email,                     # Mandatory
            "contact_number": payment.phone,            # Mandatory
            "address_line_one": payment.address_line_one,  # Mandatory
            "address_line_two": payment.address_line_two,  # Optional
            "city": payment.city,                       # Optional
            "state": payment.state,                     # Optional
            "postal_code": payment.postal_code,         # Optional
            "country": payment.country,                 # Optional
            "secret_key": settings.WEBXPAY_SECRET,     # Mandatory
            "payment": encrypted_payment,               # Mandatory
            "cms": "Django",                            # Mandatory
            "process_currency": "USD",                  # Mandatory
            "custom_fields": "",                        # Optional
            "payment_gateway_id": "",                    # Optional
            "callback_id": str(payment.transaction_id)  # Optional but recommended
        }

        return JsonResponse({
            "payment_url": settings.WEBXPAY_URL,
            "params": params
        })

    except Exception as e:
        logger.exception("Create payment error")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def payment_callback(request):
    data = request.POST or request.GET
    status = data.get("status")
    transaction_id = data.get("transaction_id")

    if not transaction_id or not status:
        return HttpResponse("Invalid callback data", status=400)

    try:
        payment = Payment.objects.get(transaction_id=transaction_id)

        if status.lower() in ["success", "paid"]:
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
                address_line_one=payment.address_line_one,
                address_line_two=payment.address_line_two,
                city=payment.city,
                state=payment.state,
                postal_code=payment.postal_code,
                country=payment.country,
                amount=payment.amount
            )
            return HttpResponse("Payment Failed")

    except Payment.DoesNotExist:
        return HttpResponse("Payment not found", status=404)
    except Exception as e:
        logger.exception("Callback error")
        return HttpResponse(str(e), status=500)
