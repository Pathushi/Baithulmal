from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_payment),
    path('callback/', views.payment_callback),
]
