import uuid
import logging
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail  # ADDED send_mail
from .models import Payment, FailedPayment, ContactMessage      # ADDED ContactMessage
# stop from changing amount
from .crypto_utils import encrypt_payment
from django.utils import timezone
from django.shortcuts import render

logger = logging.getLogger(__name__)

def send_thank_you_email(payment):
    # Generate Timestamp and Reference No
    now = timezone.now()
    date_str = now.strftime('%d/%m/%Y')
    time_str = now.strftime('%H:%M')
    timestamp = now.strftime('%Y%m%d%H%M')

    # Format: CBF-FirstNameLastName-Timestamp
    full_name_no_spaces = f"{payment.first_name}{payment.last_name}".replace(" ", "")
    ref_no = f"CBF-{full_name_no_spaces}-{timestamp}"

    subject = f"CEYLON BAITHULMAL FUND | YOUR DONATION | {date_str} | {time_str}"
    from_email = settings.EMAIL_HOST_USER
    to_email = [payment.email]

    # Professional Text Version
    text_content = f"""
Dear Sir/Madam {payment.first_name} {payment.last_name},

Thank you for your valuable donation.
Your support helps us serve better and reach more people.

YOUR DONATION DETAILS
Reference Number: {ref_no}
Name: {payment.first_name} {payment.last_name}
Donation Option: {payment.donation_option}
Donated To: {payment.donate_to}
Country: {payment.country}
Email: {payment.email}
Date | Time: {date_str} | {time_str}
Amount Donated: USD {payment.amount}

May Allah reward you and your family.

Ceylon Baithulmal Fund
https://baithulmal.lk/
"""

    # Professional HTML Version
    html_content = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px;">
          <h2 style="color: #2c3e50; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
            CEYLON BAITHULMAL FUND
          </h2>
          <p>Dear Sir/Madam <strong>{payment.first_name} {payment.last_name}</strong>,</p>
          <p>Thank you for your valuable donation. Your support helps us serve better and reach more people.</p>

          <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; font-size: 16px; color: #27ae60;">YOUR DONATION DETAILS</h3>
            <table style="width: 100%; font-size: 14px;">
              <tr><td><strong>Ref No:</strong></td><td>{ref_no}</td></tr>
              <tr><td><strong>Name:</strong></td><td>{payment.first_name} {payment.last_name}</td></tr>
              <tr><td><strong>Donation Type:</strong></td><td>{payment.donation_option}</td></tr>
              <tr><td><strong>Appeal:</strong></td><td>{payment.donate_to}</td></tr>
              <tr><td><strong>Country:</strong></td><td>{payment.country}</td></tr>
              <tr><td><strong>Date | Time:</strong></td><td>{date_str} | {time_str}</td></tr>
              <tr><td><strong>Amount:</strong></td><td><strong style="color: #27ae60;">USD {payment.amount:.2f}</strong></td></tr>
            </table>
          </div>

          <p><i>May Allah reward you and your family.</i></p>

          <hr style="border: 0; border-top: 1px solid #eee;" />
          <p style="font-size: 12px; color: #777;">
            <strong>Ceylon Baithulmal Fund</strong><br>
            <a href="https://baithulmal.lk/">baithulmal.lk</a> | c.baithulmal@gmail.com<br>
            (+94) 11 25 99 075
          </p>
        </div>
      </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


# Django normally blocks requests from external websites for security
@csrf_exempt
def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        # Get and validate amount
        # Get primary amount (fixed value or "other")
        amount_str = request.POST.get("amount", "").strip()
        
        # If "other" is selected, grab the value from the numeric box
        if amount_str.lower() == "other":
            amount_str = request.POST.get("other_amount", "").strip()

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                return JsonResponse({"error": "Amount must be greater than 0"}, status=400)
        except (ValueError, TypeError, Exception):
            return JsonResponse({"error": "Please enter a valid numeric amount"}, status=400)

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
            donation_option=request.POST.get("donation_option", "").strip(), # ADD THIS
            donate_to=request.POST.get("donate_to", "").strip(),             # ADD THIS
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

        # REQUIRED FIX (where i got the OTP from WebXPay support)- encrytion method identifier
        "enc_method": "JCs3J+6oSz4V0LgE0zi/Bg==",

        "cms": "Django",
        "process_currency": "LKR",
        "custom_fields": "",
        "payment_gateway_id": "",
        "callback_id": str(payment.transaction_id),
        "version": "5.2"  # webxpay api version
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

# Django normally blocks requests from external websites for security
@csrf_exempt
def payment_callback(request):
    # Support both POST and GET data from WebXPay
    data = request.POST if request.POST else request.GET

    # DEBUG: View exactly what the gateway is sending back in your server logs
    print(f"\n--- WEBXPAY CALLBACK DATA RECEIVED: {dict(data)} ---\n")

    # Extract ID: Check 'order_id' or 'callback_id'
    raw_id = data.get("order_id") or data.get("callback_id")
    transaction_id = raw_id.strip() if raw_id else None
    status_code = data.get("status_code")

    if not transaction_id:
        return HttpResponse("Invalid callback data: Missing transaction identification", status=400)

    try:
        # Case-insensitive lookup of the payment record
        payment = Payment.objects.get(transaction_id__iexact=transaction_id)

        # "00" is the success status code for WebXPay
        if status_code == "00":
            payment.status = "Success"
            payment.save()
            
            # Generate the same Ref No used in the professional email
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            full_name = f"{payment.first_name}{payment.last_name}".replace(" ", "")
            ref_no = f"CBF-{full_name}-{timestamp}"

            try:
                # This uses the working EmailMultiAlternatives logic we set up
                send_thank_you_email(payment)
            except Exception as e:
                logger.error(f"Email failed for {transaction_id}: {e}")

            # --- PROFESSIONAL SUCCESS UI ---
            return HttpResponse(f"""
                <div style="font-family: Arial, sans-serif; background-color: #f4f7f6; height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0;">
                    <div style="background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 90%;">
                        <div style="width: 70px; height: 70px; background: #92BC13; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 35px;">✓</div>
                        <h1 style="color: #2c3e50; margin-bottom: 10px;">Alhamdulillah!</h1>
                        <p style="color: #7f8c8d;">Your donation of <strong>LKR {payment.amount}</strong> was successful.</p>
                        <div style="background: #f9f9f9; border: 1px dashed #ccc; padding: 15px; margin: 20px 0; border-radius: 10px;">
                            <span style="font-size: 11px; color: #999; display: block; text-transform: uppercase; letter-spacing: 1px;">Reference Number</span>
                            <span style="font-weight: bold; color: #2c3e50; font-size: 14px;">{ref_no}</span>
                        </div>
                        <p style="font-size: 14px; color: #7f8c8d;">A receipt has been sent to your email.</p>
                        <a href="/" style="display: inline-block; background: #92BC13; color: white; padding: 12px 35px; text-decoration: none; border-radius: 50px; font-weight: bold; transition: 0.3s; margin-top: 10px;">Return to Home</a>
                    </div>
                </div>
            """)

        else:
            # Handle Payment Failure
            payment.status = "Failed"
            payment.save()
            
            FailedPayment.objects.create(
                transaction_id=payment.transaction_id,
                first_name=payment.first_name,
                amount=payment.amount
            )
            
            # --- PROFESSIONAL FAILURE UI ---
            return HttpResponse(f"""
                <div style="font-family: Arial, sans-serif; background-color: #f4f7f6; height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0;">
                    <div style="background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 90%;">
                        <div style="width: 70px; height: 70px; background: #e74c3c; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 35px;">✕</div>
                        <h1 style="color: #c0392b; margin-bottom: 10px;">Payment Failed</h1>
                        <p style="color: #7f8c8d;">We were unable to process your donation. Please try again or contact our support.</p>
                        <a href="/" style="display: inline-block; background: #e74c3c; color: white; padding: 12px 35px; text-decoration: none; border-radius: 50px; font-weight: bold; margin-top: 10px;">Try Again</a>
                    </div>
                </div>
            """)

    except Payment.DoesNotExist:
        logger.error(f"Payment ID {transaction_id} not found in database.")
        return HttpResponse(f"Payment ID {transaction_id} not found.", status=404)
    except Exception as e:
        logger.exception("Callback error")
        return HttpResponse("An internal error occurred.", status=500)


@csrf_exempt
def contact_us_view(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("phone", "").strip()
            message = request.POST.get("message", "").strip()

            # 1. Save to Database
            ContactMessage.objects.create(name=name, email=email, phone=phone, message=message)

            # 2. Build HTML Email Body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
                        <div style="background-color: #92BC13; color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0;">New Website Inquiry</h1>
                        </div>
                        <div style="padding: 20px;">
                            <p><strong>From:</strong> {name}</p>
                            <p><strong>Email:</strong> {email}</p>
                            <p><strong>Phone:</strong> {phone}</p>
                            <hr style="border: 0; border-top: 1px solid #eee;">
                            <p><strong>Message:</strong></p>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 5px solid #92BC13;">
                                {message}
                            </div>
                        </div>
                        <div style="background: #f1f1f1; padding: 10px; text-align: center; font-size: 12px; color: #777;">
                            This message was sent from the Ceylon Baithulmal Fund website contact form.
                        </div>
                    </div>
                </body>
            </html>
            """

            # 3. Send the HTML Email
            from django.core.mail import EmailMessage
            email_msg = EmailMessage(
                subject=f"Inquiry from {name}",
                body=html_body,
                from_email=settings.EMAIL_HOST_USER,
                to=['pathushi.m@gmail.com'],
            )
            email_msg.content_subtype = "html"  # Critical: Set to HTML
            email_msg.send()

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
