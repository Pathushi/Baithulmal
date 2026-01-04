import uuid
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

    text_content = f"Dear {payment.first_name},\n\nThank you for your donation of LKR {payment.amount}.\n\nBest regards,\nCeylon Baithulmal Fund"

    html_content = f"""
    <html>
      <body style="font-family: Arial; background:#f4f6f8; padding:20px;">
        <div style="background:#fff; padding:30px; max-width:600px; margin:auto;">
          <h2>Thank you for your donation!</h2>
          <p>Dear <strong>{payment.first_name} {payment.last_name}</strong>,</p>
          <p>You donated <strong>LKR {payment.amount:.2f}</strong>.</p>
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

        # Force the amount to have 2 decimal places ("50.00" instead of "50")
        encrypted_payment = encrypt_payment(str(payment.transaction_id), f"{amount:.2f}")

         # Build parameters according to WebXPay documentation
        params = {
        "first_name": payment.first_name,
        "last_name": payment.last_name,
        "email": payment.email,
        "contact_number": payment.phone,
        "address_line_one": payment.address_line_one,
        "address_line_two": payment.address_line_two,
        "city": payment.city,
        "state": payment.state,
        "postal_code": payment.postal_code,
        "country": payment.country,
        "return_url": settings.WEBXPAY_RETURN_URL,


        "secret_key": settings.WEBXPAY_SECRET,
        "payment": encrypted_payment,

        # REQUIRED FIX (where i got the OTP from WebXPay support)
        "enc_method": "JCs3J+6oSz4V0LgE0zi/Bg==",

        "cms": "Django",
        "process_currency": "LKR",
        "custom_fields": "",
        "payment_gateway_id": "",
        "callback_id": str(payment.transaction_id),
        "version": "5.2"
}




        # DEBUG LINE:
        print(f"--- DEBUG: SENT SECRET KEY: {params['secret_key']} ---") 
        print(f"--- DEBUG: SENT URL: {settings.WEBXPAY_URL} ---")

        return JsonResponse({
            "payment_url": settings.WEBXPAY_URL,
            "params": params
        })


    except Exception as e:
        logger.exception("Create payment error")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def payment_callback(request):
    # Support both POST and GET
    data = request.POST if request.POST else request.GET

    print(f"\n--- WEBXPAY CALLBACK DATA: {dict(data)} ---\n")

    # 1. Get the ID (WebXPay sends it as 'order_id')
    transaction_id = data.get("order_id")

    # 2. Get the Status ("00" is success)
    status_code = data.get("status_code")

    if not transaction_id:
        return HttpResponse("Invalid callback data: Missing order_id", status=400)

    try:
        
        payment = Payment.objects.get(transaction_id=transaction_id)

        # 3. Check Status
        if status_code == "00":
            payment.status = "Success"
            payment.save()
            try:
                send_thank_you_email(payment)
            except Exception as e:
                logger.error(f"Email failed: {e}")

            return HttpResponse("""
                <div style="text-align:center; padding:50px; font-family:Arial;">
                    <h1 style="color:green;">Alhamdulillah! Payment Successful.</h1>
                    <p>May Allah reward you.</p>
                    <a href="/" style="background:#28a745; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Return to Home</a>
                </div>
            """)
        else:
            payment.status = "Failed"
            payment.save()
            FailedPayment.objects.create(
                transaction_id=payment.transaction_id,
                first_name=payment.first_name,
                amount=payment.amount
            )
            return HttpResponse("""
                <div style="text-align:center; padding:50px; font-family:Arial;">
                    <h1 style="color:red;">Payment Failed</h1>
                    <p>Please try again.</p>
                    <a href="/" style="background:#dc3545; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Try Again</a>
                </div>
            """)

    except Payment.DoesNotExist:
        return HttpResponse(f"Payment ID {transaction_id} not found", status=404)
    except Exception as e:
        logger.exception("Callback error")
        return HttpResponse(str(e), status=500)
