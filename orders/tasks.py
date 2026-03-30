from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Order

@shared_task
def send_order_confirmation_email(order_id):
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Order Confirmation - {order.order_number}'
        message = f'Hi {order.shipping_name},\n\nThank you for your order {order.order_number}!\nYour total is ${order.total_amount}.\n\nWe will notify you once it ships.'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@techhub.com')
        
        send_mail(
            subject,
            message,
            from_email,
            [order.shipping_email],
            fail_silently=True,
        )
        return True
    except Order.DoesNotExist:
        return False
