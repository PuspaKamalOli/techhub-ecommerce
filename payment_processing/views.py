from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import stripe
import json
from .models import Payment, PaymentMethod
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_page(request, order_id):
    """Display payment page for an order"""
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        current_user = request.user
    else:
        order = get_object_or_404(Order, id=order_id)
        if not request.session.get(f'order_{order.order_number}'):
            return redirect('products:home')
        current_user = None
    
    # Check if payment already exists
    existing_payment = Payment.objects.filter(order=order).first()
    if existing_payment and existing_payment.status == 'completed':
        messages.warning(request, 'Payment already completed for this order.')
        return redirect('orders:order_detail', order_number=order.order_number)
    
    # Create or get payment
    payment, created = Payment.objects.get_or_create(
        order=order,
        user=current_user,
        defaults={
            'amount': order.total_amount,
            'currency': 'USD',
            'payment_method': 'stripe',
        }
    )
    
    if created:
        # Create Stripe PaymentIntent
        try:
            intent = payment.create_stripe_payment_intent()
            client_secret = intent.client_secret
        except stripe.error.StripeError as e:
            messages.error(request, f'Payment setup failed: {str(e)}')
            return redirect('orders:order_detail', order_number=order.order_number)
    else:
        # Get existing PaymentIntent
        if payment.stripe_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                client_secret = intent.client_secret
            except stripe.error.StripeError:
                # Create new PaymentIntent if old one is invalid
                intent = payment.create_stripe_payment_intent()
                client_secret = intent.client_secret
        else:
            intent = payment.create_stripe_payment_intent()
            client_secret = intent.client_secret
    
    context = {
        'order': order,
        'payment': payment,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'client_secret': client_secret,
    }
    
    return render(request, 'payment_processing/payment_page.html', context)

def payment_success(request, order_id):
    """Handle successful payment"""
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment = get_object_or_404(Payment, order=order, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)
        if not request.session.get(f'order_{order.order_number}'):
            return redirect('products:home')
        payment = get_object_or_404(Payment, order=order, user=None)
    
    if payment.status == 'completed':
        messages.success(request, 'Payment completed successfully!')
        return redirect('orders:order_detail', order_number=order.order_number)
    else:
        messages.error(request, 'Payment not completed. Please try again.')
        return redirect('payment_processing:payment_page', order_id=order_id)

def payment_cancel(request, order_id):
    """Handle cancelled payment"""
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment = get_object_or_404(Payment, order=order, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)
        if not request.session.get(f'order_{order.order_number}'):
            return redirect('products:home')
        payment = get_object_or_404(Payment, order=order, user=None)
    
    payment.status = 'cancelled'
    payment.save()
    
    messages.info(request, 'Payment was cancelled.')
    return redirect('orders:order_detail', order_number=order.order_number)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        from .tasks import process_payment_success
        payment_intent = event['data']['object']
        process_payment_success.delay(payment_intent['id'])
    elif event['type'] == 'payment_intent.payment_failed':
        from .tasks import process_payment_failure
        payment_intent = event['data']['object']
        process_payment_failure.delay(payment_intent['id'])
    
    return JsonResponse({'status': 'success'})

def payment_history(request):
    """Display user's payment history"""
    payments = Payment.objects.filter(user=request.user).select_related('order')
    
    context = {
        'payments': payments,
    }
    
    return render(request, 'payment_processing/payment_history.html', context)
