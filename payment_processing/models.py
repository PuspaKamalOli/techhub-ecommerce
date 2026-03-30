from django.db import models
from django.contrib.auth.models import User
from orders.models import Order
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash on Delivery'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='stripe')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.order.order_number} - {self.status}"
    
    def create_stripe_payment_intent(self):
        """Create a Stripe PaymentIntent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(self.amount * 100),  # Convert to cents
                currency=self.currency.lower(),
                metadata={
                    'order_id': self.order.id,
                    'order_number': self.order.order_number,
                    'user_id': self.user.id,
                }
            )
            self.stripe_payment_intent_id = intent.id
            self.save()
            return intent
        except stripe.error.StripeError as e:
            self.status = 'failed'
            self.save()
            raise e
    
    def confirm_payment(self, payment_intent_id):
        """Confirm payment completion"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == 'succeeded':
                self.status = 'completed'
                self.stripe_charge_id = intent.latest_charge
                self.transaction_id = payment_intent_id
                self.save()
                
                # Update order status
                self.order.status = 'paid'
                self.order.save()
                
                return True
            else:
                self.status = 'failed'
                self.save()
                return False
        except stripe.error.StripeError as e:
            self.status = 'failed'
            self.save()
            raise e

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255, unique=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.IntegerField(blank=True, null=True)
    card_exp_year = models.IntegerField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.card_brand} ****{self.card_last4} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
