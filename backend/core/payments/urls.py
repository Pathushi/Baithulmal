from django.urls import path
from .views import create_payment
from django.urls import path
from . import views


urlpatterns = [
    path('donate/', views.donate_page, name='donate_page'),
    path('create/', views.create_payment, name='create_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
]
