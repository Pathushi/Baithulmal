import hashlib
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Payment, FailedPayment


def generate_webxpay_hash(merchant_id, transaction_id, amount, secret):
    raw = f"{merchant_id}{transaction_id}{amount}{secret}"
    return hashlib.md5(raw.encode()).hexdigest().upper()


@csrf_exempt
def create_payment(request):
    if request.method == "POST":
        payment = Payment.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            country=request.POST.get("country"),
            amount=request.POST.get("amount"),
            message=request.POST.get("message"),
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
            "cancel_url": "http://127.0.0.1:8000/payments/failed/",
        })


@csrf_exempt
def payment_callback(request):
    transaction_id = request.POST.get("transaction_id")
    status = request.POST.get("status")  # SUCCESS / FAILED

    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        if status == "SUCCESS":
            payment.status = "Success"
            payment.save()
            return HttpResponse("Payment Successful")
        else:
            raise Exception("Failed")
    except:
        FailedPayment.objects.create(
            transaction_id=transaction_id,
            name=payment.name,
            email=payment.email,
            phone=payment.phone,
            amount=payment.amount,
        )
        return HttpResponse("Payment Failed")
