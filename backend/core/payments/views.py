from django.shortcuts import render

# Create your views here.

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import Payment
from django.conf import settings

@csrf_exempt
def create_payment(request):
    if request.method == 'POST':
        payment = Payment.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            country=request.POST.get('country'),
            amount=request.POST.get('amount'),
            message=request.POST.get('message'),
        )

        payment_url = "https://merchant.webxpay.com/payment"

        return JsonResponse({
            "payment_url": payment_url
        })

def payment_callback(request):
    # This will be called by WebXPay later
    return HttpResponse("Payment callback received")
