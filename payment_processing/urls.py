from django.urls import path
from . import views

app_name = 'payment_processing'

urlpatterns = [
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('payment/<int:order_id>/success/', views.payment_success, name='payment_success'),
    path('payment/<int:order_id>/cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('history/', views.payment_history, name='payment_history'),
]
