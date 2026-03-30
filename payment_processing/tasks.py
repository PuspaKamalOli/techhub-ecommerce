from celery import shared_task
from .models import Payment

@shared_task
def process_payment_success(payment_intent_id):
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.confirm_payment(payment_intent_id)
        
        # Trigger email task securely in the background
        from orders.tasks import send_order_confirmation_email
        send_order_confirmation_email.delay(payment.order.id)
        return True
    except Payment.DoesNotExist:
        return False

@shared_task
def process_payment_failure(payment_intent_id):
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.status = 'failed'
        payment.save()
        return True
    except Payment.DoesNotExist:
        return False
